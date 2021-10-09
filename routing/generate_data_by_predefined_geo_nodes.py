"""
Run test_data_generator_runner and test_runner from predefined links
"""
import configparser
import json
import shutil
import subprocess
import tempfile
from argparse import ArgumentParser
from collections import defaultdict
from distutils.dir_util import copy_tree
from random import shuffle

import yaml


def generate_data(config, predefined_geo_nodes,
                  generators, investigation_list):
    """
    Executes test data generator with predefined links
    """
    suites = None
    with open(predefined_geo_nodes) as _file:
        suites = json.load(_file)
    config_parser = configparser.ConfigParser()
    config_parser.read(config)
    test_data_folder = ""
    for suite in suites:
        sgn_generator = "%sTestDataGenerator" % suite[:-9]
        if not generators:
            generators = config_parser["GeneratorSection"]["generators"]
        if generators:
            config_tokens = map(lambda a: a.strip(), generators.split(","))
            if sgn_generator not in config_tokens:
                continue
        sgn_geo_nodes = suites[suite]
        sgn_geo_param = ""
        for (item_name, nodes) in sgn_geo_nodes.items():
            if investigation_list[item_name]["skip_all"] is True:
                continue
            filtered_nodes = list()
            for node in nodes:
                if node in investigation_list[item_name]["geo_nodes"]:
                    continue
                filtered_nodes.append(node)
            if len(filtered_nodes) == 0:
                continue
            shuffle(filtered_nodes)
            sgn_geo_param = "%s;%s" % (
                sgn_geo_param, "%s:%s" % (item_name, ";".join(filtered_nodes)))
        if len(sgn_geo_param) == 0:
            continue
        out = tempfile.mktemp()
        if len(test_data_folder) == 0:
            test_data_folder = tempfile.mktemp()
        try:
            command = "python3 test_data_generator_runner/run.py" \
                      " --output_folder %s --loglevel DEBUG --config %s --generators %s" \
                      " --geo_nodes \"%s\"" % (out, config, sgn_generator, sgn_geo_param)
            print(command)
            p = subprocess.Popen(command, shell=True)
            p.wait()
            copy_tree(out, test_data_folder)
        finally:
            shutil.rmtree(out)

    if len(test_data_folder) == 0:
        print("WARNING: empty generated data folder")
    else:
        print("Folder with generated data: '%s'" % test_data_folder)
    print("Data generation is done!")
    return test_data_folder


def generate_xmls(config, data_folder, out_folder):
    """
    Executes test runner
    """
    try:
        command = "python3 test_runner/run.py --loglevel DEBUG " \
                  "--result_output_folder %s " \
                  "--test_data_path %s --config %s " % (out_folder, data_folder, config)
        print(command)
        p = subprocess.Popen(command, shell=True)
        p.wait()
    finally:
        shutil.rmtree(data_folder)
    print("Folder with generated XMLs: ", out_folder)
    print("XML generation is done!")


def create_investigation_list(file_path):
    investigation_list = defaultdict(lambda: {"geo_nodes": list(), "skip_all": False})
    if len(file_path) == 0:
        print("WARN: investigation list will not be used in further processing")
        return investigation_list
    with open(file_path, "r", encoding="utf-8") as fd:
        for test_items in list(test_item for test_item in yaml.load_all(fd)):
            for item, token in test_items.items():
                if isinstance(token, str):
                    # wildcard * - skip all geo_nodes related to the current item.
                    if token.strip() == "*":
                        investigation_list[item] = {"skip_all": True, "geo_nodes": list()}
                    # parse geo_nodes list.
                    else:
                        investigation_list[item] = {"skip_all": False,
                                                    "geo_nodes": list(set(token.split(";")))}
                else:
                    print("Warning: investigation list parser: accept only string format")
                    investigation_list[item] = {"skip_all": False, "geo_nodes": list()}
    return investigation_list


def main():
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--config", dest="config",
                            help="Config file", required=True)
    opt_parser.add_argument("--predefined_geo_nodes", dest="predefined_geo_nodes",
                            help="Json file with predefined geographical nodes", required=True)
    opt_parser.add_argument("--output", dest="output", help="Path to folder with generated files",
                            required=True)
    opt_parser.add_argument("--generate_xml", dest="generate_xml", action='store_false',
                            help="Whether to generate xml test files or not")
    opt_parser.add_argument("--generators", dest="generators", default="",
                            type=str,
                            help="Comma-separated list of generators to run.")
    opt_parser.add_argument("--investigation_list", dest="investigation_list", default="",
                            type=str,
                            help="Investigation list yaml file")
    options = opt_parser.parse_args()
    investigation_list = create_investigation_list(options.investigation_list)
    generator_folder = generate_data(options.config,
                                     options.predefined_geo_nodes,
                                     options.generators,
                                     investigation_list)

    if len(generator_folder) == 0:
        return
    if options.generate_xml:
        generate_xmls(options.config, generator_folder, options.output)
    else:
        shutil.move(generator_folder, options.output)


if __name__ == "__main__":
    main()
