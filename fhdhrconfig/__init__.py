import os
import sys
import random
import configparser
import pathlib


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


class HDHRConfig():

    config_file = None
    config_handler = configparser.ConfigParser()
    script_dir = None

    config = {
                "main": {
                        'uuid': None,
                        "cache_dir": None,
                        "empty_epg_update_frequency": 43200,
                        },
                "locast": {
                              "username": None,
                              "password": None,
                              "epg_update_frequency": 43200,
                              },
                "location": {
                            'override_latitude': None,
                            'override_longitude': None,
                            'mock_location': None,
                            'override_zipcode': None,
                            },
                "fakehdhr": {
                              "address": "0.0.0.0",
                              "port": 5004,
                              "discovery_address": "0.0.0.0",
                              "tuner_count": 4,  # number of tuners in tvh
                              "concurrent_listeners": 10,
                              "friendlyname": "fHDHR-Locast",
                              "stream_type": "ffmpeg",
                              "epg_method": "proxy",
                              "font": None,
                              },
                "zap2xml": {
                            "delay": 5,
                            "postalcode": None,
                            "affiliate_id": 'gapzap',
                            "country": 'USA',
                            "device": '-',
                            "headendid": "lineupId",
                            "isoverride": True,
                            "languagecode": 'en',
                            "pref": "",
                            "timespan": 6,
                            "timezone": "",
                            "userid": "-",
                            "epg_update_frequency": 43200,
                            },
                "ffmpeg": {
                            'ffmpeg_path': "ffmpeg",
                            'bytes_per_read': '1152000',
                            "font": None,
                            },
                "direct_stream": {
                                'chunksize': 1024*1024  # usually you don't need to edit this
                                },
                "dev": {
                        'reporting_model': 'HDHR4-2DT',
                        'reporting_firmware_name': 'hdhomerun4_dvbt',
                        'reporting_firmware_ver': '20150826',
                        'reporting_tuner_type': "Antenna",
                        }
    }

    def __init__(self, script_dir, args):
        self.get_config_path(script_dir, args)
        self.import_config()
        self.config_adjustments(script_dir)

    def get_config_path(self, script_dir, args):
        if args.cfg:
            self.config_file = pathlib.Path(str(args.cfg))
        if not self.config_file or not os.path.exists(self.config_file):
            print("Config file missing, Exiting...")
            clean_exit()
        print("Loading Configuration File: " + str(self.config_file))

    def import_config(self):
        self.config_handler.read(self.config_file)
        for each_section in self.config_handler.sections():
            if each_section not in list(self.config.keys()):
                self.config[each_section] = {}
            for (each_key, each_val) in self.config_handler.items(each_section):
                self.config[each_section.lower()][each_key.lower()] = each_val

    def write(self, section, key, value):
        self.config[section][key] = value
        self.config_handler.set(section, key, value)

        with open(self.config_file, 'w') as config_file:
            self.config_handler.write(config_file)

    def config_adjustments(self, script_dir):

        self.config["main"]["script_dir"] = script_dir

        data_dir = pathlib.Path(script_dir).joinpath('data')
        self.config["main"]["data_dir"] = data_dir

        self.config["fakehdhr"]["font"] = pathlib.Path(data_dir).joinpath('garamond.ttf')

        if not self.config["main"]["cache_dir"]:
            self.config["main"]["cache_dir"] = pathlib.Path(data_dir).joinpath('cache')
        else:
            self.config["main"]["cache_dir"] = pathlib.Path(self.config["main"]["cache_dir"])
        if not self.config["main"]["cache_dir"].is_dir():
            print("Invalid Cache Directory. Exiting...")
            clean_exit()
        cache_dir = self.config["main"]["cache_dir"]

        if not self.config["locast"]["username"] or not self.config["locast"]["password"]:
            print("Locast Login Credentials Missing. Exiting...")
            clean_exit()

        empty_cache = pathlib.Path(cache_dir).joinpath('empty_cache')
        self.config["main"]["empty_cache"] = empty_cache
        if not empty_cache.is_dir():
            empty_cache.mkdir()
        self.config["main"]["empty_cache_file"] = pathlib.Path(empty_cache).joinpath('epg.json')

        locast_cache = pathlib.Path(cache_dir).joinpath('locast')
        self.config["main"]["locast_cache"] = locast_cache
        if not locast_cache.is_dir():
            locast_cache.mkdir()
        self.config["locast"]["sidfile"] = pathlib.Path(locast_cache).joinpath('sid.txt')
        self.config["locast"]["epg_cache"] = pathlib.Path(locast_cache).joinpath('epg.json')
        locast_web_cache = pathlib.Path(locast_cache).joinpath('locast_web_cache')
        self.config["main"]["locast_web_cache"] = locast_web_cache
        if not locast_web_cache.is_dir():
            locast_web_cache.mkdir()

        zap_cache = pathlib.Path(cache_dir).joinpath('zap2it')
        self.config["main"]["zap_cache"] = zap_cache
        if not zap_cache.is_dir():
            zap_cache.mkdir()
        self.config["zap2xml"]["epg_cache"] = pathlib.Path(zap_cache).joinpath('epg.json')
        zap_web_cache = pathlib.Path(zap_cache).joinpath('zap_web_cache')
        self.config["main"]["zap_web_cache"] = zap_web_cache
        if not zap_web_cache.is_dir():
            zap_web_cache.mkdir()

        www_dir = pathlib.Path(data_dir).joinpath('www')
        self.config["main"]["www_dir"] = www_dir
        self.config["main"]["favicon"] = pathlib.Path(www_dir).joinpath('favicon.ico')

        www_image_dir = pathlib.Path(www_dir).joinpath('images')
        self.config["main"]["www_image_dir"] = www_image_dir
        self.config["main"]["image_def_channel"] = pathlib.Path(www_image_dir).joinpath("default-channel-thumb.png")
        self.config["main"]["image_def_content"] = pathlib.Path(www_image_dir).joinpath("default-content-thumb.png")

        # generate UUID here for when we are not using docker
        if self.config["main"]["uuid"] is None:
            print("No UUID found.  Generating one now...")
            # from https://pynative.com/python-generate-random-string/
            # create a string that wouldn't be a real device uuid for
            self.config["main"]["uuid"] = ''.join(random.choice("hijklmnopqrstuvwxyz") for i in range(8))
            self.write('main', 'uuid', self.config["main"]["uuid"])
        print("UUID set to: " + self.config["main"]["uuid"] + "...")

        print("Server is set to run on  " +
              str(self.config["fakehdhr"]["address"]) + ":" +
              str(self.config["fakehdhr"]["port"]))
