from io import StringIO


class Index_HTML():

    def __init__(self, settings):
        self.config = settings
        self.index_html = None

    def get_index_html(self, base_url, force_update=False):
        if not self.index_html or force_update:

            friendlyname = self.config.dict["fhdhr"]["friendlyname"]

            fakefile = StringIO()

            fakefile.write("<!DOCTYPE html>\n")
            fakefile.write("<html>\n")

            fakefile.write("<head>\n")
            fakefile.write("<title>%s</title>\n" % friendlyname)
            fakefile.write("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n")
            fakefile.write("</head>\n")

            fakefile.write("<h2 id=\"mcetoc_1cdobsl3g0\" style=\"text-align: center;\"><span style=\"text-decoration: underline;\"><strong><em>%s</em></strong></span></h2>\n" % friendlyname)

            # a list of 2 part lists containing button information
            button_list = [
                            ["xmltv", "xmltv.xml"],
                            ["m3u", "channels.m3u"],
                            ["debug", "debug.json"]
                            ]

            for button_item in button_list:
                button_label = button_item[0]
                button_path = button_item[1]
                fakefile.write("<div style=\"text-align: center;\">\n")
                fakefile.write("  <p><button onclick=\"OpenLink('%s')\">%s</a></button></p>\n" % (button_path, button_label))
                fakefile.write("</div>\n")

            fakefile.write("</html>\n")
            fakefile.write("\n")

            fakefile.write("<script>\n")
            fakefile.write("function OpenLink(NewURL) {\n")
            fakefile.write("    window.open(NewURL, \"_self\");\n")
            fakefile.write("}\n")
            fakefile.write("</script>")

            self.index_html = fakefile.getvalue()

        return self.index_html
