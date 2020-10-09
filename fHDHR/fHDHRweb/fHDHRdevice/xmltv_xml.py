import xml.etree.ElementTree
from io import BytesIO

from fHDHR.tools import sub_el


class xmlTV_XML():
    """Methods to create xmltv.xml"""
    xmltv_xml = None

    def __init__(self, settings, epghandling):
        self.config = settings
        self.epghandling = epghandling

    def get_xmltv_xml(self, base_url, force_update=False):

        epgdict = self.epghandling.epgtypes.get_epg()
        return self.create_xmltv(base_url, epgdict)

    def xmltv_headers(self):
        """This method creates the XML headers for our xmltv"""
        xmltvgen = xml.etree.ElementTree.Element('tv')
        xmltvgen.set('source-info-url', self.config.dict["fhdhr"]["friendlyname"])
        xmltvgen.set('source-info-name', self.config.dict["main"]["servicename"])
        xmltvgen.set('generator-info-name', 'fHDHR')
        xmltvgen.set('generator-info-url', 'fHDHR/' + self.config.dict["main"]["reponame"])
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

    def create_xmltv(self, base_url, epgdict):
        if not epgdict:
            return self.xmltv_empty()

        out = self.xmltv_headers()

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
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + "/images?source=epg&type=channel&id=" + str(epgdict[c]['id'])))
            else:
                sub_el(c_out, 'icon', src=("http://" + str(base_url) + "/images?source=generate&message=" + str(epgdict[c]['number'])))

        for channelnum in list(epgdict.keys()):

            channel_listing = epgdict[channelnum]['listing']

            for program in channel_listing:

                prog_out = sub_el(out, 'programme',
                                       start=program['time_start'],
                                       stop=program['time_end'],
                                       channel=str(channelnum))

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

                if program["thumbnail"]:
                    sub_el(prog_out, 'icon', src=("http://" + str(base_url) + "/images?source=epg&type=content&id=" + str(program['id'])))
                else:
                    sub_el(prog_out, 'icon', src=("http://" + str(base_url) + "/images?source=generate&message=" + program['title'].replace(" ", "")))

                if program['rating']:
                    rating_out = sub_el(prog_out, 'rating', system="MPAA")
                    sub_el(rating_out, 'value', text=program['rating'])

                if program['isnew']:
                    sub_el(prog_out, 'new')

        return self.xmltv_file(out)
