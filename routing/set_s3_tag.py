#!/usr/bin/python
import logging
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime as dt
from xml.etree.ElementTree import fromstring

import boto3
from dateutil.tz import tzutc

DATE_FORMAT = "%d %B %Y %H:%M:%S"

"""AWS app related constants"""
LDM_BUCKET = "maps-sources-us-east-1"
LDM_PREFIX = "ldm/sqlite/{}/"
ALLOWED_STORAGE_CLASSES = ('STANDARD', 'STANDARD_IA')
TAG_NAME = "lastAccessDate"
CLIPPER_PREFIX = "/metadata/build/clipper"
# Days since the last tag updating
LAST_UPDATED_DAYS = 160

"""Regex patterns"""
BUCKET_KEY_REGEX = r"s3:\/\/(?P<bucket>[^/]+)/(?P<key>[^\s$,]+)"
REGION_DVN_REGEX = r"CDC_(?P<region>[^\n_]+)|Source_data_(?P<dvn>[^\n]+)"

"""Logging settings"""
LOG_NAME = "SetS3Tag"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] --- %(message)s (%(filename)s:%(lineno)s)"

"""Initialize logging routine"""
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger(name=LOG_NAME)


def create_s3_session(service_name="s3", connection_type="client"):
    """Create an S3 connection session"""
    session = boto3.client(service_name) if connection_type == "client" \
        else boto3.resource(service_name)
    log.info("Connection to AWS S3 [{}]: [{}] is successfully created".format(connection_type,
                                                                              session))
    return session


def get_objects_metadata(session, ldm_name, bucket, prefix):
    try:
        response = session.list_objects(Bucket=bucket, Prefix=prefix.format(ldm_name))
    except session.exceptions.NoSuchBucket:
        log.error("No such [{}] bucket on S3.".format(bucket)), sys.exit(1)
    else:
        return response.get("Contents", []) if response.get("Contents") \
            else log.error(
            "There are not any objects stored on S3 for the [{}] LDM".format(ldm_name))


def validate_storage_information(metadata):
    for data in metadata:
        key = data.get("Key")
        storage_class = data.get("StorageClass")
        last_modified_date = data.get("LastModified")
        last_modified_days = (dt.now().replace(tzinfo=tzutc()) - last_modified_date).days

        if storage_class not in ALLOWED_STORAGE_CLASSES:
            log.error("Object key [{}] was modified [{}] day(s) ago and already has restricted [{}]"
                      " storage class ".format(key, last_modified_days, storage_class))
        else:
            log.info("Object key [{}] has storage class [{}], was modified [{}] day(s) ago and "
                     "might be moved to Glassier in {} day(s))".format(key, storage_class,
                                                                       last_modified_days,
                                                                       180 - last_modified_days))
            yield key


def get_object_tagging(session, key, bucket):
    try:
        response = session.get_object_tagging(Bucket=bucket, Key=key)
    except session.exceptions.NoSuchKey:
        log.error("Specified [{}] key does not exist.".format(key))
    except session.exceptions.ClientError:
        log.error("TagSet for [{}] key specified does not exist.".format(key))
    else:
        return response.get("TagSet")


def set_object_tagging(session, tag_set, key, bucket, tag_key, time_stamp):
    time_date = dt.fromtimestamp(time_stamp).strftime(DATE_FORMAT)
    # Create initial tagging object
    tagging = dict(TagSet=tag_set)
    # Update tagging object with new data
    tagging["TagSet"].append(dict(Key="{}".format(tag_key), Value="{}".format(time_stamp)))
    try:
        response = session.put_object_tagging(Bucket=bucket, Key=key, Tagging=tagging)
    except session.exceptions.NoSuchKey:
        log.error("Specified object key [{}] does not exist. Tag is not set.".format(key))
    except session.exceptions.ClientError:
        log.error("PutObjectTagging operation will not be performed: Access Denied. "
                  "[{}] object's tag has not been updated.".format(key))
    else:
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            log.info("Object key [{}] tag has been updated with new lastAccessDate [{}] | "
                     "[{}]".format(key, time_stamp, time_date))
        else:
            log.error("Object key [{}] tag has not been updated. Returned response status "
                      "code [{}]".format(key, response["ResponseMetadata"]["HTTPStatusCode"]))


def delete_object_tagging(session, key, bucket):
    try:
        response = session.delete_object_tagging(Bucket=bucket, Key=key)
    except session.exceptions.NoSuchKey:
        log.error("The specified object key [{}] does not exist. "
                  "Tag is not deleted.".format(key))
    except session.exceptions.ClientError:
        log.error("DeleteObjectTagging operation will not be performed: Access Denied. "
                  "[{}] object's tag has not been deleted.".format(key))
    else:
        if response and response["ResponseMetadata"]["HTTPStatusCode"] == 204:
            log.info("Object key [{}] tag has been deleted.".format(key))
        else:
            log.error("Object key [{}] tag has not been deleted. Returned response status "
                      "code [{}]".format(key, response["ResponseMetadata"]["HTTPStatusCode"]))


def get_tag_info(tag_set_list, tag_key):
    for tag in tag_set_list:
        if tag.get("Key") == tag_key:
            return tag


def validate_last_access_date_value(key, last_access_date_tag, time_stamp):
    last_access_date = last_access_date_tag.get("Value")
    timedelta = dt.fromtimestamp(int(time_stamp)) - dt.fromtimestamp(int(last_access_date))
    if timedelta.days < LAST_UPDATED_DAYS:
        log.info("Object's key [{}] lastAccessDate tag value will not be updated "
                 "(at least [{}] days after the last updating)".format(key, timedelta.days))
        return True
    else:
        log.warning("Object's key [{}] [{}] value will be updated ({} days after "
                    "the last updating)".format(key, TAG_NAME, timedelta.days))
        return False


def update_object_tagging(session, metadata, bucket, tag_key, time_stamp):
    for key in validate_storage_information(metadata):
        tag_set = get_object_tagging(session, key, bucket)
        if not get_tag_info(tag_set, tag_key):
            log.warning("Object's key [{}] [{}] tag value will be added".format(key, tag_key))
            set_object_tagging(session, tag_set, key, bucket, tag_key, time_stamp)
        else:
            last_access_date_tag = get_tag_info(tag_set, tag_key=TAG_NAME)
            if validate_last_access_date_value(key, last_access_date_tag, time_stamp):
                continue
            else:
                for tag in tag_set:
                    if tag["Key"] == tag_key:
                        tag_set.remove(tag)
                set_object_tagging(session, tag_set, key, bucket, tag_key, time_stamp)


def get_bucket_and_key(path):
    matches = re.findall(BUCKET_KEY_REGEX, path)
    if len(matches) == 1 and len(matches[0]) == 2:
        bucket, key = matches[0][0], matches[0][1]
        log.info("Found bucket: [{}] and object key: [{}]".format(bucket, key))
        return bucket, key
    else:
        log.error("Incorrect path to map: [{}], please recheck if 's3://' present".format(path))
        sys.exit(1)


def get_map_build_info(path):
    session = create_s3_session(connection_type="resource")
    bucket_name, key_path = get_bucket_and_key(path)
    bucket_object = session.Bucket(bucket_name)
    build_info = defaultdict(list)
    if "format8" in key_path:
        log.info("FORMAT8 map identified on path [{}]".format(key_path))
        key_name = key_path + "/sources.xml"
        key_object = bucket_object.Object(key_name)
        sources_content = key_object.get()["Body"].read().decode("utf-8")
        # Parse XML document from string constant
        root = fromstring(sources_content)
        if root.attrib.get("s3_bucket") == "s3://" + LDM_BUCKET:
            for children in root:
                if children.tag == "ldm" and children.attrib.get("path") in LDM_PREFIX:
                    for child in children:
                        build_info[child.attrib.get("region")].append(child.text)
    else:
        log.info("NDS map identified on path [{}]".format(key_path))
        log.warning("Getting sources information will take some time".format(key_path))
        key_name = key_path + CLIPPER_PREFIX
        contents = session.meta.client.list_objects(Bucket=bucket_name,
                                                    Prefix=key_name).get("Contents")
        for key_name in [content.get("Key") for content in contents]:
            country, _ = key_name.split("/")[-1].split(".")[0].split("_")[:2]
            key_object = bucket_object.Object(key_name)
            clipper_content = key_object.get()["Body"].read().decode("utf-8")
            matches = re.findall(REGION_DVN_REGEX, clipper_content)
            region, dvn = [list(filter(None, list(match))).pop() for match in matches]
            ldm_name = region + "_" + dvn
            build_info[region].append(ldm_name)
    return build_info


if __name__ == "__main__":
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument("--ldm-list", dest="ldm_list",
                        help="Comma separated list of DVNs", required=False)
    parser.add_argument("--map-path", dest="map_path", default=False,
                        help="Path to map sources on S3", required=False)
    args = parser.parse_args()

    # Create S3 Client connection
    s3_client = create_s3_session()

    # Unpack LDM list argument or get list of LDMs directly from map data
    ldm_list = args.ldm_list.split(",") if not args.map_path \
        else [v.pop() for k, v in get_map_build_info(args.map_path).items()]

    # Run processing of each LDM in the given list
    log.info("Received {} LDM list".format(ldm_list))
    for ldm in ldm_list:
        log.info("Start processing: [{}] DVN".format(ldm))
        object_metadata = get_objects_metadata(s3_client, ldm, LDM_BUCKET, LDM_PREFIX)
        # Skipping non-existing DVN
        if object_metadata:
            # Get DVN specific timestamp
            timestamp = int(dt.timestamp(dt.now()))
            # Update object tagging
            update_object_tagging(s3_client, object_metadata, LDM_BUCKET, TAG_NAME, timestamp)
