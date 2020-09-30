FROM python:3.8-slim

#RUN apk add --no-cache --update python3 py3-pip python3-dev gcc musl-dev libffi-dev file
#RUN apk add --no-cache --update gcc musl-dev libffi-dev file
#RUN pip3 install --upgrade pip

RUN apt-get -qq update && \
    apt-get -qq -y install ffmpeg && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/*

COPY ./ /app/
WORKDIR /app
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "/app/main.py", "--config_file", "/app/config/config.ini"]
