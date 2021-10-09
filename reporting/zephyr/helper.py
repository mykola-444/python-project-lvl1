import re
from bs4 import BeautifulSoup


class Helper:
    mapping_between_zephyr_and_pytest_statuses = {"failure": "failed", "error": "failed", "skipped": "unexecuted"}

    def get_jira_keys_for_don(self, path_to_results_xml) -> dict:
        soup = BeautifulSoup(open(path_to_results_xml, "r", encoding="utf-8"), "html.parser")
        re_search = re.compile(r"don-[0-9]+")
        jira_key_status = {}
        for testcase in soup.find_all('testcase'):
            if testcase.find("failure"):
                self.__append_jira_key_status(jira_key_status, testcase, "Failed", re_search)
            elif testcase.find("error"):
                self.__append_jira_key_status(jira_key_status, testcase, "Error", re_search)
            else:
                self.__append_jira_key_status(jira_key_status, testcase, "Passed", re_search)
        return jira_key_status

    def __append_jira_key_status(self, key_status, xml_test_case, status, search) -> None:
        if search.findall(xml_test_case["classname"]):
            key_status[search.findall(xml_test_case["classname"])[0]] = status
        else:
            key_status[xml_test_case["classname"]] = status

    @staticmethod
    def get_test_summary(row_test_name: str) -> str:
        test_summary = row_test_name[row_test_name.find("[") + 1:(row_test_name.find("|") or row_test_name.find("]"))] \
            if row_test_name.find("[") != -1 else row_test_name
        return test_summary.split("test_")[-1].replace("_", " ")

    @classmethod
    def get_zephyr_test_name_with_test_result_mapping(cls, path_to_results) -> list:
        """
        :param path_to_results: path to junit xml
        :return: dict {'status' : 'test status', 'summary': 'test summary'}.
        """
        test_result = []

        soup = BeautifulSoup(open(path_to_results, "r", encoding="utf-8"), "html.parser")
        for testcase in soup.find_all('testcase'):
            for status in cls.mapping_between_zephyr_and_pytest_statuses.keys():
                if testcase.find(status):
                    if testcase.find(status)['message'] == "expected test failure":
                        test_status = "failed"
                    else:
                        test_status = cls.mapping_between_zephyr_and_pytest_statuses[status]
                    break
            else:
                test_status = "passed"
            test_result.append({"status": test_status, "testcase": testcase["name"]})
        return test_result
