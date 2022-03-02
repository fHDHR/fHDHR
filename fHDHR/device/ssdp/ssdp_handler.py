

import fHDHR.exceptions

from fHDHR.tools import checkattr


class SSDP_failed():
    def __init__(self):
        pass


class SSDP_Handler():
    """
    A wrapper for SSDP Handlers to maintain consistancy.
    """

    def __init__(self, fhdhr, ssdp, plugin):
        self.fhdhr = fhdhr
        self.ssdp = ssdp
        self.plugin = plugin
        self.plugin_utils = self.plugin.plugin_utils

        # Attempt to setup SSDP Plugin
        self.instatiate_ssdp_handler()

        # Setup Config Options
        self.setup_config()

    """Functions/properties called During init"""

    def instatiate_ssdp_handler(self):

        try:
            self.method = self.plugin.Plugin_OBJ(self.fhdhr, self.plugin_utils, self.ssdp.broadcast_ip, self.ssdp.max_age)

        except fHDHR.exceptions.SSDPSetupError as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror)
            self.fhdhr.logger.error(error_out)
            self.method = SSDP_failed()

        except Exception as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror)
            self.fhdhr.logger.error(error_out)
            self.method = SSDP_failed()

    def setup_config(self):
        # Set config defaults for method
        self.fhdhr.config.set_plugin_defaults(self.name, self.default_settings)
        for default_setting in list(self.default_settings.keys()):
            setting_value = eval("self.%s" % default_setting)
            # Set SSDP attributes if missing
            self.fhdhr.logger.debug("Setting %s SSDP Configuration %s=%s" % (self.name, default_setting, setting_value))

    @property
    def default_settings(self):
        # Gather Default settings to pass to SSDP methods later
        default_settings = {
            "ssdp_enabled": {"section": "ssdp", "option": "enabled"},
            "ssdp_max_age": {"section": "ssdp", "option": "max_age"},
            }
        # Create Default Config Values and Descriptions for SSDP methods
        default_settings = self.fhdhr.config.get_plugin_defaults(default_settings)
        return default_settings

    @property
    def config_dict(self):
        return self.fhdhr.config.dict[self.name]

    """Expected Properties for a SSDP Handler"""

    @property
    def setup_success(self):
        if type(self.method).__name__ == "SSDP_failed":
            return False
        return True

    def has_method(self, method):
        if checkattr(self.method, "method"):
            return True
        return False

    @property
    def name(self):
        return self.plugin.name.lower()

    @property
    def notify(self):
        if checkattr(self.method, 'notify'):
            return self.method.notify
        return None

    def on_recv(self, headers, cmd, ssdp_handling_list):
        if checkattr(self.method, 'on_recv'):
            return self.method.on_recv(headers, cmd, ssdp_handling_list)

    """
    Returns configuration values in the following order
    1) If the plugin manually handles it
    2) The value we use in the config system
    """

    @property
    def enabled(self):
        if checkattr(self.method, "enabled"):
            return self.method.enabled
        return self.config_dict["ssdp_enabled"]

    @property
    def max_age(self):
        if checkattr(self.method, "max_age"):
            return self.method.max_age
        return self.config_dict["ssdp_max_age"]

    """Dirty Shortcut area"""

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.method, name):
            return eval("self.method.%s" % name)
