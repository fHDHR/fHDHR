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

    config = {}

    def __init__(self, script_dir, args):
        self.get_config_path(script_dir, args)
        self.import_default_config(script_dir)
        self.import_service_config(script_dir)
        self.import_config()
        self.critical_config(script_dir)
        self.config_adjustments_this()
        self.config_adjustments()

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

    def import_default_config(self, script_dir):
        config_handler = configparser.ConfigParser()
        data_dir = pathlib.Path(script_dir).joinpath('data')
        internal_config_dir = pathlib.Path(data_dir).joinpath('internal_config')
        serviceconf = pathlib.Path(internal_config_dir).joinpath('fakehdhr.ini')
        config_handler.read(serviceconf)
        for each_section in config_handler.sections():
            if each_section not in list(self.config.keys()):
                self.config[each_section] = {}
            for (each_key, each_val) in config_handler.items(each_section):
                if each_val == "fHDHR_None":
                    each_val = None
                elif each_val == "fHDHR_True":
                    each_val = True
                elif each_val == "fHDHR_False":
                    each_val = False
                self.config[each_section.lower()][each_key.lower()] = each_val

    def import_service_config(self, script_dir):
        config_handler = configparser.ConfigParser()
        data_dir = pathlib.Path(script_dir).joinpath('data')
        internal_config_dir = pathlib.Path(data_dir).joinpath('internal_config')
        serviceconf = pathlib.Path(internal_config_dir).joinpath('serviceconf.ini')
        config_handler.read(serviceconf)
        for each_section in config_handler.sections():
            if each_section not in list(self.config.keys()):
                self.config[each_section] = {}
            for (each_key, each_val) in config_handler.items(each_section):
                if each_val == "fHDHR_None":
                    each_val = None
                elif each_val == "fHDHR_True":
                    each_val = True
                elif each_val == "fHDHR_False":
                    each_val = False
                self.config[each_section.lower()][each_key.lower()] = each_val

    def write(self, section, key, value):
        self.config[section][key] = value
        self.config_handler.set(section, key, value)

        with open(self.config_file, 'w') as config_file:
            self.config_handler.write(config_file)

    def critical_config(self, script_dir):

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

        empty_cache = pathlib.Path(cache_dir).joinpath('empty_cache')
        self.config["empty"]["empty_cache"] = empty_cache
        if not empty_cache.is_dir():
            empty_cache.mkdir()
        self.config["empty"]["empty_cache_file"] = pathlib.Path(empty_cache).joinpath('epg.json')

        www_dir = pathlib.Path(data_dir).joinpath('www')
        self.config["main"]["www_dir"] = www_dir
        self.config["main"]["favicon"] = pathlib.Path(www_dir).joinpath('favicon.ico')

    def config_adjustments(self):

        # generate UUID here for when we are not using docker
        if self.config["main"]["uuid"] is None:
            print("No UUID found.  Generating one now...")
            # from https://pynative.com/python-generate-random-string/
            # create a string that wouldn't be a real device uuid for
            self.config["main"]["uuid"] = ''.join(random.choice("hijklmnopqrstuvwxyz") for i in range(8))
            self.write('main', 'uuid', self.config["main"]["uuid"])
        print("UUID set to: " + self.config["main"]["uuid"] + "...")

        if not self.config["fakehdhr"]["discovery_address"]:
            if self.config["fakehdhr"]["address"] != "0.0.0.0":
                self.config["fakehdhr"]["discovery_address"] = self.config["fakehdhr"]["address"]

        print("Server is set to run on  " +
              str(self.config["fakehdhr"]["address"]) + ":" +
              str(self.config["fakehdhr"]["port"]))

    def config_adjustments_this(self):
        self.config["proxy"] = self.config.pop("locast")
        self.config_adjustments_proxy()
        self.config_adjustments_zap2it()

    def config_adjustments_proxy(self):
        cache_dir = self.config["main"]["cache_dir"]

        credentials_list = self.config["main"]["credentials"].split(",")
        creds_missing = False
        if len(credentials_list):
            for cred_item in credentials_list:
                if not self.config["proxy"][cred_item]:
                    creds_missing = True
            if creds_missing:
                print(self.config["main"]["servicename"] + " Login Credentials Missing. Exiting...")
                clean_exit()

        proxy_cache = pathlib.Path(cache_dir).joinpath('proxy')
        self.config["main"]["proxy_cache"] = proxy_cache
        if not proxy_cache.is_dir():
            proxy_cache.mkdir()
        self.config["proxy"]["epg_cache"] = pathlib.Path(proxy_cache).joinpath('epg.json')
        proxy_web_cache = pathlib.Path(proxy_cache).joinpath('proxy_web_cache')
        self.config["main"]["proxy_web_cache"] = proxy_web_cache
        if not proxy_web_cache.is_dir():
            proxy_web_cache.mkdir()

    def config_adjustments_zap2it(self):
        cache_dir = self.config["main"]["cache_dir"]

        zap_cache = pathlib.Path(cache_dir).joinpath('zap2it')
        self.config["main"]["zap_cache"] = zap_cache
        if not zap_cache.is_dir():
            zap_cache.mkdir()
        self.config["zap2it"]["epg_cache"] = pathlib.Path(zap_cache).joinpath('epg.json')
        zap_web_cache = pathlib.Path(zap_cache).joinpath('zap_web_cache')
        self.config["main"]["zap_web_cache"] = zap_web_cache
        if not zap_web_cache.is_dir():
            zap_web_cache.mkdir()
