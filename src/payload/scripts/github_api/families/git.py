"""The ``git`` family of the GitHub operations index: the Git database API (blobs, commits, references, tags, trees).

Part 1 declares the one record the compatibility commands use (design D5): ``git/delete-ref``, which
``delete-remote-branch`` sends. Its ``ref`` is a multi-segment path parameter (``conventions.md`` "Path
parameters"): the value keeps its ``/`` (``heads/feature/login``) and is given without the ``refs/`` prefix, so
``registry.expand`` percent-encodes each segment but not the slashes between them. Every other operation of the
family is on ``PENDING`` until a record covers it (part 2, #14).
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "git"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/git.md "Delete a reference": path parameters only, no query, no body; 204 on success.
    RestOperation(
        operation_id="git/delete-ref",
        method="DELETE",
        path="/repos/{owner}/{repo}/git/refs/{ref}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset(
    {
        "git/get-blob",
        "git/create-blob",
        "git/get-commit",
        "git/create-commit",
        "git/list-matching-refs",
        "git/get-ref",
        "git/update-ref",
        "git/create-ref",
        "git/get-tag",
        "git/create-tag",
        "git/get-tree",
        "git/create-tree",
    }
)
