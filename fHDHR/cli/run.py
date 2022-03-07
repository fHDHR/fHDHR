import os
import argparse
import time
import pathlib
import json

from fHDHR import fHDHR_OBJ
import fHDHR.exceptions
import fHDHR.config
import fHDHR.logger
import fHDHR.plugins
import fHDHR.versions
import fHDHR.scheduler
import fHDHR.web
import fHDHR.origins
from fHDHR.db import fHDHRdb
from fHDHR.time_manager import Time_Manager

ERR_CODE = 1
ERR_CODE_NO_RESTART = 2


def build_args_parser(script_dir):
    """
    Build argument parser for fHDHR.
    """

    parser = argparse.ArgumentParser(description='fHDHR')
    parser.add_argument('-c', '--config', dest='cfg', type=str, default=pathlib.Path(script_dir).joinpath('config.ini'), required=False, help='configuration file to load.')
    parser.add_argument('--setup', dest='setup', type=str, required=False, nargs='?', const=True, default=False, help='Setup Configuration file.')
    parser.add_argument('--iliketobreakthings', dest='iliketobreakthings', type=str, nargs='?', const=True, required=False, default=False, help='Override Config Settings not meant to be overridden.')
    parser.add_argument('-v', '--version', dest='version', type=str, required=False, nargs='?', const=True, default=False, help='Show Version Number.')
    return parser.parse_args()


def run(settings, fhdhr_time, logger, db, script_dir, fHDHR_web, plugins, versions, web, scheduler, deps):
    """
    Create fHDHR and fHDHH_web objects, and run threads.
    """

    fhdhr = fHDHR_OBJ(settings, fhdhr_time, logger, db, plugins, versions, web, scheduler, deps)
    fhdhrweb = fHDHR_web.fHDHR_HTTP_Server(fhdhr)

    versions.sched_init(fhdhr)

    try:

        # Start Flask Thread
        fhdhrweb.start()

        # Start SSDP Thread
        if fhdhr.device.ssdp.multicast_address and "ssdp" in list(fhdhr.threads.keys()):
            fhdhr.device.ssdp.start()

        # Start additional interface Plugin threads
        fhdhr.device.run_interface_plugin_threads()

        # Run Scheduled Jobs thread
        fhdhr.scheduler.fhdhr_self_add(fhdhr)
        fhdhr.scheduler.run()

        # Perform Startup Tasks
        fhdhr.scheduler.startup_tasks()

        logger.noob("fHDHR and fHDHR_web should now be running and accessible via the web interface at %s" % fhdhr.api.base)
        if settings.dict["logging"]["level"].upper() == "NOOB":
            logger.noob("Set your [logging]level to INFO if you wish to see more logging output.")

        # wait forever
        restart_code = "restart"
        while fhdhr.threads["flask"].is_alive():
            time.sleep(1)

        if restart_code in ["restart"]:
            logger.noob("fHDHR has been signaled to restart.")

        return restart_code

    except KeyboardInterrupt:
        return ERR_CODE_NO_RESTART

    return ERR_CODE


def start(args, script_dir, fhdhr_time, fHDHR_web, deps):
    """
    Get Configuration for fHDHR and start.
    """

    try:
        settings = fHDHR.config.Config(args, script_dir)
    except fHDHR.exceptions.ConfigurationError as exerror:
        print(exerror)
        return ERR_CODE_NO_RESTART

    # Setup Logging
    logger = fHDHR.logger.Logger(settings)
    settings.logger = logger

    # Setup Version System
    versions = fHDHR.versions.Versions(settings, logger)

    loading_versions_string = ""
    core_versions = versions.get_core_versions()
    for item in list(core_versions.keys()):
        if loading_versions_string != "":
            spaceprefix = ", "
        else:
            spaceprefix = " "
        loading_versions_string += "%s%s %s" % (spaceprefix, core_versions[item]["name"], core_versions[item]["version"])

    logger.noob("Loading %s" % loading_versions_string)
    logger.info("Importing Core config values from Configuration File: %s" % settings.config_file)

    logger.debug("Logging to File: %s" % os.path.join(settings.internal["paths"]["logs_dir"], '.fHDHR.log'))

    # Continue non-core settings setup
    settings.secondary_setup()

    # add config to time manager
    fhdhr_time.setup(settings, logger)

    # Setup Database
    db = fHDHRdb(settings, logger)

    logger.debug("Setting Up shared Web Requests system.")
    web = fHDHR.web.WebReq()

    scheduler = fHDHR.scheduler.Scheduler(settings, logger, db)

    # Continue Version System Setup
    versions.secondary_setup(db, web, scheduler)

    # Find Plugins and import their default configs
    plugins = fHDHR.plugins.PluginsHandler(settings, logger, db, versions, deps)

    return run(settings, fhdhr_time, logger, db, script_dir, fHDHR_web, plugins, versions, web, scheduler, deps)


def config_setup(args, script_dir, fHDHR_web):
    """
    Setup Config file.
    """

    settings = fHDHR.config.Config(args, script_dir, fHDHR_web)
    fHDHR.plugins.PluginsHandler(settings)
    settings.setup_user_config()
    return ERR_CODE


def main(script_dir, fHDHR_web, deps):
    """
    fHDHR run script entry point.
    """

    fhdhr_time = Time_Manager()

    try:
        args = build_args_parser(script_dir)

        if args.version:
            versions_string = ""
            version_file = pathlib.Path(script_dir).joinpath("version.json")
            with open(version_file, 'r') as jsonversion:
                core_versions = json.load(jsonversion)
            for item in list(core_versions.keys()):
                if versions_string != "":
                    spaceprefix = ", "
                else:
                    spaceprefix = ""
                versions_string += "%s%s %s" % (spaceprefix, item, core_versions[item])
            print(versions_string)
            return ERR_CODE

        if args.setup:
            return config_setup(args, script_dir, fHDHR_web)

        while True:

            returned_code = start(args, script_dir, fhdhr_time, fHDHR_web, deps)
            if returned_code not in ["restart"]:
                return returned_code

    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE


if __name__ == '__main__':
    """
    Trigger main function.
    """
    main()
