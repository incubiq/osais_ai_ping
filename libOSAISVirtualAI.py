
## ------------------------------------------------------------------------
#       OSAIS python Lib (interface between AIs and OSAIS)
## ------------------------------------------------------------------------

import requests
import schedule
import json
import sys
import base64
from datetime import datetime
import argparse

from libOSAISTools import getHostInfo, listDirContent, is_running_in_docker, get_external_ip, get_container_ip, get_machine_name, get_os_name, getCudaInfo, downloadImage, start_observer_thread, clearOldFiles, start_notification_thread

## ------------------------------------------------------------------------
#       all global vars
## ------------------------------------------------------------------------

gVersionLibOSAIS="1.0.15"       ## version of this library (to keep it latest everywhere)
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
gIPLocal=get_container_ip()     ## where this AI can be accessed locally
gPortAI=None                    ## port where this AI is accessed (will be set by AI config)
gPortGateway=3023               ## port where the gateway can be accessed
gPortLocalOSAIS=3022            ## port where a local OSAIS can be accessed

## virtual AI / local /docker ?
gIsDocker=is_running_in_docker()   ## are we running in a Docker?
gIsVirtualAI=False              ## are we working as a Virtual AI config?
gIsLocal=False                  ## are we working locally (localhost server)?

## temp cache
gAProcessed=[]                  ## all token being sent to processing (never call twice for same)
gIsScheduled=False              ## do we have a scheduled event running?

## run times
gIsWarmup=False                 ## True if the request was a warmup one (not a true one from client)
gIsBusy=False                   ## True if AI busy processing
gDefaultCost=float(1)           ## default cost value in secs (will get overriden fast, this value is no big deal)
gaProcessTime=[]                ## Array of last x (10/20?) time spent for processed requests 

## processing specifics
gArgsOSAIS=None                 ## the args passed to the AI which are specific to OSAIS for sending notifications

## when running as vAI
gInputDir="./_input/"
gOutputDir="./_output/"

AI_PROGRESS_ERROR=-1
AI_PROGRESS_IDLE=0
AI_PROGRESS_ARGS=1
AI_PROGRESS_AI_STARTED=2
AI_PROGRESS_INIT_IMAGE=3
AI_PROGRESS_DONE_IMAGE=4
AI_PROGRESS_AI_STOPPED=5

## ------------------------------------------------------------------------
#       Load config
## ------------------------------------------------------------------------

# load the config file into a JSON
def _loadConfig(_name): 
    global gVersion
    global gDescription
    global gOrigin
    global gDefaultCost

    _json = None
    _dirFile=None
    try:
        from pathlib import Path
        current_working_directory = Path.cwd()
        _dirFile=f'{current_working_directory}/{_name}.json'
        fJSON = open(_dirFile)
        _json = json.load(fJSON)
    except Exception as err:
        print(f'CRITICAL: No config file {_dirFile}')
        sys.exit()

    gVersion=_json["version"]
    gDescription=_json["description"]
    gOrigin=_json["origin"]
    _cost=_json["default_cost"]
    if _cost!=None:
        gDefaultCost=float(_cost)

    return _json

# get the full AI config, including JSON params and hardware info
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

## PUBLIC - load the config of this AI
def osais_loadConfig(_name): 
    return _loadConfig(_name)

## PUBLIC - Get env from file (local or docker)
def osais_getEnv(_filename):
    global gUsername
    global gIsVirtualAI
    global gIsLocal
    global gName

    ## read env from config file
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

## ------------------------------------------------------------------------
#       cost calculation
## ------------------------------------------------------------------------

# init the dafault cost array
def _initializeCost() :
    global gDefaultCost
    global gaProcessTime
    from array import array
    gaProcessTime=array('f', [gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost,gDefaultCost])

# init the dafault cost array
def _addCost(_cost) :
    global gIsWarmup
    global gaProcessTime
    if gIsWarmup==False:
        gaProcessTime.insert(0, _cost)
        gaProcessTime.pop()

# init the dafault cost array
def _getAverageCost() :
    global gaProcessTime
    average = sum(gaProcessTime) / len(gaProcessTime)
    return average

## ------------------------------------------------------------------------
#       args processing
## ------------------------------------------------------------------------

# where is the output dir?
def _getOutputDir():
    global gArgsOSAIS
    global gOutputDir

    if gArgsOSAIS!=None:
        return gArgsOSAIS.outdir
    return gOutputDir

# receives args from request and put them in a array for processing
def _getArgs(_args):
    aResult = []
    for key, value in _args.items():
        if key.startswith("-"):
            aResult.append(key)
            aResult.append(value)
    return aResult

# give new args 
def _argsFromFilter(_originalArgs, _aFilter, _bKeep):
    from werkzeug.datastructures import MultiDict
    _dict = MultiDict([])
    for i, arg in enumerate(_originalArgs):
        if _bKeep:
            if arg in _aFilter and i < len(_originalArgs) - 1:
                _dict.add(arg, _originalArgs[i+1])
        else:
            if arg not in _aFilter and i < len(_originalArgs) - 1:
                _dict.add(arg, _originalArgs[i+1])
    
    _args=_getArgs(_dict)
    return _args

## ------------------------------------------------------------------------
#       System info
## ------------------------------------------------------------------------

def _clearDir():
    clearOldFiles(gInputDir)
    clearOldFiles(gOutputDir)

## PUBLIC - info about harware this AI is running on
def osais_getHarwareInfo() :
    return getHostInfo()

## PUBLIC - get list of files in a dir (check what was generated)
def osais_getDirectoryListing(_dir) :
    return listDirContent(_dir)

## PUBLIC - info about this AI
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

## ------------------------------------------------------------------------
#       connect to Gateway
## ------------------------------------------------------------------------

# notify the gateway of our AI config file
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
        print("CRITICAL: "+err.msg)
        raise err
    return True

## PUBLIC - Reset connection to local gateway
def osais_resetGateway(_localGateway):
    global gOriginGateway
    gOriginGateway=_localGateway
    try:
        _notifyGateway()
    except Exception as err:
        print("CRITICAL: "+err.msg)
        raise err
    
    print("=> This AI is reset to talk to Gateway "+_localGateway)
    return True

## ------------------------------------------------------------------------
#       authenticate into OSAIS as virtual AI
## ------------------------------------------------------------------------

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
            print("CRITICAL: "+err.msg)
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
            print("CRITICAL: "+err.msg)
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
            print("CRITICAL: "+err.msg)
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


## PUBLIC - Authenticate the Virtual AI into OSAIS
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
            print("CRITICAL: "+err.msg)
            raise err
        
        # Run the scheduler
        if gIsScheduled==False:
            gIsScheduled=True
            schedule.every().day.at("10:30").do(_loginVAI)

    return resp

## ------------------------------------------------------------------------
#       Run the AI
## ------------------------------------------------------------------------

## PUBLIC - parse args for OSAIS (not those for AI)
def osais_initParser(aArg):
    global gArgsOSAIS
    global gInputDir
    global gOutputDir
    global gIsWarmup

    # Create the parser
    vq_parser = argparse.ArgumentParser(description='Arg parser init by OSAIS')

    # Add the AI Gateway / OpenSourceAIs arguments
    vq_parser.add_argument("-orig",  "--origin", type=str, help="AI Gateway server origin", default=f"http://{gIPLocal}:{gPortGateway}/" , dest='OSAIS_origin')     ##  this is for comms with AI Gateway
    vq_parser.add_argument("-t",  "--token", type=str, help="OpenSourceAIs token", default="0", dest='tokenAI')               ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-u",  "--username", type=str, help="OpenSourceAIs username", default="", dest='username')       ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-uid",  "--unique_id", type=int, help="Unique ID of this AI session", default=0, dest='uid')    ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-odir", "--outdir", type=str, help="Output directory", default=gOutputDir, dest='outdir')
    vq_parser.add_argument("-idir", "--indir", type=str, help="input directory", default=gInputDir, dest='indir')
    vq_parser.add_argument("-local", "--islocal", type=bool, help="is local or prod?", default=False, dest='isLocal')
    vq_parser.add_argument("-cycle", "--cycle", type=int, help="cycle", default=0, dest='cycle')
    vq_parser.add_argument("-filename", "--filename", type=str, help="filename", default="default", dest='filename')
    vq_parser.add_argument("-warmup", "--warmup", type=bool, help="warmup", default=False, dest='warmup')

    gArgsOSAIS = vq_parser.parse_args(aArg)
    gIsWarmup=gArgsOSAIS.warmup
    return True

## PUBLIC - run the AI (at least try)
def osais_runAI(*args):
    global gIsBusy
    global gAProcessed
    global gName 
    global gLastProcessStart_at

    ## get args
    fn_run=args[0]
    _args=args[1]

    ## do not process twice same uid
    _uid=_args.get('-uid')
    if _uid in gAProcessed:
        return  "not processing, already tried..."

    ## start time
    gIsBusy=True
    beg_date = datetime.utcnow()

    ## reprocess AI args
    aArgForparserAI=_getArgs(_args)
    args_ExclusiveOSAIS=['-orig', '-t', '-u', '-uid', '-local', '-cycle', '-warmup']
    aArgForparserAI=_argsFromFilter(aArgForparserAI, args_ExclusiveOSAIS, False)

    ## process the filename passed in dir (case localhost / AI Gateway), or download file from URL (case AI running as Virtual AI)
    _input=None
    _filename=_args.get('-filename')
    _urlUpload=_args.get('url_upload')
    if not _filename and _urlUpload:
        try:
            _input=downloadImage(_urlUpload)
            if _input:
                aArgForparserAI.append("-filename")
                aArgForparserAI.append(_input)
            else:
                ## min requirements
                print("no image to process")
                return "input required"
        except Exception as err:
            print("CRITICAL: "+err.msg)
            raise err
    
    ## Init OSAIS Params (from all args, keep only those for OSAIS)
    aArgForParserOSAIS=_getArgs(_args)
    args_ExclusiveOSAIS.append('-odir')
    args_ExclusiveOSAIS.append('-idir')
    aArgForParserOSAIS=_argsFromFilter(aArgForParserOSAIS, args_ExclusiveOSAIS, True)
    osais_initParser(aArgForParserOSAIS)

    if gIsWarmup:
        print("\r\n=> Warming up... \r\n")
    else:
        print("\r\n=> before run: processed args from url: "+str(aArgForparserAI)+"\r\n")

    ## processing accepted
    gLastProcessStart_at=datetime.utcnow()
    gAProcessed.append(_uid)

    ## notify OSAIS (start)
    CredsParam=getCredsParams()
    MorphingParam=getMorphingParams()
    StageParam=getStageParams(AI_PROGRESS_AI_STARTED, 0)
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## start watch file creation
    _output=_getOutputDir()
    watch_directory(_output, osais_onNotifyFileCreated, _args)

    ## Notif OSAIS
    StageParam=getStageParams(AI_PROGRESS_INIT_IMAGE, 0)
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## run AI
    response=None
    try:
        if len(args)==2:
            response=fn_run(aArgForparserAI)
        else:
            if len(args)==3:
                response=fn_run(aArgForparserAI, args[2])
            else:
                response=fn_run(aArgForparserAI, args[2], args[3])
    except Exception as err:
        print("CRITICAL: "+err.msg)
        raise err

    ## calculate cost
    gIsBusy=False
    end_date = datetime.utcnow()
    cost = (end_date - beg_date).total_seconds()
    _addCost(cost)

    ## notify end
    StageParam=getStageParams(AI_PROGRESS_AI_STOPPED, cost)
    osais_notify(CredsParam, MorphingParam , StageParam)

    ## default OK response if the AI does not send any
    if response==None:
        response=True
    return response

## ------------------------------------------------------------------------
#       get formatted params from AI current state
## ------------------------------------------------------------------------

def getCredsParams() :
    global gName
    global gArgsOSAIS
    return {
        "engine": gName, 
        "tokenAI": gArgsOSAIS.tokenAI,
        "username": gArgsOSAIS.username,
        "isLocal": gArgsOSAIS.isLocal
    } 

def getMorphingParams() :
    global gArgsOSAIS
    return {
        "uid": gArgsOSAIS.uid,
        "cycle": gArgsOSAIS.cycle,
        "filename": gArgsOSAIS.filename, 
        "odir": _getOutputDir()
    }

def getStageParams(_stage, _cost) :
    global gArgsOSAIS
    if _stage==AI_PROGRESS_ARGS:
        return {"stage": AI_PROGRESS_AI_STARTED, "descr":"Just parsed AI params"}
    if _stage==AI_PROGRESS_ERROR:
        return {"stage": AI_PROGRESS_AI_STOPPED, "descr":"AI stopped with error"}
    if _stage==AI_PROGRESS_AI_STARTED:
        return {"stage": AI_PROGRESS_AI_STARTED, "descr":"AI started"}
    if _stage==AI_PROGRESS_AI_STOPPED:
        return {"stage": AI_PROGRESS_AI_STOPPED, "descr":"AI stopped", "cost": _cost}
    if _stage==AI_PROGRESS_INIT_IMAGE:
        return {"stage": AI_PROGRESS_INIT_IMAGE, "descr":"destination image = "+gArgsOSAIS.filename}
    if _stage==AI_PROGRESS_DONE_IMAGE:
        return {"stage": AI_PROGRESS_DONE_IMAGE, "descr":"copied input image to destination image"}
    return {"stage": AI_PROGRESS_ERROR, "descr":"error"}

## ------------------------------------------------------------------------
#       Notifications to Gateway / OSAIS
## ------------------------------------------------------------------------

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

def osais_onNotifyFileCreated(_dir, _filename, _args):
    gArgsOSAIS.filename=_filename
    _stageParam=getStageParams(AI_PROGRESS_DONE_IMAGE, 0)
    _morphingParam=getMorphingParams()
    _credsParam=getCredsParams()
    osais_notify(_credsParam, _morphingParam, _stageParam)            # OSAIS Notification
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
    global gIsWarmup

    ## no notification of warmup
    if gIsWarmup:
        return None
    
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
                _dir=gOutputDir
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

## ------------------------------------------------------------------------
#       Init processing
## ------------------------------------------------------------------------

## PUBLIC - resetting who this AI is talking to (OSAIS prod and dbg)
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

## PUBLIC - Init the Virtual AI
def osais_initializeAI():
    global gIsDocker
    global gIsLocal
    global gIsVirtualAI
    global gUsername
    global gName
    global gPortAI
    global gVersion
    global gPortGateway
    global gPortLocalOSAIS
    global gIPLocal
    global gExtIP
    global gOriginGateway
    global gAuthToken
    global gAuthTokenLocal
    global gOriginOSAIS
    global gOriginLocalOSAIS

    ## load env 
    _envFile="env_local"
    if gIsDocker:
        _envFile="env_docker"
        print("\r\n=> in Docker\r\n")
    else:
        print("\r\n=> NOT in Docker\r\n")        
    obj=osais_getEnv(_envFile)
    gIsLocal=obj["isLocal"]
    gIsVirtualAI=obj["isVirtualAI"]
    gUsername=obj["username"]
    gName=obj["name"]

    ## from env, load AI config
    gConfig=osais_loadConfig(gName)
    gPortAI = gConfig["port"]
    gVersion = gConfig["version"]

    print("\r\n===== Config =====")
    print("is Local: "+str(gIsLocal))
    print("is Virtual: "+str(gIsVirtualAI))
    print("owned by client: "+str(gUsername))
    print("===== /Config =====\r\n")

    ## make sure we have a config file
    _loadConfig(gName)

    ## where is OSAIS for us then?
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
            return None

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
            return None

    ## init default cost
    _initializeCost()

    print("\r\n")
    return gName

## ------------------------------------------------------------------------
#       Starting point of Lib
## ------------------------------------------------------------------------

# Multithreading for observers
watch_directory=start_observer_thread(_getOutputDir(), osais_onNotifyFileCreated, None)     

#cleaning dir every 10min
schedule.every(10).minutes.do(_clearDir)

print("\r\nPython OSAIS Lib is loaded...")


