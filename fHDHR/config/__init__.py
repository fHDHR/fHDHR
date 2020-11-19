import os
import random
import configparser
import pathlib
import logging
import subprocess
import platform

import fHDHR.exceptions
from fHDHR.tools import isint, isfloat, is_arithmetic, is_docker


class Config():

    def __init__(self, filename, script_dir):
        self.dict = {}
        self.config_file = filename
        self.parser = configparser.RawConfigParser(allow_no_value=True)

        self.load_defaults(script_dir)

        print("Loading Configuration File: " + str(self.config_file))
        self.read_config(self.config_file)

        self.config_verification()

    def load_defaults(self, script_dir):

        data_dir = pathlib.Path(script_dir).joinpath('data')
        www_dir = pathlib.Path(data_dir).joinpath('www')

        self.dict["filedir"] = {
                                    "script_dir": script_dir,
                                    "data_dir": data_dir,

                                    "cache_dir": pathlib.Path(data_dir).joinpath('cache'),
                                    "internal_config": pathlib.Path(data_dir).joinpath('internal_config'),
                                    "www_dir": www_dir,
                                    "www_images_dir": pathlib.Path(www_dir).joinpath('images'),
                                    "www_templates_dir": pathlib.Path(www_dir).joinpath('templates'),
                                    "font": pathlib.Path(data_dir).joinpath('garamond.ttf'),
                                    "favicon": pathlib.Path(data_dir).joinpath('favicon.ico'),
                                    "epg_cache": {},
                                    }

        for conffile in os.listdir(self.dict["filedir"]["internal_config"]):
            conffilepath = os.path.join(self.dict["filedir"]["internal_config"], conffile)
            if str(conffilepath).endswith(".ini"):
                self.read_config(conffilepath)

    def read_config(self, conffilepath):
        config_handler = configparser.ConfigParser()
        config_handler.read(conffilepath)
        for each_section in config_handler.sections():
            if each_section.lower() not in list(self.dict.keys()):
                self.dict[each_section.lower()] = {}
            for (each_key, each_val) in config_handler.items(each_section):
                if not each_val:
                    each_val = None
                elif each_val.lower() in ["none", "false"]:
                    each_val = False
                elif each_val.lower() in ["true"]:
                    each_val = True
                elif isint(each_val):
                    each_val = int(each_val)
                elif isfloat(each_val):
                    each_val = float(each_val)
                elif is_arithmetic(each_val):
                    each_val = eval(each_val)
                elif "," in each_val:
                    each_val = each_val.split(",")
                self.dict[each_section.lower()][each_key.lower()] = each_val

    def write(self, section, key, value):
        if section == self.dict["main"]["dictpopname"]:
            self.dict["origin"][key] = value
        else:
            self.dict[section][key] = value

        config_handler = configparser.ConfigParser()
        config_handler.read(self.config_file)

        if not config_handler.has_section(section):
            config_handler.add_section(section)

        config_handler.set(section, key, value)

        with open(self.config_file, 'w') as config_file:
            config_handler.write(config_file)

    def config_verification(self):

        if self.dict["main"]["thread_method"] not in ["threading", "multiprocessing"]:
            raise fHDHR.exceptions.ConfigurationError("Invalid Threading Method. Exiting...")

        if self.dict["main"]["required"]:
            required_missing = []
            if isinstance(self.dict["main"]["required"], str):
                self.dict["main"]["required"] = [self.dict["main"]["required"]]
            if len(self.dict["main"]["required"]):
                for req_item in self.dict["main"]["required"]:
                    req_section = req_item.split("/")[0]
                    req_key = req_item.split("/")[1]
                    if not self.dict[req_section][req_key]:
                        required_missing.append(req_item)
            if len(required_missing):
                raise fHDHR.exceptions.ConfigurationError("Required configuration options missing: " + ", ".join(required_missing))

        self.dict["origin"] = self.dict.pop(self.dict["main"]["dictpopname"])

        if isinstance(self.dict["main"]["valid_epg_methods"], str):
            self.dict["main"]["valid_epg_methods"] = [self.dict["main"]["valid_epg_methods"]]

        if self.dict["epg"]["method"] and self.dict["epg"]["method"] not in ["None"]:
            if isinstance(self.dict["epg"]["method"], str):
                self.dict["epg"]["method"] = [self.dict["epg"]["method"]]
            epg_methods = []
            for epg_method in self.dict["epg"]["method"]:
                if epg_method == self.dict["main"]["dictpopname"] or epg_method == "origin":
                    epg_methods.append("origin")
                elif epg_method in ["None"]:
                    raise fHDHR.exceptions.ConfigurationError("Invalid EPG Method. Exiting...")
                elif epg_method in self.dict["main"]["valid_epg_methods"]:
                    epg_methods.append(epg_method)
                else:
                    raise fHDHR.exceptions.ConfigurationError("Invalid EPG Method. Exiting...")
        self.dict["epg"]["def_method"] = self.dict["epg"]["method"][0]

        # generate UUID here for when we are not using docker
        if not self.dict["main"]["uuid"]:
            # from https://pynative.com/python-generate-random-string/
            # create a string that wouldn't be a real device uuid for
            self.dict["main"]["uuid"] = ''.join(random.choice("hijklmnopqrstuvwxyz") for i in range(8))
            self.write('main', 'uuid', self.dict["main"]["uuid"])

        if self.dict["main"]["cache_dir"]:
            if not pathlib.Path(self.dict["main"]["cache_dir"]).is_dir():
                raise fHDHR.exceptions.ConfigurationError("Invalid Cache Directory. Exiting...")
            self.dict["filedir"]["cache_dir"] = pathlib.Path(self.dict["main"]["cache_dir"])
        cache_dir = self.dict["filedir"]["cache_dir"]

        logs_dir = pathlib.Path(cache_dir).joinpath('logs')
        self.dict["filedir"]["logs_dir"] = logs_dir
        if not logs_dir.is_dir():
            logs_dir.mkdir()

        self.dict["database"]["path"] = pathlib.Path(cache_dir).joinpath('fhdhr.db')

        for epg_method in self.dict["main"]["valid_epg_methods"]:
            if epg_method and epg_method != "None":
                epg_cache_dir = pathlib.Path(cache_dir).joinpath(epg_method)
                if not epg_cache_dir.is_dir():
                    epg_cache_dir.mkdir()
                if epg_method not in list(self.dict["filedir"]["epg_cache"].keys()):
                    self.dict["filedir"]["epg_cache"][epg_method] = {}
                self.dict["filedir"]["epg_cache"][epg_method]["top"] = epg_cache_dir
                epg_web_cache_dir = pathlib.Path(epg_cache_dir).joinpath("web_cache")
                if not epg_web_cache_dir.is_dir():
                    epg_web_cache_dir.mkdir()
                self.dict["filedir"]["epg_cache"][epg_method]["web_cache"] = epg_web_cache_dir
                self.dict["filedir"]["epg_cache"][epg_method]["epg_json"] = pathlib.Path(epg_cache_dir).joinpath('epg.json')

        if self.dict["fhdhr"]["stream_type"] not in ["direct", "ffmpeg", "vlc"]:
            raise fHDHR.exceptions.ConfigurationError("Invalid stream type. Exiting...")

        opersystem = platform.system()
        self.dict["main"]["opersystem"] = opersystem
        if opersystem in ["Linux", "Darwin"]:
            # Linux/Mac
            if os.getuid() == 0 or os.geteuid() == 0:
                print('Warning: Do not run fHDHR with root privileges.')
        elif opersystem in ["Windows"]:
            # Windows
            if os.environ.get("USERNAME") == "Administrator":
                print('Warning: Do not run fHDHR as Administrator.')
        else:
            print("Uncommon Operating System, use at your own risk.")

        isdocker = is_docker()
        self.dict["main"]["isdocker"] = isdocker

        if self.dict["fhdhr"]["stream_type"] == "ffmpeg":
            try:
                ffmpeg_command = [self.dict["ffmpeg"]["ffmpeg_path"],
                                  "-version",
                                  "pipe:stdout"
                                  ]

                ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)
                ffmpeg_version = ffmpeg_proc.stdout.read()
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                ffmpeg_version = ffmpeg_version.decode().split("version ")[1].split(" ")[0]
            except FileNotFoundError:
                ffmpeg_version = None
            self.dict["ffmpeg"]["version"] = ffmpeg_version
        else:
            self.dict["ffmpeg"]["version"] = "N/A"

        if self.dict["fhdhr"]["stream_type"] == "vlc":
            try:
                vlc_command = [self.dict["vlc"]["vlc_path"],
                               "--version",
                               "pipe:stdout"
                               ]

                vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.PIPE)
                vlc_version = vlc_proc.stdout.read()
                vlc_proc.terminate()
                vlc_proc.communicate()
                vlc_version = vlc_version.decode().split("version ")[1].split('\n')[0]
            except FileNotFoundError:
                vlc_version = None
            self.dict["vlc"]["version"] = vlc_version
        else:
            self.dict["vlc"]["version"] = "N/A"

        if not self.dict["fhdhr"]["discovery_address"] and self.dict["fhdhr"]["address"] != "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = self.dict["fhdhr"]["address"]
        if not self.dict["fhdhr"]["discovery_address"] or self.dict["fhdhr"]["discovery_address"] == "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = None

    def logging_setup(self):

        log_level = self.dict["logging"]["level"].upper()

        # Create a custom logger
        logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=log_level)
        logger = logging.getLogger('fHDHR')
        log_file = os.path.join(self.dict["filedir"]["logs_dir"], 'fHDHR.log')

        # Create handlers
        # c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_file)
        # c_handler.setLevel(log_level)
        f_handler.setLevel(log_level)

        # Create formatters and add it to handlers
        # c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        # logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        return logger

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if name in list(self.dict.keys()):
            return self.dict[name]
