# coding=utf-8

from .originwrapper import OriginServiceWrapper
from .device import fHDHR_Device
from .api import fHDHR_API_URLs

import fHDHR.tools

fHDHR_VERSION = "v0.6.0-beta"


class fHDHR_INT_OBJ():

    def __init__(self, settings, logger, db):
        self.version = fHDHR_VERSION
        self.config = settings
        self.logger = logger
        self.db = db

        self.web = fHDHR.tools.WebReq()

        self.api = fHDHR_API_URLs(settings, self.web)

        self.threads = {}


class fHDHR_OBJ():

    def __init__(self, settings, logger, db, plugins):
        self.fhdhr = fHDHR_INT_OBJ(settings, logger, db)

        self.originwrapper = OriginServiceWrapper(self.fhdhr, plugins.origin)

        self.device = fHDHR_Device(self.fhdhr, self.originwrapper, plugins)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.fhdhr, name):
            return eval("self.fhdhr.%s" % name)
