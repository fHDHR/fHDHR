from datetime import datetime
import time


class Time_Manager():

    def __init__(self):
        self._start = {
                        "datetime": datetime.now(),
                        "epoch": time.time()
                        }

    def setup(self, config, logger):
        self.config = config
        self.logger = logger

        self.logger.debug("Setting Up Time Manager.")

    @property
    def time_periods(self):
        return list(dict((v, k) for k, v in self.levels.items()).keys())

    @property
    def level(self):
        level = self.config.dict["fhdhr"]["humanized_time_granularity"].lower()
        if level in self.time_periods:
            return level
        if level.endswith("s"):
            level_unpluraled = level[:-1]
            if level_unpluraled in self.time_periods:
                return level_unpluraled
        level = self.conf_level_default
        return level

    @property
    def level_number(self):
        res = dict((v, k) for k, v in self.levels.items())
        level_number = res[self.level]
        return level_number

    @property
    def conf_level_default(self):
        return self.config.conf_default["fhdhr"]["humanized_time_granularity"]["value"]

    @property
    def start_datetime(self):
        return self._start["datetime"]

    @property
    def start_epoch(self):
        return self._start["epoch"]

    def humanized_time(self, timeval):

        if isinstance(timeval, type(None)):
            return "N/A"

        displaymsg = None

        timeval = float(timeval)

        levels = self.levels
        level_number = self.level_number

        time_periods = []
        for time_period_level_number in list(levels.keys()):
            if time_period_level_number <= level_number:
                level_name = levels[time_period_level_number]
                time_periods.append(level_name)

                if level_name == "year":
                    currenttimevar = timeval // (365 * 24 * 3600)
                    timeval = timeval % (365 * 24 * 3600)
                elif level_name == "day":
                    currenttimevar = timeval // (24 * 3600)
                    timeval = timeval % (24 * 3600)
                elif level_name == "hour":
                    currenttimevar = timeval // 3600
                    timeval %= 3600
                elif level_name in ["minute", "second"]:
                    currenttimevar = timeval // 60
                    timeval %= 60

                if currenttimevar >= 1:
                    time_period = level_name
                    if currenttimevar > 1:
                        time_period = str(time_period + "s")
                    if displaymsg:
                        displaymsg = "%s %s %s" % (displaymsg, int(currenttimevar), time_period)
                    else:
                        displaymsg = "%s %s" % (int(currenttimevar), time_period)

        if not displaymsg:
            displaymsg = "less than 1 %s" % time_periods[-1]

        return displaymsg

    @property
    def levels(self):
        return {
                0: "year",
                1: "day",
                2: "hour",
                3: "minute",
                4: "second"
                }
