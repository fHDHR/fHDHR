import urllib.request
import json
import m3u8


class OriginChannels():

    def __init__(self, settings, origin, logger, web):
        self.config = settings
        self.origin = origin
        self.logger = logger
        self.web = web

    def get_channels(self):

        stationsReq = urllib.request.Request('https://api.locastnet.org/api/watch/epg/' +
                                             str(self.origin.location["DMA"]),
                                             headers={'Content-Type': 'application/json',
                                                      'authorization': 'Bearer ' + self.origin.token})

        stationsOpn = urllib.request.urlopen(stationsReq)
        stationsRes = json.load(stationsOpn)
        stationsOpn.close()

        for index, locast_station in enumerate(stationsRes):
            try:
                assert(float(locast_station['callSign'].split()[0]))
                stationsRes[index]['channel'] = locast_station['callSign'].split()[0]
            except ValueError:
                pass

        cleaned_channels = []
        for station_item in stationsRes:
            clean_station_item = {
                                 "name": station_item["name"],
                                 "callsign": str(station_item['callSign']).split(" ")[1],
                                 "number": str(station_item['callSign']).split(" ")[0],
                                 "id": station_item["id"],
                                 }
            cleaned_channels.append(clean_station_item)
        return cleaned_channels

    def get_channel_stream(self, chandict, allchandict):
        caching = True
        streamlist = []
        streamdict = {}
        videoUrlReq = urllib.request.Request('https://api.locastnet.org/api/watch/station/' +
                                             str(chandict["id"]) + '/' +
                                             self.origin.location['latitude'] + '/' +
                                             self.origin.location['longitude'],
                                             headers={'Content-Type': 'application/json',
                                                      'authorization': 'Bearer ' + self.origin.token})
        videoUrlOpn = urllib.request.urlopen(videoUrlReq)
        videoUrlRes = json.load(videoUrlOpn)
        if self.config.dict["origin"]["force_best"]:
            streamurl = self.m3u8_beststream(videoUrlRes['streamUrl'])
        else:
            streamurl = videoUrlRes['streamUrl']
        streamdict = {"number": chandict["number"], "stream_url": streamurl}
        streamlist.append(streamdict)

        return streamlist, caching

    def m3u8_beststream(self, m3u8_url):
        bestStream = None
        videoUrlM3u = m3u8.load(m3u8_url)

        if not videoUrlM3u.is_variant:
            return m3u8_url

        for videoStream in videoUrlM3u.playlists:
            if not bestStream:
                bestStream = videoStream
            elif videoStream.stream_info.bandwidth > bestStream.stream_info.bandwidth:
                bestStream = videoStream

        if not bestStream:
            return bestStream.absolute_uri
        else:
            return m3u8_url
