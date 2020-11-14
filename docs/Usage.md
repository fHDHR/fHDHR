<p align="center">fHDHR    <img src="images/logo.ico" alt="Logo"/></p>

---
[Main](README.md)  |  [Setup and Usage](Usage.md)  |  [Locast](Origin.md)  |  [Credits/Related Projects](Related-Projects.md)
---
**f**un
**H**ome
**D**istribution
**H**iatus
**R**ecreation

---

[Basic Configuration](Config.md)  | [Advanced Configuration](ADV_Config.md) |  [WebUI](WebUI.md)

---

# Author Notes

* All Testing is currently done in Proxmox LXC, Ubuntu 20.04, Python 3.8


# Prerequisites

* A Linux or Mac "Server". Windows currently does not work. A "Server" is a computer that is typically always online.
* Python 3.7 or later.
* Consult [This Page](Origin.md) for additional setup specific to this variant of fHDHR.


# Optional Prerequisites
* If you intend to use Docker, [This Guide](https://docs.docker.com/get-started/) should help you get started. The author of fHDHR is not a docker user, but will still try to help.

fHDHR uses direct connections with video sources by default. Alternatively, you can install and update the [config](Config.md) accordingly. You will need to make these available to your systems PATH, or manually set their path via the config file.

* ffmpeg
* vlc


# Installation

## Linux

* Download the zip, or git clone
* Navigate into your script directory and run `pip3 install -r requirements.txt`
* Copy the included `config.example.ini` file to a known location. The script will not run without this. There is no default configuration file location. [Modify the configuration file to suit your needs.](Config.md)

* Run with `python3 main.py -c=` and the path to the config file.


## Docker
TODO

# Setup

Now that you have fHDHR running, You can navigate (in a web browser) to the IP:Port from the configuration step above.

If you did not setup a `discovery_address` in your config, SSDP will be disabled. This is not a problem as clients like Plex can have the IP:Port entered manually!

You can copy the xmltv link from the webUI and use that in your client software to provide Channel Guide information.
