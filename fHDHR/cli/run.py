import os
import sys
import argparse
import time
import multiprocessing
import platform

from fHDHR import fHDHR_VERSION, fHDHR_OBJ
import fHDHR.exceptions
import fHDHR.config
from fHDHR.http import fHDHR_HTTP_Server
from fHDHR.db import fHDHRdb

ERR_CODE = 1
ERR_CODE_NO_RESTART = 2


if sys.version_info.major == 2 or sys.version_info < (3, 7):
    print('Error: fHDHR requires python 3.7+.')
    sys.exit(1)

opersystem = platform.system()
if opersystem in ["Windows"]:
    print("WARNING: This script may fail on Windows.")


def build_args_parser():
    """Build argument parser for fHDHR"""
    parser = argparse.ArgumentParser(description='fHDHR')
    parser.add_argument('-c', '--config', dest='cfg', type=str, required=True, help='configuration file to load.')
    return parser.parse_args()


def get_configuration(args, script_dir):
    if not os.path.isfile(args.cfg):
        raise fHDHR.exceptions.ConfigurationNotFound(filename=args.cfg)
    return fHDHR.config.Config(args.cfg, script_dir)


def run(settings, logger, db):

    fhdhr = fHDHR_OBJ(settings, logger, db)
    fhdhrweb = fHDHR_HTTP_Server(fhdhr)

    # Ensure spawn on Windows instead of fork
    if settings.dict["main"]["opersystem"] in ["Windows"]:
        multiprocessing.set_start_method('spawn')

    try:

        print("HTTP Server Starting")
        fhdhr_web = multiprocessing.Process(target=fhdhrweb.run)
        fhdhr_web.start()

        if settings.dict["fhdhr"]["discovery_address"]:
            print("SSDP Server Starting")
            fhdhr_ssdp = multiprocessing.Process(target=fhdhr.device.ssdp.run)
            fhdhr_ssdp.start()

        if settings.dict["epg"]["method"]:
            print("EPG Update Starting")
            fhdhr_epg = multiprocessing.Process(target=fhdhr.device.epg.run)
            fhdhr_epg.start()

        # wait forever
        while True:
            time.sleep(3600)

    except KeyboardInterrupt:
        return ERR_CODE_NO_RESTART

    return ERR_CODE


def start(args, script_dir):
    """Get Configuration for fHDHR and start"""

    try:
        settings = get_configuration(args, script_dir)
    except fHDHR.exceptions.ConfigurationError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    logger = settings.logging_setup()

    db = fHDHRdb(settings)

    return run(settings, logger, db)


def main(script_dir):
    """fHDHR run script entry point"""

    print("Loading fHDHR " + fHDHR_VERSION)

    try:
        args = build_args_parser()
        return start(args, script_dir)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE


if __name__ == '__main__':
    main()
