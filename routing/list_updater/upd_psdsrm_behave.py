import re
import json
import logging
from common_data import Data
from upd_library import Lib


"""
    PSD MITF that is using Behave and *.json files
"""


log = logging.getLogger("PSD_Behave")


class SpartaPSDBehaveStream:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_list_of_names(xml_root):
        data = list()
        for section in xml_root.iter("system-out"):
            target = re.findall(Lib.PSD_FAILED_TEST, section.text)
            if target:
                for record in target:
                    data.append(re.search(Lib.PSD_FILE_NAME, record).group())
        return data

    @staticmethod
    def get_failed_tests_names(data):
        names_list = list()
        for item in data:
            xml_body = Data.read_from_xml_file(item)
            names = SpartaPSDBehaveStream.get_list_of_names(xml_body)
            if names:
                for name in names:
                    names_list.append(name)
        return names_list

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
            details = SpartaPSDBehaveStream.get_failed_tests_names(reports)
        else:
            log.error(" Warning! There were no useful links found. Script is stopped. "
                      "Please check results manually.".upper())
            raise ValueError("'links' is empty.")
        return details

    @staticmethod
    def get_psd_geo_data(files):
        geo_data = dict()
        for json_file in files:
            body = Data.read_from_json_file(json_file)
            if body["debug_data"]:
                item_name = body["debug_data"]["item_name"]
                geo_node = str(body["debug_data"]["geo_node"])
                geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [geo_node]
        return geo_data

    def run_calculation(self):
        log.info(" Behave mode for PSD is started. '*.json' files are expected.")
        if self.job_url:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.job_url)
        else:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.jenkins_job)
        failed_tests = self.get_list_of_failed_psd_tests(self.change_id, self.jenkins_job, self.key, self.job_url)
        log.info(" Failed tests number: {}".format(len(failed_tests)))
        log.info(" List of failed tests: {}".format(failed_tests))
        files_locations = Data.get_psd_files_location(self.key, failed_tests, region_name, "*.json")
        geo_data = self.get_psd_geo_data(files_locations)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
