
## ------------------------------------------------------------------------
#       OSAIS python Lib (interface between AIs and OSAIS)
## ------------------------------------------------------------------------

import requests
import schedule
import json
import sys
import base64
from datetime import datetime

from libOSAISTools import getHostInfo, listDirContent, is_running_in_docker, get_external_ip, get_machine_name, get_os_name, getCudaInfo, downloadImage

## ------------------------------------------------------------------------
#       all global vars
## ------------------------------------------------------------------------

gName=None                      ## name of this AI (name of engine)
gMachineName=get_machine_name() ## the name of the machine (will change all the time if inside docker, ot keep same if running on local server)
gLastchecked_at=datetime.utcnow()  ## when was this AI last used for processing anything

## authenticate into OSAIS
gAuthToken=None                 ## auth token into OSAIS for when working as virtual Ai
gToken=None                     ## token used for authentication into OSAIS
gSecret=None                    ## secret used for authentication into OSAIS
gOriginOSAIS=None               ## location of OSAIS

## authenticate into a local OSAIS (debug)
gAuthTokenLocal=None            ## auth token into a local OSAIS (debug) for when working as virtual Ai
gTokenLocal=None                ## token used for authentication into a local OSAIS (debug)
gSecretLocal=None               ## secret used for authentication into a local OSAIS (debug)
gOriginLocalOSAIS=None          ## location of a local OSAIS (debug)

gOriginGateway=None             ## location of the local gateway for this (local) AI

## IP and Ports
gExtIP=get_external_ip()        ## where this AI can be accessed from outside (IP)
gIPLocal=None                   ## where this AI can be accessed locally (localhost)
gPortAI=None                    ## port where this AI is accessed 
gPortGateway=None               ## port where the gateway can be accessed
gPortLocalOSAIS=None            ## port where a local OSAIS can be accessed

## virtual AI / local /docker ?
gIsDocker=is_running_in_docker()   ## are we running in a Docker?
gIsVirtualAI=False              ## are we working as a Virtual AI config?
gIsLocal=False                  ## are we working locally (localhost server)?

## temp cache
gAProcessed=[]                  ## all token being sent to processing (never call twice for same)

AI_PROGRESS_ERROR=-1
AI_PROGRESS_IDLE=0
AI_PROGRESS_ARGS=1
AI_PROGRESS_AI_STARTED=2
AI_PROGRESS_INIT_IMAGE=3
AI_PROGRESS_DONE_IMAGE=4
AI_PROGRESS_AI_STOPPED=5

## ------------------------------------------------------------------------
#       private fcts
## ------------------------------------------------------------------------

# Register our VAI into OSAIS
def _registerVAI():
    global gExtIP
    global gIPLocal
    global gPortLocalOSAIS
    global gPortAI
    global gName
    global gToken
    global gSecret
    global gOriginOSAIS
    global gTokenLocal
    global gSecretLocal
    global gOriginLocalOSAIS
    global gIsVirtualAI

    _ip=gExtIP
    if gIsVirtualAI:
        _ip=gIPLocal

    objCudaInfo=getCudaInfo()
    gpuName="no GPU"
    if objCudaInfo != 0 and "name" in objCudaInfo and objCudaInfo["name"]:
        gpuName=objCudaInfo["name"]

    headers = {
        "Content-Type": "application/json"
    }
    objParam={
        "os": get_os_name(),
        "gpu": gpuName,
        "machine": get_machine_name(),
        "ip": _ip,
        "port": gPortAI,
        "engine": gName
    }

    ## reg with Prod
    try:
        response = requests.post(f"{gOriginOSAIS}api/v1/public/virtualai/register", headers=headers, data=json.dumps(objParam))
        objRes=response.json()["data"]
        if objRes is None:
            print("COULD NOT REGISTER, stopping it here")
            sys.exit()

        gToken=objRes["token"]
        gSecret=objRes["secret"]
        print("We are REGISTERED with OSAIS Prod")

    except Exception as err:
        raise err

    ## reg with Local OSAIS (debug)
    try:
        response = requests.post(f"{gOriginLocalOSAIS}api/v1/public/virtualai/register", headers=headers, data=json.dumps(objParam))
        objRes=response.json()["data"]
        if objRes is None:
            print("COULD NOT REGISTER with debug")

        gTokenLocal=objRes["token"]
        gSecretLocal=objRes["secret"]
        print("We are REGISTERED with OSAIS Local (debug)")
    except Exception as err:
        ## nothing 
        return True

    return True

# Authenticate into OSAIS
def _loginVAI():
    global gToken
    global gSecret
    global gAuthToken
    global gTokenLocal
    global gSecretLocal
    global gAuthTokenLocal

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{gOriginOSAIS}api/v1/public/virtualai/login", headers=headers, data=json.dumps({
            "token": gToken,
            "secret": gSecret
        }))

        objRes=response.json()["data"]
        if objRes is None:
            print("COULD NOT LOGIN, stopping it here")
            sys.exit()

        print("We got an authentication token into OSAIS")
        gAuthToken=objRes["authToken"]    

    except Exception as err:
        raise err

    try:
        response = requests.post(f"{gOriginLocalOSAIS}api/v1/public/virtualai/login", headers=headers, data=json.dumps({
            "token": gTokenLocal,
            "secret": gSecretLocal
        }))

        objRes=response.json()["data"]
        if objRes is None:
            print("COULD NOT LOGIN into OSAIS Local")

        print("We got an authentication token into OSAIS Local (debug)")
        gAuthTokenLocal=objRes["authToken"]    

    except Exception as err:
        return True

    return True

def _getArgs(_args):
    result = []
    for key, value in _args.items():
        if key.startswith("-"):
            result.append(key)
            result.append(value)
    return result

# Upload image to OSAIS 
def _uploadImageToOSAIS(objParam, isLocal):
    if gIsVirtualAI==False:
        return None
    
    global gAuthToken
    global gOriginOSAIS
    global gAuthTokenLocal
    global gOriginLocalOSAIS

    _auth=gAuthToken
    if isLocal:
        _auth=gAuthTokenLocal
    _osais=gOriginOSAIS
    if isLocal:
        _osais=gOriginLocalOSAIS

    # lets go call OSAIS AI Gateway / or OSAIS itself
    headers = {
        "Content-Type": 'application/json', 
        'Accept': 'text/plain',
        "Authorization": f"Bearer {_auth}"
    }

    api_url=f"{_osais}api/v1/private/upload"        
    payload = json.dumps(objParam)
    response = requests.post(api_url, headers=headers, data=payload )
    objRes=response.json()
    return objRes    

## ------------------------------------------------------------------------
#       public fcts
## ------------------------------------------------------------------------

## resetting who this AI is talking to (OSAIS or gateway)
def osais_resetOSAIS(_locationProd, _localtionDebug):
    global gOriginOSAIS
    global gOriginLocalOSAIS
    gOriginOSAIS=_locationProd
    gOriginLocalOSAIS=_localtionDebug
    print("=> This AI is reset to talk to PROD "+gOriginOSAIS)
    print("=> This AI is reset to talk to DEBUG "+gOriginLocalOSAIS+"\r\n")
    return True

# Init the Virtual AI
def osais_initializeAI(params):
    global gPortAI
    gPortAI=params["port_ai"]
    global gPortGateway
    gPortGateway=params["port_gateway"]
    global gPortLocalOSAIS
    gPortLocalOSAIS=params["port_localOSAIS"]
    global gIPLocal
    gIPLocal=params["ip_local"]
    global gName
    gName=params["engine"]
    global gIsLocal
    gIsLocal=params["isLocal"]
    global gIsVirtualAI
    gIsVirtualAI=params["isVirtualAI"]

    ## where is OSAIS for us then?
    global gExtIP
    global gIsDocker
    global gOriginGateway
    gOriginGateway=f"http://{gIPLocal}:{gPortGateway}/"         ## config for local gateway (local and not virtual)

    osais_resetOSAIS("https://opensourceais.com/", f"http://{gIPLocal}:{gPortLocalOSAIS}/")

    if gIsVirtualAI:
        osais_authenticateAI()

    if gIsVirtualAI==False: 
        print("=> Running "+gName+" AI as a server connected to local Gateway "+gOriginOSAIS+"\r\n")
    else:
        print("=> Running "+gName+" AI as a virtual AI connected to: "+gOriginOSAIS+"\r\n")
    return True

## info about this AI
def osais_getInfo() :
    global gExtIP
    global gPortAI
    global gName
    global gIsDocker
    global gMachineName
    return {
        "name": gName,
        "location": f"{gExtIP}:{gPortAI}/",
        "isRunning": True,    
        "isDocker": gIsDocker,    
        "lastActive_at": gLastchecked_at,
        "machine": gMachineName
    }

## info about harware this AI is running on
def osais_getHarwareInfo() :
    return getHostInfo()

## get list of files in a dir (check what was generated)
def osais_getDirectoryListing(_dir) :
    return listDirContent(_dir)

# Authenticate the Virtual AI into OSAIS
def osais_authenticateAI():
    global gIsVirtualAI
    global gOriginOSAIS
    if gIsVirtualAI:

        resp= _registerVAI()
        print(json.dumps(resp, indent=4))

        resp=_loginVAI()
        print(json.dumps(resp, indent=4))

        # Run the scheduler
        schedule.every().day.at("10:30").do(_loginVAI)

    return True

def osais_runAI(fn_run, _args):
    _input=None
    aFinalArg=_getArgs(_args)

    ## process the filename passed in dir (case localhost / AI Gateway), or download file from URL (case AI running as Virtual AI)
    _filename=_args.get('-filename')
    _urlUpload=_args.get('url_upload')
    if not _filename and _urlUpload:
        _input=downloadImage(_urlUpload)
        if _input:
            aFinalArg.append("-filename")
            aFinalArg.append(_input)
        else:
            ## min requirements
            print("no image to process")
            return "input required"

    print("\r\n=> before run: processed args from url: "+str(aFinalArg)+"\r\n")

    ## do not process twice same uid
    _uid=_args.get('-uid')
    global gAProcessed
    if _uid in gAProcessed:
        return  "not processing, already tried..."
    
    global gName 
    gAProcessed.append(_uid)
    _token=_args.get('-t')

    isLocal=(_args.get('-local')=="True")

    ## notify start
    CredsParam={"engine": gName, "tokenAI": _token, "username": _args.get('-u'), "isLocal": isLocal}
    MorphingParam={"uid": _uid, "cycle": 0, "filename": _input}
    StageParam={"stage": AI_PROGRESS_AI_STARTED, "descr": "AI is ready to start"}
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## run the AI
    fn_run(aFinalArg)

    ## notify end
    StageParam={"stage": AI_PROGRESS_AI_STOPPED,  "descr": "end of AI job..."}
    osais_notify(CredsParam, MorphingParam , StageParam)

    return "request processed!"

# Direct Notify OSAIS 
def osais_notify(CredParam, MorphingParam, StageParam):
    global gIPLocal
    global gPortGateway
    global gOriginOSAIS
    global gOriginLocalOSAIS
    global gIsVirtualAI
    global gAuthToken
    global gAuthTokenLocal
    global gLastchecked_at
    gLastchecked_at = datetime.utcnow()

    # notification console log
    merged = dict()
    merged.update(CredParam)
    merged.update(MorphingParam)
    print("NotifyOSAIS ("+str(StageParam["stage"])+"/ "+StageParam["descr"]+"): "+str(merged))
    print("\r\n")

    _filename=""
    if MorphingParam["filename"]!="":
        _filename=MorphingParam["filename"]

    # lets go call OSAIS AI Gateway / or OSAIS itself
    headers = {
        "Content-Type": "application/json"
    }

    ## config for calling gateway
    api_url = f"{gOriginGateway}api/v1/public/notify"

    ## config for calling OSAIS (no gateway)
    if gIsVirtualAI:
        _osais=gOriginOSAIS
        _auth=gAuthToken

        if CredParam["isLocal"]:
            _osais=gOriginLocalOSAIS
            _auth=gAuthTokenLocal

        if gIsVirtualAI==True:
            headers["Authorization"]= f"Bearer {_auth}"
            api_url=f"{_osais}api/v1/private/notify"

    objParam={
        "response": {
            "token": CredParam["tokenAI"],
            "uid": str(MorphingParam["uid"]),
            "stage": str(StageParam["stage"]),
            "cycle": str(MorphingParam["cycle"]),
            "engine": CredParam["engine"],
            "username": CredParam["username"],
            "descr": StageParam["descr"],
            "filename": _filename
        }
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(objParam) )
    objRes=response.json()

    if StageParam["stage"]==AI_PROGRESS_DONE_IMAGE:
        if gIsVirtualAI==True:
            _dirImage=f"./_output/{_filename}"

            with open(_dirImage, "rb") as image_file:
                image_data = image_file.read()

            im_b64 = base64.b64encode(image_data).decode("utf8")
            param={
                "image": im_b64,
                "uid": str(MorphingParam["uid"]),
                "cycle": str(MorphingParam["cycle"]),
                "engine": CredParam["engine"],
            }            
            _uploadImageToOSAIS(param, CredParam["isLocal"])
    return objRes

def getCredsParams(_args) :
    global gName
    return {"engine": gName, "tokenAI": _args.tokenAI, "username": _args.username, "isLocal": _args.isLocal} 

def getMorphingParams(_args) :
    return {"uid": _args.uid, "cycle": 0, "filename":_args.init_image}

def getStageParams(_args, _stage) :
    if _stage==AI_PROGRESS_ARGS:
        return {"stage": AI_PROGRESS_AI_STARTED, "descr":"Just parsed AI params"}
    if _stage==AI_PROGRESS_ERROR:
        return {"stage": AI_PROGRESS_AI_STOPPED, "descr":"AI stopped with error"}
    if _stage==AI_PROGRESS_AI_STARTED:
        return {"stage": AI_PROGRESS_AI_STARTED, "descr":"AI started"}
    if _stage==AI_PROGRESS_AI_STOPPED:
        return {"stage": AI_PROGRESS_AI_STOPPED, "descr":"AI stopped"}
    if _stage==AI_PROGRESS_INIT_IMAGE:
        return {"stage": AI_PROGRESS_INIT_IMAGE, "descr":"destination image = "+_args.output}
    if _stage==AI_PROGRESS_DONE_IMAGE:
        return {"stage": AI_PROGRESS_DONE_IMAGE, "descr":"copied input image to destination image"}
    return {"stage": AI_PROGRESS_ERROR, "descr":"error"}


## ------------------------------------------------------------------------
#       Init processing
## ------------------------------------------------------------------------

print("AI ready for processing requests...")

