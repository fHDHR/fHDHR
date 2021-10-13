import functools
import schedule
import time

from fHDHR.tools import humanized_time


class Scheduler():
    """
    fHDHR Scheduling events system.
    """

    def __init__(self, settings, logger, db):
        self.config = settings
        self.logger = logger
        self.db = db

        self.schedule = schedule

    # This decorator can be applied to any job function
    def job_wrapper(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            job_name = func.__name__
            start_timestamp = time.time()

            self.logger.debug('Running job: %s' % job_name)

            result = func(*args, **kwargs)

            total_time = humanized_time(time.time() - start_timestamp)
            self.logger.debug('Job %s completed in %s seconds' % (job_name, total_time))

            return result

        return wrapper

    def remove(self, remtag):
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                if remtag in list(job_item.tags):
                    self.schedule.cancel_job(job_item)

    def list_tags(self):
        tagslist = []
        joblist = self.jobs
        for job_item in joblist:
            if len(list(job_item.tags)):
                tagslist.extend(list(job_item.tags))
        return tagslist

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

        while True:
            self.schedule.run_pending()
            time.sleep(1)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if hasattr(self.schedule, name):
            return eval("self.schedule.%s" % name)
