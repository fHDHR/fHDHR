FROM lsiobase/ubuntu:focal
LABEL maintainer="berserkirwolf"
ENV TITLE="fHDHR"
ENV VERSION="1.0.0"

RUN \
	echo "************ install & upgrade packages ************" && \
	apt-get update -y && \
	apt-get install -y --no-install-recommends \
		python3 \
		python3-pip \
		gcc \
		git \
		ffmpeg \
		youtube-dl && \
	rm -rf \
		/tmp/* \
		/var/lib/apt/lists/* \
		/var/tmp/* && \
	echo "************ install download fHDHR ************"  && \
	git clone https://github.com/fHDHR/fHDHR.git && \
	echo "************ install pip dependencies ************" && \
	python3 -m pip install --user --upgrade pip && \	
 	pip3 install -r fHDHR/requirements.txt && \
	echo "************ cleanup  ************" && \
	rm -rf fHDHR

# copy local files
COPY root/ /

# set work directory
WORKDIR /config

# ports and volumes
VOLUME /config
