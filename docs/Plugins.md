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

This page will discuss types of plugins.

# Origins
[Look Here for plugins that start with "fHDHR_plugin_origin_"](https://github.com/fHDHR).

An Origin plugin is where we are streaming video from. It provides fHDHR with a channel listing, and how to connect to a service to stream from.

Some Origin plugins will provide EPG data, those that don't will have blocks of empty timeslot data created.

Some Origin Plugins will provide an added webpage to the webUI.

Without an Origin plugin installed, fHDHR really cannot do much of anything.


# Interface Plugins
[Look Here for plugins that start with "fHDHR_plugin_interface_"](https://github.com/fHDHR).

Interface plugins provide additionally access to fHDHR. By default, fHDHR provides basic channel with an accessible API for channel tuning, EPG, and m3u.

A plugin of most interest to the average user will be the `fHDHR_plugin_interface_hdhr` plugin which provides Plex access to fHDHR as if it was a HDHomeRun device.


# Stream Plugins
[Look Here for plugins that start with "fHDHR_plugin_stream_"](https://github.com/fHDHR).

These plugins provide alternative methods for streaming. At it's core fHDHR was designed to NOT rely on ffmpeg/vlc to run.

These plugins can allow transcoding at the fHDHR level, whereas fHDHR core cannot.

# EPG Plugins
[Look Here for plugins that start with "fHDHR_plugin_epg_"](https://github.com/fHDHR).

These plugins provide alternative sources of EPG information. This can be handy for origin plugins that don't provide good/any EPG.
