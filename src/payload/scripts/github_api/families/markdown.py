"""The ``markdown`` family of the GitHub operations index: the rendering of a Markdown document as HTML.

The one record, ``markdown/render``, is the section of ``docs/api-reference/github/rest/markdown.md`` its operation ID
names: its method and path and the first-level fields of its JSON request body (``text``, ``mode``, ``context``). It
does not page, has no ``multi_segment`` name, and sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``; its ``200`` is
``text/html``, which ``call`` writes to standard output unchanged (#28 D3).

``call markdown/render`` (#28) sends it. ``markdown/render-raw`` stays on ``PENDING``: its request body is the
document as ``text/plain`` or ``text/x-markdown``, not a JSON object, which ``Transport.request`` does not send; issue
#46 owns that request form (issue #33 DL-001).
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "markdown"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/markdown.md "Render a Markdown document": body ``text``, ``mode`` and ``context``; 200 with ``text/html``
    # text; ``call`` writes the HTML unchanged (#28 D3).
    RestOperation(
        operation_id="markdown/render",
        method="POST",
        path="/markdown",
        query_params=frozenset(),
        body_params=frozenset({"text", "mode", "context"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset({"markdown/render-raw"})
