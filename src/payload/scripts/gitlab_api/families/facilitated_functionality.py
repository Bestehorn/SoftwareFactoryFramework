"""The ``facilitated-functionality`` endpoint family of the GitLab wrapper: the event lists — all events, a
user's contribution events and a project's visible events.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/facilitated-functionality.md`` (issue #13, design.md D1 and D5; issue #38, change.md
AC-1 to AC-5), in page order under a comment naming its section: the method, the path as ``operations-index.md`` writes
it, and one ``Param`` per query row, in table order:

- every row is ``Kind.SCALAR`` and none is required; no record has a body or ``fixed`` values;
- every record is ``Paging.OFFSET``: two sections are headed "List", and "Retrieve contribution events for a user" has
  a ``page`` row.

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Location, Paging, Param, RestOperation

FAMILY = "facilitated-functionality"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Events API: List all events".
    RestOperation(
        operation_id="facilitated-functionality#list-all-events",
        method="GET",
        path="/events",
        params=(
            Param(name="action", location=Location.QUERY),
            Param(name="target_type", location=Location.QUERY),
            Param(name="before", location=Location.QUERY),
            Param(name="after", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Events API: Retrieve contribution events for a user"; paged by its `page` row.
    RestOperation(
        operation_id="facilitated-functionality#retrieve-contribution-events-for-a-user",
        method="GET",
        path="/users/:id/events",
        params=(
            Param(name="action", location=Location.QUERY),
            Param(name="target_type", location=Location.QUERY),
            Param(name="before", location=Location.QUERY),
            Param(name="after", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Events API: List all visible events for a project".
    RestOperation(
        operation_id="facilitated-functionality#list-all-visible-events-for-a-project",
        method="GET",
        path="/projects/:project_id/events",
        params=(
            Param(name="action", location=Location.QUERY),
            Param(name="target_type", location=Location.QUERY),
            Param(name="before", location=Location.QUERY),
            Param(name="after", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
