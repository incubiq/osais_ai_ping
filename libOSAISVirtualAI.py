
## ------------------------------------------------------------------------
#       OSAIS python Lib (interface between AIs and OSAIS)
## ------------------------------------------------------------------------

import requests
import schedule
import json
import sys
import base64
from datetime import datetime

from libOSAISTools import getHostInfo, listDirContent, is_running_in_docker, get_external_ip, get_container_ip, get_machine_name, get_os_name, getCudaInfo, downloadImage, start_watch_directory, stop_watch_directory

## ------------------------------------------------------------------------
#       all global vars
## ------------------------------------------------------------------------

gVersionLibOSAIS="1.0.12"       ## version of this library (to keep it latest everywhere)
gUsername=None                  ## user owning this AI (necessary to claim VirtAI regs)

gName=None                      ## name of this AI (name of engine)
gVersion="0.0.0"                ## name of this AI's version (version of engine)
gDescription=None               ## AI's quick description
gOrigin=None                    ## where this AI came from (on internet)
gMachineName=get_machine_name() ## the name of the machine (will change all the time if inside docker, ot keep same if running on local server)
gLastChecked_at=datetime.utcnow()  ## when was this AI last used for processing anything
gLastProcessStart_at=None       ## when was this AI last start event for processing anything

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
gIsScheduled=False              ## do we have a scheduled event running?

## run timmes
gIsBusy=False                   ## True if AI busy processing
gDefaultCost=float(1)           ## default cost value in secs (will get overriden fast, this value is no big deal)
gaProcessTime=[]                ## Array of last x (10/20?) time spent for processed requests 

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

# load the config file into a JSON
def _loadConfig(_name): 
    global gVersion
    global gDescription
    global gOrigin
    global gDefaultCost

    fJSON = open(f'{_name}.json')
    _json = json.load(fJSON)
    gVersion=_json["version"]
    gDescription=_json["description"]
    gOrigin=_json["origin"]
    _cost=_json["default_cost"]
    if _cost!=None:
        gDefaultCost=float(_cost)
    return _json

## get the full AI config, including JSON params and hardware info
def _getFullConfig(_name) :
    global gUsername
    global gPortAI
    global gName
    global gToken
    global gSecret
    global gOriginOSAIS
    global gTokenLocal
    global gSecretLocal
    global gOriginLocalOSAIS
    global gIsVirtualAI
    global gIPLocal
    global gExtIP
 
    _ip=gExtIP
    if gIsVirtualAI:
        _ip=gIPLocal

    _json=_loadConfig(_name)

    objCudaInfo=getCudaInfo()
    gpuName="no GPU"
    if objCudaInfo != 0 and "name" in objCudaInfo and objCudaInfo["name"]:
        gpuName=objCudaInfo["name"]

    return {
        "username": gUsername,
        "os": get_os_name(),
        "gpu": gpuName,
        "machine": get_machine_name(),
        "ip": _ip,
        "port": gPortAI,
        "engine": _json
    }

## init the dafault cost array
def _initializeCost() :
    global gDefaultCost
    global gaProcessTime
    from array import array
    gaProcessTime=array('f', [gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost])

## init the dafault cost array
def _addCost(_cost) :
    global gaProcessTime
    gaProcessTime.insert(0, _cost)
    gaProcessTime.pop()

## init the dafault cost array
def _getAverageCost() :
    global gaProcessTime
    average = sum(gaProcessTime) / len(gaProcessTime)
    return average

## where is the output dir?
def _getOutputDir(_args):
    _output="./_output"
    _tmpO=_args.get('-odir')
    if _tmpO!=None:
        _output=_tmpO
    return _output

## notify the gateway of our AI config file
def _notifyGateway() : 
    global gName
    global gOriginGateway

    headers = {
        "Content-Type": 'application/json', 
        'Accept': 'text/plain',
    }
    objParam=_getFullConfig(gName)

    ## notify gateway
    try:
        response = requests.post(f"{gOriginGateway}api/v1/public/ai/config", headers=headers, data=json.dumps(objParam))
        objRes=response.json()["data"]
        if objRes is None:
            raise ValueError("CRITICAL: could not notify Gateway")

    except Exception as err:
        raise err
    return True

# Register our VAI into OSAIS
def _registerVAI():
    global gName
    global gToken
    global gSecret
    global gOriginOSAIS
    global gTokenLocal
    global gSecretLocal
    global gOriginLocalOSAIS
    global gIsLocal

    headers = {
        "Content-Type": 'application/json', 
        'Accept': 'text/plain',
    }
    objParam=_getFullConfig(gName)

    ## reg with Prod
    if gIsLocal==False:
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
    else:
        try:
            response = requests.post(f"{gOriginLocalOSAIS}api/v1/public/virtualai/register", headers=headers, data=json.dumps(objParam))
            objRes=response.json()["data"]
            if objRes is None:
                print("COULD NOT REGISTER with debug")

            gTokenLocal=objRes["token"]
            gSecretLocal=objRes["secret"]
            print("We are REGISTERED with OSAIS Local (debug)")
        except Exception as err:
            raise err

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

    if gToken!= None:
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

    if gTokenLocal!= None:
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

def osais_getEnv(_filename):
    import os
    global gUsername
    global gIsVirtualAI
    global gIsLocal
    global gName
    gUsername = os.environ.get('USERNAME')                ## getting the username from the docker config (this AI belongs to the User)
    gIsVirtualAI=os.environ.get('IS_VIRTUALAI')=="True"   ## is this used as a virtual AI, or a local server used by a gateway?
    gIsLocal = os.environ.get('IS_LOCAL')=="True"         ## we are running locally by default, unless Docker config says otherwise 
    if os.environ.get("TERM_PROGRAM")=="vscode":          ## local when in debug
        with open(_filename, "r") as f:
            content = f.read()
        variables = content.split("\n")
        for var in variables:
            if var!="":
                key, value = var.split("=")
                if key == "USERNAME":
                    gUsername = value
                elif key == "IS_LOCAL":
                    gIsLocal = (value=="True")
                elif key == "IS_VIRTUALAI":
                    gIsVirtualAI = (value=="True")
                elif key == "ENGINE":
                    gName = value
    return {
        "username": gUsername,
        "isLocal": gIsLocal,
        "isVirtualAI": gIsVirtualAI,
        "name": gName
    }

## load the config of this AI
def osais_loadConfig(_name): 
    return _loadConfig(_name)

## resetting who this AI is talking to (OSAIS prod and dbg)
def osais_resetOSAIS(_locationProd, _localtionDebug):
    global gOriginOSAIS
    global gOriginLocalOSAIS
    gOriginOSAIS=_locationProd
    gOriginLocalOSAIS=_localtionDebug
    if _locationProd!=None:
        print("=> This AI is reset to talk to PROD "+gOriginOSAIS)
    if _localtionDebug!=None:
        print("=> This AI is reset to talk to DEBUG "+gOriginLocalOSAIS+"\r\n")
    return True

def osais_resetGateway(_localGateway):
    global gOriginGateway
    gOriginGateway=_localGateway
    try:
        _notifyGateway()
    except Exception as err:
        raise err
    
    print("=> This AI is reset to talk to Gateway "+_localGateway)
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
    global gUsername
    gUsername=params["username"]

    ## where is OSAIS for us then?
    global gExtIP
    global gIsDocker
    global gOriginGateway
    global gAuthToken
    global gAuthTokenLocal
    global gOriginOSAIS
    global gOriginLocalOSAIS

    print("\r\n===== Config =====")
    print("is Local: "+str(gIsLocal))
    print("is Virtual: "+str(gIsVirtualAI))
    print("owned by client: "+str(gUsername))
    print("===== /Config =====\r\n")


    ## put back local IP where it can be called...
    if gIsLocal:
        gIPLocal=get_container_ip()

    gOriginGateway=f"http://{gIPLocal}:{gPortGateway}/"         ## config for local gateway (local and not virtual)

    if gIsVirtualAI:
        if gIsLocal:
            osais_resetOSAIS(None, f"http://{gIPLocal}:{gPortLocalOSAIS}/")
        else:
            osais_resetOSAIS("https://opensourceais.com/", None)
        try:
            osais_authenticateAI()
        except Exception as err:
            print("=> CRITICAL: Could not connect virtual AI "+gName+ " to OSAIS")

        if gAuthToken!=None:
            print("=> Running "+gName+" AI as a virtual AI connected to: "+gOriginOSAIS)
        if gAuthTokenLocal!=None:
            print("=> Running "+gName+" AI as a virtual AI connected to: "+gOriginLocalOSAIS)
    else:
        try:
            osais_resetGateway(gOriginGateway)
            print("=> Running "+gName+" AI as a server connected to local Gateway "+gOriginGateway)
        except Exception as err:
            print("CRITICAL: could not notify Gateway at "+gOriginGateway)

    ## init default cost
    _initializeCost()

    print("\r\n")
    return True

## info about this AI
def osais_getInfo() :
    global gExtIP
    global gPortAI
    global gName
    global gVersion
    global gIsDocker
    global gMachineName
    global gUsername
    global gIsBusy
    global gLastProcessStart_at
    global gLastChecked_at

    objConf=_getFullConfig(gName)

    return {
        "name": gName,
        "version": gVersion,
        "location": f"{gExtIP}:{gPortAI}/",
        "isRunning": True,    
        "isDocker": gIsDocker,    
        "lastActive_at": gLastChecked_at,
        "lastProcessStart_at": gLastProcessStart_at,
        "machine": gMachineName,
        "owner": gUsername, 
        "isAvailable": (gIsBusy==False),
        "averageResponseTime": _getAverageCost(), 
        "json": objConf["engine"]
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
    global gIsScheduled
    
    Resp={"data": None}
    if gIsVirtualAI:

        try:
            resp= _registerVAI()
            resp=_loginVAI()
        except Exception as err:
            raise err
        
        # Run the scheduler
        if gIsScheduled==False:
            gIsScheduled=True
            schedule.every().day.at("10:30").do(_loginVAI)

    return resp

def osais_runAI(*args):
    global gIsBusy

    fn_run=args[0]
    _args=args[1]

    gIsBusy=True
    beg_date = datetime.utcnow()

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
    
    ## processing accepted
    global gLastProcessStart_at
    gLastProcessStart_at=datetime.utcnow()

    global gName 
    gAProcessed.append(_uid)
    _token=_args.get('-t')

    isLocal=(_args.get('-local')=="True")

    ## notify start
    CredsParam={"engine": gName, "tokenAI": _token, "username": _args.get('-u'), "isLocal": isLocal}
    MorphingParam={"uid": _uid, "cycle": 0, "filename": _input}
    StageParam={"stage": AI_PROGRESS_AI_STARTED, "descr": "AI is ready to start"}
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## start watch file creation
    _output=_getOutputDir(_args)
    ## start_watch_directory(_output, osais_onNotifyFileCreated)

    ## run the AI
    response=None
    if len(args)==2:
        response=fn_run(aFinalArg)
    else:
        if len(args)==3:
            response=fn_run(aFinalArg, args[2])
        else:
            response=fn_run(aFinalArg, args[2], args[3])

    ## stop watch file creation
    stop_watch_directory()

    gIsBusy=False
    end_date = datetime.utcnow()
    cost = (end_date - beg_date).total_seconds()
    _addCost(cost)

    ## notify end
    StageParam={"stage": AI_PROGRESS_AI_STOPPED,  "descr": "end of AI job...", "cost": cost}
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## default OK response if the AI does not send any
    if response==None:
        response=True
    return response

def osais_onNotifyFileCreated(_filename):
    print("notified file Created ("+_filename+")")
    return True

# Direct Notify OSAIS 
def osais_notify(CredParam, MorphingParam, StageParam):
    global gIPLocal
    global gPortGateway
    global gOriginOSAIS
    global gOriginLocalOSAIS
    global gIsVirtualAI
    global gAuthToken
    global gAuthTokenLocal
    global gLastChecked_at
    gLastChecked_at = datetime.utcnow()

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

    if "cost" in StageParam:
        objParam["response"]["cost"]= str(StageParam["cost"])
    
    response = requests.post(api_url, headers=headers, data=json.dumps(objParam) )
    objRes=response.json()

    if StageParam["stage"]==AI_PROGRESS_DONE_IMAGE:
        if gIsVirtualAI==True:
            _dir=MorphingParam["odir"]
            if _dir==None:
                _dir="./_output/"
            _dirImage=_dir+_filename

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
    _initImg="default"
    if hasattr(_args, 'init_image') and _args.init_image:
        _initImg=_args.init_image
    return {"uid": _args.uid, "cycle": _args.cycle, "filename":_initImg, "odir":_args.outdir}

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

print("\r\nPython OSAIS Lib is loaded...")


