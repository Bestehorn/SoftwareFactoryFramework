"""The ``reactions`` family of the GitHub operations index: the reactions on commit comments, issue comments, issues,
pull request review comments and releases.

Each record is the section of ``docs/api-reference/github/rest/reactions.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body (``content``, the reaction, on
every create record). The five ``list-for-*`` records page by ``link``: each ``200`` is a bare array of ``reaction``
with a ``Link`` header, and "Lists wrapped in an object" names none of them, so none has an item key; every create and
delete record sends one request. No path parameter of the family may contain ``/``, so ``multi_segment`` is empty
throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "reactions"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/reactions.md "List reactions for a commit comment": query ``content``; page-based, the body is the array.
    RestOperation(
        operation_id="reactions/list-for-commit-comment",
        method="GET",
        path="/repos/{owner}/{repo}/comments/{comment_id}/reactions",
        query_params=frozenset({"content", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Create reaction for a commit comment": body ``content``; 200 or 201 with a ``reaction``.
    RestOperation(
        operation_id="reactions/create-for-commit-comment",
        method="POST",
        path="/repos/{owner}/{repo}/comments/{comment_id}/reactions",
        query_params=frozenset(),
        body_params=frozenset({"content"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Delete a commit comment reaction": path parameters only; 204 on success.
    RestOperation(
        operation_id="reactions/delete-for-commit-comment",
        method="DELETE",
        path="/repos/{owner}/{repo}/comments/{comment_id}/reactions/{reaction_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "List reactions for an issue comment": query ``content``; page-based, the body is the array.
    RestOperation(
        operation_id="reactions/list-for-issue-comment",
        method="GET",
        path="/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
        query_params=frozenset({"content", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Create reaction for an issue comment": body ``content``; 200 or 201 with a ``reaction``.
    RestOperation(
        operation_id="reactions/create-for-issue-comment",
        method="POST",
        path="/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
        query_params=frozenset(),
        body_params=frozenset({"content"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Delete an issue comment reaction": path parameters only; 204 on success.
    RestOperation(
        operation_id="reactions/delete-for-issue-comment",
        method="DELETE",
        path="/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions/{reaction_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "List reactions for an issue": query ``content``; page-based, the body is the array.
    RestOperation(
        operation_id="reactions/list-for-issue",
        method="GET",
        path="/repos/{owner}/{repo}/issues/{issue_number}/reactions",
        query_params=frozenset({"content", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Create reaction for an issue": body ``content``; 200 or 201 with a ``reaction``.
    RestOperation(
        operation_id="reactions/create-for-issue",
        method="POST",
        path="/repos/{owner}/{repo}/issues/{issue_number}/reactions",
        query_params=frozenset(),
        body_params=frozenset({"content"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Delete an issue reaction": path parameters only; 204 on success.
    RestOperation(
        operation_id="reactions/delete-for-issue",
        method="DELETE",
        path="/repos/{owner}/{repo}/issues/{issue_number}/reactions/{reaction_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "List reactions for a pull request review comment": query ``content``; page-based, the body is
    # the array.
    RestOperation(
        operation_id="reactions/list-for-pull-request-review-comment",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions",
        query_params=frozenset({"content", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Create reaction for a pull request review comment": body ``content``; 200 or 201 with a
    # ``reaction``.
    RestOperation(
        operation_id="reactions/create-for-pull-request-review-comment",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions",
        query_params=frozenset(),
        body_params=frozenset({"content"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Delete a pull request comment reaction": path parameters only; 204 on success. Its operation
    # ID reads ``pull-request-comment``, not ``pull-request-review-comment``, as the section writes it.
    RestOperation(
        operation_id="reactions/delete-for-pull-request-comment",
        method="DELETE",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions/{reaction_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "List reactions for a release": query ``content``; page-based, the body is the array.
    RestOperation(
        operation_id="reactions/list-for-release",
        method="GET",
        path="/repos/{owner}/{repo}/releases/{release_id}/reactions",
        query_params=frozenset({"content", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Create reaction for a release": body ``content``; 200 or 201 with a ``reaction``.
    RestOperation(
        operation_id="reactions/create-for-release",
        method="POST",
        path="/repos/{owner}/{repo}/releases/{release_id}/reactions",
        query_params=frozenset(),
        body_params=frozenset({"content"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/reactions.md "Delete a release reaction": path parameters only; 204 on success.
    RestOperation(
        operation_id="reactions/delete-for-release",
        method="DELETE",
        path="/repos/{owner}/{repo}/releases/{release_id}/reactions/{reaction_id}",
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
