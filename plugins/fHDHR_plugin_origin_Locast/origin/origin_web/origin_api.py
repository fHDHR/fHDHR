

class Origin_API():
    endpoints = ["/api/origin"]
    endpoint_name = "api_origin"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return "Success"
