#!/usr/bin/python
import configparser
import glob
import jinja2
import json
import os

import _pickle as pickle

from argparse import ArgumentParser
from collections import defaultdict

from utils.web.ref_client import get_ref_client_url


def get_test_data(test_data_path, config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    app_code = config["GeneratorSection"]["REF_APP_CODE"]
    app_id = config["GeneratorSection"]["REF_APP_ID"]
    data = defaultdict(list)
    test_data_files = glob.glob(os.path.join(test_data_path, "*"))
    for test_data_file in test_data_files:
        if not os.path.isfile(test_data_file):
            continue
        _file = open(test_data_file, "rb")
        try:
            content = _file.read()
            if test_data_file.endswith("json"):
                f_data = json.loads(content)
            elif test_data_file.endswith("dump"):
                f_data = pickle.loads(content)
            else:
                print("WARNING: Undetermined input data file: '%s'" %
                      test_data_file)
                continue
        except Exception as err:
            print("WARNING: %s" % err)
        finally:
            _file.close()
        try:
            url = get_ref_client_url(app_code, app_id, **f_data)
            f_name = test_data_file.split("/")[-1].split(".")[0]
            data[f_data["debug_data"]["item_name"]].append((f_name, url))
        except Exception as err:
            print("WARNING: %s" % err)
    return data


def create_report(template, output, data):
    abs_path = os.path.abspath(template)
    name = abs_path.split("/")[-1]
    path = abs_path[:-len(name)]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
    environment = {"LDM_REGION_DVN": os.environ.get("LDM_REGION_DVN"),
                   "BUILD_URL": os.environ.get("BUILD_URL"),
                   }
    res_html = env.get_template(name).render(items=data,
                                             sorted=sorted,
                                             environment=environment)
    with open(output, "w") as fh:
        fh.write(res_html)


def main():
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--config", dest="config",
                            help="Path to configuration file", type=str)
    opt_parser.add_argument("--test_data_path", dest="test_data_path",
                            help="Path to folder with generated test data (dump files)",
                            default="", required=True)
    opt_parser.add_argument("--template", dest="template",
                            help="Path to Jinja template")
    opt_parser.add_argument("--output", dest="output",
                            help="HTML page with links to RefClient",
                            default="index.html")
    options = opt_parser.parse_args()
    print("Creating URLs...")
    data = get_test_data(options.test_data_path, options.config)
    print("Generating report...")
    create_report(options.template, options.output, data)
    print("Created report: %s" % options.output)


if __name__ == "__main__":
    main()
