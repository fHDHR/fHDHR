from flask import request, render_template, session


class Settings_HTML():
    endpoints = ["/settings", "/settings.html"]
    endpoint_name = "page_settings_html"
    endpoint_access_level = 1
    pretty_name = "Settings"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        web_settings_dict = {}
        for config_section in list(self.fhdhr.config.conf_default.keys()):
            web_settings_dict[config_section] = {}

            for config_item in list(self.fhdhr.config.conf_default[config_section].keys()):
                if self.fhdhr.config.conf_default[config_section][config_item]["config_web"]:
                    real_config_section = config_section
                    if config_section == self.fhdhr.config.dict["main"]["dictpopname"]:
                        real_config_section = "origin"
                    web_settings_dict[config_section][config_item] = {
                        "value": self.fhdhr.config.dict[real_config_section][config_item],
                        "value_default": self.fhdhr.config.conf_default[config_section][config_item]["value"],
                        "hide": self.fhdhr.config.conf_default[config_section][config_item]["config_web_hidden"]
                        }
            if not len(web_settings_dict[config_section].keys()):
                del web_settings_dict[config_section]

        return render_template('settings.html', session=session, request=request, fhdhr=self.fhdhr, web_settings_dict=web_settings_dict, list=list)
