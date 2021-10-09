from _jira.jira import JiraAPI
from gerrit.gerrit_handler import GerritHandler
from reporting_config import user_credentials, report_page_templates
from zephyr.zephyr import ZephyrAPI
from jinja2 import Environment, FileSystemLoader
from atlassian import Confluence
from logger import Logger

log = Logger(" ReportPageBuilder ").log


class ReportPageBuilder:
    def __init__(self, aepreq_jira_key, fix_version, cycle_name, map_version, map_revision,
                 map_region="World", platform="Linux64"):
        self.aepreq_key = aepreq_jira_key
        self.fix_version = fix_version
        self.cycle_name = cycle_name
        self.map_version = map_version
        self.map_revision = map_revision
        self.map_region = map_region
        self.platform = platform
        self.zapi = ZephyrAPI()
        self.confluence = Confluence(
                url='https://confluence.in.here.com',
                **user_credentials
                )

    def create_page(self):
        page_content = self.fill_page_template()
        self.confluence.update_or_create(
                parent_id=self._find_parent_page_id(),
                title=self._page_title(),
                body=page_content, representation='storage')

    def _page_title(self):
        return f"{self.fix_version} - {JiraAPI.get_jira_summary_by_key(self.aepreq_key)}"

    def fill_page_template(self) -> str:
        page_data = dict(
                aepreq_key=self.aepreq_key,
                aepreq_component=None,
                filter_id=self._get_zapi_filter_id(),
                fix_version=self.fix_version,
                jira_tests=self._get_functional_test_cases(),
                map_version=self.map_version,
                map_revision=self.map_revision,
                map_region=self.map_region,
                platform=self.platform,
                sdk_version=f"{self.fix_version} - SDK1.X"
                )

        page_content = Environment(loader=FileSystemLoader(report_page_templates))\
            .get_template('aepreq_report_page.html').render(page_data=page_data)

        return page_content

    def _get_aepreq_additional_test_info(self) -> tuple:
        gerrit = GerritHandler()
        linked_aqa_issues = self.zapi.get_test_creation_task_from_aepreq(self.aepreq_key)
        commits = set()
        all_labels = set()
        log.info(f"linked_aqa_issues -> {linked_aqa_issues}")
        for aqa_issue in linked_aqa_issues:

            gerrit_commit = gerrit.get_gerrit_commit_url(aqa_issue)
            labels = self.zapi.get_issue_labels(aqa_issue)
            log.info(f"gerrit_commit -> {gerrit_commit}")
            log.info(f"labels -> {labels}")
            commits.update([gerrit_commit])
            all_labels.update(labels)
        return list(commits), list(all_labels)

    def _get_functional_test_cases(self):
        test_info = self.zapi.get_aepreq_tests_info(self.aepreq_key)
        gerrit_commits, labels = [aqa_issue for aqa_issue in self._get_aepreq_additional_test_info()]
        commit = " ,".join(gerrit_commits) if len(gerrit_commits) > 1 else gerrit_commits[0]
        label = " ,".join(labels) if len(labels) > 1 else labels[0]
        for test in test_info:
            if "Closed" in test.get("status"):
                test["status"] = "done"
            test.update({"gerrit_commit": commit, "label": label})
        log.info(f"jira tests -> {test_info}")
        return test_info

    def _get_zapi_filter_id(self):
        zapi_filter_query = f'project = "HERESDK" AND fixVersion = "{self.fix_version}" ' \
                            f'AND cycleName in ("{self.cycle_name}") AND issue in linkedIssues({self.aepreq_key})'
        zapi_filter_id = self.zapi.create_execution_filter(
                filter_name=f"{self.cycle_name}_{self.aepreq_key}",
                query=zapi_filter_query)
        log.info(f"zapi_filter_query -> {zapi_filter_query}")
        log.info(f"zapi_filter_id -> {zapi_filter_id}")
        return zapi_filter_id

    def _find_parent_page_id(self) -> int:
        hasdk_releases = 561519772
        release_page_id = self._find_child_id(hasdk_releases, f"{self.fix_version} - SDK1.X")
        rc_release_page_id = self._find_child_id(release_page_id, f"RC - {self.fix_version} - SDK1.X")
        rc_test_summary_page_id = self._find_child_id(rc_release_page_id, "Product Requirements Test Summary")
        return rc_test_summary_page_id

    def _find_child_id(self, parent_id: int, part_of_child_name: str) -> int:
        children = self.confluence.get_page_child_by_type(parent_id, limit=100)
        log.info(f"children -> {children}")
        for child in children:
            if part_of_child_name in child.get('title'):
                return child.get('id')
        return 0
