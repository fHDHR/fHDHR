import uuid


class Channel_IDs():
    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def get(self, origin_id):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "IDs") or []
        existing_channel_info = [self.fhdhr.db.get_channel_value(channel_id, "info") or {} for channel_id in existing_ids]
        for existing_channel in existing_channel_info:
            if existing_channel["origin_id"] == origin_id:
                return existing_channel["fhdhr_id"]
        return self.assign()

    def assign(self):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "IDs") or []
        channel_id = None
        while not channel_id:
            unique_id = str(uuid.uuid4())
            if str(unique_id) not in existing_ids:
                channel_id = str(unique_id)
        existing_ids.append(channel_id)
        self.fhdhr.db.set_fhdhr_value("channels", "IDs", existing_ids)
        return channel_id

    def get_number(self, channel_id):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "IDs") or []
        existing_channel_info = [self.fhdhr.db.get_channel_value(channel_id, "info") or {} for channel_id in existing_ids]
        cnumber = [existing_channel["number"] for existing_channel in existing_channel_info if existing_channel["fhdhr_id"] == channel_id] or None
        if cnumber:
            return cnumber

        used_numbers = [existing_channel["number"] for existing_channel in existing_channel_info]
        for i in range(1000, 2000):
            if str(float(i)) not in used_numbers:
                break
        return str(float(i))
