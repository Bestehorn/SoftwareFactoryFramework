"""The ``issues`` family of the GitHub operations index: the records the issues and claim commands send (design D5).

Each record is the index row of its operation ID (method and path), the query and body parameter names the section
of ``rest/issues.md`` that row links documents, and its paging kind (D4); both list operations return a bare array,
so neither has an item key (``conventions.md`` "Lists wrapped in an object"). The commands that send them, by D5's
table:

- ``list-issues``: ``issues/list-for-repo``, followed by ``link``;
- ``get-issue``, ``get-issue-comments``: ``issues/get``; ``issues/list-comments``, every page by ``link``;
- ``comment-issue``, ``create-issue``, ``update-issue``: ``issues/create-comment``, ``issues/create``,
  ``issues/update``;
- ``reopen-issue``, ``checklist``: ``issues/get``, ``issues/update``;
- the claim commands, with ``users/get-authenticated``: ``start-issue`` (``issues/get``, ``issues/add-labels``,
  ``issues/add-assignees``), ``release-issue`` (``issues/get``, ``issues/update``, ``issues/remove-assignees``),
  ``claim-check`` (``issues/get``), and ``label-add``, ``label-remove``, ``assign`` (``issues/add-labels``,
  ``issues/remove-label``, ``issues/get``, ``issues/add-assignees``, ``issues/remove-assignees``).

Every other operation ID of the family is on ``PENDING`` until a record covers it (part 2, #14).
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "issues"

OPERATIONS: Tuple[RestOperation, ...] = (
    RestOperation(
        operation_id="issues/list-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/issues",
        query_params=frozenset(
            {
                "milestone",
                "state",
                "assignee",
                "type",
                "creator",
                "mentioned",
                "issue_field_values",
                "labels",
                "sort",
                "direction",
                "since",
                "per_page",
                "page",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/get",
        method="GET",
        path="/repos/{owner}/{repo}/issues/{issue_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/list-comments",
        method="GET",
        path="/repos/{owner}/{repo}/issues/{issue_number}/comments",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/create",
        method="POST",
        path="/repos/{owner}/{repo}/issues",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "title",
                "body",
                "assignee",
                "milestone",
                "labels",
                "assignees",
                "issue_field_values",
                "type",
                "parent_issue_id",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/update",
        method="PATCH",
        path="/repos/{owner}/{repo}/issues/{issue_number}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "title",
                "body",
                "assignee",
                "state",
                "state_reason",
                "duplicate_issue_id",
                "milestone",
                "labels",
                "assignees",
                "issue_field_values",
                "type",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/create-comment",
        method="POST",
        path="/repos/{owner}/{repo}/issues/{issue_number}/comments",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/add-labels",
        method="POST",
        path="/repos/{owner}/{repo}/issues/{issue_number}/labels",
        query_params=frozenset(),
        body_params=frozenset({"labels"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/remove-label",
        method="DELETE",
        path="/repos/{owner}/{repo}/issues/{issue_number}/labels/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/add-assignees",
        method="POST",
        path="/repos/{owner}/{repo}/issues/{issue_number}/assignees",
        query_params=frozenset(),
        body_params=frozenset({"assignees"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    RestOperation(
        operation_id="issues/remove-assignees",
        method="DELETE",
        path="/repos/{owner}/{repo}/issues/{issue_number}/assignees",
        query_params=frozenset(),
        body_params=frozenset({"assignees"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset(
    {
        "issues/add-blocked-by-dependency",
        "issues/add-issue-field-values",
        "issues/add-relates-to",
        "issues/add-sub-issue",
        "issues/approve-suggestion",
        "issues/check-user-can-be-assigned",
        "issues/check-user-can-be-assigned-to-issue",
        "issues/create-issue-artifact",
        "issues/create-label",
        "issues/create-milestone",
        "issues/delete-comment",
        "issues/delete-issue-artifact",
        "issues/delete-issue-field-value",
        "issues/delete-label",
        "issues/delete-milestone",
        "issues/dismiss-suggestion",
        "issues/get-comment",
        "issues/get-event",
        "issues/get-issue-artifact",
        "issues/get-label",
        "issues/get-milestone",
        "issues/get-parent",
        "issues/list",
        "issues/list-assignees",
        "issues/list-comments-for-repo",
        "issues/list-dependencies-blocked-by",
        "issues/list-dependencies-blocking",
        "issues/list-events",
        "issues/list-events-for-repo",
        "issues/list-events-for-timeline",
        "issues/list-for-authenticated-user",
        "issues/list-for-org",
        "issues/list-issue-artifacts",
        "issues/list-issue-field-values-for-issue",
        "issues/list-labels-for-milestone",
        "issues/list-labels-for-repo",
        "issues/list-labels-on-issue",
        "issues/list-milestones",
        "issues/list-relates-to",
        "issues/list-sub-issues",
        "issues/list-suggestions",
        "issues/lock",
        "issues/pin-comment",
        "issues/remove-all-labels",
        "issues/remove-dependency-blocked-by",
        "issues/remove-relates-to",
        "issues/remove-sub-issue",
        "issues/reprioritize-sub-issue",
        "issues/set-issue-field-values",
        "issues/set-labels",
        "issues/unlock",
        "issues/unpin-comment",
        "issues/update-comment",
        "issues/update-issue-artifact",
        "issues/update-label",
        "issues/update-milestone",
    }
)
