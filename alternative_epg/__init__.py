import os

alt_epg_top_dir = os.path.dirname(__file__)
for entry in os.scandir(alt_epg_top_dir):
    if entry.is_dir() and not entry.is_file() and entry.name[0] != '_':
        imp_string = "from .%s import *" % entry.name
        exec(imp_string)
