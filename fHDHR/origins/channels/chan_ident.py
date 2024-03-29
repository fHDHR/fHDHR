import uuid


class Channel_IDs():
    """
    fHDHR channel Identification system.
    """

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.origins = origins

    def get(self, origin_id, origin_obj):
        """
        Get a Channel ID for existing, or assign.
        """

        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin_obj.name) or []
        existing_channel_info = [self.fhdhr.db.get_fhdhr_value(channel_id, "dict", origin_obj.name) or {} for channel_id in existing_ids]
        for existing_channel in existing_channel_info:

            if existing_channel["origin_id"] == origin_id:
                return existing_channel["id"]

        return self.assign(origin_obj)

    def assign(self, origin_obj):
        """
        Assign a channel an ID.
        """

        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin_obj.name) or []

        channel_id = None
        while not channel_id:

            unique_id = str(uuid.uuid4())
            if str(unique_id) not in existing_ids:
                channel_id = str(unique_id)

        existing_ids.append(channel_id)
        self.fhdhr.db.set_fhdhr_value("channels", "list", existing_ids, origin_obj.name)

        return channel_id

    def get_number(self, channel_id, origin_obj):
        """
        Get an unused channel number.
        """

        existing_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin_obj.name) or []
        existing_channel_info = [self.fhdhr.db.get_fhdhr_value(channel_id, "dict", origin_obj.name) or {} for channel_id in existing_ids]

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
