from gevent.pywsgi import WSGIServer
from flask import Flask, send_from_directory, request, abort, Response, stream_with_context

from . import fHDHRdevice


class HDHR_Hub():

    def __init__(self):
        pass

    def hubprep(self, settings, origserv, epghandling):
        self.config = settings

        self.devicexml = fHDHRdevice.Device_XML(settings)
        self.discoverjson = fHDHRdevice.Discover_JSON(settings)
        self.lineupxml = fHDHRdevice.Lineup_XML(settings, origserv)
        self.lineupjson = fHDHRdevice.Lineup_JSON(settings, origserv)
        self.lineupstatusjson = fHDHRdevice.Lineup_Status_JSON(settings, origserv)
        self.images = fHDHRdevice.imageHandler(settings, epghandling)
        self.tuners = fHDHRdevice.Tuners(settings)
        self.watch = fHDHRdevice.WatchStream(settings, origserv, self.tuners)
        self.station_scan = fHDHRdevice.Station_Scan(settings, origserv)
        self.xmltv = fHDHRdevice.xmlTV_XML(settings, epghandling)
        self.htmlerror = fHDHRdevice.HTMLerror(settings)

        self.debug = fHDHRdevice.Debug_JSON(settings, origserv, epghandling)

        self.origserv = origserv
        self.epghandling = epghandling

    def tuner_grab(self):
        self.tuners.tuner_grab()

    def tuner_close(self):
        self.tuners.tuner_close()

    def get_xmltv(self, base_url):
        return self.xmltv.get_xmltv_xml(base_url)

    def get_device_xml(self, base_url):
        return self.devicexml.get_device_xml(base_url)

    def get_discover_json(self, base_url):
        return self.discoverjson.get_discover_json(base_url)

    def get_lineup_status_json(self):
        return self.lineupstatusjson.get_lineup_json(self.station_scan.scanning())

    def get_lineup_xml(self, base_url):
        return self.lineupxml.get_lineup_xml(base_url)

    def get_lineup_json(self, base_url):
        return self.lineupjson.get_lineup_json(base_url)

    def get_debug_json(self, base_url):
        return self.debug.get_debug_json(base_url, self.tuners.tuners)

    def get_html_error(self, message):
        return self.htmlerror.get_html_error(message)

    def post_lineup_scan_start(self):
        self.station_scan.scan()

    def get_image(self, request_args):
        return self.images.get_image(request_args)

    def get_stream_info(self, request_args):
        return self.watch.get_stream_info(request_args)

    def get_stream(self, channel_id, method, channelUri, content_type):
        return self.watch.get_stream(channel_id, method, channelUri, content_type)


hdhr = HDHR_Hub()


class HDHR_HTTP_Server():
    app = Flask(__name__,)

    @app.route('/')
    def root_path():
        return hdhr.config.dict["fhdhr"]["friendlyname"]

    @app.route('/favicon.ico', methods=['GET'])
    def favicon():
        return send_from_directory(hdhr.config.dict["filedir"]["www_dir"],
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

    @app.route('/device.xml', methods=['GET'])
    def device_xml():
        base_url = request.headers["host"]
        device_xml = hdhr.get_device_xml(base_url)
        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')

    @app.route('/discover.json', methods=['GET'])
    def discover_json():
        base_url = request.headers["host"]
        discover_json = hdhr.get_discover_json(base_url)
        return Response(status=200,
                        response=discover_json,
                        mimetype='application/json')

    @app.route('/lineup_status.json', methods=['GET'])
    def lineup_status_json():
        linup_status_json = hdhr.get_lineup_status_json()
        return Response(status=200,
                        response=linup_status_json,
                        mimetype='application/json')

    @app.route('/lineup.xml', methods=['GET'])
    def lineup_xml():
        base_url = request.headers["host"]
        lineupxml = hdhr.get_lineup_xml(base_url)
        return Response(status=200,
                        response=lineupxml,
                        mimetype='application/xml')

    @app.route('/lineup.json', methods=['GET'])
    def lineup_json():
        base_url = request.headers["host"]
        station_list = hdhr.get_lineup_json(base_url)
        return Response(status=200,
                        response=station_list,
                        mimetype='application/json')

    @app.route('/xmltv.xml', methods=['GET'])
    def xmltv_xml():
        base_url = request.headers["host"]
        xmltv = hdhr.get_xmltv(base_url)
        return Response(status=200,
                        response=xmltv,
                        mimetype='application/xml')

    @app.route('/api/xmltv')
    def api_xmltv():
        if 'DeviceAuth' in list(request.args.keys()):
            if request.args['DeviceAuth'] == hdhr.config.dict["dev"]["device_auth"]:
                base_url = request.headers["host"]
                xmltv = hdhr.get_xmltv(base_url)
                return Response(status=200,
                                response=xmltv,
                                mimetype='application/xml')
        return "not subscribed"

    @app.route('/debug.json', methods=['GET'])
    def debug_json():
        base_url = request.headers["host"]
        debugreport = hdhr.get_debug_json(base_url)
        return Response(status=200,
                        response=debugreport,
                        mimetype='application/json')

    @app.route('/images', methods=['GET'])
    def images():
        image, imagetype = hdhr.get_image(request.args)
        return Response(image, content_type=imagetype, direct_passthrough=True)

    @app.route('/auto/<channel>')
    def auto(channel):
        request_args = {
                        "channel": channel.replace('v', ''),
                        "method": hdhr.config.dict["fhdhr"]["stream_type"]
                        }
        channel_id = request_args["channel"]
        method, channelUri, content_type = hdhr.get_stream_info(request_args)
        if channelUri:
            if method == "direct":
                return Response(hdhr.get_stream(channel_id, method, channelUri, content_type), content_type=content_type, direct_passthrough=True)
            elif method == "ffmpeg":
                return Response(stream_with_context(hdhr.get_stream(channel_id, method, channelUri, content_type)), mimetype="video/mpeg")
        abort(503)

    @app.route('/watch', methods=['GET'])
    def watch():
        if 'method' in list(request.args.keys()) and 'channel' in list(request.args.keys()):
            channel_id = str(request.args["channel"])
            method = str(request.args["method"])
            method, channelUri, content_type = hdhr.get_stream_info(request.args)
            if channelUri:
                if method == "direct":
                    return Response(hdhr.get_stream(channel_id, method, channelUri, content_type), content_type=content_type, direct_passthrough=True)
                elif method == "ffmpeg":
                    return Response(stream_with_context(hdhr.get_stream(channel_id, method, channelUri, content_type)), mimetype="video/mpeg")
        abort(503)

    @app.route('/lineup.post', methods=['POST'])
    def lineup_post():
        if 'scan' in list(request.args.keys()):
            if request.args['scan'] == 'start':
                hdhr.post_lineup_scan_start()
                return Response(status=200, mimetype='text/html')
            elif request.args['scan'] == 'abort':
                return Response(status=200, mimetype='text/html')
            else:
                print("Unknown scan command " + request.args['scan'])
                currenthtmlerror = hdhr.get_html_error("501 - " + request.args['scan'] + " is not a valid scan command")
                return Response(status=200, response=currenthtmlerror, mimetype='text/html')
        else:
            currenthtmlerror = hdhr.get_html_error("501 - not a valid command")
            return Response(status=200, response=currenthtmlerror, mimetype='text/html')

    def __init__(self, settings):
        self.config = settings

    def run(self):
        self.http = WSGIServer((
                            self.config.dict["fhdhr"]["address"],
                            int(self.config.dict["fhdhr"]["port"])
                            ), self.app.wsgi_app)
        try:
            self.http.serve_forever()
        except KeyboardInterrupt:
            self.http.stop()


def interface_start(settings, origserv, epghandling):
    print("Starting fHDHR Web Interface")
    hdhr.hubprep(settings, origserv, epghandling)
    fakhdhrserver = HDHR_HTTP_Server(settings)
    fakhdhrserver.run()
