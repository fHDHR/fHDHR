import os
import sys
import platform

from fHDHR import fHDHR_VERSION
from fHDHR.tools import is_docker


class Versions():

    def __init__(self, settings, fHDHR_web, logger):
        self.fHDHR_web = fHDHR_web
        self.logger = logger

        self.dict = {}

        self.register_fhdhr()
        self.register_env()

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
                self.logger.warning('Warning: Do not run fHDHR with root privileges.')
        elif opersystem in ["Windows"]:
            # Windows
            if os.environ.get("USERNAME") == "Administrator":
                self.logger.warning('Warning: Do not run fHDHR as Administrator.')
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
