import sys
import argparse
import time
import pathlib

from fHDHR import fHDHR_VERSION, fHDHR_OBJ
import fHDHR.exceptions
import fHDHR.config
import fHDHR.logger
import fHDHR.plugins
import fHDHR.versions
import fHDHR.origins
from fHDHR.db import fHDHRdb

ERR_CODE = 1
ERR_CODE_NO_RESTART = 2


if sys.version_info.major == 2 or sys.version_info < (3, 7):
    print('Error: fHDHR requires python 3.7+.')
    sys.exit(1)


def build_args_parser(script_dir):
    """Build argument parser for fHDHR"""
    parser = argparse.ArgumentParser(description='fHDHR')
    parser.add_argument('-c', '--config', dest='cfg', type=str, default=pathlib.Path(script_dir).joinpath('config.ini'), required=False, help='configuration file to load.')
    parser.add_argument('--setup', dest='setup', type=str, required=False, nargs='?', const=True, default=False, help='Setup Configuration file.')
    parser.add_argument('--iliketobreakthings', dest='iliketobreakthings', type=str, nargs='?', const=True, required=False, default=False, help='Override Config Settings not meant to be overridden.')
    return parser.parse_args()


def run(settings, logger, db, script_dir, fHDHR_web, plugins, versions):

    fhdhr = fHDHR_OBJ(settings, logger, db, plugins, versions)
    fhdhrweb = fHDHR_web.fHDHR_HTTP_Server(fhdhr)

    try:

        # Start Flask Thread
        fhdhrweb.start()

        # Perform some actions now that HTTP Server is running
        fhdhr.api.get("/api/startup_tasks")

        # Start SSDP Thread
        if fhdhr.device.ssdp.multicast_address and "ssdp" in list(fhdhr.threads.keys()):
            fhdhr.device.ssdp.start()

        # Start EPG Thread
        if settings.dict["epg"]["method"] and "epg" in list(fhdhr.threads.keys()):
            fhdhr.device.epg.start()

        # wait forever
        restart_code = "restart"
        while fhdhr.threads["flask"].is_alive():
            time.sleep(1)
        return restart_code

    except KeyboardInterrupt:
        return ERR_CODE_NO_RESTART

    return ERR_CODE


def start(args, script_dir, fHDHR_web):
    """Get Configuration for fHDHR and start"""

    try:
        settings = fHDHR.config.Config(args, script_dir)
    except fHDHR.exceptions.ConfigurationError as e:
        print(e)
        return ERR_CODE_NO_RESTART

    # Find Plugins and import their default configs
    plugins = fHDHR.plugins.PluginsHandler(settings)

    if settings.conf_was_missing:
        settings.setup_user_config()

    # Apply User Configuration
    settings.user_config()
    settings.config_verification()

    # Load An External Plugins Directory
    if settings.internal["paths"]["external_plugins_dir"]:
        plugins.list_plugins(settings.internal["paths"]["external_plugins_dir"])
        settings.user_config()
        settings.config_verification()

    # Setup Logging
    logger = fHDHR.logger.Logger(settings)

    # Setup Database
    db = fHDHRdb(settings)

    # Setup Plugins
    plugins.load_plugins(logger, db)

    # Setup Version System
    versions = fHDHR.versions.Versions(settings, fHDHR_web, plugins)

    # Continue Plugin Setup
    plugins.setup(versions)
    settings.config_verification_plugins()

    return run(settings, logger, db, script_dir, fHDHR_web, plugins, versions)


def config_setup(args, script_dir, fHDHR_web):
    settings = fHDHR.config.Config(args, script_dir, fHDHR_web)
    fHDHR.plugins.PluginsHandler(settings)
    settings.setup_user_config()
    return ERR_CODE


def main(script_dir, fHDHR_web):
    """fHDHR run script entry point"""

    print("Loading fHDHR %s" % fHDHR_VERSION)
    print("Loading fHDHR_web %s" % fHDHR_web.fHDHR_web_VERSION)

    try:
        args = build_args_parser(script_dir)

        if args.setup:
            return config_setup(args, script_dir, fHDHR_web)

        while True:
            returned_code = start(args, script_dir, fHDHR_web)
            if returned_code not in ["restart"]:
                return returned_code
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE


if __name__ == '__main__':
    main()
