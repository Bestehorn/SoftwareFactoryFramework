"""Tests for ``gitlab_api/families/no_stage_assigned.py``: the records of the no-stage-assigned endpoint family, the
group and project integrations APIs (issue #36, ``change.md`` AC-1, AC-2, AC-3, AC-5, AC-6).

What is pinned:

- nothing is pending, and the records' operation IDs are the References of the family's rows of
  ``docs/api-reference/gitlab/operations-index.md`` (AC-1);
- every ``Param`` is typed as its row of ``rest/no-stage-assigned.md``: ``Kind.ARRAY`` for an ``array of strings`` row
  and ``Kind.SCALAR`` for every other, ``required`` exactly where Required reads ``yes``; every record has a JSON body
  and no ``fixed`` pairs (AC-2);
- the two "List all active integrations" records are ``Paging.OFFSET``, every other record ``Paging.NONE`` (AC-3);
- each list record, called through the product's ``main(argv=["call", ...])`` against the fake host serving two pages,
  the second asked for by ``x-next-page``, prints the items of both as one JSON array; the group record's ``id`` is
  sent as one encoded segment, and the project record's is the configured project (AC-5, #41 design.md D8);
- a settings write sends its four attributes as a JSON body, each as the JSON value given (AC-6).

Every expected operation ID, ``ARRAY`` name, required name and paged ID is a literal table transcribed from
``operations-index.md`` and ``rest/no-stage-assigned.md``, never read from the records. The names and ``In`` of every
``Param``, and one call of every record, are proven by ``test/test_gitlab_wrapper_contract.py``.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_no_stage_assigned.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_no_stage_assigned_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.no_stage_assigned"
REGISTRY = "registry"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CALL = "call"
REST_BASE = fixtures.REST_BASE

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-no-stage-assigned-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_NEXT_PAGE = "x-next-page"
CONTENT_TYPE_JSON = "application/json"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

METHOD_GET = "GET"
METHOD_PUT = "PUT"
# The options of `call` (#41 design.md D2) and the `:id` path parameter, which defaults to the configured project on a
# `/projects/:id` path only (#41 AC-1.8).
OPTION_PATH = "--path"
OPTION_RAW_FIELD = "-f"
OPTION_FIELD = "-F"
PATH_ID = "id"
ASSIGNED = "="
# Transport.pages: OFFSET adds `per_page=MAX_PER_PAGE` to the first request, and the next page's request sets `page` to
# the `x-next-page` value (#13 AC-2.5).
FIRST_PAGE_QUERY = "?per_page=100"
NEXT_PAGE = "2"
SECOND_PAGE_QUERY = f"?per_page=100&page={NEXT_PAGE}"
LAST_PAGE = ""

# The `registry.Kind` and `registry.Paging` member names the tables hold.
KIND_ARRAY = "ARRAY"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"

# --- The tables, transcribed from the reference -----------------------------------------------------------------

# The Reference of every row of operations-index.md that links rest/no-stage-assigned.md, written
# `no-stage-assigned#<anchor>`, in index order (sorted by path). Each Reference carries one row.
OPERATION_IDS: Tuple[str, ...] = (
    "no-stage-assigned#get-google-cloud-identity-and-access-management",
    "no-stage-assigned#get-asana-settings",
    "no-stage-assigned#set-up-asana",
    "no-stage-assigned#disable-asana",
    "no-stage-assigned#get-assembla-settings",
    "no-stage-assigned#set-up-assembla",
    "no-stage-assigned#disable-assembla",
    "no-stage-assigned#get-atlassian-bamboo-settings",
    "no-stage-assigned#set-up-atlassian-bamboo",
    "no-stage-assigned#disable-atlassian-bamboo",
    "no-stage-assigned#get-bugzilla-settings",
    "no-stage-assigned#set-up-bugzilla",
    "no-stage-assigned#disable-bugzilla",
    "no-stage-assigned#get-buildkite-settings",
    "no-stage-assigned#set-up-buildkite",
    "no-stage-assigned#disable-buildkite",
    "no-stage-assigned#get-campfire-classic-settings",
    "no-stage-assigned#set-up-campfire-classic",
    "no-stage-assigned#disable-campfire-classic",
    "no-stage-assigned#get-clickup-settings",
    "no-stage-assigned#set-up-clickup",
    "no-stage-assigned#disable-clickup",
    "no-stage-assigned#get-confluence-workspace-settings",
    "no-stage-assigned#set-up-confluence-workspace",
    "no-stage-assigned#disable-confluence-workspace",
    "no-stage-assigned#get-custom-issue-tracker-settings",
    "no-stage-assigned#set-up-a-custom-issue-tracker",
    "no-stage-assigned#disable-a-custom-issue-tracker",
    "no-stage-assigned#get-datadog-settings",
    "no-stage-assigned#set-up-datadog",
    "no-stage-assigned#disable-datadog",
    "no-stage-assigned#get-diffblue-cover-settings",
    "no-stage-assigned#set-up-diffblue-cover",
    "no-stage-assigned#disable-diffblue-cover",
    "no-stage-assigned#get-discord-notifications-settings",
    "no-stage-assigned#set-up-discord-notifications",
    "no-stage-assigned#disable-discord-notifications",
    "no-stage-assigned#get-drone-settings",
    "no-stage-assigned#set-up-drone",
    "no-stage-assigned#disable-drone",
    "no-stage-assigned#get-emails-on-push-settings",
    "no-stage-assigned#set-up-emails-on-push",
    "no-stage-assigned#disable-emails-on-push",
    "no-stage-assigned#get-ewm-settings",
    "no-stage-assigned#set-up-ewm",
    "no-stage-assigned#disable-ewm",
    "no-stage-assigned#get-external-wiki-settings",
    "no-stage-assigned#set-up-an-external-wiki",
    "no-stage-assigned#disable-an-external-wiki",
    "no-stage-assigned#get-gitguardian-settings",
    "no-stage-assigned#set-up-gitguardian",
    "no-stage-assigned#disable-gitguardian",
    "no-stage-assigned#get-github-settings",
    "no-stage-assigned#set-up-github",
    "no-stage-assigned#disable-github",
    "no-stage-assigned#get-gitlab-for-slack-app-settings",
    "no-stage-assigned#set-up-gitlab-for-slack-app",
    "no-stage-assigned#disable-gitlab-for-slack-app",
    "no-stage-assigned#get-google-artifact-management-settings",
    "no-stage-assigned#set-up-google-artifact-management",
    "no-stage-assigned#disable-google-artifact-management",
    "no-stage-assigned#set-up-google-cloud-identity-and-access-management",
    "no-stage-assigned#disable-google-cloud-identity-and-access-management",
    "no-stage-assigned#get-google-chat-settings",
    "no-stage-assigned#set-up-google-chat",
    "no-stage-assigned#disable-google-chat",
    "no-stage-assigned#get-harbor-settings",
    "no-stage-assigned#set-up-harbor",
    "no-stage-assigned#disable-harbor",
    "no-stage-assigned#get-irker-settings",
    "no-stage-assigned#set-up-irker",
    "no-stage-assigned#disable-irker",
    "no-stage-assigned#get-gitlab-for-jira-cloud-app-settings",
    "no-stage-assigned#update-integration-for-a-group",
    "no-stage-assigned#get-jira-settings",
    "no-stage-assigned#set-up-jira",
    "no-stage-assigned#disable-jira",
    "no-stage-assigned#get-linear-settings",
    "no-stage-assigned#set-up-linear",
    "no-stage-assigned#disable-linear",
    "no-stage-assigned#get-matrix-notifications-settings",
    "no-stage-assigned#set-up-matrix-notifications",
    "no-stage-assigned#disable-matrix-notifications",
    "no-stage-assigned#get-mattermost-slash-commands-settings",
    "no-stage-assigned#set-up-mattermost-slash-commands",
    "no-stage-assigned#disable-mattermost-slash-commands",
    "no-stage-assigned#get-mattermost-notifications-settings",
    "no-stage-assigned#set-up-mattermost-notifications",
    "no-stage-assigned#disable-mattermost-notifications",
    "no-stage-assigned#get-microsoft-teams-notifications-settings",
    "no-stage-assigned#set-up-microsoft-teams-notifications",
    "no-stage-assigned#disable-microsoft-teams-notifications",
    "no-stage-assigned#get-mock-ci-settings",
    "no-stage-assigned#set-up-mock-ci",
    "no-stage-assigned#disable-mock-ci",
    "no-stage-assigned#get-packagist-settings",
    "no-stage-assigned#set-up-packagist",
    "no-stage-assigned#disable-packagist",
    "no-stage-assigned#get-phorge-settings",
    "no-stage-assigned#set-up-phorge",
    "no-stage-assigned#disable-phorge",
    "no-stage-assigned#get-pipeline-status-emails-settings",
    "no-stage-assigned#set-up-pipeline-status-emails",
    "no-stage-assigned#disable-pipeline-status-emails",
    "no-stage-assigned#get-pivotal-tracker-settings",
    "no-stage-assigned#set-up-pivotal-tracker",
    "no-stage-assigned#disable-pivotal-tracker",
    "no-stage-assigned#get-pumble-settings",
    "no-stage-assigned#set-up-pumble",
    "no-stage-assigned#disable-pumble",
    "no-stage-assigned#get-pushover-settings",
    "no-stage-assigned#set-up-pushover",
    "no-stage-assigned#disable-pushover",
    "no-stage-assigned#get-redmine-settings",
    "no-stage-assigned#set-up-redmine",
    "no-stage-assigned#disable-redmine",
    "no-stage-assigned#get-slack-notifications-settings",
    "no-stage-assigned#set-up-slack-notifications",
    "no-stage-assigned#disable-slack-notifications",
    "no-stage-assigned#get-squash-tm-settings",
    "no-stage-assigned#set-up-squash-tm",
    "no-stage-assigned#disable-squash-tm",
    "no-stage-assigned#get-jetbrains-teamcity-settings",
    "no-stage-assigned#set-up-jetbrains-teamcity",
    "no-stage-assigned#disable-jetbrains-teamcity",
    "no-stage-assigned#get-telegram-settings",
    "no-stage-assigned#set-up-telegram",
    "no-stage-assigned#disable-telegram",
    "no-stage-assigned#get-unify-circuit-settings",
    "no-stage-assigned#set-up-unify-circuit",
    "no-stage-assigned#disable-unify-circuit",
    "no-stage-assigned#get-webex-teams-settings",
    "no-stage-assigned#set-up-webex-teams",
    "no-stage-assigned#disable-webex-teams",
    "no-stage-assigned#get-youtrack-settings",
    "no-stage-assigned#set-up-youtrack",
    "no-stage-assigned#disable-youtrack",
    "no-stage-assigned#list-all-active-integrations",
    "no-stage-assigned#get-google-cloud-identity-and-access-management-1",
    "no-stage-assigned#get-apple-app-store-connect-settings",
    "no-stage-assigned#set-up-apple-app-store-connect",
    "no-stage-assigned#disable-apple-app-store-connect",
    "no-stage-assigned#get-asana-settings-1",
    "no-stage-assigned#set-up-asana-1",
    "no-stage-assigned#disable-asana-1",
    "no-stage-assigned#get-assembla-settings-1",
    "no-stage-assigned#set-up-assembla-1",
    "no-stage-assigned#disable-assembla-1",
    "no-stage-assigned#get-atlassian-bamboo-settings-1",
    "no-stage-assigned#set-up-atlassian-bamboo-1",
    "no-stage-assigned#disable-atlassian-bamboo-1",
    "no-stage-assigned#get-bugzilla-settings-1",
    "no-stage-assigned#set-up-bugzilla-1",
    "no-stage-assigned#disable-bugzilla-1",
    "no-stage-assigned#get-buildkite-settings-1",
    "no-stage-assigned#set-up-buildkite-1",
    "no-stage-assigned#disable-buildkite-1",
    "no-stage-assigned#get-campfire-classic-settings-1",
    "no-stage-assigned#set-up-campfire-classic-1",
    "no-stage-assigned#disable-campfire-classic-1",
    "no-stage-assigned#get-clickup-settings-1",
    "no-stage-assigned#set-up-clickup-1",
    "no-stage-assigned#disable-clickup-1",
    "no-stage-assigned#get-confluence-workspace-settings-1",
    "no-stage-assigned#set-up-confluence-workspace-1",
    "no-stage-assigned#disable-confluence-workspace-1",
    "no-stage-assigned#get-custom-issue-tracker-settings-1",
    "no-stage-assigned#set-up-a-custom-issue-tracker-1",
    "no-stage-assigned#disable-a-custom-issue-tracker-1",
    "no-stage-assigned#get-datadog-settings-1",
    "no-stage-assigned#set-up-datadog-1",
    "no-stage-assigned#disable-datadog-1",
    "no-stage-assigned#get-diffblue-cover-settings-1",
    "no-stage-assigned#set-up-diffblue-cover-1",
    "no-stage-assigned#disable-diffblue-cover-1",
    "no-stage-assigned#get-discord-notifications-settings-1",
    "no-stage-assigned#set-up-discord-notifications-1",
    "no-stage-assigned#disable-discord-notifications-1",
    "no-stage-assigned#get-drone-settings-1",
    "no-stage-assigned#set-up-drone-1",
    "no-stage-assigned#disable-drone-1",
    "no-stage-assigned#get-emails-on-push-settings-1",
    "no-stage-assigned#set-up-emails-on-push-1",
    "no-stage-assigned#disable-emails-on-push-1",
    "no-stage-assigned#get-ewm-settings-1",
    "no-stage-assigned#set-up-ewm-1",
    "no-stage-assigned#disable-ewm-1",
    "no-stage-assigned#get-external-wiki-settings-1",
    "no-stage-assigned#set-up-an-external-wiki-1",
    "no-stage-assigned#disable-an-external-wiki-1",
    "no-stage-assigned#get-gitguardian-settings-1",
    "no-stage-assigned#set-up-gitguardian-1",
    "no-stage-assigned#disable-gitguardian-1",
    "no-stage-assigned#get-github-settings-1",
    "no-stage-assigned#set-up-github-1",
    "no-stage-assigned#disable-github-1",
    "no-stage-assigned#get-gitlab-for-slack-app-settings-1",
    "no-stage-assigned#set-up-gitlab-for-slack-app-1",
    "no-stage-assigned#disable-gitlab-for-slack-app-1",
    "no-stage-assigned#get-google-artifact-management-settings-1",
    "no-stage-assigned#set-up-google-artifact-management-1",
    "no-stage-assigned#disable-google-artifact-management-1",
    "no-stage-assigned#set-up-google-cloud-identity-and-access-management-1",
    "no-stage-assigned#disable-google-cloud-identity-and-access-management-1",
    "no-stage-assigned#get-google-play-settings",
    "no-stage-assigned#set-up-google-play",
    "no-stage-assigned#disable-google-play",
    "no-stage-assigned#get-google-chat-settings-1",
    "no-stage-assigned#set-up-google-chat-1",
    "no-stage-assigned#disable-google-chat-1",
    "no-stage-assigned#get-harbor-settings-1",
    "no-stage-assigned#set-up-harbor-1",
    "no-stage-assigned#disable-harbor-1",
    "no-stage-assigned#get-irker-settings-1",
    "no-stage-assigned#set-up-irker-1",
    "no-stage-assigned#disable-irker-1",
    "no-stage-assigned#get-jenkins-settings",
    "no-stage-assigned#set-up-jenkins",
    "no-stage-assigned#disable-jenkins",
    "no-stage-assigned#get-gitlab-for-jira-cloud-app-settings-1",
    "no-stage-assigned#update-integration-for-a-project",
    "no-stage-assigned#get-jira-settings-1",
    "no-stage-assigned#set-up-jira-issues",
    "no-stage-assigned#disable-jira-1",
    "no-stage-assigned#get-linear-settings-1",
    "no-stage-assigned#set-up-linear-1",
    "no-stage-assigned#disable-linear-1",
    "no-stage-assigned#get-matrix-notifications-settings-1",
    "no-stage-assigned#set-up-matrix-notifications-1",
    "no-stage-assigned#disable-matrix-notifications-1",
    "no-stage-assigned#get-mattermost-slash-commands-settings-1",
    "no-stage-assigned#set-up-mattermost-slash-commands-1",
    "no-stage-assigned#disable-mattermost-slash-commands-1",
    "no-stage-assigned#get-mattermost-notifications-settings-1",
    "no-stage-assigned#set-up-mattermost-notifications-1",
    "no-stage-assigned#disable-mattermost-notifications-1",
    "no-stage-assigned#get-microsoft-teams-notifications-settings-1",
    "no-stage-assigned#set-up-microsoft-teams-notifications-1",
    "no-stage-assigned#disable-microsoft-teams-notifications-1",
    "no-stage-assigned#get-mock-ci-settings-1",
    "no-stage-assigned#set-up-mock-ci-1",
    "no-stage-assigned#disable-mock-ci-1",
    "no-stage-assigned#get-packagist-settings-1",
    "no-stage-assigned#set-up-packagist-1",
    "no-stage-assigned#disable-packagist-1",
    "no-stage-assigned#get-phorge-settings-1",
    "no-stage-assigned#set-up-phorge-1",
    "no-stage-assigned#disable-phorge-1",
    "no-stage-assigned#get-pipeline-status-emails-settings-1",
    "no-stage-assigned#set-up-pipeline-status-emails-1",
    "no-stage-assigned#disable-pipeline-status-emails-1",
    "no-stage-assigned#get-pivotal-tracker-settings-1",
    "no-stage-assigned#set-up-pivotal-tracker-1",
    "no-stage-assigned#disable-pivotal-tracker-1",
    "no-stage-assigned#get-pumble-settings-1",
    "no-stage-assigned#set-up-pumble-1",
    "no-stage-assigned#disable-pumble-1",
    "no-stage-assigned#get-pushover-settings-1",
    "no-stage-assigned#set-up-pushover-1",
    "no-stage-assigned#disable-pushover-1",
    "no-stage-assigned#get-redmine-settings-1",
    "no-stage-assigned#set-up-redmine-1",
    "no-stage-assigned#disable-redmine-1",
    "no-stage-assigned#get-slack-notifications-settings-1",
    "no-stage-assigned#set-up-slack-notifications-1",
    "no-stage-assigned#disable-slack-notifications-1",
    "no-stage-assigned#get-squash-tm-settings-1",
    "no-stage-assigned#set-up-squash-tm-1",
    "no-stage-assigned#disable-squash-tm-1",
    "no-stage-assigned#get-jetbrains-teamcity-settings-1",
    "no-stage-assigned#set-up-jetbrains-teamcity-1",
    "no-stage-assigned#disable-jetbrains-teamcity-1",
    "no-stage-assigned#get-telegram-settings-1",
    "no-stage-assigned#set-up-telegram-1",
    "no-stage-assigned#disable-telegram-1",
    "no-stage-assigned#get-unify-circuit-settings-1",
    "no-stage-assigned#set-up-unify-circuit-1",
    "no-stage-assigned#disable-unify-circuit-1",
    "no-stage-assigned#get-webex-teams-settings-1",
    "no-stage-assigned#set-up-webex-teams-1",
    "no-stage-assigned#disable-webex-teams-1",
    "no-stage-assigned#get-youtrack-settings-1",
    "no-stage-assigned#set-up-youtrack-1",
    "no-stage-assigned#disable-youtrack-1",
    "no-stage-assigned#list-all-active-integrations-1",
)

# The records AC-5 and AC-6 call, and the two the `array of strings` rows belong to.
OP_LIST_GROUP_INTEGRATIONS = "no-stage-assigned#list-all-active-integrations"  # GET /groups/:id/integrations
OP_LIST_PROJECT_INTEGRATIONS = "no-stage-assigned#list-all-active-integrations-1"  # GET /projects/:id/integrations
OP_SET_UP_JIRA = "no-stage-assigned#set-up-jira"  # PUT /groups/:id/integrations/jira
OP_SET_UP_JIRA_ISSUES = "no-stage-assigned#set-up-jira-issues"  # PUT /projects/:id/integrations/jira

# Every `Param` whose Kind is not SCALAR, by record: the `array of strings` rows ("Set up Jira", "Set up Jira issues").
# Every other row of the page is `string`, `boolean`, `integer` or `number`, a SCALAR.
NON_SCALAR_PARAMS: Dict[str, Dict[str, str]] = {
    OP_SET_UP_JIRA: {"project_keys": KIND_ARRAY},
    OP_SET_UP_JIRA_ISSUES: {"project_keys": KIND_ARRAY},
}

# The rows whose Required reads `yes`, by record, in table order. A record with no such row is not listed: every
# section without a table, and the tables of "Set up GitLab for Slack app", "Update integration for a group" and
# "Update integration for a project".
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "no-stage-assigned#set-up-asana": ("api_key",),
    "no-stage-assigned#set-up-assembla": ("token",),
    "no-stage-assigned#set-up-atlassian-bamboo": ("bamboo_url", "build_key", "username", "password"),
    "no-stage-assigned#set-up-bugzilla": ("new_issue_url", "issues_url", "project_url"),
    "no-stage-assigned#set-up-buildkite": ("token", "project_url"),
    "no-stage-assigned#set-up-campfire-classic": ("token",),
    "no-stage-assigned#set-up-clickup": ("issues_url", "project_url"),
    "no-stage-assigned#set-up-confluence-workspace": ("confluence_url",),
    "no-stage-assigned#set-up-a-custom-issue-tracker": ("new_issue_url", "issues_url", "project_url"),
    "no-stage-assigned#set-up-datadog": ("api_key",),
    "no-stage-assigned#set-up-diffblue-cover": (
        "diffblue_license_key",
        "diffblue_access_token_name",
        "diffblue_access_token_secret",
    ),
    "no-stage-assigned#set-up-discord-notifications": ("webhook",),
    "no-stage-assigned#set-up-drone": ("token", "drone_url"),
    "no-stage-assigned#set-up-emails-on-push": ("recipients",),
    "no-stage-assigned#set-up-ewm": ("new_issue_url", "project_url", "issues_url"),
    "no-stage-assigned#set-up-an-external-wiki": ("external_wiki_url",),
    "no-stage-assigned#set-up-gitguardian": ("token",),
    "no-stage-assigned#set-up-github": ("token", "repository_url"),
    "no-stage-assigned#set-up-google-chat": ("webhook",),
    "no-stage-assigned#set-up-google-artifact-management": (
        "artifact_registry_project_id",
        "artifact_registry_location",
        "artifact_registry_repositories",
    ),
    "no-stage-assigned#set-up-google-cloud-identity-and-access-management": (
        "workload_identity_federation_project_id",
        "workload_identity_federation_project_number",
        "workload_identity_pool_id",
        "workload_identity_pool_provider_id",
    ),
    "no-stage-assigned#set-up-harbor": ("url", "project_name", "username", "password"),
    "no-stage-assigned#set-up-irker": ("recipients",),
    "no-stage-assigned#set-up-jetbrains-teamcity": ("teamcity_url", "build_type", "username", "password"),
    "no-stage-assigned#set-up-jira": ("url", "password"),
    "no-stage-assigned#set-up-linear": ("workspace_url",),
    "no-stage-assigned#set-up-matrix-notifications": ("token", "room"),
    "no-stage-assigned#set-up-mattermost-notifications": ("webhook",),
    "no-stage-assigned#set-up-mattermost-slash-commands": ("token",),
    "no-stage-assigned#set-up-microsoft-teams-notifications": ("webhook",),
    "no-stage-assigned#set-up-mock-ci": ("mock_service_url",),
    "no-stage-assigned#set-up-packagist": ("username", "token"),
    "no-stage-assigned#set-up-phorge": ("issues_url", "project_url"),
    "no-stage-assigned#set-up-pipeline-status-emails": ("recipients",),
    "no-stage-assigned#set-up-pivotal-tracker": ("token",),
    "no-stage-assigned#set-up-pumble": ("webhook",),
    "no-stage-assigned#set-up-pushover": ("api_key", "user_key", "priority"),
    "no-stage-assigned#set-up-redmine": ("new_issue_url", "project_url", "issues_url"),
    "no-stage-assigned#set-up-slack-notifications": ("webhook",),
    "no-stage-assigned#set-up-squash-tm": ("url",),
    "no-stage-assigned#set-up-telegram": (
        "token",
        "room",
        "push_events",
        "issues_events",
        "confidential_issues_events",
        "merge_requests_events",
        "tag_push_events",
        "note_events",
        "confidential_note_events",
        "pipeline_events",
        "wiki_page_events",
    ),
    "no-stage-assigned#set-up-unify-circuit": ("webhook",),
    "no-stage-assigned#set-up-webex-teams": ("webhook",),
    "no-stage-assigned#set-up-youtrack": ("issues_url", "project_url"),
    "no-stage-assigned#set-up-apple-app-store-connect": (
        "app_store_issuer_id",
        "app_store_key_id",
        "app_store_private_key_file_name",
        "app_store_private_key",
    ),
    "no-stage-assigned#set-up-asana-1": ("api_key",),
    "no-stage-assigned#set-up-assembla-1": ("token",),
    "no-stage-assigned#set-up-atlassian-bamboo-1": ("bamboo_url", "build_key", "username", "password"),
    "no-stage-assigned#set-up-bugzilla-1": ("new_issue_url", "issues_url", "project_url"),
    "no-stage-assigned#set-up-buildkite-1": ("token", "project_url"),
    "no-stage-assigned#set-up-campfire-classic-1": ("token",),
    "no-stage-assigned#set-up-clickup-1": ("issues_url", "project_url"),
    "no-stage-assigned#set-up-confluence-workspace-1": ("confluence_url",),
    "no-stage-assigned#set-up-a-custom-issue-tracker-1": ("new_issue_url", "issues_url", "project_url"),
    "no-stage-assigned#set-up-datadog-1": ("api_key", "datadog_ci_visibility"),
    "no-stage-assigned#set-up-diffblue-cover-1": (
        "diffblue_license_key",
        "diffblue_access_token_name",
        "diffblue_access_token_secret",
    ),
    "no-stage-assigned#set-up-discord-notifications-1": ("webhook",),
    "no-stage-assigned#set-up-drone-1": ("token", "drone_url"),
    "no-stage-assigned#set-up-emails-on-push-1": ("recipients",),
    "no-stage-assigned#set-up-ewm-1": ("new_issue_url", "project_url", "issues_url"),
    "no-stage-assigned#set-up-an-external-wiki-1": ("external_wiki_url",),
    "no-stage-assigned#set-up-gitguardian-1": ("token",),
    "no-stage-assigned#set-up-github-1": ("token", "repository_url"),
    "no-stage-assigned#set-up-google-chat-1": ("webhook",),
    "no-stage-assigned#set-up-google-artifact-management-1": (
        "artifact_registry_project_id",
        "artifact_registry_location",
        "artifact_registry_repositories",
    ),
    "no-stage-assigned#set-up-google-cloud-identity-and-access-management-1": (
        "workload_identity_federation_project_id",
        "workload_identity_federation_project_number",
        "workload_identity_pool_id",
        "workload_identity_pool_provider_id",
    ),
    "no-stage-assigned#set-up-google-play": ("package_name", "service_account_key", "service_account_key_file_name"),
    "no-stage-assigned#set-up-harbor-1": ("url", "project_name", "username", "password"),
    "no-stage-assigned#set-up-irker-1": ("recipients",),
    "no-stage-assigned#set-up-jenkins": ("jenkins_url", "project_name"),
    "no-stage-assigned#set-up-jetbrains-teamcity-1": ("teamcity_url", "build_type", "username", "password"),
    "no-stage-assigned#set-up-jira-issues": ("url", "password"),
    "no-stage-assigned#set-up-linear-1": ("workspace_url",),
    "no-stage-assigned#set-up-matrix-notifications-1": ("token", "room"),
    "no-stage-assigned#set-up-mattermost-notifications-1": ("webhook",),
    "no-stage-assigned#set-up-mattermost-slash-commands-1": ("token",),
    "no-stage-assigned#set-up-microsoft-teams-notifications-1": ("webhook",),
    "no-stage-assigned#set-up-mock-ci-1": ("mock_service_url",),
    "no-stage-assigned#set-up-packagist-1": ("username", "token"),
    "no-stage-assigned#set-up-phorge-1": ("issues_url", "project_url"),
    "no-stage-assigned#set-up-pipeline-status-emails-1": ("recipients",),
    "no-stage-assigned#set-up-pivotal-tracker-1": ("token",),
    "no-stage-assigned#set-up-pumble-1": ("webhook",),
    "no-stage-assigned#set-up-pushover-1": ("api_key", "user_key", "priority"),
    "no-stage-assigned#set-up-redmine-1": ("new_issue_url", "project_url", "issues_url"),
    "no-stage-assigned#set-up-slack-notifications-1": ("webhook",),
    "no-stage-assigned#set-up-squash-tm-1": ("url",),
    "no-stage-assigned#set-up-telegram-1": (
        "token",
        "room",
        "push_events",
        "issues_events",
        "confidential_issues_events",
        "merge_requests_events",
        "tag_push_events",
        "note_events",
        "confidential_note_events",
        "pipeline_events",
        "wiki_page_events",
    ),
    "no-stage-assigned#set-up-unify-circuit-1": ("webhook",),
    "no-stage-assigned#set-up-webex-teams-1": ("webhook",),
    "no-stage-assigned#set-up-youtrack-1": ("issues_url", "project_url"),
}

# The paged records (DL-004: conventions.md "Pagination", offset paging is every list endpoint's default).
PAGED_RECORDS: Dict[str, str] = {
    OP_LIST_GROUP_INTEGRATIONS: PAGING_OFFSET,
    OP_LIST_PROJECT_INTEGRATIONS: PAGING_OFFSET,
}

# --- The calls ----------------------------------------------------------------------------------------------------

# Response keys of an integration (the integrations APIs' "List all active integrations" answer).
FIELD_ID = "id"
FIELD_SLUG = "slug"
FIELD_ACTIVE = "active"
INTEGRATION_ITEMS: Tuple[Dict[str, Any], ...] = (
    {FIELD_ID: 75, FIELD_SLUG: "jenkins", FIELD_ACTIVE: True},
    {FIELD_ID: 76, FIELD_SLUG: "slack", FIELD_ACTIVE: True},
)
# A group full path: one `--path id` value holding `/`, sent as ONE segment (conventions.md "URL-encoding path
# parameters").
GROUP_FULL_PATH = "g/sub"
GROUP_INTEGRATIONS_URL = f"{REST_BASE}/groups/g%2Fsub/integrations"
PROJECT_INTEGRATIONS_URL = f"{REST_BASE}/projects/{PROJECT_ID}/integrations"

# AC-6: "Set up Jira issues", four of its rows, each given as `-f` text or as `-F` JSON.
FIELD_URL = "url"
FIELD_JIRA_AUTH_TYPE = "jira_auth_type"
FIELD_USE_INHERITED_SETTINGS = "use_inherited_settings"
FIELD_PROJECT_KEYS = "project_keys"
JIRA_SERVER_URL = "https://jira.example.com"
JIRA_ARGV: Tuple[str, ...] = (
    OP_SET_UP_JIRA_ISSUES,
    OPTION_RAW_FIELD,
    f"{FIELD_URL}{ASSIGNED}{JIRA_SERVER_URL}",
    OPTION_FIELD,
    f"{FIELD_JIRA_AUTH_TYPE}{ASSIGNED}1",
    OPTION_FIELD,
    f"{FIELD_USE_INHERITED_SETTINGS}{ASSIGNED}true",
    OPTION_FIELD,
    f'{FIELD_PROJECT_KEYS}{ASSIGNED}["A"]',
)
JIRA_BODY: Dict[str, Any] = {
    FIELD_URL: JIRA_SERVER_URL,
    FIELD_JIRA_AUTH_TYPE: 1,
    FIELD_USE_INHERITED_SETTINGS: True,
    FIELD_PROJECT_KEYS: ["A"],
}
# No `--path id`: a `/projects/:id` path takes the configured project.
JIRA_URL = f"{REST_BASE}/projects/{PROJECT_ID}/integrations/jira"
JIRA_ANSWER: Dict[str, Any] = {FIELD_ID: 77, FIELD_SLUG: "jira", FIELD_ACTIVE: True}


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory; the entry script reads ``config/gitlab.json`` under it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` (``families.no_stage_assigned`` for the family) inside a test, after asserting its
    file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def media_type(*, value: Optional[str]) -> Optional[str]:
    """The media type of a ``Content-Type`` value, lower-cased and without its parameters; ``None`` without one."""
    if value is None:
        return None
    message = Message()
    message[HEADER_CONTENT_TYPE] = value
    return message.get_content_type()


def non_scalar_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[str, Dict[str, str]]:
    """``{operation_id: {name: Kind name}}`` of every ``Param`` whose Kind is not SCALAR, over the records with any."""
    typed = {
        record.operation_id: {
            param.name: param.kind.name for param in record.params if param.kind is not registry.Kind.SCALAR
        }
        for record in records
    }
    return {operation_id: names for operation_id, names in typed.items() if names}


def required_params(*, records: Sequence[Any]) -> Dict[str, FrozenSet[str]]:
    """``{operation_id: names}`` of every ``Param`` declared ``required=True``, over the records with any."""
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required) for record in records
    }
    return {operation_id: names for operation_id, names in required.items() if names}


# --- AC-1: nothing is pending ---------------------------------------------------------------------------------------


def test_nothing_is_pending() -> None:
    """AC-1: ``PENDING`` is empty, and ``OPERATIONS`` declares one record per Reference of the family's index rows,
    each ID once."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"PENDING holds {len(pending)} key(s); each has its record (AC-1): {pending}"
    declared = sorted(record.operation_id for record in family.OPERATIONS)
    missing = sorted(frozenset(OPERATION_IDS) - frozenset(declared))
    unknown = sorted(frozenset(declared) - frozenset(OPERATION_IDS))
    assert declared == sorted(OPERATION_IDS), (
        f"OPERATIONS declares {len(declared)} record(s), the index has {len(OPERATION_IDS)} References; missing: "
        f"{missing}; not a Reference of the family: {unknown}"
    )


# --- AC-2: every Param typed as its row -------------------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-2: the ``array of strings`` rows are ``Kind.ARRAY`` and every other ``Param`` is ``Kind.SCALAR``; the
    ``Param``s declared ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body
    and no ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    assert non_scalar_params(records=records, registry=registry) == NON_SCALAR_PARAMS, (
        "the Params that are not Kind.SCALAR are the `array of strings` rows, as Kind.ARRAY (AC-2)"
    )
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert required_params(records=records) == expected_required, (
        "required=True exactly where the row's Required reads `yes` (AC-2)"
    )
    misbodied = [
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    ]
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-2): {misbodied}"


# --- AC-3: only the list records are paged ----------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-3: the two "List all active integrations" records are ``Paging.OFFSET``; every other record is
    ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {
        record.operation_id: record.paging.name for record in family.OPERATIONS if record.paging.name != PAGING_NONE
    }
    assert paged == PAGED_RECORDS, f"the records not Paging.NONE, with their Paging (AC-3): {paged}"


# --- AC-5: a list record prints every page ----------------------------------------------------------------------------


class ListCase(NamedTuple):
    """A call of a list record and the URL of its list before the query, which each page request extends."""

    argv: Tuple[str, ...]
    url: str


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            ListCase(
                argv=(OP_LIST_GROUP_INTEGRATIONS, OPTION_PATH, f"{PATH_ID}{ASSIGNED}{GROUP_FULL_PATH}"),
                url=GROUP_INTEGRATIONS_URL,
            ),
            id="group-id-one-encoded-segment",
        ),
        pytest.param(
            ListCase(argv=(OP_LIST_PROJECT_INTEGRATIONS,), url=PROJECT_INTEGRATIONS_URL),
            id="project-id-the-configured-project",
        ),
    ],
)
def test_a_list_record_prints_every_page(
    case: ListCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-5: two pages scripted at their exact URLs, the second named by the first's ``x-next-page``; the call exits 0,
    requests both pages in order, and prints the items of both as one JSON array."""
    first_page = f"{case.url}{FIRST_PAGE_QUERY}"
    second_page = f"{case.url}{SECOND_PAGE_QUERY}"
    fake_gitlab.script(
        method=METHOD_GET, url=first_page, headers=((HEADER_NEXT_PAGE, NEXT_PAGE),), body=[INTEGRATION_ITEMS[0]]
    )
    fake_gitlab.script(
        method=METHOD_GET, url=second_page, headers=((HEADER_NEXT_PAGE, LAST_PAGE),), body=[INTEGRATION_ITEMS[1]]
    )
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_page), (METHOD_GET, second_page)], (
        "each page requested as Transport.pages does, the id one encoded segment or the configured project (AC-5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(INTEGRATION_ITEMS)), (
        f"one JSON array of every item of both pages, in page order, as print_json writes it (AC-5):\n{captured.out}"
    )


# --- AC-6: a settings write sends its typed body ------------------------------------------------------------------


def test_a_settings_write_sends_its_typed_body(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6: ``-f url=...``, ``-F jira_auth_type=1``, ``-F use_inherited_settings=true`` and
    ``-F 'project_keys=["A"]'`` send one ``PUT`` to the configured project's Jira integration whose JSON body is those
    four values: a string, an integer, a boolean and an array."""
    fake_gitlab.script(method=METHOD_PUT, url=JIRA_URL, body=JIRA_ANSWER)
    code = run_call(root=project, argv=JIRA_ARGV)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(JIRA_ARGV)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_PUT, JIRA_URL)], "one PUT to the record's path, id the configured project"
    request = fake_gitlab.requests[0]
    assert media_type(value=request.header(name=HEADER_CONTENT_TYPE)) == CONTENT_TYPE_JSON, (
        f"the body's Content-Type: {request.header(name=HEADER_CONTENT_TYPE)!r}"
    )
    assert request.json() == JIRA_BODY, "the JSON body holds the four values, each as the JSON value given (AC-6)"
