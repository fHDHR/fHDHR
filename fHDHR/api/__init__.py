from gevent.pywsgi import WSGIServer
from flask import Flask, send_from_directory, request, abort, Response, stream_with_context

from . import hub


fhdhrhub = hub.fHDHR_Hub()


class HDHR_HTTP_Server():
    app = Flask(__name__,)

    @app.route('/')
    def root_path():
        base_url = request.headers["host"]
        return fhdhrhub.get_index_html(base_url)

    @app.route('/guide')
    def channel_guide_html():
        return fhdhrhub.get_channel_guide_html()

    @app.route('/origin')
    def origin_html():
        base_url = request.headers["host"]
        return fhdhrhub.get_origin_html(base_url)

    @app.route('/style.css', methods=['GET'])
    def style_css():
        return send_from_directory(fhdhrhub.config.dict["filedir"]["www_dir"], 'style.css')

    @app.route('/favicon.ico', methods=['GET'])
    def favicon():
        return send_from_directory(fhdhrhub.config.dict["filedir"]["www_dir"],
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

    @app.route('/device.xml', methods=['GET'])
    def device_xml():
        base_url = request.headers["host"]
        device_xml = fhdhrhub.get_device_xml(base_url)
        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')

    @app.route('/discover.json', methods=['GET'])
    def discover_json():
        base_url = request.headers["host"]
        discover_json = fhdhrhub.get_discover_json(base_url)
        return Response(status=200,
                        response=discover_json,
                        mimetype='application/json')

    @app.route('/lineup_status.json', methods=['GET'])
    def lineup_status_json():
        linup_status_json = fhdhrhub.get_lineup_status_json()
        return Response(status=200,
                        response=linup_status_json,
                        mimetype='application/json')

    @app.route('/lineup.xml', methods=['GET'])
    def lineup_xml():
        base_url = request.headers["host"]
        lineupxml = fhdhrhub.get_lineup_xml(base_url)
        return Response(status=200,
                        response=lineupxml,
                        mimetype='application/xml')

    @app.route('/lineup.json', methods=['GET'])
    def lineup_json():
        base_url = request.headers["host"]
        station_list = fhdhrhub.get_lineup_json(base_url)
        return Response(status=200,
                        response=station_list,
                        mimetype='application/json')

    @app.route('/xmltv.xml', methods=['GET'])
    def xmltv_xml():
        base_url = request.headers["host"]
        xmltv = fhdhrhub.get_xmltv(base_url)
        return Response(status=200,
                        response=xmltv,
                        mimetype='application/xml')

    @app.route('/api/xmltv')
    def api_xmltv():
        DeviceAuth = request.args.get('DeviceAuth', default=None, type=str)
        if DeviceAuth == fhdhrhub.config.dict["dev"]["device_auth"]:
            base_url = request.headers["host"]
            xmltv = fhdhrhub.get_xmltv(base_url)
            return Response(status=200,
                            response=xmltv,
                            mimetype='application/xml')
        return "not subscribed"

    @app.route('/diagnostics', methods=['GET'])
    def debug_html():
        base_url = request.headers["host"]
        return fhdhrhub.get_diagnostics_html(base_url)

    @app.route('/version', methods=['GET'])
    def version_html():
        base_url = request.headers["host"]
        return fhdhrhub.get_version_html(base_url)

    @app.route('/debug.json', methods=['GET'])
    def debug_json():
        base_url = request.headers["host"]
        debugreport = fhdhrhub.get_debug_json(base_url)
        return Response(status=200,
                        response=debugreport,
                        mimetype='application/json')

    @app.route('/api/channels.m3u', methods=['GET'])
    @app.route('/channels.m3u', methods=['GET'])
    def channels_m3u():
        base_url = request.headers["host"]
        channels_m3u = fhdhrhub.get_channels_m3u(base_url)
        return Response(status=200,
                        response=channels_m3u,
                        mimetype='text/plain')

    @app.route('/<channel>.m3u', methods=['GET'])
    def channel_m3u(channel):
        base_url = request.headers["host"]
        channel_m3u = fhdhrhub.get_channel_m3u(base_url, channel)
        return Response(status=200,
                        response=channel_m3u,
                        mimetype='text/plain')

    @app.route('/images', methods=['GET'])
    def images():
        image, imagetype = fhdhrhub.get_image(request.args)
        return Response(image, content_type=imagetype, direct_passthrough=True)

    @app.route('/auto/<channel>')
    def auto(channel):
        base_url = request.headers["host"]
        stream_args = {
                        "channel": channel.replace('v', ''),
                        "method": request.args.get('method', default=fhdhrhub.config.dict["fhdhr"]["stream_type"], type=str),
                        "duration": request.args.get('duration', default=0, type=int),
                        "accessed": fhdhrhub.device.channels.get_fhdhr_stream_url(base_url, channel.replace('v', '')),
                        }
        stream_args = fhdhrhub.get_stream_info(stream_args)
        if stream_args["channelUri"]:
            if stream_args["method"] == "direct":
                return Response(fhdhrhub.get_stream(stream_args), content_type=stream_args["content_type"], direct_passthrough=True)
            elif stream_args["method"] == "ffmpeg":
                return Response(stream_with_context(fhdhrhub.get_stream(stream_args)), mimetype="video/mpeg")
        abort(503)

    @app.route('/chanscan', methods=['GET'])
    def chanscan():
        fhdhrhub.post_lineup_scan_start()
        linup_status_json = fhdhrhub.get_lineup_status_json()
        return Response(status=200,
                        response=linup_status_json,
                        mimetype='application/json')

    @app.route('/lineup.post', methods=['POST'])
    def lineup_post():
        if 'scan' in list(request.args.keys()):
            if request.args['scan'] == 'start':
                fhdhrhub.post_lineup_scan_start()
                return Response(status=200, mimetype='text/html')
            elif request.args['scan'] == 'abort':
                return Response(status=200, mimetype='text/html')
            else:
                print("Unknown scan command " + request.args['scan'])
                currenthtmlerror = fhdhrhub.get_html_error("501 - " + request.args['scan'] + " is not a valid scan command")
                return Response(status=200, response=currenthtmlerror, mimetype='text/html')
        else:
            currenthtmlerror = fhdhrhub.get_html_error("501 - not a valid command")
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


def interface_start(settings, origin):
    print("Starting fHDHR Web Interface")
    fhdhrhub.setup(settings, origin)
    fakhdhrserver = HDHR_HTTP_Server(settings)
    fakhdhrserver.run()
