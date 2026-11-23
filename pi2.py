#!/usr/bin/env python3
# Runs pi2 (pi/2 for Python) from this checkout. Works from any directory:
#   python3 ~/pi-2/pi2.py --model ollama/gemma4-workshop:12b -e path/to/extension.py
import sys

if sys.version_info < (3, 10):
    sys.exit("pi2 needs Python 3.10 or newer; this is " + sys.version.split()[0] + ". Run it with a newer python3.")

# Python puts this file's folder first on the module path, so `pi2` is the package next to it.
from pi2.cli import main

main()
