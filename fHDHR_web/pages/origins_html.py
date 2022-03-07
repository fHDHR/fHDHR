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
        return self.handler(*args)

    def handler(self, *args):

        origin_name = request.args.get('origin', default=None, type=str)
        if not origin_name:
            origin_name = self.fhdhr.origins.first_origin

        origin_info_dict = {}
        origin_settings_dict = {}
        origin_plugin_dict = {}
        origin_obj = None

        if origin_name:
            origin_obj = self.fhdhr.origins.get_origin_obj(origin_name)

        if origin_obj:
            origin_info_dict.update({
                                    "Setup Success": origin_obj.setup_success,
                                    "Channel Count (total)": origin_obj.count_channels,
                                    "Channel Count (enabled)": origin_obj.count_channels_enabled,
                                    })

            tuners_in_use = self.fhdhr.device.tuners.inuse_tuner_count(origin_obj.name)
            max_tuners = self.fhdhr.origins.get_origin_property(origin_obj.name, "tuners")
            origin_info_dict["Tuner Usage"] = "%s/%s" % (str(tuners_in_use), str(max_tuners))

            for setting in list(origin_obj.default_settings.keys()):
                origin_settings_dict.update({setting: origin_obj.get_config_value(setting)})

            # Pull information from the origin plugin
            origin_plugin_dict.update(origin_obj.webpage_dict)

        return render_template('origins.html', request=request, session=session, fhdhr=self.fhdhr,
                               origin_obj=origin_obj, origin_name=origin_name, origin_info_dict=origin_info_dict,
                               origin_plugin_dict=origin_plugin_dict, origin_settings_dict=origin_settings_dict,
                               list=list, len=len)
