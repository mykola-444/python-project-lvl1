import re
import json
import logging

from common_data import Data
from upd_library import Lib


"""
    PSD MITF that is using *.feature files
"""


log = logging.getLogger("PSD_Feature")


class SpartaPSDFeatureStream:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_test_details(report, root):
        details = dict()
        positions = list()
        test_name, file_name = None, None
        for test_case in root.iter("testcase"):
            if test_case.get("status") == "passed":
                continue
            else:
                try:
                    failure = test_case.getchildren()[0].text
                    case_name = test_case.get("name")
                    test_name = re.search(Lib.PSD_FAILED_TEST_NAME, case_name).group()
                    location = re.search(Lib.PSD_FILE_LOCATION, failure).group()
                    file_name = re.search(Lib.PSD_CUT_FILE_NAME, location).group()
                    number = re.search(Lib.PSD_FAILED_TEST_NUMBER, case_name).group(2)
                    positions.append(int(number))
                except AttributeError as ex:
                    log.error(" Something happened during the report parsing: '{}'.\n"
                              "Regex has returned the blank result: {}".format(report, ex))
        details[file_name] = {"test": test_name, "position": positions}
        return details

    @staticmethod
    def get_failed_tests_details(reports):
        output = dict()
        for report in reports:
            content = Data.read_from_xml_file(report)
            details = SpartaPSDFeatureStream.get_test_details(report, content)
            if Data.get_failure_number(content) > 0:
                log.info(" Report: {}; Failed case: {}".format(report, details))
                for key, values in details.items():
                    output[key] = output[key] + values if key in output else values
        return output

    @staticmethod
    def get_list_of_failed_psd_tests(change_id, jenkins_job, key, job_url):
        links = list()
        if job_url:
            links.append(job_url)
        else:
            current_patch_set = json.loads(Data.get_current_patch_set(change_id).decode("utf-8").split("\n")[0])
            comments = json.loads(Data.get_comments(change_id).decode("utf-8").split("\n")[0])
            links = Data.get_list_of_job(current_patch_set["currentPatchSet"]["number"],
                                         comments["comments"],
                                         jenkins_job,
                                         key)
        log.info(" List of jobs: {}".format(links))
        if links:
            build_number = max([int(build) for build in [link.split("/")[-2] for link in links]])
            build_link = [link for link in links if str(build_number) in link].pop()
            log.info(" Check the job: {}".format(build_link))
            Data.get_and_extract_archive(build_link, Lib.TEST_REPORTS_ARCHIVE)
            reports = Data.get_test_xml_reports(Lib.PSD_REPORT_PREFIX)
            log.info(" Tests reports: {}".format(reports))
            details = SpartaPSDFeatureStream.get_failed_tests_details(reports)
        else:
            log.warning(" Warning! There were no useful links found. Script is stopped. "
                        "Please check results manually.".upper())
            raise ValueError("'links' is empty.")
        return details

    @staticmethod
    def get_psd_geo_data(details, features):
        geo_data = dict()
        for feature in features:
            line_count = -1
            check_this_line = False
            current = re.search(Lib.PSD_CUT_FILE_NAME, feature).group()
            test_name = details[current].get("test")
            position = details[current].get("position")
            body = Data.read_from_text_file(feature)
            for line in body:
                if ("Scenario Outline" in line and test_name in line) or check_this_line:
                    check_this_line = True
                    if line.lstrip(" ").startswith("|"):
                        line_count += 1
                        if line_count in position:
                            geo_node = re.search(Lib.PSD_GEO_NODE, line).group().replace("|", "").strip()
                            item_name = Data.get_item_name_from_file_name(current)
                            geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [
                                geo_node]
                if "Scenario Outline" in line and test_name not in line:
                    check_this_line = False
        return geo_data

    def run_calculation(self):
        log.info(" Feature mode for PSD is started. '*.feature' files are expected.")
        if not self.job_url:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.jenkins_job)
        else:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.job_url)
        failed_tests = self.get_list_of_failed_psd_tests(self.change_id, self.jenkins_job, self.key, self.job_url)
        log.info(" List of failed tests: {}".format(failed_tests))
        files_locations = Data.get_psd_files_location(self.key, failed_tests, region_name, "*.feature")
        geo_data = self.get_psd_geo_data(failed_tests, files_locations)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
