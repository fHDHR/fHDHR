

from .index_html import Index_HTML
from .channels_html import Channels_HTML
from .guide_html import Guide_HTML
from .tuners_html import Tuners_HTML
from .xmltv_html import xmlTV_HTML
from .versions_html import Versions_HTML
from .diagnostics_html import Diagnostics_HTML
from .settings_html import Settings_HTML
from .channels_editor_html import Channels_Editor_HTML
from .channel_delete import Channel_Delete_HTML
from .playlists_html import Playlists_HTML
from .ssdp_html import SSDP_HTML


class fHDHR_Pages():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.index_html = Index_HTML(fhdhr)
        self.channels_html = Channels_HTML(fhdhr)
        self.channels_editor_html = Channels_Editor_HTML(fhdhr)
        self.channel_delete = Channel_Delete_HTML(fhdhr)
        self.guide_html = Guide_HTML(fhdhr)
        self.tuners_html = Tuners_HTML(fhdhr)
        self.xmltv_html = xmlTV_HTML(fhdhr)
        self.playlists_html = Playlists_HTML(fhdhr)
        self.versions_html = Versions_HTML(fhdhr)
        self.diagnostics_html = Diagnostics_HTML(fhdhr)
        self.settings_html = Settings_HTML(fhdhr)
        self.ssdp_html = SSDP_HTML(fhdhr)
