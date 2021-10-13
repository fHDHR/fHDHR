import os
import sys
import platform
import pathlib
import json
import re


class Versions():
    """
    fHDHR versioning management system.
    """

    def __init__(self, settings, logger):
        self.config = settings
        self.logger = logger

        self.github_org_list_url = "https://api.github.com/orgs/fHDHR/repos?type=all"
        self.github_fhdhr_core_info_url = "https://raw.githubusercontent.com/fHDHR/fHDHR/main/version.json"

        self.dict = {}

        self.register_fhdhr()

        self.register_env()

        self.update_url = "/api/versions?method=check"

    def secondary_setup(self, db, web, scheduler):
        self.db = db
        self.web = web
        self.scheduler = scheduler

        self.official_plugins = self.db.get_fhdhr_value("versions", "dict") or {}
        self.core_versions = self.db.get_fhdhr_value("core_versions", "dict") or {}

    def sched_init(self, fhdhr):
        """
        The Scheduled update method.
        """

        self.api = fhdhr.api
        self.scheduler.every(self.config.dict["fhdhr"]["versions_check_interval"]).seconds.do(
            self.scheduler.job_wrapper(self.get_online_versions)).tag("Versions Update")

    def sched_update(self):
        """
        Use an API thread to update Versions listing.
        """

        self.api.threadget(self.update_url)

    def get_online_versions(self):
        """
        Update Onling versions listing.
        """

        self.logger.debug("Checking for Online Core Versioning Information")
        core_versions = {}

        try:
            core_json = self.web.session.get(self.github_fhdhr_core_info_url).json()
        except self.web.exceptions.ReadTimeout as err:
            self.logger.error("Online Core Versioning Information Check Failed: %s" % err)
            core_json = None

        if core_json:
            for key in list(core_json.keys()):
                core_versions[key] = {"name": key, "version": core_json[key], "type": "core"}
            self.db.set_fhdhr_value("core_versions", "dict", core_versions)
            self.core_versions = core_versions

        self.logger.debug("Checking for Online Plugin Information")
        official_plugins = {}

        try:
            github_org_json = self.web.session.get(self.github_org_list_url).json()
        except self.web.exceptions.ReadTimeout as err:
            self.logger.error("Online Plugin Information Check Failed: %s" % err)
            github_org_json = None

        if github_org_json:
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

            self.db.set_fhdhr_value("versions", "dict", official_plugins)
            self.official_plugins = official_plugins

    def get_core_versions(self):
        returndict = {}
        for item in list(self.dict.keys()):
            if self.dict[item]["type"] == "fHDHR":
                returndict[item] = self.dict[item].copy()
        return returndict

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

        script_dir = self.config.internal["paths"]["script_dir"]
        version_file = pathlib.Path(script_dir).joinpath("version.json")
        with open(version_file, 'r') as jsonversion:
            versions = json.load(jsonversion)

        for key in list(versions.keys()):
            self.register_version(key, versions[key], "fHDHR")

    def is_docker(self):
        path = "/proc/self/cgroup"
        if not os.path.isfile(path):
            return False
        with open(path) as f:
            for line in f:
                if re.match("\d+:[\w=]+:/docker(-[ce]e)?/\w+", line):
                    return True
            return False

    def is_virtualenv(self):
        # return True if started from within a virtualenv or venv
        base_prefix = getattr(sys, "base_prefix", None)
        # real_prefix will return None if not in a virtualenv enviroment or the default python path
        real_prefix = getattr(sys, "real_prefix", None) or sys.prefix
        return base_prefix != real_prefix

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

        isvirtualenv = self.is_virtualenv()
        self.register_version("Virtualenv", isvirtualenv, "env")

        isdocker = self.is_docker()
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
