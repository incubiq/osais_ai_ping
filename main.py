##
## when in docker:
##
##   Put yourself in the src directory
##   Go in Linux : wsl
##   Build the docker image: docker build -t <your creds>:ai_ping .
##   Run doker instance of our latest image: docker run -it -v "$(pwd)/_input:/src/app/_input" -v "$(pwd)/_output:/src/app/_output" --name ai_ping --rm --gpus all --publish 5001:5000 yeepeekoo/my_images:ai_ping
##   Test it: http://localhost:5001/
##
##
## when debug locally:
##
##   Put yourself in the src directory
##   Run with: uvicorn main:app --host 0.0.0.0 --port 5001
##   Test it : http://localhost:5001/
##

## ------------------------------------------------------------------------
#       connect the AI with OSAIS
## ------------------------------------------------------------------------

import sys
import os

from osais_debug import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_getDirectoryListing, osais_runAI, osais_authenticateAI, osais_isLocal
#from osais import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_getDirectoryListing, osais_runAI, osais_authenticateAI, osais_isLocal

## register and login this AI
try:
    APP_ENGINE=osais_initializeAI()
    sys.stdout.flush()

except Exception as err:
    print('CRITICAL: Init OSAIS failed with exception')
    sys.exit(0)

if APP_ENGINE==None:
    print('CRITICAL: Init OSAIS failed')
    sys.exit(0)

## ------------------------------------------------------------------------
#       AI endpoint and warmup
## ------------------------------------------------------------------------

## AI endpoint call
from _ping import fn_run

## Test if this AI works (used for warm-up call)
def _test(): 
    import time
    from werkzeug.datastructures import MultiDict
    ts=int(time.time())
    sample_args = MultiDict([
        ('-u', 'test_user'),
        ('-uid', str(ts)),
        ('-t', 'a641d6413a99f8fe50a28f31b456af7ccc38cd34baac87e5f978d140bb0e1fc2'),
        ('-width', '512'),
        ('-height', '512'),
        ('url_upload', 'http://localhost:3022/assets/clown.jpg'),
        ('-o', str(ts)+'.jpg'),
        ('-local', 'True'),
        ('-warmup', 'True'),
#        ('-idir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\input'),
#        ('-odir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\output'),
#        ('-orig', 'http://192.168.1.83:3022/'),
    ])
    try:
        osais_runAI(fn_run, sample_args)
        return True
    except:
        return False

## warmup
_test()

## ------------------------------------------------------------------------
#       init app (fastapi)
## ------------------------------------------------------------------------

from fastapi import FastAPI, Request
app = FastAPI()

## ------------------------------------------------------------------------
#       routes for this AI (important ones)
## ------------------------------------------------------------------------

@app.get('/')
def home():
    return {"data":osais_getInfo()}

@app.get('/auth')
def auth():
    return {"data":osais_authenticateAI()}

@app.get('/status')
def status():
    return {"data":osais_getInfo()}

@app.get('/docker')
def inDocker():
    return {"data": {
            "is_local": os.environ.get('IS_LOCAL'),
            "is_virtualai": os.environ.get('IS_VIRTUALAI'),
            "engine": os.environ.get('ENGINE'),
            "username": os.environ.get("USERNAME")
        }
    }

@app.get('/run/')
def run(request: Request):
    try:
        osais_runAI(fn_run, request.query_params._dict)
        return {"data": True}
    except:
        return {"data": False}

## ------------------------------------------------------------------------
#       routes for this AI (optional)
## ------------------------------------------------------------------------

@app.get('/gpu')
def gpu():
    return {"data":osais_getHarwareInfo()}

@app.get('/test')
def test():
    bRet=_test()
    return {"data": bRet}

## ------------------------------------------------------------------------
#       test routes when in local mode
## ------------------------------------------------------------------------

if osais_isLocal():
    @app.get('/root')
    def root():
        return osais_getDirectoryListing("./")

    @app.get('/input')
    def input():
        return osais_getDirectoryListing("./_input")

    @app.get('/output')
    def output():
        return osais_getDirectoryListing("./_output")
    