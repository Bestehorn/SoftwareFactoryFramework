"""The ``pulls`` family of the GitHub operations index: pull requests, their review comments, reviews and requested
reviewers.

Each record is the section of ``docs/api-reference/github/rest/pulls.md`` its operation ID names, a ``pulls/`` ID (the
file's ``agent-merge/`` and ``pull-request-stacks/`` sections are other families): its method and path, the names of
its ``query`` rows, and the first-level fields of its request body. ``comments[].path`` and its siblings are fields of
each ``comments`` item, and the ``(body)`` row of a reviewer request is a constraint that names no field. No path
parameter spans segments. A list record whose section has a ``Paging:`` line pages by ``link``: its ``200`` is a bare
array with a ``Link`` header, so it has no item key. ``pulls/list-requested-reviewers`` answers one object, so it sends
one request, as every other record does. Every record asks for ``application/json`` with the default API version, also
where its section names another media type (``conventions.md`` "Headers, media types and API versions").

``create-pr``, ``get-pr``, ``approve-pr`` and ``merge-pr`` send ``pulls/create``, ``pulls/get``, ``pulls/create-review``
and ``pulls/merge``; ``get-pr-checks`` reads the head SHA with ``pulls/get`` (design D5). Every record is also sent by
``call <operation-id>`` (#28), which refuses ``pulls/merge`` and ``pulls/merge-async`` (#32 DL-003): both merge, and
``merge-pr`` is the subcommand that does. ``pulls/update-branch``, which writes the pull request's head branch, is the
one pending ID (#32 DL-002).
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "pulls"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/pulls.md "Create a pull request": sent by ``create-pr``; 201 with a ``pull-request``.
    RestOperation(
        operation_id="pulls/create",
        method="POST",
        path="/repos/{owner}/{repo}/pulls",
        query_params=frozenset(),
        body_params=frozenset(
            {"title", "head", "head_repo", "base", "body", "maintainer_can_modify", "draft", "issue"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get a pull request": sent by ``get-pr`` and ``get-pr-checks``; 200 with a ``pull-request``.
    RestOperation(
        operation_id="pulls/get",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Create a review for a pull request": sent by ``approve-pr``; 200 with a ``pull-request-review``.
    RestOperation(
        operation_id="pulls/create-review",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        query_params=frozenset(),
        body_params=frozenset({"commit_id", "body", "event", "comments"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Merge a pull request": sent by ``merge-pr``, refused by ``call``; 200 with the merge result.
    RestOperation(
        operation_id="pulls/merge",
        method="PUT",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/merge",
        query_params=frozenset(),
        body_params=frozenset({"commit_title", "commit_message", "sha", "merge_method"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List review comments in a repository": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-review-comments-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/comments",
        query_params=frozenset({"sort", "direction", "since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get a review comment for a pull request": path parameters only; 200 with the review comment.
    RestOperation(
        operation_id="pulls/get-review-comment",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Update a review comment for a pull request": body ``body``; 200 with the review comment.
    RestOperation(
        operation_id="pulls/update-review-comment",
        method="PATCH",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Delete a review comment for a pull request": path parameters only, no query, no body; 204.
    RestOperation(
        operation_id="pulls/delete-review-comment",
        method="DELETE",
        path="/repos/{owner}/{repo}/pulls/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List review comments on a pull request": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-review-comments",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/comments",
        query_params=frozenset({"sort", "direction", "since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Create a review comment for a pull request": the first-level body fields; 201 with the comment.
    RestOperation(
        operation_id="pulls/create-review-comment",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/comments",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "body",
                "commit_id",
                "path",
                "position",
                "side",
                "line",
                "start_line",
                "start_side",
                "in_reply_to",
                "subject_type",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Create a reply for a review comment": body ``body``; 201 with the reply.
    RestOperation(
        operation_id="pulls/create-reply-for-review-comment",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Request a Copilot code review for a pull request": optional body ``review_effort``; 201.
    RestOperation(
        operation_id="pulls/request-copilot-code-review",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/copilot-code-review",
        query_params=frozenset(),
        body_params=frozenset({"review_effort"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List pull requests": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list",
        method="GET",
        path="/repos/{owner}/{repo}/pulls",
        query_params=frozenset({"state", "head", "base", "sort", "direction", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Update a pull request": the first-level body fields; 200 with the ``pull-request``.
    RestOperation(
        operation_id="pulls/update",
        method="PATCH",
        path="/repos/{owner}/{repo}/pulls/{pull_number}",
        query_params=frozenset(),
        body_params=frozenset({"title", "body", "state", "base", "maintainer_can_modify"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List commits on a pull request": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-commits",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/commits",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List pull requests files": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-files",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/files",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Check if a pull request has been merged": path parameters only; 204 when merged, else 404.
    RestOperation(
        operation_id="pulls/check-if-merged",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/merge",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Merge a pull request asynchronously": its body can bypass rules; refused by ``call`` (DL-003).
    RestOperation(
        operation_id="pulls/merge-async",
        method="PUT",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/merge-async",
        query_params=frozenset(),
        body_params=frozenset(
            {"commit_title", "commit_message", "sha", "merge_method", "merge_action", "bypass_rules"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get the result of an asynchronous merge": path parameters only; 200 with the merge result.
    RestOperation(
        operation_id="pulls/get-merge-async-result",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/merge-async/{uuid}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get all requested reviewers for a pull request": one object and no ``Paging:`` line; one request.
    RestOperation(
        operation_id="pulls/list-requested-reviewers",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Request reviewers for a pull request": body ``reviewers`` and ``team_reviewers``; 201.
    RestOperation(
        operation_id="pulls/request-reviewers",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers",
        query_params=frozenset(),
        body_params=frozenset({"reviewers", "team_reviewers"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Remove requested reviewers from a pull request": body ``reviewers`` and ``team_reviewers``.
    RestOperation(
        operation_id="pulls/remove-requested-reviewers",
        method="DELETE",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers",
        query_params=frozenset(),
        body_params=frozenset({"reviewers", "team_reviewers"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Rerequest reviewers for a pull request": body ``reviewers`` and ``team_reviewers``; 201.
    RestOperation(
        operation_id="pulls/rerequest-reviewers",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers/rerequest",
        query_params=frozenset(),
        body_params=frozenset({"reviewers", "team_reviewers"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List reviews for a pull request": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-reviews",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Get a review for a pull request": path parameters only; 200 with a ``pull-request-review``.
    RestOperation(
        operation_id="pulls/get-review",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Update a review for a pull request": body ``body``; 200 with the review.
    RestOperation(
        operation_id="pulls/update-review",
        method="PUT",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Delete a pending review for a pull request": path parameters only; 200 with the deleted review.
    RestOperation(
        operation_id="pulls/delete-pending-review",
        method="DELETE",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "List comments for a pull request review": a bare array with a ``Link`` header; pages by ``link``.
    RestOperation(
        operation_id="pulls/list-comments-for-review",
        method="GET",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Dismiss a review for a pull request": body ``message`` and ``event``; 200 with the review.
    RestOperation(
        operation_id="pulls/dismiss-review",
        method="PUT",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/dismissals",
        query_params=frozenset(),
        body_params=frozenset({"message", "event"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/pulls.md "Submit a review for a pull request": body ``body`` and ``event``; 200 with the review.
    RestOperation(
        operation_id="pulls/submit-review",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events",
        query_params=frozenset(),
        body_params=frozenset({"body", "event"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset({"pulls/update-branch"})
