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
#       all global vars
## ------------------------------------------------------------------------

gPortAI = 5001
gPortGateway = 3023
gPortLocalOSAIS = 3022
gIPLocalOSAIS="192.168.1.83"

## ------------------------------------------------------------------------
#       connect the AI with OSAIS
## ------------------------------------------------------------------------

## register and login this virtual AI
from libOSAISVirtualAI import osais_initializeAI, osais_getInfo, osais_getHarwareInfo, osais_getDirectoryListing, osais_runAI
osais_initializeAI({
    "engine": APP_ENGINE, 
    "port_ai": gPortAI, 
    "port_gateway": gPortGateway, 
    "port_localOSAIS": gPortLocalOSAIS, 
    "ip_local": gIPLocalOSAIS,
    "isLocal": False,           ## change this to run from external IP
    "isVirtualAI": True         ## change this to run alongside AI Gateway
})

## ------------------------------------------------------------------------
#       routes for this AI (important ones)
## ------------------------------------------------------------------------

@app.route('/')
def home():
    return jsonify(osais_getInfo())

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
