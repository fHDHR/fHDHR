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

# The Boring Disclaimers (at the top of the docs for a reason)


fHDHR is a Python service to take various sources of video and make them accessible to client software including, but not limited to*:

* [Plex](https://www.plex.tv/)
* [Emby](https://emby.media/)
* [Jellyfin](https://jellyfin.org/)
* [Channels](https://getchannels.com/)

fHDHR is not directly affiliated with the above client software, and you will receive NO support for this script via their forums.

fHDHR was designed to connect to clients by emulating a piece of hardware called the [HDHomeRun from SiliconDust](https://www.silicondust.com/). fHDHR is in NO way affiliated with SiliconDust, and is NOT a HDHomeRun device. fHDHR simply uses the API structure used by the authentic HDHomeRun to connect to client DVR solutions. This functionality has since been moved to a plugin.

fHDHR core supports m3u, but with plugins can emulate an HDHomeRun, or a Plex Media Grabber. Other interfaces to clients can easily be developed as plugins as well.

# History

I got the Huappage QuadHD, and the Mohu Sail as a pandemic-project. All was fine working within Plex, but I also have emby setup as a backup to Plex when auth is broken.

I thought to myself, "Self, I should look on github for a way to share my tv tuner between the two".

That's when I tried both npvrProxy with NextPVR as well as tvhProxy with TVHeadend. I had to tinker with both to get them working, but I started testing which one I liked more.

Around this same time, I stumbled upon [locast2plex by tgorgdotcom](https://github.com/tgorgdotcom/locast2plex). I wanted to contribute to that project to get it to a point that I could fork it to work for other video stream sources.

The locast2plex code development wasn't going quite fast enough for the feature-creep in my head.

I then proceded to create the initial iteration of fHDHR which I originally called "FakeHDHR". I've rewritten the core functionality a few times before landing on the current code structure, which feels 'right'.

I've worked really hard to create a structure that simplifies new variants of the core code to work with different 'origin' streams. Combining these works really well with [xTeVe](https://github.com/xteve-project/xTeVe).

One of the variants goes as far as scraping a table from a PDF file for creating a channel guide!

I can easily create more variants of the project to do other video sources. Paid ones, I could potentially accept donations for, as I don't want to pay to develop for multiple platforms.
