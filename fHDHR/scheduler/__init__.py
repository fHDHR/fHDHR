import schedule
import time


class Scheduler():

    def __init__(self):
        self.schedule = schedule

    def run(self):

        while True:
            self.schedule.run_pending()
            time.sleep(1)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.schedule, name):
            return eval("self.schedule.%s" % name)
