import os
import sys
import platform

from fHDHR import fHDHR_VERSION
from fHDHR.tools import is_docker


class Versions():

    def __init__(self, settings, fHDHR_web, plugins):
        self.plugins = plugins
        self.fHDHR_web = fHDHR_web
        self.dict = {}

        self.register_fhdhr()
        self.register_env()
        self.register_plugins()

    def register_version(self, item_name, item_version, item_type):
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

        opersystem = platform.system()
        self.register_version("Operating System", opersystem, "env")
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
        self.register_version("Docker", isdocker, "env")

    def register_plugins(self):
        plugin_names = []
        for plugin in list(self.plugins.plugins.keys()):
            if self.plugins.plugins[plugin].plugin_name not in plugin_names:
                plugin_names.append(self.plugins.plugins[plugin].plugin_name)
                self.register_version(self.plugins.plugins[plugin].plugin_name, self.plugins.plugins[plugin].manifest["version"], "plugin")
