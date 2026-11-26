"""The ``code-quality`` family of the GitHub operations index: a repository's code quality findings and its setup.

Each record is the section of ``docs/api-reference/github/rest/code-quality.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body. No path parameter of the family
may contain ``/``, so ``multi_segment`` is empty, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.
``code-quality/list-findings-for-repo`` alone has a ``Paging:`` line (``per_page`` and a cursor, the response body the
array), so it pages by ``link`` with no item key; every other record sends one request.

Every record is sent by ``call <operation-id>`` (#28); none writes a branch. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "code-quality"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/code-quality.md "List code quality findings for a repository": ``per_page`` + cursor; 200 with an array of
    # ``code-quality-finding``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-quality/list-findings-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/code-quality/findings",
        query_params=frozenset({"per_page", "direction", "before", "after", "state"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-quality.md "Get a code quality finding": path parameters only; 200 with a ``code-quality-finding``.
    RestOperation(
        operation_id="code-quality/get-finding",
        method="GET",
        path="/repos/{owner}/{repo}/code-quality/findings/{finding_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-quality.md "Get a code quality setup configuration": path parameters only; 200 with a
    # ``code-quality-setup``.
    RestOperation(
        operation_id="code-quality/get-setup",
        method="GET",
        path="/repos/{owner}/{repo}/code-quality/setup",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-quality.md "Update a code quality setup configuration": the body fields (at least one of them); 200 or
    # 202.
    RestOperation(
        operation_id="code-quality/update-setup",
        method="PATCH",
        path="/repos/{owner}/{repo}/code-quality/setup",
        query_params=frozenset(),
        body_params=frozenset({"state", "runner_type", "runner_label", "languages", "ai_findings_option"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
