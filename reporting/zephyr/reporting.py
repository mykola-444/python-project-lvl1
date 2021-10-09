from reporting_config import test_statuses, projects
from _jira.jira import JiraAPI
from logger import Logger
from zephyr.helper import Helper
from zephyr.zephyr import ZephyrAPI

log = Logger(" Zephyr-Reporting ").log

"""
    For create test cycle on Zephyr, collect data, prepare report and send them to Zephyr just run
    Reporting({project}, {release_name}, {cycle_name}, {result_path}).sync_results({cycle_description})
"""


class Reporting:

    def __init__(self, project_name: str, release_name: str, cycle_name: str, result_path: str):
        """
        Collect test report statuses and send them to Zephyr
        :param project_name: jira project name
        :param release_name: HASDK release, in zephyr API it is just 'version'
        :param cycle_name: zephyr cycle name
        :param result_path: path to tests result xml file
        """
        self.project_name = project_name
        self.zephyr_api = ZephyrAPI(release_name, cycle_name, projects.get(self.project_name))
        self.result_path = result_path
        self.report_events = Helper.get_zephyr_test_name_with_test_result_mapping(self.result_path)

    def sync_results(self, cycle_description=""):
        test_summary = self.get_test_summary()
        log.info(test_summary)
        self.zephyr_api.create_cycle(description=cycle_description)
        for status, status_id in test_statuses.items():
            issues_id_with_status = [(report["issue_id"], status_id) for report in test_summary
                                     if status == report["status"] and report["issue_key"]]
            log.debug(issues_id_with_status)
            if issues_id_with_status:
                self.zephyr_api.add_executions(issues_id_with_status)

    def get_test_summary(self) -> [dict]:
        """
        :return list of dicts test results: list wit dicts, all of dicts has keys:
        testcase (long test name), status (zephyr test status), issue_key (jira issue key), issue_id (jira_issue_id)
        """
        jira = JiraAPI()

        test_results = Helper.get_zephyr_test_name_with_test_result_mapping(self.result_path)
        for test_result in test_results:
            testcase_name = test_result.get("testcase")
            if testcase_name.split(":")[-1].strip().startswith(self.project_name):
                test_result["issue_key"] = testcase_name.split(":")[-1].strip()
            else:
                test_name = Helper.get_test_summary(testcase_name)
                test_result["issue_key"] = jira.get_issue_key_by_name(test_name)

        jira.get_jira_ids_by_keys(test_results)
        test_results = jira.jira_ids
        return test_results
