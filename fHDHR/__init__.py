# coding=utf-8

from .device import fHDHR_Device
from .api import fHDHR_API_URLs
from .origins import Origins
from .electronicprogramguide import ElectronicProgramGuide

from .streammanager import StreamManager

from fHDHR.tools import checkattr


class fHDHR_INT_OBJ():

    def __init__(self, ext_fhdhr, settings, fhdhr_time, logger, db, plugins, versions, web, scheduler, deps):
        """
        An internal catalogue of core methods.
        """

        self.ext_fhdhr = ext_fhdhr

        self.versions = versions
        self.version = versions.dict["fHDHR"]["version"]
        self.config = settings
        self.logger = logger
        self.db = db
        self.plugins = plugins
        self.web = web
        self.scheduler = scheduler
        self.deps = deps
        self.time = fhdhr_time

        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.web = self.web

        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.scheduler = self.scheduler

        self.api = fHDHR_API_URLs(settings, self.web, versions, logger)
        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.api = self.api

        self.threads = {}

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.ext_fhdhr, name):
            return eval("self.ext_fhdhr.%s" % name)


class fHDHR_OBJ():

    def __init__(self, settings, fhdhr_time, logger, db, plugins, versions, web, scheduler, deps):
        """
        The Core Backend.
        """

        logger.info("Initializing fHDHR Core Functions.")
        self.fhdhr = fHDHR_INT_OBJ(self, settings, fhdhr_time, logger, db, plugins, versions, web, scheduler, deps)

        self.fhdhr.origins = Origins(self.fhdhr)

        self.fhdhr.electronicprogramguide = ElectronicProgramGuide(self.fhdhr)

        self.device = fHDHR_Device(self.fhdhr, self.fhdhr.origins)

        self.streammanager = StreamManager(self.fhdhr, self.device, self.origins)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.fhdhr, name):
            return eval("self.fhdhr.%s" % name)

        elif checkattr(self.fhdhr.device, name):
            return eval("self.fhdhr.device.%s" % name)
