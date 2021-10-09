# -*- coding: utf-8 -*-
import fnmatch
import os
import re
import sys
from argparse import ArgumentParser

from generate_data_by_predefined_geo_nodes import create_investigation_list


def is_in_investigation_list(investigation_list, item_name, node):
    return investigation_list[item_name]["skip_all"] or (node in
                                                         investigation_list[item_name]["geo_nodes"])


def remove_xmls(path, investigation_list):
    xmls = list()
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.xml'):
            xmls.append(os.path.join(root, filename))
    print("investigation_list_filter: XMLs under analysis (count=%d):" % len(xmls))
    print('%s' % "\n".join(xmls))
    counter = 0

    for fname in xmls:
        should_remove = False

        with open(fname, 'r', encoding='utf-8') as fd:
            output = fd.read()
            try:
                match = re.findall("<comment>(.*?)</comment>", output, re.DOTALL)
                if not match:
                    continue
                description = match[0].strip()
                item_name = re.findall(r'item_name = (\w+)', description)[0]
                geo_node = re.findall(r'geo_node = ([0-9,|_]+)', description)[0]
                if is_in_investigation_list(investigation_list, item_name, geo_node):
                    should_remove = True
            except Exception as err:
                sys.stderr.write("Error parsing '%s':\n%s\n" % (fname, output))
                raise err

        if should_remove:
            os.unlink(fname)
            print("File %s has been removed successfully" % fname)
            counter = counter + 1
    return counter


def main():
    print("INFO: investigation_list_filter: starting investigation...")
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--investigation_list", dest="investigation_list",
                            help="Investigation list yaml file", required=True)
    opt_parser.add_argument("--xmls_path", dest="xmls_path",
                            help="Path to the test xml's folder", required=True)

    options = opt_parser.parse_args()
    investigation_list = create_investigation_list(options.investigation_list)
    print("INFO: investigation_list_filter: yaml structure: {}".format(investigation_list))
    counter = remove_xmls(options.xmls_path, investigation_list)
    print("INFO: investigation_list_filter: investigation done\n"
          "WARN: {} file(s) have been removed".format(counter))


if __name__ == '__main__':
    main()
