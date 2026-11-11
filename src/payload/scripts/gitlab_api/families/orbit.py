"""The ``orbit`` endpoint family of the GitLab wrapper: the Orbit graph search, entity context, queries and the
deployed skills.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/orbit.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5; issue #15, change.md AC-1), in page order under a
comment naming its section: the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or
body row, in table order:

- a ``string array`` row (``scopes``, ``tokens``) is ``Kind.ARRAY``, a ``hash`` row (``parameters``) ``HASH``, every
  other row ``SCALAR``; ``required`` is the Required column's ``yes`` (the ``conditional`` rows of the search are
  not); every body is JSON and no record has ``fixed`` values;
- every record is ``Paging.NONE``: the Orbit "List" sections answer one object (AC-5).

``PENDING`` is empty. "Retrieve a deployed skill file", ``GET /orbit/skills/:name/*path``, has its record since issue
#15: its two rows, ``name`` and ``path``, are path rows, so it declares no ``Param``, and ``call`` sends it with each
``/`` of the ``*path`` value kept, each part one encoded segment (issue #40, design.md D1; issue #15 AC-4).

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Param, RestOperation

FAMILY = "orbit"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Orbit API: List all graph entities that match a search"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="orbit#list-all-graph-entities-that-match-a-search",
        method="GET",
        path="/orbit/grep",
        params=(
            Param(name="search", location=Location.QUERY, required=True),
            Param(name="full_path", location=Location.QUERY),
            Param(name="limit", location=Location.QUERY),
            Param(name="namespace_id", location=Location.QUERY),
            Param(name="per_scope", location=Location.QUERY),
            Param(name="project_id", location=Location.QUERY),
            Param(name="response_format", location=Location.QUERY),
            Param(name="scopes", location=Location.QUERY, kind=Kind.ARRAY),
        ),
    ),
    # "Orbit API: Retrieve entity context".
    RestOperation(
        operation_id="orbit#retrieve-entity-context",
        method="POST",
        path="/orbit/context",
        params=(
            Param(name="tokens", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="expand", location=Location.BODY),
            Param(name="response_format", location=Location.BODY),
        ),
    ),
    # "Orbit API: Run a query".
    RestOperation(
        operation_id="orbit#run-a-query",
        method="POST",
        path="/orbit/query",
        params=(
            Param(name="query", location=Location.BODY, required=True),
            Param(name="response_format", location=Location.BODY),
            Param(name="source_type", location=Location.BODY),
        ),
    ),
    # "Orbit API: Run a named query".
    RestOperation(
        operation_id="orbit#run-a-named-query",
        method="POST",
        path="/orbit/query/:name",
        params=(
            Param(name="parameters", location=Location.BODY, kind=Kind.HASH),
            Param(name="response_format", location=Location.BODY),
            Param(name="source_type", location=Location.BODY),
        ),
    ),
    # "Orbit API: List all deployed skills"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="orbit#list-all-deployed-skills",
        method="GET",
        path="/orbit/skills",
    ),
    # "Orbit API: Retrieve a deployed skill".
    RestOperation(
        operation_id="orbit#retrieve-a-deployed-skill",
        method="GET",
        path="/orbit/skills/:name",
    ),
    # "Orbit API: Check deployed skill metadata".
    RestOperation(
        operation_id="orbit#check-deployed-skill-metadata",
        method="HEAD",
        path="/orbit/skills/:name",
    ),
    # "Orbit API: Retrieve a deployed skill file"; its `name` and `path` rows are path rows, so it has no Param.
    RestOperation(
        operation_id="orbit#retrieve-a-deployed-skill-file",
        method="GET",
        path="/orbit/skills/:name/*path",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
