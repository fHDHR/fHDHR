import os
import sys
import random
import configparser
import pathlib
import subprocess
import platform
import json

import fHDHR.exceptions
from fHDHR import fHDHR_VERSION
from fHDHR.tools import isint, isfloat, is_arithmetic, is_docker


class Config():

    def __init__(self, filename, script_dir, origin, fHDHR_web):
        self.origin = origin
        self.fHDHR_web = fHDHR_web

        self.internal = {}
        self.conf_default = {}
        self.dict = {}
        self.config_file = filename

        self.initial_load(script_dir)
        self.config_verification()

    def initial_load(self, script_dir):

        data_dir = pathlib.Path(script_dir).joinpath('data')
        fHDHR_web_dir = pathlib.Path(script_dir).joinpath('fHDHR_web')
        www_dir = pathlib.Path(fHDHR_web_dir).joinpath('www_dir')
        origin_dir = pathlib.Path(script_dir).joinpath('origin')

        self.internal["paths"] = {
                                    "script_dir": script_dir,
                                    "data_dir": data_dir,
                                    "alternative_epg": pathlib.Path(script_dir).joinpath('alternative_epg'),
                                    "origin": origin_dir,
                                    "origin_web": pathlib.Path(origin_dir).joinpath('origin_web'),
                                    "cache_dir": pathlib.Path(data_dir).joinpath('cache'),
                                    "internal_config": pathlib.Path(data_dir).joinpath('internal_config'),
                                    "fHDHR_web_dir": fHDHR_web_dir,
                                    "www_dir": www_dir,
                                    "www_templates_dir": pathlib.Path(fHDHR_web_dir).joinpath('templates'),
                                    "font": pathlib.Path(data_dir).joinpath('garamond.ttf'),
                                    }

        for conffile in os.listdir(self.internal["paths"]["internal_config"]):
            conffilepath = os.path.join(self.internal["paths"]["internal_config"], conffile)
            if str(conffilepath).endswith(".json"):
                self.read_json_config(conffilepath)

        for file_item in os.listdir(self.internal["paths"]["fHDHR_web_dir"]):
            file_item_path = pathlib.Path(self.internal["paths"]["fHDHR_web_dir"]).joinpath(file_item)
            if str(file_item_path).endswith("_conf.json"):
                self.read_json_config(file_item_path)

        for dir_type in ["alternative_epg", "origin"]:

            for file_item in os.listdir(self.internal["paths"][dir_type]):
                file_item_path = pathlib.Path(self.internal["paths"][dir_type]).joinpath(file_item)
                if file_item_path.is_dir():
                    for sub_file_item in os.listdir(file_item_path):
                        sub_file_item_path = pathlib.Path(file_item_path).joinpath(sub_file_item)
                        if str(sub_file_item_path).endswith("_conf.json"):
                            self.read_json_config(sub_file_item_path)
                else:
                    if str(file_item_path).endswith("_conf.json"):
                        self.read_json_config(file_item_path)

        print("Loading Configuration File: %s" % self.config_file)
        self.read_ini_config(self.config_file)

        self.load_versions()

    def load_versions(self):

        self.internal["versions"] = {}

        self.internal["versions"]["fHDHR"] = fHDHR_VERSION

        self.internal["versions"]["fHDHR_web"] = self.fHDHR_web.fHDHR_web_VERSION

        self.internal["versions"][self.origin.ORIGIN_NAME] = self.origin.ORIGIN_VERSION

        self.internal["versions"]["Python"] = sys.version

        opersystem = platform.system()
        self.internal["versions"]["Operating System"] = opersystem
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
        self.internal["versions"]["Docker"] = isdocker

        if self.dict["streaming"]["method"] == "ffmpeg":
            try:
                ffmpeg_command = [self.dict["ffmpeg"]["path"],
                                  "-version",
                                  "pipe:stdout"
                                  ]

                ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)
                ffmpeg_version = ffmpeg_proc.stdout.read()
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                ffmpeg_proc.kill()
                ffmpeg_version = ffmpeg_version.decode().split("version ")[1].split(" ")[0]
            except FileNotFoundError:
                ffmpeg_version = "Missing"
                print("Failed to find ffmpeg.")
            self.internal["versions"]["ffmpeg"] = ffmpeg_version

        if self.dict["streaming"]["method"] == "vlc":
            try:
                vlc_command = [self.dict["vlc"]["path"],
                               "--version",
                               "pipe:stdout"
                               ]

                vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.PIPE)
                vlc_version = vlc_proc.stdout.read()
                vlc_proc.terminate()
                vlc_proc.communicate()
                vlc_proc.kill()
                vlc_version = vlc_version.decode().split("version ")[1].split('\n')[0]
            except FileNotFoundError:
                vlc_version = "Missing"
                print("Failed to find vlc.")
            self.internal["versions"]["vlc"] = vlc_version

    def read_json_config(self, conffilepath):
        with open(conffilepath, 'r') as jsonconf:
            confimport = json.load(jsonconf)
        for section in list(confimport.keys()):

            if section not in self.dict.keys():
                self.dict[section] = {}

            if section not in self.conf_default.keys():
                self.conf_default[section] = {}

            for key in list(confimport[section].keys()):

                if key not in list(self.conf_default[section].keys()):
                    self.conf_default[section][key] = {}

                confvalue = confimport[section][key]["value"]
                if key == "xmltv_offset":
                    confvalue = str(confvalue)
                elif isint(confvalue):
                    confvalue = int(confvalue)
                elif isfloat(confvalue):
                    confvalue = float(confvalue)
                elif is_arithmetic(confvalue):
                    confvalue = eval(confvalue)
                elif "," in confvalue:
                    confvalue = confvalue.split(",")
                elif str(confvalue).lower() in ["none"]:
                    confvalue = None
                elif str(confvalue).lower() in ["false"]:
                    confvalue = False
                elif str(confvalue).lower() in ["true"]:
                    confvalue = True

                self.dict[section][key] = confvalue

                self.conf_default[section][key]["value"] = confvalue

                for config_option in ["config_web_hidden", "config_file", "config_web"]:
                    if config_option not in list(confimport[section][key].keys()):
                        config_option_value = False
                    else:
                        config_option_value = confimport[section][key][config_option]
                        if str(config_option_value).lower() in ["none"]:
                            config_option_value = None
                        elif str(config_option_value).lower() in ["false"]:
                            config_option_value = False
                        elif str(config_option_value).lower() in ["true"]:
                            config_option_value = True
                    self.conf_default[section][key][config_option] = config_option_value

    def read_ini_config(self, conffilepath):
        config_handler = configparser.ConfigParser()
        config_handler.read(conffilepath)
        for each_section in config_handler.sections():
            if each_section.lower() not in list(self.dict.keys()):
                self.dict[each_section.lower()] = {}
            for (each_key, each_val) in config_handler.items(each_section):
                if not each_val:
                    each_val = None
                elif each_key == "xmltv_offset":
                    each_val = str(each_val)
                elif each_val.lower() in ["none"]:
                    each_val = None
                elif each_val.lower() in ["false"]:
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

                import_val = True
                if each_section in list(self.conf_default.keys()):
                    if each_key in list(self.conf_default[each_section].keys()):
                        if not self.conf_default[each_section][each_key]["config_file"]:
                            import_val = False

                if import_val:
                    self.dict[each_section.lower()][each_key.lower()] = each_val

    def write(self, section, key, value):

        if not value:
            value = None
        if value.lower() in ["none"]:
            value = None
        elif value.lower() in ["false"]:
            value = False
        elif value.lower() in ["true"]:
            value = True
        elif isint(value):
            value = int(value)
        elif isfloat(value):
            value = float(value)
        elif isinstance(value, list):
            ",".join(value)

        if section == self.dict["main"]["dictpopname"]:
            self.dict["origin"][key] = value
        else:
            self.dict[section][key] = value

        config_handler = configparser.ConfigParser()
        config_handler.read(self.config_file)

        if not config_handler.has_section(section):
            config_handler.add_section(section)

        config_handler.set(section, key, str(value))

        with open(self.config_file, 'w') as config_file:
            config_handler.write(config_file)

    def config_verification(self):

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
                raise fHDHR.exceptions.ConfigurationError("Required configuration options missing: %s" % ", ".join(required_missing))

        self.dict["origin"] = self.dict.pop(self.dict["main"]["dictpopname"])

        if isinstance(self.dict["epg"]["valid_epg_methods"], str):
            self.dict["epg"]["valid_epg_methods"] = [self.dict["epg"]["valid_epg_methods"]]

        if self.dict["epg"]["method"] and self.dict["epg"]["method"] not in ["None"]:
            if isinstance(self.dict["epg"]["method"], str):
                self.dict["epg"]["method"] = [self.dict["epg"]["method"]]
            epg_methods = []
            for epg_method in self.dict["epg"]["method"]:
                if epg_method == self.dict["main"]["dictpopname"] or epg_method == "origin":
                    epg_methods.append("origin")
                elif epg_method in ["None"]:
                    raise fHDHR.exceptions.ConfigurationError("Invalid EPG Method. Exiting...")
                elif epg_method in self.dict["epg"]["valid_epg_methods"]:
                    epg_methods.append(epg_method)
                else:
                    raise fHDHR.exceptions.ConfigurationError("Invalid EPG Method. Exiting...")
        self.dict["epg"]["def_method"] = self.dict["epg"]["method"][0]

        if not self.dict["main"]["uuid"]:
            self.dict["main"]["uuid"] = ''.join(random.choice("hijklmnopqrstuvwxyz") for i in range(8))
            self.write('main', 'uuid', self.dict["main"]["uuid"])

        if self.dict["main"]["cache_dir"]:
            if not pathlib.Path(self.dict["main"]["cache_dir"]).is_dir():
                raise fHDHR.exceptions.ConfigurationError("Invalid Cache Directory. Exiting...")
            self.internal["paths"]["cache_dir"] = pathlib.Path(self.dict["main"]["cache_dir"])
        cache_dir = self.internal["paths"]["cache_dir"]

        logs_dir = pathlib.Path(cache_dir).joinpath('logs')
        self.internal["paths"]["logs_dir"] = logs_dir
        if not logs_dir.is_dir():
            logs_dir.mkdir()

        self.dict["database"]["path"] = pathlib.Path(cache_dir).joinpath('fhdhr.db')

        if self.dict["streaming"]["method"] not in ["direct", "ffmpeg", "vlc"]:
            raise fHDHR.exceptions.ConfigurationError("Invalid stream type. Exiting...")

        if not self.dict["fhdhr"]["discovery_address"] and self.dict["fhdhr"]["address"] != "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = self.dict["fhdhr"]["address"]
        if not self.dict["fhdhr"]["discovery_address"] or self.dict["fhdhr"]["discovery_address"] == "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = None

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if name in list(self.dict.keys()):
            return self.dict[name]
