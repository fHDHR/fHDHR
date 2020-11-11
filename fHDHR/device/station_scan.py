from multiprocessing import Process


class Station_Scan():

    def __init__(self, fhdhr, channels):
        self.fhdhr = fhdhr

        self.channels = channels

        self.fhdhr.db.delete_fhdhr_value("station_scan", "scanning")

    def scan(self):
        self.fhdhr.logger.info("Channel Scan Requested by Client.")

        scan_status = self.fhdhr.db.get_fhdhr_value("station_scan", "scanning")
        if not scan_status:
            self.fhdhr.db.set_fhdhr_value("station_scan", "scanning", 1)
            chanscan = Process(target=self.runscan)
            chanscan.start()
        else:
            self.fhdhr.logger.info("Channel Scan Already In Progress!")

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
