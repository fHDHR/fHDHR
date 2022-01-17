
"""Exceptions to throw."""


class TunerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'TunerError: %s' % self.value


class OriginSetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'OriginSetupError: %s' % self.value


class SSDPSetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'OriginSetupError: %s' % self.value


class EPGSetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'EPGSetupError: %s' % self.value


class WEBSetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'WEBSetupError: %s' % self.value


class INTERFACESetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'INTERFACESetupError: %s' % self.value


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
