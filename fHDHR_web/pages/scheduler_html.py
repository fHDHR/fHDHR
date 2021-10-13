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

        return render_template('scheduler.html', request=request, session=session, fhdhr=self.fhdhr, jobsdicts=formatted_jobsdicts)
