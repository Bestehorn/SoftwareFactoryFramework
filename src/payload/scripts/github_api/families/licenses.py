"""The ``licenses`` family of the GitHub operations index: the licenses GitHub knows and a repository's license.

Each record is the section of ``docs/api-reference/github/rest/licenses.md`` its operation ID names: its method and
path and the names of its ``query`` rows; no operation of the family has a request body.
``licenses/get-all-commonly-used`` alone pages, by ``link``: its ``200`` is the array, and "Lists wrapped in an
object" names no ``licenses`` operation, so it has no item key; the other two sections have no ``Paging:`` line, so
their records send one request. No path parameter of the family may contain ``/``, so ``multi_segment`` is empty
throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``: ``licenses/get-for-repo`` too,
although its docs name ``application/vnd.github.html+json`` and ``application/vnd.github.raw+json``; those media types
are #28's requirements residual, not this record's.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "licenses"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/licenses.md "Get all commonly used licenses": query ``featured``; page-based, the body is the array.
    RestOperation(
        operation_id="licenses/get-all-commonly-used",
        method="GET",
        path="/licenses",
        query_params=frozenset({"featured", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/licenses.md "Get a license": path parameters only; 200 with a ``license``.
    RestOperation(
        operation_id="licenses/get",
        method="GET",
        path="/licenses/{license}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/licenses.md "Get the license for a repository": query ``ref``; 200 with a ``license-content``; sent with
    # ``ACCEPT_JSON``, not the ``html`` or ``raw`` media types the docs name (#28's requirements residual).
    RestOperation(
        operation_id="licenses/get-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/license",
        query_params=frozenset({"ref"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
