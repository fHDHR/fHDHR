

class Locast_API():
    endpoints = ["/api/locast"]
    endpoint_name = "api_locast"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, plugin_utils):
        self.plugin_utils = plugin_utils

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return "Success"
