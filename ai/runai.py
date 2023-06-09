
##
##      PING AI
##

import os
import argparse
import shutil
from datetime import datetime

default_image_width = 512
default_image_height = 512

def fnRun(_args): 
    vq_parser = argparse.ArgumentParser()

    # OSAIS arguments
    vq_parser.add_argument("-odir", "--outdir", type=str, help="Output directory", default="./_output/", dest='outdir')
    vq_parser.add_argument("-idir", "--indir", type=str, help="input directory", default="./_input/", dest='indir')

    # Add the PING arguments
    vq_parser.add_argument("-p",    "--prompts", type=str, help="Text prompts", default=None, dest='prompts')
    vq_parser.add_argument("-filename","--init_image", type=str, help="Initial image", default="clown.jpg", dest='init_image')
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
        "aFile": [_resFile]
    }
