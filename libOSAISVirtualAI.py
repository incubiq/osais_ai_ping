
## ------------------------------------------------------------------------
#       OSAIS python Lib (interface between AIs and OSAIS)
## ------------------------------------------------------------------------

import requests
import schedule
import json
import sys
import os
import base64
from datetime import datetime

from libOSAISTools import getHostInfo, listDirContent, is_running_in_docker, get_external_ip, get_machine_name, get_os_name, getCudaInfo, downloadImage

## ------------------------------------------------------------------------
#       all global vars
## ------------------------------------------------------------------------

gName=None                      ## name of this AI (name of engine)
gMachineName=get_machine_name() ## the name of the machine (will change all the time if inside docker, ot keep same if running on local server)
gAuthToken=None                 ## auth token into OSAIS for when working as virtual Ai
gToken=None                     ## token used for authentication into OSAIS
gSecret=None                    ## secret used for authentication into OSAIS
gOriginOSAIS=None               ## location of OSAIS
gLastchecked_at=datetime.utcnow()  ## when was this AI last used for processing anything
gExtIP=get_external_ip()        ## where this AI can be accessed from outside (IP)
gIPLocal=None                   ## where this AI can be accessed locally (localhost)
gPortAI=None                    ## port where this AI is accessed 
gPortGateway=None               ## port where the gateway can be accessed
gPortLocalOSAIS=None            ## port where a local OSAIS can be accessed
gIsDocker=is_running_in_docker()   ## are we running in a Docker?
gIsVirtualAI=False              ## are we working as a Virtual AI config?
gIsLocal=False                  ## are we working locally (localhost server)?
gAProcessed=[]                  ## all token being sent to processing (never call twice for same)

AI_PROGRESS_ERROR=-1
AI_PROGRESS_IDLE=0
AI_PROGRESS_AI_STARTED=2
AI_PROGRESS_INIT_IMAGE=3
AI_PROGRESS_DONE_IMAGE=4
AI_PROGRESS_AI_STOPPED=5

## ------------------------------------------------------------------------
#       private fcts
## ------------------------------------------------------------------------

def _updateOriginOSAIS(ip):
    global gOriginOSAIS
    if ip=="13.40.45.141":
        gOriginOSAIS="https://opensourceais.com/"
    else:
        gOriginOSAIS="https://opensourceais.com/"

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

    response = requests.post(gOriginOSAIS+"api/v1/public/virtualai/register", headers=headers, data=json.dumps(objParam))

    objRes=response.json()["data"]
    if objRes is None:
        print("COULD NOT REGISTER, stopping it here")
        sys.exit()

    gToken=objRes["token"]
    gSecret=objRes["secret"]
    print("We are REGISTERED")
    return objRes

# Authenticate into OSAIS
def _loginVAI():
    global gToken
    global gSecret
    global gAuthToken

    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(gOriginOSAIS+"api/v1/public/virtualai/login", headers=headers, data=json.dumps({
        "token": gToken,
        "secret": gSecret
    }))

    objRes=response.json()["data"]
    if objRes is None:
        print("COULD NOT LOGIN, stopping it here")
        sys.exit()

    print("We got an authentication token into OSAIS")
    gAuthToken=objRes["authToken"]    
    return objRes

def _getArgs(_args):
    result = []
    for key, value in _args.items():
        if key.startswith("-"):
            result.append(key)
            result.append(value)
    return result

# Upload image to OSAIS 
def _uploadImageToOSAIS(objParam):
    global gAuthToken
    global gOriginOSAIS

    # lets go call OSAIS AI Gateway / or OSAIS itself
    headers = {
        "Content-Type": 'application/json', 
        'Accept': 'text/plain',
        "Authorization": f"Bearer {gAuthToken}"
    }

    if gIsVirtualAI==True:
        api_url=gOriginOSAIS+"api/v1/private/upload"        
        payload = json.dumps(objParam)
        response = requests.post(api_url, headers=headers, data=payload )
        objRes=response.json()
        return objRes    
    return None

## ------------------------------------------------------------------------
#       public fcts
## ------------------------------------------------------------------------

## resetting who this AI is talking to (OSAIS or gateway)
def osais_resetOSAIS(_location):
    global gOriginOSAIS
    gOriginOSAIS=_location
    print("=> This AI is reset to talk to "+gOriginOSAIS+"\r\n")
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
    _osais=f"http://{gIPLocal}:{gPortGateway}/"         ## config for local gateway (local and not virtual)
    if gIsVirtualAI:
        _osais=f"http://{gIPLocal}:{gPortLocalOSAIS}/"  ## config for local OSAIS (local and virtual)
    if gIsDocker:
        _osais=f"https://opensourceais.com/"            ## config for prod OSAIS (remote and virtual)

    osais_resetOSAIS(_osais)

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

    ## notify start
    CredsParam={"engine": gName, "tokenAI": _token, "username": _args.get('-u')}
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
    global gOriginOSAIS
    global gIsVirtualAI
    global gAuthToken
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

    api_url = gOriginOSAIS+"api/v1/public/notify"
    if gIsVirtualAI==True:
        headers["Authorization"]= f"Bearer {gAuthToken}"
        api_url=gOriginOSAIS+"api/v1/private/notify"

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
            _uploadImageToOSAIS(param)
    return objRes


## ------------------------------------------------------------------------
#       Init processing
## ------------------------------------------------------------------------

print("AI ready for processing requests...")

