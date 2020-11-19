import sys
from flask import request, render_template


class Version_HTML():
    endpoints = ["/version", "/version.html"]
    endpoint_name = "version"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        version_dict = {
                        "fHDHR": self.fhdhr.version,
                        "Python": sys.version,
                        "Operating System": self.fhdhr.config.dict["main"]["opersystem"],
                        "Using Docker": self.fhdhr.config.dict["main"]["isdocker"],
                        "ffmpeg": self.fhdhr.config.dict["ffmpeg"]["version"],
                        "vlc": self.fhdhr.config.dict["vlc"]["version"],
                        }
        return render_template('version.html', request=request, fhdhr=self.fhdhr, version_dict=version_dict, list=list)
