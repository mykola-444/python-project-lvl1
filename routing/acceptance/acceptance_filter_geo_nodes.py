import os
import json
from argparse import ArgumentParser
from lxml import etree
from robot.api import TestData, ResourceFile
from collections import defaultdict
from acceptance_tests_updater_dev import get_geo_node_from_keyword


def get_tc_name(tc_name):
    """
    Takes test case name and remove number in the end if the number exists
    """
    return tc_name[:tc_name.rfind(" ")] if tc_name[-1].isdigit() else tc_name


def get_geo_nodes(source):
    """
    Parses test case's resources and returns dictionary with test cases and geo nodes.
    """
    suite_file = TestData(source=source)
    keywords = dict()
    for resource in suite_file.imports:
        if "setup.robot" in resource.name:
            continue
        lib = os.path.abspath(os.path.join(os.path.dirname(source), resource.name.strip()))
        resource_file = ResourceFile(source=lib)
        for keyword in resource_file.populate().keywords:
            geo_node, item_name = get_geo_node_from_keyword(keyword)
            if geo_node is None:
                continue
            keywords[keyword.name] = geo_node, item_name
    # Find test cases which contain generated keywords:
    test_cases = defaultdict(list)
    for test in suite_file.testcase_table:
        for step in test.steps:
            if step.name in keywords:
                test_cases[test.name] = keywords[step.name]
    return test_cases


def parse_xunit(report):
    """
    Parses xunit report and returns passed and failed test cases.
    """
    passed = dict()
    failed = dict()
    with open(report, encoding="utf-8") as fobj:
        xml = fobj.read()
    root = etree.fromstring(xml.encode("utf8"))
    # for one test suite
    suites = list()
    for suite in root.iter("suite"):
        suites.append(suite)
    counter = 0
    for suite in suites:
        source = suite.get("source")
        if not source:
            continue
        geo_nodes = get_geo_nodes(source)
        for test_case in suite.iter("test"):
            tc_name = get_tc_name(test_case.get("name"))
            if test_case.get("name") in geo_nodes:
                st_tag = test_case.find("status")
                status = st_tag.get("status")
                if status == "PASS":
                    if geo_nodes[test_case.get("name")][1] not in passed:
                        passed[geo_nodes[test_case.get("name")][1]] = defaultdict(list)
                    counter += 1
                    passed[geo_nodes[test_case.get("name")][1]][tc_name].append(geo_nodes[test_case.get("name")][0])
                else:
                    if geo_nodes[test_case.get("name")][1] not in failed:
                        failed[geo_nodes[test_case.get("name")][1]] = defaultdict(list)
                    failed[geo_nodes[test_case.get("name")][1]][tc_name].append(geo_nodes[test_case.get("name")][0])
    return passed, failed


def dict_to_json_file(data, file_path):
    print("Created file: {}".format(os.path.abspath(file_path)))
    with open(file_path, "w", encoding="utf-8") as f_:
        json.dump(data, f_)


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-r", "--report", type=str, dest="report",
                        help="Path to xunit report.")
    parser.add_argument("-p", "--passed", type=str, dest="passed",
                        default="pass.json",
                        help="Passed test cases")
    parser.add_argument("-f", "--failed", type=str, dest="failed",
                        default="fail.json",
                        help="Failed test cases")
    options = parser.parse_args()
    passed, failed = parse_xunit(options.report)
    dict_to_json_file(passed, options.passed)
    dict_to_json_file(failed, options.failed)


if __name__ == "__main__":
    main()
