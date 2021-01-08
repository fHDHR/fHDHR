from flask import request, render_template, session


class Tools_HTML():
    endpoints = ["/tools", "/tools.html"]
    endpoint_name = "tools_html"
    endpoint_access_level = 2
    pretty_name = "Tools"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('tools.html', session=session, request=request, fhdhr=self.fhdhr)
