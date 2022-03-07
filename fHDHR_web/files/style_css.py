from flask import Response
import pathlib
from io import StringIO


class Style_CSS():
    endpoints = ["/style.css"]
    endpoint_name = "file_style_css"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.internal_style_file = pathlib.Path(
            self.fhdhr.config.internal["paths"]["www_dir"]).joinpath('style.css')

        self.internal_style = StringIO()
        self.internal_style.write(open(self.internal_style_file).read())

        self.pull_external_theme()

    def pull_external_theme(self):
        self.external_style = None
        self.external_style_address = None
        if self.fhdhr.config.dict["web_ui"]["theme"]:
            if self.fhdhr.config.dict["web_ui"]["theme"].startswith(tuple(["http://", "https://"])):
                css_req = self.fhdhr.web.session.get(self.fhdhr.config.dict["web_ui"]["theme"])
                self.external_style = StringIO(css_req.text)
                self.external_style_address = self.fhdhr.config.dict["web_ui"]["theme"]

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        main_output = StringIO()

        main_output.write(self.internal_style.getvalue())
        if self.fhdhr.config.dict["web_ui"]["theme"]:
            if self.fhdhr.config.dict["web_ui"]["theme"] != self.external_style_address:
                self.pull_external_theme()
            if self.external_style:
                main_output.write(self.external_style.getvalue())

        return Response(status=200, response=main_output.getvalue(), mimetype="text/css")
