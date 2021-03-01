#!/usr/bin/env python3
# coding=utf-8
# pylama:ignore=E402
import os
import sys
import pathlib
SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

from fHDHR.deps import Dependencies
deps = Dependencies(SCRIPT_DIR)

from gevent import monkey
monkey.patch_all(ssl=False)

from fHDHR.cli import run
import fHDHR_web

if __name__ == "__main__":
    sys.exit(run.main(SCRIPT_DIR, fHDHR_web, deps))
