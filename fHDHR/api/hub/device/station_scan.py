from multiprocessing import Process


class Station_Scan():

    def __init__(self, settings, channels):
        self.config = settings
        self.channels = channels
        self.chanscan = Process(target=self.runscan)

    def scan(self):
        print("Channel Scan Requested by Client.")
        try:
            self.chanscan.start()
        except AssertionError:
            print("Channel Scan Already In Progress!")

    def runscan(self):
        self.channels.get_channels(forceupdate=True)
        print("Requested Channel Scan Complete.")

    def scanning(self):
        try:
            self.chanscan.join(timeout=0)
            return self.chanscan.is_alive()
        except AssertionError:
            return False
