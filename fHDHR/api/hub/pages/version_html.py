from io import StringIO

from fHDHR import fHDHR_VERSION


class Version_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.page_elements = page_elements

    def get_version_html(self, base_url, force_update=False):

        fakefile = StringIO()

        for line in self.page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("  </tr>\n")

        fakefile.write("  <tr>\n")
        fakefile.write("    <td>%s</td>\n" % ("fHDHR"))
        fakefile.write("    <td>%s</td>\n" % (str(fHDHR_VERSION)))
        fakefile.write("  </tr>\n")

        for line in self.page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
