import os
import re
import fnmatch
import logging
from common_data import Data
from upd_library import Lib


log = logging.getLogger("SpartaStreams")


class SpartaStreams:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_streams_failed_cases(tests):
        cases = dict()
        for line in tests:
            test_name = re.search(Lib.STREAMS_TEST_NAME, line).group(2)
            file_name = re.search(Lib.STREAMS_FILE_NAME, line).group(2).replace("_json", ".json")
            cases[file_name] = cases[file_name] + [test_name] if file_name in cases else [test_name]
        return cases

    @staticmethod
    def get_streams_files_location(key, tests, region):
        cases = list()
        for root, folders, files in os.walk(Lib.MITF_FILES_PATH):
            for json_file in fnmatch.filter(files, "*.json"):
                file_path = os.path.join(root, json_file)
                if json_file in tests and "/team-{}/{}".format(str.lower(key), str.upper(region)) in file_path:
                    cases.append(file_path)
        return cases

    @staticmethod
    def get_streams_geo_data(files, tests):
        geo_data = dict()
        for json_file in files:
            body = Data.read_from_json_file(json_file)
            for case in body["tests"]:
                item_name = case["debug_data"]["item_name"]
                geo_node = str(case["debug_data"]["geo_node"])
                for keys, values in tests.items():
                    if keys in json_file and case["name"] in values:
                        geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [geo_node]
        return geo_data

    def run_calculation(self):
        if self.job_url:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.job_url)
        else:
            region_name = Data.get_region_name_from_sparta_jenkins_job(self.jenkins_job)
        failed_tests = Data.get_list_of_failed_streams_tests(self.change_id, self.jenkins_job, self.key, self.job_url)
        log.info(" Failed tests number: {}".format(len(failed_tests)))
        log.info(" List of failed tests: {}".format(failed_tests))
        details = self.get_streams_failed_cases(failed_tests)
        log.info(" Suites that contain failed tests: {}".format(details.keys()))
        files_locations = self.get_streams_files_location(self.key, details, region_name)
        geo_data = self.get_streams_geo_data(files_locations, details)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
