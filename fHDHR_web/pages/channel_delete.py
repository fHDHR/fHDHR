from flask import request, render_template, session


class Channel_Delete_HTML():
    endpoints = ["/channel_delete", "/channel_delete.html"]
    endpoint_name = "page_channel_delete_html"
    endpoint_access_level = 99
    pretty_name = "Channel Delete"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        origin = request.args.get('origin', default=None, type=str)
        fhdhr_id = request.args.get('fhdhr_id', default=None, type=str)

        return render_template('channel_delete.html', request=request, session=session, fhdhr=self.fhdhr, fhdhr_id=fhdhr_id, origin=origin)
