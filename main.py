#!/usr/bin/env python3
# coding=utf-8
# pylama:ignore=E402
try:
    from gevent import monkey
    monkey.patch_all()
    gevent_check = True
except ModuleNotFoundError:
    gevent_check = False

import os
import sys
import pathlib
SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

from deps import Dependencies
deps = Dependencies(SCRIPT_DIR)
if not gevent_check:
    print("gevent was missing, restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit()

from fHDHR.cli import run
import fHDHR_web

if __name__ == "__main__":
    sys.exit(run.main(SCRIPT_DIR, fHDHR_web, deps))
