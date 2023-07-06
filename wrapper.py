#!/usr/bin/env python
# wrapper for the shell script

DAEMON : str = './daemon.sh'
SHELL : str = 'bash'

import os
import sys

### set working directory
## $ cd "$(dirname "$(readlink -f "$0")")"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def execute(args=sys.argv):
    daemon = os.path.abspath(DAEMON)
    args = [ SHELL, daemon ] + sys.argv[1:]
    os.execvp(SHELL, args)
