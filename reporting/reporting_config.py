import os
from base64 import b64encode

reporting_dir = os.path.dirname(os.path.abspath(__file__))

bot_credentials = dict(username="intbot", password="password123")
user_credentials = dict(username="username", password="password")

jira_url = "https://saeljira.it.here.com"
gerrit_url = "https://gerrit.it.here.com"
confluence_url = "https://confluence.in.here.com"

jira_key_storage = reporting_dir + "/_jira/jira_key_storage.json"
report_page_templates = reporting_dir + "/confluence/templates/"

traceability_matrix_page_templates = reporting_dir + "/traceability_matrix/templates/"
traceability_matrix_done_page = reporting_dir + "/traceability_matrix/results/traceability_matrix.html"

test_statuses = {"passed": 1, "failed": 2, "running": 3, "blocked": 4, "wip": 5, "not implemented": 6, "unexecuted": -1}

AUTH_HEADERS = {
    "Authorization": "Basic " + b64encode("{username}:{password}".format(**bot_credentials).encode()).decode(),
    "Content-Type": "application/json"
    }

projects = {"HERESDK": 22294, "DON": 23792}

hasdk_releases = 561519772
