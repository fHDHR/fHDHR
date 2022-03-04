
import fHDHR.exceptions
from fHDHR.tools import checkattr

from .epg import EPG
from .tuners import Tuners
from .images import imageHandler
from .ssdp import SSDPServer


class fHDHR_Device():
    """
    The fHDHR devices.
    """

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.fhdhr.logger.debug("Setting Up internal \"Devices\".")

        self.epg = EPG(fhdhr, origins)

        self.tuners = Tuners(fhdhr, self.epg, origins)

        self.images = imageHandler(fhdhr, self.epg)

        self.ssdp = SSDPServer(fhdhr)

        self.interfaces = {}

        self.fhdhr.logger.info("Detecting and Opening any found Interface plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("interface"):

            method = self.fhdhr.plugins.plugins[plugin_name].name.lower()

            plugin_utils = self.fhdhr.plugins.plugins[plugin_name].plugin_utils
            plugin_utils.channels = self.channels
            plugin_utils.epg = self.epg
            plugin_utils.tuners = self.tuners
            plugin_utils.images = self.images
            plugin_utils.ssdp = self.ssdp
            plugin_utils.origins = self.fhdhr.origins

            try:

                self.interfaces[method] = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(fhdhr, plugin_utils)

            except fHDHR.exceptions.INTERFACESetupError as exerror:
                error_out = self.fhdhr.logger.lazy_exception(exerror)
                self.fhdhr.logger.error(error_out)

            except Exception as exerror:
                error_out = self.fhdhr.logger.lazy_exception(exerror)
                self.fhdhr.logger.error(error_out)

    def run_interface_plugin_threads(self):

        self.fhdhr.logger.debug("Checking Interface Plugins for threads to run.")

        for interface_plugin in list(self.interfaces.keys()):

            if checkattr(self.interfaces[interface_plugin], 'run_thread'):
                self.fhdhr.logger.info("Starting %s interface plugin thread." % interface_plugin)
                self.interfaces[interface_plugin].run_thread()
                self.fhdhr.logger.debug("Started %s interface plugin thread." % interface_plugin)
