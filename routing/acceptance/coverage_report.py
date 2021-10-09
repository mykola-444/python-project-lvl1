import importlib
import json
import fnmatch
import os
import re
from lxml import etree
from argparse import ArgumentParser
from utils.acceptance_tests import collect
from test_data_generator_runner.run import get_available_generators, get_test_items


def find_child_rec(node, element):
    for item in node.findall(element):
        yield item
        for child in find_child_rec(item, element):
            yield child


def get_item_name(keyword_name, path_to_libs):
    for root, _, filenames in os.walk(path_to_libs):
        for filename in fnmatch.filter(filenames, '*.robot'):
            path_to_lib = os.path.join(root, filename)
            with open(path_to_lib, "r", encoding="utf-8") as _f:
                found = False
                for line in _f:
                    if not line.startswith("#"):
                        keywords = re.findall(r'^([a-zA-Z].*)', line)
                        if keywords:
                            # for this particular coverage report
                            key = keywords[0].replace(" 0", "")
                            if key == keyword_name:
                                found = True
                    if found:
                        item_name = re.findall(r'@item_name: +(.*)', line)
                        if item_name:
                            return item_name[0]
    return None


def get_generator_name(item_name):
    generators = get_available_generators()
    for parent in generators:
        if not generators[parent]:
            continue
        classes = generators[parent].keys()
        for generator in sorted(classes):
            module = importlib.import_module(generators[parent][generator])
            test_items = get_test_items(module, generator)
            if test_items is None:
                continue
            for test_item in sorted(test_items):
                if test_item == item_name:
                    return generator

    return None


def parse_detailed_report(root, covered_keywords):
    suites = list(find_child_rec(root, "suite"))
    covered_tests = dict()
    errors = list()
    for suite in suites:
        if not suite.get("source").endswith(".robot"):
            continue
        source = suite.get("source")
        if not source:
            continue
        # Shorten path to international/car:
        source = source[source.find("international") + 14:]
        src_path, src_file = os.path.dirname(source), os.path.basename(source)
        # This job is supposed to use report from dev pipeline as an input:
        if src_file.startswith("dev_"):
            source = os.path.join(src_path, src_file[4:])
        for test_case in suite.iter("test"):
            test_name = test_case.get("name")
            # This job will use the first test of each kind to collect statistics:
            if test_name.endswith(" 0"):
                test_name = test_name[:-2]
            else:
                continue
            st_tag = test_case.find("status")
            status = st_tag.get("status")
            # Check if this verification might be safely ommitted:
            if status:
                for step in test_case.findall("kw"):
                    step_name = step.get("name")
                    # See comment above to understand this verification:
                    if step_name.endswith(" 0"):
                        step_name = step_name[:-2]
                    if step_name in covered_keywords:
                        suite_full_path = \
                            ".".join(list(reversed(
                                [ancestor.get("name") for ancestor in suite.iterancestors()][:-1])))
                        suite_name = suite.get("name")
                        if suite_name.startswith("Dev "):
                            suite_name = suite_name.replace("Dev ", "")
                        suite_full_path = ".".join([suite_full_path, suite_name])
                        test_full_path = "%s.%s" % (suite_full_path, test_name)
                        try:
                            covered_tests[step_name].append(test_full_path)
                        except KeyError:
                            covered_tests[step_name] = [test_full_path, ]
                        if source not in covered_keywords[step_name]:
                            errors.append((step_name, source))

    return covered_tests, errors


def parse_xunit(report, sources):
    covered_data = dict()
    errors = {"No generator for item": [],
              "No item_name for keyword": []}

    root = etree.parse(report)
    covered_keywords = collect()

    test_by_kwd, errors["Expected source is missing"] = \
        parse_detailed_report(root, covered_keywords)

    for cov_kwd in test_by_kwd:
        item_name = get_item_name(cov_kwd, os.path.join(sources, "..", "lib"))
        if not item_name:
            errors["No item_name for keyword"].append(cov_kwd)
            continue
        generator = get_generator_name(item_name)
        if not generator:
            errors["No generator for item"].append(item_name)
            continue
        try:
            for item in test_by_kwd[cov_kwd]:
                covered_data[generator][item_name].append(item)
        except KeyError:
            try:
                covered_data[generator][item_name] = test_by_kwd[cov_kwd]
            except KeyError:
                covered_data[generator] = {item_name: test_by_kwd[cov_kwd]}

    return covered_data, errors


def main():
    parser = ArgumentParser(description="Get coverage report out of full xunit report")
    parser.add_argument("-r", "--report", type=str, dest="report",
                        help="Path to _full_ xunit report of acceptance tests",
                        required=True, action='append', nargs='+')
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources (including \"international\" dir)",
                        required=True)
    parser.add_argument("-o", "--output_dir", type=str, dest="output",
                        help="Path to output reports", required=True)
    options = parser.parse_args()
    for report in options.report:
        coverage_data, errors = parse_xunit(report[0], options.sources)
        # TODO (asmirnov): Implement multiple report processing.

    num_of_cover_tests = int()
    for item in coverage_data:
        for cov_tsts in coverage_data[item]:
            num_of_cover_tests += len(coverage_data[item][cov_tsts])
    print("Number of covered tests:", num_of_cover_tests)
    with open(os.path.join(options.output, "coverage.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(coverage_data, indent=4))
    with open(os.path.join(options.output, "errors.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(errors, indent=4))
    exit_code = 0
    for error_type in errors:
        if errors[error_type]:
            exit_code = 1
    exit(exit_code)


if __name__ == "__main__":
    main()
