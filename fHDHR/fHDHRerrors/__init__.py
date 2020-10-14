
class TunerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'TunerError: %s' % self.value


class LoginError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'LoginError: %s' % self.value


class EPGSetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'EPGSetupError: %s' % self.value


class ConfigurationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'ConfigurationError: %s' % self.value


class ConfigurationNotFound(ConfigurationError):
    def __init__(self, filename):
        super(ConfigurationNotFound, self).__init__(None)
        self.filename = filename

    def __str__(self):
        return 'Unable to find the configuration file %s' % self.filename
