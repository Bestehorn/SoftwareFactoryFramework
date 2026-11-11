"""The ``agent-automations`` family of the GitHub operations index: the agent automations of a repository, their
revisions and their runs, and the automations listed for the user.

Each record is the section of ``docs/api-reference/github/rest/agent-automations.md`` its operation ID names: its
method and path, the names of its ``query`` rows, and the first-level fields of its request body
(``triggers.interval.cadence`` is a field of ``triggers``). No path parameter spans segments, and every record sends
``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The four sections with a ``Paging:`` line page by ``link``: ``agent-automations/list-automations``, whose ``200`` is
the array, so it has no item key, and the repository's lists of automations, revisions and tasks, whose items are in
``automations``, ``revisions`` and ``tasks`` (``conventions.md`` "Lists wrapped in an object").
``agent-automations/list-available-repo-automation-triggers`` answers an array with no ``Link`` header, so it sends one
request, as every other record does.

Every record is sent by ``call <operation-id>`` (#28) but the three whose call writes a branch or creates issues,
``agent-automations/create-repo-automation``, ``agent-automations/edit-repo-automation`` and
``agent-automations/create-repo-automation-task``, which ``commands/call.py`` ``GATED_OPERATIONS`` refuses (issue #33
AC-6). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "agent-automations"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/agent-automations.md "agent-automations"
    RestOperation(
        operation_id="agent-automations/list-automations",
        method="GET",
        path="/agents/automations",
        query_params=frozenset({"page", "per_page", "type"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/list-repo-automations",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations",
        query_params=frozenset({"page", "per_page", "type"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="automations",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/create-repo-automation",
        method="POST",
        path="/agents/repos/{owner}/{repo}/automations",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "triggers",
                "prompt",
                "model",
                "reasoning_effort",
                "tools",
                "enabled",
                "type",
                "require_actor_write_permission",
                "continuous_history",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/list-available-repo-automation-tools",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/available-tools",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/list-available-repo-automation-triggers",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/available-triggers",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/get-repo-automation",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/edit-repo-automation",
        method="PATCH",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "enabled",
                "require_actor_write_permission",
                "continuous_history",
                "model",
                "reasoning_effort",
                "triggers",
                "prompt",
                "tools",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/delete-repo-automation",
        method="DELETE",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/list-automation-revisions",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}/revisions",
        query_params=frozenset({"cursor", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="revisions",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/get-automation-revision",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}/revisions/{revision_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/list-repo-automation-tasks",
        method="GET",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}/tasks",
        query_params=frozenset({"per_page", "page", "sort", "direction", "state", "is_archived"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="tasks",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-automations/create-repo-automation-task",
        method="POST",
        path="/agents/repos/{owner}/{repo}/automations/{automation_id}/tasks",
        query_params=frozenset(),
        body_params=frozenset({"event", "context"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
