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
#       Use BASE AI 
## ------------------------------------------------------------------------

import sys
sys.path.insert(0, '../osais_ai_base')

## ensure we have the latest files
from main_init import osais_copyBaseFiles
osais_copyBaseFiles()

## now point to latest source and start APP...
sys.path.remove('../osais_ai_base')
sys.path.insert(0, './_osais')
from main_fastapi import app
