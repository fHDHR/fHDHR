import os
import importlib

from .plugin_utils import Plugin_Utils
from fHDHR.tools import checkattr


class Plugin():
    """
    Methods for a Plugin.
    """

    def __init__(self, config, logger, db, versions, plugin_name, plugin_path, plugin_conf, plugin_manifest):
        self.config = config
        self.db = db
        self.logger = logger
        self.versions = versions

        # Gather Info about Plugin
        self.plugin_name = plugin_name
        self.modname = os.path.basename(plugin_path)
        self.path = plugin_path
        self.multi_plugin = (self.plugin_name != self.modname)
        self.default_conf = plugin_conf
        self.manifest = plugin_manifest

        if self.multi_plugin:
            self.plugin_dict_name = "%s.%s" % (plugin_name, self.modname)

        else:
            self.plugin_dict_name = plugin_name

        self.plugin_utils = Plugin_Utils(config, logger, db, versions, plugin_name, plugin_manifest, self.modname, self.path)

        # Load the module
        self._module = self._load()

        self._module.Plugin_OBJ.plugin_utils = self.plugin_utils

        # Gather Default settings to pass to plugin
        self.default_settings = {
            "proxy_enabled": {"section": "proxy", "option": "enabled"},
            "proxy_proto": {"section": "proxy", "option": "proto"},
            "proxy_host": {"section": "proxy", "option": "host"},
            "proxy_port": {"section": "proxy", "option": "port"},
            }

        # Create Default Config Values and Descriptions for plugin
        self.default_settings = self.config.get_plugin_defaults(self.default_settings)

        # Setup proxy settings for the plugin
        # self.setup_proxy()

    def setup(self):
        """
        If a plugin has a setup function, run it.
        """

        if self.has_setup():
            self.logger.info("%s has a pre-flight setup routine. Running now." % self.plugin_dict_name)
            self._module.setup(self, self.versions)

    def has_setup(self):
        """
        Check if a plugin has a setup function.
        """

        return checkattr(self._module, 'setup')

    def _load(self):
        """
        Load the plugin.
        """

        mod = importlib.import_module('plugins.'+self.plugin_dict_name)
        return mod

    @property
    def name(self):
        """
        Shortcut to plugin manifest value for name.
        """

        return self.manifest["name"]

    @property
    def version(self):
        """
        Shortcut to plugin manifest value for version.
        """

        return self.manifest["version"]

    @property
    def type(self):
        """
        Shortcut to plugin manifest value for type.
        """

        return self.manifest["type"]

    def setup_proxy(self):

        # Set config defaults for plugin name
        self.config.set_plugin_defaults(self.name.lower(), self.default_settings)

        for default_setting in list(self.default_settings.keys()):

            # Set plugin attributes if missing
            if not checkattr(self._module.Plugin_OBJ, default_setting):
                self.logger.debug("Setting %s %s attribute to: %s" % (self.plugin_name, default_setting, self.config.dict[self.name.lower()][default_setting]))
                setattr(self._module.Plugin_OBJ, default_setting, self.config.dict[self.name.lower()][default_setting])

    @property
    def proxy_domains_list(self):
        """Allow Plugins to return a list of domains for proxying"""
        if checkattr(self._module.Plugin_OBJ, 'proxy_domains_list'):
            domains_list = self._module.Plugin_OBJ.proxy_domains_list
            if isinstance(domains_list, str):
                domains_list = [domains_list]
            return domains_list
        return []

    @property
    def Plugin_OBJ(self):
        return self._module.Plugin_OBJ
