

class fHDHR_Detect():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr
        self.fhdhr.db.delete_fhdhr_value("ssdp_detect", "list")

    def set(self, location):
        detect_list = self.fhdhr.db.get_fhdhr_value("ssdp_detect", "list") or []
        if location not in detect_list:
            detect_list.append(location)
            self.fhdhr.db.set_fhdhr_value("ssdp_detect", "list", detect_list)

    def get(self):
        return self.fhdhr.db.get_fhdhr_value("ssdp_detect", "list") or []
