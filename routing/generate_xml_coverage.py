#!/usr/bin/python
import configparser
import jinja2
import os
import re
import fnmatch
import importlib
import inspect

from argparse import ArgumentParser
from collections import defaultdict

from utils.web.ref_client import get_visualization_points_url
from tests.base_test_suite import parse_test_data


def get_test_items(config):
    generators = config["GeneratorSection"]["GENERATORS"].split(",")
    result = list()
    for root, _, files in os.walk("tests"):
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
                if not hasattr(module, "gen"):
                    continue
                generator = module.gen.__name__
                # TODO: Remove the acceptance tests filtering
                if (generator not in generators or suite.startswith("Acceptance")):
                    continue
                for item in inspect.getmembers(getattr(module, suite)):
                    if (item[0].startswith("test") and item[0] not in
                            ("test_tear_down", "test_set_up")):
                        try:
                            res = parse_test_data(inspect.getsource(item[1]))
                        except IndexError:
                            continue
                        result.append(res[2])
    return result


def get_xml_data(path_to_xmls, config):
    matches = defaultdict(list)
    for root, dirnames, filenames in os.walk(path_to_xmls):
        for filename in fnmatch.filter(filenames, '*.xml'):
            path = os.path.join(root, filename)
            with open(path, "r") as _f:
                content = _f.read()
                lngs = re.findall('lng="(.*?)"', content)
                lats = re.findall('lat="(.*?)"', content)
                if not lngs or not lats:
                    continue
                matches[path[path.find("test"):path.rfind("_")]].append((lngs[0], lats[0]))
    expected = get_test_items(config)
    for item in expected:
        if item not in matches:
            matches[item] = []
    return matches


def get_urls(suites, config):
    data = dict()

    for suite in suites:
        keys = suite.split("/")
        root = data
        last = keys[-1]
        for key in keys:
            if key in root:
                root = root[key]
            elif key == last:
                url = get_visualization_points_url(suites[suite])
                root[keys[-1]] = (len(suites[suite]), url)
            else:
                root[key] = dict()
                root = root[key]
    return data


def create_report(template, output, data, config):
    abs_path = os.path.abspath(template)
    name = abs_path.split("/")[-1]
    path = abs_path[:-len(name)]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
    environment = {"LDM_REGION_DVN": os.environ.get("LDM_REGION_DVN"),
                   "BUILD_URL": os.environ.get("BUILD_URL"),
                   }
    urls = get_urls(data, config)
    res_html = env.get_template(name).render(items=urls,
                                             tcn=config["GeneratorSection"]["TEST_CASE_NUMBER"],
                                             sorted=sorted,
                                             int=int,
                                             dict=dict,
                                             isinstance=isinstance,
                                             environment=environment)
    with open(output, "w") as fh:
        fh.write(res_html)


def main():
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--config", dest="config",
                            help="Path to configuration file", type=str)
    opt_parser.add_argument("--path_to_xmls", dest="path_to_xmls",
                            help="Path to folder with xmls",
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

    data = get_xml_data(options.path_to_xmls, config)
    print("Generating report...")
    create_report(options.template, options.output, data, config)
    print("Created report: %s" % options.output)


if __name__ == "__main__":
    main()
