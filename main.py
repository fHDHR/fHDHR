#!/usr/bin/env python3
# coding=utf-8
# pylama:ignore=E402
from gevent import monkey
monkey.patch_all()
import os
import sys
import pathlib

from fHDHR.cli import run
import alternative_epg

try:
    import fHDHR_web
except ModuleNotFoundError:
    print("Error: fHDHR_web Not Found.")
    sys.exit(1)

try:
    import origin
except ModuleNotFoundError:
    print("Error: Origin Not Found.")
    sys.exit(1)

SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    sys.exit(run.main(SCRIPT_DIR, fHDHR_web, origin, alternative_epg))
