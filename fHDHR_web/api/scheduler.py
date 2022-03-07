from flask import request, redirect, Response
import urllib.parse
import json


class Scheduler_API():
    endpoints = ["/api/scheduler"]
    endpoint_name = "api_scheduler"
    endpoint_methods = ["GET", "POST"]
    endpoint_parameters = {
                            "method": {
                                    "default": "get"
                                    }
                            }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default="get", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            jobsdicts = self.fhdhr.scheduler.list_jobs

            formatted_jobsdicts = []
            for job_dict in jobsdicts:
                for run_item in ["last_run", "next_run"]:
                    if job_dict[run_item]:
                        job_dict[run_item] = job_dict[run_item].timestamp()
                formatted_jobsdicts.append(job_dict)

            return_json = json.dumps(formatted_jobsdicts, indent=4)

            return Response(status=200,
                            response=return_json,
                            mimetype='application/json')

        elif method == "run":
            job_tag = request.form.get('job_tag', None)

            if not job_tag:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method

            self.fhdhr.scheduler.run_from_tag(job_tag)

        elif method == "remove":
            job_tag = request.form.get('job_tag', None)

            if not job_tag:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method

            self.fhdhr.scheduler.remove(job_tag)

        elif method == "add":
            job_name = request.form.get('name', None)
            job_type = request.form.get('type', None)
            job_interval = request.form.get('interval', None)

            if job_type == "EPG Update":
                if job_interval:
                    self.fhdhr.scheduler.every(int(job_interval)).seconds.do(
                        self.fhdhr.scheduler.job_wrapper(self.fhdhr.device.epg.update), job_name).tag("%s EPG Update" % job_name)

            elif job_type == "Channel Scan":
                if job_interval:
                    self.fhdhr.origins.origins_dict[job_name].channels.schedule_scan(job_interval)

            elif job_type == "Versions Update":
                if job_interval:
                    self.fhdhr.scheduler.every(int(job_interval)).seconds.do(
                        self.fhdhr.scheduler.job_wrapper(self.fhdhr.versions.get_online_versions)).tag("Versions Update")

            elif job_type == "SSDP Alive":
                if job_interval:
                    max_age = int(self.ssdp_handling[job_name].max_age)
                    self.fhdhr.scheduler.every(max_age).seconds.do(
                        self.fhdhr.scheduler.job_wrapper(self.do_alive), [job_name]).tag("%s SSDP Alive" % job_name)

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
