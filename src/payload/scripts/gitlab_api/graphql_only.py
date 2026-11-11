"""The GraphQL-only capabilities of the GitLab wrapper: ``GraphQLOperation`` records that belong to no REST family.

``registry.lookup`` reads ``OPERATIONS`` beside every family module's records.

The coverage rule (issue #41, design D6) has no exclusion: every first cell of the table under ``### Only in GraphQL``
in ``docs/api-reference/gitlab/graphql/conventions.md`` is either served by the ``capability`` of a record in
``OPERATIONS`` or held in ``PENDING_CAPABILITIES``, verbatim, experimental or not, and neither names a capability the
table lacks. ``test/test_gitlab_wrapper_coverage.py`` holds the rule. Part 1 (issue #13) declares no record, so every
first cell is on ``PENDING_CAPABILITIES``, in the table's order; a record that serves a capability takes it off.

A record of a query or mutation that the GraphQL reference marks ``Status: Experiment`` says so in its comment.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import GraphQLOperation

OPERATIONS: Tuple[GraphQLOperation, ...] = ()
PENDING_CAPABILITIES: FrozenSet[str] = frozenset(
    {
        "Work items",
        "Epics with new features (assignees, health status, links to other item types)",
        "Branch rules",
        "Group-wide and instance-wide vulnerability lists",
        "Design uploads",
        "Asynchronous pipeline creation",
        "Work item CSV import",
        "Query cost introspection",
    }
)
