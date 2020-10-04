import os
import sys
import time
from io import BytesIO
import xml.etree.ElementTree as ET

from . import epgtypes


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
        self.config = config.copy()
        self.epgtypes = epgtypes.EPGTypes(config, serviceproxy)

    def get_xmltv(self, base_url):
        epgdict = self.epgtypes.get_epg()
        if not epgdict:
            return self.dummyxml()

        epg_method = self.config["fakehdhr"]["epg_method"]

        out = ET.Element('tv')
        out.set('source-info-url', self.config["fakehdhr"]["friendlyname"])
        out.set('source-info-name', self.config["main"]["servicename"])
        out.set('generator-info-name', 'FAKEHDHR')
        out.set('generator-info-url', 'FAKEHDHR/' + self.config["main"]["reponame"])

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
                channel_thumbnail = self.epgtypes.thumb_url(epg_method, "channel", base_url, str(epgdict[c]['thumbnail']))
                sub_el(c_out, 'icon', src=(str(channel_thumbnail)))
            else:
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + "/images?source=empty&type=channel&id=" + c['number']))

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
                    content_thumbnail = self.epgtypes.thumb_url(epg_method, "content", base_url, str(epgdict[c]['thumbnail']))
                    sub_el(prog_out, 'icon', src=(str(content_thumbnail)))
                else:
                    sub_el(prog_out, 'icon', src=("http://" + str(base_url) + "/images?source=empty&type=content&id=" + program['title']))

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
        out.set('source-info-url', self.config["fakehdhr"]["friendlyname"])
        out.set('source-info-name', self.config["main"]["servicename"])
        out.set('generator-info-name', 'FAKEHDHR')
        out.set('generator-info-url', 'FAKEHDHR/' + self.config["main"]["reponame"])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(ET.tostring(out, encoding='UTF-8'))
        return fakefile.getvalue()


def epgServerProcess(config, epghandling):

    sleeptime = int(config[config["fakehdhr"]["epg_method"]]["epg_update_frequency"])

    try:

        while True:
            epghandling.epgtypes.update()
            time.sleep(sleeptime)

    except KeyboardInterrupt:
        clean_exit()
