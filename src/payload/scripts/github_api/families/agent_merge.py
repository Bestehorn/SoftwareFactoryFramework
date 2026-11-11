"""The ``agent-merge`` family of the GitHub operations index: the Agent Merge configuration of a pull request.

The family's index rows link the ``agent-merge`` group of ``docs/api-reference/github/rest/pulls.md``; each record is
the section its operation ID names: its method and path and the first-level fields of its request body. No section has
a ``query`` row or a ``Paging:`` line, so every record sends one request, with no item key, no multi-segment path
parameter, ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28) but ``agent-merge/put-agent-merge-enrollment``, whose call writes
a branch or creates issues (its ``allowed_actions`` are ``fix_ci`` and ``resolve_merge_conflicts``) and which
``commands/call.py`` ``GATED_OPERATIONS`` refuses (issue #33 AC-6). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "agent-merge"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/pulls.md "agent-merge"
    RestOperation(
        operation_id="agent-merge/get-agent-merge-enrollment",
        method="GET",
        path="/agents/repos/{owner}/{repo}/pulls/{pull_number}/agent-merge",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-merge/put-agent-merge-enrollment",
        method="PUT",
        path="/agents/repos/{owner}/{repo}/pulls/{pull_number}/agent-merge",
        query_params=frozenset(),
        body_params=frozenset({"allowed_actions"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-merge/delete-agent-merge-enrollment",
        method="DELETE",
        path="/agents/repos/{owner}/{repo}/pulls/{pull_number}/agent-merge",
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
