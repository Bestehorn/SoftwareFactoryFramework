"""The ``search`` family of the GitHub operations index: search of code, commits, issues and pull requests, labels,
repositories, topics and users.

Each record is the section of ``docs/api-reference/github/rest/search.md`` its operation ID names: its method and path,
and the names of its ``query`` rows; no section has a path parameter or a request body. Every record pages by ``link``,
its ``200`` an object holding the page's results under ``items`` beside ``total_count``, the item key
``conventions.md`` "Lists wrapped in an object" names for every ``search/*`` operation (the Paging line of
``search/issues-and-pull-requests`` also names ``lexical_fallback_reason``; the table names ``items``). Every record
sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``: the ``text-match`` media type "Headers, media types and API
versions" lists for the search endpoints is not asked for.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "search"
#: ``conventions.md`` "Lists wrapped in an object": the key every ``search/*`` page holds its results under.
ITEM_KEY_ITEMS = "items"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/search.md "Search code": query ``q``, ``sort``, ``order``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/code",
        method="GET",
        path="/search/code",
        query_params=frozenset({"q", "sort", "order", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search commits": query ``q``, ``sort``, ``order``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/commits",
        method="GET",
        path="/search/commits",
        query_params=frozenset({"q", "sort", "order", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search issues and pull requests": query ``q``, ``sort``, ``order``, ``advanced_search``,
    # ``search_type``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/issues-and-pull-requests",
        method="GET",
        path="/search/issues",
        query_params=frozenset({"q", "sort", "order", "per_page", "page", "advanced_search", "search_type"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search labels": query ``repository_id``, ``q``, ``sort``, ``order``; page-based, items in
    # ``items``.
    RestOperation(
        operation_id="search/labels",
        method="GET",
        path="/search/labels",
        query_params=frozenset({"repository_id", "q", "sort", "order", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search repositories": query ``q``, ``sort``, ``order``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/repos",
        method="GET",
        path="/search/repositories",
        query_params=frozenset({"q", "sort", "order", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search topics": query ``q``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/topics",
        method="GET",
        path="/search/topics",
        query_params=frozenset({"q", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/search.md "Search users": query ``q``, ``sort``, ``order``; page-based, items in ``items``.
    RestOperation(
        operation_id="search/users",
        method="GET",
        path="/search/users",
        query_params=frozenset({"q", "sort", "order", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=ITEM_KEY_ITEMS,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
