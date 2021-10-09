import re
import json
import logging
from common_data import Data
from upd_library import Lib


log = logging.getLogger("SDKRouting")


class SDKRoutingStream:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_failed_job(change_id, key, job_url, topic):
        if not job_url:
            jobs = Lib.SDK_JENKINS_JOBS[key]
            for job in jobs:
                body = json.loads(Data.get_jenkins_response(job).content.decode("utf-8"))
                builds = body["builds"]
                counter = 0
                for build in builds:
                    if counter >= Lib.HOW_MANY_JOBS_SHOULD_BE_CHECKED_SDK:
                        log.info(" Limit ({}) is reached. The next job will be checked."
                                 .format(Lib.HOW_MANY_JOBS_SHOULD_BE_CHECKED_SDK))
                        break
                    build_body = json.loads(Data.get_jenkins_response(build["url"]).content.decode("utf-8"))
                    build_description = build_body["description"]
                    if change_id in build_description or topic in build_description:
                        url = build_body["url"]
                        job_body = json.loads(Data.get_jenkins_response(url).content.decode("utf-8"))
                        if job_body["result"] in ("UNSTABLE", "FAILURE"):
                            return url
                    else:
                        counter += 1
                        continue
                else:
                    log.warning("\nWarning! '{}' folder is not contain any completed jobs with '{}' topic.\n"
                                "The next '{}' folder will be checked.\n"
                                "If the result will be unsuccessful too,"
                                "please run 'rebuild all please' command.".format(jobs[0], topic, jobs[1]))
        else:
            return job_url

    @staticmethod
    def get_list_of_failed_routing_tests(job, key):
        if job:
            Data.get_xunit_report(job, Lib.TEST_REPORT, key)
            tests = Data.get_failed_tests_from_report()
        else:
            log.warning(" Warning! There were no useful links found. Script is stopped. "
                        "Please check results manually.".upper())
            raise ValueError("'links' is empty.")
        return tests

    @staticmethod
    def get_routing_geo_data(files, tests):
        geo_data = dict()
        for xml_file in files:
            for test in tests.values():
                ldm = re.search(Lib.ROUTING_LDM_FROM_FILE_PATH, xml_file).group()
                for db_key, db_regions in Lib.LDM_DATABASE.items():
                    if ldm == db_key and test['region'] in db_regions and test['xml_name'] in xml_file:
                        item_name, geo_node = Data.get_data_from_file(xml_file)
                        geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [
                            geo_node]
        return geo_data

    @staticmethod
    def get_superset_routing_geo_data(files, tests):
        geo_data = dict()
        for xml_file in files:
            for test in tests.values():
                ldm = re.search(Lib.ROUTING_LDM_FROM_FILE_PATH, xml_file).group()
                if ldm == test['region'] and test['xml_name'] in xml_file:
                    item_name, geo_node = Data.get_data_from_file(xml_file)
                    geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [
                        geo_node]
        return geo_data

    @staticmethod
    def get_geo_data(files, tests, key):
        if key == 'sup':
            geo_data = SDKRoutingStream.get_superset_routing_geo_data(files, tests)
        else:
            geo_data = SDKRoutingStream.get_routing_geo_data(files, tests)
        return geo_data

    def run_calculation(self):
        topic = Data.get_env_variable("TOPIC")
        failed_job = SDKRoutingStream.get_failed_job(self.change_id, self.key, self.job_url, topic)
        log.info(" Failed job is {}".format(failed_job))
        failed_tests = SDKRoutingStream.get_list_of_failed_routing_tests(failed_job, self.key)
        log.info(" Failed tests number is {}".format(len(failed_tests)))
        log.info(" List of failed tests: {}".format(failed_tests))
        details = Data.get_routing_failed_cases(failed_tests)
        files_locations = Data.get_routing_files_location(self.key, details)
        geo_data = SDKRoutingStream.get_geo_data(files_locations, details, self.key)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
