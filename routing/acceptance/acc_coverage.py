"""
Calculates number of covered test cases.
Example:
$ python3 acc_coverage.py -t PATH/map-integration-testing/tests/acceptance/templates/ \
-s PATH/share/spec/international/

"""
import glob
import os
from argparse import ArgumentParser
from robot.api import ResourceFile, TestCaseFile
from collections import defaultdict


def get_keywords_map(template_folder):
    key_map = defaultdict(list)
    for filename in glob.glob(template_folder + "**/*.robot", recursive=True):
        file_ = os.path.join(template_folder, filename)
        resource_file = ResourceFile(source=file_)
        for keyword in resource_file.populate().keywords:
            for step in keyword.steps:
                for l in step.as_list():
                    if l.startswith("# @file:"):
                        key_map[l[8:].strip()].append(keyword.name)
    return key_map


def parse_sources(key_map, source_folder):
    counter = 0
    tags = defaultdict(int)
    for file_, keywords in key_map.items():
        for keyword in keywords:
            test_file = TestCaseFile(source=os.path.join(source_folder, file_))
            try:
                for test_case in test_file.populate().testcase_table:
                    for step in test_case.steps:
                        if keyword == step.name:
                            counter += 1
                            for tag in test_case.tags.as_list():
                                tags[tag] += 1
                            print(file_, " ", keyword, " ", test_case.name)
                            break
            except Exception as err:
                print(err)
    return counter, tags


def main():
    parser = ArgumentParser(description="Get coverage report out of full xunit report")
    parser.add_argument("-t", "--templates", type=str, dest="templates",
                        help="Path to MITF's templates",
                        required=True)
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources (including \"international\" dir)",
                        required=True)
    options = parser.parse_args()
    keyword_map = get_keywords_map(options.templates)
    counter, tags = parse_sources(keyword_map, options.sources)
    print("Total: ", counter)
    print("Tags: ", tags)


if __name__ == "__main__":
    main()
