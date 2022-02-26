
import fHDHR.exceptions
from fHDHR.tools import checkattr


class Origin_StandIN():
    """
    A standin for Origins that fail to setup properly.
    """

    def __init__(self):
        self.setup_success = False

    def get_channels(self):
        return []

    def get_channel_stream(self, chandict, stream_args):
        return None


class Origins():
    """
    fHDHR Origins system.
    """

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        # Gather Default settings to pass to origins later
        self.default_settings = {
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
        self.default_settings = self.fhdhr.config.get_plugin_defaults(self.default_settings)

        self.origins_dict = {}
        self.origin_selfadd()

        self.fhdhr.logger.debug("Giving Packaged non-origin Origin Plugins access to base origin plugin.")

        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"] and self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod_type"] == "origin":
                self.fhdhr.plugins.plugins[plugin_name].plugin_utils.origin = self.origins_dict[self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"].lower()]

    @property
    def valid_origins(self):
        """
        Generate a list of valid origins.
        """

        return [origin for origin in list(self.origins_dict.keys())]

    def origin_selfadd(self):
        """
        Import Origins.
        """

        self.fhdhr.logger.info("Detecting and Opening any found origin plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("origin"):

            method = self.fhdhr.plugins.plugins[plugin_name].name.lower()
            self.fhdhr.logger.info("Found Origin: %s" % method)

            try:
                plugin_utils = self.fhdhr.plugins.plugins[plugin_name].plugin_utils
                self.origins_dict[method] = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(plugin_utils)
                self.fhdhr.logger.info("%s Origin Setup Success" % method)
                self.origins_dict[method].setup_success = True

            except fHDHR.exceptions.OriginSetupError as e:
                self.fhdhr.logger.error("%s Origin Setup Failed: %s" % (method, e))
                self.origins_dict[method] = Origin_StandIN()

            except Exception as e:
                self.fhdhr.logger.error("%s Origin Setup Failed: %s" % (method, e))
                self.origins_dict[method] = Origin_StandIN()

            # Set config defaults for method
            self.fhdhr.config.set_plugin_defaults(method, self.default_settings)

            for default_setting in list(self.default_settings.keys()):

                # Set Origin attributes if missing
                if not checkattr(self.origins_dict[method], default_setting):
                    self.fhdhr.logger.debug("Setting %s %s attribute to: %s" % (method, default_setting, self.fhdhr.config.dict[method][default_setting]))
                    setattr(self.origins_dict[method], default_setting, self.fhdhr.config.dict[method][default_setting])
