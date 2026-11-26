"""The ``activity`` family of the GitHub operations index: events, feeds, notifications, starring and watching.

Each record is the section of ``docs/api-reference/github/rest/activity.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its JSON request body. No path parameter row of
the family reads "may contain ``/``", so ``multi_segment`` is empty throughout.

A section with a ``Paging:`` line is ``Paging.LINK``: the nine event lists, the two notification lists, the stargazer
list and the star history, the two starred-repository lists, the watcher list and the two watched-repository lists.
``conventions.md`` "Lists wrapped in an object" names no ``activity/`` operation, so each pages a bare array and has
no item key; every other record sends one request.

Every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, the documented default (``conventions.md`` "Headers,
media types and API versions"). The sections of ``activity/list-stargazers-for-repo``,
``activity/list-repos-starred-by-authenticated-user`` and ``activity/list-repos-starred-by-user`` name
``application/vnd.github.star+json``, which adds ``starred_at`` to each entry; their records do not ask for it.
Every record is sent by ``call <operation-id>`` (#28). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "activity"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/activity.md "List public events": query ``per_page`` and ``page``; 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-public-events",
        method="GET",
        path="/events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List public events for a network of repositories": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-public-events-for-repo-network",
        method="GET",
        path="/networks/{owner}/{repo}/events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List public organization events": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-public-org-events",
        method="GET",
        path="/orgs/{org}/events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repository events": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-repo-events",
        method="GET",
        path="/repos/{owner}/{repo}/events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List events for the authenticated user": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-events-for-authenticated-user",
        method="GET",
        path="/users/{username}/events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List organization events for the authenticated user": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-org-events-for-authenticated-user",
        method="GET",
        path="/users/{username}/events/orgs/{org}",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List public events for a user": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-public-events-for-user",
        method="GET",
        path="/users/{username}/events/public",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List events received by the authenticated user": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-received-events-for-user",
        method="GET",
        path="/users/{username}/received_events",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List public events received by a user": 200 with an array of ``event``.
    RestOperation(
        operation_id="activity/list-received-public-events-for-user",
        method="GET",
        path="/users/{username}/received_events/public",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get feeds": no parameter; 200 with a ``feed``.
    RestOperation(
        operation_id="activity/get-feeds",
        method="GET",
        path="/feeds",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List notifications for the authenticated user": ``before`` is a timestamp filter; 200 with an
    # array of ``thread`` and a ``Link`` header.
    RestOperation(
        operation_id="activity/list-notifications-for-authenticated-user",
        method="GET",
        path="/notifications",
        query_params=frozenset({"all", "is_done", "participating", "since", "before", "page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Mark notifications as read": body ``last_read_at`` and ``read``; 202 or 205.
    RestOperation(
        operation_id="activity/mark-notifications-as-read",
        method="PUT",
        path="/notifications",
        query_params=frozenset(),
        body_params=frozenset({"last_read_at", "read"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get a thread": path parameter ``thread_id``; 200 with a ``thread``.
    RestOperation(
        operation_id="activity/get-thread",
        method="GET",
        path="/notifications/threads/{thread_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Mark a thread as read": path parameter ``thread_id``, no body; 205 on success.
    RestOperation(
        operation_id="activity/mark-thread-as-read",
        method="PATCH",
        path="/notifications/threads/{thread_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Mark a thread as done": path parameter ``thread_id``; 204 on success.
    RestOperation(
        operation_id="activity/mark-thread-as-done",
        method="DELETE",
        path="/notifications/threads/{thread_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get a thread subscription for the authenticated user": 200 with a ``thread-subscription``.
    RestOperation(
        operation_id="activity/get-thread-subscription-for-authenticated-user",
        method="GET",
        path="/notifications/threads/{thread_id}/subscription",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Set a thread subscription": body ``ignored``; 200 with a ``thread-subscription``.
    RestOperation(
        operation_id="activity/set-thread-subscription",
        method="PUT",
        path="/notifications/threads/{thread_id}/subscription",
        query_params=frozenset(),
        body_params=frozenset({"ignored"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Delete a thread subscription": path parameter ``thread_id``; 204 on success.
    RestOperation(
        operation_id="activity/delete-thread-subscription",
        method="DELETE",
        path="/notifications/threads/{thread_id}/subscription",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repository notifications for the authenticated user": ``before`` is a timestamp filter;
    # 200 with an array of ``thread`` and a ``Link`` header.
    RestOperation(
        operation_id="activity/list-repo-notifications-for-authenticated-user",
        method="GET",
        path="/repos/{owner}/{repo}/notifications",
        query_params=frozenset({"all", "is_done", "participating", "since", "before", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Mark repository notifications as read": body ``last_read_at``; 202 or 205.
    RestOperation(
        operation_id="activity/mark-repo-notifications-as-read",
        method="PUT",
        path="/repos/{owner}/{repo}/notifications",
        query_params=frozenset(),
        body_params=frozenset({"last_read_at"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List stargazers": 200 with an array of ``simple-user`` and a ``Link`` header (``stargazer``
    # entries under ``application/vnd.github.star+json``, which the record does not ask for).
    RestOperation(
        operation_id="activity/list-stargazers-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/stargazers",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get stargazer count": path parameters only; 200 with an object.
    RestOperation(
        operation_id="activity/get-stargazer-count-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/stargazers/count",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get repository star history": 200 with an array of ``stargazer-history`` and a ``Link`` header.
    RestOperation(
        operation_id="activity/get-stargazer-history-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/stargazers/history",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repositories starred by the authenticated user": 200 with an array of ``repository``
    # and a ``Link`` header (``starred-repository`` under the star media type, which the record does not ask for).
    RestOperation(
        operation_id="activity/list-repos-starred-by-authenticated-user",
        method="GET",
        path="/user/starred",
        query_params=frozenset({"sort", "direction", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Check if a repository is starred by the authenticated user": 204 when starred, 404 when not.
    RestOperation(
        operation_id="activity/check-repo-is-starred-by-authenticated-user",
        method="GET",
        path="/user/starred/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Star a repository for the authenticated user": no body; 204 on success.
    RestOperation(
        operation_id="activity/star-repo-for-authenticated-user",
        method="PUT",
        path="/user/starred/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Unstar a repository for the authenticated user": 204 on success.
    RestOperation(
        operation_id="activity/unstar-repo-for-authenticated-user",
        method="DELETE",
        path="/user/starred/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repositories starred by a user": 200 with an array and a ``Link`` header (the star media
    # type, which the record does not ask for, adds ``starred_at``).
    RestOperation(
        operation_id="activity/list-repos-starred-by-user",
        method="GET",
        path="/users/{username}/starred",
        query_params=frozenset({"sort", "direction", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List watchers": 200 with an array of ``simple-user`` and a ``Link`` header.
    RestOperation(
        operation_id="activity/list-watchers-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/subscribers",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Get a repository subscription": path parameters only; 200 with a ``repository-subscription``.
    RestOperation(
        operation_id="activity/get-repo-subscription",
        method="GET",
        path="/repos/{owner}/{repo}/subscription",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Set a repository subscription": body ``subscribed`` and ``ignored``; 200 with a
    # ``repository-subscription``.
    RestOperation(
        operation_id="activity/set-repo-subscription",
        method="PUT",
        path="/repos/{owner}/{repo}/subscription",
        query_params=frozenset(),
        body_params=frozenset({"subscribed", "ignored"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "Delete a repository subscription": path parameters only; 204 on success.
    RestOperation(
        operation_id="activity/delete-repo-subscription",
        method="DELETE",
        path="/repos/{owner}/{repo}/subscription",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repositories watched by the authenticated user": 200 with an array of
    # ``minimal-repository`` and a ``Link`` header.
    RestOperation(
        operation_id="activity/list-watched-repos-for-authenticated-user",
        method="GET",
        path="/user/subscriptions",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/activity.md "List repositories watched by a user": 200 with an array of ``minimal-repository`` and a
    # ``Link`` header.
    RestOperation(
        operation_id="activity/list-repos-watched-by-user",
        method="GET",
        path="/users/{username}/subscriptions",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
