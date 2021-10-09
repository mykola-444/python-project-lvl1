import asyncio
import aiohttp
import time
import json
import requests
import ssl
import certifi

from reporting_config import AUTH_HEADERS, jira_url
from logger import Logger
from urls import urls
sslcontext = ssl.create_default_context(cafile=certifi.where())
log = Logger(" ZephyrAPI ").log


class ZephyrAPI:
    def __init__(self, version_name: str = None, cycle_name: str = None, project_id: int = None):
        self._session = requests.Session()
        self.project_id = project_id
        self.version_name = version_name
        self.cycle_name = cycle_name
        self._cycles = {}
        self._cycle_id = ""
        self.__version_id = ""

    def create_cycle(self, cloned_cycle_id="", description=""):
        """
        :param description: test cycle description
        :param cloned_cycle_id: cycle ID for cloning
        :return: created cycle_id
        """
        if self._cycle_exists():
            return
        description = description or "python func test on carlo level"
        data = {
            'name': self.cycle_name,
            'build': self.version_name,
            'clonedCycleId': cloned_cycle_id,
            'description': description,
            'projectId': self.project_id,
            'versionId': self.version_id
            }
        resp = self._session.post(url=urls.create_cycle, data=json.dumps(data), headers=AUTH_HEADERS)
        creating_status = resp.json()
        log.info(creating_status)
        if "created successfully" in creating_status.get("responseMessage"):
            self._cycle_id = creating_status.get("id")
        else:
            raise Exception("Cycle was not created")
        if resp.json().get("jobProgressToken"):
            self.__wait_until_zephyr_process_ended_get_its_id(resp.json().get("jobProgressToken"))
        else:
            self.__wait_until_cycle_will_be_exist()

    def _cycle_exists(self) -> bool:
        self.get_cycles_by_release_version(ignore_old_result=True)
        if self.cycle_name in self._cycles.keys():
            self._cycle_id = self._cycles[self.cycle_name]["cycle_id"]
            return True
        else:
            return False

    def get_cycles_by_release_version(self, ignore_old_result=False) -> dict:
        if self._cycles and not ignore_old_result:
            return self._cycles
        resp = self._session.get(url=urls.get_cycles_by_version(self.project_id, self.version_id), headers=AUTH_HEADERS)
        self._cycles = {v['name']: {"cycle_id": k, "version_id": v["versionId"], "version_name": v["versionName"]}
                        for k, v in resp.json().items() if k.isdigit()}
        return self._cycles

    @property
    def version_id(self):
        if not self.__version_id:
            self.__get_version_id()
        return self.__version_id

    def add_executions(self, issues_with_status: list):
        asyncio.run(self.async_run(issues_with_status, self.add_execution_with_status))

    async def async_run(self, iterable_data: list, func: 'function') -> None:
        semaphore = asyncio.Semaphore(5)
        async with aiohttp.ClientSession() as async_session:
            tasks = [func(semaphore, async_session, *_data) for _data in iterable_data]
            await asyncio.gather(*tasks)

    async def add_execution_with_status(self, semaphore: asyncio.Semaphore,
                                        session: aiohttp.ClientSession, issue_id: int, status_id: int):
        async with semaphore:
            execution_id = await self.add_execution(session, issue_id)
            if execution_id.isdigit():
                await self.set_execution_status(session, execution_id, status_id)
            else:
                log.info(execution_id)

    async def add_execution(self, session: aiohttp.ClientSession, issue_id: int, attempts=5) -> str:
        if not attempts:
            return f"Issue {issue_id} was not added to the cycle {self._cycle_id}"
        data = {"projectId": self.project_id, "issueId": issue_id, "cycleId": self._cycle_id,
                "versionId": self.version_id}
        async with session.post(url=urls.add_test_to_cycle, data=json.dumps(data), headers=AUTH_HEADERS) as response:
            log.info(f"url -> {urls.add_test_to_cycle}, data -> {data}, resp -> {response.status}")
            if response.status != 200:
                attempts -= 1
                return await self.add_execution(session, issue_id, attempts)
            execution_data = await response.json()
            execution_id = [k for k in execution_data.keys()][0]
            return execution_id

    async def set_execution_status(self, session: aiohttp.ClientSession, execution_id, status_id, attempts=5):
        if not attempts:
            return f"Status {status_id} was not added to execution {execution_id} in the cycle {self._cycle_id}"
        data = {"status": status_id, "changeAssignee": "false"}
        async with session.put(
                url=urls.set_execution_status(execution_id), data=json.dumps(data), headers=AUTH_HEADERS) as response:
            log.info(f"url -> {urls.set_execution_status(execution_id)}, data -> {data}, resp -> {response.status}")
            if response.status != 200:
                attempts -= 1
                return await self.set_execution_status(session, execution_id, status_id, attempts)
            return

    def __get_version_id(self) -> str:
        all_versions = self._session.get(urls.get_all_versions(self.project_id), headers=AUTH_HEADERS)
        all_versions_name_and_id = {version["name"]: version["id"] for version in all_versions.json()}
        self.__version_id = all_versions_name_and_id.get(self.version_name)
        return self.__version_id

    def __wait_until_zephyr_process_ended_get_its_id(self, job_progress_token, timeout=60 * 30) -> str:
        span = time.time() + timeout
        while time.time() < span:
            resp = self._session.get(urls.wait_until_cycle_created(job_progress_token), headers=AUTH_HEADERS)
            progress = resp.json().get("progress")
            log.info("Added tests to cycle, progress {} %".format(int(progress*100)))
            if progress == 1.0:  # '1.0' means 100% of execution and cycle is created
                new_cycle_id = resp.json().get("entityId")
                return new_cycle_id
            time.sleep(1)
        else:
            raise TimeoutError("The following cycle were not created for {} seconds".format(timeout))

    def __wait_until_cycle_will_be_exist(self) -> None:
        while not self._cycle_exists():
            time.sleep(1)

    def create_execution_filter(self, filter_name, query, description='') -> int:
        """Creates new execution filter"""
        log.info(f"Execution filter name -> {filter_name}")
        if filter_name in self.get_execution_filters():
            print("Execution Filter '{0}' is already exist. Going to remove it".format(filter_name))
            self.delete_execution_filter(filter_name)
        data = {
            'filterName': filter_name,
            'query': query,
            'description': description or "python func test on carlo level",
            "isFavorite": "true",
            "sharePerm": "1"
            }
        resp = self._session.post(url=urls.create_filter, data=json.dumps(data), headers=AUTH_HEADERS)
        log.info(resp.text)
        log.info(f"Created execution filter with name '{filter_name}' and query '{query}'")
        return resp.json().get("id")

    def get_execution_filters(self, filters=""):
        """
        Gets All Execution Filters

        :param: filters: additional filter like 'byUser=&fav=&offset=&maxRecords='
        """
        resp = self._session.get(urls.get_filters(filters), headers=AUTH_HEADERS)
        log.info(resp.text)
        return {execution_filter.get("filterName"): execution_filter for execution_filter in resp.json()}

    def delete_execution_filter(self, filter_name):
        """
        Deletes a ZQL filter by id

        :param filter_name: filter name
        """
        execution_filter_id = self.get_execution_filters()[filter_name]["id"]
        resp = self._session.delete(urls.delete_filter(execution_filter_id), headers=AUTH_HEADERS)
        log.info(resp.text)

    @staticmethod
    def get_aepreq_tests_info(aepreq: str) -> [dict]:
        resp = requests.get(urls.get_list_of_tests_by_requirement(aepreq), headers=AUTH_HEADERS)
        log.info(resp.text)
        return [test_case["test"] for test_case in resp.json()[0]["tests"]]

    @staticmethod
    def get_test_creation_task_from_aepreq(aepreq: str) -> [str]:
        row_resp = requests.get(urls.get_linked_issues(aepreq), headers=AUTH_HEADERS)
        all_linked_data = row_resp.json()
        linked_issues = all_linked_data["fields"]["issuelinks"]
        return [issue["inwardIssue"]["key"] for issue in linked_issues
                if "[AQA]" in issue.get("inwardIssue", {}).get("fields", {}).get("summary", "")]

    @staticmethod
    def get_issue_labels(issue_key: str) -> [str]:
        resp = requests.get(urls.get_issue_labels(issue_key), headers=AUTH_HEADERS).json()
        return resp.get("fields", {}).get("labels", [])

    @staticmethod
    def execute_search(zql_query: str) -> dict:
        print(urls.get_execute_search(zql_query))
        return requests.get(urls.get_execute_search(zql_query), headers=AUTH_HEADERS).json()

    @staticmethod
    def get_test_by_req_id(req_id) -> [dict]:
        try:
            return requests.get(urls.get_search_test_by_requirement_id(req_id), headers=AUTH_HEADERS, timeout=60).json()
        except Exception:
            return ZephyrAPI.get_test_by_req_id(req_id)


    @staticmethod
    async def async_get_test_by_req_id(session, req_id, attempts=5) -> [dict]:
        if not attempts:
            return []
        url = f"{jira_url}/rest/zapi/latest/traceability/testsByRequirement?requirementIdOrKeyList={req_id}"
        async with session.put(url=url, headers=AUTH_HEADERS, ssl=sslcontext) as response:
            log.info(f"url -> {url}, resp -> {response.status}")
            if response.status != 200:
                attempts -= 1
                return await ZephyrAPI.async_get_test_by_req_id(session, req_id, attempts)
        return await response.json()


if __name__ == "__main__":
    z = ZephyrAPI("a","b",1)
    query = 'project = "HERESDK" AND fixVersion = "19wk51" AND cycleName in ("19wk51_RC_HASDK1.X_Functional_Linux_All") and issue in linkedIssues(AEPREQ-3763)'
    filterName = 'test_autogenerated_filter'
    description = 'test autogenerated filter'
    z.create_execution_filter(filterName, query, description)