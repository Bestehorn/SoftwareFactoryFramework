"""The ``git`` family of the GitHub operations index: the Git database API (blobs, commits, references, tags, trees).

Each record is the section of ``docs/api-reference/github/rest/git.md`` its operation ID names: its method and path,
the names of its ``query`` rows, and the first-level fields of its request body (``author.name`` is a field of
``author``, ``tree[].path`` one of each ``tree`` item). A path parameter whose row reads "may contain ``/``
(multi-segment path)" is in ``multi_segment`` (``conventions.md`` "Path parameters"): its value keeps its ``/``
(``heads/feature/login``), a ``ref`` given without the ``refs/`` prefix, so ``registry.expand`` percent-encodes each
segment but not the slashes between them. ``git/list-matching-refs`` alone pages, by ``link``: its ``200`` is a bare
array with a ``Link`` header, so it has no item key; every other record sends one request.

``delete-remote-branch`` sends ``git/delete-ref`` (design D5); every record is also sent by ``call <operation-id>``
(#28), which refuses ``git/create-ref`` and ``git/update-ref``, the records that create or move a branch (#27 AC-7).
No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "git"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/git.md "Create a blob": body ``content`` and ``encoding``; 201 with a ``short-blob``.
    RestOperation(
        operation_id="git/create-blob",
        method="POST",
        path="/repos/{owner}/{repo}/git/blobs",
        query_params=frozenset(),
        body_params=frozenset({"content", "encoding"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Get a blob": path parameters only; 200 with a ``blob``.
    RestOperation(
        operation_id="git/get-blob",
        method="GET",
        path="/repos/{owner}/{repo}/git/blobs/{file_sha}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Create a commit": the first-level body fields; 201 with a ``git-commit``.
    RestOperation(
        operation_id="git/create-commit",
        method="POST",
        path="/repos/{owner}/{repo}/git/commits",
        query_params=frozenset(),
        body_params=frozenset({"message", "tree", "parents", "author", "committer", "signature"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Get a commit object": ``commit_sha`` may contain ``/``; 200 with a ``git-commit``.
    RestOperation(
        operation_id="git/get-commit",
        method="GET",
        path="/repos/{owner}/{repo}/git/commits/{commit_sha}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset({"commit_sha"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "List matching references": ``ref`` may contain ``/``; 200 with an array of ``git-ref`` and a
    # ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="git/list-matching-refs",
        method="GET",
        path="/repos/{owner}/{repo}/git/matching-refs/{ref}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Get a reference": ``ref`` may contain ``/``; 200 with a ``git-ref``.
    RestOperation(
        operation_id="git/get-ref",
        method="GET",
        path="/repos/{owner}/{repo}/git/ref/{ref}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Create a reference": body ``ref`` (with its ``refs/`` prefix) and ``sha``; 201 with a ``git-ref``.
    RestOperation(
        operation_id="git/create-ref",
        method="POST",
        path="/repos/{owner}/{repo}/git/refs",
        query_params=frozenset(),
        body_params=frozenset({"ref", "sha"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Update a reference": ``ref`` may contain ``/``; body ``sha`` and ``force``; 200 with a ``git-ref``.
    RestOperation(
        operation_id="git/update-ref",
        method="PATCH",
        path="/repos/{owner}/{repo}/git/refs/{ref}",
        query_params=frozenset(),
        body_params=frozenset({"sha", "force"}),
        multi_segment=frozenset({"ref"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
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
    # rest/git.md "Create a tag object": the first-level body fields; 201 with a ``git-tag``.
    RestOperation(
        operation_id="git/create-tag",
        method="POST",
        path="/repos/{owner}/{repo}/git/tags",
        query_params=frozenset(),
        body_params=frozenset({"tag", "message", "object", "type", "tagger"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Get a tag": path parameters only; 200 with a ``git-tag``.
    RestOperation(
        operation_id="git/get-tag",
        method="GET",
        path="/repos/{owner}/{repo}/git/tags/{tag_sha}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Create a tree": body ``tree`` (an array of entries) and ``base_tree``; 201 with a ``git-tree``.
    RestOperation(
        operation_id="git/create-tree",
        method="POST",
        path="/repos/{owner}/{repo}/git/trees",
        query_params=frozenset(),
        body_params=frozenset({"tree", "base_tree"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/git.md "Get a tree": ``tree_sha`` may contain ``/``; query ``recursive``; 200 with a ``git-tree``.
    RestOperation(
        operation_id="git/get-tree",
        method="GET",
        path="/repos/{owner}/{repo}/git/trees/{tree_sha}",
        query_params=frozenset({"recursive"}),
        body_params=frozenset(),
        multi_segment=frozenset({"tree_sha"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
