"""The ``security-governance`` endpoint family of the GitLab wrapper: a group's security settings.

Its one record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/security-governance.md`` (issue #42, the security slice of the wrapper rewrite;
issue #41 design.md D8): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per body
attribute with the table's Type column as its ``Kind``. The section has one endpoint, the family's one index key, so
``PENDING`` is empty.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Param, RestOperation

FAMILY = "security-governance"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Group security settings API: Update group security settings"; `projects_to_exclude` is an array of integers.
    RestOperation(
        operation_id="security-governance#update-group-security-settings",
        method="PUT",
        path="/groups/:id/security_settings",
        params=(
            Param(name="secret_push_protection_enabled", location=Location.BODY, required=True),
            Param(name="projects_to_exclude", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
