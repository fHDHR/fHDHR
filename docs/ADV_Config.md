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

Here, we'll break down all of the configuration options per section.

## Main
Here's the `main` section.
* `uuid` will be created automatically, you need not worry about this.
* `cache_dir` is handy for keeping cached files out of the script directory. This is helpful for reinstalls as well as development.

````
[main]
# uuid =
# cache_dir =
````

## streaming

* `method` can be set to `ffmpeg`, `vlc` or `direct`.
* `bytes_per_read` determines how many bytes of the stream to read before sending the data to your client. Increasing this value may cause longer load times, and lowering it may effect `stuttering`.
* `origin_quality` can be set to high,medium,low for most variants. Variants that make use of m3u8 will Autoselect High for the direct method if not set. ffmpeg/vlc will determine the best stream on their own. Some Variants can allow alternative values.
* `transcode_quality` works with ffmpeg/vlc to use fHDHR for handling quality instead of the origin. Valid settings include: heavy,mobile,internet720,internet480,internet360,internet240


````
[streaming]
# method = direct
# bytes_per_read = 1152000
# origin_quality = None
# transcode_quality = None
````


## fhdhr

The `fhdhr` contains all the configuration options for interfacing between this script and your media platform.
* `address` and `port` are what we will allow the script to listen on. `0.0.0.0` is the default, and will respond to all.
* `discovery_address` may be helpful for making SSDP work properly. If `address` is not `0.0.0.0`, we will use that. If this is not set to a real IP, we won't run SSDP. SSDP is only really helpful for discovering in Plex/Emby. It's a wasted resource since you can manually add the `ip:port` of the script to Plex.
* `tuner_count` is a limit of devices able to stream from the script. The default is 3, as per Locast's documentation. A 4th is possible, but is not reccomended.
* `friendlyname` is to set the name that Plex sees the script as.
* `reporting_*` are settings that show how the script projects itself as a hardware device.
* `device_auth` and `require_auth` are for an unimplemented Authentication feature.
* `chanscan_on_start` Scans Origin for new channels at startup.


````
[fhdhr]
# address = 0.0.0.0
# discovery_address = 0.0.0.0
# port = 5004
# tuner_count =  4
# friendlyname = fHDHR-Locast
# reporting_firmware_name = fHDHR_Locast
# reporting_manufacturer = BoronDust
# reporting_model = fHDHR
# reporting_firmware_ver = 20201001
# reporting_tuner_type = Antenna
# device_auth = fHDHR
# require_auth = False
# chanscan_on_start = True
````

# EPG
* `images` can be set to `proxy` or `pass`. If you choose `proxy`, images will be reverse proxied through fHDHR.
* `method` defaults to `origin` and will pull the xmltv data from Locast. Other Options include `blocks` which is an hourly schedule with minimal channel information. Another option is `zap2it`, which is another source of EPG information. Channel Numbers may need to be manually mapped.
* `update_frequency` determines how often we check for new scheduling information. In Seconds.
* `reverse_days` allows Blocks of EPG data to be created prior to the start of the EPG Source data.
* `forward_days` allows Blocks of EPG data to be created after the end of the EPG Source data.
* `block_size` in seconds, sets the default block size for data before, after and missing timeslots.
* `xmltv_offset` allows the final xmltv file to have an offset for users with timezone issues.

````
[epg]
# images = pass
# method = origin
# update_frequency = 43200
# reverse_days = -1
# forward_days = 7
# block_size = 1800
# xmltv_offset = +0000
````

## ffmpeg

The `ffmpeg` section includes:
* `path` is useful if ffmpeg is not in your systems PATH, or you want to manually specify.

````
[ffmpeg]
# path = ffmpeg
````

## vlc

The `vlc` section includes:
* `path` is useful if ffmpeg is not in your systems PATH, or you want to manually specify.

````
[vlc]
# path = cvlc
````

# Logging
* `level` determines the amount of logging you wish to see in the console, as well as to the logfile (stored in your cache directory).

````
[logging]
# level = WARNING
````

# Database
* experiment with these settings at your own risk. We use sqlalchemy to provide database options, but we default to sqlite.

TODO: improve documentation here.

````
[database]
# type = sqlite
# driver = None
user = None
pass = None
host = None
port = None
name = None
````

## RMG

````
# enabled = True
````

## SSDP

````
# enabled = True
# max_age = 1800
# proto = ipv6
# iface = None
# multicast_address = None
````

## Locast
The `locast` section
* requires `username` and `password`. The script will not run without these.
* `override_zipcode` is useful for if your DMA is not being picked up correctly.
* `override_latitude` and `override_longitude` are helpful for "mocking" your location.


````
[locast]
# username =
# password =
# override_zipcode = None
# mock_location = None
````

## zap2it

`zap2it` contains a ton of configuration options, and defaults to options that in my experience don't need to be adjusted.
* `postalcode` is a value of importance, and is helpful. If not set, the script will attempt to retrieve your postalcode automatically.

````
[zap2it]
# delay = 5
# postalcode = None
# affiliate_id = gapzap
# country = USA
# device = -
# headendid = lineupId
# isoverride = True
# languagecode = en
# pref =
# timespan = 6
# timezone =
# userid = -
````
