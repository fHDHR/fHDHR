# coding=utf-8

from .origin import OriginServiceWrapper
from .device import fHDHR_Device

import fHDHR.tools

fHDHR_VERSION = "v0.4.0-beta"


class fHDHR_OBJ():

    def __init__(self, settings, logger, db):
        self.version = fHDHR_VERSION
        self.config = settings
        self.logger = logger
        self.db = db

        self.web = fHDHR.tools.WebReq()

        self.origin = OriginServiceWrapper(settings, logger, self.web, db)

        self.device = fHDHR_Device(settings, self.version, self.origin, logger, self.web, db)
