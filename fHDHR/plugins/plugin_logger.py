from fHDHR.tools import checkattr


class Plugin_Logger():
    """
    A wrapper for the Database System.
    """

    def __init__(self, name, logger):
        self._logger = logger
        self.name = name
        self.namespace = name.lower()

    def critical(self, message, *args, **kws):
        return self._logger.critical("[%s] %s" % (self.namespace, message), *args, **kws)

    def error(self, message, *args, **kws):
        return self._logger.error("[%s] %s" % (self.namespace, message), *args, **kws)

    def warning(self, message, *args, **kws):
        return self._logger.warning("[%s] %s" % (self.namespace, message), *args, **kws)

    def noob(self, message, *args, **kws):
        return self._logger.noob("[%s] %s" % (self.namespace, message), *args, **kws)

    def info(self, message, *args, **kws):
        return self._logger.info("[%s] %s" % (self.namespace, message), *args, **kws)

    def debug(self, message, *args, **kws):
        return self._logger.debug("[%s] %s" % (self.namespace, message), *args, **kws)

    def ssdp(self, message, *args, **kws):
        return self._logger.ssdp("[%s] %s" % (self.namespace, message), *args, **kws)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self, name.lower()):
            return eval("self._logger.%s" % name.lower())

        if checkattr(self._logger, name):
            return eval("self._logger.%s" % name)
