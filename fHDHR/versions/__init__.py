import os
import sys
import platform

from fHDHR import fHDHR_VERSION
from fHDHR.tools import is_docker


class Versions():

    def __init__(self, settings, fHDHR_web, logger, web):
        self.fHDHR_web = fHDHR_web
        self.logger = logger
        self.web = web

        self.github_org_list_url = "https://api.github.com/orgs/fHDHR/repos?type=all"
        self.github_fhdhr_core_info_url = "https://raw.githubusercontent.com/fHDHR/fHDHR/main/version.json"

        self.dict = {}
        self.official_plugins = {}

        self.register_fhdhr()
        self.register_env()

        self.get_online_versions()

    def get_online_versions(self):

        self.logger.debug("Checking for Online Plugin Information")

        official_plugins = {}

        github_org_json = self.web.session.get(self.github_org_list_url).json()

        online_plugin_names = [x["name"] for x in github_org_json if x["name"].startswith("fHDHR_plugin_")]
        for plugin_name in online_plugin_names:
            plugin_json_url = "https://raw.githubusercontent.com/fHDHR/%s/main/plugin.json" % plugin_name
            plugin_json = self.web.session.get(plugin_json_url)
            if plugin_json.status_code == 200:
                plugin_json = plugin_json.json()
                official_plugins[plugin_name] = plugin_json
        self.official_plugins = official_plugins

        core_json = self.web.session.get(self.github_fhdhr_core_info_url).json()
        for key in list(core_json.keys()):
            self.official_plugins[key] = {"name": key, "version": core_json[key], "type": "core"}

    def register_version(self, item_name, item_version, item_type):
        self.logger.debug("Registering %s item: %s %s" % (item_type, item_name, item_version))
        self.dict[item_name] = {
                                "name": item_name,
                                "version": item_version,
                                "type": item_type
                                }

    def register_fhdhr(self):

        self.register_version("fHDHR", fHDHR_VERSION, "fHDHR")
        self.register_version("fHDHR_web", self.fHDHR_web.fHDHR_web_VERSION, "fHDHR")

    def register_env(self):

        self.register_version("Python", sys.version, "env")
        if sys.version_info.major == 2 or sys.version_info < (3, 7):
            self.logger.error('Error: fHDHR requires python 3.7+. Do NOT expect support for older versions of python.')

        opersystem = platform.system()
        self.register_version("Operating System", opersystem, "env")
        if opersystem in ["Linux", "Darwin"]:
            # Linux/Mac
            if os.getuid() == 0 or os.geteuid() == 0:
                self.logger.warning('Do not run fHDHR with root privileges.')
        elif opersystem in ["Windows"]:
            # Windows
            if os.environ.get("USERNAME") == "Administrator":
                self.logger.warning('Do not run fHDHR as Administrator.')
        else:
            self.logger.warning("Uncommon Operating System, use at your own risk.")

        isdocker = is_docker()
        self.register_version("Docker", isdocker, "env")

    def register_plugins(self, plugins):
        self.logger.info("Scanning Plugins for Version Information.")
        self.plugins = plugins
        plugin_names = []
        for plugin in list(self.plugins.plugins.keys()):
            if self.plugins.plugins[plugin].plugin_name not in plugin_names:
                plugin_names.append(self.plugins.plugins[plugin].plugin_name)
                self.register_version(self.plugins.plugins[plugin].plugin_name, self.plugins.plugins[plugin].manifest["version"], "plugin")
