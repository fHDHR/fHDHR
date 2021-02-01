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
