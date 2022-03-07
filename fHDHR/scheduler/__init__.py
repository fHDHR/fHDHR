import functools
import threading
import schedule
import time

from fHDHR.tools import checkattr


class Scheduler():
    """
    fHDHR Scheduling events system.
    """

    def __init__(self, settings, logger, db):
        self.config = settings
        self.logger = logger
        self.db = db

        self.schedule = schedule

    def fhdhr_self_add(self, fhdhr):
        self.fhdhr = fhdhr

    @property
    def enabled_jobs(self):
        return [x["name"] for x in self.list_jobs]

    @property
    def unscheduled_jobs(self):

        unscheduled_job_items = []

        enabled_jobs = self.enabled_jobs

        origin_methods = self.fhdhr.origins.list_origins
        for origin_name in origin_methods:
            scan_tag = self.fhdhr.origins.get_origin_property(origin_name, "scan_tag")
            if scan_tag not in enabled_jobs:
                chanscan_interval = self.fhdhr.origins.get_origin_property(origin_name, "chanscan_interval")
                unscheduled_job_items.append({
                    "name": scan_tag,
                    "type": "Channel Scan",
                    "interval": self.fhdhr.time.humanized_time(chanscan_interval),
                    "interval_epoch": chanscan_interval
                    })

        epg_methods = self.fhdhr.device.epg.valid_epg_methods
        for epg_method in epg_methods:
            if "%s EPG Update" % epg_method not in enabled_jobs:
                frequency_seconds = self.fhdhr.device.epg.epg_handling[epg_method].update_frequency
                unscheduled_job_items.append({
                    "name": "%s EPG Update" % epg_method,
                    "type": "EPG Update",
                    "interval": self.fhdhr.time.humanized_time(frequency_seconds),
                    "interval_epoch": frequency_seconds
                    })

        if "Versions Update" not in enabled_jobs:
            frequency_seconds = self.fhdhr.config.dict["fhdhr"]["versions_check_interval"]
            unscheduled_job_items.append({
                "name": "Versions Update",
                "type": "Versions Update",
                "interval": self.fhdhr.time.humanized_time(frequency_seconds),
                "interval_epoch": frequency_seconds
                })

        ssdp_methods = list(self.fhdhr.device.ssdp.ssdp_handling.keys())
        for ssdp_method in ssdp_methods:
            if "%s SSDP Alive" % ssdp_method not in enabled_jobs:
                frequency_seconds = self.fhdhr.device.ssdp.ssdp_handling[ssdp_method].max_age
                unscheduled_job_items.append({
                    "name": "%s SSDP Alive" % ssdp_method,
                    "type": "SSDP Alive",
                    "interval": self.fhdhr.time.humanized_time(frequency_seconds),
                    "interval_epoch": frequency_seconds
                    })
        return unscheduled_job_items

    # This decorator can be applied to any job function
    def job_wrapper(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            job_name = func.__name__
            start_timestamp = time.time()

            self.logger.debug('Running job: %s' % job_name)

            result = func(*args, **kwargs)

            total_time = self.fhdhr.time.humanized_time(time.time() - start_timestamp)
            self.logger.debug('Job %s completed in %s' % (job_name, total_time))

            return result

        return wrapper

    def get_scheduled_time(self, jobtag):
        """Get last and next run info for a tag"""
        jobsdict = {
                    "name": None,
                    "last_run": None,
                    "next_run": None
                    }
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                if jobtag in list(job_item.tags):
                    jobsdict.update({
                                     "name": list(job_item.tags)[0],
                                     "last_run": job_item.last_run,
                                     "next_run": job_item.next_run
                                     })
        return jobsdict

    def remove(self, remtag):
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                if remtag in list(job_item.tags):
                    self.schedule.cancel_job(job_item)

    @property
    def list_tags(self):
        tagslist = []
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                tagslist.extend(list(job_item.tags))
        return tagslist

    @property
    def list_jobs(self):
        jobsdicts = []
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                jobsdicts.append({
                    "name": list(job_item.tags)[0],
                    "last_run": job_item.last_run,
                    "next_run": job_item.next_run
                    })
        return jobsdicts

    @property
    def list_jobs_humanized(self):
        jobsdicts = self.list_jobs
        formatted_jobsdicts = []
        nowtime = time.time()
        for job_dict in jobsdicts:
            job_dict_copy = job_dict.copy()
            for run_item in ["last_run", "next_run"]:
                if job_dict_copy[run_item]:
                    job_dict_copy[run_item] = job_dict_copy[run_item].timestamp()
                    if job_dict_copy[run_item] > nowtime:
                        job_dict_copy[run_item] = self.fhdhr.time.humanized_time(job_dict_copy[run_item] - nowtime)
                    else:
                        job_dict_copy[run_item] = self.fhdhr.time.humanized_time(nowtime - job_dict_copy[run_item])
                else:
                    job_dict_copy[run_item] = "Never"
            formatted_jobsdicts.append(job_dict_copy)
        return formatted_jobsdicts

    def run_from_tag(self, runtag):
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                if runtag in list(job_item.tags):
                    self.logger.debug("Job %s was triggered to run." % list(job_item.tags)[0])
                    job_item.run()

    def run(self):
        """
        Run all scheduled tasks.
        """

        # Start a thread to run the events
        t = threading.Thread(target=self.thread_worker, args=())
        t.start()

    def thread_worker(self):
        while True:
            self.schedule.run_pending()
            time.sleep(1)

    def startup_tasks(self):
        self.fhdhr.logger.noob("Running Startup Tasks.")

        tags_list = self.list_tags

        self.startup_versions_update(tags_list)

        self.startup_channel_scan(tags_list)

        self.startup_epg_update(tags_list)

        self.startup_ssdp_alive(tags_list)

        self.fhdhr.logger.noob("Startup Tasks Complete.")

        return "Success"

    def startup_epg_update(self, tags_list):
        for epg_method in self.fhdhr.device.epg.epg_methods:
            updateepg = self.fhdhr.device.epg.epg_handling[epg_method].epg_update_on_start
            if updateepg:
                if ("%s EPG Update" % epg_method) in tags_list:
                    self.fhdhr.scheduler.run_from_tag("%s EPG Update" % epg_method)

    def startup_channel_scan(self, tags_list):
        for origin_name in self.fhdhr.origins.list_origins:
            updatechannels = self.fhdhr.origins.get_origin_property(origin_name, "chanscan_on_start")
            if updatechannels:
                if ("%s Channel Scan" % origin_name) in tags_list:
                    self.fhdhr.scheduler.run_from_tag("%s Channel Scan" % origin_name)

    def startup_versions_update(self, tags_list):
        if "Versions Update" in tags_list:
            self.fhdhr.scheduler.run_from_tag("Versions Update")

    def startup_ssdp_alive(self, tags_list):
        ssdp_methods = list(self.fhdhr.device.ssdp.ssdp_handling.keys())
        for ssdp_method in ssdp_methods:
            if "%s SSDP Alive" % ssdp_method in tags_list:
                self.fhdhr.scheduler.run_from_tag("%s SSDP Alive")

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.schedule, name):
            return eval("self.schedule.%s" % name)
