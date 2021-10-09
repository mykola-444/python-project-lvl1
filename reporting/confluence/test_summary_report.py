from jinja2 import Environment, FileSystemLoader

from confluence.base_report import BaseReport
from reporting_config import report_page_templates
from logger import Logger

log = Logger(" ReportPageBuilder ").log


class TestSummaryReport(BaseReport):

    def __init__(self, fix_version, aepreq_reports=None):
        super().__init__(fix_version)
        self._aepreq_reports = aepreq_reports
        self._aepreqs_jira_keys = None
        self._search_query = None

    @property
    def search_query(self):
        search_params = 'issue in linkedIssues'
        if not self._search_query:
            search_issues = ' or '.join([f'{search_params}({aep})' for aep in self.aepreq_reports])
            self._search_query = f"project = HERESDK and issuetype in (Bug, Question) and ({search_issues}) " \
                                 f"ORDER BY priority DESC, status DESC"
        return self._search_query

    @property
    def aepreq_reports(self):
        if not self._aepreq_reports:
            self._aepreq_reports = self.prepare_qepreq_reporst_info()
        return self._aepreq_reports

    @property
    def aepreq_jira_keys(self):
        if not self._aepreqs_jira_keys:
            self._aepreqs_jira_keys = ','.join([k for k in self.aepreq_reports])
        return self._aepreqs_jira_keys

    @property
    def rc_test_summary_page_id(self):
        return self._find_child_id(self.rc_release_page_id, "Product Requirements Test Summary")

    def prepare_qepreq_reporst_info(self):
        children_info = self.confluence.get_child_pages(page_id=self.rc_test_summary_page_id)
        reports_info = {}
        for child in children_info:
            report_name = child['title']
            aepreq_key = report_name.split('[')[1].split(']')[0]
            report_url = child['_links']['webui']
            reports_info.update({aepreq_key: {
                "report_name": self.replace_amp(report_name),
                "report_url": report_url
                }})
        return reports_info

    def replace_amp(self, string: str):
        if '&' in string:
            string = string.replace('&', '&amp;')
        return string

    def create_page(self, blank_page=False):
        page_content = self.fill_page_template() if not blank_page else "Coming soon =)"
        self.confluence.update_or_create(parent_id=self.rc_release_page_id,
                                         title=self._page_title(),
                                         body=page_content,
                                         representation='storage')

    def _page_title(self):
        return f"RC - {self.fix_version} - SDK1.X Product Requirements Test Summary"

    def fill_page_template(self) -> str:
        page_data = dict(
                aepreq_reports=self.aepreq_reports,
                aepreqs_jira_keys=self.aepreq_jira_keys,
                search_query=self.search_query
                )

        page_content = Environment(loader=FileSystemLoader(report_page_templates)) \
            .get_template('test_summary_page.html').render(page_data=page_data)
        return page_content
