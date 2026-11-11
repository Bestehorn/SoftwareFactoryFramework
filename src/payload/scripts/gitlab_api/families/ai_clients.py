"""The ``ai-clients`` endpoint family of the GitLab wrapper: the GitLab Duo Chat completions.

The record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/ai-clients.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5) under a comment naming its section: the method, the
path as ``operations-index.md`` writes it, and one ``Param`` per body row, in table order. The ``array`` row
(``additional_context``) is ``Kind.ARRAY``, every other row ``SCALAR``; ``required`` is the Required column's ``yes``;
the body is JSON, the record has no ``fixed`` values and is ``Paging.NONE``.

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Param, RestOperation

FAMILY = "ai-clients"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "GitLab Duo Chat completions API: Generate a Chat response".
    RestOperation(
        operation_id="ai-clients#generate-a-chat-response",
        method="POST",
        path="/chat/completions",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="resource_type", location=Location.BODY),
            Param(name="resource_id", location=Location.BODY),
            Param(name="referer_url", location=Location.BODY),
            Param(name="client_subscription_id", location=Location.BODY),
            Param(name="with_clean_history", location=Location.BODY),
            Param(name="project_id", location=Location.BODY),
            Param(name="additional_context", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
