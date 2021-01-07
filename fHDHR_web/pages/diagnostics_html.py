from flask import request, render_template, session


class Diagnostics_HTML():
    endpoints = ["/diagnostics", "/diagnostics.html"]
    endpoint_name = "page_diagnostics_html"
    endpoint_access_level = 2
    pretty_name = "Diagnostics"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        button_dict = {}

        for route_group in list(session["route_list"].keys()):
            if route_group not in ["pages", "brython", "files"]:
                button_dict[route_group] = []
                for route_item in list(session["route_list"][route_group].keys()):
                    if not session["route_list"][route_group][route_item]["name"].startswith("page_"):
                        button_link = session["route_list"][route_group][route_item]["endpoints"][0]
                        parameter_index = 0
                        for parameter in list(session["route_list"][route_group][route_item]["endpoint_default_parameters"].keys()):
                            parameter_val = session["route_list"][route_group][route_item]["endpoint_default_parameters"][parameter]
                            if not parameter_index:
                                button_link += "?"
                            else:
                                button_link += "&"
                            button_link += "%s=%s" % (parameter, parameter_val)
                        button_link = button_link.replace("<devicekey>", self.fhdhr.config.dict["main"]["uuid"])
                        button_link = button_link.replace("<base_url>", base_url)
                        button_dict[route_group].append({
                                            "label": session["route_list"][route_group][route_item]["pretty_name"],
                                            "link": button_link,
                                            })

        return render_template('diagnostics.html', session=session, request=request, fhdhr=self.fhdhr, button_dict=button_dict, list=list)
