import glob
import os
from argparse import ArgumentParser
from robot.api import TestData
from collections import defaultdict
from utils.acceptance_tests import get_keywords_dep


def check_for_existing_keywords(sources):
    base_path = os.path.abspath(sources)
    path_to_lib_folder = os.path.join(os.path.dirname(base_path), "lib")
    existing_keywords = defaultdict(list)
    for filename in glob.iglob('{}/**/*.robot'.format(path_to_lib_folder), recursive=True):
        keywords = get_keywords_dep(filename)
        for keyword, suites in keywords.items():
            for suite in suites:
                parsed_suite = TestData(source=os.path.join(sources, suite))
                for tc_keyword in parsed_suite.keyword_table.keywords:
                    if tc_keyword.name == keyword:
                        existing_keywords[keyword].append(suite)
                        break
    return existing_keywords


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)
    options = parser.parse_args()
    existing_keywords = check_for_existing_keywords(options.sources)
    if existing_keywords:
        for keyword, suites in existing_keywords.items():
            print("Keyword '{}' exists in the following test suite(s):".format(keyword))
            for suite in suites:
                print("\t{}".format(suite))


if __name__ == "__main__":
    main()
