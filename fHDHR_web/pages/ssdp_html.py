from flask import request, render_template, session


class SSDP_HTML():
    endpoints = ["/ssdp", "/ssdp.html"]
    endpoint_name = "page_ssdp_html"
    endpoint_access_level = 1
    endpoint_category = "tool_pages"
    pretty_name = "SSDP"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('ssdp.html', request=request, session=session, fhdhr=self.fhdhr)
