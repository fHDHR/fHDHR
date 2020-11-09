from flask import send_from_directory


class Favicon_ICO():
    endpoints = ["/favicon.ico"]
    endpoint_name = "favicon"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return send_from_directory(self.fhdhr.config.dict["filedir"]["www_dir"],
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')
