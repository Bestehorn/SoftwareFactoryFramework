"""The ``pull-request-stacks`` family of the GitHub operations index: a repository's pull request stacks.

Each record is the section of ``docs/api-reference/github/rest/pulls.md`` (its ``stacks`` part) its operation ID
names: its method and path, the names of its ``query`` rows, and the one field of its request body,
``pull_requests``. ``pull-request-stacks/list`` alone pages, by ``link``: its ``200`` is the array, and "Lists wrapped
in an object" names no ``pull-request-stacks`` operation, so it has no item key; every other record sends one request.
No path parameter of the family may contain ``/``, so ``multi_segment`` is empty throughout, and every record sends
``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Creating, extending and unstacking a stack groups existing pull requests and writes no branch, so every record is sent
by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "pull-request-stacks"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/pulls.md "List pull request stacks": query ``pull_request``; page-based, the body is the array.
    RestOperation(
        operation_id="pull-request-stacks/list",
        method="GET",
        path="/repos/{owner}/{repo}/stacks",
        query_params=frozenset({"pull_request", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Create a pull request stack": body ``pull_requests``; 201 with an object.
    RestOperation(
        operation_id="pull-request-stacks/create",
        method="POST",
        path="/repos/{owner}/{repo}/stacks",
        query_params=frozenset(),
        body_params=frozenset({"pull_requests"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get a pull request stack": path parameters only; 200 with an object.
    RestOperation(
        operation_id="pull-request-stacks/get",
        method="GET",
        path="/repos/{owner}/{repo}/stacks/{stack_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Add pull requests to a pull request stack": body ``pull_requests``; 200 with an object.
    RestOperation(
        operation_id="pull-request-stacks/add",
        method="POST",
        path="/repos/{owner}/{repo}/stacks/{stack_number}/add",
        query_params=frozenset(),
        body_params=frozenset({"pull_requests"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Remove pull requests from a pull request stack": path parameters only; 200 with an object, or 204.
    RestOperation(
        operation_id="pull-request-stacks/unstack",
        method="POST",
        path="/repos/{owner}/{repo}/stacks/{stack_number}/unstack",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
