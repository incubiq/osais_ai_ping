# OSAIS: AI_PING
A basic python prog that connects AI to OSAIS or OSAIS Gateway. It demonstrates how to integrate any AI into OSAIS for compatibility.

The ai_ping can run as either of those options:
 - a local server (localhost) connected to an OSAIS local gateway
 - a local docker (local ip) connected to an OSAIS local gateway
 - a remote docker (remote ip) connected to OSAIS as a VirtualAI

The ai _ping does not make use of GPU to run, but can request a test on GPU by calling the route /gpu (which will break if no GPU on the hardware running it)

## Requirements

 1/ Python libs requirement: See All requirements in the Dockerfile ; the requirements.txt is a minimal requirement on top of another setup prepared for AI (including tensorflow etc...)

 2/ it is assumed that two directories /_input  and  /_output  exist and are accessible by the AI. /_input receives the files to process by the AAI before it starts, whereas /_output  receives any file output from the AI.

## BATCH MODE RUN
// to test PING in BATCH mode (not a server), use: runlocal.bat  (it has its entry point with runlocal.py, then making use of _ping.py)

## SERVER MODE RUN
// the python servers are built with FLASK ; when debugging (not in docker), it needs a FLASK app defined to run
// in windows (when debugging) use :  $env:FLASK_APP="flask_5000"
// in linux / wsl, use :  FLASK_APP="flask_5000"
// to run PING in local server mode (localhost:5001)
  - go to the source dir
  - $env:FLASK_APP="flask_5000"
  - python -m flask run --host=0.0.0.0 --port=5001   

  // this localhost may run on http://<192.168.1.108>:5001   so this is where we can access it (nowhere else, all other pings fail)
  // localhost:5001/run... can have some problems with access from other local servers, so we prefer an IP....

## DOCKER MODE (SERVER) RUN
docker build -t <your_repo>:ai_ping .
docker push <your_repo>:ai_ping

// on windows
docker run -it -v "$(pwd)/_input:/src/app/_input" -v "$(pwd)/_output:/src/app/_output" --name ai_ping --rm --publish 5001:5000 yeepeekoo/my_images:ai_ping

// on WLS => same (but GPU should work! => add param: --gpus all)
