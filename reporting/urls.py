from reporting_config import jira_url, gerrit_url


class URLS:
    def __init__(self):
        self.__host = jira_url
        self.__gerrit = gerrit_url

    @property
    def login(self):
        return self.__make_url("/login.jsp")

    @property
    def create_cycle(self):
        return self.__make_url("/rest/zapi/latest/cycle/")

    @property
    def create_filter(self):
        return self.__make_url("/rest/zapi/latest/zql/executionFilter/")

    def get_filters(self, data):
        return self.__make_url("/rest/zapi/latest/zql/executionFilter/search?{}", data)

    def delete_filter(self, filter_id):
        return self.__make_url("/rest/zapi/latest/zql/executionFilter/{}", filter_id)

    def wait_until_cycle_created(self, job_progress: str):
        return self.__make_url('/rest/zapi/latest/execution/jobProgress/{}/', job_progress)

    def get_cycles_by_version(self, project_id, version_id):
        return self.__make_url("/rest/zapi/latest/cycle?projectId={}&versionId={}", project_id, version_id)

    def get_list_of_tests_by_requirement(self, aepreq):
        return self.__make_url("/rest/zapi/latest/traceability/testsByRequirement?requirementIdOrKeyList={}", aepreq)

    def get_all_versions(self, project_id):
        return self.__make_url("/rest/api/2/project/{}/versions", project_id)

    @property
    def add_tests_to_cycle(self):
        return self.__make_url("/rest/zapi/latest/execution/addTestsToCycle/")

    def get_executions(self, cycle_id):
        return self.__make_url("/rest/zapi/latest/execution?action=expand&cycleId={}", cycle_id)

    def get_execute_search(self, query):
        return self.__make_url("/rest/zapi/latest/zql/executeSearch?zqlQuery={}&maxRecords=10000", query)

    def get_search_test_by_requirement_id(self, requirement_id):
        return self.__make_url("/rest/zapi/latest/traceability/testsByRequirement?requirementIdOrKeyList={}", requirement_id)

    def set_execution_status(self, execution_id):
        return self.__make_url("/rest/zapi/latest/execution/{}/execute", execution_id)

    @property
    def add_test_to_cycle(self):
        return self.__make_url("/rest/zapi/latest/execution/")

    def get_jira_issue_content(self, jira_key: str) -> str:
        return self.__make_url("/rest/api/latest/issue/{}", jira_key)

    @property
    def search_in_jira(self):
        return self.__make_url("/rest/api/2/search")

    def get_linked_issues(self, issue_key):
        return f"{self.__host}/rest/api/latest/issue/{issue_key}?fields=summary,issuelinks"

    def get_issue_labels(self, issue_key):
        return f"{self.__host}/rest/api/latest/issue/{issue_key}?fields=labels"

    def get_issue_summary(self, issue_key):
        return f"{self.__host}/rest/api/latest/issue/{issue_key}?fields=summary"

    @property
    def gerrit_login(self):
        return self.__gerrit + "/login"

    def get_gerrit_commit(self, heresdk_key):
        return self.__gerrit + f"/changes/?q=project:mos%2Fqa_automation+message:{heresdk_key}+status:merged"

    def __make_url(self, url: str, *params) -> str:
        return self.__host + url.format(*params)


urls = URLS()
