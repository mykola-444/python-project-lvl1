import re
import os
import json
import logging
import fnmatch
import requests
import subprocess
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from upd_library import Lib


log = logging.getLogger("CommonData")


class Data:

    # guidance, nds-dal, positioning, psd behave, psd feature, routing spt, search, traffic
    @staticmethod
    def get_current_patch_set(change_id):
        return subprocess.check_output(["ssh", "-p", "29418", "gerrit.it.here.com", "gerrit", "query",
                                        "--format=JSON",
                                        "--current-patch-set",
                                        "change:{}".format(change_id)])

    # guidance, nds-dal, positioning, psd behave, psd feature, routing spt, search, traffic
    @staticmethod
    def get_comments(change_id):
        return subprocess.check_output(["ssh", "-p", "29418", "gerrit.it.here.com", "gerrit", "query",
                                        "--format=JSON",
                                        "--comments",
                                        "change:{}".format(change_id)])

    # routing spt, sdk, search, traffic
    @staticmethod
    def get_xunit_report(url, test_report, key):
        if key in Lib.SDK_ROUTING_PROGRAMS:
            try:
                subprocess.check_call(["wget", "-qO", "{}".format(test_report),
                                       "{}s3/download/{}".format(url, test_report)])
            except subprocess.CalledProcessError:
                log.warning(" Report was not uploaded to S3. Check in the artifact folder.")
                subprocess.check_call(["wget", "-qO", "{}".format(test_report),
                                       "{}artifact/{}".format(url, test_report)])
        else:
            try:
                subprocess.check_call(["wget", "-qO", "{}".format(test_report),
                                       "{}s3/download/outputs/xunit/{}".format(url, test_report)])
            except subprocess.CalledProcessError:
                log.error("Impossible to download a report.")
                raise

    # guidance, nds-dal, positioning, psd behave, psd feature
    @staticmethod
    def get_and_extract_archive(url, file_name):
        try:
            subprocess.check_call(["wget", "-qO", "{}".format(file_name), "{}s3/download/{}".format(url, file_name)])
            subprocess.check_call(["tar", "xf", file_name])
        except subprocess.CalledProcessError:
            log.error("Impossible to download or extract an archive.")
            raise

    # sdk
    @staticmethod
    def get_jenkins_response(request):
        log.info(" Check the job: {}".format(request))
        return requests.get("https://{}/api/json?pretty=true".format(request[8:]))

    # sdk
    @staticmethod
    def get_env_variable(variable):
        output = os.environ.get(variable)
        if output is None:
            raise ValueError(" Warning! Variable {} is not set".format(variable))
        return output

    # guidance, psd feature, positioning, psd behave, nds-dal, routing spt, search, traffic
    @staticmethod
    def get_list_of_job(patch_set, comments, jenkins_job, key):
        output = list()
        for comment in comments:
            """
                If you are checking functionality for tests reasons using already submitted review
                don't forget to decrease patch set number in the next "if" statement!
            """
            if "Patch Set {}".format(patch_set) in comment["message"] and \
                    ("Build Failed" in comment["message"] or "Build Unstable" in comment["message"]):
                messages = comment["message"]
                for message in messages.split("\n\n"):
                    marker = Data.failed_job_marker(key)
                    if jenkins_job in message and marker in message:
                        output.append(message.split(" : ")[0])
        return output

    # guidance, psd feature, positioning, psd behave, nds-dal, routing spt, search, traffic
    @staticmethod
    def failed_job_marker(key):
        if key in ['spt', 'psd', 'guidance', 'positioning']:
            return 'UNSTABLE'
        return 'FAILURE'

    # psd behave, psd feature, search, traffic
    @staticmethod
    def get_region_name_from_sparta_jenkins_job(job_name):
        if "-eu-" in job_name:
            region = "EU"
        elif "-na-" in job_name:
            region = "NA"
        else:
            region = "RW"
        log.info(" Detected region is: {}".format(region))
        return region

    # routing spt, sdk, search, traffic
    @staticmethod
    def get_failed_tests_from_report():
        tests = list()
        content = Data.read_from_xml_file(Lib.TEST_REPORT)
        for child in content.iter('testcase'):
            if child.find('failure') is not None or child.find('error') is not None:
                tests.append(child.get('name'))
        return tests

    # routing spt, search, traffic
    @classmethod
    def get_list_of_failed_streams_tests(cls, change_id, jenkins_job, key, job_url):
        links = list()
        if job_url:
            links.append(job_url)
        else:
            current_patch_set = json.loads(cls.get_current_patch_set(change_id).decode("utf-8").split("\n")[0])
            comments = json.loads(cls.get_comments(change_id).decode("utf-8").split("\n")[0])
            links = Data.get_list_of_job(current_patch_set["currentPatchSet"]["number"],
                                         comments["comments"],
                                         jenkins_job,
                                         key)
        log.info(" List of jobs: {}".format(links))
        if links:
            log.info(" Check the job: {}".format(max(links)))
            build_number = max([int(build) for build in [link.split("/")[-2] for link in links]])
            build_link = [link for link in links if str(build_number) in link].pop()
            cls.get_xunit_report(build_link, Lib.TEST_REPORT, key)
            test_results = cls.get_failed_tests_from_report()
        else:
            log.warning(" Warning! There were no useful links found. Script is stopped. "
                        "Please check results manually.".upper())
            raise ValueError("'links' is empty.")
        return test_results

    # routing spt, sdk
    @staticmethod
    def get_routing_failed_cases(tests):
        cases = dict()
        for line in tests:
            cases[line.rstrip()] = {'region': re.search(Lib.ROUTING_REGION_NAME, line).group(),
                                    'xml_name': '{}.xml'.format(re.search(Lib.ROUTING_FILE_NAME, line).group())}
        return cases

    # routing spt, sdk
    @staticmethod
    def get_files_names(tests):
        names = list()
        for test in tests.values():
            names.append(test['xml_name'])
        return names

    # routing spt, sdk
    @staticmethod
    def get_routing_files_location(key, tests):
        output = list()
        test_names = Data.get_files_names(tests)
        for root, _, files in os.walk(Lib.MITF_FILES_PATH):
            for xml_file in fnmatch.filter(files, "*.xml"):
                file_path = os.path.join(root, xml_file)
                if xml_file in test_names and "nds/{}/".format(key) in file_path:
                    output.append(file_path)
        return output

    # routing spt, sdk
    @staticmethod
    def get_data_from_file(file_path):
        item_name, geo_node = "", ""
        root = Data.read_from_xml_file(file_path)
        for child in root.iter('comment'):
            geo_node = re.search(Lib.ROUTING_GEO_NODE, child.text).group().replace("geo_node = ", "")
            item_name = re.search(Lib.ROUTING_ITEM_NAME, child.text).group().replace("item_name = ", "")
        return item_name, geo_node

    # guidance, positioning, psd feature
    @staticmethod
    def get_failure_number(content):
        return len(content.findall(".//failure")) or len(content.findall(".//error"))

    # guidance, positioning
    @staticmethod
    def get_test_details(content, reg_file_name, reg_data, reg_node_id):
        details = dict()
        for test_case in content.iter("testcase"):
            try:
                """
                    We get 'node_id' from 'name' attribute of <testcase> tag and 'item_name' from text section
                    of <failure> tag
                """
                failure = test_case.find("failure").text
                message = test_case.get("name")
                filename = re.search(reg_file_name, failure).group()
                item_name = Data.get_item_name_from_file_name(filename)
                data = re.search(reg_data, message).group()
                node_id = re.search(reg_node_id, data).group()
                details[item_name] = details[item_name] + [node_id] if item_name in details else [node_id]
            except AttributeError:
                pass
        return details

    # collect
    @staticmethod
    def add_comment(date, node_ids):
        return "# {}. Automatically added: \"{}\"".format(date, ';'.join(node_ids))

    # collect
    @staticmethod
    def format_line(ext_key, node_ids):
        return "{}: \"{}\"".format(ext_key, ';'.join(node_ids))

    # collect
    @staticmethod
    def collect_updated_investigation_list(fresh_data, investigation_list):
        output = list()
        keys_base = list()
        current_date = datetime.today().strftime("%Y-%m-%d")
        content = Data.read_from_text_file(investigation_list)
        for line in content:
            if not line.startswith("#") and len(line.strip(" ")) > 1:
                # if line isn't comment
                update_flag = False
                item_name = re.search(Lib.REGEX_ITEM_AND_NODES, line).group(1)
                keys_base.append(item_name)
                node_ids = re.search(Lib.REGEX_ITEM_AND_NODES, line).group(3)
                node_ids_list = list(node_ids.split(";"))
                # check line and update values if it's necessary
                if item_name in fresh_data:
                    for value in fresh_data.get(item_name):
                        if value not in node_ids_list:
                            node_ids_list.append(value)
                            update_flag = True
                if update_flag:
                    output.append(Data.format_line(item_name, node_ids_list))
                    output.append(Data.add_comment(current_date, fresh_data[item_name]))
                else:
                    # if line was not changed
                    output.append(Data.format_line(item_name, node_ids_list))
            elif line.startswith("#"):
                # if line is comment
                output.append(line)
        for fresh_key, fresh_value in fresh_data.items():
            # if item_name is a new
            if fresh_key not in keys_base:
                output.append(Data.format_line(fresh_key, fresh_value))
                output.append(Data.add_comment(current_date, fresh_data[fresh_key]))
        return output

    # writer
    @staticmethod
    def write_investigation_list(data, investigation_list):
        with open(investigation_list, "w") as updated_list:
            for line in data:
                if len(line) > 1:
                    updated_list.write(line + "\n")
        log.info(" '{}' is updated and can be uploaded to S3.".format(investigation_list))

    # guidance, positioning, psd feature
    @staticmethod
    def get_item_name_from_file_name(file_name):
        if re.match(Lib.ITEM_NAME, file_name):
            return "_".join(file_name.split(".")[0].split("_")[1:])
        elif re.findall(Lib.NOT_WORD_ITEM_NAME, file_name):
            return "_".join(file_name.split("_")[0:-2])
        else:
            return file_name

    # routing spt, sdk, search, traffic
    @staticmethod
    def read_from_xml_file(file_name):
        with open(file_name, "r") as item:
            content = ElementTree.parse(item)
        return content.getroot()

    # collect, psd feature
    @staticmethod
    def read_from_text_file(file_name):
        with open(file_name, "r") as item:
            content = item.read().split("\n")
        return content

    # psd behave, search, traffic
    @staticmethod
    def read_from_json_file(file_name):
        with open(file_name, "r") as item:
            content = json.loads(item.read())
        return content

    # guidance, positioning, psd behave, psd feature
    @staticmethod
    def get_test_xml_reports(prefix):
        output = list()
        for folder, _, files in os.walk("."):
            for xml in files:
                if xml.startswith(prefix) and xml.endswith(".xml"):
                    output.append(os.path.join(folder, xml))
        return output

    # psd behave, psd feature
    @staticmethod
    def get_psd_files_location(key, tests, region, extension):
        cases = list()
        for root, _, files in os.walk(Lib.MITF_FILES_PATH):
            for target in fnmatch.filter(files, extension):
                file_path = os.path.join(root, target)
                if target in tests and "/team-{}/{}".format(str.lower(key), str.upper(region)) in file_path:
                    cases.append(file_path)
        return cases

    # psd behave, psd feature
    @staticmethod
    def check_input_files_type(folder, ext_name, destination):
        for root, _, files in os.walk(destination):
            for file_name in files:
                if folder in root and file_name.endswith('.{}'.format(ext_name)):
                    return True
        return False
