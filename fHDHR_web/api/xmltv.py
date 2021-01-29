from flask import Response, request, redirect, session
import xml.etree.ElementTree
from io import BytesIO
import urllib.parse
import datetime

from fHDHR.tools import sub_el


class xmlTV():
    """Methods to create xmltv.xml"""
    endpoints = ["/api/xmltv", "/xmltv.xml"]
    endpoint_name = "api_xmltv"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.xmltv_offset = {}
        for epg_method in list(self.fhdhr.device.epg.epg_handling.keys()):
            if epg_method in list(self.fhdhr.config.dict.keys()):
                if "xmltv_offset" in list(self.fhdhr.config.dict[epg_method].keys()):
                    self.xmltv_offset[epg_method] = self.fhdhr.config.dict[epg_method]["xmltv_offset"]
            if epg_method not in list(self.xmltv_offset.keys()):
                self.xmltv_offset[epg_method] = self.fhdhr.config.dict["epg"]["xmltv_offset"]

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if self.fhdhr.config.dict["fhdhr"]["require_auth"]:
            if session["deviceauth"] != self.fhdhr.config.dict["fhdhr"]["device_auth"]:
                return "not subscribed"

        base_url = request.url_root[:-1]

        method = request.args.get('method', default="get", type=str)

        source = request.args.get('source', default=self.fhdhr.config.dict["epg"]["def_method"], type=str)
        if source not in list(self.fhdhr.config.dict["epg"]["valid_methods"].keys()):
            return "%s Invalid xmltv method" % source

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            epgdict = self.fhdhr.device.epg.get_epg(source)

            if source in self.fhdhr.origins.valid_origins:
                epgdict = epgdict.copy()
                for c in list(epgdict.keys()):
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("origin_id", epgdict[c]["id"], source)
                    epgdict[chan_obj.number] = epgdict.pop(c)
                    epgdict[chan_obj.number]["name"] = chan_obj.dict["name"]
                    epgdict[chan_obj.number]["callsign"] = chan_obj.dict["callsign"]
                    epgdict[chan_obj.number]["number"] = chan_obj.number
                    epgdict[chan_obj.number]["id"] = chan_obj.dict["origin_id"]
                    epgdict[chan_obj.number]["thumbnail"] = chan_obj.thumbnail

            xmltv_xml = self.create_xmltv(base_url, epgdict, source)

            return Response(status=200,
                            response=xmltv_xml,
                            mimetype='application/xml')

        elif method == "update":
            self.fhdhr.device.epg.update(source)

        elif method == "clearcache":
            self.fhdhr.device.epg.clear_epg_cache(source)

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method

    def xmltv_headers(self):
        """This method creates the XML headers for our xmltv"""
        xmltvgen = xml.etree.ElementTree.Element('tv')
        xmltvgen.set('source-info-url', self.fhdhr.config.dict["fhdhr"]["friendlyname"])
        xmltvgen.set('source-info-name', self.fhdhr.config.dict["main"]["servicename"])
        xmltvgen.set('generator-info-name', 'fHDHR')
        xmltvgen.set('generator-info-url', 'fHDHR/%s' % self.fhdhr.config.dict["main"]["reponame"])
        return xmltvgen

    def xmltv_file(self, xmltvgen):
        """This method is used to close out the xml file"""
        xmltvfile = BytesIO()
        xmltvfile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        xmltvfile.write(xml.etree.ElementTree.tostring(xmltvgen, encoding='UTF-8'))
        return xmltvfile.getvalue()

    def xmltv_empty(self):
        """This method is called when creation of a full xmltv is not possible"""
        return self.xmltv_file(self.xmltv_headers())

    def timestamp_to_datetime(self, time_start, time_end, source):
        xmltvtimetamps = {}
        source_offset = self.xmltv_offset[source]
        for time_item, time_value in zip(["time_start", "time_end"], [time_start, time_end]):
            timestampval = datetime.datetime.fromtimestamp(time_value).strftime('%Y%m%d%H%M%S')
            xmltvtimetamps[time_item] = "%s %s" % (timestampval, source_offset)
        return xmltvtimetamps

    def create_xmltv(self, base_url, epgdict, source):
        if not epgdict:
            return self.xmltv_empty()
        epgdict = epgdict.copy()

        out = self.xmltv_headers()

        if source in self.fhdhr.origins.valid_origins:
            for c in list(epgdict.keys()):
                chan_obj = self.fhdhr.device.channels.get_channel_obj("origin_id", epgdict[c]["id"], source)
                epgdict[chan_obj.number] = epgdict.pop(c)
                epgdict[chan_obj.number]["name"] = chan_obj.dict["name"]
                epgdict[chan_obj.number]["callsign"] = chan_obj.dict["callsign"]
                epgdict[chan_obj.number]["number"] = chan_obj.number
                epgdict[chan_obj.number]["id"] = chan_obj.dict["origin_id"]
                epgdict[chan_obj.number]["thumbnail"] = chan_obj.thumbnail

        for c in list(epgdict.keys()):

            c_out = sub_el(out, 'channel', id=str(epgdict[c]['number']))
            sub_el(c_out, 'display-name',
                   text='%s %s' % (epgdict[c]['number'], epgdict[c]['callsign']))
            sub_el(c_out, 'display-name',
                   text='%s %s %s' % (epgdict[c]['number'], epgdict[c]['callsign'], str(epgdict[c]['id'])))
            sub_el(c_out, 'display-name', text=epgdict[c]['number'])
            sub_el(c_out, 'display-name', text=epgdict[c]['callsign'])
            sub_el(c_out, 'display-name', text=epgdict[c]['name'])

            if self.fhdhr.config.dict["epg"]["images"] == "proxy":
                sub_el(c_out, 'icon', src=("%s/api/images?method=get&type=channel&id=%s" % (base_url, epgdict[c]['id'])))
            else:
                sub_el(c_out, 'icon', src=(epgdict[c]["thumbnail"]))

        for channelnum in list(epgdict.keys()):

            channel_listing = epgdict[channelnum]['listing']

            for program in channel_listing:

                xmltvtimetamps = self.timestamp_to_datetime(program['time_start'], program['time_end'], source)

                prog_out = sub_el(out, 'programme',
                                       start=xmltvtimetamps['time_start'],
                                       stop=xmltvtimetamps['time_end'],
                                       channel=str(channelnum))

                sub_el(prog_out, 'title', lang='en', text=program['title'])

                sub_el(prog_out, 'desc', lang='en', text=program['description'])

                sub_el(prog_out, 'sub-title', lang='en', text='Movie: %s' % program['sub-title'])

                sub_el(prog_out, 'length', units='minutes', text=str(int(program['duration_minutes'])))

                for f in program['genres']:
                    sub_el(prog_out, 'category', lang='en', text=f)
                    sub_el(prog_out, 'genre', lang='en', text=f)

                if program['seasonnumber'] and program['episodenumber']:
                    s_ = int(str(program['seasonnumber']), 10)
                    e_ = int(str(program['episodenumber']), 10)
                    sub_el(prog_out, 'episode-num', system='dd_progid',
                           text=str(program['id']))
                    sub_el(prog_out, 'episode-num', system='common',
                           text='S%02dE%02d' % (s_, e_))
                    sub_el(prog_out, 'episode-num', system='xmltv_ns',
                           text='%d.%d.' % (int(s_)-1, int(e_)-1))
                    sub_el(prog_out, 'episode-num', system='SxxExx">S',
                           text='S%02dE%02d' % (s_, e_))

                if program["thumbnail"]:
                    if self.fhdhr.config.dict["epg"]["images"] == "proxy":
                        sub_el(prog_out, 'icon', src=("%s/api/images?method=get&type=content&id=%s" % (base_url, program['id'])))
                    else:
                        sub_el(prog_out, 'icon', src=(program["thumbnail"]))
                else:
                    sub_el(prog_out, 'icon', src=("%s/api/images?method=generate&type=content&message=%s" % (base_url, urllib.parse.quote(program['title']))))

                if program['rating']:
                    rating_out = sub_el(prog_out, 'rating', system="MPAA")
                    sub_el(rating_out, 'value', text=program['rating'])

                if program['isnew']:
                    sub_el(prog_out, 'new')

        return self.xmltv_file(out)
