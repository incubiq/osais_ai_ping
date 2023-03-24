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
#       init app
## ------------------------------------------------------------------------

## init app
APP_ENGINE="ping"
from flask import Flask, request, jsonify
app = Flask(APP_ENGINE)

## ------------------------------------------------------------------------
#       connect the AI with OSAIS
## ------------------------------------------------------------------------

import os
from libOSAISVirtualAI import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_getDirectoryListing, osais_runAI, osais_loadConfig, osais_authenticateAI

gClientToken = os.environ.get('CLIENT_TOKEN')         ## getting the client_token from the docker config (this AI belongs to the client)
gIsVirtualAI=os.environ.get('IS_VIRTUALAI')=="True"   ## is this used as a virtual AI, or a local server used by a gateway?
gIsLocal = os.environ.get('IS_LOCAL')=="True"         ## we are running locally by default, unless Docker config says otherwise 
if os.environ.get("TERM_PROGRAM")=="vscode":          ## local when in debug
    gIsLocal = True
    gIsVirtualAI = True

gConfig=osais_loadConfig(APP_ENGINE)
gPortAI = gConfig["port"]
gVersion = gConfig["version"]
gPortGateway = 3023                         ## port of the local gateway (if configured to run alongside it)?
gPortLocalOSAIS = 3022                      ## port of the local OSAIS (if running on debug)?
gIPLocalOSAIS="0.0.0.0"                     ## IP of the local OSAIS

print("===== Config =====")
print("is Local: "+str(gIsLocal))
print("is Virtual: "+str(gIsVirtualAI))
print("owned by client: "+str(gClientToken))
print("===== /Config =====")

## register and login this virtual AI
osais_initializeAI({
    "clientToken": gClientToken,
    "engine": APP_ENGINE, 
    "port_ai": gPortAI, 
    "port_gateway": gPortGateway, 
    "port_localOSAIS": gPortLocalOSAIS, 
    "ip_local": gIPLocalOSAIS,
    "isLocal": gIsLocal,   
    "isVirtualAI": gIsVirtualAI
})

## ------------------------------------------------------------------------
#       routes for this AI (important ones)
## ------------------------------------------------------------------------

@app.route('/')
def home():
    return jsonify(osais_getInfo())

@app.route('/auth')
def auth():
    return jsonify(osais_authenticateAI())

@app.route('/status')
def status():
    return jsonify(osais_getInfo())

@app.route('/run')
def run():
    from _ping import fn_run
    return osais_runAI(fn_run, request.args)

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
