from flask import request, render_template, session


class Channel_Delete_HTML():
    endpoints = ["/channel_delete", "/channel_delete.html"]
    endpoint_name = "page_channel_delete_html"
    endpoint_access_level = 99
    pretty_name = "Channel Delete"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        origin_name = request.args.get('origin', default=None, type=str)
        fhdhr_channel_id = request.args.get('fhdhr_channel_id', default=None, type=str)

        return render_template('channel_delete.html', request=request, session=session, fhdhr=self.fhdhr, fhdhr_channel_id=fhdhr_channel_id, origin_name=origin_name)
