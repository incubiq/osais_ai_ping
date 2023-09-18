
##
##      PING AI
##

import os
import argparse
import shutil
from datetime import datetime

default_image_width = 512
default_image_height = 512

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

    try:
        args = vq_parser.parse_args(_args)
        print(args)
        
    except Exception as err:
        print("\r\nCRITICAL ERROR!!!")
        raise err

    beg_date = datetime.utcnow()
    ## we do nothing (just a copy of image)
    
    ## include cycle in output name
    basename = args.output.split(".")
    fileOut=basename[0]
    fileExt=basename[1]

    _resFile=fileOut+"_0."+fileExt
    shutil.copy2(os.path.join(args.indir, args.init_image), os.path.join(args.outdir, _resFile))
    
    ## return output
    end_date = datetime.utcnow()
    return {
        "beg_date": beg_date,
        "end_date": end_date,
        "mCost": 0,                      ## cost multiplier of this particular AI (vs normal cost)
        "aFile": [_resFile]
    }
