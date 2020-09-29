from gevent.pywsgi import WSGIServer
from flask import (Flask, send_from_directory, request, Response,
                   abort, stream_with_context)
from io import BytesIO
import xml.etree.ElementTree as ET
import json
import time
import requests
import subprocess
import errno
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont


def sub_el(parent, name, text=None, **kwargs):
    el = ET.SubElement(parent, name, **kwargs)
    if text:
        el.text = text
    return el


def getSize(txt, font):
    testImg = PIL.Image.new('RGB', (1, 1))
    testDraw = PIL.ImageDraw.Draw(testImg)
    return testDraw.textsize(txt, font)


class HDHR_Hub():
    config = None
    serviceproxy = None
    epghandling = None
    station_scan = False
    station_list = []

    def __init__(self):
        self.station_scan = False

    def get_xmltv(self, base_url):
        return self.epghandling.get_xmltv(base_url)

    def get_image(self, req_args):
        imageid = req_args["id"]

        if req_args["source"] == "proxy":
            if req_args["type"] == "channel":
                imageUri = self.serviceproxy.get_channel_thumbnail(imageid)
            elif req_args["type"] == "content":
                imageUri = self.serviceproxy.get_content_thumbnail(imageid)
            req = requests.get(imageUri)
            return req.content

        elif req_args["source"] == "empty":
            if req_args["type"] == "channel":
                width = 360
                height = 270
                text = req_args["id"]
                fontsize = 72
            elif req_args["type"] == "content":
                width = 1080
                height = 1440
                fontsize = 100
                text = req_args["id"]

            colorBackground = "#228822"
            colorText = "#717D7E"
            colorOutline = "#717D7E"
            fontname = str(self.config["fakehdhr"]["font"])

            font = PIL.ImageFont.truetype(fontname, fontsize)
            text_width, text_height = getSize(text, font)
            img = PIL.Image.new('RGBA', (width+4, height+4), colorBackground)
            d = PIL.ImageDraw.Draw(img)
            d.text(((width-text_width)/2, (height-text_height)/2), text, fill=colorText, font=font)
            d.rectangle((0, 0, width+3, height+3), outline=colorOutline)

            s = BytesIO()
            img.save(s, 'png')
            return s.getvalue()

    def get_xmldiscover(self, base_url):
        out = ET.Element('root')
        out.set('xmlns', "urn:schemas-upnp-org:device-1-0")

        sub_el(out, 'URLBase', "http://" + base_url)

        specVersion_out = sub_el(out, 'specVersion')
        sub_el(specVersion_out, 'major', "1")
        sub_el(specVersion_out, 'minor', "0")

        device_out = sub_el(out, 'device')
        sub_el(device_out, 'deviceType', "urn:schemas-upnp-org:device:MediaServer:1")
        sub_el(device_out, 'friendlyName', self.config["fakehdhr"]["friendlyname"])
        sub_el(device_out, 'manufacturer', "Silicondust")
        sub_el(device_out, 'modelName', self.config["dev"]["reporting_model"])
        sub_el(device_out, 'modelNumber', self.config["dev"]["reporting_model"])
        sub_el(device_out, 'serialNumber')
        sub_el(device_out, 'UDN', "uuid:" + self.config["main"]["uuid"])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(ET.tostring(out, encoding='UTF-8'))
        return fakefile.getvalue()

    def get_discover_json(self, base_url):
        jsondiscover = {
                            "FriendlyName": self.config["fakehdhr"]["friendlyname"],
                            "Manufacturer": "Silicondust",
                            "ModelNumber": self.config["dev"]["reporting_model"],
                            "FirmwareName": self.config["dev"]["reporting_firmware_name"],
                            "TunerCount": self.config["fakehdhr"]["tuner_count"],
                            "FirmwareVersion": self.config["dev"]["reporting_firmware_ver"],
                            "DeviceID": self.config["main"]["uuid"],
                            "DeviceAuth": "locastproxy",
                            "BaseURL": "http://" + base_url,
                            "LineupURL": "http://" + base_url + "/lineup.json"
                        }
        return jsondiscover

    def get_lineup_status(self):
        if self.station_scan:
            channel_count = self.serviceproxy.get_station_total()
            jsonlineup = {
                          "ScanInProgress": "true",
                          "Progress": 99,
                          "Found": channel_count
                          }
        else:
            jsonlineup = {
                          "ScanInProgress": "false",
                          "ScanPossible": "true",
                          "Source": self.config["dev"]["reporting_tuner_type"],
                          "SourceList": [self.config["dev"]["reporting_tuner_type"]],
                          }
        return jsonlineup

    def get_lineup_xml(self, base_url):
        out = ET.Element('Lineup')
        station_list = self.serviceproxy.get_station_list(base_url)
        for station_item in station_list:
            program_out = sub_el(out, 'Program')
            sub_el(program_out, 'GuideNumber', station_item['GuideNumber'])
            sub_el(program_out, 'GuideName', station_item['GuideName'])
            sub_el(program_out, 'URL', station_item['URL'])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(ET.tostring(out, encoding='UTF-8'))
        return fakefile.getvalue()

    def get_debug(self, base_url):
        debugjson = {
                    "base_url": base_url,
                    }
        return debugjson

    def get_html_error(self, message):
        htmlerror = """<html>
                        <head></head>
                        <body>
                            <h2>{}</h2>
                        </body>
                        </html>"""
        return htmlerror.format(message)

    def station_scan_change(self, enablement):
        self.station_scan = enablement


hdhr = HDHR_Hub()


class HDHR_HTTP_Server():
    app = Flask(__name__,)

    @app.route('/')
    def root_path():
        return hdhr.config["fakehdhr"]["friendlyname"]

    @app.route('/favicon.ico', methods=['GET'])
    def favicon():
        return send_from_directory(hdhr.config["main"]["www_dir"],
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

    @app.route('/device.xml', methods=['GET'])
    def device_xml():
        base_url = request.headers["host"]
        devicexml = hdhr.get_xmldiscover(base_url)
        return Response(status=200,
                        response=devicexml,
                        mimetype='application/xml')

    @app.route('/discover.json', methods=['GET'])
    def discover_json():
        base_url = request.headers["host"]
        jsondiscover = hdhr.get_discover_json(base_url)
        return Response(status=200,
                        response=json.dumps(jsondiscover, indent=4),
                        mimetype='application/json')

    @app.route('/lineup_status.json', methods=['GET'])
    def lineup_status_json():
        linup_status_json = hdhr.get_lineup_status()
        return Response(status=200,
                        response=json.dumps(linup_status_json, indent=4),
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
        station_list = hdhr.serviceproxy.get_station_list(base_url)
        return Response(status=200,
                        response=json.dumps(station_list, indent=4),
                        mimetype='application/json')

    @app.route('/xmltv.xml', methods=['GET'])
    def xmltv_xml():
        base_url = request.headers["host"]
        xmltv = hdhr.get_xmltv(base_url)
        return Response(status=200,
                        response=xmltv,
                        mimetype='application/xml')

    @app.route('/debug.json', methods=['GET'])
    def debug_json():
        base_url = request.headers["host"]
        debugreport = hdhr.get_debug(base_url)
        return Response(status=200,
                        response=json.dumps(debugreport, indent=4),
                        mimetype='application/json')

    @app.route('/images', methods=['GET'])
    def images_nothing():
        if ('source' not in list(request.args.keys()) or 'id' not in list(request.args.keys()) or 'type' not in list(request.args.keys())):
            abort(404)

        image = hdhr.get_image(request.args)
        return Response(image, content_type='image/png', direct_passthrough=True)

    @app.route('/watch', methods=['GET'])
    def watch_nothing():
        if 'method' in list(request.args.keys()):
            if 'channel' in list(request.args.keys()):

                station_list = hdhr.serviceproxy.get_channel_streams()
                channelUri = station_list[str(request.args["channel"])]
                if not channelUri:
                    abort(404)

                if request.args["method"] == "direct":
                    duration = request.args.get('duration', default=0, type=int)

                    if not duration == 0:
                        duration += time.time()

                    req = requests.get(channelUri, stream=True)

                    def generate():
                        yield ''
                        for chunk in req.iter_content(chunk_size=hdhr.config["direct_stream"]['chunksize']):
                            if not duration == 0 and not time.time() < duration:
                                req.close()
                                break
                            yield chunk

                    return Response(generate(), content_type=req.headers['content-type'], direct_passthrough=True)

                if request.args["method"] == "ffmpeg":

                    ffmpeg_command = [hdhr.config["ffmpeg"]["ffmpeg_path"],
                                      "-i", channelUri,
                                      "-c", "copy",
                                      "-f", "mpegts",
                                      "-nostats", "-hide_banner",
                                      "-loglevel", "warning",
                                      "pipe:stdout"
                                      ]
                    ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)

                    def generate():

                        videoData = ffmpeg_proc.stdout.read(int(hdhr.config["ffmpeg"]["bytes_per_read"]))

                        while True:
                            if not videoData:
                                break
                            else:
                                # from https://stackoverflow.com/questions/9932332
                                try:
                                    yield videoData
                                    time.sleep(0.1)
                                except IOError as e:
                                    # Check we hit a broken pipe when trying to write back to the client
                                    if e.errno == errno.EPIPE:
                                        # Send SIGTERM to shutdown ffmpeg
                                        ffmpeg_proc.terminate()
                                        # ffmpeg writes a bit of data out to stderr after it terminates,
                                        # need to read any hanging data to prevent a zombie process.
                                        ffmpeg_proc.communicate()
                                        break
                                    else:
                                        raise

                            videoData = ffmpeg_proc.stdout.read(int(hdhr.config["ffmpeg"]["bytes_per_read"]))

                    ffmpeg_proc.terminate()
                    try:
                        ffmpeg_proc.communicate()
                    except ValueError:
                        print("Connection Closed")

                    return Response(stream_with_context(generate()), mimetype="audio/mpeg")
        abort(404)

    @app.route('/lineup.post', methods=['POST'])
    def lineup_post():
        if 'scan' in list(request.args.keys()):
            if request.args['scan'] == 'start':
                hdhr.station_scan_change(True)
                hdhr.station_list = []
                hdhr.station_scan_change(False)
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

    def __init__(self, config):
        self.config = config.config

    def run(self):
        http = WSGIServer((
                            self.config["fakehdhr"]["address"],
                            int(self.config["fakehdhr"]["port"])
                            ), self.app.wsgi_app)
        http.serve_forever()


def interface_start(config, serviceproxy, epghandling):
    hdhr.config = config.config
    hdhr.station_scan = False
    hdhr.serviceproxy = serviceproxy
    hdhr.epghandling = epghandling
    fakhdhrserver = HDHR_HTTP_Server(config)
    fakhdhrserver.run()
