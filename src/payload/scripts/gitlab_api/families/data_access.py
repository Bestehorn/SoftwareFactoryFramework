"""The ``data-access`` endpoint family of the GitLab wrapper: the batched background migrations and the database
migrations.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/data-access.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section:
the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- every row is ``Kind.SCALAR`` and none is required; every body is JSON and no record has ``fixed`` values;
- "List the last 20 batched background migrations" is ``Paging.OFFSET``, every other record ``Paging.NONE``: "List
  pending migrations" answers one object (AC-5).

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Location, Paging, Param, RestOperation

FAMILY = "data-access"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Batched background migrations API: List the last 20 batched background migrations".
    RestOperation(
        operation_id="data-access#list-the-last-20-batched-background-migrations",
        method="GET",
        path="/admin/batched_background_migrations",
        params=(
            Param(name="database", location=Location.QUERY),
            Param(name="job_class_name", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Batched background migrations API: Retrieve a batched background migration".
    RestOperation(
        operation_id="data-access#retrieve-a-batched-background-migration",
        method="GET",
        path="/admin/batched_background_migrations/:id",
        params=(Param(name="database", location=Location.QUERY),),
    ),
    # "Batched background migrations API: Pause a batched background migration".
    RestOperation(
        operation_id="data-access#pause-a-batched-background-migration",
        method="PUT",
        path="/admin/batched_background_migrations/:id/pause",
        params=(Param(name="database", location=Location.BODY),),
    ),
    # "Batched background migrations API: Resume a batched background migration".
    RestOperation(
        operation_id="data-access#resume-a-batched-background-migration",
        method="PUT",
        path="/admin/batched_background_migrations/:id/resume",
        params=(Param(name="database", location=Location.BODY),),
    ),
    # "Database migrations API: Mark a migration as successful".
    RestOperation(
        operation_id="data-access#mark-a-migration-as-successful",
        method="POST",
        path="/admin/migrations/:version/mark",
        params=(Param(name="database", location=Location.BODY),),
    ),
    # "Database migrations API: List pending migrations"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="data-access#list-pending-migrations",
        method="GET",
        path="/admin/migrations/pending",
        params=(Param(name="database", location=Location.QUERY),),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
