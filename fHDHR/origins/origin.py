
import fHDHR.exceptions
from fHDHR.tools import checkattr

from .channels import Channels


class Origin_failed():
    def __init__(self):
        pass


class Origin():
    """
    A wrapper for Origins to maintain consistancy.
    """

    def __init__(self, fhdhr, plugin, id_system):
        self.fhdhr = fhdhr
        self.plugin = plugin
        self.plugin_utils = self.plugin.plugin_utils
        self.id_system = id_system

        # Attempt to setup Origin Plugin
        self.instatiate_origin()

        # Setup Config Options
        self.setup_config()

        # Setup Channels
        self.channels = Channels(fhdhr, self, id_system)

    """Functions/properties called During init"""

    def instatiate_origin(self):

        try:
            self.method = self.plugin.Plugin_OBJ(self.plugin.plugin_utils)

        except fHDHR.exceptions.OriginSetupError as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "%s Origin Setup Failed" % self.name)
            self.fhdhr.logger.error(error_out)
            self.method = Origin_failed()

        except Exception as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "%s Origin Setup Failed" % self.name)
            self.fhdhr.logger.error(error_out)
            self.method = Origin_failed()

    def setup_config(self):
        """Set config defaults for method"""

        self.fhdhr.config.set_plugin_defaults(self.name, self.default_settings)

        for default_setting in list(self.default_settings.keys()):
            setting_value = self.get_config_value(default_setting)

            """Set Origin attributes if missing"""
            self.fhdhr.logger.debug("Setting %s Origin Configuration %s=%s" % (self.name, default_setting, setting_value))

    @property
    def default_settings(self):
        """Gather Default settings to pass to origins later"""

        default_settings = {
            "tuners": {"section": "fhdhr", "option": "default_tuners"},
            "chanscan_on_start": {"section": "fhdhr", "option": "chanscan_on_start"},
            "chanscan_interval": {"section": "fhdhr", "option": "chanscan_interval"},
            "stream_method": {"section": "streaming", "option": "method"},
            "origin_quality": {"section": "streaming", "option": "origin_quality"},
            "transcode_quality": {"section": "streaming", "option": "transcode_quality"},
            "bytes_per_read": {"section": "streaming", "option": "bytes_per_read"},
            "buffer_size": {"section": "streaming", "option": "buffer_size"},
            "stream_restore_attempts": {"section": "streaming", "option": "stream_restore_attempts"},
            }

        """Create Default Config Values and Descriptions for origins"""
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

    def get_config_value(self, origin_attr):
        """
        Returns configuration values in the following order
        1) If the plugin manually handles it
        2) The value we use in the config system
        """

        if checkattr(self.method, origin_attr):
            return eval("self.method.%s" % origin_attr)

        if self.config_dict[origin_attr]:
            return self.config_dict[origin_attr]

        return self.get_default_value(origin_attr)

    """Expected Properties for an Origin"""

    @property
    def webpage_dict(self):
        if checkattr(self.method, "webpage_dict"):
            return self.method.webpage_dict
        return {}

    @property
    def setup_success(self):
        if type(self.method).__name__ == "Origin_failed":
            return False
        return True

    def has_method(self, method):
        if checkattr(self.method, method):
            return True
        return False

    @property
    def name(self):
        return self.plugin.name.lower()

    def get_channels(self):
        if checkattr(self.method, "get_channels"):
            return self.method.get_channels()
        return []

    def get_channel_stream(self, chandict, stream_args):
        if checkattr(self.method, "get_channel_stream"):
            return self.method.get_channel_stream(chandict, stream_args)
        return None

    def prime_stream(self, tuner_number, stream_args):
        if checkattr(self.method, "prime_stream"):
            self.fhdhr.logger.info("Running %s prime_stream method." % self.name)
            self.method.prime_stream(tuner_number, stream_args)

    def close_stream(self, tuner_number, stream_args):
        if checkattr(self.method, "close_stream"):
            self.fhdhr.logger.info("Running %s close_stream method." % self.name)
            self.method.close_stream(tuner_number, stream_args)

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

        if checkattr(self.channels, name):
            return eval("self.channels.%s" % name)
