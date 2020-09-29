# FakeHDHR_Locast

(based off of original code from

  * [tvhProxy by jkaberg](https://github.com/jkaberg/tvhProxy)
  * [locast2plex by tgorgdotcom](https://github.com/tgorgdotcom/locast2plex)
  * myself coding for locast2plex

  )

Until I have time to do the wiki thing for this project, instructions will be in this `README.md`.

PRs welcome for:

* Docker support


Vague Instructions (specific details intentionally excluded):

* Install ffmpeg, and verify it is accessible in PATH. Otherwise, you may specify it's path in your configuration later.
* Install Python3 and Python3-pip. There will be no support for Python2.
* Download the zip of the `master` branch, or `git clone`.
* `pip3 install -r requirements.txt`
* Copy the included configuration example to a known path, and adjust as needed. The script will look in the current directory for `config.ini`, but this can be specified with the commandline argument `--config_file=`
