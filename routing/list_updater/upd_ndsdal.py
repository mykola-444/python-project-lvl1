import re
import os
import json
import logging
from common_data import Data
from upd_library import Lib


log = logging.getLogger("NdsDal")


class SpartaNdsDalStream:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_xml_reports_list():
        reports = list()
        for folder, _, files in os.walk("."):
            for xml in files:
                if xml.endswith("_mitf_tests.xml"):
                    reports.append(os.path.join(folder, xml))
        return reports

    @staticmethod
    def get_test_details(report, root):
        details, base_ids, item_name = dict(), list(), ""
        for testsuite in root.iter("testsuite"):
            for test_case in testsuite.iter("testcase"):
                for failure in testsuite.iter("failure"):
                    try:
                        item_name = re.search(Lib.NDSDAL_ITEM_NAME, failure.text).group()
                        node_id = re.search(Lib.NDSDAL_NODE_ID, failure.text).group()
                        if node_id not in base_ids:
                            base_ids.append(node_id)
                    except AttributeError as ex:
                        log.error(" Something happened during the report parsing: '{}'.\n"
                                  "Regex has returned the blank result: {}".format(report, ex))
                        exit(1)
            if base_ids:
                details[item_name] = details[item_name] + base_ids if item_name in details else base_ids
        return details

    @staticmethod
    def get_failed_tests_details(reports):
        output = dict()
        for report in reports:
            log.info(" Check report: {}".format(report))
            content = Data.read_from_xml_file(report)
            details = SpartaNdsDalStream.get_test_details(report, content)
            if Data.get_failure_number(content) > 0:
                log.info(" Report: {}; Failed case: {}".format(report, details))
                for key, values in details.items():
                    output[key] = output[key] + values if key in output else values
        return output

    @staticmethod
    def get_list_of_failed_ndsdal_tests(change_id, jenkins_job, key, job_url):
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
            reports = SpartaNdsDalStream.get_xml_reports_list()
            log.info(" Tests reports: {}".format(reports))
            details = SpartaNdsDalStream.get_failed_tests_details(reports)
        else:
            log.warning(" Warning! There were no useful links found. Script is stopped. "
                        "Please check results manually.".upper())
            raise ValueError("'links' is empty.")
        return details

    def run_calculation(self):
        geo_data = self.get_list_of_failed_ndsdal_tests(self.change_id, self.jenkins_job, self.key, self.job_url)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
