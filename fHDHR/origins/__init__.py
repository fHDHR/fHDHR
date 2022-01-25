
import fHDHR.exceptions


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
            "stream_method": {"section": "fhdhr", "option": "default_stream_method"},
            "origin_quality": {"section": "streaming", "option": "origin_quality"},
            "transcode_quality": {"section": "streaming", "option": "transcode_quality"},
            "bytes_per_read": {"section": "streaming", "option": "bytes_per_read"},
            "buffer_size": {"section": "streaming", "option": "buffer_size"},
            "stream_restore_attempts": {"section": "streaming", "option": "stream_restore_attempts"},
            }

        self.conf_components = ["value", "description", "valid_options",
                                "config_file", "config_web", "valid_options",
                                "config_web_hidden", "required"]

        # Create Default Config Values and Descriptions for origins
        for default_setting in list(self.default_settings.keys()):
            conf_section = self.default_settings[default_setting]["section"]
            conf_option = self.default_settings[default_setting]["option"]

            # Pull values from config system and set them as defaults here
            for conf_component in self.conf_components:
                self.default_settings[default_setting][conf_component] = self.fhdhr.config.conf_default[conf_section][conf_option][conf_component]

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
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "origin":

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

                # Create config section in config system
                if method not in list(self.fhdhr.config.dict.keys()):
                    self.fhdhr.config.dict[method] = {}

                # Create config defaults section in config system
                if method not in list(self.fhdhr.config.conf_default.keys()):
                    self.fhdhr.config.conf_default[method] = {}

                for default_setting in list(self.default_settings.keys()):

                    # create conf_option in config section for origin method with default value if missing
                    if default_setting not in list(self.fhdhr.config.dict[method].keys()):
                        self.fhdhr.config.dict[method][default_setting] = self.default_settings[default_setting]["value"]
                        self.fhdhr.logger.debug("Setting configuration [%s]%s=%s" % (method, default_setting, self.fhdhr.config.dict[method][default_setting]))

                    # create conf_option in config defaults section for origin method with default values if missing
                    if default_setting not in list(self.fhdhr.config.conf_default[method].keys()):
                        self.fhdhr.config.conf_default[method][default_setting] = {}
                        for conf_component in self.conf_components:
                            if conf_component not in list(self.fhdhr.config.conf_default[method][default_setting].keys()):
                                self.fhdhr.config.conf_default[method][default_setting][conf_component] = self.default_settings[default_setting][conf_component]

                    # Set Origin attributes if missing
                    if not hasattr(self.origins_dict[method], default_setting):
                        self.fhdhr.logger.debug("Setting %s %s attribute to: %s" % (method, default_setting, self.fhdhr.config.dict[method][default_setting]))
                        setattr(self.origins_dict[method], default_setting, self.fhdhr.config.dict[method][default_setting])
