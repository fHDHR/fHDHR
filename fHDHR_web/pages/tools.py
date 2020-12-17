from flask import request, render_template


class Tools_HTML():
    endpoints = ["/tools", "/tools.html"]
    endpoint_name = "tools_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('tools.html', request=request, fhdhr=self.fhdhr)
