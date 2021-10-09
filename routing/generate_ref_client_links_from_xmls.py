import jinja2
import os
import fnmatch

import xml.etree.ElementTree as ET

from argparse import ArgumentParser
from collections import defaultdict

# from adapters.olp.utils.coords_to_partition_id import convert_tile_id
from utils.web.ref_client import get_ols_url


def get_test_data(test_data_path):
    data = defaultdict(list)
    x_data = dict()
    for path_root, _, test_data_files in os.walk(test_data_path):
        for test_data_file in fnmatch.filter(test_data_files, '*.xml'):
            path = os.path.join(path_root, test_data_file)
            x_data[test_data_file] = list()
            data_key = " ".join(test_data_file.split("_")[:-1])
            tree = ET.parse(path)
            root = tree.getroot()
            for elem in root.findall("route_plan/waypoint/[@type='STOP']"):
                x_data[test_data_file].append((elem.attrib["lat"], elem.attrib["lng"]))
            try:
                url = get_ols_url(x_data[test_data_file][0], x_data[test_data_file][1])
                data[data_key].append((test_data_file, url))
            except Exception as err:
                print("WARNING: %s" % err)

    return data


# def get_partition_ids_from_kwd(start_p, end_p):
#     partition_ids = list()
#     partition_ids.append(convert_tile_id(float(start_p[1]), float(start_p[0]), 12))
#     partition_ids.append(convert_tile_id(float(end_p[1]), float(end_p[0]), 12))

#     return partition_ids


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
    opt_parser.add_argument("--test_data_path", dest="test_data_path",
                            help="Path to folder with test data (XML files)",
                            default="", required=True)
    opt_parser.add_argument("--template", dest="template",
                            help="Path to Jinja template")
    opt_parser.add_argument("--output", dest="output",
                            help="HTML page with links to RefClient",
                            default="index.html")
    options = opt_parser.parse_args()
    print("Creating URLs...")
    data = get_test_data(options.test_data_path)
    print("Generating report...")
    create_report(options.template, options.output, data)
    print("Created report: %s" % options.output)


if __name__ == "__main__":
    main()
