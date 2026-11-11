"""Tests of the GitHub wrapper's ``actions`` family, ``github_api/families/actions.py`` (issue #31 ``change.md``; AC-1,
AC-3, AC-4, AC-6).

Every expected value here is transcribed from ``docs/api-reference/github/rest/actions.md`` and ``conventions.md``,
never read from the records or from ``commands/call.py``:

- ``ACTIONS_OPERATION_IDS``: the operation ID of every section of ``rest/actions.md`` whose operation line names an
  ``actions/`` ID, the two of its ``oidc`` section included; its ``oidc/`` sections belong to another family. Each has
  one record and none is pending (AC-1);
- ``MULTI_SEGMENT_PARAMETERS``: for each section with one, the path parameters whose ``Parameter`` row reads "may
  contain `/` (multi-segment path)" (AC-3). No ``actions/`` section has such a row, so the table is empty;
- ``LIST_RECORDS``: each ``actions/`` section with a ``Paging:`` line (AC-4): its path, the key after "items in" (the
  item key of ``conventions.md`` "Lists wrapped in an object"; every one of them is wrapped) and whether its
  ``Parameter`` table documents ``per_page``;
- ``LINK_HEADER_ON_ONE_OBJECT``: the two ``actions/`` sections with a ``Link`` response header and no ``Paging:``
  line, whose ``200`` is one object; AC-4 makes them ``Paging.NONE``.

``test_a_list_record_prints_every_item`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page; standard output is both as one JSON array. Each case runs with ``fx.run_product_case`` through the
product entry script's ``main(argv=...)`` in the fixture project (``origin`` ``o/r``), which judges its exit code, its
standard output exactly, its requests other than ``GET`` and that every request was routed.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_actions.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

REGISTRY = "registry"
TRANSPORT = "transport"
FAMILY = "actions"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_6 = "AC-6"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
PATH_OWNER = "owner"
PATH_REPO = "repo"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"
#: How a failure message shows a key a mapping does not hold.
ABSENT = "absent"

#: AC-1: every ``actions/`` operation ID of ``rest/actions.md``, one per section.
ACTIONS_OPERATION_IDS = frozenset(
    {
        "actions/add-custom-labels-to-self-hosted-runner-for-org",
        "actions/add-custom-labels-to-self-hosted-runner-for-repo",
        "actions/add-repo-access-to-self-hosted-runner-group-in-org",
        "actions/add-selected-repo-to-org-secret",
        "actions/add-selected-repo-to-org-variable",
        "actions/add-self-hosted-runner-to-group-for-org",
        "actions/approve-workflow-run",
        "actions/cancel-workflow-run",
        "actions/create-environment-variable",
        "actions/create-hosted-runner-for-org",
        "actions/create-or-update-environment-secret",
        "actions/create-or-update-org-secret",
        "actions/create-or-update-repo-secret",
        "actions/create-org-actions-policy",
        "actions/create-org-variable",
        "actions/create-registration-token-for-org",
        "actions/create-registration-token-for-repo",
        "actions/create-remove-token-for-org",
        "actions/create-remove-token-for-repo",
        "actions/create-repo-actions-policy",
        "actions/create-repo-variable",
        "actions/create-self-hosted-runner-group-for-org",
        "actions/create-workflow-dispatch",
        "actions/delete-actions-cache-by-id",
        "actions/delete-actions-cache-by-key",
        "actions/delete-artifact",
        "actions/delete-custom-image-from-org",
        "actions/delete-custom-image-version-from-org",
        "actions/delete-environment-secret",
        "actions/delete-environment-variable",
        "actions/delete-hosted-runner-for-org",
        "actions/delete-org-actions-policy",
        "actions/delete-org-secret",
        "actions/delete-org-variable",
        "actions/delete-repo-actions-policy",
        "actions/delete-repo-secret",
        "actions/delete-repo-variable",
        "actions/delete-self-hosted-runner-from-org",
        "actions/delete-self-hosted-runner-from-repo",
        "actions/delete-self-hosted-runner-group-from-org",
        "actions/delete-workflow-run",
        "actions/delete-workflow-run-logs",
        "actions/disable-selected-repository-github-actions-organization",
        "actions/disable-selected-repository-self-hosted-runners-organization",
        "actions/disable-workflow",
        "actions/download-artifact",
        "actions/download-job-logs-for-workflow-run",
        "actions/download-step-logs-for-workflow-run-job",
        "actions/download-workflow-run-attempt-logs",
        "actions/download-workflow-run-logs",
        "actions/enable-selected-repository-github-actions-organization",
        "actions/enable-selected-repository-self-hosted-runners-organization",
        "actions/enable-workflow",
        "actions/force-cancel-workflow-run",
        "actions/generate-runner-jitconfig-for-org",
        "actions/generate-runner-jitconfig-for-repo",
        "actions/get-actions-cache-list",
        "actions/get-actions-cache-retention-limit-for-enterprise",
        "actions/get-actions-cache-retention-limit-for-organization",
        "actions/get-actions-cache-retention-limit-for-repository",
        "actions/get-actions-cache-storage-limit-for-enterprise",
        "actions/get-actions-cache-storage-limit-for-organization",
        "actions/get-actions-cache-storage-limit-for-repository",
        "actions/get-actions-cache-usage",
        "actions/get-actions-cache-usage-by-repo-for-org",
        "actions/get-actions-cache-usage-for-org",
        "actions/get-allowed-actions-organization",
        "actions/get-allowed-actions-repository",
        "actions/get-artifact",
        "actions/get-artifact-and-log-retention-settings-organization",
        "actions/get-artifact-and-log-retention-settings-repository",
        "actions/get-concurrency-group-for-repository",
        "actions/get-custom-image-for-org",
        "actions/get-custom-image-version-for-org",
        "actions/get-custom-oidc-sub-claim-for-repo",
        "actions/get-environment-public-key",
        "actions/get-environment-secret",
        "actions/get-environment-variable",
        "actions/get-fork-pr-contributor-approval-permissions-organization",
        "actions/get-fork-pr-contributor-approval-permissions-repository",
        "actions/get-github-actions-default-workflow-permissions-organization",
        "actions/get-github-actions-default-workflow-permissions-repository",
        "actions/get-github-actions-permissions-organization",
        "actions/get-github-actions-permissions-repository",
        "actions/get-hosted-runner-for-org",
        "actions/get-hosted-runners-github-owned-images-for-org",
        "actions/get-hosted-runners-limits-for-org",
        "actions/get-hosted-runners-machine-specs-for-org",
        "actions/get-hosted-runners-partner-images-for-org",
        "actions/get-hosted-runners-platforms-for-org",
        "actions/get-job-for-workflow-run",
        "actions/get-org-actions-policies",
        "actions/get-org-actions-policy",
        "actions/get-org-public-key",
        "actions/get-org-secret",
        "actions/get-org-variable",
        "actions/get-pending-deployments-for-run",
        "actions/get-private-repo-fork-pr-workflows-settings-organization",
        "actions/get-private-repo-fork-pr-workflows-settings-repository",
        "actions/get-repo-actions-policies",
        "actions/get-repo-actions-policy",
        "actions/get-repo-public-key",
        "actions/get-repo-secret",
        "actions/get-repo-variable",
        "actions/get-reviews-for-run",
        "actions/get-runner-version-deprecation-for-org",
        "actions/get-runner-version-deprecation-for-repo",
        "actions/get-self-hosted-runner-for-org",
        "actions/get-self-hosted-runner-for-repo",
        "actions/get-self-hosted-runner-group-for-org",
        "actions/get-self-hosted-runners-permissions-organization",
        "actions/get-workflow",
        "actions/get-workflow-access-to-repository",
        "actions/get-workflow-run",
        "actions/get-workflow-run-attempt",
        "actions/get-workflow-run-usage",
        "actions/get-workflow-usage",
        "actions/list-artifacts-for-repo",
        "actions/list-concurrency-groups-for-repository",
        "actions/list-concurrency-groups-for-workflow-run",
        "actions/list-custom-image-versions-for-org",
        "actions/list-custom-images-for-org",
        "actions/list-environment-secrets",
        "actions/list-environment-variables",
        "actions/list-github-hosted-runners-in-group-for-org",
        "actions/list-hosted-runners-for-org",
        "actions/list-jobs-for-workflow-run",
        "actions/list-jobs-for-workflow-run-attempt",
        "actions/list-labels-for-self-hosted-runner-for-org",
        "actions/list-labels-for-self-hosted-runner-for-repo",
        "actions/list-org-secrets",
        "actions/list-org-variables",
        "actions/list-repo-access-to-self-hosted-runner-group-in-org",
        "actions/list-repo-organization-secrets",
        "actions/list-repo-organization-variables",
        "actions/list-repo-secrets",
        "actions/list-repo-variables",
        "actions/list-repo-workflows",
        "actions/list-runner-applications-for-org",
        "actions/list-runner-applications-for-repo",
        "actions/list-selected-repos-for-org-secret",
        "actions/list-selected-repos-for-org-variable",
        "actions/list-selected-repositories-enabled-github-actions-organization",
        "actions/list-selected-repositories-self-hosted-runners-organization",
        "actions/list-self-hosted-runner-groups-for-org",
        "actions/list-self-hosted-runners-for-org",
        "actions/list-self-hosted-runners-for-repo",
        "actions/list-self-hosted-runners-in-group-for-org",
        "actions/list-workflow-run-artifacts",
        "actions/list-workflow-runs",
        "actions/list-workflow-runs-for-repo",
        "actions/re-run-job-for-workflow-run",
        "actions/re-run-workflow",
        "actions/re-run-workflow-failed-jobs",
        "actions/remove-all-custom-labels-from-self-hosted-runner-for-org",
        "actions/remove-all-custom-labels-from-self-hosted-runner-for-repo",
        "actions/remove-custom-label-from-self-hosted-runner-for-org",
        "actions/remove-custom-label-from-self-hosted-runner-for-repo",
        "actions/remove-repo-access-to-self-hosted-runner-group-in-org",
        "actions/remove-selected-repo-from-org-secret",
        "actions/remove-selected-repo-from-org-variable",
        "actions/remove-self-hosted-runner-from-group-for-org",
        "actions/review-custom-gates-for-run",
        "actions/review-pending-deployments-for-run",
        "actions/set-actions-cache-retention-limit-for-enterprise",
        "actions/set-actions-cache-retention-limit-for-organization",
        "actions/set-actions-cache-retention-limit-for-repository",
        "actions/set-actions-cache-storage-limit-for-enterprise",
        "actions/set-actions-cache-storage-limit-for-organization",
        "actions/set-actions-cache-storage-limit-for-repository",
        "actions/set-allowed-actions-organization",
        "actions/set-allowed-actions-repository",
        "actions/set-artifact-and-log-retention-settings-organization",
        "actions/set-artifact-and-log-retention-settings-repository",
        "actions/set-custom-labels-for-self-hosted-runner-for-org",
        "actions/set-custom-labels-for-self-hosted-runner-for-repo",
        "actions/set-custom-oidc-sub-claim-for-repo",
        "actions/set-fork-pr-contributor-approval-permissions-organization",
        "actions/set-fork-pr-contributor-approval-permissions-repository",
        "actions/set-github-actions-default-workflow-permissions-organization",
        "actions/set-github-actions-default-workflow-permissions-repository",
        "actions/set-github-actions-permissions-organization",
        "actions/set-github-actions-permissions-repository",
        "actions/set-private-repo-fork-pr-workflows-settings-organization",
        "actions/set-private-repo-fork-pr-workflows-settings-repository",
        "actions/set-repo-access-to-self-hosted-runner-group-in-org",
        "actions/set-selected-repos-for-org-secret",
        "actions/set-selected-repos-for-org-variable",
        "actions/set-selected-repositories-enabled-github-actions-organization",
        "actions/set-selected-repositories-self-hosted-runners-organization",
        "actions/set-self-hosted-runners-in-group-for-org",
        "actions/set-self-hosted-runners-permissions-organization",
        "actions/set-workflow-access-to-repository",
        "actions/update-environment-variable",
        "actions/update-hosted-runner-for-org",
        "actions/update-org-actions-policy",
        "actions/update-org-variable",
        "actions/update-repo-actions-policy",
        "actions/update-repo-variable",
        "actions/update-self-hosted-runner-group-for-org",
    }
)

#: AC-3: for each ``actions/`` section with one, its path parameters whose row reads "may contain `/` (multi-segment
#: path)": ``rest/actions.md`` has no such row.
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {}

#: AC-4: the ``actions/`` sections whose ``200`` is one object with a ``Link`` header and that have no ``Paging:``
#: line, so their records are ``Paging.NONE`` with no item key.
LINK_HEADER_ON_ONE_OBJECT = frozenset(
    {
        "actions/get-actions-cache-usage-for-org",
        "actions/get-hosted-runner-for-org",
    }
)


@dataclass(frozen=True)
class ListRecord:
    """A ``Paging.LINK`` record as its section documents it: the operation ID, the path template, the key its items
    sit under (``None``: the body is the array) and whether it documents ``per_page``."""

    operation_id: str
    path: str
    item_key: Optional[str]
    per_page: bool


#: AC-4, AC-6: every ``actions/`` section with a ``Paging:`` line. Each answers with an object holding its items under
#: the key its ``Paging:`` line names after "items in" (``conventions.md`` "Lists wrapped in an object").
LIST_RECORDS: Tuple[ListRecord, ...] = (
    ListRecord(
        operation_id="actions/get-actions-cache-list",
        path="/repos/{owner}/{repo}/actions/caches",
        item_key="actions_caches",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/get-actions-cache-usage-by-repo-for-org",
        path="/orgs/{org}/actions/cache/usage-by-repository",
        item_key="repository_cache_usages",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/get-org-actions-policies",
        path="/orgs/{org}/actions/policies",
        item_key="policies",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/get-repo-actions-policies",
        path="/repos/{owner}/{repo}/actions/policies",
        item_key="policies",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-artifacts-for-repo",
        path="/repos/{owner}/{repo}/actions/artifacts",
        item_key="artifacts",
        per_page=True,
    ),
    # ``per_page`` + cursor-based (``after``): the next page is the ``link`` header's URL, followed as given.
    ListRecord(
        operation_id="actions/list-concurrency-groups-for-repository",
        path="/repos/{owner}/{repo}/actions/concurrency_groups",
        item_key="concurrency_groups",
        per_page=True,
    ),
    # ``per_page`` + cursor-based (``after``, ``before``): the next page is the ``link`` header's URL, as given.
    ListRecord(
        operation_id="actions/list-concurrency-groups-for-workflow-run",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/concurrency_groups",
        item_key="concurrency_groups",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-environment-secrets",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets",
        item_key="secrets",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-environment-variables",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables",
        item_key="variables",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-github-hosted-runners-in-group-for-org",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/hosted-runners",
        item_key="runners",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-hosted-runners-for-org",
        path="/orgs/{org}/actions/hosted-runners",
        item_key="runners",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-jobs-for-workflow-run",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
        item_key="jobs",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-jobs-for-workflow-run-attempt",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs",
        item_key="jobs",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-org-secrets",
        path="/orgs/{org}/actions/secrets",
        item_key="secrets",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-org-variables",
        path="/orgs/{org}/actions/variables",
        item_key="variables",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-access-to-self-hosted-runner-group-in-org",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories",
        item_key="repositories",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-organization-secrets",
        path="/repos/{owner}/{repo}/actions/organization-secrets",
        item_key="secrets",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-organization-variables",
        path="/repos/{owner}/{repo}/actions/organization-variables",
        item_key="variables",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-secrets",
        path="/repos/{owner}/{repo}/actions/secrets",
        item_key="secrets",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-variables",
        path="/repos/{owner}/{repo}/actions/variables",
        item_key="variables",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-repo-workflows",
        path="/repos/{owner}/{repo}/actions/workflows",
        item_key="workflows",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-selected-repos-for-org-secret",
        path="/orgs/{org}/actions/secrets/{secret_name}/repositories",
        item_key="repositories",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-selected-repos-for-org-variable",
        path="/orgs/{org}/actions/variables/{name}/repositories",
        item_key="repositories",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-selected-repositories-enabled-github-actions-organization",
        path="/orgs/{org}/actions/permissions/repositories",
        item_key="repositories",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-selected-repositories-self-hosted-runners-organization",
        path="/orgs/{org}/actions/permissions/self-hosted-runners/repositories",
        item_key="repositories",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-self-hosted-runner-groups-for-org",
        path="/orgs/{org}/actions/runner-groups",
        item_key="runner_groups",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-self-hosted-runners-for-org",
        path="/orgs/{org}/actions/runners",
        item_key="runners",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-self-hosted-runners-for-repo",
        path="/repos/{owner}/{repo}/actions/runners",
        item_key="runners",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-self-hosted-runners-in-group-for-org",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/runners",
        item_key="runners",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-workflow-run-artifacts",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts",
        item_key="artifacts",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-workflow-runs",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
        item_key="workflow_runs",
        per_page=True,
    ),
    ListRecord(
        operation_id="actions/list-workflow-runs-for-repo",
        path="/repos/{owner}/{repo}/actions/runs",
        item_key="workflow_runs",
        per_page=True,
    ),
)

#: The two items every list case serves, one per page where the record documents ``per_page``.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def path_value(*, name: str) -> str:
    """A path parameter's test value: alphanumeric, so nothing needs encoding, and made from its name, so a value
    given under another name changes the path."""
    return f"{TEST_VALUE_PREFIX}{NON_ALPHANUMERIC.sub(repl='', string=name)}"


def path_values(*, listed: ListRecord) -> Dict[str, str]:
    """The value of each placeholder of ``listed.path``, in path order: the fixture's ``origin`` for ``owner`` and
    ``repo``, else ``path_value``'s."""
    origin = {PATH_OWNER: fx.OWNER, PATH_REPO: fx.REPOSITORY}
    return {name: origin.get(name, path_value(name=name)) for name in PATH_PLACEHOLDER.findall(string=listed.path)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written."""
    return PATH_PLACEHOLDER.sub(repl=lambda match: values[match.group(1)], string=path)


def list_argv(*, listed: ListRecord, values: Mapping[str, str]) -> Tuple[str, ...]:
    """``call <id>``, ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, and ``--query
    per_page=1`` when the record documents ``per_page`` (#28 design D8)."""
    argv = [CALL, listed.operation_id]
    for name, value in values.items():
        if name not in ORIGIN_PARAMETERS:
            argv.extend((OPTION_PATH, f"{name}={value}"))
    if listed.per_page:
        argv.extend((OPTION_QUERY, QUERY_ONE_PER_PAGE))
    return tuple(argv)


def list_case(*, listed: ListRecord) -> Any:
    """#28 design D8's golden case of ``listed``: exit 0, standard output both items as one JSON array, against a list
    route serving them under the record's item key on its expanded path."""
    values = path_values(listed=listed)
    return fx.GoldenCase(
        name=f"{AC_6}/exit-0/{listed.operation_id}",
        argv=list_argv(listed=listed, values=values),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.ListRouteSpec(
                url=expanded(path=listed.path, values=values), items=LISTED_ITEMS, item_key=listed.item_key
            ),
        ),
    )


def list_record_name(listed: ListRecord) -> str:
    """The test id of a ``LIST_RECORDS`` row."""
    return listed.operation_id


def actions_family() -> ModuleType:
    """``github_api.families.actions``, imported from the ``scripts`` directory beside this suite
    (``fx.import_api_module`` puts it on ``sys.path``); a copy imported from anywhere else fails here."""
    fx.import_api_module(name=REGISTRY)
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def records_by_id(*, family: ModuleType) -> Dict[str, Any]:
    """Each ``RestOperation`` of ``family.OPERATIONS``, keyed by its operation ID."""
    registry = fx.import_api_module(name=REGISTRY)
    return {record.operation_id: record for record in family.OPERATIONS if isinstance(record, registry.RestOperation)}


def shown(*, values: Mapping[str, Any], operation_id: str) -> str:
    """``values[operation_id]`` as a failure message shows it, ``absent`` when ``values`` has no such key."""
    return repr(values[operation_id]) if operation_id in values else ABSENT


def differences(*, declared: Mapping[str, Any], expected: Mapping[str, Any]) -> List[str]:
    """One line per ID whose value in ``declared`` is not its value in ``expected``, absent counted as a value."""
    return [
        f"{json.dumps(obj=operation_id)}: declared {shown(values=declared, operation_id=operation_id)}, "
        f"the section documents {shown(values=expected, operation_id=operation_id)}"
        for operation_id in sorted(set(declared) | set(expected))
        if (operation_id in declared) != (operation_id in expected)
        or declared.get(operation_id) != expected.get(operation_id)
    ]


def unrecorded(*, records: Mapping[str, Any]) -> List[str]:
    """One line per ``actions/`` ID of the reference that ``records`` holds no record of."""
    return [
        f"{json.dumps(obj=operation_id)}: no record" for operation_id in sorted(ACTIONS_OPERATION_IDS - set(records))
    ]


def test_nothing_is_pending() -> None:
    """AC-1: ``actions.PENDING`` is empty, and ``actions.OPERATIONS`` holds one record of every ``actions/`` ID of
    ``rest/actions.md``, none twice and none of another ID."""
    family = actions_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    problems = []
    pending = frozenset(family.PENDING)
    if pending:
        problems.append(f"PENDING still holds {len(pending)} IDs: {sorted(pending)}")
    missing = sorted(ACTIONS_OPERATION_IDS - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - ACTIONS_OPERATION_IDS)
    if extra:
        problems.append(f"records of IDs that are not actions/ sections: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-3: every ``actions/`` ID has a record, and each declares ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, so
    ``call`` sends them."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=actions_family())
    problems = unrecorded(records=records)
    for operation_id in sorted(ACTIONS_OPERATION_IDS & set(records)):
        record = records[operation_id]
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{json.dumps(obj=operation_id)}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{json.dumps(obj=operation_id)}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-3: every ``actions/`` ID has a record, and ``{operation_id: multi_segment}`` over the records with a
    multi-segment parameter is ``MULTI_SEGMENT_PARAMETERS``, the parameters whose row reads "may contain `/`
    (multi-segment path)": none, in ``rest/actions.md``."""
    records = records_by_id(family=actions_family())
    declared = {
        operation_id: frozenset(record.multi_segment)
        for operation_id, record in records.items()
        if record.multi_segment
    }

    problems = unrecorded(records=records) + differences(declared=declared, expected=MULTI_SEGMENT_PARAMETERS)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-4: ``{operation_id: item_key}`` over the family's ``Paging.LINK`` records is that of ``LIST_RECORDS``, the
    sections with a ``Paging:`` line; ``LINK_HEADER_ON_ONE_OBJECT`` are recorded as ``Paging.NONE``; and no other
    record names an item key."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=actions_family())
    paged = {
        operation_id: record.item_key
        for operation_id, record in records.items()
        if record.paging == registry.Paging.LINK
    }
    cased = {listed.operation_id: listed.item_key for listed in LIST_RECORDS}

    problems = differences(declared=paged, expected=cased)
    for operation_id in sorted(LINK_HEADER_ON_ONE_OBJECT):
        record = records.get(operation_id)
        if record is None:
            problems.append(f"{json.dumps(obj=operation_id)}: no record")
        elif record.paging != registry.Paging.NONE:
            problems.append(f"{json.dumps(obj=operation_id)}: paging {record.paging!r}, Paging.NONE documented")
    keyed = sorted(
        operation_id
        for operation_id, record in records.items()
        if record.paging != registry.Paging.LINK and record.item_key is not None
    )
    if keyed:
        problems.append(f"records that are not Paging.LINK yet name an item key: {keyed}")

    assert not problems, f"{len(problems)} paging problems:\n" + "\n".join(problems)


@pytest.mark.parametrize(argnames="listed", argvalues=LIST_RECORDS, ids=list_record_name)
def test_a_list_record_prints_every_item(
    listed: ListRecord, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record against a fake host serving two items under its
    item key prints both as one JSON array and exits 0, having asked for one page per item where the record documents
    ``per_page``; every request was routed."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"
