# OSAIS: AI_PING
A basic python prog that connects AI to OSAIS or OSAIS Gateway. It demonstrates how to integrate any AI into OSAIS for compatibility.

The ai_ping can run as either of those options:
 - a local server (localhost) connected to an OSAIS local gateway
 - a local docker (local ip) connected to an OSAIS local gateway
 - a remote docker (remote ip) connected to OSAIS as a VirtualAI

The ai _ping does not make use of GPU to run, but can request a test on GPU by calling the route /gpu (which will break if no GPU on the hardware running it)

## Requirements

 1/ this image uses our ai_base image, which contains all minimal and usual python lib requirements for running tensorflow

 2/ it is assumed that two directories /_input  and  /_output  exist and are accessible by the AI. /_input receives the files to process by the AI before it starts, whereas /_output  receives any file output from the AI.

## SERVER IN FASTAPI MODE
  - uvicorn main:app --host 0.0.0.0 --port 5001

## SERVER IN DOCKER FASTAPI MODE
// although fastapi runs internally on port 8000, we already redirect it to 5001. Then we want to expose it externally on 5001
 - for prod on aws: docker run -d --name ai_ping  --expose 5001 --publish 5001:5001 yeepeekoo/public:ai_ping
 - for localhost (debug) test: docker run -d --name ai_ping  --publish 5001:5001 yeepeekoo/public:ai_ping
// note that the docker config forces the AI to run as virtual (local: false) so this is incompatible with localhost callbacks

## PROD SETTINGS / UTILITIES / DEBUG

the docker_env_ping must contain:
 - your OSAIS username
 - your Virtual AI ID (which is linked to your username)

<
USERNAME=4ebexxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3f5605f3a
VAI_ID=6e77xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx6e4370
VAI_SECRET=dc9b83c4cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx23c9828
> 

// on WLS => same (but GPU should work! => add param: --gpus all)

// inspect it
docker logs ai_ping