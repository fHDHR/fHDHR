from . import device, pages, files


class fHDHR_Hub():

    def __init__(self):
        pass

    def setup(self, settings, origin):
        self.config = settings

        self.origin = origin

        self.device = device.fHDHR_Device(settings, origin)

        self.pages = pages.fHDHR_Pages(settings, self.device)

        self.files = files.fHDHR_Files(settings, self.device)

    def get_xmltv(self, base_url):
        return self.files.xmltv.get_xmltv_xml(base_url)

    def get_device_xml(self, base_url):
        return self.files.devicexml.get_device_xml(base_url)

    def get_discover_json(self, base_url):
        return self.files.discoverjson.get_discover_json(base_url)

    def get_lineup_status_json(self):
        return self.files.lineupstatusjson.get_lineup_status_json()

    def get_lineup_xml(self, base_url):
        return self.files.lineupxml.get_lineup_xml(base_url)

    def get_lineup_json(self, base_url):
        return self.files.lineupjson.get_lineup_json(base_url)

    def get_debug_json(self, base_url):
        return self.files.debug.get_debug_json(base_url)

    def get_cluster_json(self, base_url):
        return self.files.cluster.get_cluster_json(base_url)

    def get_html_error(self, message):
        return self.pages.htmlerror.get_html_error(message)

    def post_lineup_scan_start(self):
        self.device.station_scan.scan()

    def get_image(self, request_args):
        return self.device.images.get_image(request_args)

    def get_channels_m3u(self, base_url):
        return self.files.m3u.get_channels_m3u(base_url)

    def get_channel_m3u(self, base_url, channel_number):
        return self.files.m3u.get_channel_m3u(base_url, channel_number)

    def get_stream_info(self, stream_args):
        return self.device.watch.get_stream_info(stream_args)

    def get_stream(self, stream_args):
        return self.device.watch.get_stream(stream_args)

    def get_index_html(self, base_url):
        return self.pages.index.get_index_html(base_url)

    def get_channel_guide_html(self):
        return self.pages.channel_guide.get_channel_guide_html()

    def get_diagnostics_html(self, base_url):
        return self.pages.diagnostics.get_diagnostics_html(base_url)

    def get_streams_html(self, base_url):
        return self.pages.streams.get_streams_html(base_url)

    def get_version_html(self, base_url):
        return self.pages.version.get_version_html(base_url)

    def get_origin_html(self, base_url):
        return self.pages.origin.get_origin_html(base_url)

    def get_cluster_html(self, base_url):
        return self.pages.cluster.get_cluster_html(base_url)

    def m_search(self):
        self.device.ssdp.m_search()

    def cluster_add(self, location):
        self.device.cluster.add(location)

    def cluster_del(self, location):
        self.device.cluster.remove(location)

    def cluster_sync(self, location):
        self.device.cluster.sync(location)

    def cluster_leave(self):
        self.device.cluster.leave()

    def cluster_disconnect(self):
        self.device.cluster.disconnect()
