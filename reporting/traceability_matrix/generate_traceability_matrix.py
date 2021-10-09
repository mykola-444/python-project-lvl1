import sys
import time
from jira import JIRA, JIRAError
from reporting_config import bot_credentials, jira_url, traceability_matrix_page_templates, traceability_matrix_done_page
from zephyr.zephyr import ZephyrAPI
from jinja2 import Environment, FileSystemLoader
from logger import Logger


log = Logger(" TraceabilityMatrixGenerator ").log


AEPORT = "AEPORT"
JIRA_QUERY_FIND_AEPREQ = 'filter=122541'
JIRA_QUERY_FIND_AEPORT = 'issue in structure(441) and project = AEPORT'
JIRA_QUERY_FIND_CUSTOM_AEPREQ = 'issue in linkedIssues("{}") and key in structure(441) and project = AEPREQ'
ZEPHYR_QUERY = 'project = "HERESDK" AND fixVersion = "{}" AND cycleName in ("{}")'


class TraceabilityMatrixGenerator:
    def __init__(self, fix_version: str, cycle_name: str, aeport=False):
        self.jira_query = JIRA_QUERY_FIND_AEPORT if aeport else JIRA_QUERY_FIND_AEPREQ
        self.test_query = ZEPHYR_QUERY.format(fix_version, cycle_name)
        self.template = 'aeport_traceability.html' if aeport else 'aepreq_traceability.html'
        self.jira_items = []
        self.traceability = []
        self.execution_results = {}
        self.jira_items_res = []

    def create_page(self):
        page_data = self.get_traceability_content()
        data = self.prepare_to_template(page_data)
        page_content = Environment(loader=FileSystemLoader(traceability_matrix_page_templates)) \
            .get_template(self.template).render(page_data=data["formatted_data"],
                                                coverage_general_data=data["coverage_general_data"])
        with open(traceability_matrix_done_page, "w", encoding="utf-8") as out_file:
            out_file.write(page_content)

    def get_traceability_content(self):
        self.jira_items = self.get_jira_items_by_query(self.jira_query)
        self.get_zephyr_execution_results()
        self.map_requirements_and_tests(self.jira_items)
        return self.jira_items

    def get_jira_items_by_query(self, query):
        query_needed = True
        start_index = 0
        max_results = 1000
        jira_items_res = []

        while query_needed:
            jira_items = self.get_jira_query_response(query, start_index, max_results)
            if not jira_items:
                query_needed = False
            else:
                for item in jira_items:
                    if AEPORT in item.key:
                        item.aepreqs = \
                            [i for i in self.get_jira_items_by_query(JIRA_QUERY_FIND_CUSTOM_AEPREQ.format(item.key))]
                    jira_items_res += [item]
                start_index = start_index + max_results
            log.info('Number of Requirement --> ' + str(len(jira_items)))
            if not jira_items:
                log.info('Empty requirements list returned for JQL query: "{}"'.format(query))
        return jira_items_res

    #  TODO: move it to some jira class
    def get_jira_query_response(self, query, start_at, max_results):
        try:
            jira = JIRA('https://saeljira.it.here.com',
                        basic_auth=(bot_credentials["username"], bot_credentials["password"]))
            return jira.search_issues(query, startAt=start_at, maxResults=max_results)
        except JIRAError as jira_error:
            sys.exit("JIRA error: {0}".format(jira_error.text))

    def get_zephyr_execution_results(self):
        search_execution = ZephyrAPI.execute_search(self.test_query)
        log.debug("zephyr search execution -> {}".format(search_execution))
        test_executions = search_execution['executions']
        retry_count = 5
        while retry_count > 0 and len(test_executions) == 0:
            log.info('ZAPI returned empty test_executions list, RETRYING -->' + str(retry_count))
            retry_count = retry_count - 1
            time.sleep(5)
            test_executions = ZephyrAPI.execute_search(self.test_query)['executions']

        if not test_executions:
            sys.exit('ERROR: Empty execution result returned from Zephyr API Please check if Test Results '
                     'query is correct and Zephyr server is up and running properly')

        for execution in test_executions:
            result = execution['status']['name']
            if result is not 'PASS' and execution['testDefectsUnMasked']:
                defect_data = " ".join([get_hyperlink_string(str(defect))
                                        for defect in execution['testDefectsUnMasked']])
                result = result + " ==> " + defect_data
            test_result = {'issueKey': execution['issueKey'], 'result': result}
            self.execution_results[execution['issueKey']] = test_result
        return

    def map_requirements_and_tests(self, jira_items):
        for item in jira_items:
            test_list = {}
            tests = self.get_zephyr_tests_for_requirement(item.key)
            for i in range(0, len(tests)):
                current_test_jira = tests[i]['test']['key']
                if current_test_jira in self.execution_results:
                    test_list[current_test_jira] = self.execution_results[current_test_jira]['result']
                elif current_test_jira.startswith("HERESDK"):
                    test_list[current_test_jira] = "UNEXECUTED"
            item.test_list = test_list  # add "test_list" property to jira Issue object (bad way)
            if AEPORT in item.key:
                self.map_requirements_and_tests(item.aepreqs)

    def get_zephyr_tests_for_requirement(self, requirement_id):
        tests = ZephyrAPI.get_test_by_req_id(requirement_id)
        log.info('Processing Requirement-->' + str(requirement_id))
        return tests[0]['tests']

    def prepare_to_template(self, data: list) -> dict:
        formatted_data = self.format_traceability_data(data)
        if AEPORT in formatted_data[0]['key']:
            self.aeport_post_format(formatted_data)
        statistic_data = self.prepare_data_for_statistic_table(formatted_data)
        return {"coverage_general_data": statistic_data, "formatted_data": formatted_data}

    def format_traceability_data(self, data: list) -> list:
        formatted_data = []
        for i, issue in enumerate(data, start=1):
            test_dict = issue.test_list if issue.test_list else {"NON-AUTOMATABLE": "-"}
            issue_data = {"_id": i,
                          "key": issue.key,
                          "summary": issue.fields.summary,
                          "url": f"{jira_url}/browse/{issue.key}",
                          "test_list":
                              [{'key': k, 'status': v, 'url': f'{jira_url}/browse/{k}'} for k, v in test_dict.items()]}
            if 'aepreqs' in dir(issue):
                issue_data['aepreqs'] = self.format_traceability_data(issue.aepreqs)
            formatted_data.append(issue_data)
        return formatted_data

    def aeport_post_format(self, aeport_formatted_data: list):
        for aeport in aeport_formatted_data:
            if aeport['test_list'][0]['key'] == 'NON-AUTOMATABLE' and all(
                    [any(map(lambda status: status in ('UNEXECUTED', '-'), [test['status'] for test in aepreq['test_list']]))
                     for aepreq in aeport['aepreqs']]):
                aeport['test_list'][0]['key'] = 'COVERED'
                aeport['test_list'][0]['status'] = 'UNEXECUTED'
                aeport['test_list'][0]['url'] = None

            elif aeport['test_list'][0]['key'] == 'NON-AUTOMATABLE':
                aeport['test_list'][0]['key'] = 'COVERED'
                aeport['test_list'][0]['status'] = 'EXECUTED'
                aeport['test_list'][0]['url'] = None

            if aeport['test_list'][0]['key'] == 'COVERED' and all(
                    [all(map(lambda key: key == 'NON-AUTOMATABLE',
                             [test['key'] for test in aepreq['test_list']]))
                     for aepreq in aeport['aepreqs']]):
                aeport['test_list'][0]['key'] = 'NON-AUTOMATABLE'
                aeport['test_list'][0]['status'] = '-'
                aeport['test_list'][0]['url'] = None

    def prepare_data_for_statistic_table(self, formatted_data) -> dict:
        total_high_level_tasks = len(formatted_data)
        covered_high_level_tasks = 0
        total_low_level_tasks = 0
        covered_low_level_tasks = 0
        non_covered_lov_level_tasks = 0

        if AEPORT in formatted_data[0]["key"]:
            for aeport in formatted_data:
                aeports_aepreqs = len([aepreq for aepreq in aeport["aepreqs"]])
                total_low_level_tasks += aeports_aepreqs
                total_non_covered_aepreqs = len(
                        [aepreq for aepreq in aeport["aepreqs"] if aepreq["test_list"][0]['key'] == 'NON-AUTOMATABLE'])
                non_covered_lov_level_tasks += total_non_covered_aepreqs
                covered_high_level_tasks = covered_high_level_tasks + 1 \
                    if aeports_aepreqs - total_non_covered_aepreqs > 0 \
                       or aeport['test_list'][0]['key'] != 'NON-AUTOMATABLE' \
                    else covered_high_level_tasks

            covered_low_level_tasks = total_low_level_tasks - non_covered_lov_level_tasks
            non_covered_high_level_tasks = total_high_level_tasks - covered_high_level_tasks
        else:
            non_covered_high_level_tasks = \
                len([i for i in formatted_data if i['test_list'][0]['key'] == 'NON-AUTOMATABLE'])
            covered_high_level_tasks = total_high_level_tasks - non_covered_high_level_tasks

        coverage_general_data = {
            "total_high_level_tasks": total_high_level_tasks,
            "non_covered_high_level_tasks": non_covered_high_level_tasks,
            "covered_high_level_tasks": covered_high_level_tasks,
            "high_level_coverage": int(covered_high_level_tasks / (total_high_level_tasks or 1) * 100),

            "total_low_level_tasks": total_low_level_tasks,
            "non_covered_lov_level_tasks": non_covered_lov_level_tasks,
            "covered_low_level_tasks": covered_low_level_tasks,
            "low_level_coverage": int(covered_low_level_tasks / (total_low_level_tasks or 1) * 100),

            "jql_filter": self.jira_query,
            "zql_filter": self.test_query
            }
        return coverage_general_data


def get_hyperlink_string(jira_id):
    return '<a href = https://saeljira.it.here.com/browse/'+jira_id+' >'+jira_id+"</a>"

# "project = 'HERESDK' AND fixVersion = '19wk51' AND cycleName in ('RC_HASDK1.X_Functional_Linux_All')"
# def get_req_status_from_confluence(req_id):
#     from bs4 import BeautifulSoup
#     coverage_status = "NON-COVERED"
#     confl_test_coverage_page = ConfluenceAPI().get_page_content(665091329)  # https://confluence.in.here.com/display/HereAutoSDK1x/HA+SDK+1.X+Product+Requirements+Functional+Test+Coverage+Status
#     soup = BeautifulSoup(confl_test_coverage_page["body"]["storage"]["value"])
#     table = soup.find("table")
#     for table_row in table.findAll('tr'):
#         columns = table_row.findAll('td')
#         if columns and req_id in columns[1].text:
#             coverage_status = "NON-AUTOMATABLE" if "NON-AUTOMATABLE" in columns[4].text.upper() or "CANCELED" in columns[4].text.upper() else coverage_status
#     return coverage_status


# if __name__ == '__main__':
#     f2 = "filter=95187"
#     f1 = 'issue in structure(441) and project = AEPORT'
#     f11 = 'issue in structure(441) and project = AEPORT and key = AEPORT-787'
#     t = TraceabilityMatrixGenerator(f1, 'project = "HERESDK" AND fixVersion = "19wk51" AND cycleName in ("RC_HASDK1.X_Functional_Linux_All")')
#     page_data = t.get_traceability_content()
#     data = t.prepare_to_template(page_data)
#     page_content = Environment(loader=FileSystemLoader(traceability_matrix_page_templates)) \
#         .get_template('aeport_traceability.html').render(page_data=data["formatted_data"], coverage_general_data=data["coverage_general_data"])
#
#     with open(f"{traceability_matrix_page_templates}res_4.html", "w", encoding="utf-8") as out_file:
#         out_file.write(page_content)

