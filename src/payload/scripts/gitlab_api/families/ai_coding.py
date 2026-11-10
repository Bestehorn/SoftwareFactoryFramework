"""The ``ai-coding`` endpoint family of the GitLab wrapper: merge requests, their approvals, and Code Suggestions.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/ai-coding.md``
(issue #13, design.md D1 and D5): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query
or body attribute with the table's Type column as its ``Kind``. Part 1 declares the records the ``mr`` commands compose
(design.md D6): ``mr create``, ``mr get``, ``mr checks``, ``mr approve`` and ``mr merge``. ``PENDING`` holds the
``(method, path)`` key of every other index row of this family; no other family links any of them.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "ai-coding"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Merge requests API: Create a merge request".
    RestOperation(
        operation_id="ai-coding#create-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests",
        params=(
            Param(name="source_branch", location=Location.BODY, required=True),
            Param(name="target_branch", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="allow_collaboration", location=Location.BODY),
            Param(name="approvals_before_merge", location=Location.BODY),
            Param(name="allow_maintainer_to_push", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="assignee_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="merge_after", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="milestone", location=Location.BODY),
            Param(name="remove_source_branch", location=Location.BODY),
            Param(name="reviewer_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="squash", location=Location.BODY),
            Param(name="target_project_id", location=Location.BODY),
            Param(name="add_labels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="remove_labels", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge requests API: Retrieve a merge request".
    RestOperation(
        operation_id="ai-coding#retrieve-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid",
        params=(
            Param(name="include_diverged_commits_count", location=Location.QUERY),
            Param(name="include_rebase_in_progress", location=Location.QUERY),
            Param(name="render_html", location=Location.QUERY),
        ),
    ),
    # "Merge request approvals API: Approve merge request".
    RestOperation(
        operation_id="ai-coding#approve-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/approve",
        params=(
            Param(name="approval_password", location=Location.BODY),
            Param(name="sha", location=Location.BODY),
            Param(name="publish_review", location=Location.BODY),
        ),
    ),
    # "Merge requests API: Merge a merge request"; `sha` is only conditionally required, so not `required`.
    RestOperation(
        operation_id="ai-coding#merge-a-merge-request",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/merge",
        params=(
            Param(name="auto_merge", location=Location.BODY),
            Param(name="merge_commit_message", location=Location.BODY),
            Param(name="merge_when_pipeline_succeeds", location=Location.BODY),
            Param(name="sha", location=Location.BODY),
            Param(name="should_remove_source_branch", location=Location.BODY),
            Param(name="squash_commit_message", location=Location.BODY),
            Param(name="squash", location=Location.BODY),
            Param(name="skip_merge_train", location=Location.BODY),
        ),
    ),
    # "Merge requests API: List merge request pipelines": a list endpoint, so offset-paged (conventions.md
    # "Pagination": offset pagination works on every list endpoint except where a page says otherwise).
    RestOperation(
        operation_id="ai-coding#list-merge-request-pipelines",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/pipelines",
        paging=Paging.OFFSET,
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/code_suggestions/completions"),
        ("POST", "/code_suggestions/connection_details"),
        ("POST", "/code_suggestions/direct_access"),
        ("POST", "/code_suggestions/enabled"),
        ("GET", "/groups/:id/approval_rules"),
        ("POST", "/groups/:id/approval_rules"),
        ("GET", "/groups/:id/merge_requests"),
        ("GET", "/merge_requests"),
        ("GET", "/projects/:id/approval_rules"),
        ("POST", "/projects/:id/approval_rules"),
        ("DELETE", "/projects/:id/approval_rules/:approval_rule_id"),
        ("GET", "/projects/:id/approval_rules/:approval_rule_id"),
        ("PUT", "/projects/:id/approval_rules/:approval_rule_id"),
        ("GET", "/projects/:id/approvals"),
        ("POST", "/projects/:id/approvals"),
        ("GET", "/projects/:id/merge_requests"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/add_spent_time"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/approval_rules"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/approval_rules"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/approval_state"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/approvals"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/blockees"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/blocks"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/blocks"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/blocks/:block_id"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/cancel_auto_merge"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/cancel_merge_when_pipeline_succeeds"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/changes"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/closes_issues"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/commits"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/context_commits"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/context_commits"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/context_commits"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/diffs"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/draft_notes"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/draft_notes"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id/publish"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/draft_notes/bulk_publish"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/merge_ref"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/participants"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/pipelines"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/raw_diffs"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/rebase"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/related_issues"),
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/reset_approvals"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/reset_spent_time"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/reset_time_estimate"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/reviewers"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/subscribe"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/time_estimate"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/time_stats"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/todo"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/unapprove"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/unsubscribe"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/versions"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/versions/:version_id"),
    }
)
