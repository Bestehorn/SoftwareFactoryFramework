"""The ``meta`` family of the GitHub operations index: the API root, GitHub's meta information, its API versions, the
Octocat and the Zen of GitHub.

Each record is the section of ``docs/api-reference/github/rest/meta.md`` its operation ID names: its method and path
and the names of its ``query`` rows (``s``, the Octocat's speech bubble); no operation of the family has a request
body. No section has a ``Paging:`` line, so every record sends one request, ``get-all-versions`` too, although its
``200`` is an array. No path has a parameter, so ``multi_segment`` is empty throughout, and every record sends
``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

``meta/get-zen`` answers ``text/plain`` and ``meta/get-octocat`` ``application/octocat-stream``; ``call`` writes a body
that is not JSON to standard output unchanged (#28 D3), so both are plain records (issue #33 DL-002). Every record is
sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "meta"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/meta.md "GitHub API Root": no parameters; 200 with a ``root``.
    RestOperation(
        operation_id="meta/root",
        method="GET",
        path="/",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/meta.md "Get GitHub meta information": no parameters; 200 with an ``api-overview``.
    RestOperation(
        operation_id="meta/get",
        method="GET",
        path="/meta",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/meta.md "Get Octocat": query ``s``; 200 with ``application/octocat-stream`` text; ``call`` writes the text
    # unchanged (#28 D3).
    RestOperation(
        operation_id="meta/get-octocat",
        method="GET",
        path="/octocat",
        query_params=frozenset({"s"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/meta.md "Get all API versions": no parameters; 200 with an array of date strings.
    RestOperation(
        operation_id="meta/get-all-versions",
        method="GET",
        path="/versions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/meta.md "Get the Zen of GitHub": no parameters; 200 with ``text/plain`` text; ``call`` writes the text
    # unchanged (#28 D3).
    RestOperation(
        operation_id="meta/get-zen",
        method="GET",
        path="/zen",
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
