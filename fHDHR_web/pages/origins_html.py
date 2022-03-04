from flask import request, session, render_template


class Origins_HTML():
    endpoints = ["/origins", "/origins.html"]
    endpoint_name = "origins_guide_html"
    endpoint_access_level = 0
    pretty_name = "Origins"
    endpoint_category = "pages"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        origin_methods = self.fhdhr.origins.list_origins

        origin_name = request.args.get('origin', default=None, type=str)
        if not origin_name:
            origin_name = self.fhdhr.origins.first_origin

        origin_info_dict = {}
        origin_settings_dict = {}
        origin_plugin_dict = {}
        origin = None

        if origin_name:
            origin = self.fhdhr.origins.get_origin(origin_name)

        if origin:
            origin_info_dict.update({
                                    "Setup Success": origin.setup_success,
                                    "Channel Count (total)": origin.count_channels,
                                    "Channel Count (enabled)": origin.count_channels_enabled,
                                    })

            for setting in list(origin.default_settings.keys()):
                origin_settings_dict.update({setting: origin.get_config_value(setting)})

            # Pull information from the origin plugin
            origin_plugin_dict.update(origin.webpage_dict)

        return render_template('origins.html', request=request, session=session, fhdhr=self.fhdhr,
                               origin_methods=origin_methods, origin=origin, origin_name=origin_name, origin_info_dict=origin_info_dict,
                               origin_plugin_dict=origin_plugin_dict, origin_settings_dict=origin_settings_dict,
                               list=list, len=len)
