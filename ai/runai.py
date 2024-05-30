
##
##      AI_PING
##

## ------------------------------------------------------------------------
#       Generic (All AIs)
## ------------------------------------------------------------------------

import os, sys, argparse, shutil, time
from datetime import datetime

## for calling back OSAIS from AI
gNotifyCallback=None
gNotifyParams=None

## Notifications from AI
def setNotifyCallback(cb, _aParams): 
    global gNotifyParams
    global gNotifyCallback

    gNotifyParams=_aParams
    gNotifyCallback=cb

## For a debug breakpoint
def fnDebug(): 
    return True

## where to save the user profile?
def fnGetUserdataPath(_username):
    _path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DEFAULT_PROFILE_DIR = os.path.join(_path, '_profile')
    USER_PROFILE_DIR = os.path.join(DEFAULT_PROFILE_DIR, _username)
    return {
        "location": USER_PROFILE_DIR,
        "voice": False,
        "picture": True
    }

## ------------------------------------------------------------------------
#       Specific
## ------------------------------------------------------------------------

default_image_width = 512
default_image_height = 512

## WARMUP Data
def getWarmupData(_id):
    try:
        import time
        from werkzeug.datastructures import MultiDict
        ts=int(time.time())
        sample_args = MultiDict([
            ('-u', 'test_user'),
            ('-uid', str(ts)),
            ('-t', _id),
            ('-cycle', '0'),
            ('-width', '512'),
            ('-height', '512'),
            ('-o', 'warmup.jpg'),
            ('-filename', 'warmup.jpg')
        ])
        return sample_args
    except:
        print("Could not call warm up!\r\n")
        return None

## RUN AI
def fnRun(_args): 
    vq_parser = argparse.ArgumentParser()

    # OSAIS arguments
    vq_parser.add_argument("-odir", "--outdir", type=str, help="Output directory", default="./_output/", dest='outdir')
    vq_parser.add_argument("-idir", "--indir", type=str, help="input directory", default="./_input/", dest='indir')

    # Add the PING arguments
    vq_parser.add_argument("-p",    "--prompts", type=str, help="Text prompts", default=None, dest='prompts')
    vq_parser.add_argument("-filename","--init_image", type=str, help="Initial image", default="warmup.jpg", dest='init_image')
    vq_parser.add_argument("-width",  "--width", type=int, help="Image width", default=default_image_width, dest='wImage')
    vq_parser.add_argument("-height",  "--height", type=int, help="Image height", default=default_image_height, dest='hImage')
    vq_parser.add_argument("-o",    "--output", type=str, help="Output filename", default="output.png", dest='output')
    vq_parser.add_argument("-watermark",    "--watermark", type=str, help="watermark filename", default=None, dest='watermark')

    try:
        args = vq_parser.parse_args(_args)
        print(args)
        
    except Exception as err:
        print("\r\nCRITICAL ERROR!!!")
        raise err
            
    ## include cycle in output name
    fileOut, fileExt = os.path.splitext(args.output)
    _resFile=fileOut+"_0"+fileExt
    _fileOut=os.path.join(args.outdir, _resFile)
    _fileIn=os.path.join(args.indir, args.init_image)

    ## if we already have this image, we remove it, so that AI will receive notification of new copied image
    if os.path.exists(_fileOut):
        try:
            # Delete the file
            os.remove(_fileOut)
            time.sleep(0.1)     ## we purposely sleep 100ms for AI to see image removed, then added (important for its notification)
        except OSError as e:
            ## do nothing
            print ("COULD NOT REMOVE IMAGE FROM DISK")

    ## now we start clocking time
    beg_date = datetime.utcnow()

    ## we do nothing (just a copy of image)
    if args.watermark:
        import urllib.request 
        from PIL import Image 
        from osais_utils import AddWatermark
        
        if gNotifyCallback:
            gNotifyCallback(gNotifyParams, "Watermarking picture...", 0.65)
               
        _fileWatermark=os.path.join(args.indir,"watermark.png")
        urllib.request.urlretrieve(args.watermark, _fileWatermark)
        image2 = Image.open(_fileWatermark)
        
        image1 = Image.open(_fileIn)
        imgRet=AddWatermark(image1, image2)

        if gNotifyCallback:
            gNotifyCallback(gNotifyParams, "Saving picture...", 0.9)
        imgRet.save(os.path.join(args.outdir, _resFile),"JPEG")
    else:
        if gNotifyCallback:
            gNotifyCallback(gNotifyParams, "Copying picture...", 0.9)
        shutil.copy2(_fileIn, os.path.join(args.outdir, _resFile))
    
    ## return output
    end_date = datetime.utcnow()
    return {
        "beg_date": beg_date,
        "end_date": end_date,
        "mCost": 0,                      ## cost multiplier of this particular AI (vs normal cost)
        "aFile": [_resFile]
    }
