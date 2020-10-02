import os
import sys
import pathlib
import argparse
from multiprocessing import Process

import fhdhrconfig
import proxyservice
import fakehdhr
import epghandler
import ssdpserver

if sys.version_info.major == 2 or sys.version_info < (3, 3):
    print('Error: FakeHDHR requires python 3.3+.')
    sys.exit(1)


def get_args():
    parser = argparse.ArgumentParser(description='FakeHDHR.', epilog='')
    parser.add_argument('--config_file', dest='cfg', type=str, default=None, help='')
    return parser.parse_args()


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':

    # Gather args
    args = get_args()

    # set to directory of script
    script_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

    # Open Configuration File
    print("Opening and Verifying Configuration File.")
    config = fhdhrconfig.HDHRConfig(script_dir, args)

    # Open proxyservice
    serviceproxy = proxyservice.proxyserviceFetcher(config)

    # Open EPG Handler
    epghandling = epghandler.EPGhandler(config, serviceproxy)

    try:

        print("Starting EPG thread...")
        epgServer = Process(target=epghandler.epgServerProcess, args=(config, epghandling))
        epgServer.start()

        print("Starting fHDHR Interface")
        fhdhrServer = Process(target=fakehdhr.interface_start, args=(config, serviceproxy, epghandling))
        fhdhrServer.start()

        if (config.config["fakehdhr"]["discovery_address"] and
                config.config["fakehdhr"]["discovery_address"] != "0.0.0.0"):
            print("Starting SSDP server...")
            ssdpServer = Process(target=ssdpserver.ssdpServerProcess, args=(config,))
            ssdpServer.daemon = True
            ssdpServer.start()
        else:
            ssdpServer = None
            print("Not Starting SSDP server...")

    except KeyboardInterrupt:
        print('^C received, shutting down the server')
        epgServer.terminate()
        fhdhrServer.terminate()
        if ssdpServer:
            ssdpServer.terminate()
        clean_exit()
