import uuid


class Channel_IDs():
    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.origins = origins

    def get(self, origin_id, origin):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin) or []
        existing_channel_info = [self.fhdhr.db.get_fhdhr_value(channel_id, "dict", origin) or {} for channel_id in existing_ids]
        for existing_channel in existing_channel_info:
            if existing_channel["origin_id"] == origin_id:
                return existing_channel["id"]
        return self.assign(origin)

    def assign(self, origin):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin) or []
        channel_id = None
        while not channel_id:
            unique_id = str(uuid.uuid4())
            if str(unique_id) not in existing_ids:
                channel_id = str(unique_id)
        existing_ids.append(channel_id)
        self.fhdhr.db.set_fhdhr_value("channels", "list", existing_ids, origin)
        return channel_id

    def get_number(self, channel_id, origin):
        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin) or []
        existing_channel_info = [self.fhdhr.db.get_fhdhr_value(channel_id, "dict", origin) or {} for channel_id in existing_ids]
        cnumber = [existing_channel["number"] for existing_channel in existing_channel_info if existing_channel["id"] == channel_id] or None
        if cnumber:
            return cnumber

        used_numbers = []
        for existing_channel in existing_channel_info:
            if existing_channel["subnumber"]:
                number = "%s.%s" % (existing_channel["number"], existing_channel["subnumber"])
            else:
                number = existing_channel["number"]
            used_numbers.append(number)

        for i in range(1000, 2000):
            if str(float(i)) not in used_numbers:
                break
        return str(float(i))
