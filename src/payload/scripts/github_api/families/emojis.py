"""The ``emojis`` family of the GitHub operations index: the emoji names and image URLs GitHub knows.

The one record is the section of ``docs/api-reference/github/rest/emojis.md`` its operation ID names: its method and
path, with no parameter and no request body. It answers one object, so it does not page; it has no ``multi_segment``
name and sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

``call emojis/get`` (#28) sends it; ``call`` refuses no record of the family. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "emojis"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/emojis.md "Get emojis": no parameters; 200 with an object.
    RestOperation(
        operation_id="emojis/get",
        method="GET",
        path="/emojis",
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
