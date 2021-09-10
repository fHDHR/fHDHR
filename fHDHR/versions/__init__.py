import os
import sys
import platform

from fHDHR import fHDHR_VERSION
from fHDHR.tools import is_docker


class Versions():
    """
    fHDHR versioning management system.
    """

    def __init__(self, settings, fHDHR_web, logger, web, db, scheduler):
        self.fHDHR_web = fHDHR_web
        self.logger = logger
        self.web = web
        self.db = db
        self.scheduler = scheduler

        self.github_org_list_url = "https://api.github.com/orgs/fHDHR/repos?type=all"
        self.github_fhdhr_core_info_url = "https://raw.githubusercontent.com/fHDHR/fHDHR/main/version.json"

        self.dict = {}
        self.official_plugins = self.db.get_fhdhr_value("versions", "dict") or {}

        self.register_fhdhr()

        self.register_env()

        self.get_online_versions()

        self.update_url = "/api/versions?method=check"

    def sched_init(self, fhdhr):
        """
        The Scheduled update method.
        """

        self.api = fhdhr.api
        self.scheduler.every(2).to(3).hours.do(self.sched_update)

    def sched_update(self):
        """
        Use an API thread to update Versions listing.
        """

        self.api.threadget(self.update_url)

    def get_online_versions(self):
        """
        Update Onling versions listing.
        """

        self.logger.debug("Checking for Online Plugin Information")

        official_plugins = {}

        try:
            github_org_json = self.web.session.get(self.github_org_list_url).json()
        except self.web.exceptions.ReadTimeout as err:
            self.logger.error("Online Plugin Information Check Failed: %s" % err)
            return

        online_plugin_names = [x["name"] for x in github_org_json if x["name"].startswith("fHDHR_plugin_")]
        for plugin_name in online_plugin_names:

            plugin_version_check_success = 0

            for branch in ["main", "master", "dev"]:

                if not plugin_version_check_success:

                    self.logger.debug("Attempting Online Plugin Information for %s %s branch" % (plugin_name, branch))
                    plugin_json_url = "https://raw.githubusercontent.com/fHDHR/%s/%s/plugin.json" % (plugin_name, branch)
                    try:
                        plugin_json = self.web.session.get(plugin_json_url)
                        if plugin_json.status_code == 200:
                            plugin_json = plugin_json.json()
                            official_plugins[plugin_name] = plugin_json
                            plugin_version_check_success = 1
                    except self.web.exceptions.ReadTimeout as err:
                        self.logger.error("Online Plugin Information Check Failed for %s %s branch: %s" % (plugin_name, branch, err))

        self.official_plugins = official_plugins

        core_json = self.web.session.get(self.github_fhdhr_core_info_url).json()
        for key in list(core_json.keys()):
            self.official_plugins[key] = {"name": key, "version": core_json[key], "type": "core"}

        self.db.set_fhdhr_value("versions", "dict", official_plugins)

    def register_version(self, item_name, item_version, item_type):
        """
        Register a version item.
        """

        self.logger.debug("Registering %s item: %s %s" % (item_type, item_name, item_version))
        self.dict[item_name] = {
                                "name": item_name,
                                "version": item_version,
                                "type": item_type
                                }

    def register_fhdhr(self):
        """
        Register core version items.
        """

        self.register_version("fHDHR", fHDHR_VERSION, "fHDHR")
        self.register_version("fHDHR_web", self.fHDHR_web.fHDHR_web_VERSION, "fHDHR")

    def register_env(self):
        """
        Register env version items.
        """

        self.register_version("Python", sys.version, "env")
        if sys.version_info.major == 2 or sys.version_info < (3, 7):
            self.logger.error('Error: fHDHR requires python 3.7+. Do NOT expect support for older versions of python.')

        opersystem = platform.system()
        self.register_version("Operating System", opersystem, "env")

        if opersystem in ["Linux", "Darwin"]:

            # Linux/Mac
            if os.getuid() == 0 or os.geteuid() == 0:
                self.logger.warning('Do not run fHDHR with root privileges.')

        elif opersystem in ["Windows"]:

            # Windows
            if os.environ.get("USERNAME") == "Administrator":
                self.logger.warning('Do not run fHDHR as Administrator.')

        else:
            self.logger.warning("Uncommon Operating System, use at your own risk.")

        cpu_type = platform.machine()
        self.register_version("CPU Type", cpu_type, "env")

        isdocker = is_docker()
        self.register_version("Docker", isdocker, "env")

    def register_plugins(self, plugins):
        """
        Register plugin version items.
        """

        self.logger.info("Scanning Plugins for Version Information.")
        self.plugins = plugins
        plugin_names = []
        for plugin in list(self.plugins.plugins.keys()):

            if self.plugins.plugins[plugin].plugin_name not in plugin_names:
                plugin_names.append(self.plugins.plugins[plugin].plugin_name)
                self.register_version(self.plugins.plugins[plugin].plugin_name, self.plugins.plugins[plugin].manifest["version"], "plugin")
