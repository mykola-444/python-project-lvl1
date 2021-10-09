#!/bin/bash
brew install \
    git \
    python3 \
    sqlite3 \
    memcached \
    libmemcached \
    awscli
# build-essential libxml2-dev libxslt1-dev libz-dev python3-sphinx
yes | pip3 install \
    pylibmc \
    configparser \
    boto3 \
    lxml \
    pytz \
    timezonefinder \
    mock \
    requests \
    jinja2 \
    shapely \
    robotframework
