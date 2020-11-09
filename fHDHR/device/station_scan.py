from multiprocessing import Process


class Station_Scan():

    def __init__(self, settings, channels, logger, db):
        self.config = settings
        self.logger = logger
        self.channels = channels
        self.db = db
        self.db.delete_fhdhr_value("station_scan", "scanning")

    def scan(self):
        self.logger.info("Channel Scan Requested by Client.")

        scan_status = self.db.get_fhdhr_value("station_scan", "scanning")
        if not scan_status:
            self.db.set_fhdhr_value("station_scan", "scanning", 1)
            chanscan = Process(target=self.runscan)
            chanscan.start()
        else:
            self.logger.info("Channel Scan Already In Progress!")

    def runscan(self):
        self.channels.get_channels(forceupdate=True)
        self.logger.info("Requested Channel Scan Complete.")
        self.db.delete_fhdhr_value("station_scan", "scanning")

    def scanning(self):
        scan_status = self.db.get_fhdhr_value("station_scan", "scanning")
        if not scan_status:
            return False
        else:
            return True
