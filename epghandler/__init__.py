import os
import sys
import time
from io import BytesIO
import json
import xml.etree.ElementTree as ET

from . import zap2it
from . import emptyepg


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
        self.emptyepg = emptyepg.EmptyEPG(config)

        self.epg_cache = None

    def get_epg(self):
        if self.config["fakehdhr"]["epg_method"] == "empty":
            epgdict = self.emptyepg.EmptyEPG()
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

        for c in list(epgdict.keys()):

            c_out = sub_el(out, 'channel', id=str(epgdict[c]['number']))
            sub_el(c_out, 'display-name',
                          text='%s %s' % (epgdict[c]['number'], epgdict[c]['callsign']))
            sub_el(c_out, 'display-name',
                          text='%s %s %s' % (epgdict[c]['number'], epgdict[c]['callsign'], str(epgdict[c]['id'])))
            sub_el(c_out, 'display-name', text=epgdict[c]['number'])
            sub_el(c_out, 'display-name',
                          text='%s %s fcc' % (epgdict[c]['number'], epgdict[c]['callsign']))
            sub_el(c_out, 'display-name', text=epgdict[c]['callsign'])
            sub_el(c_out, 'display-name', text=epgdict[c]['callsign'])
            sub_el(c_out, 'display-name', text=epgdict[c]['name'])

            if epgdict[c]["thumbnail"] is not None:
                if epg_method == "empty":
                    sub_el(c_out, 'icon', src=("http://" + str(base_url) + str(epgdict[c]['thumbnail'])))
                elif epg_method == "proxy":
                    sub_el(c_out, 'icon', src=(str(epgdict[c]['thumbnail'])))
                elif epg_method == "zap2it":
                    sub_el(c_out, 'icon', src=(str(epgdict[c]['thumbnail'])))
                else:
                    sub_el(c_out, 'icon', src=(str(epgdict[c]['thumbnail'])))
            else:
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + "/images?source=empty&type=channel&id=empty"))

        for progitem in list(epgdict.keys()):

            channel_listing = epgdict[progitem]['listing']

            for program in channel_listing:

                prog_out = sub_el(out, 'programme',
                                  start=program['time_start'],
                                  stop=program['time_end'],
                                  channel=str(progitem))

                sub_el(prog_out, 'title', lang='en', text=program['title'])

                sub_el(prog_out, 'desc', lang='en', text=program['description'])

                sub_el(prog_out, 'sub-title', lang='en', text='Movie: ' + program['sub-title'])

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

                if program["thumbnail"] is not None:
                    if epg_method == "empty":
                        sub_el(prog_out, 'icon', src=("http://" + str(base_url) + str(program['thumbnail'])))
                    elif epg_method == "proxy":
                        sub_el(prog_out, 'icon', src=(str(program['thumbnail'])))
                    elif epg_method == "zap2it":
                        sub_el(prog_out, 'icon', src=(str(program['thumbnail'])))
                    else:
                        sub_el(prog_out, 'icon', src=(str(program['thumbnail'])))
                else:
                    sub_el(prog_out, 'icon', src=("http://" + str(base_url) + "/images?source=empty&type=content&id=empty"))

                if program['rating']:
                    rating_out = sub_el(prog_out, 'rating', system="MPAA")
                    sub_el(rating_out, 'value', text=program['rating'])

                if program['isnew']:
                    sub_el(prog_out, 'new')

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

    def update(self):
        if self.config["fakehdhr"]["epg_method"] == "empty":
            self.emptyepg.update_epg()
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
