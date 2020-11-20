from flask import request, render_template


class Version_HTML():
    endpoints = ["/version", "/version.html"]
    endpoint_name = "version_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):
        version_dict = {}
        for key in list(self.fhdhr.config.internal["versions"].keys()):
            version_dict[key] = self.fhdhr.config.internal["versions"][key]
        return render_template('version.html', request=request, fhdhr=self.fhdhr, version_dict=version_dict, list=list)
