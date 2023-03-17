
## used as the entry point from the local batch command line

import sys
from _ping import fn_run

args=sys.argv[1:]
fn_run(args)
