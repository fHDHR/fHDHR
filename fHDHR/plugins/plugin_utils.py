
from .plugin_config import Plugin_Config
from .plugin_db import Plugin_DB
from .plugin_logger import Plugin_Logger


class Plugin_Utils():
    """
    A wrapper for core functions for a plugin to have access to.
    """

    def __init__(self, config, logger, db, versions, plugin_name, plugin_manifest, modname, path):
        self.config = Plugin_Config(config, plugin_manifest["name"], logger)
        self.db = Plugin_DB(db, plugin_manifest["name"], logger)
        self.logger = Plugin_Logger(plugin_manifest["name"], logger)
        self.versions = versions
        self.namespace = plugin_manifest["name"].lower()
        self.plugin_name = plugin_name
        self.plugin_manifest = plugin_manifest
        self.path = path
        self.origin_obj = None
        self.origin_name = None
