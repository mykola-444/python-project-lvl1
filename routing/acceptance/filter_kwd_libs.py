import glob
import os
import json
import errno
import shutil
import random
from argparse import ArgumentParser
from robot.api import TestData, ResourceFile
from collections import defaultdict
from copy import deepcopy
from acceptance_tests_updater_dev import get_geo_node_from_keyword
from utils.acceptance_tests import get_keywords_dep, collect


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


def get_keywords(lib, filetered_keywords, sources, geo_nodes):
    keywords = defaultdict(list)
    for filename in glob.glob("%s%s" % (lib, '*.*')):
        file_ = os.path.join(lib, filename)
        resource_file = ResourceFile(source=file_)
        for keyword in resource_file.populate().keywords:
            geo_node = get_geo_node_from_keyword(keyword)
            keywords[keyword.name].append((geo_node, keyword))
    return keywords


def get_test_cases_map(lib, keywords, sources, geo_nodes):
    keywords = get_keywords_dep(glob.glob("%s%s" % (lib, '*.*'))[0])
    test_cases_map = defaultdict(list)
    for keyword_name, suites in keywords.items():
        for suite in suites:
            parsed_suite = TestData(source=os.path.join(sources, suite))
            for test_case in parsed_suite.testcase_table.tests:
                for step in test_case.steps:
                    if step.name in keywords:
                        test_cases_map[keyword_name].append(test_case.name)
                        break
    return test_cases_map


def create_folder(path_to_folder):
    try:
        os.makedirs(path_to_folder)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def optimize_keywords(result_lib_files):
    keyword_map_data = set()
    covered_keywords = collect().keys()
    for keyword in result_lib_files.keyword_table.keywords:
        keyword_map_data.add(keyword.name)
    unsupported_keywords = list()
    for keyword in result_lib_files.keyword_table.keywords:
        for step in keyword.steps:
            for arg in step.as_list():
                if arg in covered_keywords and arg not in keyword_map_data:
                    unsupported_keywords.append(keyword)
                    break

    for keyword in unsupported_keywords:
        result_lib_files.keyword_table.keywords.remove(keyword)


def create_kwd_libs(lib, keywords, test_cases_map, geo_nodes_file, output):
    lib_name = os.path.basename(lib)
    with open(geo_nodes_file, encoding="utf-8") as f_:
        geo_nodes = json.load(f_)
    test_cases = dict()
    for item_name, values in geo_nodes.items():
        test_cases.update(values)
    counter = 0
    # Get all geo locations
    uniq_geo_nodes = list()
    total = 0
    for instances in keywords.values():
        total += len(instances)
        for nodes in instances:
            if nodes[0][0] not in uniq_geo_nodes:
                uniq_geo_nodes.append(nodes[0][0])
    uniq_geo_nodes_size = len(uniq_geo_nodes)
    while counter < total:
        filename = os.path.abspath(os.path.join(output,
                                                "{}_{}.robot".format(lib_name,
                                                                     counter)))
        result_lib_file = ResourceFile(filename)
        for keyword_name, instances in keywords.items():
            if not(set(test_cases_map[keyword_name]).issubset(set(test_cases.keys()))):
                continue
            geo_nodes = dict()
            # filter only geo locations that pass/fail for all keywords
            for (geo_node, keyword) in instances:
                if all(geo_node[0] in test_cases[i] for i in
                       test_cases_map[keyword_name] if test_cases.get(i)):
                    geo_nodes[geo_node[0]] = keyword
            else:
                if not geo_nodes and (geo_node, keyword) in instances:
                    instances.remove((geo_node, keyword))
                    continue
            # Check that this is a new geo location
            for node_id in uniq_geo_nodes[:]:
                if geo_nodes.get(node_id):
                    new_keyword = deepcopy(geo_nodes[node_id])
                    uniq_geo_nodes.remove(node_id)
                    break
            else:
                if not geo_nodes:
                    break
                random_index = random.SystemRandom()
                new_keyword = geo_nodes[random_index.choice(list(geo_nodes.keys()))]
            result_lib_file.keyword_table.keywords.append(new_keyword)
            instances.remove((geo_node, keyword))
        optimize_keywords(result_lib_file)
        result_lib_file.save()
        # check geo_nodes list was changed
        if uniq_geo_nodes_size != len(uniq_geo_nodes):
            uniq_geo_nodes_size = len(uniq_geo_nodes)
        else:
            break
        print("Created keyword lib: '{}'".format(filename))
        counter += 1


def get_libs(path_to_libs):
    libs = dict()
    for filename in glob.iglob('{}/**/*.robot'.format(path_to_libs), recursive=True):
        libs[filename[:filename.rfind("_")]] = os.path.basename(os.path.dirname(filename))
    return libs


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-l", "--lib", type=str, dest="lib",
                        help="Path/(or prefix in dev mode) to file with keywords", required=True)
    parser.add_argument("-k", "--keywords", type=str, dest="keywords",
                        help="List with keywords that should be updated. If the option is not specified "
                             "all keywords will be updated.")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)

    parser.add_argument("-g", "--geo_nodes", type=str, dest="geo_nodes",
                        help="Path to json file with geo_nodes")
    parser.add_argument("-o", "--output", type=str, dest="output", help="Output folder")
    options = parser.parse_args()
    libs = get_libs(options.lib)
    output = os.path.abspath(options.output)
    if os.path.exists(output):
        shutil.rmtree(output)
    create_folder(output)

    for lib, folder_name in libs.items():
        path_to_folder = os.path.join(output, folder_name)
        if not os.path.exists(path_to_folder):
            create_folder(path_to_folder)
        keywords = get_keywords(lib, options.keywords, options.sources,
                                options.geo_nodes)
        test_cases_map = get_test_cases_map(lib, keywords.keys(), options.sources,
                                            options.geo_nodes)
        create_kwd_libs(lib, keywords, test_cases_map, options.geo_nodes,
                        path_to_folder)


if __name__ == "__main__":
    main()
