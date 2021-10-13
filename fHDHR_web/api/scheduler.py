from flask import request, redirect, Response
import urllib.parse
import json


class Scheduler_API():
    endpoints = ["/api/scheduler"]
    endpoint_name = "api_scheduler"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "get"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            jobsdicts = self.fhdhr.scheduler.list_jobs()

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

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
