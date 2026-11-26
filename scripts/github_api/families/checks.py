"""The ``checks`` family of the GitHub operations index: check runs and check suites.

Each record is the section of ``docs/api-reference/github/rest/checks.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body (``output.title`` is a field of
``output``, ``actions[].label`` one of each ``actions`` item, and the ``{completed}.status`` variant row of
``checks/create`` and ``checks/update`` names ``status``). The ``ref`` of ``checks/list-for-ref`` and
``checks/list-suites-for-ref`` may contain ``/`` (``conventions.md`` "Path parameters"), so it is in ``multi_segment``
and ``registry.expand`` keeps its slashes. Four records page by ``link``: ``checks/list-for-ref`` and
``checks/list-for-suite`` hold their runs under ``check_runs``, ``checks/list-suites-for-ref`` its suites under
``check_suites`` (``conventions.md`` "Lists wrapped in an object"), and the ``200`` of ``checks/list-annotations`` is
the array itself, so it has no item key; every other record sends one request.

``get-pr-checks`` sends ``checks/list-for-ref``, the record part 1 declared (#17); every record is also sent by
``call <operation-id>`` (#28). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "checks"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/checks.md "Create a check run": the first-level body fields; 201 with a ``check-run``.
    RestOperation(
        operation_id="checks/create",
        method="POST",
        path="/repos/{owner}/{repo}/check-runs",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "head_sha",
                "details_url",
                "external_id",
                "status",
                "started_at",
                "conclusion",
                "completed_at",
                "output",
                "actions",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Get a check run": path parameters only; 200 with a ``check-run``.
    RestOperation(
        operation_id="checks/get",
        method="GET",
        path="/repos/{owner}/{repo}/check-runs/{check_run_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Update a check run": the first-level body fields; 200 with a ``check-run``.
    RestOperation(
        operation_id="checks/update",
        method="PATCH",
        path="/repos/{owner}/{repo}/check-runs/{check_run_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "details_url",
                "external_id",
                "started_at",
                "status",
                "conclusion",
                "completed_at",
                "output",
                "actions",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "List check run annotations": 200 with an array of ``check-annotation`` and a ``Link`` header,
    # so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="checks/list-annotations",
        method="GET",
        path="/repos/{owner}/{repo}/check-runs/{check_run_id}/annotations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Rerequest a check run": path parameters only, no body; 201 with an ``empty-object``.
    RestOperation(
        operation_id="checks/rerequest-run",
        method="POST",
        path="/repos/{owner}/{repo}/check-runs/{check_run_id}/rerequest",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "List check runs in a check suite": the runs under ``check_runs`` (with ``total_count``) and a
    # ``Link`` header, so it pages by ``link``.
    RestOperation(
        operation_id="checks/list-for-suite",
        method="GET",
        path="/repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs",
        query_params=frozenset({"check_name", "status", "filter", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="check_runs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "List check runs for a Git reference": ``ref`` may contain ``/``; the runs under ``check_runs``.
    RestOperation(
        operation_id="checks/list-for-ref",
        method="GET",
        path="/repos/{owner}/{repo}/commits/{ref}/check-runs",
        query_params=frozenset({"check_name", "status", "filter", "per_page", "page", "app_id"}),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.LINK,
        item_key="check_runs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Create a check suite": body ``head_sha``; 200 or 201 with a ``check-suite``.
    RestOperation(
        operation_id="checks/create-suite",
        method="POST",
        path="/repos/{owner}/{repo}/check-suites",
        query_params=frozenset(),
        body_params=frozenset({"head_sha"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Update repository preferences for check suites": body ``auto_trigger_checks``; 200 with a
    # ``check-suite-preference``.
    RestOperation(
        operation_id="checks/set-suites-preferences",
        method="PATCH",
        path="/repos/{owner}/{repo}/check-suites/preferences",
        query_params=frozenset(),
        body_params=frozenset({"auto_trigger_checks"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Get a check suite": path parameters only; 200 with a ``check-suite``.
    RestOperation(
        operation_id="checks/get-suite",
        method="GET",
        path="/repos/{owner}/{repo}/check-suites/{check_suite_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "Rerequest a check suite": path parameters only, no body; 201 with an ``empty-object``.
    RestOperation(
        operation_id="checks/rerequest-suite",
        method="POST",
        path="/repos/{owner}/{repo}/check-suites/{check_suite_id}/rerequest",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/checks.md "List check suites for a Git reference": ``ref`` may contain ``/``; the suites under
    # ``check_suites`` (with ``total_count``) and a ``Link`` header, so it pages by ``link``.
    RestOperation(
        operation_id="checks/list-suites-for-ref",
        method="GET",
        path="/repos/{owner}/{repo}/commits/{ref}/check-suites",
        query_params=frozenset({"app_id", "check_name", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.LINK,
        item_key="check_suites",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
