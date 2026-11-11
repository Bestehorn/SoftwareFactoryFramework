"""The ``growth`` endpoint family of the GitLab wrapper: broadcast messages and experiments.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/growth.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section:
the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- an ``array of integers`` row (``target_access_levels``) is ``Kind.ARRAY``, every other row ``SCALAR``; ``required``
  is the Required column's ``yes``; no record has ``fixed`` values;
- each ``context[...]`` row has no ``context`` row, so it is a ``Param`` of its own: a query pair of "Get the current
  assignment" and "Clear a variant assignment", and a body pair of "Force a variant assignment", whose body is
  therefore ``BodyFormat.FORM`` (issue #41, design.md D5); every other body is JSON;
- "List all broadcast messages" and "List all experiments" are ``Paging.OFFSET``, every other record ``Paging.NONE``.

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import BodyFormat, Kind, Location, Paging, Param, RestOperation

FAMILY = "growth"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Broadcast Messages API: List all broadcast messages".
    RestOperation(
        operation_id="growth#list-all-broadcast-messages",
        method="GET",
        path="/broadcast_messages",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Broadcast Messages API: Retrieve a broadcast message".
    RestOperation(
        operation_id="growth#retrieve-a-broadcast-message",
        method="GET",
        path="/broadcast_messages/:id",
    ),
    # "Broadcast Messages API: Create a broadcast message".
    RestOperation(
        operation_id="growth#create-a-broadcast-message",
        method="POST",
        path="/broadcast_messages",
        params=(
            Param(name="message", location=Location.BODY, required=True),
            Param(name="starts_at", location=Location.BODY),
            Param(name="ends_at", location=Location.BODY),
            Param(name="font", location=Location.BODY),
            Param(name="target_access_levels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="target_path", location=Location.BODY),
            Param(name="broadcast_type", location=Location.BODY),
            Param(name="dismissable", location=Location.BODY),
            Param(name="theme", location=Location.BODY),
            Param(name="color", location=Location.BODY),
        ),
    ),
    # "Broadcast Messages API: Update a broadcast message".
    RestOperation(
        operation_id="growth#update-a-broadcast-message",
        method="PUT",
        path="/broadcast_messages/:id",
        params=(
            Param(name="message", location=Location.BODY),
            Param(name="starts_at", location=Location.BODY),
            Param(name="ends_at", location=Location.BODY),
            Param(name="font", location=Location.BODY),
            Param(name="target_access_levels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="target_path", location=Location.BODY),
            Param(name="broadcast_type", location=Location.BODY),
            Param(name="dismissable", location=Location.BODY),
            Param(name="theme", location=Location.BODY),
            Param(name="color", location=Location.BODY),
        ),
    ),
    # "Broadcast Messages API: Delete a broadcast message".
    RestOperation(
        operation_id="growth#delete-a-broadcast-message",
        method="DELETE",
        path="/broadcast_messages/:id",
    ),
    # "Experiments API: List all experiments".
    RestOperation(
        operation_id="growth#list-all-experiments",
        method="GET",
        path="/experiments",
        paging=Paging.OFFSET,
    ),
    # "Experiments API: Delete cached assignments".
    RestOperation(
        operation_id="growth#delete-cached-assignments",
        method="DELETE",
        path="/experiments/:name/cache",
    ),
    # "Experiments API: Force a variant assignment"; each `context[...]` row has no `context` row, so the body is FORM
    # and each is a pair of its own (#41 D5).
    RestOperation(
        operation_id="growth#force-a-variant-assignment",
        method="POST",
        path="/experiments/:experiment_name/assignments",
        params=(
            Param(name="variant", location=Location.BODY, required=True),
            Param(name="context[user]", location=Location.BODY),
            Param(name="context[namespace]", location=Location.BODY),
            Param(name="context[project]", location=Location.BODY),
        ),
        body=BodyFormat.FORM,
    ),
    # "Experiments API: Get the current assignment"; each `context[...]` row has no `context` row, so it is a query
    # Param of its own.
    RestOperation(
        operation_id="growth#get-the-current-assignment",
        method="GET",
        path="/experiments/:experiment_name/assignments",
        params=(
            Param(name="context[user]", location=Location.QUERY),
            Param(name="context[namespace]", location=Location.QUERY),
            Param(name="context[project]", location=Location.QUERY),
        ),
    ),
    # "Experiments API: Clear a variant assignment"; each `context[...]` row has no `context` row, so it is a query
    # Param of its own.
    RestOperation(
        operation_id="growth#clear-a-variant-assignment",
        method="DELETE",
        path="/experiments/:experiment_name/assignments",
        params=(
            Param(name="context[user]", location=Location.QUERY),
            Param(name="context[namespace]", location=Location.QUERY),
            Param(name="context[project]", location=Location.QUERY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
