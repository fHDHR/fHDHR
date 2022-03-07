from flask import request, Response

import json

from fHDHR.tools import checkattr


def tabbed_json_response(json_item):
    json_dumped = json.dumps(json_item, indent=4)
    json_response = Response(status=200,
                             response=json_dumped,
                             mimetype='application/json')
    return json_response


def api_sub_handler(self, *args):

    parameters = {}

    if checkattr(self, "endpoint_parameters"):

        for parameter in list(self.endpoint_parameters.keys()):

            if "default" in list(self.endpoint_parameters[parameter].keys()):
                parameter_default = self.endpoint_parameters[parameter]["default"]
            else:
                parameter_default = None

            parameter_requested = request.args.get(parameter,
                                                   default=parameter_default,
                                                   type=str)

            if "required" in list(self.endpoint_parameters[parameter].keys()):
                parameter_required = self.endpoint_parameters[parameter]["required"]
            else:
                parameter_required = False

            if "valid_options" in list(self.endpoint_parameters[parameter].keys()):
                parameter_valid_options = self.endpoint_parameters[parameter]["valid_options"]
            else:
                parameter_valid_options = []

            if parameter_valid_options == "origins":
                parameter_valid_options = self.fhdhr.origins.list_origins

            if isinstance(parameter_valid_options, str):
                parameter_valid_options = [parameter_valid_options]

            if parameter_required and not parameter_requested:

                return tabbed_json_response({
                                            "Missing required parameter": parameter,
                                            "Valid %s options" % parameter: ", ".join(parameter_valid_options)
                                            })

            if len(parameter_valid_options):

                if parameter_requested and parameter_requested not in parameter_valid_options:

                    return tabbed_json_response({
                                                 "Invalid %s" % parameter: parameter_requested,
                                                 "Valid %s options" % parameter: ", ".join(parameter_valid_options)
                                                 })

            parameters[parameter] = parameter_requested

    return self.handler(parameters, *args)
