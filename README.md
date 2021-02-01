<p align="center">fHDHR_Locast    <img src="docs/images/logo.ico" alt="Logo"/></p>


Welcome to the world of streaming content as a DVR device! We use some fancy python here to achieve a system of:

**f**un
**H**ome
**D**istribution
**H**iatus
**R**ecreation


Please Check the [Docs](docs/README.md) for Installation information.

fHDHR is labeled as beta until we reach v1.0.0

Join us in `#fHDHR <irc://irc.freenode.net/#fHDHR>`_ on Freenode.

# !!NOTICE!!

To reduce code duplication between variants, I am moving to a plugin system.
The normal variant repos will stay active during the transition.

This is the new "core" repo. plugin repos can be "git cloned" into the plugins folder.

I have opened up the ability for alternative EPG, Streaming, and origin plugins.

I also have moved Plex RMG and HDHR type connections to plugins. The core fHDHR will still support m3u.


## Also
Docs are still mostly the same, but will be lacking in some ways during the transition.

## Docker Support
I am not a docker user, but I am fairly certain that after you assemble the plugins you want in the plugins folder, and run the Dockerfile, it should still work*.



# Basic Installation instructions (until new Docs can be written)

## 1) git clone this repo

## 2) Install an origin plugin

## 3) Install other plugins.

* There are a couple EPG plugins that go great with Local Channel variants
* There are a couple stream method plugins that are completely optional
* Interface plugins like HDHR and RMG are useful methods to interface with clients.

## 4) Use with Plex/Emby/Channels/xTeVe (step 3 dependencies)

## 5) Profit?
