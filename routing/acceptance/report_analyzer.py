"""
Parses xunit.xml report, finds the most suitable keywords.
Execution:

$ python report_analyzer.py -r PATH_TO_PRODUCTION_REPORT/xunit.xml -s
PATH_TO_UPDATE_TEST_CASES_WITH_dev*_robot_FILES/international/ -o
PATH_ORIGIN_SOURCES/spec_orig/international/ -f OUTPUT_FOLDER
"""
import glob
import os
import re
import shutil
from argparse import ArgumentParser
from collections import defaultdict
from copy import deepcopy

from lxml import etree
from robot.api import TestData, ResourceFile

from filter_kwd_libs import create_folder
from utils.acceptance_tests import collect
from utils.geometry_tools import get_distance_between_two_points, WGS84Point

THRESHOLD = 1.7


def get_test_case_map(covered_keywords, sources):
    """
    Returns dictionary-map:
    {"TEST_CASE_NAME": "KEYWORD_NAME"}
    """
    test_case_map = dict()
    for keyword, libs in covered_keywords.items():
        for lib in libs:
            parsed_suite = TestData(source=os.path.join(sources, lib))
            for test_case in parsed_suite.testcase_table.tests:
                for step in test_case.steps:
                    if keyword == step.name:
                        test_case_map[test_case.name] = keyword
                        break
    return test_case_map


def parse_report(report):
    """
    Parses xunit.xml (production) report.
    Returns statistic of passed test cases:
    {"TC_NAME": [[0, 1, ..., MAX_INDEX], TOTAL_TEST_CASE_NUMBER]}
    """
    with open(report, encoding="utf-8") as fobj:
        xml = fobj.read()
    root = etree.fromstring(xml.encode('utf8'))
    stats = dict()
    for test_case in root.iter("testcase"):
        tc_name = test_case.get("name")
        tc_index = None
        if not tc_name:
            continue
        if tc_name[-1].isdigit():
            tc_index = tc_name[tc_name.rfind(" ") + 1:]
            tc_name = tc_name[:tc_name.rfind(" ")]
        if not stats.get(tc_name):
            stats[tc_name] = [list(), 0]
        failure = test_case.find("failure")
        if failure is None and tc_index is not None:
            stats[tc_name][0].append(tc_index)
        stats[tc_name][1] += 1
    return stats


def get_point(kwd):
    for step in kwd.steps:
        if step.name is None:
            continue
        if step.name.startswith("Provided geo stop waypoint"):
            coordinates = re.findall(r"at\((.*?)\)", step.args[0])
            if not coordinates:
                return None
            coordinates = [float(i.strip()) for i in coordinates[0].split(",")]
            return WGS84Point(coordinates[1], coordinates[0])


def get_origin_point(keyword, suite, origin):
    inner_keyword = None
    source = os.path.join(origin, suite)
    suite_file = TestData(source=source)
    point = None
    for inner_keyword in suite_file.keyword_table.keywords:
        if inner_keyword.name == keyword:
            point = get_point(inner_keyword)
            break
    else:
        for resource in suite_file.imports:
            if "setup.robot" in resource.name:
                continue
            lib = os.path.abspath(os.path.join(os.path.dirname(source), resource.name.strip()))
            resource_file = ResourceFile(source=lib)
            for keyword in resource_file.populate().keywords:
                if inner_keyword and inner_keyword.name == keyword:
                    point = get_point(inner_keyword)
                    break
            else:
                continue
            break
    return point


def get_keywords_map(sources):
    """
    Finds keywords grouped by base name
    Returns dictionary:
    {"KEYWORD_BASE_NAME": "KEYWORD_NAME_WITH_INDEX", WGS84_POINT, KEYWORD_INSTANCE}
    """
    keywords = defaultdict(list)
    for filename in glob.iglob(
            '{}/**/*.robot'.format(os.path.abspath(os.path.join(os.path.dirname(sources), "lib"))),
            recursive=True):
        base_filename = os.path.basename(filename)
        resource_file = ResourceFile(source=filename)
        for keyword in resource_file.populate().keywords:
            base_name = keyword.name[:keyword.name.rfind(" ")]
            point = get_point(keyword)
            if not keywords[base_name]:
                keywords[base_name] = [base_filename, list()]
            if not point:
                continue
            keywords[base_name][1].append((keyword.name, point, keyword))
    return keywords


def get_filtered_keywords(stats, test_case_map):
    modified_keywords = list()
    for tc_name, value in stats.items():
        if len(value[0]) * THRESHOLD > value[1]:
            if test_case_map.get(tc_name) is None:
                print("WARNING: cannot find test case: '{}'".format(tc_name))
                continue
            modified_keywords.append((test_case_map[tc_name], value[0]))
        else:
            # TODO: Send email or do something with the test cases that have a lot of failures
            pass
    return modified_keywords


def populate_keywords(filtered_keywords, covered_keywords, origin,
                      output_folder, keywords_map):
    print("Filtered keywords", filtered_keywords)
    for kw_name, _ in filtered_keywords:
        origin_point = get_origin_point(kw_name, covered_keywords[kw_name][-1], origin)
        print(keywords_map[kw_name])
        if not keywords_map[kw_name]:
            continue
        filename = os.path.join(output_folder, keywords_map[kw_name][0])
        result_lib_file = ResourceFile(filename)
        min_distance = None
        for dev_keyword in keywords_map[kw_name][1]:
            print(dev_keyword)
            print("Origin Point", origin_point)
            if not origin_point:
                continue
            distance = get_distance_between_two_points(dev_keyword[1],
                                                       origin_point)
            if min_distance is None or distance < min_distance[0]:
                min_distance = (distance, dev_keyword[2])
        print("min_distance", min_distance)
        if min_distance is None:
            continue
        new_keyword = deepcopy(min_distance[1])
        new_keyword.name = kw_name
        if os.path.exists(filename):
            existed_keywords = [keyword.name for keyword in result_lib_file.populate().keywords]
            print("Existed keywords: {}".format(existed_keywords))
            if new_keyword.name not in existed_keywords:
                print("{} exists and will populate with the new {} keyword".format(filename,
                                                                                   new_keyword))
                result_lib_file.populate().keywords.append(new_keyword)
            else:
                continue
        else:
            print("{} does not exist and "
                  "will append with the new {} keyword".format(filename, new_keyword))
            result_lib_file.keywords.append(new_keyword)
        print("Populated keyword: '{}' with the new location at a distance '{}'"
              " meters from the origin.".format(kw_name, int(min_distance[0])))
        result_lib_file.save()


def main():
    parser = ArgumentParser(description="Report analyzer.")
    parser.add_argument("-r", "--report", type=str, dest="report",
                        help="Path to xunit report.")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to source folder with robot test cases.")
    parser.add_argument("-o", "--origin", type=str, dest="origin",
                        help="Path to origin folder.")
    parser.add_argument("-f", "--output_folder", type=str, dest="output_folder",
                        help="Path to output folder with libs.")
    options = parser.parse_args()
    if os.path.exists(options.output_folder):
        shutil.rmtree(options.output_folder)
    create_folder(options.output_folder)
    # get statistic of passed/total test cases
    stats = parse_report(options.report)
    print("Test case stats:")
    print(stats)
    # get list of keywords that can be filled with MITF
    covered_keywords = collect()
    # dictionary mapping between keywords and test cases
    test_case_map = get_test_case_map(covered_keywords, options.origin)
    # get list of keywords that pass for all test cases
    filtered_keywords = get_filtered_keywords(stats, test_case_map)
    # get list of all keywords with wgs84 point that grouped by base keyword # name
    keywords_map = get_keywords_map(options.sources)
    # create lib folder with the most suitable keywords
    populate_keywords(filtered_keywords, covered_keywords, options.origin,
                      options.output_folder, keywords_map)


if __name__ == "__main__":
    main()
