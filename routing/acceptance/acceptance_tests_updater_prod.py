import glob
import os
import shutil
from argparse import ArgumentParser

from robot.api import TestData
from robot.parsing import ResourceFile

from acceptance_tests_updater_dev import filter_keywords
from utils.acceptance_tests import get_keywords_dep


def get_lib_name(lib):
    return lib.split("/")[-1]


def copy_libfile(lib, sources, keywords):
    # copy generated lib to .../here/routing/spec/lib/
    spec_folder = os.path.abspath(os.path.join(sources, ".."))
    lib_folder = os.path.join(spec_folder, "lib")
    if not os.path.exists(lib_folder):
        os.makedirs(lib_folder)
    new_lib = os.path.join(lib_folder, get_lib_name(lib))
    print("Copying '{}' to {}".format(lib, lib_folder))
    if not os.path.exists(new_lib):
        if keywords:
            result_lib_file = ResourceFile(source=new_lib)
            for resource in ResourceFile(source=lib).populate().keyword_table.keywords:
                if resource.name in keywords:
                    result_lib_file.keywords.append(resource)
            result_lib_file.save()
        else:
            shutil.copyfile(lib, new_lib)
    else:
        existing_keywords = dict()
        for resource in ResourceFile(source=new_lib).populate().keyword_table.keywords:
            existing_keywords[resource.name] = resource
        result_lib_file = ResourceFile(source=new_lib)
        for resource in ResourceFile(source=lib).populate().keyword_table.keywords:
            if keywords:
                if resource.name in keywords:
                    result_lib_file.keywords.append(resource)
                elif resource.name in existing_keywords:
                    result_lib_file.keywords.append(existing_keywords[resource.name])
            else:
                if resource.name in existing_keywords:
                    result_lib_file.keywords.append(existing_keywords[resource.name])
                else:
                    result_lib_file.keywords.append(resource)
        result_lib_file.save()
    return new_lib


def update_sources(keywords, sources, lib):
    for key, value in keywords.items():
        files = list(map(lambda x: os.path.join(sources, x), value))
        for file_ in files:
            dev_suite_file = TestData(source=file_)
            for keyword in dev_suite_file.keywords:
                if keyword.name == key:
                    break
            else:
                continue

            print("Updating {}: {}".format(file_, key))
            # get relative path based on 'setup.robot'
            setup = next((i.name for i in dev_suite_file.imports if "setup.robot" in i.name))
            lib_name = os.path.join(os.path.dirname(setup), "lib", os.path.basename(lib))
            # check and add resource to the test case
            if lib_name not in [i.name for i in dev_suite_file.imports]:
                dev_suite_file.setting_table.add_resource(lib_name)
            dev_suite_file.keywords.remove(keyword)
            dev_suite_file.save()


def main():
    parser = ArgumentParser(description="Updates the acceptance source tree for production usage.")
    parser.add_argument("-l", "--libs", type=str, dest="libs",
                        help="Path/(or prefix in dev mode) to folder with keywords", required=True)
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)
    parser.add_argument("-k", "--keywords", type=str, dest="keywords",
                        help="List with keywords that should be updated. "
                             "If the option is not specified all keywords will be updated.")
    parser.add_argument("-g", "--geo_nodes", type=str, dest="geo_nodes",
                        help="Path to json file with geo_nodes")
    options = parser.parse_args()

    print("Finding keywords with dependencies...")
    for lib in glob.iglob('{}/**/*.robot'.format(os.path.abspath(options.libs)), recursive=True):
        keywords = get_keywords_dep(lib)
        if options.keywords:
            print("Filtering...")
            # TODO: remove empty lib files
            filter_keywords(keywords, options.keywords)
        lib_file = copy_libfile(lib, options.sources, keywords)
        update_sources(keywords, options.sources, lib_file)


if __name__ == "__main__":
    main()
