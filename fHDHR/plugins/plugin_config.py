

class Plugin_Config():
    """
    A wrapper for the Config System.
    """

    def __init__(self, config, name, logger):
        self._config = config
        self.name = name
        self.namespace = name.lower()
        self.logger = logger

    @property
    def dict(self):
        """
        A Read-Only access to the config dict.
        """

        return self._config.dict.copy()

    @property
    def internal(self):
        """
        A Read-Only access to the config internals.
        """

        return self._config.internal.copy()

    @property
    def conf_default(self):
        """
        A Read-Only access to the config defaults system.
        """

        return self._config.conf_default.copy()

    def write(self, key, value, namespace=None):
        """
        A method for allowing a plugin access to its own config options.
        """

        if not namespace:
            namespace = self.namespace

        elif str(namespace).lower() != self.namespace:
            self.fhdhr.logger.error("%s plugin is not allowed write access to fhdhr config namespaces." % self.name)
            return

        return self._config.write(key, value, self.namespace)
