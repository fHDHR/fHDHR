from flask import request, redirect, session
import urllib.parse
import threading
import time


class Settings():
    endpoints = ["/api/settings"]
    endpoint_name = "api_settings"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.restart_url = "/api/settings?method=restart_actual"
        self.restart_sleep = 5

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "update":
            config_section = request.form.get('config_section', None)
            config_name = request.form.get('config_name', None)
            config_value = request.form.get('config_value', None)

            if not config_section or not config_name or not config_value:
                if redirect_url:
                    return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Failed" % method))
                else:
                    return "%s Falied" % method

            if config_section == "origin":
                config_section = self.fhdhr.config.dict["main"]["dictpopname"]

            self.fhdhr.config.write(config_section, config_name, config_value)

        elif method == "restart":
            restart_thread = threading.Thread(target=self.restart_thread)
            restart_thread.start()
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("Restarting in %s seconds" % self.restart_sleep))

        elif method == "restart_actual":
            session["restart"] = True

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            return "%s Success" % method

    def restart_thread(self):
        time.sleep(self.restart_sleep)
        self.fhdhr.api.get(self.restart_url)
