import time
import datetime
import m3u8
from collections import OrderedDict
from Crypto.Cipher import AES


class Direct_M3U8_Stream():
    """
    A method to stream m3u8.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Detected M3U8 stream URL: %s" % self.stream_args["stream_info"]["url"])

        def generate():

            segments_dict = OrderedDict()
            start_time = datetime.datetime.utcnow()
            total_secs_served = 0
            chunks_counter = 0

            while self.tuner.tuner_lock.locked():

                added, removed = 0, 0

                # (re)Load the m3u8_obj, apply headers if needbe
                try:
                    if self.stream_args["stream_info"]["headers"]:
                        m3u8_obj = m3u8.load(self.stream_args["stream_info"]["url"], headers=self.stream_args["stream_info"]["headers"])
                    else:
                        m3u8_obj = m3u8.load(self.stream_args["stream_info"]["url"])
                except Exception as exerror:
                    error_out = self.fhdhr.logger.lazy_exception(exerror, "Connection Closed")
                    self.fhdhr.logger.error(error_out)
                    return None

                m3u8_segments = m3u8_obj.segments

                if m3u8_obj.keys != [None]:
                    keys = [{"uri": key.absolute_uri, "method": key.method, "iv": key.iv} for key in m3u8_obj.keys if key]
                else:
                    keys = [None for i in range(0, len(m3u8_segments))]

                # Only add new m3u8_segments to our segments_dict
                for segment, key in zip(m3u8_segments, keys):
                    uri = segment.absolute_uri
                    if uri not in list(segments_dict.keys()):
                        chunks_counter += 1
                        segments_dict[uri] = {
                                              "downloaded": False,
                                              "duration": segment.duration,
                                              "chunk_number": chunks_counter,
                                              "key": key
                                              }
                        added += 1
                        self.fhdhr.logger.debug("Adding %s to download queue." % uri)

                    segments_dict[uri]["last_seen"] = datetime.datetime.utcnow()

                # Cleanup downloaded Queue
                for uri, data in list(segments_dict.items()):
                    if data["downloaded"] and (datetime.datetime.utcnow() - data["last_seen"]).total_seconds() > 360:
                        self.fhdhr.logger.debug("Removed %s from download queue." % uri)
                        del segments_dict[uri]
                        removed += 1

                self.fhdhr.logger.info("Refreshing m3u8, Loaded %s new segments, removed %s" % (added, removed))

                for uri, data in list(segments_dict.items()):

                    if not data["downloaded"]:

                        self.fhdhr.logger.debug("Downloading Chunk #%s: %s" % (data["chunk_number"], uri))
                        if self.stream_args["stream_info"]["headers"]:
                            chunk = self.fhdhr.web.session.get(uri, headers=self.stream_args["stream_info"]["headers"]).content
                        else:
                            chunk = self.fhdhr.web.session.get(uri).content

                        if data["key"]:
                            if data["key"]["uri"]:
                                if self.stream_args["stream_info"]["headers"]:
                                    keyfile = self.fhdhr.web.session.get(data["key"]["uri"], headers=self.stream_args["stream_info"]["headers"]).content
                                else:
                                    keyfile = self.fhdhr.web.session.get(data["key"]["uri"]).content
                                cryptor = AES.new(keyfile, AES.MODE_CBC, keyfile)
                                self.fhdhr.logger.debug("Decrypting Chunk #%s with key: %s" % (data["chunk_number"], data["key"]["uri"]))
                                chunk = cryptor.decrypt(chunk)

                        segments_dict[uri]["downloaded"] = True

                        if not chunk:
                            break

                        total_secs_served += data['duration']
                        yield chunk

                total_duration = sum([segment.duration for segment in m3u8_obj.segments])
                target_diff = 0.5 * total_duration
                runtime = (datetime.datetime.utcnow() - start_time).total_seconds()

                if total_secs_served > 0:
                    wait = total_secs_served - target_diff - runtime
                else:
                    wait = 0

                if wait > 0:
                    time.sleep(wait)

        return generate()


def m3u8_quality(fhdhr, stream_args):
    """
    Set the m3u8 Quality.
    """

    m3u8_url = stream_args["stream_info"]["url"]
    quality_profile = stream_args["origin_quality"]

    if not quality_profile:

        if stream_args["method"] in ["direct", "passthrough"]:
            quality_profile = "high"
            fhdhr.logger.info("Origin Quality not set in config. %s Method set and will default to Highest Quality" % stream_args["method"])

        else:
            fhdhr.logger.info("Origin Quality not set in config. %s Method will select the Quality Automatically" % stream_args["method"])
            return m3u8_url

    else:
        quality_profile = quality_profile.lower()
        fhdhr.logger.info("Origin Quality set in config to %s" % (quality_profile))

    while True:
        fhdhr.logger.info("Opening m3u8 for reading %s" % m3u8_url)

        try:

            if stream_args["stream_info"]["headers"]:
                videoUrlM3u = m3u8.load(m3u8_url, headers=stream_args["stream_info"]["headers"])

            else:
                videoUrlM3u = m3u8.load(m3u8_url)

        except Exception as exerror:
            error_out = fhdhr.logger.lazy_exception(exerror, "m3u8 load error")
            fhdhr.logger.error(error_out)
            return m3u8_url

        if len(videoUrlM3u.playlists):
            fhdhr.logger.info("%s m3u8 varients found" % len(videoUrlM3u.playlists))

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
            fhdhr.logger.info("Selected m3u8 details: %s" % m3u8_stats)
            m3u8_url = sorted_playlists[selected_index]["url"]

        else:
            fhdhr.logger.info("No m3u8 varients found")
            break

    return m3u8_url
