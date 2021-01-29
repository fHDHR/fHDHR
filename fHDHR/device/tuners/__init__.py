import m3u8

from fHDHR.exceptions import TunerError

from .tuner import Tuner


class Tuners():

    def __init__(self, fhdhr, epg, channels):
        self.fhdhr = fhdhr
        self.channels = channels

        self.epg = epg

        self.tuners = {}
        for origin in list(self.fhdhr.origins.origins_dict.keys()):
            self.tuners[origin] = {}

            max_tuners = int(self.fhdhr.origins.origins_dict[origin].tuners)

            self.fhdhr.logger.info("Creating %s tuners for %s." % (max_tuners, origin))

            for i in range(0, max_tuners):
                self.tuners[origin][str(i)] = Tuner(fhdhr, i, epg, origin)

        self.alt_stream_handlers = {}

    def alt_stream_methods_selfadd(self):
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
                method = self.fhdhr.plugins.plugins[plugin_name].name
                self.alt_stream_handlers[method] = self.fhdhr.plugins.plugins[plugin_name]

    def get_available_tuner(self, origin):
        return next(tunernum for tunernum in list(self.tuners[origin].keys()) if not self.tuners[origin][tunernum].tuner_lock.locked()) or None

    def get_scanning_tuner(self, origin):
        return next(tunernum for tunernum in list(self.tuners[origin].keys()) if self.tuners[origin][tunernum].status["status"] == "Scanning") or None

    def stop_tuner_scan(self, origin):
        tunernum = self.get_scanning_tuner(origin)
        if tunernum:
            self.tuners[origin][str(tunernum)].close()

    def tuner_scan(self, origin="all"):
        """Temporarily use a tuner for a scan"""

        if origin == "all":
            origins = list(self.tuners.keys())
        else:
            origins = [origin]

        for origin in origins:

            if not self.available_tuner_count(origin):
                raise TunerError("805 - All Tuners In Use")

            tunernumber = self.get_available_tuner(origin)
            self.tuners[str(tunernumber)].channel_scan(origin)

            if not tunernumber:
                raise TunerError("805 - All Tuners In Use")

    def tuner_grab(self, tuner_number, origin, channel_number):

        if str(tuner_number) not in list(self.tuners[origin].keys()):
            self.fhdhr.logger.error("Tuner %s does not exist for %s." % (tuner_number, origin))
            raise TunerError("806 - Tune Failed")

        # TunerError will raise if unavailable
        self.tuners[origin][str(tuner_number)].grab(origin, channel_number)

        return tuner_number

    def first_available(self, origin, channel_number, dograb=True):

        if not self.available_tuner_count(origin):
            raise TunerError("805 - All Tuners In Use")

        tunernumber = self.get_available_tuner(origin)

        if not tunernumber:
            raise TunerError("805 - All Tuners In Use")
        else:
            self.tuners[origin][str(tunernumber)].grab(origin, channel_number)
            return tunernumber

    def tuner_close(self, tunernum, origin):
        self.tuners[origin][str(tunernum)].close()

    def status(self, origin=None):
        all_status = {}
        if origin:
            for tunernum in list(self.tuners[origin].keys()):
                all_status[tunernum] = self.tuners[origin][str(tunernum)].get_status()
        else:
            for origin in list(self.tuners.keys()):
                all_status[origin] = {}
                for tunernum in list(self.tuners[origin].keys()):
                    all_status[origin][tunernum] = self.tuners[origin][str(tunernum)].get_status()
        return all_status

    def available_tuner_count(self, origin):
        available_tuners = 0
        for tunernum in list(self.tuners[origin].keys()):
            if not self.tuners[origin][str(tunernum)].tuner_lock.locked():
                available_tuners += 1
        return available_tuners

    def inuse_tuner_count(self, origin):
        inuse_tuners = 0
        for tunernum in list(self.tuners[origin].keys()):
            if self.tuners[origin][str(tunernum)].tuner_lock.locked():
                inuse_tuners += 1
        return inuse_tuners

    def get_stream_info(self, stream_args):

        stream_info = self.channels.get_channel_stream(stream_args, stream_args["origin"])
        if not stream_info:
            raise TunerError("806 - Tune Failed")

        if isinstance(stream_info, str):
            stream_info = {"url": stream_info, "headers": None}
        stream_args["stream_info"] = stream_info

        if not stream_args["stream_info"]["url"]:
            raise TunerError("806 - Tune Failed")

        if "headers" not in list(stream_args["stream_info"].keys()):
            stream_args["stream_info"]["headers"] = None

        if stream_args["stream_info"]["url"].startswith("udp://"):
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"
        else:

            channel_stream_url_headers = self.fhdhr.web.session.head(stream_args["stream_info"]["url"]).headers
            stream_args["true_content_type"] = channel_stream_url_headers['Content-Type']

            if stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                stream_args["content_type"] = "video/mpeg"
                if stream_args["origin_quality"] != -1:
                    stream_args["stream_info"]["url"] = self.m3u8_quality(stream_args)
            else:
                stream_args["content_type"] = stream_args["true_content_type"]

        return stream_args

    def m3u8_quality(self, stream_args):

        m3u8_url = stream_args["stream_info"]["url"]
        quality_profile = stream_args["origin_quality"]

        if not quality_profile:
            if stream_args["method"] == "direct":
                quality_profile = "high"
                self.fhdhr.logger.info("Origin Quality not set in config. Direct Method set and will default to Highest Quality")
            else:
                self.fhdhr.logger.info("Origin Quality not set in config. %s Method will select the Quality Automatically" % stream_args["method"])
                return m3u8_url
        else:
            quality_profile = quality_profile.lower()
            self.fhdhr.logger.info("Origin Quality set in config to %s" % (quality_profile))

        while True:
            self.fhdhr.logger.info("Opening m3u8 for reading %s" % m3u8_url)

            try:
                if stream_args["stream_info"]["headers"]:
                    videoUrlM3u = m3u8.load(m3u8_url, headers=stream_args["stream_info"]["headers"])
                else:
                    videoUrlM3u = m3u8.load(m3u8_url)
            except Exception as e:
                self.fhdhr.logger.info("m3u8 load error: %s" % e)
                return m3u8_url

            if len(videoUrlM3u.playlists):
                self.fhdhr.logger.info("%s m3u8 varients found" % len(videoUrlM3u.playlists))

                # Create list of dicts
                playlists, playlist_index = {}, 0
                for playlist_item in videoUrlM3u.playlists:
                    playlist_index += 1
                    playlist_dict = {
                                    "url": playlist_item.absolute_uri,
                                    "bandwidth": playlist_item.stream_info.bandwidth,
                                    }

                    if not playlist_item.stream_info.resolution:
                        playlist_dict["width"] = None
                        playlist_dict["height"] = None
                    else:
                        try:
                            playlist_dict["width"] = playlist_item.stream_info.resolution[0]
                            playlist_dict["height"] = playlist_item.stream_info.resolution[1]
                        except TypeError:
                            playlist_dict["width"] = None
                            playlist_dict["height"] = None

                    playlists[playlist_index] = playlist_dict

                sorted_playlists = sorted(playlists, key=lambda i: (
                    int(playlists[i]['bandwidth']),
                    int(playlists[i]['width'] or 0),
                    int(playlists[i]['height'] or 0)
                    ))
                sorted_playlists = [playlists[x] for x in sorted_playlists]

                if not quality_profile or quality_profile == "high":
                    selected_index = -1
                elif quality_profile == "medium":
                    selected_index = int((len(sorted_playlists) - 1)/2)
                elif quality_profile == "low":
                    selected_index = 0

                m3u8_stats = ",".join(
                    ["%s %s" % (x, sorted_playlists[selected_index][x])
                     for x in list(sorted_playlists[selected_index].keys())
                     if x != "url" and sorted_playlists[selected_index][x]])
                self.fhdhr.logger.info("Selected m3u8 details: %s" % m3u8_stats)
                m3u8_url = sorted_playlists[selected_index]["url"]

            else:
                self.fhdhr.logger.info("No m3u8 varients found")
                break

        return m3u8_url
