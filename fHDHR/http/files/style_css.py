from flask import send_from_directory


class Style_CSS():
    endpoints = ["/style.css"]
    endpoint_name = "style"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return send_from_directory(self.fhdhr.config.dict["filedir"]["www_dir"],
                                   'style.css')
