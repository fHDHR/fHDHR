
import fHDHR.exceptions
from fHDHR.tools import checkattr


class Origin_failed():
    def __init__(self):
        pass


class Origin():
    """
    A wrapper for Origins to maintain consistancy.
    """

    def __init__(self, fhdhr, plugin):
        self.fhdhr = fhdhr
        self.plugin = plugin
        self.plugin_utils = self.plugin.plugin_utils

        # Attempt to setup Origin Plugin
        self.instatiate_origin()

        # Setup Config Options
        self.setup_config()

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
        # Set config defaults for method
        self.fhdhr.config.set_plugin_defaults(self.name, self.default_settings)
        for default_setting in list(self.default_settings.keys()):
            setting_value = eval("self.%s" % default_setting)
            # Set Origin attributes if missing
            self.fhdhr.logger.debug("Setting %s Origin Configuration %s=%s" % (self.name, default_setting, setting_value))

    @property
    def setup_success(self):
        if type(self.method).__name__ == "Origin_failed":
            return False
        return True

    @property
    def name(self):
        return self.plugin.name.lower()

    @property
    def default_settings(self):
        # Gather Default settings to pass to origins later
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
        # Create Default Config Values and Descriptions for origins
        default_settings = self.fhdhr.config.get_plugin_defaults(default_settings)
        return default_settings

    @property
    def config_dict(self):
        return self.fhdhr.config.dict[self.name]

    @property
    def tuners(self):
        if checkattr(self.method, "tuners"):
            return self.method.tuners
        return self.config_dict["tuners"]

    @property
    def chanscan_on_start(self):
        if checkattr(self.method, "chanscan_on_start"):
            return self.method.chanscan_on_start
        return self.config_dict["chanscan_on_start"]

    @property
    def chanscan_interval(self):
        if checkattr(self.method, "chanscan_interval"):
            return self.method.chanscan_interval
        return self.config_dict["chanscan_interval"]

    @property
    def stream_method(self):
        if checkattr(self.method, "stream_method"):
            return self.method.stream_method
        return self.config_dict["stream_method"]

    @property
    def origin_quality(self):
        if checkattr(self.method, "origin_quality"):
            return self.method.origin_quality
        return self.config_dict["origin_quality"]

    @property
    def transcode_quality(self):
        if checkattr(self.method, "transcode_quality"):
            return self.method.transcode_quality
        return self.config_dict["transcode_quality"]

    @property
    def bytes_per_read(self):
        if checkattr(self.method, "bytes_per_read"):
            return self.method.bytes_per_read
        return self.config_dict["bytes_per_read"]

    @property
    def buffer_size(self):
        if checkattr(self.method, "buffer_size"):
            return self.method.buffer_size
        return self.config_dict["buffer_size"]

    @property
    def stream_restore_attempts(self):
        if checkattr(self.method, "stream_restore_attempts"):
            return self.method.stream_restore_attempts
        return self.config_dict["stream_restore_attempts"]

    def get_channels(self):
        if checkattr(self.method, "get_channels"):
            return self.method.get_channels()
        return []

    def get_channel_stream(self, chandict, stream_args):
        if checkattr(self.method, "get_channel_stream"):
            return self.method.get_channel_stream(chandict, stream_args)
        return None

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.method, name):
            return eval("self.method.%s" % name)
