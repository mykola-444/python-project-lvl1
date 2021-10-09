import configparser
import errno
import glob
import json
import os
from argparse import ArgumentParser
from copy import deepcopy

from robot.api import TestData
from robot.parsing import ResourceFile, TestCaseFile
from robot.parsing.settings import Resource, Tags, Documentation, Setting
from robot.parsing.model import Step

from adapters.olp.utils.coords_to_partition_id import convert_tile_id
from utils.acceptance_tests import get_keywords_dep
from utils.web.ref_client import get_ref_client_url, get_ols_url


# TODO (asmirnov): Make this configurable
MITF_TAG = "ROUTING-15269"


def filter_keywords(keywords, selected_keywords):
    selected_keywords = selected_keywords.split(",")
    keys = list(keywords.keys())
    for key in keys:
        if key not in selected_keywords:
            print("Filtering keyword: '{}'".format(key))
            del keywords[key]


def copy_libfile_dev(lib, sources, keywords):
    # copy generated lib to .../here/routing/spec/lib/
    spec_folder = os.path.abspath(os.path.join(sources, ".."))
    lib_folder = os.path.join(spec_folder, "lib")
    if not os.path.exists(lib_folder):
        os.makedirs(lib_folder)
    merged_content = "*** Keywords ***\n\n"
    for filename in glob.glob("%s%s" % (lib, '*.*')):
        name_index = filename.split("_")[-1].split(".")[0]
        if not name_index.isdigit():
            print("WARNING: lib file: '{}' does not contain index".format(filename))
            continue
        with open(filename, "r", encoding="utf-8") as fh:
            for line in fh.readlines():
                if "*** Keywords ***" not in line:
                    if line[0] not in (" ", "\n"):
                        line = line.replace("\n", " %s\n" % (name_index,))
                    merged_content += line
        merged_content += "\n\n"

    # Write merged content in temporary file:
    merged_filename = "%s.robot" % (lib,)
    with open(merged_filename, "w", encoding="utf-8") as fh:
        fh.write(merged_content)

    # Create resource structure using RobotFramework API...
    result_filename = os.path.join(lib_folder, os.path.basename(merged_filename))
    result_lib_file = ResourceFile(source=result_filename)

    for gen_kwd in ResourceFile(source=merged_filename).populate().keyword_table.keywords:
        # ... update steps that are calls of generated keywords to contain index ...
        for step in gen_kwd.steps:
            if step.name in list(keywords.keys()):
                # TODO (asmirnov): Do we need to prefix step name with resource name
                #  to avoid ambiguity?
                step.name = step.name + " " + gen_kwd.name.split(" ")[-1]
        # ... add modified keyword into the resource structure ...
        result_lib_file.keywords.append(gen_kwd)

    # ... and, finally, save this structure in proper destination
    result_lib_file.save()

    # Delete temporary file:
    try:
        os.remove(merged_filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise

    return result_filename


def get_geo_nodes(geo_nodes_file):
    if not geo_nodes_file:
        return None
    with open(geo_nodes_file, encoding="utf-8") as f_:
        data = json.load(f_)
    test_cases = dict()
    for i in data.values():
        test_cases.update(i)
    return test_cases


def get_geo_node_from_keyword(kwd):
    geo_node = item_name = None
    for step in kwd.steps:
        if "geo_node" in step.as_list()[-1]:
            geo_node = step.as_list()[-1].strip().split(" ")[-1]
        if "item_name" in step.as_list()[-1]:
            item_name = step.as_list()[-1].strip().split(" ")[-1]
    return geo_node, item_name


def get_item_name_from_keyword(kwd):
    for step in kwd.steps:
        if "item_name" in step.as_list()[-1]:
            return step.as_list()[-1].strip().split(" ")[-1]


def get_lib_kwds(lib):
    lib_kwds = list()
    gen_kwds = ResourceFile(source=lib).populate()
    for kwd in gen_kwds.keyword_table.keywords:
        geo_node, _ = get_geo_node_from_keyword(kwd)
        if geo_node is None:
            continue
        lib_kwds.append((kwd.name, geo_node))

    return lib_kwds


def get_affected_files(kwds_per_file, sources):
    affected_files = list()
    try:
        for suite in kwds_per_file:
            parsed_data = TestData(source=suite)
            tc_table = parsed_data.testcase_table
            for tc in tc_table:
                for step in tc.steps:
                    for kwd in kwds_per_file[suite]:
                        if kwd in step.as_list():
                            if suite not in affected_files:
                                affected_files.append(suite)
    except Exception as err:
        print(err)

    return affected_files


def get_affected_tests(kwds_per_file, suite, parsed_data):
    affected_tests = list()
    for suite in kwds_per_file:
        tc_table = parsed_data.testcase_table
        for tc in tc_table:
            for step in tc.steps:
                for kwd in kwds_per_file[suite]:
                    if kwd in step.as_list():
                        if tc not in affected_tests:
                            affected_tests.append(tc)

    return affected_tests


def get_kwds_per_file(keywords, sources):
    kwds_per_file = dict()
    for keyword in keywords:
        for item in keywords[keyword]:
            item = os.path.join(sources, item)
            if item not in kwds_per_file:
                kwds_per_file[item] = [keyword, ]
            else:
                kwds_per_file[item].append(keyword)

    return kwds_per_file


def get_index(name):
    return name.split(" ")[-1]


def get_basename(name):
    if "." in name:
        name = name.split(".")[1]
    return " ".join(name.split(" ")[0:-1])


def get_libkwd(name, lib_kwds):
    # TODO (asmirnov): Replace this list modification solution!!! Thus deepcopy won't be needed anymore
    lib_kwd = None
    for i, libkwd in enumerate(lib_kwds):
        if name in libkwd[0]:
            lib_kwd = libkwd[0]
            break
    lib_kwds.pop(i)
    return lib_kwd


def get_geo_node(kwd, lib_kwds):
    for lib_kwd in lib_kwds:
        if lib_kwd[0] == kwd:
            return lib_kwd[1]
    return None


def get_tc_mode(steps):
    template = "Provided transport mode is {}"
    mode = "car"
    for step in steps:
        if step.name == template.format("truck"):
            mode = "truck"
        elif step.name == template.format("pedestrian"):
            mode = "pedestrian"
    return mode


def update_sources_dev(keywords, sources, lib, config_path, geo_nodes_file, add_debug_tag, router_type):
    lib_kwds = get_lib_kwds(lib)
    geo_nodes = get_geo_nodes(geo_nodes_file)
    # TODO (asmirnov): Add processing if geo_nodes
    if geo_nodes:
        pass

    # Let's use any keyword to define iterations counter:
    iter_cnt = 0
    try:
        sample_kwd_bname = get_basename(lib_kwds[0][0])
    except IndexError:
        return
    if not sample_kwd_bname:
        return
    for lib_kwd in lib_kwds:
        if get_basename(lib_kwd[0]) == sample_kwd_bname:
            iter_cnt += 1

    print("Source folder: %s" % (sources, ))
    kwds_per_file = get_kwds_per_file(keywords, sources)
    affected_files = get_affected_files(kwds_per_file, sources)

    for file_ in affected_files:
        merge_flag = False
        # Form new test suite with tests number matching number of geo locations generated
        dev_suite_name = "{}/dev_{}".format(
            os.path.join(os.path.dirname(file_)), os.path.basename(file_))
        print("Destination file:", dev_suite_name)

        # TODO (asmrinov): Add unified error handling
        original_data = TestData(source=file_)
        dev_suite_file = TestCaseFile(source=dev_suite_name)

        affected_tests = get_affected_tests(kwds_per_file, file_, original_data)

        # Check if affected file has been processed earlier:
        if os.path.exists(dev_suite_name):
            print("Destination file already exists - merging changes")
            merge_flag = True
            tmp_dev_suite = TestCaseFile(source=dev_suite_name)
            tmp_dev_suite.populate()
            processed_kwds = set()
            processed_tests = set()
            imported_libs = list()
            # Collect keywords added as part of previous update
            for test in tmp_dev_suite.testcase_table:
                for aff_tst in affected_tests:
                    if get_basename(test.name) == aff_tst.name:
                        # TODO (asmirnov): Uncomment and remove WARNING once cleanup is done
                        # affected_tests.remove(aff_tst)
                        # affected_tests.append(test)
                        print("WARNING: Skipping - updating the same tests with keywords "
                              "from different libs is not supported yet!")
                        print("DEBUG:", test.name)
                        continue
                    if get_index(test.name):
                        processed_tests.add(test)
                for step in test:
                    if type(step) == Step:
                        if "." in step.name:
                            processed_kwds.add(get_basename(step.name))
                        for arg in step.args:
                            if "." in arg:
                                processed_kwds.add(get_basename(arg))

            for imported_lib in tmp_dev_suite.setting_table.imports.data:
                if "setup.robot" not in imported_lib.name:
                    imported_libs.append(imported_lib.name)

            # print("DEBUG: merging keywords ->", processed_kwds)
            # print("DEBUG: merging tests ->", [proc_tst.name for proc_tst in processed_tests])
            # print("DEBUG: merging imports ->", imported_libs)

        for affected_test in affected_tests:
            lib_kwds_local = deepcopy(lib_kwds)
            for _ in range(iter_cnt):
                modified_tc = dev_suite_file.testcase_table.add(affected_test.name)
                name_modified = False
                modified_tc.tags = affected_test.tags
                idx = -1
                mode = None
                for step in affected_test.steps:
                    mod_pos = -1
                    for kwd in kwds_per_file[file_]:
                        for i, step_elem in enumerate(step.as_list()):
                            if kwd == step_elem:
                                mod_pos = i
                    if mod_pos != -1:
                        if mod_pos == 0:
                            mod_kwd = get_libkwd(step.name, lib_kwds_local)
                            # modified_tc.add_step(["%s.%s" % (lib_import_prefix, mod_kwd), ] + step.args)
                            modified_tc.add_step([mod_kwd, ] + step.args)
                            if not modified_tc.doc.value:
                                modified_tc.doc.value = affected_test.doc.value
                            mode = get_tc_mode(affected_test.steps)
                            ref_client_link = add_ref_client_link(mod_kwd, config_path, lib, router_type, mode)
                            if ref_client_link:
                                modified_tc.doc.value = ' '.join([modified_tc.doc.value, ref_client_link])
                            partition_ids = get_partition_ids_from_kwd(mod_kwd, lib)
                            if partition_ids:
                                modified_tc.doc.value = ' '.join([modified_tc.doc.value, str(partition_ids)])
                        else:
                            try:
                                modified_tc.add_step([step.name, ] + step.args)
                            except Exception as err:
                                print(err)
                                continue
                            mod_kwd = get_libkwd(step.args[mod_pos - 1], lib_kwds_local)
                            if idx == -1:
                                idx = get_index(mod_kwd)
                                # modified_tc.steps[-1].args[mod_pos - 1] = "%s.%s" % (lib_import_prefix, mod_kwd)
                                modified_tc.steps[-1].args[mod_pos - 1] = mod_kwd
                            else:
                                mod_arg = step.args[mod_pos - 1] + " " + idx
                                # modified_tc.steps[-1].args[mod_pos - 1] = "%s.%s" % (lib_import_prefix, mod_arg)
                                modified_tc.steps[-1].args[mod_pos - 1] = mod_arg
                        if idx == -1:
                            idx = get_index(mod_kwd)
                        if not name_modified:
                            modified_tc.name = " ".join([modified_tc.name, idx])
                            if add_debug_tag:
                                modified_tc.tags.value.append("DEBUG")
                            name_modified = True
                    else:
                        try:
                            modified_tc.add_step([step.name, ] + step.args)
                        except Exception as err:
                            print(err)

        if merge_flag:
            for processed_test in processed_tests:
                proc_test = dev_suite_file.testcase_table.add(processed_test.name)
                for step in processed_test:
                    if type(step) == Step:
                        proc_test.add_step([step.name, ] + step.args)
                    elif type(step) == Documentation:
                        proc_test.doc.value = step.value
                    elif type(step) == Tags:
                        proc_test.tags.value = step.value
                    else:
                        pass  # print("WARNING: Skipping unsupported data type", type(step))

        # Move all the keywords which are not replaced by generated ones into new suite:
        # TODO (asmirnov): Ideally we do not need add unused keywords here
        for kwd in original_data.keyword_table:
            add_flag = True
            rm_flag = False
            if kwd.name in kwds_per_file[file_]:
                add_flag = False
            if merge_flag:
                if kwd.name in processed_kwds:
                    add_flag = False
                    if kwd.name in [kwd.name for kwd in dev_suite_file.keywords]:
                        rm_flag = True
            if add_flag:
                dev_suite_file.keywords.append(kwd)
            if rm_flag:
                pass
                # TODO (asmirnov): Make deletion of unnecessary keywords working
                # dev_suite_file.keywords = [x for x in dev_suite_file.keywords if x.name != kwd.name]

        # Preserve all (or _at least_ Documentation and Resource) original settings and ...:
        for setting in original_data.setting_table:
            if len(setting.as_list()) > 1:
                if type(setting) is Resource:
                    if "setup.robot" in setting.as_list()[1]:
                        if not dev_suite_file.setting_table.imports.data:
                            dev_suite_file.setting_table.imports.add(Resource(dev_suite_file,
                                                                              name=setting.name))
                        else:
                            if "setup.robot" not in dev_suite_file.setting_table.imports.data[0].as_list()[1]:
                                dev_suite_file.setting_table.imports.add(Resource(dev_suite_file,
                                                                                  name=setting.name))

                if type(setting) is Documentation:
                    dev_suite_file.setting_table.doc.value = setting.value
                if type(setting) is Tags:
                    if setting.as_list()[0] == "Force Tags":
                        suite_tags = setting.as_list()[1:]
                        if not add_debug_tag:
                            if MITF_TAG not in suite_tags:
                                setting.value.append(MITF_TAG)
                        dev_suite_file.setting_table.force_tags = setting

        if not dev_suite_file.setting_table.force_tags:
            if not add_debug_tag:
                dev_suite_file.setting_table.force_tags = Setting("Force Tags")
                dev_suite_file.setting_table.force_tags.value.append(MITF_TAG)

        # ... add Resource with generated keywords:
        # setup.lib is always first
        if not dev_suite_file.imports.data or "setup.robot" \
                not in dev_suite_file.imports.data[0].name:
            print("WARNING: cannot find setup.robot")
            continue
        # TODO (asmirnov): Remove extra import of setup.robot
        # Avoid duplicate imports - applicable when in merge mode:
        lib_import_str = "{0}lib{1}".format(dev_suite_file.imports.data[0].name[:-11],
                                            lib[lib.rfind("/"):])

        if merge_flag:
            for imported_lib in imported_libs:
                dev_suite_file.setting_table.imports.add(Resource(dev_suite_file, imported_lib))

        existing_imports = [imprt.name for imprt in dev_suite_file.setting_table.imports]
        if lib_import_str not in existing_imports:
            dev_suite_file.setting_table.imports.add(Resource(dev_suite_file, lib_import_str))

        # Preserve all existing variables even if they are not used in tests:
        for variable in original_data.variable_table:
            dev_suite_file.variable_table.variables.append(variable)

        # Save dev test suite to the file:
        dev_suite_file.save()


def get_points_from_kwd(keyword, lib):
    start_end_points = list()

    gen_kwds = ResourceFile(source=lib).populate()
    for kwd in gen_kwds.keyword_table.keywords:
        if kwd.name == keyword:
            for step in kwd:
                for item in step.as_list():
                    if "at(" in str(item):
                        start_end_points.append(item)
            start_end_points = [(item[3:-1].split(",")) for item in start_end_points]

            for item in start_end_points:
                start_end_points[start_end_points.index(item)] = (item[0], item[1].strip())

            return start_end_points[0], start_end_points[1]


def add_ref_client_link(keyword, config_path, lib, router_type, mode="car"):
    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        start_p, end_p = get_points_from_kwd(keyword, lib)
        if router_type == "hls":
            app_code = config["GeneratorSection"]["REF_APP_CODE"]
            app_id = config["GeneratorSection"]["REF_APP_ID"]
            url = get_ref_client_url(app_code, app_id, start_p, end_p, mode=mode)
        else:
            # TODO: Remove hardcoded mode https://saeljira.it.here.com/browse/MITF-788
            url = get_ols_url(start_p, end_p, mode=mode)
        return url
    except IndexError:
        pass
    except Exception as err:
        print('ERROR: Error adding RefClient link - ', err)


def get_partition_ids_from_kwd(keyword, lib):
    partition_ids = list()

    try:
        start_p, end_p = get_points_from_kwd(keyword, lib)
    except IndexError:
        return []
    try:
        partition_ids.append(convert_tile_id(float(start_p[1]), float(start_p[0]), 12))
        partition_ids.append(convert_tile_id(float(end_p[1]), float(end_p[0]), 12))
    except Exception as err:
        print(err)

    return partition_ids


def main():
    parser = ArgumentParser(description="Updates the acceptance source tree for development purposes.")
    parser.add_argument("-l", "--lib", type=str, dest="lib",
                        help="Path/(or prefix in dev mode) to file with keywords", required=True)
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)
    parser.add_argument("-k", "--keywords", type=str, dest="keywords",
                        help="List with keywords that should be updated. "
                             "If the option is not specified all keywords will be updated.")
    parser.add_argument("-g", "--geo_nodes", type=str, dest="geo_nodes",
                        help="Path to json file with geo_nodes")
    parser.add_argument("-c", "--config", type=str, dest="config", required=True,
                        help="Path to MITF config file. "
                             "Necessary for getting RefClient credentials")
    parser.add_argument("-d", "--no_debug_tag", dest="add_debug_tag", action='store_false',
                        help="Specifies if DEBUG tag will be added to each test case")
    parser.add_argument("-r", "--router_type", dest="router_type", type=str, choices=["hls", "ols"],
                        default="hls",
                        help="Defines service type")
    options = parser.parse_args()

    print("Finding keywords with dependencies...")
    try:
        keywords = get_keywords_dep(glob.glob("%s%s" % (options.lib, '*.*'))[0])
    except IndexError:
        print("Cannot find keywords - check input files")
        exit(1)
    result_lib_file = copy_libfile_dev(options.lib, options.sources, keywords)
    if options.keywords:
        print("Filtering...")
        filter_keywords(keywords, options.keywords)
    update_sources_dev(keywords, options.sources,
                       result_lib_file, options.config, options.geo_nodes, options.add_debug_tag,
                       options.router_type)


if __name__ == "__main__":
    main()
