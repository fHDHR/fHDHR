from fHDHR.tools import checkattr


class Plugin_DB():
    """
    A wrapper for the Database System.
    """

    def __init__(self, db, name, logger):
        self._db = db
        self.name = name
        self.namespace = name.lower()
        self.logger = logger

    # fhdhr
    def set_fhdhr_value(self, pluginitem, key, value, namespace="default"):
        """
        Block access to setting fHDHR database values.
        """

        self.fhdhr.logger.error("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    def get_fhdhr_value(self, pluginitem, key, namespace="default"):
        """
        Allow access to Reading fHDHR database values.
        """

        return self._db.get_fhdhr_value(pluginitem, key, namespace=namespace.lower())

    def delete_fhdhr_value(self, pluginitem, key, namespace="default"):
        """
        Block access to deleting fHDHR database values.
        """

        self.fhdhr.logger.error("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    # Plugin
    def set_plugin_value(self, pluginitem, key, value, namespace=None):
        """
        Allow setting plugin database values for this plugin only.
        """

        if not namespace:
            namespace = self.namespace

        elif namespace.lower() != self.namespace:
            self.fhdhr.logger.error("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
            return

        return self._db.set_plugin_value(pluginitem, key, value, namespace=self.namespace)

    def get_plugin_value(self, pluginitem, key, namespace=None):
        """
        Read plugin database values.
        """

        if not namespace:
            namespace = self.namespace

        return self._db.get_plugin_value(pluginitem, key, namespace=namespace.lower())

    def delete_plugin_value(self, pluginitem, key, namespace=None):
        """
        Allow deleting plugin database values for this plugin only.
        """

        if not namespace:
            namespace = self.namespace

        elif namespace.lower() != self.namespace:
            self.fhdhr.logger.error("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
            return

        return self._db.delete_plugin_value(pluginitem, key, namespace=self.namespace)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self._db, name):
            return eval("self._db.%s" % name)
