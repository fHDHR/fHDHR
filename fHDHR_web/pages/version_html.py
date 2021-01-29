from flask import request, render_template, session


class Version_HTML():
    endpoints = ["/version", "/version.html"]
    endpoint_name = "page_version_html"
    endpoint_access_level = 1
    endpoint_category = "tool_pages"
    pretty_name = "Version"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        version_dict = {}
        for key in list(self.fhdhr.config.internal["versions"].keys()):
            version_dict[key] = self.fhdhr.config.internal["versions"][key]

        # Sort the Version Info
        sorted_version_list = sorted(version_dict, key=lambda i: (version_dict[i]['type'], version_dict[i]['name']))
        sorted_version_dict = {
                                "fHDHR": version_dict["fHDHR"],
                                "fHDHR_web": version_dict["fHDHR_web"]
                                }
        for version_item in sorted_version_list:
            if version_item not in ["fHDHR", "fHDHR_web"]:
                sorted_version_dict[version_item] = version_dict[version_item]

        return render_template('version.html', request=request, session=session, fhdhr=self.fhdhr, version_dict=sorted_version_dict, list=list)
