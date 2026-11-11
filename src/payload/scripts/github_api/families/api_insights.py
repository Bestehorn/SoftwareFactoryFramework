"""The ``api-insights`` family of the GitHub operations index: an organization's API usage statistics, by route,
subject, summary, time and user.

Each record is the section of ``docs/api-reference/github/rest/orgs.md`` (its ``api-insights`` part) its operation ID
names: its method and path and the names of its ``query`` rows; no operation of the family takes a request body. The
three sections with a ``Paging:`` line, ``get-route-stats-by-actor``, ``get-subject-stats`` and ``get-user-stats``,
page by ``link``: each ``200`` is the array, and "Lists wrapped in an object" names none of them, so none has an item
key. The summary and time stats have no ``Paging:`` line and send one request. No path parameter of the family may
contain ``/``, so ``multi_segment`` is empty throughout, and every record sends ``API_VERSION_DEFAULT`` and
``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "api-insights"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/orgs.md "Get route stats by actor": the query rows; page-based, the body is the array.
    RestOperation(
        operation_id="api-insights/get-route-stats-by-actor",
        method="GET",
        path="/orgs/{org}/insights/api/route-stats/{actor_type}/{actor_id}",
        query_params=frozenset(
            {"min_timestamp", "max_timestamp", "page", "per_page", "direction", "sort", "api_route_substring"}
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get subject stats": the query rows; page-based, the body is the array.
    RestOperation(
        operation_id="api-insights/get-subject-stats",
        method="GET",
        path="/orgs/{org}/insights/api/subject-stats",
        query_params=frozenset(
            {"min_timestamp", "max_timestamp", "page", "per_page", "direction", "sort", "subject_name_substring"}
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get summary stats": query ``min_timestamp`` and ``max_timestamp``; 200 with an
    # ``api-insights-summary-stats``.
    RestOperation(
        operation_id="api-insights/get-summary-stats",
        method="GET",
        path="/orgs/{org}/insights/api/summary-stats",
        query_params=frozenset({"min_timestamp", "max_timestamp"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get summary stats by user": query ``min_timestamp`` and ``max_timestamp``; 200 with an
    # ``api-insights-summary-stats``.
    RestOperation(
        operation_id="api-insights/get-summary-stats-by-user",
        method="GET",
        path="/orgs/{org}/insights/api/summary-stats/users/{user_id}",
        query_params=frozenset({"min_timestamp", "max_timestamp"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get summary stats by actor": query ``min_timestamp`` and ``max_timestamp``; 200 with an
    # ``api-insights-summary-stats``.
    RestOperation(
        operation_id="api-insights/get-summary-stats-by-actor",
        method="GET",
        path="/orgs/{org}/insights/api/summary-stats/{actor_type}/{actor_id}",
        query_params=frozenset({"min_timestamp", "max_timestamp"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get time stats": query ``min_timestamp``, ``max_timestamp`` and ``timestamp_increment``; 200 with
    # ``api-insights-time-stats``, an array of objects.
    RestOperation(
        operation_id="api-insights/get-time-stats",
        method="GET",
        path="/orgs/{org}/insights/api/time-stats",
        query_params=frozenset({"min_timestamp", "max_timestamp", "timestamp_increment"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get time stats by user": query ``min_timestamp``, ``max_timestamp`` and ``timestamp_increment``; 200
    # with ``api-insights-time-stats``, an array of objects.
    RestOperation(
        operation_id="api-insights/get-time-stats-by-user",
        method="GET",
        path="/orgs/{org}/insights/api/time-stats/users/{user_id}",
        query_params=frozenset({"min_timestamp", "max_timestamp", "timestamp_increment"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get time stats by actor": query ``min_timestamp``, ``max_timestamp`` and ``timestamp_increment``;
    # 200 with ``api-insights-time-stats``, an array of objects.
    RestOperation(
        operation_id="api-insights/get-time-stats-by-actor",
        method="GET",
        path="/orgs/{org}/insights/api/time-stats/{actor_type}/{actor_id}",
        query_params=frozenset({"min_timestamp", "max_timestamp", "timestamp_increment"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get user stats": the query rows; page-based, the body is the array.
    RestOperation(
        operation_id="api-insights/get-user-stats",
        method="GET",
        path="/orgs/{org}/insights/api/user-stats/{user_id}",
        query_params=frozenset(
            {"min_timestamp", "max_timestamp", "page", "per_page", "direction", "sort", "actor_name_substring"}
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
