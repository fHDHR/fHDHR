from flask import request, Response, abort


class Images():
    endpoints = ["/api/images"]
    endpoint_name = "api_images"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "generate",
                                    "type": "content",
                                    "message": "Internal Image Handling"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        image = None

        method = request.args.get('method', default="get", type=str)

        if method == "generate":
            image_type = request.args.get('type', default="content", type=str)
            if image_type in ["content", "channel"]:
                message = request.args.get('message', default="Unknown Request", type=str)
                image = self.fhdhr.device.images.generate_image(image_type, message)

        elif method == "get":
            source = request.args.get('source', default=self.fhdhr.config.dict["epg"]["method"], type=str)
            if source in self.fhdhr.config.dict["epg"]["valid_methods"]:
                image_type = request.args.get('type', default="content", type=str)
                if image_type in ["content", "channel"]:
                    image_id = request.args.get('id', default=None, type=str)
                    if image_id:
                        image = self.fhdhr.device.images.get_epg_image(image_type, image_id)

        else:
            image = self.fhdhr.device.images.generate_image("content", "Unknown Request")

        if image:
            imagemimetype = self.fhdhr.device.images.get_image_type(image)
            return Response(image, content_type=imagemimetype, direct_passthrough=True)

        else:
            return abort(501, "Not a valid image request")
