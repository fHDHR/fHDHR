from flask import redirect


class Root_URL():
    endpoints = ["/"]
    endpoint_name = "page_root_html"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):
        return redirect("/index")
