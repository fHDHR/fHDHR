import os
import sys
import time
import argparse
from multiprocessing import Process

from fHDHR import fHDHR_VERSION, config, originservice, ssdpserver, epghandler, fHDHRerrors, fHDHRweb

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
        raise config.ConfigurationNotFound(filename=args.cfg)
    return config.Config(args.cfg, script_dir)


def get_originservice(settings):
    return originservice.OriginService(settings)


def run(settings, origserv, epghandling):

    if settings.dict["fhdhr"]["discovery_address"]:
        ssdpServer = Process(target=ssdpserver.ssdpServerProcess, args=(settings,))
        ssdpServer.start()

    if settings.dict["fhdhr"]["epg_method"]:
        epgServer = Process(target=epghandler.epgServerProcess, args=(settings, epghandling))
        epgServer.start()

    fhdhrweb = Process(target=fHDHRweb.interface_start, args=(settings, origserv, epghandling))
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
    except fHDHRerrors.ConfigurationError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    try:
        origserv = get_originservice(settings)
    except fHDHRerrors.LoginError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    try:
        epghandling = epghandler.EPGhandler(settings, origserv)
    except fHDHRerrors.EPGSetupError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    return run(settings, origserv, epghandling)


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
