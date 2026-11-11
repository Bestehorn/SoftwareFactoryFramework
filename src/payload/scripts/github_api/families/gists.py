"""The ``gists`` family of the GitHub operations index: gists, their comments, commits, forks, stars and revisions.

Each record is the section of ``docs/api-reference/github/rest/gists.md`` its operation ID names: its method and path,
the names of its ``query`` rows, and the first-level fields of its JSON request body (``files.*.content`` is a field of
``files``). No path parameter row of the family reads "may contain ``/``" (``gists/get-revision``'s ``sha`` included),
so ``multi_segment`` is empty throughout.

A section with a ``Paging:`` line is ``Paging.LINK``: the comment list, the four gist lists (the authenticated user's,
the public, the starred and a user's), the commit list and the fork list. Each section names the response body as
the array and ``conventions.md`` "Lists wrapped in an object" names no ``gists/`` operation, so none has an item key;
every other record sends one request.

Every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, the documented default (``conventions.md`` "Headers,
media types and API versions"); the sections that name ``application/vnd.github.raw+json`` are not asked for it.
Every record is sent by ``call <operation-id>`` (#28). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "gists"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/gists.md "List gist comments": query ``per_page`` and ``page``; 200 with an array of ``gist-comment`` and a
    # ``Link`` header.
    RestOperation(
        operation_id="gists/list-comments",
        method="GET",
        path="/gists/{gist_id}/comments",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Create a gist comment": body ``body``; 201 with a ``gist-comment``.
    RestOperation(
        operation_id="gists/create-comment",
        method="POST",
        path="/gists/{gist_id}/comments",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Get a gist comment": path parameters only; 200 with a ``gist-comment``.
    RestOperation(
        operation_id="gists/get-comment",
        method="GET",
        path="/gists/{gist_id}/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Update a gist comment": body ``body``; 200 with a ``gist-comment``.
    RestOperation(
        operation_id="gists/update-comment",
        method="PATCH",
        path="/gists/{gist_id}/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Delete a gist comment": path parameters only; 204 on success.
    RestOperation(
        operation_id="gists/delete-comment",
        method="DELETE",
        path="/gists/{gist_id}/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List gists for the authenticated user": query ``since``, ``per_page`` and ``page``; 200 with an
    # array of ``base-gist`` and a ``Link`` header.
    RestOperation(
        operation_id="gists/list",
        method="GET",
        path="/gists",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Create a gist": body ``description``, ``files`` (keyed by file name) and ``public``; 201 with a
    # ``gist-simple``.
    RestOperation(
        operation_id="gists/create",
        method="POST",
        path="/gists",
        query_params=frozenset(),
        body_params=frozenset({"description", "files", "public"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List public gists": query ``since``, ``per_page`` and ``page``; 200 with an array of
    # ``base-gist`` and a ``Link`` header.
    RestOperation(
        operation_id="gists/list-public",
        method="GET",
        path="/gists/public",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List starred gists": query ``since``, ``per_page`` and ``page``; 200 with an array of
    # ``base-gist`` and a ``Link`` header.
    RestOperation(
        operation_id="gists/list-starred",
        method="GET",
        path="/gists/starred",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Get a gist": path parameter ``gist_id``; 200 with a ``gist-simple``.
    RestOperation(
        operation_id="gists/get",
        method="GET",
        path="/gists/{gist_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Update a gist": body ``description`` and ``files`` (a ``null`` entry deletes that file); 200 with
    # a ``gist-simple``.
    RestOperation(
        operation_id="gists/update",
        method="PATCH",
        path="/gists/{gist_id}",
        query_params=frozenset(),
        body_params=frozenset({"description", "files"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Delete a gist": path parameter ``gist_id``; 204 on success.
    RestOperation(
        operation_id="gists/delete",
        method="DELETE",
        path="/gists/{gist_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List gist commits": query ``per_page`` and ``page``; 200 with an array of ``gist-commit`` and a
    # ``Link`` header.
    RestOperation(
        operation_id="gists/list-commits",
        method="GET",
        path="/gists/{gist_id}/commits",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List gist forks": query ``per_page`` and ``page``; 200 with an array of ``gist-simple`` and a
    # ``Link`` header.
    RestOperation(
        operation_id="gists/list-forks",
        method="GET",
        path="/gists/{gist_id}/forks",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Fork a gist": path parameter ``gist_id``, no body; 201 with a ``base-gist``.
    RestOperation(
        operation_id="gists/fork",
        method="POST",
        path="/gists/{gist_id}/forks",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Check if a gist is starred": 204 when starred, 404 when not.
    RestOperation(
        operation_id="gists/check-is-starred",
        method="GET",
        path="/gists/{gist_id}/star",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Star a gist": path parameter ``gist_id``, no body; 204 on success.
    RestOperation(
        operation_id="gists/star",
        method="PUT",
        path="/gists/{gist_id}/star",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Unstar a gist": path parameter ``gist_id``; 204 on success.
    RestOperation(
        operation_id="gists/unstar",
        method="DELETE",
        path="/gists/{gist_id}/star",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "Get a gist revision": path parameters ``gist_id`` and ``sha``; 200 with a ``gist-simple``.
    RestOperation(
        operation_id="gists/get-revision",
        method="GET",
        path="/gists/{gist_id}/{sha}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gists.md "List gists for a user": query ``since``, ``per_page`` and ``page``; 200 with an array of
    # ``base-gist`` and a ``Link`` header.
    RestOperation(
        operation_id="gists/list-for-user",
        method="GET",
        path="/users/{username}/gists",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
