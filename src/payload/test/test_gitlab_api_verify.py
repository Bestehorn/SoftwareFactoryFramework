"""Tests for ``gitlab_api/families/verify.py``, the ``verify`` endpoint family of the GitLab wrapper (issue #37, the
verify slice of the wrapper rewrite; ``change.md`` AC-1, AC-3, AC-4 and AC-6).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/verify.md``) and
``docs/api-reference/gitlab/rest/verify.md`` (each section's endpoints, its heading, and the ``In``, ``Type`` and
``Required`` columns of its ``| Attribute | In | Type | Required |`` table). What is pinned:

- AC-1 (as issue #63 design.md D9 restates it): ``PENDING`` is exactly the keys of the three IDs kept pending (DL-003:
  the two ``*artifact_path`` downloads and the merge-train add); ``OPERATIONS`` declares every Reference of the family
  but those three IDs and ``verify#runners-api-1``, whose endpoints each have a section of their own, each key of an
  ID once; a section with several endpoints has one record per endpoint, its base record (the section's first) first
  and the others in the section's order (issue #63 AC-1.1, AC-1.3, design.md D1, D8);
- AC-3: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``ARRAY_OF_HASHES`` for a Type ``array of hashes``,
  ``array of hash`` or ``array of strategy JSON objects``, ``ARRAY`` for any other Type holding ``array``, ``HASH`` for
  ``hash`` or ``object``); the ``required`` ``Param``s, exactly the Required ``yes`` rows that are query or body
  attributes; a JSON body and no ``fixed`` pairs on every record. A member row (``strategies:name``,
  ``platform_kubernetes_attributes[api_url]``, ``assets:links``, ``test_splits[].path``) is no ``Param``: it goes
  inside its parent row (AC-2); a ``not[...]`` row with no ``not`` row is its own ``Param``;
- AC-4: the records that are not ``Paging.NONE`` are the ``GET`` sections whose heading begins with "List", each
  ``Paging.OFFSET`` but ``verify#list-pipelines`` (``Paging.KEYSET``, conventions.md: keyset only), and
  ``verify#list-all-scopes-for-a-runner-controller`` is not among them (it answers one object; DL-004); with each, the
  paging rows of its section the record declares (``page``/``per_page`` for OFFSET; ``pagination``, ``per_page``,
  ``order_by``, ``sort`` for KEYSET — conventions.md "Offset-based", "Keyset-based");
- AC-6: each paged record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for every
  placeholder of its path against a fake host serving one item on each of two pages — the second asked for by
  ``x-next-page`` (OFFSET) or at the first page's ``Link`` ``rel="next"`` URL (KEYSET) — exits 0, requests both pages
  at their exact URLs, and prints both items as one JSON array (``print_json``).

AC-2 and AC-5 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, so the module collects whatever the family declares. The fake GitLab host and the socket guard
(``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_verify.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Callable, Dict, FrozenSet, List, Mapping, NamedTuple, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_verify_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.verify"
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
TOKEN = "glpat-gitlab-api-verify-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
METHOD_GET = "GET"
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
HEADER_NEXT_PAGE = "x-next-page"
HEADER_LINK = "Link"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

# Transport.pages: OFFSET adds `per_page=MAX_PER_PAGE` to the first request, and the next page's request sets `page` to
# the `x-next-page` value (#13 AC-2.5); KEYSET sends the first request as the record's path and query, then requests the
# `Link` rel="next" URL as given (#13 AC-2.6).
FIRST_PAGE_QUERY = "per_page=100"
NEXT_PAGE = "2"
NEXT_PAGE_QUERY = f"page={NEXT_PAGE}"
LAST_PAGE = ""  # an empty `x-next-page`: no next page
# conventions.md "Keyset-based", `GET /pipelines`: `cursor` from the `Link` header, only `order_by=created_at` and
# `sort=desc`.
KEYSET_NEXT_QUERY = "cursor=eyJpZCI6IjEwIn0%3D&order_by=created_at&sort=desc"

# A path parameter as operations-index.md and rest/verify.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` and `registry.Paging` member names the tables hold.
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"
PAGING_KEYSET = "KEYSET"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: the Reference of every row linking rest/verify.md, written `verify#<anchor>`, sorted.
INDEX_REFERENCES: Tuple[str, ...] = (
    "verify#add-a-cluster-to-a-project",
    "verify#add-a-deploy-key-for-a-project",
    "verify#add-a-merge-request-to-a-merge-train",
    "verify#add-deploy-key",
    "verify#add-instance-scope",
    "verify#add-runner-scope",
    "verify#approve-or-reject-a-deployment",
    "verify#assign-a-runner-to-project",
    "verify#cancel-a-job",
    "verify#cancel-all-jobs-for-a-pipeline",
    "verify#collect-release-evidence",
    "verify#create-a-deployment",
    "verify#create-a-feature-flag",
    "verify#create-a-feature-flag-user-list",
    "verify#create-a-freeze-period",
    "verify#create-a-group-cluster",
    "verify#create-a-group-deploy-token",
    "verify#create-a-group-variable",
    "verify#create-a-new-pipeline",
    "verify#create-a-new-pipeline-schedule",
    "verify#create-a-project-deploy-token",
    "verify#create-a-release",
    "verify#create-a-release-link",
    "verify#create-a-runner",
    "verify#create-a-runner-controller-token",
    "verify#create-a-trigger-token",
    "verify#create-a-url-configuration",
    "verify#create-a-variable",
    "verify#create-a-variable-for-a-pipeline-schedule",
    "verify#create-an-agent",
    "verify#create-an-agent-token",
    "verify#create-an-environment",
    "verify#create-an-instance-cluster",
    "verify#create-instance-variable",
    "verify#create-or-update-a-feature-flag",
    "verify#delete-a-deploy-key",
    "verify#delete-a-deployment",
    "verify#delete-a-feature",
    "verify#delete-a-feature-flag",
    "verify#delete-a-freeze-period",
    "verify#delete-a-group-cluster",
    "verify#delete-a-group-deploy-token",
    "verify#delete-a-group-variable",
    "verify#delete-a-pipeline",
    "verify#delete-a-pipeline-schedule",
    "verify#delete-a-pipeline-trigger-token",
    "verify#delete-a-project-deploy-token",
    "verify#delete-a-release",
    "verify#delete-a-release-link",
    "verify#delete-a-runner-by-authentication-token",
    "verify#delete-a-runner-by-id",
    "verify#delete-a-runner-controller",
    "verify#delete-a-url-configuration",
    "verify#delete-a-variable",
    "verify#delete-a-variable-for-a-pipeline-schedule",
    "verify#delete-all-job-artifacts-in-a-project",
    "verify#delete-an-agent",
    "verify#delete-an-environment",
    "verify#delete-cluster-from-a-project",
    "verify#delete-feature-flag-user-list",
    "verify#delete-instance-cluster",
    "verify#delete-instance-variable",
    "verify#delete-job-artifacts",
    "verify#delete-multiple-stopped-review-apps",
    "verify#discover-job-router-information",
    "verify#download-a-release-asset",
    "verify#download-a-single-artifact-file-by-job-id",
    "verify#download-a-single-artifact-file-by-reference-name",
    "verify#download-job-artifacts-by-job-id",
    "verify#download-job-artifacts-by-reference-name",
    "verify#enable-a-deploy-key",
    "verify#erase-a-job",
    "verify#get-a-release-by-a-tag-name",
    "verify#get-a-single-protected-environment",
    "verify#get-the-latest-release",
    "verify#initialize-test-balancing-for-a-parallel-job",
    "verify#keep-job-artifacts",
    "verify#list-all-agent-tokens",
    "verify#list-all-agents",
    "verify#list-all-available-runners",
    "verify#list-all-cicd-templates",
    "verify#list-all-clusters-in-a-project",
    "verify#list-all-deploy-keys",
    "verify#list-all-deploy-tokens",
    "verify#list-all-environments",
    "verify#list-all-feature-flag-definitions",
    "verify#list-all-feature-flag-user-lists-for-a-project",
    "verify#list-all-feature-flags",
    "verify#list-all-files-in-the-artifacts-archive",
    "verify#list-all-group-level-protected-environments",
    "verify#list-all-group-variables",
    "verify#list-all-instance-variables",
    "verify#list-all-jobs-by-pipeline",
    "verify#list-all-jobs-for-a-project",
    "verify#list-all-jobs-processed-by-a-runner",
    "verify#list-all-merge-requests-associated-with-a-deployment",
    "verify#list-all-merge-requests-in-a-merge-train",
    "verify#list-all-merge-trains-for-a-project",
    "verify#list-all-of-a-groups-runners",
    "verify#list-all-of-a-projects-runners",
    "verify#list-all-pipeline-schedules",
    "verify#list-all-pipelines-triggered-by-a-pipeline-schedule",
    "verify#list-all-project-deployments",
    "verify#list-all-release-links",
    "verify#list-all-releases-in-a-group",
    "verify#list-all-resource-groups",
    "verify#list-all-runner-controller-tokens",
    "verify#list-all-runner-controllers",
    "verify#list-all-runners",
    "verify#list-all-runners-managers",
    "verify#list-all-scopes-for-a-runner-controller",
    "verify#list-all-trigger-jobs-by-pipeline",
    "verify#list-all-url-configurations",
    "verify#list-deploy-keys-for-project",
    "verify#list-feature-flags-for-a-project",
    "verify#list-freeze-periods",
    "verify#list-group-clusters",
    "verify#list-group-deploy-tokens",
    "verify#list-instance-clusters",
    "verify#list-pipelines",
    "verify#list-project-deploy-keys-for-user",
    "verify#list-project-deploy-tokens",
    "verify#list-project-pipelines",
    "verify#list-project-trigger-tokens",
    "verify#list-project-variables",
    "verify#list-protected-environments",
    "verify#list-releases",
    "verify#list-upcoming-jobs-for-a-specific-resource-group",
    "verify#metadata-api-1",
    "verify#protect-a-single-environment",
    "verify#protect-a-single-environment-1",
    "verify#register-a-runner-controller",
    "verify#remove-instance-scope",
    "verify#remove-runner-scope",
    "verify#request-the-next-batch-of-tests",
    "verify#reset-groups-runner-registration-token",
    "verify#reset-instances-runner-registration-token",
    "verify#reset-projects-runner-registration-token",
    "verify#reset-runners-authentication-token-by-using-the-current-token",
    "verify#reset-runners-authentication-token-by-using-the-runner-id",
    "verify#retrieve-a-cluster-from-a-project",
    "verify#retrieve-a-deploy-key",
    "verify#retrieve-a-deployment",
    "verify#retrieve-a-feature-flag",
    "verify#retrieve-a-feature-flag-user-list",
    "verify#retrieve-a-freeze-period",
    "verify#retrieve-a-group-cluster",
    "verify#retrieve-a-group-deploy-token",
    "verify#retrieve-a-job-by-job-id",
    "verify#retrieve-a-job-by-job-token",
    "verify#retrieve-a-log-file-for-a-job",
    "verify#retrieve-a-pipeline-schedule",
    "verify#retrieve-a-project-deploy-token",
    "verify#retrieve-a-release-link",
    "verify#retrieve-a-resource-group",
    "verify#retrieve-a-single-instance-cluster",
    "verify#retrieve-a-single-pipeline",
    "verify#retrieve-a-single-protected-environment",
    "verify#retrieve-a-single-runner-controller",
    "verify#retrieve-a-single-runner-controller-token",
    "verify#retrieve-a-single-variable",
    "verify#retrieve-a-test-report-for-a-pipeline",
    "verify#retrieve-a-test-report-summary-for-a-pipeline",
    "verify#retrieve-a-url-configuration",
    "verify#retrieve-a-variable-for-a-pipeline-schedule",
    "verify#retrieve-an-agent",
    "verify#retrieve-an-agent-token",
    "verify#retrieve-an-environment",
    "verify#retrieve-certificate-based-clusters",
    "verify#retrieve-current-job-for-a-resource-group",
    "verify#retrieve-details-of-a-cicd-template",
    "verify#retrieve-details-of-a-group-variable",
    "verify#retrieve-feature-flag-settings",
    "verify#retrieve-gitlab-agent-for-kubernetes-by-ci_job_token",
    "verify#retrieve-instance-variable-details",
    "verify#retrieve-merge-train-status",
    "verify#retrieve-pipeline-variables",
    "verify#retrieve-runners-details",
    "verify#retrieve-the-latest-pipeline",
    "verify#retrieve-trigger-token-details",
    "verify#retry-a-job",
    "verify#retry-jobs-in-a-pipeline",
    "verify#revoke-a-runner-controller-token",
    "verify#revoke-an-agent-token",
    "verify#rotate-a-runner-controller-token",
    "verify#run-a-job",
    "verify#run-a-pipeline-schedule-immediately",
    "verify#runners-api-1",
    "verify#set-percentage-of-actors-rollout",
    "verify#stop-an-environment",
    "verify#stop-stale-environments",
    "verify#trigger-a-pipeline-with-a-token",
    "verify#unassign-a-runner-from-project",
    "verify#unprotect-a-single-environment",
    "verify#unprotect-a-single-environment-1",
    "verify#update-a-cluster-in-a-project",
    "verify#update-a-deploy-key",
    "verify#update-a-deployment",
    "verify#update-a-feature-flag",
    "verify#update-a-feature-flag-user-list",
    "verify#update-a-freeze-period",
    "verify#update-a-group-cluster",
    "verify#update-a-group-variable",
    "verify#update-a-pipeline-schedule",
    "verify#update-a-pipeline-trigger-token",
    "verify#update-a-protected-environment",
    "verify#update-a-protected-environment-1",
    "verify#update-a-release",
    "verify#update-a-release-link",
    "verify#update-a-resource-group",
    "verify#update-a-runner-controller",
    "verify#update-a-variable",
    "verify#update-a-variable-for-a-pipeline-schedule",
    "verify#update-an-existing-environment",
    "verify#update-an-instance-cluster",
    "verify#update-feature-flag-settings",
    "verify#update-instance-variable",
    "verify#update-ownership-of-a-pipeline-schedule",
    "verify#update-pipeline-metadata",
    "verify#update-runners-details",
    "verify#validate-cicd-configuration",
    "verify#validate-existing-cicd-configuration",
    "verify#verify-authentication-for-a-registered-runner",
)

# DL-003: the three IDs kept pending, and the keys of their rows (rest/verify.md "Download a single artifact file by
# job ID", "Download a single artifact file by reference name", "Add a merge request to a merge train"; one endpoint
# each).
KEPT_PENDING_IDS: FrozenSet[str] = frozenset(
    {
        "verify#download-a-single-artifact-file-by-job-id",
        "verify#download-a-single-artifact-file-by-reference-name",
        "verify#add-a-merge-request-to-a-merge-train",
    }
)
KEPT_PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("GET", "/projects/:id/jobs/:job_id/artifacts/*artifact_path"),
        ("GET", "/projects/:id/jobs/artifacts/:ref_name/raw/*artifact_path"),
        ("POST", "/projects/:id/merge_trains/merge_requests/:merge_request_iid"),
    }
)
# The section "Runners API" (`verify#runners-api-1`) lists five endpoints, each the endpoint of a section of its own
# ("List all available runners", "List all runners", "List all jobs processed by a runner", "List all of a project's
# runners", "List all of a group's runners"): no record.
NO_RECORD_ID = "verify#runners-api-1"
# The other sections with several endpoints (issue #63, design.md D1, D8): "Metadata API", "Get the latest release" and
# "List all of a group's runners". Each ID's base record takes the section's first endpoint ...
BASE_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "verify#metadata-api-1": ("GET", "/metadata"),
    "verify#get-the-latest-release": ("GET", "/projects/:id/releases/permalink/latest"),
    "verify#list-all-of-a-groups-runners": ("GET", "/groups/:id/runners"),
}
# ... and the records after it take the section's other endpoints, in the order its endpoint line lists them.
OTHER_ENDPOINT_KEYS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "verify#metadata-api-1": (("GET", "/version"),),
    "verify#get-the-latest-release": (
        ("GET", "/projects/:id/releases/permalink/latest/evidence"),
        ("GET", "/projects/:id/releases/permalink/latest/downloads/bin/asset.exe"),
    ),
    "verify#list-all-of-a-groups-runners": (("GET", "/groups/:id/runners/all"),),
}
PENDING_KEYS: FrozenSet[Tuple[str, str]] = KEPT_PENDING_KEYS

# rest/verify.md: every query and body attribute whose Kind is not SCALAR, by record (AC-3). Every other attribute's
# Type is a scalar one (`string`, `integer`, `boolean`, `datetime`, `JSON`, `integer or string`, ...). A record with
# none is not listed.
NON_SCALAR_PARAMS: Dict[str, Dict[str, str]] = {
    "verify#add-a-cluster-to-a-project": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#create-a-feature-flag": {"strategies": KIND_ARRAY_OF_HASHES},
    "verify#create-a-group-cluster": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#create-a-group-deploy-token": {"scopes": KIND_ARRAY},
    "verify#create-a-new-pipeline": {"variables": KIND_ARRAY, "inputs": KIND_HASH},
    "verify#create-a-new-pipeline-schedule": {"inputs": KIND_HASH},
    "verify#create-a-project-deploy-token": {"scopes": KIND_ARRAY},
    "verify#create-a-release": {"milestones": KIND_ARRAY, "assets": KIND_HASH},
    "verify#create-a-runner": {"info": KIND_HASH, "tag_list": KIND_ARRAY},
    "verify#create-an-instance-cluster": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#delete-a-group-variable": {"filter": KIND_HASH},
    "verify#delete-a-variable": {"filter": KIND_HASH},
    "verify#initialize-test-balancing-for-a-parallel-job": {"test_splits": KIND_ARRAY_OF_HASHES},
    "verify#list-all-available-runners": {"tag_list": KIND_ARRAY},
    "verify#list-all-jobs-by-pipeline": {"scope": KIND_ARRAY},
    "verify#list-all-jobs-for-a-project": {"scope": KIND_ARRAY},
    "verify#list-all-merge-requests-associated-with-a-deployment": {
        "assignee_username": KIND_ARRAY,
        "labels": KIND_ARRAY,
        "not[assignee_username]": KIND_ARRAY,
        "not[labels]": KIND_ARRAY,
    },
    "verify#list-all-of-a-groups-runners": {"tag_list": KIND_ARRAY},
    "verify#list-all-of-a-projects-runners": {"tag_list": KIND_ARRAY},
    "verify#list-all-runners": {"tag_list": KIND_ARRAY},
    "verify#list-all-trigger-jobs-by-pipeline": {"scope": KIND_ARRAY},
    "verify#protect-a-single-environment": {"deploy_access_levels": KIND_ARRAY, "approval_rules": KIND_ARRAY},
    "verify#protect-a-single-environment-1": {"deploy_access_levels": KIND_ARRAY, "approval_rules": KIND_ARRAY},
    "verify#retrieve-a-single-variable": {"filter": KIND_HASH},
    "verify#retrieve-details-of-a-group-variable": {"filter": KIND_HASH},
    "verify#retry-a-job": {"job_inputs": KIND_HASH, "inputs": KIND_HASH},
    "verify#run-a-job": {"job_inputs": KIND_HASH, "job_variables_attributes": KIND_ARRAY_OF_HASHES},
    "verify#trigger-a-pipeline-with-a-token": {"variables": KIND_HASH, "inputs": KIND_HASH},
    "verify#update-a-cluster-in-a-project": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#update-a-feature-flag": {"strategies": KIND_ARRAY_OF_HASHES},
    "verify#update-a-group-cluster": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#update-a-group-variable": {"filter": KIND_HASH},
    "verify#update-a-pipeline-schedule": {"inputs": KIND_HASH},
    "verify#update-a-protected-environment": {"deploy_access_levels": KIND_ARRAY, "approval_rules": KIND_ARRAY},
    "verify#update-a-protected-environment-1": {"deploy_access_levels": KIND_ARRAY, "approval_rules": KIND_ARRAY},
    "verify#update-a-release": {"milestones": KIND_ARRAY},
    "verify#update-a-variable": {"filter": KIND_HASH},
    "verify#update-an-instance-cluster": {"platform_kubernetes_attributes": KIND_HASH},
    "verify#update-runners-details": {"tag_list": KIND_ARRAY},
}

# rest/verify.md: the query and body attributes whose Required reads `yes`, by record, in table order (AC-3). A record
# with none is not listed; a path row is no Param, and a member row (`platform_kubernetes_attributes[api_url]`,
# `test_splits[].path`) is part of its parent.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "verify#add-a-cluster-to-a-project": ("name", "platform_kubernetes_attributes"),
    "verify#add-a-deploy-key-for-a-project": ("key", "title"),
    "verify#add-deploy-key": ("key", "title"),
    "verify#approve-or-reject-a-deployment": ("status",),
    "verify#assign-a-runner-to-project": ("runner_id",),
    "verify#create-a-deployment": ("environment", "sha", "ref", "tag", "status"),
    "verify#create-a-feature-flag": ("name", "version"),
    "verify#create-a-feature-flag-user-list": ("name", "user_xids"),
    "verify#create-a-freeze-period": ("freeze_start", "freeze_end"),
    "verify#create-a-group-cluster": ("name", "platform_kubernetes_attributes"),
    "verify#create-a-group-deploy-token": ("name", "scopes"),
    "verify#create-a-group-variable": ("key", "value"),
    "verify#create-a-new-pipeline": ("ref",),
    "verify#create-a-new-pipeline-schedule": ("cron", "description", "ref"),
    "verify#create-a-project-deploy-token": ("name", "scopes"),
    "verify#create-a-release": ("tag_name", "ref"),
    "verify#create-a-release-link": ("name", "url"),
    "verify#create-a-runner": ("token",),
    "verify#create-a-runner-controller-token": ("description",),
    "verify#create-a-trigger-token": ("description",),
    "verify#create-a-url-configuration": ("url",),
    "verify#create-a-variable": ("key", "value"),
    "verify#create-a-variable-for-a-pipeline-schedule": ("key", "value"),
    "verify#create-an-agent": ("name",),
    "verify#create-an-agent-token": ("name",),
    "verify#create-an-environment": ("name",),
    "verify#create-an-instance-cluster": ("name", "platform_kubernetes_attributes"),
    "verify#create-instance-variable": ("key", "value"),
    "verify#create-or-update-a-feature-flag": ("value",),
    "verify#delete-a-runner-by-authentication-token": ("token",),
    "verify#download-job-artifacts-by-reference-name": ("job",),
    "verify#get-the-latest-release": ("suffix_path",),
    "verify#initialize-test-balancing-for-a-parallel-job": ("test_splits",),
    "verify#protect-a-single-environment": ("name", "deploy_access_levels"),
    "verify#protect-a-single-environment-1": ("name", "deploy_access_levels"),
    "verify#reset-runners-authentication-token-by-using-the-current-token": ("token",),
    "verify#retrieve-certificate-based-clusters": ("group_id",),
    "verify#retrieve-gitlab-agent-for-kubernetes-by-ci_job_token": ("CI_JOB_TOKEN",),
    "verify#stop-stale-environments": ("before",),
    "verify#trigger-a-pipeline-with-a-token": ("ref", "token"),
    "verify#update-a-deployment": ("status",),
    "verify#update-a-group-variable": ("value",),
    "verify#update-a-variable": ("value",),
    "verify#update-an-existing-environment": ("environment_id",),
    "verify#update-feature-flag-settings": ("minimum_role",),
    "verify#update-instance-variable": ("value",),
    "verify#update-pipeline-metadata": ("name",),
    "verify#update-runners-details": ("runner_id",),
    "verify#validate-cicd-configuration": ("content",),
    "verify#verify-authentication-for-a-registered-runner": ("token",),
}

# conventions.md "Offset-based" and "Keyset-based": the query names of each paging method, by `registry.Paging` name.
PAGING_PARAMETERS: Dict[str, FrozenSet[str]] = {
    PAGING_OFFSET: frozenset({"page", "per_page"}),
    PAGING_KEYSET: frozenset({"pagination", "per_page", "order_by", "sort"}),
}
# The paging rows a list section's table holds: both offset rows, none, or (`GET /pipelines`) `order_by` and `sort`.
PAGE_AND_PER_PAGE: FrozenSet[str] = frozenset({"page", "per_page"})
NO_PAGING_ROWS: FrozenSet[str] = frozenset()
ORDER_BY_AND_SORT: FrozenSet[str] = frozenset({"order_by", "sort"})


class PagedRecord(NamedTuple):
    """A list section's record: its ``Paging`` name, the paging rows of its table, and its path (the section's endpoint,
    or of several its first)."""

    paging: str
    paging_rows: FrozenSet[str]
    path: str


# rest/verify.md: every section that is a `GET` headed "List", but "List all scopes for a runner controller" (AC-4,
# DL-004). The two part-1 lists are among them.
PAGED_RECORDS: Dict[str, PagedRecord] = {
    "verify#list-all-agent-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/cluster_agents/:agent_id/tokens"
    ),
    "verify#list-all-agents": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/cluster_agents"
    ),
    "verify#list-all-available-runners": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/runners"
    ),
    "verify#list-all-cicd-templates": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/templates/gitlab_ci_ymls"
    ),
    "verify#list-all-clusters-in-a-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/clusters"
    ),
    "verify#list-all-deploy-keys": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/deploy_keys"
    ),
    "verify#list-all-deploy-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/deploy_tokens"
    ),
    "verify#list-all-environments": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/environments"
    ),
    "verify#list-all-feature-flag-definitions": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/features/definitions"
    ),
    "verify#list-all-feature-flag-user-lists-for-a-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/feature_flags_user_lists"
    ),
    "verify#list-all-feature-flags": PagedRecord(paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/features"),
    "verify#list-all-files-in-the-artifacts-archive": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/jobs/:job_id/artifacts/tree"
    ),
    "verify#list-all-group-level-protected-environments": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/groups/:id/protected_environments"
    ),
    "verify#list-all-group-variables": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/groups/:id/variables"
    ),
    "verify#list-all-instance-variables": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/admin/ci/variables"
    ),
    "verify#list-all-jobs-by-pipeline": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/pipelines/:pipeline_id/jobs"
    ),
    "verify#list-all-jobs-for-a-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/jobs"
    ),
    "verify#list-all-jobs-processed-by-a-runner": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/runners/:id/jobs"
    ),
    "verify#list-all-merge-requests-associated-with-a-deployment": PagedRecord(
        paging=PAGING_OFFSET,
        paging_rows=PAGE_AND_PER_PAGE,
        path="/projects/:id/deployments/:deployment_id/merge_requests",
    ),
    "verify#list-all-merge-requests-in-a-merge-train": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/projects/:id/merge_trains/:target_branch"
    ),
    "verify#list-all-merge-trains-for-a-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/projects/:id/merge_trains"
    ),
    "verify#list-all-of-a-groups-runners": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/groups/:id/runners"
    ),
    "verify#list-all-of-a-projects-runners": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/runners"
    ),
    "verify#list-all-pipeline-schedules": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/pipeline_schedules"
    ),
    "verify#list-all-pipelines-triggered-by-a-pipeline-schedule": PagedRecord(
        paging=PAGING_OFFSET,
        paging_rows=PAGE_AND_PER_PAGE,
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines",
    ),
    "verify#list-all-project-deployments": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/deployments"
    ),
    "verify#list-all-release-links": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/releases/:tag_name/assets/links"
    ),
    "verify#list-all-releases-in-a-group": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/groups/:id/releases"
    ),
    "verify#list-all-resource-groups": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/resource_groups"
    ),
    "verify#list-all-runner-controller-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/runner_controllers/:id/tokens"
    ),
    "verify#list-all-runner-controllers": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/runner_controllers"
    ),
    "verify#list-all-runners": PagedRecord(paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/runners/all"),
    "verify#list-all-runners-managers": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/runners/:id/managers"
    ),
    "verify#list-all-trigger-jobs-by-pipeline": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/pipelines/:pipeline_id/trigger_jobs"
    ),
    "verify#list-all-url-configurations": PagedRecord(
        paging=PAGING_OFFSET,
        paging_rows=NO_PAGING_ROWS,
        path="/projects/:id/cluster_agents/:agent_id/url_configurations",
    ),
    "verify#list-deploy-keys-for-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/deploy_keys"
    ),
    "verify#list-feature-flags-for-a-project": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/feature_flags"
    ),
    "verify#list-freeze-periods": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/freeze_periods"
    ),
    "verify#list-group-clusters": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/groups/:id/clusters"
    ),
    "verify#list-group-deploy-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/groups/:id/deploy_tokens"
    ),
    "verify#list-instance-clusters": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/admin/clusters"
    ),
    "verify#list-pipelines": PagedRecord(paging=PAGING_KEYSET, paging_rows=ORDER_BY_AND_SORT, path="/pipelines"),
    "verify#list-project-deploy-keys-for-user": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/users/:id_or_username/project_deploy_keys"
    ),
    "verify#list-project-deploy-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/deploy_tokens"
    ),
    "verify#list-project-pipelines": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/pipelines"
    ),
    "verify#list-project-trigger-tokens": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/triggers"
    ),
    "verify#list-project-variables": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/variables"
    ),
    "verify#list-protected-environments": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=NO_PAGING_ROWS, path="/projects/:id/protected_environments"
    ),
    "verify#list-releases": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/releases"
    ),
    "verify#list-upcoming-jobs-for-a-specific-resource-group": PagedRecord(
        paging=PAGING_OFFSET, paging_rows=PAGE_AND_PER_PAGE, path="/projects/:id/resource_groups/:key/upcoming_jobs"
    ),
}


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
    """Import ``gitlab_api.<name>`` (``families.verify`` for the family) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
    return "\n".join(lines)


def mapping_difference(*, declared: Mapping[Any, Any], expected: Mapping[Any, Any]) -> str:
    """The keys ``declared`` lacks or has beyond ``expected``, and each key whose value differs."""
    lines = [set_difference(declared=set(declared), expected=set(expected))]
    lines.extend(
        f"{key!r}: declared {declared[key]!r}, expected {expected[key]!r}"
        for key in sorted(set(declared) & set(expected))
        if declared[key] != expected[key]
    )
    return "\n".join(line for line in lines if line)


def endpoints_by_id(*, records: Sequence[Any]) -> Dict[str, Tuple[Tuple[str, str], ...]]:
    """``{operation_id: ((method, path), ...)}`` over ``records``, each ID's keys in declaration order."""
    declared: Dict[str, List[Tuple[str, str]]] = {}
    for record in records:
        declared.setdefault(record.operation_id, []).append((record.method, record.path))
    return {operation_id: tuple(keys) for operation_id, keys in declared.items()}


def repeated_keys(*, endpoints: Mapping[str, Sequence[Tuple[str, str]]]) -> List[Tuple[str, Tuple[str, str]]]:
    """Each ``(operation_id, key)`` that ``endpoints`` holds more than once for its ID, sorted."""
    return sorted(
        {(operation_id, key) for operation_id, keys in endpoints.items() for key in keys if list(keys).count(key) > 1}
    )


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


def declared_paging_rows(*, record: Any) -> FrozenSet[str]:
    """The names of ``PAGING_PARAMETERS`` for the record's ``Paging`` that the record declares as ``Param``s."""
    names = frozenset(param.name for param in record.params)
    return names & PAGING_PARAMETERS.get(record.paging.name, NO_PAGING_ROWS)


def path_values(*, path: str) -> Dict[str, str]:
    """A distinct number for each placeholder of ``path``, in path order: ``101``, ``102``, ..."""
    names = dict.fromkeys(match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=path))
    return {name: str(FIRST_PATH_VALUE + position) for position, name in enumerate(names)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each placeholder replaced by its value (the values are digits, so nothing is encoded)."""
    return PLACEHOLDER.sub(repl=lambda match: values[match.group(GROUP_NAME)], string=path)


class Page(NamedTuple):
    """One page the fake host serves: its exact URL and the paging headers it answers with."""

    url: str
    headers: Tuple[Tuple[str, str], ...]


def offset_pages(*, url: str) -> Tuple[Page, Page]:
    """Two OFFSET pages of the list at ``url``: the first names page 2 in ``x-next-page``, the second names none."""
    first = f"{url}?{FIRST_PAGE_QUERY}"
    return (
        Page(url=first, headers=((HEADER_NEXT_PAGE, NEXT_PAGE),)),
        Page(url=f"{first}&{NEXT_PAGE_QUERY}", headers=((HEADER_NEXT_PAGE, LAST_PAGE),)),
    )


def keyset_pages(*, url: str) -> Tuple[Page, Page]:
    """Two KEYSET pages of the list at ``url``: the first names the second in ``Link`` rel="next", the second has no
    ``Link``."""
    following = f"{url}?{KEYSET_NEXT_QUERY}"
    return (
        Page(url=url, headers=((HEADER_LINK, f'<{following}>; rel="next"'),)),
        Page(url=following, headers=()),
    )


# The two pages a list of each paging method is served as.
PAGE_CHAINS: Dict[str, Callable[..., Tuple[Page, Page]]] = {
    PAGING_OFFSET: offset_pages,
    PAGING_KEYSET: keyset_pages,
}


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


def list_params() -> List[Any]:
    """One case per entry of ``PAGED_RECORDS``, named by its anchor."""
    return [
        pytest.param(operation_id, listed, id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id, listed in PAGED_RECORDS.items()
    ]


# --- AC-1: what stays pending ---------------------------------------------------------------------------------------


def test_only_the_kept_keys_are_pending() -> None:
    """AC-1, UB-3, issue #63 AC-1.1, AC-1.3 (design.md D9): ``PENDING`` is the kept IDs' keys, and ``OPERATIONS``
    declares every index Reference of the family but the kept IDs and ``verify#runners-api-1``, each key of an ID
    once; an ID of several records is a section's, its base record first and then its other endpoints in the section's
    order."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "verify.PENDING is not the keys AC-1 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )
    endpoints = endpoints_by_id(records=family.OPERATIONS)
    repeated = repeated_keys(endpoints=endpoints)
    assert not repeated, f"verify.OPERATIONS declares these keys of one ID more than once: {repeated}"
    expected = frozenset(INDEX_REFERENCES) - KEPT_PENDING_IDS - {NO_RECORD_ID}
    assert frozenset(endpoints) == expected, (
        f"verify.OPERATIONS declares {len(endpoints)} ID(s), AC-1 expects {len(expected)}:\n"
        + set_difference(declared=set(endpoints), expected=set(expected))
    )
    bases = {operation_id: keys[0] for operation_id, keys in endpoints.items() if operation_id in BASE_ENDPOINTS}
    assert bases == BASE_ENDPOINTS, "each section's first record is not its base record (issue #63 D1):\n" + (
        mapping_difference(declared=bases, expected=BASE_ENDPOINTS)
    )
    others = {operation_id: keys[1:] for operation_id, keys in endpoints.items() if len(keys) > 1}
    assert others == OTHER_ENDPOINT_KEYS, "the records after a base record are not its section's other endpoints:\n" + (
        mapping_difference(declared=others, expected=OTHER_ENDPOINT_KEYS)
    )


# --- AC-3: kinds, required attributes, bodies -----------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-3: the ``Param``s that are not ``Kind.SCALAR`` carry the ``Kind`` of their row's Type; the ``Param``s
    declared ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body and no
    ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = non_scalar_params(records=records, registry=registry)
    assert typed == NON_SCALAR_PARAMS, "the Params that are not Kind.SCALAR are not the sections' (AC-3):\n" + (
        mapping_difference(declared=typed, expected=NON_SCALAR_PARAMS)
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert required == expected_required, "required=True is not exactly where Required reads `yes` (AC-3):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    misbodied = [
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    ]
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-3): {misbodied}"


# --- AC-4, AC-6: the list records -----------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-4: the records that are not ``Paging.NONE``, each with its ``Paging`` and the paging rows it declares, are
    ``PAGED_RECORDS``'s."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {
        record.operation_id: (record.paging.name, declared_paging_rows(record=record))
        for record in family.OPERATIONS
        if record.paging.name != PAGING_NONE
    }
    expected = {operation_id: (listed.paging, listed.paging_rows) for operation_id, listed in PAGED_RECORDS.items()}
    assert paged == expected, "the paged records are not the sections' lists (AC-4):\n" + mapping_difference(
        declared=paged, expected=expected
    )


@pytest.mark.parametrize(argnames=("operation_id", "listed"), argvalues=list_params())
def test_a_list_record_prints_every_page(
    operation_id: str, listed: PagedRecord, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6: ``call <id> --path NAME=VALUE ...`` against two pages, the second asked for by ``x-next-page`` (OFFSET) or
    at the ``Link`` rel="next" URL (KEYSET), exits 0, requests both pages at their exact URLs and prints both items as
    one JSON array."""
    values = path_values(path=listed.path)
    argv = [
        operation_id,
        *(part for name, value in values.items() for part in (OPTION_PATH, f"{name}{ASSIGNED}{value}")),
    ]
    pages = PAGE_CHAINS[listed.paging](url=f"{REST_BASE}{expanded(path=listed.path, values=values)}")
    for page, item in zip(pages, PAGE_ITEMS):
        fake_gitlab.script(method=METHOD_GET, url=page.url, headers=page.headers, body=[item])
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, page.url) for page in pages], (
        "each page requested as Transport.pages does (#13 AC-2.5, AC-2.6)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-6):\n{captured.out}"
    )
