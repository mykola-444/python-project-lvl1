"""
The script takes S3 path to map and returns list of DVNs of the map.
Example:
1.
    $ python3 resolve_dvns.py -p s3://hnds-motegi-prod/prod/EU/1.45.71.444
    Source Data DVNs for 1.45.71.444:
    WEU_171G1
    EEU_171G0
2.
    $ python3 resolve_dvns.py -p
    s3://maps-artifacts-us-east-1/maps/map_79/format8/int/builds/08.030.0079.0150
    Source Data DVNs for 08.030.0079.0150:
    APAC_17143
    AU_17141
    EEU_17143
    IND_17144
    MEA_17141
    NA_17140
    SAM_17142
    TWN_17141
    WEU_17142
    ANT_161H0
    APAC_HK_171R0
    APAC_MACAU_171Q0
    MEA_IM2_171R0
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from argparse import ArgumentParser


def get_f8_sources(path):
    dirpath = tempfile.mkdtemp()
    subprocess.check_output("aws s3 cp %s/sources.xml %s"
                            % (path, dirpath), shell=True)
    dvns = list()
    with open(os.path.join(dirpath, "sources.xml")) as _file:
        for line in _file:
            for reg_dvn in set(re.findall(">(.*?)</dvn>", line)):
                dvns.append(reg_dvn)
    shutil.rmtree(dirpath)
    return dvns


def get_nds_sources(path):
    local_clipper_path = tempfile.mkdtemp()
    aws_clipper_path = "%s/metadata/build/clipper/" % (path)
    dvns = set()
    countries = set()
    subprocess.call(
        "aws s3 cp %s %s --recursive --exclude '*' --include '*'"
        % (aws_clipper_path, local_clipper_path), shell=True)
    for update_region_info in os.listdir(local_clipper_path):
        with open(os.path.join(local_clipper_path, update_region_info)) as file_:
            line = file_.readlines()
            dvns.add(get_dvn_name(line))
            countries.add(update_region_info[:3])
    shutil.rmtree(local_clipper_path)
    return list(dvns), countries


def get_dvn_name(line):
    items = line[0].strip().split("_")
    reg = items[1] + "_" + items[2] if len(items) == 4 else items[1]
    return "%s_%s" % (reg, line[-1].strip().split("_")[-1])


def load_properties(filepath, sep='=', comment_char='#'):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    with open(filepath, "rt") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(comment_char):
                key_value = line.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"')
                props[key] = value
    return props


def get_regions_countries(map_config_path):
    regions = set()
    countries = set()
    props = load_properties(map_config_path)
    if "map_format8" in map_config_path:
        # Format8 or BRF
        aws_source_path = "%s/%s/sources.xml" % (props["map_aws_s3_bucket_url"], props["map_path"])
        local_source_path = tempfile.mktemp()
        subprocess.call("aws s3 cp %s %s" % (aws_source_path, local_source_path), shell=True)
        with open(local_source_path, "r") as _file:
            for line in _file:
                for reg_dvn in set(re.findall(">(.*?)</dvn>", line)):
                    regions.add(reg_dvn)
        os.remove(local_source_path)
    elif "map_nds" in map_config_path or "sparta" in map_config_path:
        # NDS
        markets_meta = {k: v for k, v in props.items() if k.startswith("folder_metadata_")}
        for market in markets_meta:
            # Example: markets_meta[market] = 'hnds-motegi-prod/prod/RW/1.47.73.486/metadata/map'
            # markets_meta[market][:-13] = 'hnds-motegi-prod/prod/RW/1.47.73.486'
            path = "s3://%s" % (markets_meta[market][:-13])
            if "sparta" in map_config_path:
                _regions, countries = get_nds_sources(path)
                print("Regions: ", _regions, "Countries: ", countries)
                regions.update(_regions)
            else:
                regions.update(get_nds_sources(path)[0])
    else:
        print("ERROR: Undetermined map config file", map_config_path)
        sys.exit(1)

    return list(regions), countries


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-p", "--path", type=str, dest="path",
                        help="Path to source DB", required=True)
    args = parser.parse_args()
    if "format8" in args.path:
        # F8/brf/F6
        dvns = get_f8_sources(args.path)
    else:
        # NDS maps
        dvns = get_nds_sources(args.path)
    input_map = args.path.split("/")[-1]
    if not dvns:
        print("ERROR: Cannot find DVNs for map '%s'. Please verify path: '%s'"
              % (input_map, args.path))
        sys.exit()
    print("\n\nSource Data DVNs for %s:" % input_map)
    for dvn in dvns:
        print(dvn)


if __name__ == "__main__":
    main()
