

class fHDHR_Page_Elements():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr
        self.location = self.fhdhr.device.cluster.location

    def get(self, request):
        return {"top": self.pagetop(request), "end": self.pageend(request)}

    def pagetop(self, request):
        friendlyname = self.fhdhr.config.dict["fhdhr"]["friendlyname"]
        servicename = str(self.fhdhr.config.dict["main"]["servicename"])

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
                "<h1 style=\"text-align: center;\">",
                "<span style=\"text-decoration: underline;\"><strong><em>%s</em></strong>" % friendlyname,
                "</span>",
                "<img class=\"pull-left\" src=\"%s\" alt=\"%s\" width=\"100\" height=\"100\">\n" % ("/favicon.ico", "fHDHR Logo"),
                "</h1>"
                "<br><br>",
                "<h2>"
                "<div>",

                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/", "fHDHR"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/origin", servicename),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/guide", "Guide"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/cluster", "Cluster"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/streams", "Streams"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/xmltv", "xmltv"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/version", "Version"),
                "<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % ("/diagnostics", "Diagnostics"),

                "<a class=\"pull-right\" style=\"padding: 5px;\" href=\"%s\">%s</a>" % ("/api/xmltv?method=get&source=" + self.fhdhr.device.epg.def_method, "xmltv"),
                "<a class=\"pull-right\" style=\"padding: 5px;\" href=\"%s\">%s</a>" % ("/api/m3u?method=get&channel=all", "m3u"),

                "</div>",
                "<hr align=\"center\" width=\"100%\">"
                ]
        fhdhr_list = self.fhdhr.device.cluster.cluster()
        locations = []
        for location in list(fhdhr_list.keys()):
            item_dict = {
                        "base_url": fhdhr_list[location]["base_url"],
                        "name": fhdhr_list[location]["name"]
                        }
            if item_dict["base_url"] != self.location:
                locations.append(item_dict)
        if len(locations):
            upper_part.append("<div>")
            locations = sorted(locations, key=lambda i: i['name'])
            for location in locations:
                upper_part.append("<button class=\"pull-left\" onclick=\"OpenLink('%s')\">%s</a></button>" % (location["base_url"], location["name"]))
            upper_part.append("</div>")
            upper_part.append("<hr align=\"center\" width=\"100%\">")

        retmessage = request.args.get('retmessage', default=None, type=str)
        if retmessage:
            upper_part.append("<p>%s</p>" % retmessage)

        return upper_part

    def pageend(self, request):
        return [
            "</html>",
            "",

            "<script>",
            "function OpenLink(NewURL) {",
            "    window.open(NewURL, \"_self\");",
            "}",
            "</script>"
            ]
