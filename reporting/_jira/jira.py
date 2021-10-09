import asyncio
import json
import aiohttp
import requests

from reporting_config import jira_key_storage, AUTH_HEADERS
from logger import Logger
from urls import urls

log = Logger("[ ZephyrAPI ]").log


class JiraAPI:
    def __init__(self):
        self.read_jira_key_storage()
        self.jira_ids = []
        self.test_data = None
        self.__loaded_jira_keys = None
        self.__jira_keys = None

    def __del__(self) -> None:
        if self.__loaded_jira_keys != self.__jira_keys:
            with open(jira_key_storage, "w") as key_storage:
                key_storage.write(json.dumps(self.__jira_keys))

    def get_jira_ids_by_keys(self, jira_keys: list):
        self.test_data = jira_keys.copy()
        asyncio.run(self.async_run(jira_keys, self.__get_jira_ids))

    async def async_run(self, iterable_data: list, func: '__get_jira_ids'):
        semaphore = asyncio.Semaphore(10)
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as async_session:
            tasks = [func(semaphore, async_session, _data) for _data in iterable_data]
            await asyncio.gather(*tasks)

    async def __get_jira_ids(self, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, jira_test_data: dict) -> None:
        async with semaphore:
            jira_key = jira_test_data.get("issue_key")
            log.info(urls.get_jira_issue_content(jira_key))
            resp = await session.get(url=urls.get_jira_issue_content(jira_key), headers=AUTH_HEADERS)
            try:
                issue_data = await resp.json()
                jira_test_data["issue_id"] = issue_data.get("id")
            except:
                jira_test_data["issue_id"] = ""

            self.jira_ids.append(jira_test_data)

    def get_issue_key_by_name(self, test_name) -> str:
        path_phrase = test_name.replace(" - ", " ")
        if not self.__jira_keys:
            self.read_jira_key_storage()

        if self.__jira_keys.get(test_name):
            return self.__jira_keys.get(test_name)

        accurate_search_data = {"jql": 'summary ~ "\\"{path_phrase}\\""'.format(path_phrase=path_phrase), "fields": ["key", ]}
        resp = requests.post(urls.search_in_jira, data=json.dumps(accurate_search_data), headers=AUTH_HEADERS)

        if not resp.json().get("issues"):
            # using jql by LIKE pattern
            like_search_data = {"jql": 'summary ~ "{path_phrase}"'.format(path_phrase=path_phrase), "fields": ["key", ]}
            resp = requests.post(urls.search_in_jira, data=json.dumps(like_search_data), headers=AUTH_HEADERS)
            if not resp.json().get("issues"):
                return ""
                # raise Exception("Jira ticket was not found! Path phrase: {}".format(path_phrase))

        jira_key = resp.json().get("issues")[0]["key"]
        self.__jira_keys[test_name] = jira_key
        return jira_key

    def read_jira_key_storage(self) -> None:
        with open(jira_key_storage, "r") as storage:
            self.__loaded_jira_keys = json.loads(storage.read())
            self.__jira_keys = self.__loaded_jira_keys.copy()

    @staticmethod
    def get_jira_summary_by_key(jira_key: str) -> str:
        resp = requests.get(urls.get_issue_summary(jira_key), headers=AUTH_HEADERS)
        return resp.json().get("fields", {}).get("summary", "empty")

# @staticmethod
    # def get_issue_content(key):
    #     resp = requests.post(urls.get_jira_issue_content(key), headers=AUTH_HEADERS).json()
    #     fields = resp["fields"]
    #     labels = fields["labels"]
    #     summary = fields["summary"]
    #     component = [component.get("name") for component in fields.get("components")]
