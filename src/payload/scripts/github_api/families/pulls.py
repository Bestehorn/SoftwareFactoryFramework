"""The ``pulls`` family of the GitHub operations index: the records the ``pulls`` compatibility commands send.

``create-pr``, ``get-pr``, ``approve-pr`` and ``merge-pr`` send ``pulls/create``, ``pulls/get``, ``pulls/create-review``
and ``pulls/merge``; ``get-pr-checks`` reads the head SHA with ``pulls/get`` (design D5). Each record is its row of
``docs/api-reference/github/operations-index.md`` with the query and body names of the ``rest/pulls.md`` section that
row links; none of them pages. A body name is the top-level field only: ``comments[].path`` and its siblings are
fields of each ``comments`` item. Every other operation ID of the family is on ``PENDING`` (design D2).
"""

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "pulls"

OPERATIONS = (
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
)

PENDING = frozenset(
    {
        "pulls/check-if-merged",
        "pulls/create-reply-for-review-comment",
        "pulls/create-review-comment",
        "pulls/delete-pending-review",
        "pulls/delete-review-comment",
        "pulls/dismiss-review",
        "pulls/get-merge-async-result",
        "pulls/get-review",
        "pulls/get-review-comment",
        "pulls/list",
        "pulls/list-comments-for-review",
        "pulls/list-commits",
        "pulls/list-files",
        "pulls/list-requested-reviewers",
        "pulls/list-review-comments",
        "pulls/list-review-comments-for-repo",
        "pulls/list-reviews",
        "pulls/merge-async",
        "pulls/remove-requested-reviewers",
        "pulls/request-copilot-code-review",
        "pulls/request-reviewers",
        "pulls/rerequest-reviewers",
        "pulls/submit-review",
        "pulls/update",
        "pulls/update-branch",
        "pulls/update-review",
        "pulls/update-review-comment",
    }
)
