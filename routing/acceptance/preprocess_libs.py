"""
Merge libs from different import DVNs:
Example of execution:
$ python preprocess_libs.py -p /tmp/output/ -o /tmp/merged_libs

Expected folder with libs:

$ tree /tmp/output/
output/
├── AU_18123
│   └── highways
│       ├── highways_car_lib_0.robot
│       ├── highways_car_lib_1.robot
│       ├── highways_truck_lib_0.robot
│       └── highways_truck_lib_1.robot
└── WEU_18122
    ├── highways
    │   ├── highways_car_lib_0.robot
    │   ├── highways_car_lib_1.robot
    │   ├── highways_truck_lib_0.robot
    │   └── highways_truck_lib_1.robot
    └── toll_roads
        ├── toll_roads_car_one_way_direction_without_alternatives_lib_0.robot
        ├── toll_roads_car_one_way_direction_without_alternatives_lib_1.robot

Output folder 'merged_libs':
$ tree /tmp/merged_libs
├── highways
│   ├── highways_car_lib_0.robot
│   ├── highways_car_lib_1.robot
│   ├── highways_car_lib_2.robot
│   ├── highways_car_lib_3.robot
│   ├── highways_truck_lib_0.robot
│   └── highways_truck_lib_1.robot
│   └── highways_truck_lib_2.robot
│   └── highways_truck_lib_3.robot
└── toll_roads
    ├── toll_roads_car_one_way_direction_without_alternatives_lib_0.robot
    ├── toll_roads_car_one_way_direction_without_alternatives_lib_1.robot
"""

import glob
import os
import shutil
from argparse import ArgumentParser
from collections import defaultdict
from filter_kwd_libs import create_folder
from robot.api import ResourceFile
from shutil import copyfile


def copy_with_specified_keywords(source_file, dest_file, path_to_subfolder, keywords):
    keywords = keywords.split(";")
    source_resource_file = ResourceFile(source=source_file)
    dest_resource_file = None
    for keyword in source_resource_file.populate().keywords:
        if keyword.name in keywords:
            if dest_resource_file is None:
                if not os.path.exists(path_to_subfolder):
                    create_folder(path_to_subfolder)
                dest_resource_file = ResourceFile(source=dest_file)
            dest_resource_file.keywords.append(keyword)
    if dest_resource_file:
        dest_resource_file.save()


def merge_libs(path_to_libs, output, keywords):
    counters = defaultdict(int)
    for dvn in os.listdir(path_to_libs):
        for subfolder in os.listdir(os.path.join(path_to_libs, dvn)):
            path_to_subfolder = os.path.join(output, subfolder)
            for source_file in glob.iglob(
                    '{}/*.robot'.format(os.path.join(path_to_libs,
                                                     dvn, subfolder))):
                base_name = source_file[source_file.rfind("/") + 1:source_file.rfind("_")]
                dest_file = "{}/{}_{}.robot".format(
                    os.path.join(output, subfolder),
                    base_name,
                    counters[base_name])
                if keywords is None:
                    if not os.path.exists(path_to_subfolder):
                        create_folder(path_to_subfolder)
                    print("Copy '{}' to '{}'".format(source_file, dest_file))
                    copyfile(source_file, dest_file)
                    counters[base_name] += 1
                else:
                    copy_with_specified_keywords(source_file, dest_file,
                                                 path_to_subfolder, keywords)
                    if os.path.exists(dest_file):
                        counters[base_name] += 1


def main():
    parser = ArgumentParser(description="Merge keywords from different folders to one.")
    parser.add_argument("-p", "--path_to_libs", type=str, dest="path_to_libs",
                        help="Path to folder that contains folders with libs split by DVN", required=True)
    parser.add_argument("-k", "--keywords", type=str, dest="keywords",
                        help="Semicolon separated list of keywords")
    parser.add_argument("-o", "--output", type=str, dest="output",
                        help="Output folder that contains merged libs", required=True)
    options = parser.parse_args()
    output = os.path.abspath(options.output)
    if os.path.exists(output):
        shutil.rmtree(output)
    create_folder(output)
    merge_libs(options.path_to_libs, output, options.keywords)


if __name__ == "__main__":
    main()
