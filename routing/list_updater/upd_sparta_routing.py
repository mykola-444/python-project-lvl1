import logging
from common_data import Data


log = logging.getLogger("SpartaRouting")


class SpartaRoutingStream:

    def __init__(self, config):
        self.change_id = config.change_id
        self.jenkins_job = config.jenkins_job
        self.key = config.key
        self.investigation_list = config.investigation_list
        self.job_url = config.job_url

    @staticmethod
    def get_routing_geo_data(files, tests):
        geo_data = dict()
        for xml_file in files:
            for test in tests.values():
                if test['xml_name'] in xml_file and test['region'] in xml_file:
                    item_name, geo_node = Data.get_data_from_file(xml_file)
                    geo_data[item_name] = geo_data[item_name] + [geo_node] if item_name in geo_data else [geo_node]
        return geo_data

    def run_calculation(self):
        failed_tests = Data.get_list_of_failed_streams_tests(self.change_id, self.jenkins_job, self.key, self.job_url)
        log.info(" Failed tests number is: {}".format(len(failed_tests)))
        log.info(" List of failed tests: {}".format(failed_tests))
        details = Data.get_routing_failed_cases(failed_tests)
        files_locations = Data.get_routing_files_location(self.key, details)
        geo_data = SpartaRoutingStream.get_routing_geo_data(files_locations, details)
        log.info(" Collected data: {}".format(geo_data))
        return geo_data
