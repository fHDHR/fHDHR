import schedule
import time


class Scheduler():
    """
    fHDHR Scheduling events system.
    """

    def __init__(self):
        self.schedule = schedule

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
