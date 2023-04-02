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
##   Set env var once:  $env:FLASK_APP="flask_5000"
##   Run with: python -m flask run --host=0.0.0.0 --port=5001
##   Test it : http://localhost:5001/
##

## ------------------------------------------------------------------------
#       init config
## ------------------------------------------------------------------------

# select env file 
import os
import sys

## docker of local?
def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

if is_docker():
    _envFile="env_docker"
    print("\r\n=> in Docker\r\n")
else:
    print("\r\n=> NOT in Docker\r\n")
    _envFile="env_local"

## ------------------------------------------------------------------------
#       connect the AI with OSAIS
## ------------------------------------------------------------------------

from libOSAISVirtualAI import osais_getEnv, osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_getDirectoryListing, osais_runAI, osais_loadConfig, osais_authenticateAI

## get input param from env
obj=osais_getEnv(_envFile)
gIsLocal=obj["isLocal"]
gIsVirtualAI=obj["isVirtualAI"]
gUsername=obj["username"]
APP_ENGINE=obj["name"]

## load the AI params
gConfig=osais_loadConfig(APP_ENGINE)
gPortAI = gConfig["port"]
gVersion = gConfig["version"]

## location of OSAIS gateway / debug
gPortGateway = 3023                         ## port of the local gateway (if configured to run alongside it)?
gPortLocalOSAIS = 3022                      ## port of the local OSAIS (if running on debug)?
gIPLocalOSAIS="0.0.0.0"                     ## IP of the local OSAIS (will be overwritten at init)

## register and login this AI
if osais_initializeAI({
    "username": gUsername,
    "engine": APP_ENGINE, 
    "port_ai": gPortAI, 
    "port_gateway": gPortGateway, 
    "port_localOSAIS": gPortLocalOSAIS, 
    "ip_local": gIPLocalOSAIS,
    "isLocal": gIsLocal,   
    "isVirtualAI": gIsVirtualAI
}) == False:
    sys.exit(0)

## ------------------------------------------------------------------------
#       init app (flask)
## ------------------------------------------------------------------------

from flask import Flask, request, jsonify
app = Flask(APP_ENGINE)

## ------------------------------------------------------------------------
#       routes for this AI (important ones)
## ------------------------------------------------------------------------

@app.route('/')
def home():
    return jsonify({"data":osais_getInfo()})

@app.route('/auth')
def auth():
    return jsonify({"data": osais_authenticateAI()})

@app.route('/status')
def status():
    return jsonify({"data": osais_getInfo()})

@app.route('/run')
def run():
    from _ping import fn_run
    osais_runAI(fn_run, request.args)
    return jsonify({"data": True})

## ------------------------------------------------------------------------
#       routes for this AI (optional)
## ------------------------------------------------------------------------

@app.route('/gpu')
def gpu():
    return jsonify(osais_getHarwareInfo())

@app.route('/root')
def root():
    return osais_getDirectoryListing("./")

@app.route('/input')
def input():
    return osais_getDirectoryListing("./_input")

@app.route('/output')
def output():
    return osais_getDirectoryListing("./_output")

@app.route('/test')
def test():
    import time
    from werkzeug.datastructures import MultiDict
    ts=int(time.time())
    sample_args = MultiDict([
        ('-u', 'http://192.168.1.83:3022'),
        ('-uid', str(ts)),
        ('-t', 'a641d6413a99f8fe50a28f31b456af7ccc38cd34baac87e5f978d140bb0e1fc2'),
        ('-width', '512'),
        ('-height', '512'),
        ('url_upload', 'http://192.168.1.83:3022/uploads/client/clown.jpg'),
        ('-o', str(ts)+'.jpg'),
        ('-local', 'True'),
        ('-idir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\input'),
        ('-odir', 'D:\\Websites\\opensourceais\\backend_public\\_temp\\output'),
        ('-orig', 'http://192.168.1.83:3022/'),
    ])
    from _ping import fn_run
    osais_runAI(fn_run, sample_args)
    return jsonify({"data": True})
