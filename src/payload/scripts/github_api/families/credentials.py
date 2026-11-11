"""The ``credentials`` family of the GitHub operations index: the revocation of leaked credentials.

The one record is the section of ``docs/api-reference/github/rest/credentials.md`` its operation ID names: its method
and path and the one field of its request body, ``credentials``. It does not page, has no ``multi_segment`` name, and
sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

``call credentials/revoke`` (#28) sends it: the call revokes the credentials it is given and writes no branch, so
``call`` does not refuse it; whether to run it is the caller's decision (#28 design, Security "Destructive
operations"). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "credentials"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/credentials.md "Revoke a list of credentials": body ``credentials``; 202 with an object; the credentials
    # given are revoked.
    RestOperation(
        operation_id="credentials/revoke",
        method="POST",
        path="/credentials/revoke",
        query_params=frozenset(),
        body_params=frozenset({"credentials"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
