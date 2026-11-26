"""The ``classroom`` family of the GitHub operations index: GitHub Classroom's classrooms, assignments and grades.

Each record is the section of ``docs/api-reference/github/rest/classroom.md`` its operation ID names: its method and
path; no operation of the family has a query row or a request body. Every section is titled "Closed", is marked
deprecated, and documents ``410`` as its only response, so every record sends one request and no record pages. No
path parameter of the family may contain ``/``, so ``multi_segment`` is empty throughout, and every record sends
``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "classroom"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/classroom.md "Closed - Get an assignment": path parameters only; 410 only: the API is closed.
    RestOperation(
        operation_id="classroom/get-an-assignment",
        method="GET",
        path="/assignments/{assignment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/classroom.md "Closed - List accepted assignments for an assignment": path parameters only; 410 only: the API
    # is closed.
    RestOperation(
        operation_id="classroom/list-accepted-assignments-for-an-assignment",
        method="GET",
        path="/assignments/{assignment_id}/accepted_assignments",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/classroom.md "Closed - Get assignment grades": path parameters only; 410 only: the API is closed.
    RestOperation(
        operation_id="classroom/get-assignment-grades",
        method="GET",
        path="/assignments/{assignment_id}/grades",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/classroom.md "Closed - List classrooms": no parameters; 410 only: the API is closed.
    RestOperation(
        operation_id="classroom/list-classrooms",
        method="GET",
        path="/classrooms",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/classroom.md "Closed - Get a classroom": path parameters only; 410 only: the API is closed.
    RestOperation(
        operation_id="classroom/get-a-classroom",
        method="GET",
        path="/classrooms/{classroom_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/classroom.md "Closed - List assignments for a classroom": path parameters only; 410 only: the API is closed.
    RestOperation(
        operation_id="classroom/list-assignments-for-a-classroom",
        method="GET",
        path="/classrooms/{classroom_id}/assignments",
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
