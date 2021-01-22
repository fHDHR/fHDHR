
from fHDHR.tools import isint, isfloat


class OriginChannels():

    def __init__(self, fhdhr, origin):
        self.fhdhr = fhdhr
        self.origin = origin

    def get_channels(self):

        stations_url = 'https://api.locastnet.org/api/watch/epg/%s' % self.origin.location["DMA"]
        url_headers = {'Content-Type': 'application/json', 'authorization': 'Bearer %s' % self.origin.token}

        try:
            stationsReq = self.fhdhr.web.session.get(stations_url, headers=url_headers)
            stationsReq.raise_for_status()
        except self.fhdhr.web.exceptions.SSLError as err:
            self.fhdhr.logger.error('Error while getting stations: %s' % err)
            return []
        except self.fhdhr.web.exceptions.HTTPError as err:
            self.fhdhr.logger.error('Error while getting stations: %s' % err)
            return []

        stationsRes = stationsReq.json()

        cleaned_channels = []
        for station_item in stationsRes:

            thumbnails = []
            for thumb_opt in ["logo226Url", "logoUrl"]:

                try:
                    thumbnail = station_item[thumb_opt]
                except TypeError:
                    thumbnail = None
                except KeyError:
                    thumbnail = None
                if thumbnail:
                    thumbnails.append(thumbnail)
            if not len(thumbnails):
                thumbnails = [None]

            clean_station_item = {
                                 "name": station_item["name"],
                                 "id": station_item["id"],
                                 "thumbnail": thumbnails[0]
                                 }

            # Typically this will be `2.1 KTTW` but occasionally Locast only provides a channel number here
            # fHDHR device.channels will provide us a number if that is the case
            if (isint(str(station_item['callSign']).split(" ")[0])
               or isfloat(str(station_item['callSign']).split(" ")[0])):
                clean_station_item["number"] = str(station_item['callSign']).split(" ")[0]
                clean_station_item["callsign"] = str(" ".join(station_item['callSign'].split(" ")[1:]))
            else:
                clean_station_item["callsign"] = str(station_item['callSign'])

            cleaned_channels.append(clean_station_item)
        return cleaned_channels

    def get_channel_stream(self, chandict, stream_args):

        videoUrl = "https://api.locastnet.org/api/watch/station/%s/%s/%s" % (chandict["origin_id"], self.origin.location['latitude'], self.origin.location['longitude'])

        videoUrl_headers = {
                            'Content-Type': 'application/json',
                            'authorization': 'Bearer %s' % self.origin.token,
                            'User-Agent': "curl/7.64.1"}

        try:
            videoUrlReq = self.fhdhr.web.session.get(videoUrl, headers=videoUrl_headers)
            videoUrlReq.raise_for_status()
        except self.fhdhr.web.exceptions.HTTPError as err:
            self.fhdhr.logger.error('Error while getting station URL: %s' % err)
            return None

        videoUrlRes = videoUrlReq.json()

        stream_info = {"url": videoUrlRes['streamUrl']}

        return stream_info
