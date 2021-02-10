from flask import request, render_template, session


class xmlTV_HTML():
    endpoints = ["/xmltv", "/xmltv.html"]
    endpoint_name = "page_xmltv_html"
    endpoint_access_level = 1
    endpoint_category = "pages"
    pretty_name = "XMLTV"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('xmltv.html', request=request, session=session, fhdhr=self.fhdhr)
