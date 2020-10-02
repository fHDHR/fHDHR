from . import zap2it
from . import empty


class EPGTypes():

    def __init__(self, config, serviceproxy):
        self.config = config.config
        self.proxy = serviceproxy
        self.zap2it = zap2it.ZapEPG(config, serviceproxy)
        self.empty = empty.EmptyEPG(config, serviceproxy)

    def get_epg(self):
        method_to_call = getattr(self, self.config["fakehdhr"]["epg_method"])
        func_to_call = getattr(method_to_call, 'epg_cache_open')
        epgdict = func_to_call()
        return epgdict

    def thumb_url(self, epg_method, thumb_type, base_url, thumbnail):
        method_to_call = getattr(self, self.config["fakehdhr"]["epg_method"])
        func_to_call = getattr(method_to_call, 'thumb_url')
        thumbnail = func_to_call(thumb_type, base_url, thumbnail)
        return thumbnail

    def update(self):
        method_to_call = getattr(self, self.config["fakehdhr"]["epg_method"])
        func_to_call = getattr(method_to_call, 'update_epg')
        func_to_call()
