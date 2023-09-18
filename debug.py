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
#       Debug our app
## ------------------------------------------------------------------------

import sys
import uvicorn
sys.path.insert(0, '../osais_ai_base')

if __name__ == "__main__":
    from main_fastapi import app, initializeApp
#    uvicorn.run(main_fastapi.app, host="0.0.0.0", port=5001)
    initializeApp("env_vai")
