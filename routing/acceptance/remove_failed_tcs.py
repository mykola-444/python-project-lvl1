import os
from lxml import etree
from argparse import ArgumentParser
from robot.api import TestData
from robot.parsing import TestCaseFile


def find_child_rec(node, element):
    for item in node.findall(element):
        yield item
        for child in find_child_rec(item, element):
            yield child


def parse_xunit_report(report):
    root = etree.parse(report)
    suites = list(find_child_rec(root, "suite"))
    failed_tests = list()
    for suite in suites:
        if not suite.get("source").endswith(".robot"):
            continue
        source = suite.get("source")
        if not source:
            continue
        for test_case in suite.iter("test"):
            st_tag = test_case.find("status")
            if st_tag.get("status") == "FAIL":
                failed_tests.append((test_case.get("name"), source))

    return (failed_tests)


def update_sources(failed_tests, actual_src_prefix):
    for failed_test, failed_source in failed_tests:
        report_src_prefix = failed_source.partition("/spec/")[0] + "/spec/"
        source_path = failed_source.replace(report_src_prefix, actual_src_prefix)
        # Check that replace operation has succeeded:
        if actual_src_prefix not in source_path:
            continue
        try:
            parsed_data = TestData(source=source_path)
        except Exception as err:
            print("Skipping %s processing: %s" % (source_path, err))
            continue
        base_dev_suite_name = os.path.basename(source_path)
        if not base_dev_suite_name.startswith("dev_"):
            print("Skipping %s since it's not MITF generated stuff" % (base_dev_suite_name, ))
            continue
        dev_suite_name = os.path.join(os.path.dirname(source_path),
                                      "tmp_%s" % (base_dev_suite_name, ))
        dev_suite_file = TestCaseFile(source=dev_suite_name)
        tc_table = parsed_data.testcase_table
        for test in tc_table:
            if test.name == failed_test and source_path == test.source:
                print("Removing failed test: %s" % (test.name, ))
            else:
                dev_suite_file.testcase_table.tests.append(test)

        dev_suite_file.setting_table = parsed_data.setting_table
        dev_suite_file.variable_table = parsed_data.variable_table
        dev_suite_file.keyword_table = parsed_data.keyword_table

        dev_suite_file.save()
        os.rename(dev_suite_name, source_path)
        print("Saving updated file: %s" % (source_path, ))


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-r", "--report", type=str, dest="report",
                        help="Path to xunit report. Option can be specified multiple times",
                        required=True, action='append', nargs='+')
    parser.add_argument("-a", "--actual-src-prefix", type=str, dest="actual_prefix",
                        help="Path to \"spec\" folder in source tree.", required=True)
    options = parser.parse_args()

    for report in options.report:
        print("Processing file %s" % (report[0], ))
        failed_tcs = parse_xunit_report(report[0])
        update_sources(failed_tcs, options.actual_prefix)


if __name__ == "__main__":
    main()
