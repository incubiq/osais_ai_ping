# OSAIS: AI_PING
A basic python prog that connects AI to OSAIS or OSAIS Gateway. It demonstrates how to integrate any AI into OSAIS for compatibility.

This AI can run as either of those options:
 - a local server (localhost) connected to an OSAIS local gateway
 - a local docker (local ip) connected to an OSAIS local gateway
 - a remote docker (remote ip) connected to OSAIS as a VirtualAI

AI general attributes
 - Origin: https://github.com/incubiq/osais_ai_ping
 - Runs on port: 5001  (below referenced as <port>)
 - AI internal name: ai_ping  (below referenced as <engine>)
 - Use CPU? : yes
 - Use GPU? : no
 - Access to AI main page: <ip>:<port>  (where <ip> is where the AI is run from)

## Requirements

 - this image uses our ai_base image, which contains all minimal and usual python lib requirements for running tensorflow

 - it is assumed that two directories /_input  and  /_output  exist and are accessible by the AI. /_input receives the files to process by the AI before it starts, whereas /_output  receives any file output from the AI.

## LOCAL SERVER IN FASTAPI MODE
 - uvicorn main:app --host 0.0.0.0 --port <port>

## SERVER IN DOCKER FASTAPI MODE
Although fastapi runs internally on port 8000, we already redirect it to <port>. Then we want to expose it externally on <port>

 - for prod on aws (this will run the AI as a Virtual AI): 
    docker run -d --name <engine> --env-file env_vai --expose <port> --publish <port>:<port> yeepeekoo/public:<engine>

 - for localhost test (this will run tha AI as a slave to the local AI gateway): 
    docker run -d --name <engine> --env-file env_local --publish <port>:<port> yeepeekoo/public:<engine>

## PROD SETTINGS / UTILITIES / DEBUG

The env file for using the AI as a slave to an AI gateway (env_local) must contain:
 - your OSAIS username

<
USERNAME=4ebexxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3f5605f3a
> 

The env file for using the AI as a Virtual AI (env_vai) must contain:
 - your OSAIS username
 - your Virtual AI ID (which is linked to your username)

<
USERNAME=4ebexxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3f5605f3a
VAI_ID=6e77xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx6e4370
VAI_SECRET=dc9b83c4cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx23c9828
> 


To inspect a running AI:  docker logs <engine>
