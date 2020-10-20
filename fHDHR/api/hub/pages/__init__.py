# pylama:ignore=W0611
from .index_html import Index_HTML
from .htmlerror import HTMLerror


class fHDHR_Pages():

    def __init__(self, settings):
        self.config = settings
        self.index = Index_HTML(settings)
        self.htmlerror = HTMLerror(settings)
