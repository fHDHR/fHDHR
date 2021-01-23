import os
import sys
import pathlib

plugins_top_dir = os.path.dirname(__file__)
print("Importing Plugins Prior to Script Run.")
plugin_dict = {}
for entry in os.scandir(plugins_top_dir):
    if entry.is_dir() and not entry.is_file() and entry.name[0] != '_':

        curr_dict = {}
        plugin_use = True

        # Import
        imp_string = "from .%s import *" % entry.name
        exec(imp_string)

        for plugin_item in ["NAME", "VERSION", "TYPE"]:
            plugin_item_eval_string = "%s.PLUGIN_%s" % (entry.name, plugin_item)
            try:
                curr_dict[plugin_item] = eval(plugin_item_eval_string)
            except AttributeError:
                curr_dict[plugin_item] = None

        if curr_dict["TYPE"] == "origin":
            curr_dict["PATH"] = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).joinpath(entry.name).joinpath('origin')
        elif curr_dict["TYPE"] in ["alt_epg", "alt_stream"]:
            curr_dict["PATH"] = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).joinpath(entry.name)

        plugin_import_print_string = "Found %s type plugin: %s %s. " % (curr_dict["TYPE"], curr_dict["NAME"], curr_dict["VERSION"])
        if not any(curr_dict[plugin_item] for plugin_item in ["NAME", "VERSION", "TYPE"]):
            plugin_import_print_string += " ImportWarning: Missing PLUGIN_* Value."
            plugin_use = False

        elif curr_dict["TYPE"] not in ["origin", "alt_epg", "alt_stream"]:
            plugin_use = False
            plugin_import_print_string += " ImportWarning: Invalid PLUGIN_TYPE."

        # Only allow a single origin
        elif curr_dict["TYPE"] == "origin" and len([x for x in list(plugin_dict.keys()) if plugin_dict[x]["TYPE"] == "origin"]):
            plugin_use = False
            plugin_import_print_string += " ImportWarning: Only one Origin Allowed."

        if plugin_use:
            plugin_import_print_string += " Import Success"

        # add to plugin_dict
        print(plugin_import_print_string)
        if plugin_use and entry.name not in plugin_dict:
            plugin_dict[entry.name] = curr_dict

            # Import Origin
            if curr_dict["TYPE"] == "origin":
                imp_string = "from .%s import origin" % entry.name
                exec(imp_string)
                imp_string = "from .%s import %s_Setup" % (entry.name, curr_dict["NAME"].upper())
                try:
                    exec(imp_string)
                except ImportError:
                    pass
            elif curr_dict["TYPE"] == "alt_epg":
                imp_string = "from .%s import *" % entry.name
                exec(imp_string)
            elif curr_dict["TYPE"] == "alt_stream":
                imp_string = "from .%s import *" % entry.name
                exec(imp_string)

if not len([x for x in list(plugin_dict.keys()) if plugin_dict[x]["TYPE"] == "origin"]):
    print("No Origin Plugin found.")
    sys.exit(1)
