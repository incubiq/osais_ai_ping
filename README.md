# OSAIS: AI_PING
A basic python prog that connects AI to OSAIS or OSAIS Gateway. It demonstrates how to integrate any AI into OSAIS for compatibility.

The ai_ping can run as either of those options:
 - a local server (localhost) connected to an OSAIS local gateway
 - a local docker (local ip) connected to an OSAIS local gateway
 - a remote docker (remote ip) connected to OSAIS as a VirtualAI

The ai _ping does not make use of GPU to run, but can request a test on GPU by calling the route /gpu (which will break if no GPU on the hardware running it)

This ai_ping comes in 2 flavours for running in server: flask and fastapi. The final prod version is using the fastapi, mostly for additional ease of compatibility with huggingface deployments.

## Requirements

 1/ Python libs requirement: See All requirements in the Dockerfile ; the requirements.txt is a minimal requirement on top of another setup prepared for AI (including tensorflow etc...)

 2/ it is assumed that two directories /_input  and  /_output  exist and are accessible by the AI. /_input receives the files to process by the AAI before it starts, whereas /_output  receives any file output from the AI.

## BATCH MODE RUN
// to test PING in BATCH mode (not a server), use: runlocal.bat  (it has its entry point with runlocal.py, then making use of _ping.py)


## SERVER IN FLASK MODE
// flask config: when debugging (not in docker), it needs a FLASK app defined to run
//      in windows (when debugging) use :  $env:FLASK_APP="main_flask"
//      in linux / wsl, use :  FLASK_APP="main_flask"

  - go to /python/ai_ping  dir
  - (if necessary) update to latest osais package : pip install -r requirements.txt --upgrade
  - $env:FLASK_APP="main_flask"
  - python -m flask run --host=0.0.0.0 --port=5001   

  // remember this localhost runs on http://192.168.1.108:5001   so this is where we can access it (nowhere else, all other pings may fail)
  // localhost:5001/run... can have some problems with ping....
  // test call:  http://192.168.1.108:5001/run?orig=https%3A%2F%2Fe48c-2a00-23c7-b71c-7b01-1da9-f2a0-e6d7-8738.ngok.io%2F&token=a641d6413a99f8fe50a28f31b456af7ccc38cd34baac87e5f978d140bb0e1fc2&uid=1678711765000&username=http://192.168.1.108:3022&input=1678711765000.jpg&size=512&output=1678711765000.jpg&odir=D%3A%5CWebsites%5Copensourceais%5Cbackend_public%5C_temp%5Coutput%5C&idir=D%3A%5CWebsites%5Copensourceais%5Cbackend_public%5C_temp%5Cinput%5C

## SERVER IN DOCKER FLASK MODE
// flask runs internally on port 5000, and we want to expose it externally on 5001
docker run -d --name ai_ping  --publish 5001:5000 yeepeekoo/public:ai_ping

## SERVER IN FASTAPI MODE
  - uvicorn main_fastapi:app --host 0.0.0.0 --port 5001

## SERVER IN DOCKER FASTAPI MODE
// although fastapi runs internally on port 8000, we already redirect it to 5001. Then we want to expose it externally on 5001
 - for prod on aws: docker run -d --name ai_ping  --expose 5001 --publish 5001:5001 yeepeekoo/public:ai_ping
 - for localhost (debug) test: docker run -d --name ai_ping  --publish 5001:5001 yeepeekoo/public:ai_ping
// note that the docker config forces the AI to run as virtual (local: false) so this is incompatible with localhost callbacks


## PROD SETTINGS / UTILITIES / DEBUG

the docker_env_ping must contain reference to the client owning this virtual AI, and settings for acting as a remote Virtual AI
<
CLIENT_TOKEN=<your client token>
IS_LOCAL=False
IS_VIRTUALAI=True
ENGINE=ping
> 

// on WLS => same (but GPU should work! => add param: --gpus all)

// inspect it
docker logs ai_ping