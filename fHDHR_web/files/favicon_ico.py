from flask import send_from_directory


class Favicon_ICO():
    endpoints = ["/favicon.ico"]
    endpoint_name = "file_favicon_ico"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return send_from_directory(self.fhdhr.config.internal["paths"]["www_dir"],
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')
