"""The ``agent-foundations`` endpoint family of the GitLab wrapper: the AI Catalog seeding and the Duo Agent Platform
flows.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/agent-foundations.md`` (issue #13, design.md D1 and D5; issue #38, change.md AC-1 to
AC-5), in page order under a comment naming its section: the method, the path as ``operations-index.md`` writes it, and
one ``Param`` per query or body row, in table order:

- every row is ``Kind.SCALAR`` and none is required; every body is JSON and no record has ``fixed`` values;
- every record is ``Paging.NONE``: "List all agent privileges" answers one object (AC-5).

``PENDING`` holds the keys of "Trigger a flow" and "Restart a flow", which have no record: a flow writes code, merge
requests and issues, and no subcommand sends either (change.md AC-2 and Residuals).

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Location, Param, RestOperation

FAMILY = "agent-foundations"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "AI Catalog admin API: Seed GitLab-managed external agents".
    RestOperation(
        operation_id="agent-foundations#seed-gitlab-managed-external-agents",
        method="POST",
        path="/admin/ai_catalog/seed_external_agents",
    ),
    # "Flows API: Get workflow trace as JSONL"; the trace is the body as the host sends it (AC-8).
    RestOperation(
        operation_id="agent-foundations#get-workflow-trace-as-jsonl",
        method="GET",
        path="/ai/duo_workflows/workflows/:workflow_id/trace.jsonl",
        params=(Param(name="thread", location=Location.QUERY),),
    ),
    # "Flows API: List all agent privileges"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="agent-foundations#list-all-agent-privileges",
        method="GET",
        path="/ai/duo_workflows/workflows/agent_privileges",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/ai/duo_workflows/workflows"),
        ("POST", "/ai/duo_workflows/workflows/:workflow_id/restart"),
    }
)
