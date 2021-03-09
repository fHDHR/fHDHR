# coding=utf-8

from .device import fHDHR_Device
from .api import fHDHR_API_URLs
from fHDHR.origins import Origins

fHDHR_VERSION = "v0.9.0-beta"


class fHDHR_INT_OBJ():

    def __init__(self, settings, logger, db, plugins, versions, web, scheduler, deps):
        """
        An internal catalogue of core methods.
        """

        self.version = fHDHR_VERSION
        self.versions = versions
        self.config = settings
        self.logger = logger
        self.db = db
        self.plugins = plugins
        self.web = web
        self.scheduler = scheduler
        self.deps = deps

        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.web = self.web

        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.scheduler = self.scheduler

        self.api = fHDHR_API_URLs(settings, self.web, versions, logger)
        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.plugins[plugin_name].plugin_utils.api = self.api

        self.threads = {}


class fHDHR_OBJ():

    def __init__(self, settings, logger, db, plugins, versions, web, scheduler, deps):
        """
        The Core Backend.
        """

        logger.info("Initializing fHDHR Core Functions.")
        self.fhdhr = fHDHR_INT_OBJ(settings, logger, db, plugins, versions, web, scheduler, deps)

        self.fhdhr.origins = Origins(self.fhdhr)

        self.device = fHDHR_Device(self.fhdhr, self.fhdhr.origins)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if hasattr(self.fhdhr, name):
            return eval("self.fhdhr.%s" % name)

        elif hasattr(self.fhdhr.device, name):
            return eval("self.fhdhr.device.%s" % name)
