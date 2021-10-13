from flask import request, render_template, session
import time

from fHDHR.tools import humanized_time


class Scheduler_HTML():
    endpoints = ["/scheduler", "/scheduler.html"]
    endpoint_name = "page_scheduler_html"
    endpoint_access_level = 2
    pretty_name = "Scheduler"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        jobsdicts = self.fhdhr.scheduler.list_jobs()
        formatted_jobsdicts = []
        nowtime = time.time()
        for job_dict in jobsdicts:
            job_dict_copy = job_dict.copy()
            for run_item in ["last_run", "next_run"]:
                if job_dict_copy[run_item]:
                    job_dict_copy[run_item] = job_dict_copy[run_item].timestamp()
                    if job_dict_copy[run_item] > nowtime:
                        job_dict_copy[run_item] = humanized_time(job_dict_copy[run_item] - nowtime)
                    else:
                        job_dict_copy[run_item] = humanized_time(nowtime - job_dict_copy[run_item])
                else:
                    job_dict_copy[run_item] = "Never"
            formatted_jobsdicts.append(job_dict_copy)

        unscheduled_job_items = []
        enabled_jobs = [x["name"] for x in jobsdicts]

        origin_methods = self.fhdhr.origins.valid_origins
        for origin in origin_methods:
            if "%s Channel Scan" % origin not in enabled_jobs:
                chanscan_interval = self.fhdhr.origins.origins_dict[origin].chanscan_interval
                unscheduled_job_items.append({
                    "name": origin,
                    "type": "Channel Scan",
                    "interval": humanized_time(chanscan_interval),
                    "interval_epoch": chanscan_interval
                    })

        epg_methods = self.fhdhr.device.epg.valid_epg_methods
        for epg_method in epg_methods:
            if "%s EPG Update" % epg_method not in enabled_jobs:
                frequency_seconds = self.fhdhr.device.epg.epg_handling[epg_method]["class"].update_frequency
                unscheduled_job_items.append({
                    "name": epg_method,
                    "type": "EPG Update",
                    "interval": humanized_time(frequency_seconds),
                    "interval_epoch": frequency_seconds
                    })

        return render_template('scheduler.html', request=request, session=session, fhdhr=self.fhdhr, jobsdicts=formatted_jobsdicts, unscheduled_job_items=unscheduled_job_items)
