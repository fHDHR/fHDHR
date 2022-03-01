
import fHDHR.exceptions
from fHDHR.tools import checkattr


class Web_failed():
    def __init__(self):
        pass


class WebPlugin():
    """
    A wrapper for Web Plugins to maintain consistancy.
    """

    def __init__(self, fhdhr, plugin):
        self.fhdhr = fhdhr
        self.plugin = plugin
        self.plugin_utils = self.plugin.plugin_utils

        # Attempt to setup Web Plugin
        self.instatiate_web_plugin()

        # Setup Config Options
        self.setup_config()

    """Functions/properties called During init"""

    def instatiate_web_plugin(self):

        try:
            self.method = self.plugin.Plugin_OBJ(self.fhdhr, self.plugin_utils)

        except fHDHR.exceptions.WEBSetupError as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror)
            self.fhdhr.logger.error(error_out)
            self.method = Web_failed()

        except Exception as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror)
            self.fhdhr.logger.error(error_out)
            self.method = Web_failed()

    def setup_config(self):
        # Set config defaults for method
        self.fhdhr.config.set_plugin_defaults(self.name, self.default_settings)
        for default_setting in list(self.default_settings.keys()):
            setting_value = eval("self.%s" % default_setting)
            # Set Web Plugin attributes if missing
            self.fhdhr.logger.debug("Setting %s Web Plugin Configuration %s=%s" % (self.name, default_setting, setting_value))

    @property
    def default_settings(self):
        # Gather Default settings to pass to web plugins later
        default_settings = {
            "pages_to_refresh": {"section": "web_ui", "option": "pages_to_refresh"},
            }
        # Create Default Config Values and Descriptions for web plugins
        default_settings = self.fhdhr.config.get_plugin_defaults(default_settings)
        default_settings["pages_to_refresh"]["value"] = []
        return default_settings

    @property
    def config_dict(self):
        return self.fhdhr.config.dict[self.name]

    """Expected Properties for a web plugin"""

    @property
    def setup_success(self):
        if type(self.method).__name__ == "Web_failed":
            return False
        return True

    @property
    def name(self):
        return self.plugin.name.lower()

    @property
    def endpoint_directory(self):
        return [x for x in dir(self.method) if self.isapath(x)]

    @property
    def pages_to_refresh(self):
        if checkattr(self.method, "pages_to_refresh"):
            pages_to_refresh = self.method.pages_to_refresh
        else:
            pages_to_refresh = self.config_dict["pages_to_refresh"]
        if isinstance(pages_to_refresh, str):
            pages_to_refresh = [pages_to_refresh]
        return pages_to_refresh

    def isapath(self, item):
        """
        Ignore instances.
        """

        if item.startswith("__") and item.endswith("__"):
            return False

        not_a_page_list = ["fhdhr", "plugin_utils", "auto_page_refresh", "pages_to_refresh"]
        if item in not_a_page_list:
            return False

        if item.startswith("proxy_"):
            return False

        return True

    """Dirty Shortcut area"""

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.method, name):
            return eval("self.method.%s" % name)
