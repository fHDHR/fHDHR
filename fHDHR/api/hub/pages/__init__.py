# pylama:ignore=W0611
from io import StringIO

from .htmlerror import HTMLerror
from .index_html import Index_HTML
from .origin_html import Origin_HTML
from .cluster_html import Cluster_HTML
from .diagnostics_html import Diagnostics_HTML
from .streams_html import Streams_HTML
from .version_html import Version_HTML
from .channel_guide_html import Channel_Guide_HTML


class fHDHR_Page_Elements():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get(self):
        return {"top": self.pagetop(), "end": self.pageend()}

    def pagetop(self):
        friendlyname = self.config.dict["fhdhr"]["friendlyname"]
        servicename = str(self.config.dict["main"]["servicename"])

        upper_part = [
                "<!DOCTYPE html>",
                "<html>",

                "<head>",
                "<title>%s</title>" % friendlyname,
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
                "<style>",
                "table, th, td {",
                "border: 1px solid black;",
                "}",
                "</style>",
                "<link href=\"style.css\" rel=\"stylesheet\">",
                "</head>",
                "<h1 id=\"mcetoc_1cdobsl3g0\" style=\"text-align: center;\"><span style=\"text-decoration: underline;\"><strong><em>%s</em></strong></span></h1><br>" % friendlyname,
                "",
                "<h2>"
                "<div>",

                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/", "fHDHR"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/origin", servicename),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/guide", "Guide"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/version", "Version"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/diagnostics", "Diagnostics"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/cluster", "Cluster"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/streams", "Streams"),

                "<a class=\"pull-right\" style=\"padding: 5px;\" href=\"%s\">%s</a>" % ("xmltv.xml", "xmltv"),
                "<a class=\"pull-right\" style=\"padding: 5px;\" href=\"%s\">%s</a>" % ("channels.m3u", "m3u"),

                "</div>",
                "<hr align=\"center\" width=\"100%\">"
                ]
        fhdhr_list = self.device.cluster.cluster
        locations = []
        for location in list(fhdhr_list.keys()):
            item_dict = {
                        "base_url": fhdhr_list[location]["base_url"],
                        "name": fhdhr_list[location]["name"]
                        }
            if item_dict["name"] != friendlyname:
                locations.append(item_dict)
        if len(locations):
            upper_part.append("<div>")
            locations = sorted(locations, key=lambda i: i['name'])
            for location in locations:
                upper_part.append("<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % (location["base_url"], location["name"]))
            upper_part.append("</div>")
            upper_part.append("<hr align=\"center\" width=\"100%\">")

        return upper_part

    def pageend(self):
        return [
            "</html>",
            "",

            "<script>",
            "function OpenLink(NewURL) {",
            "    window.open(NewURL, \"_self\");",
            "}",
            "</script>"
            ]


class fHDHR_Pages():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

        self.page_elements = fHDHR_Page_Elements(settings, device)

        self.htmlerror = HTMLerror(settings)

        self.index = Index_HTML(settings, self.device, self.page_elements)
        self.origin = Origin_HTML(settings, self.device, self.page_elements)
        self.cluster = Cluster_HTML(settings, self.device, self.page_elements)
        self.diagnostics = Diagnostics_HTML(settings, self.device, self.page_elements)
        self.version = Version_HTML(settings, self.device, self.page_elements)
        self.channel_guide = Channel_Guide_HTML(settings, self.device, self.page_elements)
        self.streams = Streams_HTML(settings, self.device, self.page_elements)
