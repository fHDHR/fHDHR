
class HTMLerror():
    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def get_html_error(self, message):
        htmlerror = """<html>
                        <head></head>
                        <body>
                            <h2>{}</h2>
                        </body>
                        </html>"""
        return htmlerror.format(message)
