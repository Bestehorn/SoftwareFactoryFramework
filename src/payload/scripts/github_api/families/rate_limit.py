"""The ``rate-limit`` family of the GitHub operations index: the authenticated user's rate limit status.

The one record is the section of ``docs/api-reference/github/rest/rate-limit.md`` its operation ID names: its method
and path, with no parameter and no request body. Its section has no ``Paging:`` line, so it sends one request; it has
no ``multi_segment`` name and sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

``call rate-limit/get`` (#28) sends it; ``call`` refuses no record of the family. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "rate-limit"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/rate-limit.md "Get rate limit status for the authenticated user": no parameters; 200 with a
    # ``rate-limit-overview``.
    RestOperation(
        operation_id="rate-limit/get",
        method="GET",
        path="/rate_limit",
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
