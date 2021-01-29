

from .rmg_ident_xml import RMG_Ident_XML
from .device_xml import RMG_Device_XML
from .devices_discover import RMG_Devices_Discover
from .devices_probe import RMG_Devices_Probe
from .devices_devicekey import RMG_Devices_DeviceKey
from .devices_devicekey_channels import RMG_Devices_DeviceKey_Channels
from .devices_devicekey_scanners import RMG_Devices_DeviceKey_Scanners
from .devices_devicekey_networks import RMG_Devices_DeviceKey_Networks
from .devices_devicekey_scan import RMG_Devices_DeviceKey_Scan
from .devices_devicekey_prefs import RMG_Devices_DeviceKey_Prefs
from .devices_devicekey_media import RMG_Devices_DeviceKey_Media


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

        self.rmg_ident_xml = RMG_Ident_XML(fhdhr)
        self.device_xml = RMG_Device_XML(fhdhr)
        self.devices_discover = RMG_Devices_Discover(fhdhr)
        self.devices_probe = RMG_Devices_Probe(fhdhr)
        self.devices_devicekey = RMG_Devices_DeviceKey(fhdhr)
        self.devices_devicekey_channels = RMG_Devices_DeviceKey_Channels(fhdhr)
        self.devices_devicekey_scanners = RMG_Devices_DeviceKey_Scanners(fhdhr)
        self.devices_devicekey_networks = RMG_Devices_DeviceKey_Networks(fhdhr)
        self.devices_devicekey_scan = RMG_Devices_DeviceKey_Scan(fhdhr)
        self.devices_devicekey_prefs = RMG_Devices_DeviceKey_Prefs(fhdhr)
        self.devices_devicekey_media = RMG_Devices_DeviceKey_Media(fhdhr)
