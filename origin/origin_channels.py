import m3u8

from fHDHR.tools import isint, isfloat


class OriginChannels():

    def __init__(self, fhdhr, origin):
        self.fhdhr = fhdhr
        self.origin = origin

    def get_channels(self):

        stations_url = 'https://api.locastnet.org/api/watch/epg/' + str(self.origin.location["DMA"])
        url_headers = {'Content-Type': 'application/json', 'authorization': 'Bearer %s' % self.origin.token}

        try:
            stationsReq = self.fhdhr.web.session.get(stations_url, headers=url_headers)
            stationsReq.raise_for_status()
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

    def get_channel_stream(self, chandict):
        videoUrl = ('https://api.locastnet.org/api/watch/station/' +
                    str(chandict["origin_id"]) + '/' +
                    self.origin.location['latitude'] + '/' +
                    self.origin.location['longitude']
                    )
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

        if self.fhdhr.config.dict["origin"]["force_best"]:
            streamurl = self.m3u8_beststream(videoUrlRes['streamUrl'])
        else:
            streamurl = videoUrlRes['streamUrl']
        return streamurl

    def m3u8_beststream(self, m3u8_url):
        bestStream = None
        videoUrlM3u = m3u8.load(m3u8_url)
        self.fhdhr.logger.info('force_best set in config. Checking for Best Stream')

        if len(videoUrlM3u.playlists) == 0 or not videoUrlM3u.is_variant:
            self.fhdhr.logger.info('No Stream Variants Available.')
            return m3u8_url

        for videoStream in videoUrlM3u.playlists:
            if not bestStream:
                bestStream = videoStream
            elif videoStream.stream_info.bandwidth > bestStream.stream_info.bandwidth:
                bestStream = videoStream

        if bestStream:
            self.fhdhr.logger.info('BestStream URL Found!')
            return bestStream.absolute_uri
        else:
            self.fhdhr.logger.info('No Stream Variant Found.')
            return m3u8_url
