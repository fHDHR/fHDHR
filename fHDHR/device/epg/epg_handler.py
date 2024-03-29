
import time

import fHDHR.exceptions
from fHDHR.tools import checkattr


class EPG_failed():
    def __init__(self):
        pass


class EPG_Handler():
    """
    A wrapper for epg method to maintain consistancy.
    """

    def __init__(self, fhdhr, plugin, channels):
        self.fhdhr = fhdhr
        self.plugin = plugin
        self.plugin_utils = self.plugin.plugin_utils
        self.channels = channels

        self._epgdict = {}

        # Attempt to setup EPG Plugin
        self.instatiate_epg()

        # Setup Config Options
        self.setup_config()

    """Functions/properties called During init"""

    def instatiate_epg(self):

        try:
            self.method = self.plugin.Plugin_OBJ(self.channels, self.plugin_utils)

        except fHDHR.exceptions.EPGSetupError as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "%s EPG Setup Failed" % self.name)
            self.fhdhr.logger.error(error_out)
            self.method = EPG_failed()

        except Exception as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "%s EPG Setup Failed" % self.name)
            self.fhdhr.logger.error(error_out)
            self.method = EPG_failed()

    def setup_config(self):
        """Set config defaults for method"""

        self.fhdhr.config.set_plugin_defaults(self.name, self.default_settings)

        for default_setting in list(self.default_settings.keys()):
            setting_value = self.get_config_value(default_setting)

            """Set EPG attributes if missing"""
            self.fhdhr.logger.debug("Setting %s EPG Configuration %s=%s" % (self.name, default_setting, setting_value))

    @property
    def default_settings(self):
        # Gather Default settings to pass to epg method later
        default_settings = {
            "epg_update_frequency": {"section": "epg", "option": "update_frequency"},
            "epg_xmltv_offset": {"section": "epg", "option": "xmltv_offset"},
            "epg_update_on_start": {"section": "epg", "option": "epg_update_on_start"},
            }
        # Create Default Config Values and Descriptions for epg method
        default_settings = self.fhdhr.config.get_plugin_defaults(default_settings)
        return default_settings

    def get_default_value(self, setting):
        default_settings = self.default_settings
        if setting not in list(default_settings.keys()):
            return None
        conf_section = default_settings[setting]["section"]
        conf_option = default_settings[setting]["option"]
        return self.fhdhr.config.dict[conf_section][conf_option]

    @property
    def config_dict(self):
        return self.fhdhr.config.dict[self.name]

    def get_config_value(self, epg_attr):
        """
        Returns configuration values in the following order
        1) If the plugin manually handles it
        2) The value we use in the config system
        """

        if checkattr(self.method, epg_attr):
            return eval("self.method.%s" % epg_attr)

        if self.config_dict[epg_attr]:
            return self.config_dict[epg_attr]

        return self.get_default_value(epg_attr)

    """Expected Properties for an EPG"""

    @property
    def setup_success(self):
        if type(self.method).__name__ == "EPG_failed":
            return False
        return True

    def has_method(self, method):
        if checkattr(self.method, method):
            return True
        return False

    @property
    def name(self):
        return self.plugin.name.lower()

    def clear_cache(self):
        if checkattr(self.method, "clear_cache"):
            self.method.clear_cache()
        self._epgdict = {}
        self.fhdhr.db.delete_fhdhr_value("epg_dict", self.name)

    def get_epg(self):

        if len(self._epgdict.keys()):
            return self._epgdict

        self._epgdict = self.fhdhr.db.get_fhdhr_value("epg_dict", self.name) or {}

    def update_epg(self):
        if checkattr(self.method, "update_epg"):
            return self.method.update_epg()
        return {}

    def set_epg(self, sorted_chan_guide):
        self._epgdict = sorted_chan_guide
        self.fhdhr.db.set_fhdhr_value("epg_dict", self.name, sorted_chan_guide)
        self.fhdhr.db.set_fhdhr_value("epg", "update_time", self.name, time.time())

    """Dirty Shortcut area"""

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.method, name):
            return eval("self.method.%s" % name)

        if checkattr(self.plugin_utils, name):
            return eval("self.plugin_utils.%s" % name)

        if name in list(self.default_settings.keys()):
            return self.get_config_value(name)
