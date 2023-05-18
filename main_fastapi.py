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

from osais_debug import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_isDocker, osais_getClientID, osais_getDirectoryListing, osais_runAI, osais_authenticateAI, osais_isDebug, osais_authenticateClient, osais_postRequest, osais_downloadImage, osais_uploadFileToS3, osais_downloadFileFromS3
#from osais import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_isDocker, osais_getClientID, osais_getDirectoryListing, osais_runAI, osais_authenticateAI, osais_isDebug, osais_authenticateClient, osais_postRequest, osais_downloadImage, osais_uploadFileToS3, osais_downloadFileFromS3

global gObjClient

## register and login this AI
try:
    env_file=None
    if osais_isDocker()==False:
        env_file="env_local"
    
    ## init the AI and if it's config as a VAI, log is as VAI into OSAIS
    objInit=osais_initializeAI(env_file)
    APP_ENGINE=objInit["engine"]
    gObjClient=objInit["client"]

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
def _warmup(): 
    print("\r\nwill attempt a warm up request...")
    try:
        import time
        from werkzeug.datastructures import MultiDict
        ts=int(time.time())
        sample_args = MultiDict([
            ('-u', 'test_user'),
            ('-uid', str(ts)),
            ('-t', osais_getClientID()),
            ('-cycle', '0'),
            ('-width', '512'),
            ('-height', '512'),
            ('-o', str(ts)+'.jpg'),
            ('-filename', 'clown.jpg'),
            ('-warmup', 'True'),
    #        ('-idir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\input'),
    #        ('-odir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\output'),
    #        ('-orig', 'http://192.168.1.83:3022/'),
        ])
        osais_runAI(fn_run, sample_args)
        return True
    except:
        print("Could not call warm up!\r\n")
        return False

## ------------------------------------------------------------------------
#       init app (fastapi)
## ------------------------------------------------------------------------

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

## warmup
_warmup()

## ------------------------------------------------------------------------
#       routes for uploading / downloading files
## ------------------------------------------------------------------------

@app.post('/upload')
async def upload(file: UploadFile):
  filename = file.filename
  try:
    content = await file.read()
    with open(f"./_input/{filename}", "wb") as f:
        # save locally (to then upload to S3)
        f.write(content)

        # upload to S3
        _filename=osais_uploadFileToS3(f"./_input/{filename}", "input/")

        # return the S3 filename
        return {filename: _filename}
  except Exception as err:
    print("Could not upload file "+filename+"\r\n")
    return {"data": None}

  return HTMLResponse(content=osais_getDirectoryListing("./_input"), status_code=200)

@app.post('/download')
def download(request: Request):
    import urllib.parse
    query_string = request.url.query
    url_parameter = urllib.parse.parse_qs(query_string)['url'][0]
    _image=osais_downloadFileFromS3(url_parameter)
    print("downloaded : "+_image)
    return HTMLResponse(content=osais_getDirectoryListing("./_input"), status_code=200)


## ------------------------------------------------------------------------
#       routes for this AI (important ones)
## ------------------------------------------------------------------------

def _convert_python_to_js(data):
    if isinstance(data, dict):
        return {_convert_python_to_js(key): _convert_python_to_js(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_convert_python_to_js(item) for item in data]
    elif data is None:
        return "null"
    elif data is True:
        return "true"
    elif data is False:
        return "false"
    else:
        return data

@app.get('/')
def home():
    global gObjClient
    config=osais_getInfo()
    config["client"]=gObjClient

    env = Environment(loader=FileSystemLoader('./templates/'))
    template = env.get_template('tpl_form.html')
    _config=_convert_python_to_js(config)
    return HTMLResponse(content=template.render(_config), status_code=200)

@app.get('/status')
def status():
    return {"data":osais_getInfo()}

@app.get('/wakeup')
async def wakeup(request: Request, origin: str):
    import urllib.parse
    _origin=urllib.parse.unquote(urllib.parse.unquote(origin))
    return osais_authenticateAI(_origin)

@app.get('/docker')
def inDocker():
    return {"data": {
            "is_local": os.environ.get('IS_LOCAL'),
            "is_virtualai": os.environ.get('IS_VIRTUALAI'),
            "engine": os.environ.get('ENGINE'),
            "username": os.environ.get("USERNAME")
        }
    }

@app.get('/run')
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
    bRet=_warmup()
    return {"data": bRet}

## ------------------------------------------------------------------------
#       test routes when in DEBUG mode
## ------------------------------------------------------------------------

#if osais_isDebug():
@app.get('/root')
def root():
    return HTMLResponse(content=osais_getDirectoryListing("./"), status_code=200)

@app.get('/input')
def input():
    return HTMLResponse(content=osais_getDirectoryListing("./_input"), status_code=200)

@app.get('/output')
def output():
    return HTMLResponse(content=osais_getDirectoryListing("./_output"), status_code=200)
