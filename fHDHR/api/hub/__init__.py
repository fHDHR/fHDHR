from . import device, pages, files


class fHDHR_Hub():

    def __init__(self):
        pass

    def setup(self, settings, origin):
        self.config = settings

        self.origin = origin

        self.pages = pages.fHDHR_Pages(settings)

        self.device = device.fHDHR_Device(settings, origin)

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

    def get_html_error(self, message):
        return self.pages.htmlerror.get_html_error(message)

    def post_lineup_scan_start(self):
        self.device.station_scan.scan()

    def get_image(self, request_args):
        return self.device.images.get_image(request_args)

    def get_channels_m3u(self, base_url):
        return self.files.m3u.get_channels_m3u(base_url)

    def get_stream_info(self, stream_args):
        return self.device.watch.get_stream_info(stream_args)

    def get_stream(self, stream_args):
        return self.device.watch.get_stream(stream_args)

    def get_index_html(self, base_url):
        return self.pages.index.get_index_html(base_url)
