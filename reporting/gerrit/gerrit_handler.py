import json
from requests import Session

import reporting_config as config
from urls import urls
from logger import Logger


log = Logger(" GerritHandler ").log


class GerritHandler:
    def __init__(self):
        self.session = Session()
        self.session.post(urls.gerrit_login, config.user_credentials)

    def get_gerrit_commit_url(self, heresdk_test_creation_task) -> str:
        # heresdk_test_creation_task = aepreq
        row_resp = self.session.get(urls.get_gerrit_commit(heresdk_test_creation_task))
        resp = json.loads(self.__fix_gerrit_json_response(row_resp.text))
        log.info(resp)
        commit_id = resp[0]["_number"]
        return f"{config.gerrit_url}/#/c/{commit_id}/"

    def __fix_gerrit_json_response(self, resp: str) -> str:
        return resp.lstrip(")]}'")
