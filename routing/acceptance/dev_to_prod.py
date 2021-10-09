import glob
import os
from argparse import ArgumentParser

from robot.api import TestData
from robot.parsing import TestCaseFile


def get_basename(name):
    if "." in name:
        name = name.split(".")[1]
    return " ".join(name.split(" ")[0:-1])


def get_unique_test_names(tc_table):
    filtered_tests = {}
    for tc in tc_table:
        if get_basename(tc.name) not in filtered_tests.keys():
            filtered_tests[get_basename(tc.name)] = tc.name

    return filtered_tests.values()


def remove_duplicates(sources):
    suites = glob.glob("%s/%s" % (os.path.join(sources, "international"), "**/dev_*.robot"), recursive=True)
    for suite in suites:
        parsed_data = TestData(source=suite)
        tc_table = parsed_data.testcase_table
        unique_test_names = get_unique_test_names(tc_table)

        base_dev_suite_name = os.path.basename(suite)
        base_suite_name = base_dev_suite_name.replace("dev_", "")
        suite_name = os.path.join(os.path.dirname(suite), base_suite_name)
        suite_file = TestCaseFile(source=suite_name)

        for test in tc_table:
            if test.name in unique_test_names:
                suite_file.testcase_table.tests.append(test)

        suite_file.setting_table = parsed_data.setting_table
        suite_file.variable_table = parsed_data.variable_table
        suite_file.keyword_table = parsed_data.keyword_table

        print("Saving updated file: %s" % (suite_name, ))
        suite_file.save()
        print("Deleting dev file: %s" % (suite, ))
        os.remove(suite)


def main():
    parser = ArgumentParser(description="Adjust development version of acceptance test source tree for production usage.")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)
    options = parser.parse_args()

    remove_duplicates(options.sources)

    # TODO (asmirnov): Next steps:
    # - delete keywords with unused indices from lib file
    # - rename used keywords by omitting index
    # - update 'remove_duplicates' to store test cases and keywords inside them w/o indices


if __name__ == "__main__":
    main()
