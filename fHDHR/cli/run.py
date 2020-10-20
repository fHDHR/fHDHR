import os
import sys
import time
import argparse
from multiprocessing import Process

from fHDHR import fHDHR_VERSION
import fHDHR.exceptions
import fHDHR.config

import fHDHR.origin
import fHDHR.api
import fHDHR.ssdpserver

ERR_CODE = 1
ERR_CODE_NO_RESTART = 2


if sys.version_info.major == 2 or sys.version_info < (3, 3):
    print('Error: fHDHR requires python 3.3+.')
    sys.exit(1)


def build_args_parser():
    """Build argument parser for fHDHR"""
    print("Validating CLI Argument")
    parser = argparse.ArgumentParser(description='fHDHR')
    parser.add_argument('-c', '--config', dest='cfg', type=str, required=True, help='configuration file to load.')
    return parser.parse_args()


def get_configuration(args, script_dir):
    if not os.path.isfile(args.cfg):
        raise fHDHR.exceptions.ConfigurationNotFound(filename=args.cfg)
    return fHDHR.config.Config(args.cfg, script_dir)


def run(settings, origin):

    if settings.dict["fhdhr"]["discovery_address"]:
        ssdpServer = Process(target=fHDHR.ssdpserver.ssdpServerProcess, args=(settings,))
        ssdpServer.start()

    fhdhrweb = Process(target=fHDHR.api.interface_start, args=(settings, origin))
    fhdhrweb.start()

    print(settings.dict["fhdhr"]["friendlyname"] + " is now running!")

    # wait forever
    while True:
        time.sleep(3600)

    return ERR_CODE


def start(args, script_dir):
    """Get Configuration for fHDHR and start"""

    try:
        settings = get_configuration(args, script_dir)
    except fHDHR.exceptions.ConfigurationError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    try:
        origin = fHDHR.origin.origin_channels.OriginService(settings)
    except fHDHR.exceptions.OriginSetupError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    return run(settings, origin)


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
