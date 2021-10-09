#!/bin/bash
apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-dev \
    libmemcached-dev \
    memcached \
    python3-setuptools \
    python3-pip \
    sqlite3 \
    libsqlite3-dev \
    libxml2-dev \
    libxslt1-dev \
    libz-dev \
    python3-sphinx \
    awscli
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
    shapely
