

class Plugin_DB():
    def __init__(self, db, name, logger):
        self._db = db
        self.name = name
        self.namespace = name.lower()
        self.logger = logger

    # fhdhr
    def set_fhdhr_value(self, pluginitem, key, value, namespace="default"):
        self.fhdhr.logger.error("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    def get_fhdhr_value(self, pluginitem, key, namespace="default"):
        return self._db.get_fhdhr_value(pluginitem, key, namespace=namespace.lower())

    def delete_fhdhr_value(self, pluginitem, key, namespace="default"):
        self.fhdhr.logger.error("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    # Plugin
    def set_plugin_value(self, pluginitem, key, value, namespace=None):
        if not namespace:
            namespace = self.namespace
        elif namespace.lower() != self.namespace:
            self.fhdhr.logger.error("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
            return
        return self._db.set_plugin_value(pluginitem, key, value, namespace=self.namespace)

    def get_plugin_value(self, pluginitem, key, namespace=None):
        if not namespace:
            namespace = self.namespace
        return self._db.get_plugin_value(pluginitem, key, namespace=namespace.lower())

    def delete_plugin_value(self, pluginitem, key, namespace=None):
        if not namespace:
            namespace = self.namespace
        elif namespace.lower() != self.namespace:
            self.fhdhr.logger.error("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
            return
        return self._db.delete_plugin_value(pluginitem, key, namespace=self.namespace)
