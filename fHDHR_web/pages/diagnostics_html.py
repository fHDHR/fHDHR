from flask import request, render_template, session


class Diagnostics_HTML():
    endpoints = ["/diagnostics", "/diagnostics.html"]
    endpoint_name = "page_diagnostics_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        button_list = []

        button_list.append({
                            "label": "Debug Json",
                            "hdhr": None,
                            "rmg": None,
                            "other": "/api/debug",
                            })

        button_list.append({
                            "label": "Cluster Json",
                            "hdhr": None,
                            "rmg": None,
                            "other": "/api/cluster?method=get",
                            })

        button_list.append({
                            "label": "Lineup XML",
                            "hdhr": "/lineup.xml",
                            "rmg": None,
                            "other": None,
                            })

        button_list.append({
                            "label": "Lineup JSON",
                            "hdhr": "/hdhr/lineup.json",
                            "rmg": None,
                            "other": None,
                            })

        button_list.append({
                            "label": "Lineup Status",
                            "hdhr": "/hdhr/lineup_status.json",
                            "rmg": None,
                            "other": None,
                            })

        button_list.append({
                            "label": "Discover Json",
                            "hdhr": "/hdhr/discover.json",
                            "rmg": None,
                            "other": None,
                            })

        button_list.append({
                            "label": "Device XML",
                            "hdhr": "/hdhr/device.xml",
                            "rmg": "/rmg/device.xml",
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Identification XML",
                            "hdhr": "",
                            "rmg": "/rmg",
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Devices Discover",
                            "hdhr": "",
                            "rmg": "/rmg/devices/discover",
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Devices Probe",
                            "hdhr": "",
                            "rmg": "/rmg/devices/probe?uri=%s" % base_url,
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Devices by DeviceKey",
                            "hdhr": "",
                            "rmg": "/rmg/devices/%s" % self.fhdhr.config.dict["main"]["uuid"],
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Channels by DeviceKey",
                            "hdhr": "",
                            "rmg": "/rmg/devices/%s/channels" % self.fhdhr.config.dict["main"]["uuid"],
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Scanners by DeviceKey",
                            "hdhr": "",
                            "rmg": "/rmg/devices/%s/scanners" % self.fhdhr.config.dict["main"]["uuid"],
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Networks by DeviceKey",
                            "hdhr": "",
                            "rmg": "/rmg/devices/%s/networks" % self.fhdhr.config.dict["main"]["uuid"],
                            "other": None,
                            })

        button_list.append({
                            "label": "RMG Scan by DeviceKey",
                            "hdhr": "",
                            "rmg": "/rmg/devices/%s/scan" % self.fhdhr.config.dict["main"]["uuid"],
                            "other": None,
                            })

        return render_template('diagnostics.html', session=session, request=request, fhdhr=self.fhdhr, button_list=button_list)
