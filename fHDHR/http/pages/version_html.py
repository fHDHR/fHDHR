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
                        "Operating System": self.fhdhr.config.internal["versions"]["opersystem"],
                        "Using Docker": self.fhdhr.config.internal["versions"]["isdocker"],
                        "ffmpeg": self.fhdhr.config.internal["versions"]["ffmpeg"],
                        "vlc": self.fhdhr.config.internal["versions"]["vlc"],
                        }
        return render_template('version.html', request=request, fhdhr=self.fhdhr, version_dict=version_dict, list=list)
