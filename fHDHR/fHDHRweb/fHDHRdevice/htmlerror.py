
class HTMLerror():
    def __init__(self, settings):
        self.config = settings

    def get_html_error(self, message):
        htmlerror = """<html>
                        <head></head>
                        <body>
                            <h2>{}</h2>
                        </body>
                        </html>"""
        return htmlerror.format(message)
