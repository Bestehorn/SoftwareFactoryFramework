"""The ``agent-tasks`` family of the GitHub operations index: the agent tasks of a repository, and tasks listed and
read by ID alone (``agent-tasks/list-tasks``, ``agent-tasks/get-task-by-id``).

Each record is the section of ``docs/api-reference/github/rest/agent-tasks.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body. No path parameter spans
segments, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``. ``agent-tasks/list-tasks-for-repo`` and
``agent-tasks/list-tasks`` have a ``Paging:`` line and page by ``link``, their items in ``tasks`` (``conventions.md``
"Lists wrapped in an object"); every other record sends one request.

Every record is sent by ``call <operation-id>`` (#28) but ``agent-tasks/create-task-in-repo``, whose call writes a
branch or creates issues (its body names ``create_pull_request``, ``base_ref`` and ``head_ref``) and which
``commands/call.py`` ``GATED_OPERATIONS`` refuses (issue #33 AC-6). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "agent-tasks"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/agent-tasks.md "agent-tasks"
    RestOperation(
        operation_id="agent-tasks/list-tasks-for-repo",
        method="GET",
        path="/agents/repos/{owner}/{repo}/tasks",
        query_params=frozenset(
            {"per_page", "page", "sort", "direction", "state", "is_archived", "since", "creator_id"}
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="tasks",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-tasks/create-task-in-repo",
        method="POST",
        path="/agents/repos/{owner}/{repo}/tasks",
        query_params=frozenset(),
        body_params=frozenset({"prompt", "model", "custom_agent", "create_pull_request", "base_ref", "head_ref"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-tasks/get-task-by-repo-and-id",
        method="GET",
        path="/agents/repos/{owner}/{repo}/tasks/{task_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-tasks/list-tasks",
        method="GET",
        path="/agents/tasks",
        query_params=frozenset({"per_page", "page", "sort", "direction", "state", "is_archived", "since"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="tasks",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="agent-tasks/get-task-by-id",
        method="GET",
        path="/agents/tasks/{task_id}",
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
