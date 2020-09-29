import os
import sys
import time
import datetime
from io import BytesIO
import json
import xml.etree.ElementTree as ET

from . import zap2it


def sub_el(parent, name, text=None, **kwargs):
    el = ET.SubElement(parent, name, **kwargs)
    if text:
        el.text = text
    return el


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


class EPGhandler():

    def __init__(self, config, serviceproxy):
        self.config = config.config
        self.serviceproxy = serviceproxy
        self.zapepg = zap2it.ZapEPG(config)

        self.epg_cache = None

        self.empty_cache_dir = config.config["main"]["empty_cache"]
        self.empty_cache_file = config.config["main"]["empty_cache_file"]

    def get_epg(self):
        if self.config["fakehdhr"]["epg_method"] == "empty":
            epgdict = self.epg_cache_open()
        elif self.config["fakehdhr"]["epg_method"] == "proxy":
            epgdict = self.serviceproxy.epg_cache_open()
        elif self.config["fakehdhr"]["epg_method"] == "zap2it":
            epgdict = self.zapepg.epg_cache_open()
        return epgdict

    def epg_cache_open(self):
        epg_cache = None
        if os.path.isfile(self.empty_cache_file):
            with open(self.empty_cache_file, 'r') as epgfile:
                epg_cache = json.load(epgfile)
        return epg_cache

    def get_xmltv(self, base_url):
        epgdict = self.get_epg()
        if not epgdict:
            return self.dummyxml()

        epg_method = self.config["fakehdhr"]["epg_method"]

        out = ET.Element('tv')
        out.set('source-info-url', 'Locast')
        out.set('source-info-name', 'Locast')
        out.set('generator-info-name', 'FAKEHDHR')
        out.set('generator-info-url', 'FAKEHDHR/FakeHDHR_Locast')

        for channel in list(epgdict.keys()):
            c_out = sub_el(out, 'channel', id=epgdict[channel]['id'])
            sub_el(c_out, 'display-name',
                          text='%s %s' % (epgdict[channel]['number'], epgdict[channel]['callsign']))
            sub_el(c_out, 'display-name', text=epgdict[channel]['number'])
            sub_el(c_out, 'display-name', text=epgdict[channel]['callsign'])

            if epg_method == "empty":
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + str(epgdict[channel]['thumbnail'])))
            elif epg_method == "proxy":
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + str(epgdict[channel]['thumbnail'])))
            elif epg_method == "zap2it":
                sub_el(c_out, 'icon', src=(str(epgdict[channel]['thumbnail'])))
            else:
                sub_el(c_out, 'icon', src=(str(epgdict[channel]['thumbnail'])))

        for channel in list(epgdict.keys()):
            channel_listing = epgdict[channel]['listing']

            for program in channel_listing:

                prog_out = sub_el(out, 'programme',
                                  start=program['time_start'],
                                  stop=program['time_end'],
                                  channel=epgdict[channel]["id"])

                if program['title']:
                    sub_el(prog_out, 'title', lang='en', text=program['title'])

                if 'movie' in program['genres'] and program['releaseyear']:
                    sub_el(prog_out, 'sub-title', lang='en', text='Movie: ' + program['releaseyear'])
                elif program['episodetitle']:
                    sub_el(prog_out, 'sub-title', lang='en', text=program['episodetitle'])

                sub_el(prog_out, 'length', units='minutes', text=str(int(program['duration_minutes'])))

                for f in program['genres']:
                    sub_el(prog_out, 'category', lang='en', text=f)
                    sub_el(prog_out, 'genre', lang='en', text=f)

                if program["thumbnail"] is not None:
                    if epg_method == "empty":
                        sub_el(prog_out, 'icon', src=("http://" + str(base_url) + str(program['thumbnail'])))
                    elif epg_method == "proxy":
                        sub_el(prog_out, 'icon', src=("http://" + str(base_url) + str(program['thumbnail'])))
                    elif epg_method == "zap2it":
                        sub_el(prog_out, 'icon', src=(str(program['thumbnail'])))
                    else:
                        sub_el(prog_out, 'icon', src=(str(program['thumbnail'])))

                if program['rating']:
                    r = ET.SubElement(prog_out, 'rating')
                    sub_el(r, 'value', text=program['rating'])

                if 'seasonnumber' in list(program.keys()) and 'episodenumber' in list(program.keys()):
                    if program['seasonnumber'] and program['episodenumber']:
                        s_ = int(program['seasonnumber'], 10)
                        e_ = int(program['episodenumber'], 10)
                        sub_el(prog_out, 'episode-num', system='common',
                               text='S%02dE%02d' % (s_, e_))
                        sub_el(prog_out, 'episode-num', system='xmltv_ns',
                               text='%d.%d.' % (int(s_)-1, int(e_)-1))
                        sub_el(prog_out, 'episode-num', system='SxxExx">S',
                               text='S%02dE%02d' % (s_, e_))

                # if 'New' in event['flag'] and 'live' not in event['flag']:
                #    sub_el(prog_out, 'new')

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(ET.tostring(out, encoding='UTF-8'))
        return fakefile.getvalue()

    def dummyxml(self):
        out = ET.Element('tv')
        out.set('source-info-url', 'Locast')
        out.set('source-info-name', 'Locast')
        out.set('generator-info-name', 'FAKEHDHR')
        out.set('generator-info-url', 'FAKEHDHR/FakeHDHR_Locast')

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(ET.tostring(out, encoding='UTF-8'))
        return fakefile.getvalue()

    def update_epg(self):
        print('Updating Empty EPG cache file.')

        programguide = {}

        timestamps = []
        todaydate = datetime.date.today()
        for x in range(0, 6):
            xdate = todaydate + datetime.timedelta(days=x)
            xtdate = xdate + datetime.timedelta(days=1)

            for hour in range(0, 24):
                time_start = datetime.datetime.combine(xdate, datetime.time(hour, 0))
                if hour + 1 < 24:
                    time_end = datetime.datetime.combine(xdate, datetime.time(hour + 1, 0))
                else:
                    time_end = datetime.datetime.combine(xtdate, datetime.time(0, 0))
                timestampdict = {
                                "time_start": str(time_start.strftime('%Y%m%d%H%M%S')) + " +0000",
                                "time_end": str(time_end.strftime('%Y%m%d%H%M%S')) + " +0000",
                                }
                timestamps.append(timestampdict)

        for c in self.serviceproxy.get_channels():
            if str(c["channel"]) not in list(programguide.keys()):
                programguide[str(c["channel"])] = {}

            channel_thumb_path = ("/images?source=empty&type=channel&id=%s" % (str(c['channel'])))
            programguide[str(c["channel"])]["thumbnail"] = channel_thumb_path

            if "name" not in list(programguide[str(c["channel"])].keys()):
                programguide[str(c["channel"])]["name"] = c["name"]

            if "callsign" not in list(programguide[str(c["channel"])].keys()):
                programguide[str(c["channel"])]["callsign"] = c["name"]

            if "id" not in list(programguide[str(c["channel"])].keys()):
                programguide[str(c["channel"])]["id"] = c["id"]

            if "number" not in list(programguide[str(c["channel"])].keys()):
                programguide[str(c["channel"])]["number"] = c["channel"]

            if "listing" not in list(programguide[str(c["channel"])].keys()):
                programguide[str(c["channel"])]["listing"] = []

            for timestamp in timestamps:
                clean_prog_dict = {}

                clean_prog_dict["time_start"] = timestamp['time_start']
                clean_prog_dict["time_end"] = timestamp['time_end']
                clean_prog_dict["duration_minutes"] = 60.0

                content_thumb = ("/images?source=empty&type=content&id=%s" % (str(c['channel'])))
                clean_prog_dict["thumbnail"] = content_thumb

                clean_prog_dict["title"] = "Unavailable"

                clean_prog_dict["genres"] = []

                clean_prog_dict["sub-title"] = "Unavailable"

                clean_prog_dict['releaseyear'] = ""
                clean_prog_dict["episodetitle"] = "Unavailable"

                clean_prog_dict["description"] = "Unavailable"

                clean_prog_dict['rating'] = "N/A"

                programguide[str(c["channel"])]["listing"].append(clean_prog_dict)

        self.epg_cache = programguide
        with open(self.empty_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated Empty EPG cache file.')
        return programguide

    def update(self):
        if self.config["fakehdhr"]["epg_method"] == "empty":
            self.update_epg()
        elif self.config["fakehdhr"]["epg_method"] == "proxy":
            self.serviceproxy.update_epg()
        elif self.config["fakehdhr"]["epg_method"] == "zap2it":
            self.zapepg.update_epg()


def epgServerProcess(config, epghandling):

    if config.config["fakehdhr"]["epg_method"] == "empty":
        sleeptime = config.config["main"]["empty_epg_update_frequency"]
    elif config.config["fakehdhr"]["epg_method"] == "proxy":
        sleeptime = config.config["locast"]["epg_update_frequency"]
    elif config.config["fakehdhr"]["epg_method"] == "zap2it":
        sleeptime = config.config["zap2xml"]["epg_update_frequency"]

    try:

        while True:
            epghandling.update()
            time.sleep(sleeptime)

    except KeyboardInterrupt:
        clean_exit()
