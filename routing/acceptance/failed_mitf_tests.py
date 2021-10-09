import os
from argparse import ArgumentParser
from collections import defaultdict

from lxml import etree
from robot.api import TestData

from utils.acceptance_tests import collect


def parse_detailed_report(root, covered_keywords):
    # for execution of several suites
    suites = [root.find("suite")]
    suites.extend(suites[-1].findall("suite"))
    failed_keywords = set()
    for suite in suites:
        source = suite.get("source")
        # remove path to international/car
        if not source:
            continue
        source = source[source.find("international") + 14:]
        for test_case in suite.iter("test"):
            print(test_case.get("name"))
            st_tag = test_case.find("status")
            status = st_tag.get("status")
            if status == "FAIL":
                for step in test_case.findall("kw"):
                    if (step.get("name") in
                            covered_keywords and source in
                            covered_keywords[step.get("name")]):
                        failed_keywords.add(step.get("name"))
    return failed_keywords


def parse_brief_report(root, covered_keywords, sources):
    test_case_keywords_map = defaultdict(set)
    # Iterate through already covered cases
    for keyword, libs in covered_keywords.items():
        print(keyword, libs)
        for lib in libs:
            parsed_suite = TestData(source=os.path.join(sources, lib))
            for _test_case in parsed_suite.testcase_table:
                _steps = [step.name for step in _test_case.steps]
                for _keyword in parsed_suite.keyword_table:
                    if keyword == _keyword.name and keyword in _steps:
                        test_case_keywords_map[_test_case.name].add(keyword)
    failed_keywords, failed_test_cases = set(), set()
    # Iterate through failed test cases from the given xUnit report
    print("INFO: Getting failed test cases from [{}] xUnit Report".format(root.docinfo.URL))
    print("INFO: [{}] fail(s) and [{}] error(s) detected by "
          "RobotFrameWork of [{}] tests".format(root.getroot().attrib["failures"],
                                                root.getroot().attrib["errors"],
                                                root.getroot().attrib["tests"]))
    for fail in root.iter("failure"):
        failed_test_case = fail.getparent().get("name")
        if failed_test_case in test_case_keywords_map:
            failed_keyword = ", ".join(test_case_keywords_map[failed_test_case])
            print("INFO: Failed [{}] test case is covered by MITF "
                  "on [{}] keyword".format(failed_test_case, failed_keyword))
            failed_test_cases.add(failed_test_case), failed_keywords.add(failed_keyword)
        else:
            print("WARN: Failing [{}] test case IS NOT covered by MITF".format(failed_test_case))
    return list(failed_keywords)


def parse_xunit(report, sources):
    root = etree.parse(report)
    # for one test suite
    covered_keywords = collect()
    if root.find("suite"):
        failed_test_cases = parse_detailed_report(root, covered_keywords)
    else:
        failed_test_cases = parse_brief_report(root, covered_keywords, sources)
    return failed_test_cases


def main():
    parser = ArgumentParser(description="Filter partitions ids.")
    parser.add_argument("-r", "--report", type=str, dest="report", required=True,
                        help="Path to xunit report.")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources.")
    options = parser.parse_args()
    failed_keywords = parse_xunit(options.report, options.sources)
    if not failed_keywords:
        print("WARN: There are not failing test cases covered by MITF")
    else:
        with open("failed_keywords.txt", "w") as outfile:
            outfile.writelines("\n".join(failed_keywords))


if __name__ == "__main__":
    main()
