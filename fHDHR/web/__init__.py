import requests


class WebReq():
    def __init__(self):
        self.session = requests.Session()
        self.exceptions = requests.exceptions

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.session, name):
            return eval("self.session.%s" % name)
