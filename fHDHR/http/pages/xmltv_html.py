from flask import request
from io import StringIO


class xmlTV_HTML():
    endpoints = ["/xmltv"]
    endpoint_name = "xmltv"

    def __init__(self, fhdhr, page_elements):
        self.fhdhr = fhdhr
        self.page_elements = page_elements

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        fakefile = StringIO()
        page_elements = self.page_elements.get(request)

        for line in page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">fHDHR xmltv Options</h4>")
        fakefile.write("\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th>Version</th>\n")
        fakefile.write("    <th>Link</th>\n")
        fakefile.write("    <th>Options</th>\n")
        fakefile.write("  </tr>\n")

        for epg_method in self.fhdhr.config.dict["main"]["valid_epg_methods"]:
            if epg_method not in [None, "None"]:
                epg_method_name = epg_method
                if epg_method == "origin":
                    epg_method_name = self.fhdhr.config.dict["main"]["dictpopname"]
                fakefile.write("  <tr>\n")
                fakefile.write("    <td>%s</td>\n" % (epg_method_name))
                fakefile.write("    <td><a href=\"%s\">%s</a>\n" % ("/api/xmltv?method=get&source=" + epg_method, epg_method_name))

                fakefile.write("    <td>\n")
                fakefile.write("        <div>\n")
                fakefile.write(
                    "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                    ("/api/xmltv?method=update&source=" + epg_method + "&redirect=%2Fxmltv", "Update"))
                fakefile.write("        </div>\n")
                fakefile.write("    </td>\n")

                fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
