import os
import random
import configparser
import pathlib

import fHDHR.exceptions
from fHDHR.tools import isint, isfloat, is_arithmetic


class Config():

    def __init__(self, filename, script_dir):
        self.dict = {}
        self.config_file = filename
        self.parser = configparser.RawConfigParser(allow_no_value=True)

        self.load_defaults(script_dir)

        print("Loading Configuration File: " + str(self.config_file))
        self.read_config(self.config_file)

        print("Verifying Configuration settings.")
        self.config_verification()

        print("Server is set to run on  " +
              str(self.dict["fhdhr"]["address"]) + ":" +
              str(self.dict["fhdhr"]["port"]))

    def load_defaults(self, script_dir):

        data_dir = pathlib.Path(script_dir).joinpath('data')
        www_dir = pathlib.Path(data_dir).joinpath('www')
        www_images_dir = pathlib.Path(www_dir).joinpath('images')

        self.dict["filedir"] = {
                                    "script_dir": script_dir,
                                    "data_dir": data_dir,

                                    "cache_dir": pathlib.Path(data_dir).joinpath('cache'),
                                    "internal_config": pathlib.Path(data_dir).joinpath('internal_config'),
                                    "www_dir": www_dir,
                                    "www_images_dir": www_images_dir,
                                    "font": pathlib.Path(data_dir).joinpath('garamond.ttf'),
                                    "favicon": pathlib.Path(data_dir).joinpath('favicon.ico'),
                                    "epg_cache": {},
                                    }

        for conffile in os.listdir(self.dict["filedir"]["internal_config"]):
            conffilepath = os.path.join(self.dict["filedir"]["internal_config"], conffile)
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

        if self.dict["fhdhr"]["epg_method"] and self.dict["fhdhr"]["epg_method"] not in ["None"]:
            if self.dict["fhdhr"]["epg_method"] == self.dict["main"]["dictpopname"]:
                self.dict["fhdhr"]["epg_method"] = "origin"
            elif self.dict["fhdhr"]["epg_method"] not in self.dict["main"]["valid_epg_methods"]:
                raise fHDHR.exceptions.ConfigurationError("Invalid EPG Method. Exiting...")
        else:
            print("EPG Method not set, will not create EPG/xmltv")

        # generate UUID here for when we are not using docker
        if not self.dict["main"]["uuid"]:
            print("No UUID found.  Generating one now...")
            # from https://pynative.com/python-generate-random-string/
            # create a string that wouldn't be a real device uuid for
            self.dict["main"]["uuid"] = ''.join(random.choice("hijklmnopqrstuvwxyz") for i in range(8))
            self.write('main', 'uuid', self.dict["main"]["uuid"])
            print("UUID set to: " + str(self.dict["main"]["uuid"]) + "...")
        else:
            print("UUID read as: " + str(self.dict["main"]["uuid"]) + "...")

        if self.dict["main"]["cache_dir"]:
            print("Verifying cache directory...")
            if not pathlib.Path(self.dict["main"]["cache_dir"]).is_dir():
                raise fHDHR.exceptions.ConfigurationError("Invalid Cache Directory. Exiting...")
            self.dict["filedir"]["cache_dir"] = pathlib.Path(self.dict["main"]["cache_dir"])
        print("Cache set to " + str(self.dict["filedir"]["cache_dir"]))
        cache_dir = self.dict["filedir"]["cache_dir"]

        self.dict["main"]["channel_numbers"] = pathlib.Path(cache_dir).joinpath("cnumbers.json")
        self.dict["main"]["ssdp_detect"] = pathlib.Path(cache_dir).joinpath("ssdp_list.json")
        self.dict["main"]["cluster"] = pathlib.Path(cache_dir).joinpath("cluster.json")

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

        if self.dict["fhdhr"]["stream_type"] not in ["direct", "ffmpeg"]:
            raise fHDHR.exceptions.ConfigurationError("Invalid stream type. Exiting...")

        if not self.dict["fhdhr"]["discovery_address"] and self.dict["fhdhr"]["address"] != "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = self.dict["fhdhr"]["address"]
        if not self.dict["fhdhr"]["discovery_address"] or self.dict["fhdhr"]["discovery_address"] == "0.0.0.0":
            self.dict["fhdhr"]["discovery_address"] = None
            print("SSDP Server disabled.")
