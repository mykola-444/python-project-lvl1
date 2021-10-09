#!/usr/bin/python
import configparser
import os
import re
import fnmatch
import importlib
import inspect

from argparse import ArgumentParser
from collections import defaultdict

from tests.base_test_suite import parse_test_data
from generate_xml_coverage import create_report
from robot.parsing import ResourceFile


def get_point(kwd):
    for step in kwd.steps:
        if step.name is None:
            continue
        if step.name.startswith("Provided geo stop waypoint"):
            coordinates = re.findall(r"at\((.*?)\)", step.args[0])
            if not coordinates:
                return None
            return [float(i.strip()) for i in coordinates[0].split(",")]


def get_keywords_data():
    path_to_template = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tests/acceptance/templates"))
    keyword_data = defaultdict(list)
    for root, _, files in os.walk(path_to_template):
        for _file in files:
            if not _file.endswith(".robot"):
                continue
            path = os.path.join(root, _file)
            result_lib_file = ResourceFile(source=path)
            for gen_kwd in result_lib_file.populate().keyword_table.keywords:
                if gen_kwd.name[0].islower():
                    print("DEBUG: Skipped keyword: {}".format(gen_kwd.name))
                    continue
                keyword_data[os.path.splitext(_file)[0]].append(gen_kwd.name)
    return keyword_data


def get_test_items(config):
    generators = config["GeneratorSection"]["GENERATORS"].split(",")
    result = list()
    for root, _, files in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                               "../../tests"))):
        folder_name = os.path.basename(root)
        for _file in files:
            if not _file.endswith(".py"):
                continue
            if _file.startswith("__") or "base_test_suite" in _file:
                continue
            module_path = "tests.%s.%s" % \
                (folder_name, _file[:-3])
            try:
                module = __import__(module_path)
            except ImportError as err:
                print("ERROR: %s" % err)
                continue
            for suite in dir(getattr(getattr(module, folder_name),
                                     _file[:-3])):
                module = importlib.import_module(module_path)
                if hasattr(module, "gen"):
                    generator = module.gen.__name__
                elif hasattr(module, "acc_gen"):
                    generator = module.acc_gen.__name__
                else:
                    continue
                # TODO: Remove the acceptance tests filtering
                if (generator not in generators or not
                        suite.startswith("Acceptance") or suite.startswith("AcceptanceBase")):
                    continue
                for item in inspect.getmembers(getattr(module, suite)):
                    if (item[0].startswith("test") and item[0] not in
                            ("test_tear_down", "test_set_up")):
                        try:
                            res = parse_test_data(inspect.getsource(item[1]))
                        except IndexError:
                            continue
                        result.append(res[0])
    return result


def get_robot_data(path_to_robot_libs, config):
    matches = defaultdict(dict)
    for root, _, filenames in os.walk(path_to_robot_libs):
        for filename in fnmatch.filter(filenames, '*.robot'):
            path = os.path.join(root, filename)
            result_lib_file = ResourceFile(source=path)
            lib_name = os.path.splitext(filename)[0]
            for gen_kwd in result_lib_file.populate().keyword_table.keywords:
                kwd_name = gen_kwd.name[:gen_kwd.name.rfind(" ")]
                if kwd_name[0].islower():
                    continue
                if not matches[lib_name].get(kwd_name):
                    matches[lib_name][kwd_name] = list()

                point = get_point(gen_kwd)
                if not point:
                    continue
                matches[lib_name][kwd_name].append((point[1], point[0]))

    expected = get_test_items(config)
    keywords_data = get_keywords_data()
    result = dict()
    for item in expected:
        for keyword in keywords_data[item]:
            result[os.path.join(item, keyword)] = list()
        if item in matches:
            for keyword in matches[item]:
                if keyword in matches[item]:
                    result[os.path.join(item, keyword)] = matches[item][keyword]
    return result


def main():
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--config", dest="config",
                            help="Path to configuration file", type=str)
    opt_parser.add_argument("--path_to_robot_libs", dest="path_to_robot_libs",
                            help="Path to folder with robot framework libs",
                            default="", required=True)
    opt_parser.add_argument("--template", dest="template",
                            help="Path to Jinja template")
    opt_parser.add_argument("--output", dest="output",
                            help="HTML page with links to RefClient",
                            default="index.html")
    options = opt_parser.parse_args()
    print("Creating URLs...")
    config = configparser.ConfigParser()
    config.read(options.config)

    data = get_robot_data(options.path_to_robot_libs, config)
    print("Generating report...")
    create_report(options.template, options.output, data, config)
    print("Created report: %s" % options.output)


if __name__ == "__main__":
    main()
