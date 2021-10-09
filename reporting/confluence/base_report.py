from atlassian import Confluence
from logger import Logger
from reporting_config import user_credentials, hasdk_releases, confluence_url

log = Logger(" ReportPageBuilder ").log


class BaseReport:

    def __init__(self, fix_version):
        self.fix_version = fix_version
        self.confluence = Confluence(url=confluence_url, **user_credentials)

    @property
    def release_page_id(self):
        return self._find_child_id(hasdk_releases, f"{self.fix_version} - SDK1.X")

    @property
    def rc_release_page_id(self):
        return self._find_child_id(self.release_page_id, f"RC - {self.fix_version} - SDK1.X")

    def _find_child_id(self, parent_id: int, part_of_child_name: str, child_limit=300) -> int:
        children = self.confluence.get_page_child_by_type(parent_id, limit=child_limit)
        log.info(f"children -> {children}")
        for child in children:
            if part_of_child_name in child.get('title'):
                return child.get('id')
        return 0

    def create_page(self): raise NotImplemented

    def _page_title(self): raise NotImplemented

    def fill_page_template(self): raise NotImplemented

