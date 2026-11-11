"""The ``markdown`` family of the GitHub operations index: the rendering of a Markdown document as HTML.

The two records, ``markdown/render`` and ``markdown/render-raw``, are the sections of
``docs/api-reference/github/rest/markdown.md`` their operation IDs name: each one's method and path, and for
``markdown/render`` the first-level fields of its JSON request body (``text``, ``mode``, ``context``). Neither pages
nor has a ``multi_segment`` name, and both send ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``; each ``200`` is
``text/html``, which ``call`` writes to standard output unchanged (#28 D3).

``call markdown/render`` (#28) sends the JSON body. ``markdown/render-raw``'s body is the document itself, read by
``call --input`` and sent as ``CONTENT_TYPE_TEXT``, the first of its section's two ``Request body`` media types (issue
#46 D4); ``PENDING`` is empty.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT, CONTENT_TYPE_TEXT

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
    # rest/markdown.md "Render a Markdown document in raw mode": body the document as ``text/plain``, the first of its
    # two ``Request body`` lines, from ``call --input``; 200 with ``text/html`` text, written unchanged (#28 D3).
    RestOperation(
        operation_id="markdown/render-raw",
        method="POST",
        path="/markdown/raw",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
        content_type=CONTENT_TYPE_TEXT,
    ),
)

PENDING: FrozenSet[str] = frozenset()
