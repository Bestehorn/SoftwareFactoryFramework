"""The ``agent-foundations`` endpoint family of the GitLab wrapper: the AI Catalog seeding and the Duo Agent Platform
flows.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/agent-foundations.md`` (issue #13, design.md D1 and D5; issue #38, change.md AC-1 to
AC-5; issue #15, change.md AC-1), in page order under a comment naming its section: the method, the path as
``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- an ``integer array`` row is ``Kind.ARRAY``, an ``array of objects`` row ``ARRAY_OF_HASHES``, every other row
  ``SCALAR``, and none is required; every body is JSON and no record has ``fixed`` values;
- every record is ``Paging.NONE``: "List all agent privileges" answers one object (AC-5).

``PENDING`` is empty. "Trigger a flow" (``OP_TRIGGER_A_FLOW``) and "Restart a flow" (``OP_RESTART_A_FLOW``) have their
records since issue #15: a flow writes code, merge requests and issues, and no subcommand sends either, so
``commands/call.py``'s ``GATED_OPERATIONS`` maps each to ``None`` and ``call`` refuses it, ": no subcommand sends it",
before any request is sent (issue #15 AC-3).

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Param, RestOperation

FAMILY = "agent-foundations"

# "Trigger a flow": `commands/call.py`'s `GATED_OPERATIONS` maps it to `None` (issue #15 AC-3).
OP_TRIGGER_A_FLOW = "agent-foundations#trigger-a-flow"
# "Restart a flow": `commands/call.py`'s `GATED_OPERATIONS` maps it to `None` (issue #15 AC-3).
OP_RESTART_A_FLOW = "agent-foundations#restart-a-flow"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "AI Catalog admin API: Seed GitLab-managed external agents".
    RestOperation(
        operation_id="agent-foundations#seed-gitlab-managed-external-agents",
        method="POST",
        path="/admin/ai_catalog/seed_external_agents",
    ),
    # "Flows API: Trigger a flow"; a flow writes code, merge requests and issues, so `call` refuses it (issue #15).
    RestOperation(
        operation_id=OP_TRIGGER_A_FLOW,
        method="POST",
        path="/ai/duo_workflows/workflows",
        params=(
            Param(name="additional_context", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="agent_privileges", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="ai_catalog_item_consumer_id", location=Location.BODY),
            Param(name="ai_catalog_item_version_id", location=Location.BODY),
            Param(name="allow_agent_to_request_user", location=Location.BODY),
            Param(name="callback_hook_id", location=Location.BODY),
            Param(name="client_reference", location=Location.BODY),
            Param(name="environment", location=Location.BODY),
            Param(name="goal", location=Location.BODY),
            Param(name="image", location=Location.BODY),
            Param(name="issue_id", location=Location.BODY),
            Param(name="merge_request_id", location=Location.BODY),
            Param(name="namespace_id", location=Location.BODY),
            Param(name="pre_approved_agent_privileges", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="project_id", location=Location.BODY),
            Param(name="source", location=Location.BODY),
            Param(name="source_branch", location=Location.BODY),
            Param(name="start_workflow", location=Location.BODY),
            Param(name="workflow_definition", location=Location.BODY),
        ),
    ),
    # "Flows API: Restart a flow"; its one row is the path's `workflow_id`, no Param, and `call` refuses it (issue #15).
    RestOperation(
        operation_id=OP_RESTART_A_FLOW,
        method="POST",
        path="/ai/duo_workflows/workflows/:workflow_id/restart",
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

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
