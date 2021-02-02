<p align="center">fHDHR    <img src="images/logo.ico" alt="Logo"/></p>

---
[Main](README.md)  |  [Setup and Usage](Usage.md)  |  [Plugins](Plugins.md)  |  [Credits/Related Projects](Related-Projects.md)
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
* Plugins may have other requirements as well.


# Optional Prerequisites
* If you intend to use Docker, [This Guide](https://docs.docker.com/get-started/) should help you get started. The author of fHDHR is not a docker user, but will still try to help.

# Installation

## Linux

The below instructions use the user "sysop", but you can run it as any user. The script will allow you to run as root, but warns against doing so.

* Download the release zip, or git clone to your prefered location. `cd /home/sysop && git clone https://github.com/fHDHR/fHDHR.git`
* Navigate into your script directory and install the python requirements. `cd fHDHR && pip3 install -r requirements.txt`
* Copy the included `config.example.ini` file to a known location. The script will not run without this. There is no default configuration file location. [Modify the configuration file to suit your needs.](Config.md) `cp config.example.ini /home/sysop/config.ini`

* [Install plugins.](Plugins.md) fHDHR will technically run without plugins installed, but is particularly useless without an "origin" plugin.

* Run with the path to the config file. `python3 /home/sysop/fhdhr/main.py -c=/home/sysop/config.ini`


## Docker
This portion of the guide assumes you are using a Linux system with both docker and docker-compose installed. This (or some variation thereof) may work on Mac or Windows, but has not been tested.

* this guide assumes we wish to use the `~/fhdhr` directory for our install (you can use whatever directory you like, just make the appropriate changes elsewhere in this guide).
* run the following commands to clone the repo into `~/fhdhr/fHDHR`
```
cd ~/fhdhr
git clone https://github.com/fHDHR/fHDHR.git
```
* create your config.ini file (as described earlier in this guide) in the `~/fhdhr/fHDHR` directory
* while still in the `~/fhdhr` directory, create the following `docker-compose.yml` file
```
version: '3'

services:
  fhdhr:
    build: ./fHDHR
    container_name: fhdhr
    network_mode: host
    volumes:
      - ./fHDHR/config.ini:/app/config/config.ini
```
* run the following command to build and launch the container
```
docker-compose up --build -d fhdhr
```

After a short period of time (during which docker will build your new fHDHR container), you should now have a working build of fHDHR running inside a docker container.

As the code changes and new versions / bug fixes are released, at any point you can pull the latest version of the code and rebuild your container with the following commands:
```
cd ~/fhdhr/fHDHR
git checkout master
git pull
cd ~/fhdhr
docker-compose up --build -d fhdhr
```
<hr />

You can repeat these instructions for as many fHDHR containers as your system resources will allow, changing the port it runs on.

# Setup

Now that you have fHDHR running, You can navigate (in a web browser) to the IP:Port from the configuration step above.

If you did not setup a `discovery_address` in your config, SSDP will be disabled. This is not a problem as clients like Plex can have the IP:Port entered manually!

You can copy the xmltv link from the webUI and use that in your client software to provide Channel Guide information.
