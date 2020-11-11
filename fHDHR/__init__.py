# coding=utf-8

from .origin import OriginServiceWrapper
from .device import fHDHR_Device

import fHDHR.tools

fHDHR_VERSION = "v0.4.0-beta"


class fHDHR_INT_OBJ():

    def __init__(self, settings, logger, db):
        self.version = fHDHR_VERSION
        self.config = settings
        self.logger = logger
        self.db = db

        self.web = fHDHR.tools.WebReq()


class fHDHR_OBJ():

    def __init__(self, settings, logger, db):
        self.fhdhr = fHDHR_INT_OBJ(settings, logger, db)

        self.origin = OriginServiceWrapper(self.fhdhr)

        self.device = fHDHR_Device(self.fhdhr, self.origin)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.fhdhr, name):
            return eval("self.fhdhr." + name)
