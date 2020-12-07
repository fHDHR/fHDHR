#!/usr/bin/env python3
# coding=utf-8
# pylama:ignore=E402
from gevent import monkey
monkey.patch_all()
import os
import sys
import pathlib
from multiprocessing import freeze_support

from fHDHR.cli import run
import alternative_epg
import origin

SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    freeze_support()
    sys.exit(run.main(SCRIPT_DIR, alternative_epg, origin))
