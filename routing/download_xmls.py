#!/usr/bin/python3
import configparser
import fnmatch
import logging
import os
import re
import sys
import tarfile
import urllib
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime as dt
from xml.etree.ElementTree import fromstring

import boto3
import botocore
from dateutil.tz import tzutc

from set_s3_tag import get_objects_metadata, LDM_BUCKET, LDM_PREFIX, ALLOWED_STORAGE_CLASSES

"""Root settings"""
EXCLUDED_REGIONS = ["ANT"]
F8_CONFIG_SECTION = "F8-MAP-CONFIGS"
NDS_CONFIG_SECTION = "NDS-MAP-CONFIGS"
UNSUPPORTED_FILES = ["*.robot", ]
LDM_PREFIX_SQLITE = "ldm/sqlite/{}/"
LDM_PREFIX_CACHE = "ldm/cache/{}/"

"""Logging settings"""
LOG_NAME = __name__
LOG_FORMAT = "[%(asctime)s] [%(levelname)-7s] --- %(message)s (%(filename)s:%(lineno)s)"

"""Initialize logging routine"""
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(name=LOG_NAME)


def parse_map_configs(config_section, map_config_path):
    """Read the file passed as parameter as a properties file"""
    with open(map_config_path, "r") as config_file:
        config_string = "[{}]".format(config_section) + config_file.read()
    map_config = configparser.ConfigParser()
    map_config.read_string(config_string)
    return map_config


def get_map_paths(map_config):
    map_paths = []
    if F8_CONFIG_SECTION in map_config.sections():
        map_path = "{}/{}".format(map_config[F8_CONFIG_SECTION].get("map_aws_s3_bucket_url", ""),
                                  map_config[F8_CONFIG_SECTION].get("map_path", ""))
        map_paths.append(map_path)
        logger.info("Found s3 path to the F8 map [{}]".format(map_path))
    elif NDS_CONFIG_SECTION in map_config.sections():
        for name, value in map_config[NDS_CONFIG_SECTION].items():
            if name.startswith("folder_client"):
                map_path = "s3://" + "/".join(value.split("/")[:-2])
                map_paths.append(map_path)
                logger.info("Found s3 path to the NDS map [{}]".format(map_path))
    else:
        logger.error("Cannot parse config [{}] section(s)".format(" ,".join(map_config.sections())))
        sys.exit(1)
    return map_paths


def create_s3_session(service_name, connection_type):
    """Create an S3 connection session"""
    session = boto3.client(service_name) if connection_type == "client" \
        else boto3.resource(service_name)
    logger.info("Connection to S3 [{}]: [{}] is successfully established".format(connection_type,
                                                                                 session))
    return session


def get_bucket_and_key(map_path):
    parsed = urllib.parse.urlparse(map_path)
    bucket, key = parsed.netloc, parsed.path.lstrip("/")
    logger.info("Found bucket: [{}] and object key: [{}]".format(bucket, key))
    return bucket, key


def get_f8_map_build_info(session, map_path):
    bucket, key = get_bucket_and_key(map_path)
    bucket_object = session.Bucket(bucket)
    build_info = defaultdict(list)
    key += "/sources.xml"
    key_object = bucket_object.Object(key)
    sources_content = key_object.get()["Body"].read().decode("utf-8")
    # Parse XML document from string constant
    root = fromstring(sources_content)
    if root.attrib.get("s3_bucket") == "s3://" + "maps-sources-us-east-1":
        for children in root:
            if children.tag == "ldm" and (children.attrib.get("path") == LDM_PREFIX_SQLITE or LDM_PREFIX_CACHE):
                for child in children:
                    if child.text not in build_info[child.attrib.get("region")]:
                        build_info[child.attrib.get("region", [])].append(child.text)
                    else:
                        continue
    return build_info


def get_nds_map_build_info(session, map_path):
    bucket, key = get_bucket_and_key(map_path)
    bucket_object = session.Bucket(bucket)
    build_info, countries = defaultdict(list), []
    logger.warning("Getting sources information from clipper info files will take some time...")
    key += "/metadata/build/clipper"
    contents = session.meta.client.list_objects(Bucket=bucket, Prefix=key).get("Contents")
    for key in [content.get("Key") for content in contents]:
        country, _ = key.split("/")[-1].split(".")[0].split("_")[:2]
        countries.append(country)
        key_object = bucket_object.Object(key)
        clipper_content = key_object.get()["Body"].read().decode("utf-8")
        dvn_regex = r"CDC_(?P<region>[^\n_]+)|Source_data_(?P<dvn>[^\n]+)"
        matches = re.findall(dvn_regex, clipper_content)
        region, dvn = [list(filter(None, list(match))).pop() for match in matches]
        ldm_name = region + "_" + dvn
        logger.info("Retrieved: [{}] country code of [{}] LDM "
                    "from [{}] clipper file".format(country, ldm_name, key.split("/")[-1]))
        if ldm_name not in build_info[region]:
            build_info[region].append(ldm_name)
        else:
            continue
    return build_info, sorted(list(set(countries)))


def skip_unsupported_regions(build_info):
    for region in list(build_info.keys()):
        if region in EXCLUDED_REGIONS:
            logger.warning("Removed unsupported LDMs: {}".format(build_info.pop(region)))
        else:
            continue


def parse_map_build_info(session, map_config_path):
    region_ldms, countries = [], []
    if "format8" in map_config_path:
        logger.info("FORMAT8 map identified on map config path [{}]".format(map_config_path))
        map_config = parse_map_configs(F8_CONFIG_SECTION, map_config_path)
        for map_path in get_map_paths(map_config):
            region_ldms.append(get_f8_map_build_info(session, map_path))
    else:
        logger.info("NDS map identified on map config path [{}]".format(map_config_path))
        map_config = parse_map_configs(NDS_CONFIG_SECTION, map_config_path)
        for map_path in get_map_paths(map_config):
            build_info, countries_list = get_nds_map_build_info(session, map_path)
            region_ldms.append(build_info)
            countries += countries_list
    return region_ldms, sorted(list(set(countries)))


def get_ldms_of_missed_tests(session, ldms, bucket, prefix="mitf/xml"):
    bucket_object = session.Bucket(bucket)
    missed_test_ldms = list()
    for ldm in ldms:
        if not list(bucket_object.objects.filter(Prefix="{}/{}".format(prefix, ldm))):
            missed_test_ldms.append(ldm)
    return missed_test_ldms


def download_files_from_s3(session, bucket, ldm, archive_file, prefix="mitf/xml"):
    key = "{}/{}/tests.tgz".format(prefix, ldm)
    try:
        session.Bucket(bucket).download_file(key, archive_file)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.error("The [{}] object does not exist on the [{}] bucket".format(key, bucket))
        elif e.response['Error']['Code'] == "403":
            logger.error("Operation on [{}] object of [{}] bucket - FORBIDDEN, "
                         "please set correct ACL Settings".format(key, bucket))
        else:
            raise
        sys.exit(1)
    else:
        logger.info("Object [{}] has been successfully downloaded to [{}]".format(key,
                                                                                  archive_file))


def extract_archive(archive_file, xmls_path):
    if not tarfile.is_tarfile(archive_file):
        logger.error("Given [{}] is not a tar archive file".format(archive_file))
    try:
        tar_file = tarfile.open(archive_file)
    except tarfile.ReadError:
        logger.error("Cannot define archive on [{}] path".format(archive_file))
    else:
        tar_file.extractall(xmls_path)
        logger.info("Archive [{}] has been successfully extracted to [{}]".format(archive_file,
                                                                                  xmls_path))
        test_version_file = os.path.join(xmls_path, "MITF_VERSION")
        mitf_version_file = os.path.join("map-integration-testing", "VERSION")
        if not os.path.isfile(test_version_file):
            logger.error("There is no [MITF_VERSION] file on [{}] path".format(test_version_file))
            logger.info("Trying to find it in another place ...")
            for dirpath, dirnames, filenames in os.walk(os.path.abspath(xmls_path)):
                for filename in filenames:
                    if filename == "MITF_VERSION":
                        test_version_file = os.path.join(dirpath, filename)
                        logger.info("Version [{}] file found".format(test_version_file))
        if not os.path.isfile(test_version_file) or os.path.isfile(mitf_version_file):
            logger.error("Cannot compare MITF generator versions")
        else:
            with open(os.path.join(xmls_path, "MITF_VERSION"), "r") as test_version_reader, \
                    open("map-integration-testing/VERSION", "r") as mitf_version_reader:
                test_version = test_version_reader.read().strip()
                mitf_version = mitf_version_reader.read().strip()
            logger.info("Tests were generated on current MITF version [{}]".format(test_version)) \
                if test_version == mitf_version \
                else logger.error("Please note that tests have been generated on not actual MITF SW"
                                  " version [{}] but current version is [{}].".format(test_version,
                                                                                      mitf_version))
        os.remove(archive_file)
        logger.info("File [{}] has been successfully removed".format(archive_file))
        tar_file.close()


def remove_unsupported_xmls(xmls_path, countries):
    for root, dirnames, file_names in os.walk(xmls_path):
        for filename in fnmatch.filter(file_names, "*.xml"):
            try:
                file_path = os.path.join(root, filename)
                country = re.search(r"code=\"(.*?)\"", open(file_path, encoding='utf-8').read()).group(1)
                if countries and country not in countries:
                    logger.warning("Test [{}] has been excluded (Country: [{}])".format(file_path,
                                                                                        country))
                    os.remove(os.path.join(root, filename))
            except Exception as err:
                logger.error("{}".format(err))
                sys.exit(1)


def remove_unsupported_test_files(xmls_path):
    for root, dirnames, filenames in os.walk(xmls_path):
        for pattern in UNSUPPORTED_FILES:
            for filename in fnmatch.filter(filenames, pattern):
                logger.warning("Unsupported test file format detected: {}".format(filename))
                os.remove(os.path.join(root, filename))
                logger.info("File [{}] has been successfully removed".format(filename))


def validate_storage_information(metadata, ldm_name):
    storage_info = {
        ldm_name: {
            "storage_class": set(),
            "last_modified": set()
        }}
    for data in metadata:
        key = data.get("Key")
        if data.get("Key").split("/")[2] != ldm_name:
            logger.error("Object key [{}] inconsistency with [{}] LDM name".format(key, ldm_name))
            sys.exit(1)
        else:
            storage_info[ldm_name]["storage_class"].add(data.get("StorageClass"))
            storage_info[ldm_name]["last_modified"].add((dt.now().replace(tzinfo=tzutc()) -
                                                         data.get("LastModified")).days)
    storage_class = storage_info[ldm_name]["storage_class"].pop()
    last_modified = storage_info[ldm_name]["last_modified"].pop()
    if storage_class not in ALLOWED_STORAGE_CLASSES:
        logger.error("[{}] LDM objects were modified [{}] day(s) ago and already have restricted "
                     "[{}] storage class".format(ldm_name, last_modified, storage_class))
    else:
        logger.info("[{}] LDM objects have storage class [{}], were modified [{}] day(s) ago and "
                    "might be moved to Glassier in {} day(s))".format(ldm_name,
                                                                      storage_class,
                                                                      last_modified,
                                                                      180 - int(last_modified)))


def main(options):
    bucket = options.mitf_bucket
    logger.info("Using mitf [{}] bucket".format(bucket))
    resource_session = create_s3_session(service_name="s3", connection_type="resource")
    client_session = create_s3_session(service_name="s3", connection_type="client")
    build_info_list, country_list = parse_map_build_info(resource_session, options.map_config)
    missed_tests = get_ldms_of_missed_tests(resource_session,
                                            [v for key, val in build_info_list[0].items() for v in val],
                                            bucket)
    if missed_tests:
        logger.error("Cannot find generated tests of next LDMs {}".format(missed_tests))
        sys.exit(1)
    for build_info in build_info_list:
        skip_unsupported_regions(build_info)
        regions_list, ldms_list = [], []
        for region, ldms in build_info.items():
            xmls_path = os.path.join(options.path_to_xmls, region)
            if not os.path.exists(xmls_path):
                os.makedirs(xmls_path)
            archive_file = os.path.join(xmls_path, "tests.tgz")
            for ldm in ldms:
                download_files_from_s3(resource_session, bucket, ldm, archive_file)
                ldms_list.append(ldm)
                extract_archive(archive_file, xmls_path)
            remove_unsupported_xmls(xmls_path, country_list)
            remove_unsupported_test_files(xmls_path)
            regions_list.append(region)
        logger.info("Regions: {}".format(sorted(regions_list)))
        logger.info("LDMs: {}".format(sorted(ldms_list)))
        for ldm_name in ldms_list:
            metadata = get_objects_metadata(client_session, ldm_name, LDM_BUCKET, LDM_PREFIX)
            if metadata:
                validate_storage_information(metadata, ldm_name)

        logger.info("Countries: {}".format(country_list)) if country_list else None


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--map_config", dest="map_config", help="Path to map config", required=True)
    parser.add_argument("--path_to_xmls", dest="path_to_xmls", help="Path to xmls", required=True)
    parser.add_argument("--mitf_bucket", dest="mitf_bucket", default="mitf-artifacts")
    arguments = parser.parse_args()
    main(arguments)
