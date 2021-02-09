from flask import request, render_template, session


class Playlists_HTML():
    endpoints = ["/playlists", "/playlists.html"]
    endpoint_name = "page_playlists_html"
    endpoint_access_level = 1
    endpoint_category = "pages"
    pretty_name = "M3U/W3U"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        return render_template('playlists.html', request=request, session=session, fhdhr=self.fhdhr, list=list)
