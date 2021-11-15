#!/usr/bin/env python3
# coding=utf-8
# pylama:ignore=E402
"""monkey.patch_all must be run as soon as possible."""
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

"""
Install Dependencies at startup.
Caution, if dependencies fail to install, this will result in issues later on.
This is mainly here to install dependencies that have been added after upgrades,
and doing a manual install of dependencies prior to install is still reccomended.
"""
from deps import Dependencies
deps = Dependencies(SCRIPT_DIR)


"""If gevent was not installed prior to the Dependencies check, restart."""
if not gevent_check:
    print("gevent was missing, restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit()

from fHDHR.cli import run
import fHDHR_web

if __name__ == "__main__":
    """Calls fHDHR.cli running methods."""
    sys.exit(run.main(SCRIPT_DIR, fHDHR_web, deps))
