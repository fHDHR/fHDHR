from flask import request, render_template


class xmlTV_HTML():
    endpoints = ["/xmltv", "/xmltv.html"]
    endpoint_name = "xmltv_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('xmltv.html', request=request, fhdhr=self.fhdhr)
