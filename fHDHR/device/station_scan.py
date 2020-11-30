import multiprocessing
import threading


class Station_Scan():

    def __init__(self, fhdhr, channels):
        self.fhdhr = fhdhr

        self.channels = channels

        self.fhdhr.db.delete_fhdhr_value("station_scan", "scanning")

    def scan(self, waitfordone=False):
        self.fhdhr.logger.info("Channel Scan Requested by Client.")

        scan_status = self.fhdhr.db.get_fhdhr_value("station_scan", "scanning")
        if scan_status:
            self.fhdhr.logger.info("Channel Scan Already In Progress!")
        else:
            self.fhdhr.db.set_fhdhr_value("station_scan", "scanning", 1)

            if waitfordone:
                self.runscan()
            else:
                if self.fhdhr.config.dict["main"]["thread_method"] in ["multiprocessing"]:
                    chanscan = multiprocessing.Process(target=self.runscan)
                elif self.fhdhr.config.dict["main"]["thread_method"] in ["threading"]:
                    chanscan = threading.Thread(target=self.runscan)
                if self.fhdhr.config.dict["main"]["thread_method"] in ["multiprocessing", "threading"]:
                    chanscan.start()

    def runscan(self):
        self.channels.get_channels(forceupdate=True)
        self.fhdhr.logger.info("Requested Channel Scan Complete.")
        self.fhdhr.db.delete_fhdhr_value("station_scan", "scanning")

    def scanning(self):
        scan_status = self.fhdhr.db.get_fhdhr_value("station_scan", "scanning")
        if not scan_status:
            return False
        else:
            return True
