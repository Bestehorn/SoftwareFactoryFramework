"""The ``codes-of-conduct`` family of the GitHub operations index: the codes of conduct GitHub offers.

Each record is the section of ``docs/api-reference/github/rest/codes-of-conduct.md`` its operation ID names: its
method and path; neither operation has a query row or a request body. Neither section has a ``Paging:`` line, so both
records send one request, ``get-all-codes-of-conduct`` too, although its ``200`` is an array. ``key`` may not contain
``/``, so ``multi_segment`` is empty, and both records send ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses neither. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "codes-of-conduct"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/codes-of-conduct.md "Get all codes of conduct": no parameters; 200 with an array of ``code-of-conduct``.
    RestOperation(
        operation_id="codes-of-conduct/get-all-codes-of-conduct",
        method="GET",
        path="/codes_of_conduct",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codes-of-conduct.md "Get a code of conduct": path parameters only; 200 with a ``code-of-conduct``.
    RestOperation(
        operation_id="codes-of-conduct/get-conduct-code",
        method="GET",
        path="/codes_of_conduct/{key}",
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
