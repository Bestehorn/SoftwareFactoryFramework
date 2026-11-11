"""The ``gitignore`` family of the GitHub operations index: GitHub's ``.gitignore`` templates.

Each record is the section of ``docs/api-reference/github/rest/gitignore.md`` its operation ID names: its method and
path; neither operation has a query row or a request body. Neither section has a ``Paging:`` line, so both records
send one request, ``get-all-templates`` too, although its ``200`` is an array of names. ``name`` may not contain
``/``, so ``multi_segment`` is empty, and both records send ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``:
``gitignore/get-template`` too, although its docs name ``application/vnd.github.raw+json``, which returns the template
as text; that media type is #28's requirements residual, not this record's.

Every record is sent by ``call <operation-id>`` (#28), which refuses neither. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "gitignore"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/gitignore.md "Get all gitignore templates": no parameters; 200 with an array of strings.
    RestOperation(
        operation_id="gitignore/get-all-templates",
        method="GET",
        path="/gitignore/templates",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/gitignore.md "Get a gitignore template": path parameters only; 200 with a ``gitignore-template``; sent with
    # ``ACCEPT_JSON``, not the ``raw`` media type the docs name (#28's requirements residual).
    RestOperation(
        operation_id="gitignore/get-template",
        method="GET",
        path="/gitignore/templates/{name}",
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
