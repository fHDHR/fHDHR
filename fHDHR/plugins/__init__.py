import os
import imp
import json


class Plugin_DB():
    def __init__(self, db, name):
        self._db = db
        self.name = name
        self.namespace = name.lower()

    # fhdhr
    def set_fhdhr_value(self, pluginitem, key, value, namespace="default"):
        print("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    def get_fhdhr_value(self, pluginitem, key, namespace="default"):
        return self._db.get_fhdhr_value(pluginitem, key, namespace=namespace.lower())

    def delete_fhdhr_value(self, pluginitem, key, namespace="default"):
        print("%s plugin is not allowed write access to fhdhr db namespaces." % self.name)
        return

    # Plugin
    def set_plugin_value(self, pluginitem, key, value, namespace=None):
        if not namespace:
            namespace = self.namespace
        elif namespace.lower() != self.namespace:
            print("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
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
            print("%s plugin is not allowed write access to %s db namespace." % (self.name, namespace))
            return
        return self._db.delete_plugin_value(pluginitem, key, namespace=self.namespace)


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


class Plugin_Utils():

    def __init__(self, config, logger, db, plugin_name, plugin_manifest, modname):
        self.config = Plugin_Config(config, plugin_manifest["name"])
        self.db = Plugin_DB(db, plugin_manifest["name"])
        self.logger = logger
        self.namespace = plugin_manifest["name"].lower()
        self.plugin_name = plugin_name
        self.plugin_manifest = plugin_manifest
        self.origin = None


class Plugin():

    def __init__(self, config, logger, db, plugin_name, plugin_path, plugin_conf, plugin_manifest):
        self.config = config
        self.db = db
        self.logger = logger

        # Gather Info about Plugin
        self.plugin_name = plugin_name
        self.modname = os.path.basename(plugin_path)
        self.path = plugin_path
        self.module_type = imp.PKG_DIRECTORY
        self.multi_plugin = (self.plugin_name != self.modname)
        self.default_conf = plugin_conf
        self.manifest = plugin_manifest

        if self.multi_plugin:
            self.plugin_dict_name = "%s_%s" % (plugin_name, self.modname)
        else:
            self.plugin_dict_name = plugin_name

        self.plugin_utils = Plugin_Utils(config, logger, db, plugin_name, plugin_manifest, self.modname)

        # Load the module
        self._module = self._load()

    def setup(self):

        if self.type == "alt_epg":
            self.config.register_valid_epg_method(self.name, self.plugin_dict_name)
        elif self.type == "alt_stream":
            self.config.register_valid_streaming_method(self.name, self.plugin_dict_name)
        elif self.type == "web":
            self.config.register_web_path(self.manifest["name"], self.path, self.plugin_dict_name)

        if self.has_setup():
            self._module.setup(self)

    def has_setup(self):
        return hasattr(self._module, 'setup')

    def _load(self):
        description = ('', '', self.module_type)
        mod = imp.load_module(self.plugin_dict_name, None, self.path, description)
        return mod

    @property
    def name(self):
        return self.manifest["name"]

    @property
    def version(self):
        return self.manifest["version"]

    @property
    def type(self):
        return self.manifest["type"]

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if name == "Plugin_OBJ":
            return self._module.Plugin_OBJ


class PluginsHandler():

    def __init__(self, settings):
        self.config = settings

        self.plugins = {}

        self.found_plugins = []
        self.found_plugins_conf = []
        self.list_plugins()

    def setup(self):
        for plugin_name in list(self.plugins.keys()):
            self.plugins[plugin_name].setup()

    def load_plugin_configs(self):
        for file_item_path in self.found_plugins_conf:
            self.config.import_conf_json(file_item_path)

    def list_plugins(self):
        for directory in self.config.internal["paths"]["plugins_dir"]:

            base = os.path.abspath(directory)
            for filename in os.listdir(base):
                abspath = os.path.join(base, filename)

                if os.path.isdir(abspath):

                    plugin_conf = []
                    for subfilename in os.listdir(abspath):
                        subabspath = os.path.join(abspath, subfilename)
                        if subfilename.endswith("_conf.json"):
                            plugin_conf.append(subabspath)
                            self.found_plugins_conf.append(subabspath)

                    # Plugin/multi-plugin must have a basic manifest json
                    conffilepath = os.path.join(abspath, 'plugin.json')
                    if os.path.isfile(conffilepath):
                        plugin_manifest = json.load(open(conffilepath, 'r'))

                        for plugin_man_item in ["name", "version", "type"]:
                            if plugin_man_item not in list(plugin_manifest.keys()):
                                plugin_manifest[plugin_man_item] = None

                        self.config.register_version(os.path.basename(filename), plugin_manifest["version"], "plugin")

                        if plugin_manifest["type"] == "origin":
                            self.config.register_valid_origin_method(plugin_manifest["name"])

                        plugin_import_print_string = "Found %s type plugin: %s %s. " % (plugin_manifest["type"], plugin_manifest["name"], plugin_manifest["version"])

                        # Warn for multiple origins
                        if plugin_manifest["type"] == "origin" and len([plugin_name for plugin_name, plugin_path, plugin_conf, plugin_manifest in self.found_plugins if plugin_manifest["type"] == "origin"]):
                            plugin_import_print_string += " ImportWarning: Only one Origin Allowed."

                        if not any(plugin_manifest[plugin_item] for plugin_item in ["name", "version", "type"]):
                            plugin_import_print_string += " ImportWarning: Missing PLUGIN_* Value."
                        else:

                            # Single Plugin
                            if os.path.isfile(os.path.join(abspath, '__init__.py')):
                                plugin_manifest["tagged_mod"] = None
                                plugin_manifest["tagged_mod_type"] = None
                                self.found_plugins.append((os.path.basename(filename), abspath, plugin_conf, plugin_manifest))

                            else:

                                # Multi-Plugin
                                for subfilename in os.listdir(abspath):
                                    subabspath = os.path.join(abspath, subfilename)

                                    if os.path.isdir(subabspath):

                                        subconffilepath = os.path.join(subabspath, 'plugin.json')
                                        if os.path.isfile(subconffilepath):
                                            subplugin_manifest = json.load(open(subconffilepath, 'r'))

                                            for subplugin_man_item in ["name", "version", "type"]:
                                                if subplugin_man_item not in list(subplugin_manifest.keys()):
                                                    subplugin_manifest[subplugin_man_item] = plugin_manifest[subplugin_man_item]
                                        else:
                                            subplugin_manifest = plugin_manifest

                                        subplugin_manifest["tagged_mod"] = None
                                        subplugin_manifest["tagged_mod_type"] = None
                                        if plugin_manifest["type"] != subplugin_manifest["type"]:
                                            subplugin_manifest["tagged_mod"] = plugin_manifest["name"]
                                            subplugin_manifest["tagged_mod_type"] = plugin_manifest["type"]

                                        if os.path.isfile(os.path.join(subabspath, '__init__.py')):
                                            self.found_plugins.append((os.path.basename(filename), subabspath, plugin_conf, subplugin_manifest))

                        print(plugin_import_print_string)
        self.load_plugin_configs()

    def load_plugins(self, logger, db):
        self.logger = logger
        self.db = db
        for plugin_name, plugin_path, plugin_conf, plugin_manifest in self.found_plugins:
            plugin_item = Plugin(self.config, self.logger, self.db, plugin_name, plugin_path, plugin_conf, plugin_manifest)
            self.plugins[plugin_item.plugin_dict_name] = plugin_item
