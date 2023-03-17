
##
##      Entry of the AI_PING prog
##
##          - parse args
##          - do ping (ie nothing...)
##

import os
import sys
import platform
import shutil

absFilePath = os.path.abspath(__file__)                
fileDir = os.path.dirname(os.path.abspath(__file__))
root=os.path.join(fileDir, '..') 
sys.path.append(root) 

# need to include OSAIS python lib
from libOSAISVirtualAI import osais_notify, osais_getInfo, getCredsParams, getMorphingParams, getStageParams
from libOSAISVirtualAI import AI_PROGRESS_ERROR, AI_PROGRESS_AI_STARTED, AI_PROGRESS_INIT_IMAGE, AI_PROGRESS_DONE_IMAGE, AI_PROGRESS_AI_STOPPED

## init notify params
AI_ENGINE=osais_getInfo()["name"]

import argparse

print("\r - Current version of Python is ", sys.version)
print("\r - Platform version: ", platform.python_version())
print ("\r - "+argparse.__name__ + " v"+argparse.__version__)

import subprocess

current_machine_id = None
if os.name == "nt":  # Windows
    current_machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
else:  # Linux / Docker
    current_machine_id = os.popen("cat /etc/machine-id").read().strip() ## os.uname()[1]
print ("\r - machine uid: "+current_machine_id)

import uuid 
print ("\r - machine uuid: "+str (hex(uuid.getnode())))

default_image_width = 512
default_image_height = 512

def fn_run(_args): 

    # Create the parser
    vq_parser = argparse.ArgumentParser(description='Dummy image generation - using PING')

    # Add the AI Gateway / OpenSourceAIs arguments
    vq_parser.add_argument("-orig",  "--origin", type=str, help="AI Gateway server origin", default="http://localhost:3654/", dest='OSAIS_origin')     ##  this is for comms with AI Gateway
    vq_parser.add_argument("-t",  "--token", type=str, help="OpenSourceAIs token", default="0", dest='tokenAI')               ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-u",  "--username", type=str, help="OpenSourceAIs username", default="", dest='username')       ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-uid",  "--unique_id", type=int, help="Unique ID of this AI session", default=0, dest='uid')    ##  this is for comms with OpenSourceAIs
    vq_parser.add_argument("-odir", "--outdir", type=str, help="Output directory", default="./_output/", dest='outdir')
    vq_parser.add_argument("-idir", "--indir", type=str, help="input directory", default="./_input/", dest='indir')
    vq_parser.add_argument("-local", "--islocal", type=bool, help="is local or prod?", default=False, dest='isLocal')

    # Add the PING arguments
    vq_parser.add_argument("-p",    "--prompts", type=str, help="Text prompts", default=None, dest='prompts')
    vq_parser.add_argument("-filename","--init_image", type=str, help="Initial image", default="clown.jpg", dest='init_image')
    vq_parser.add_argument("-width",  "--width", type=int, help="Image width", default=default_image_width, dest='wImage')
    vq_parser.add_argument("-height",  "--height", type=int, help="Image height", default=default_image_height, dest='hImage')
    vq_parser.add_argument("-o",    "--output", type=str, help="Output filename", default="output.png", dest='output')

    CredsParam=None
    MorphingParam=None
    StageParam=None

    try:
        args = vq_parser.parse_args(_args)
        CredsParam=getCredsParams(args)
        MorphingParam=getMorphingParams(args)
        StageParam=getStageParams(args, AI_PROGRESS_AI_STARTED)
        osais_notify(CredsParam, MorphingParam , StageParam)            # OSAIS Notification
        print(args)
    except:
        print("\r\nCRITICAL ERROR!!!")
        CredsParam=getCredsParams(args)
        MorphingParam=getMorphingParams(args)
        StageParam=getStageParams(args, AI_PROGRESS_ERROR)
        osais_notify(CredsParam, MorphingParam , StageParam)            # OSAIS Notification
        return False

    StageParam=getStageParams(args, AI_PROGRESS_INIT_IMAGE)
    osais_notify(CredsParam, MorphingParam , StageParam)            # OSAIS Notification

    shutil.copy2(os.path.join(args.indir, args.init_image), os.path.join(args.outdir, args.output))

    StageParam=getStageParams(args, AI_PROGRESS_DONE_IMAGE)
    osais_notify(CredsParam, MorphingParam , StageParam)            # OSAIS Notification

    lst=[]
    for arg in sys.argv:
        lst.append(arg)

    print (' '.join(lst))

    sys.stdout.flush()
