

class Plugin_Config():
    def __init__(self, config, name):
        self._config = config
        self.name = name
        self.namespace = name.lower()

    @property
    def dict(self):
        return self._config.dict.copy()

    @property
    def internal(self):
        return self._config.internal.copy()

    @property
    def conf_default(self):
        return self._config.conf_default.copy()

    def write(self, key, value, namespace=None):
        if not namespace:
            namespace = self.namespace
        elif str(namespace).lower() != self.namespace:
            print("%s plugin is not allowed write access to fhdhr config namespaces." % self.name)
            return
        return self._config.write(key, value, self.namespace)
