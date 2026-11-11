"""The ``ai-coding`` endpoint family of the GitLab wrapper: merge requests, their approvals, draft notes and context
commits, and Code Suggestions.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/ai-coding.md``
(issue #13, design.md D1 and D5): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query
or body attribute with the table's Type column as its ``Kind``. Part 1 declares the records the ``mr`` commands compose
(design.md D6): ``mr create``, ``mr get``, ``mr checks``, ``mr approve`` and ``mr merge``; ``commands/call.py`` refuses
the ``mr merge`` record and names that subcommand (``GATED_OPERATIONS``).

Issue #35 adds, after part 1's and in page order, one record for every other section of the page but one. A query
member row (``not[labels]``) is a query ``Param`` of its own; a body member row (``position[base_sha]``) is a key of
its parent's value, never a ``Param``. A record is ``Paging.OFFSET`` when it is a ``GET`` headed "List", has a ``page``
row, or is one of the four "Retrieve" lists GitLab pages (participants, reviewers, dependencies, blocked merge
requests); none is ``Paging.KEYSET``.

``PENDING`` holds the one key left, that of "Rebase a merge request" (issue #35, DL-002): it rewrites the merge
request's source branch, no subcommand sends it, and ``call`` refuses a declared id only by naming the subcommand that
does, so the id stays undeclared and ``call`` refuses it as unknown. No other family links that key.

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
    # "Code Suggestions API: Generate code completions".
    RestOperation(
        operation_id="ai-coding#generate-code-completions",
        method="POST",
        path="/code_suggestions/completions",
        params=(
            Param(name="current_file", location=Location.BODY, kind=Kind.HASH, required=True),
            Param(name="intent", location=Location.BODY),
            Param(name="stream", location=Location.BODY),
            Param(name="project_path", location=Location.BODY),
            Param(name="generation_type", location=Location.BODY),
            Param(name="context", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="user_instruction", location=Location.BODY),
        ),
    ),
    # "Code Suggestions API: Validate that Code Suggestions is enabled".
    RestOperation(
        operation_id="ai-coding#validate-that-code-suggestions-is-enabled",
        method="POST",
        path="/code_suggestions/enabled",
        params=(Param(name="project_path", location=Location.BODY, required=True),),
    ),
    # "Code Suggestions API: Fetch direct connection details for the AI Gateway".
    RestOperation(
        operation_id="ai-coding#fetch-direct-connection-details-for-the-ai-gateway",
        method="POST",
        path="/code_suggestions/direct_access",
    ),
    # "Code Suggestions API: Fetch connection details".
    RestOperation(
        operation_id="ai-coding#fetch-connection-details",
        method="POST",
        path="/code_suggestions/connection_details",
    ),
    # "Draft Notes API: List all merge request draft notes".
    RestOperation(
        operation_id="ai-coding#list-all-merge-request-draft-notes",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes",
        paging=Paging.OFFSET,
    ),
    # "Draft Notes API: Retrieve a draft note".
    RestOperation(
        operation_id="ai-coding#retrieve-a-draft-note",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
    ),
    # "Draft Notes API: Create a draft note"; the `position[...]` rows are keys of the `position` hash.
    RestOperation(
        operation_id="ai-coding#create-a-draft-note",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes",
        params=(
            Param(name="note", location=Location.BODY, required=True),
            Param(name="commit_id", location=Location.BODY),
            Param(name="in_reply_to_discussion_id", location=Location.BODY),
            Param(name="resolve_discussion", location=Location.BODY),
            Param(name="position", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Draft Notes API: Update a draft note"; the `position[...]` rows are keys of the `position` hash.
    RestOperation(
        operation_id="ai-coding#update-a-draft-note",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
        params=(
            Param(name="note", location=Location.BODY),
            Param(name="position", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Draft Notes API: Delete a draft note".
    RestOperation(
        operation_id="ai-coding#delete-a-draft-note",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
    ),
    # "Draft Notes API: Publish a draft note".
    RestOperation(
        operation_id="ai-coding#publish-a-draft-note",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id/publish",
    ),
    # "Draft Notes API: Publish all pending draft notes".
    RestOperation(
        operation_id="ai-coding#publish-all-pending-draft-notes",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/draft_notes/bulk_publish",
        params=(
            Param(name="note", location=Location.BODY),
            Param(name="internal", location=Location.BODY),
            Param(name="reviewer_state", location=Location.BODY),
        ),
    ),
    # "Merge request approvals API: Unapprove a merge request".
    RestOperation(
        operation_id="ai-coding#unapprove-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/unapprove",
    ),
    # "Merge request approvals API: Reset approvals for a merge request".
    RestOperation(
        operation_id="ai-coding#reset-approvals-for-a-merge-request",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/reset_approvals",
    ),
    # "Merge request approvals API: Retrieve approval configuration for a project".
    RestOperation(
        operation_id="ai-coding#retrieve-approval-configuration-for-a-project",
        method="GET",
        path="/projects/:id/approvals",
    ),
    # "Merge request approvals API: Update approval configuration for a project".
    RestOperation(
        operation_id="ai-coding#update-approval-configuration-for-a-project",
        method="POST",
        path="/projects/:id/approvals",
        params=(
            Param(name="approvals_before_merge", location=Location.BODY),
            Param(name="disable_overriding_approvers_per_merge_request", location=Location.BODY),
            Param(name="merge_requests_author_approval", location=Location.BODY),
            Param(name="merge_requests_disable_committers_approval", location=Location.BODY),
            Param(name="require_password_to_approve", location=Location.BODY),
            Param(name="require_reauthentication_to_approve", location=Location.BODY),
            Param(name="reset_approvals_on_push", location=Location.BODY),
            Param(name="selective_code_owner_removals", location=Location.BODY),
        ),
    ),
    # "Merge request approvals API: List all approval rules for a project".
    RestOperation(
        operation_id="ai-coding#list-all-approval-rules-for-a-project",
        method="GET",
        path="/projects/:id/approval_rules",
        paging=Paging.OFFSET,
    ),
    # "Merge request approvals API: Retrieve an approval rule for a project".
    RestOperation(
        operation_id="ai-coding#retrieve-an-approval-rule-for-a-project",
        method="GET",
        path="/projects/:id/approval_rules/:approval_rule_id",
    ),
    # "Merge request approvals API: Create an approval rule for a project".
    RestOperation(
        operation_id="ai-coding#create-an-approval-rule-for-a-project",
        method="POST",
        path="/projects/:id/approval_rules",
        params=(
            Param(name="approvals_required", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="applies_to_all_protected_branches", location=Location.BODY),
            Param(name="group_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="protected_branch_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="report_type", location=Location.BODY),
            Param(name="rule_type", location=Location.BODY),
            Param(name="user_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="usernames", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge request approvals API: Update an approval rule for a project".
    RestOperation(
        operation_id="ai-coding#update-an-approval-rule-for-a-project",
        method="PUT",
        path="/projects/:id/approval_rules/:approval_rule_id",
        params=(
            Param(name="applies_to_all_protected_branches", location=Location.BODY),
            Param(name="approvals_required", location=Location.BODY),
            Param(name="group_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="name", location=Location.BODY),
            Param(name="protected_branch_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="remove_hidden_groups", location=Location.BODY),
            Param(name="user_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="usernames", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge request approvals API: Delete an approval rule for a project".
    RestOperation(
        operation_id="ai-coding#delete-an-approval-rule-for-a-project",
        method="DELETE",
        path="/projects/:id/approval_rules/:approval_rule_id",
    ),
    # "Merge request approvals API: Retrieve approval state for a merge request".
    RestOperation(
        operation_id="ai-coding#retrieve-approval-state-for-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/approvals",
    ),
    # "Merge request approvals API: Retrieve approval details for a merge request".
    RestOperation(
        operation_id="ai-coding#retrieve-approval-details-for-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_state",
    ),
    # "Merge request approvals API: List all approval rules for a merge request".
    RestOperation(
        operation_id="ai-coding#list-all-approval-rules-for-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_rules",
        paging=Paging.OFFSET,
    ),
    # "Merge request approvals API: Retrieve an approval rule for a specific merge request".
    RestOperation(
        operation_id="ai-coding#retrieve-an-approval-rule-for-a-specific-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
    ),
    # "Merge request approvals API: Create an approval rule for a merge request".
    RestOperation(
        operation_id="ai-coding#create-an-approval-rule-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_rules",
        params=(
            Param(name="approvals_required", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="approval_project_rule_id", location=Location.BODY),
            Param(name="group_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="user_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="usernames", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge request approvals API: Update an approval rule for a merge request".
    RestOperation(
        operation_id="ai-coding#update-an-approval-rule-for-a-merge-request",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
        params=(
            Param(name="approvals_required", location=Location.BODY),
            Param(name="group_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="name", location=Location.BODY),
            Param(name="remove_hidden_groups", location=Location.BODY),
            Param(name="user_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="usernames", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge request approvals API: Delete an approval rule for a merge request".
    RestOperation(
        operation_id="ai-coding#delete-an-approval-rule-for-a-merge-request",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
    ),
    # "Merge request approvals API: List all approval rules for a group".
    RestOperation(
        operation_id="ai-coding#list-all-approval-rules-for-a-group",
        method="GET",
        path="/groups/:id/approval_rules",
        paging=Paging.OFFSET,
    ),
    # "Merge request approvals API: Create an approval rule for a group".
    RestOperation(
        operation_id="ai-coding#create-an-approval-rule-for-a-group",
        method="POST",
        path="/groups/:id/approval_rules",
        params=(
            Param(name="approvals_required", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="group_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="rule_type", location=Location.BODY),
            Param(name="user_ids", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Merge request context commits API: List context commits for a merge request".
    RestOperation(
        operation_id="ai-coding#list-context-commits-for-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/context_commits",
        paging=Paging.OFFSET,
    ),
    # "Merge request context commits API: Create context commits for a merge request".
    RestOperation(
        operation_id="ai-coding#create-context-commits-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/context_commits",
        params=(Param(name="commits", location=Location.BODY, kind=Kind.ARRAY, required=True),),
    ),
    # "Merge request context commits API: Delete context commits from a merge request".
    RestOperation(
        operation_id="ai-coding#delete-context-commits-from-a-merge-request",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/context_commits",
        params=(Param(name="commits", location=Location.QUERY, kind=Kind.ARRAY, required=True),),
    ),
    # "Merge requests API: List merge requests"; each `not[...]` row is a query Param of its own.
    RestOperation(
        operation_id="ai-coding#list-merge-requests",
        method="GET",
        path="/merge_requests",
        params=(
            Param(name="approved_by_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approved_by_usernames", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approver_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="deployed_after", location=Location.QUERY),
            Param(name="deployed_before", location=Location.QUERY),
            Param(name="merged_after", location=Location.QUERY),
            Param(name="merged_before", location=Location.QUERY),
            Param(name="environment", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="merge_user_id", location=Location.QUERY),
            Param(name="merge_user_username", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="non_archived", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="reviewer_id", location=Location.QUERY),
            Param(name="reviewer_username", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="view", location=Location.QUERY),
            Param(name="draft", location=Location.QUERY),
            Param(name="wip", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="with_merge_status_recheck", location=Location.QUERY),
            Param(name="source_project_id", location=Location.QUERY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[reviewer_username]", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[my_reaction_emoji]", location=Location.QUERY),
            Param(name="not[reviewer_id]", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: List project merge requests"; each `not[...]` row is a query Param of its own.
    RestOperation(
        operation_id="ai-coding#list-project-merge-requests",
        method="GET",
        path="/projects/:id/merge_requests",
        params=(
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approved_by_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approved_by_usernames", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approver_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="deployed_after", location=Location.QUERY),
            Param(name="deployed_before", location=Location.QUERY),
            Param(name="merged_after", location=Location.QUERY),
            Param(name="merged_before", location=Location.QUERY),
            Param(name="environment", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="merge_user_id", location=Location.QUERY),
            Param(name="merge_user_username", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="reviewer_id", location=Location.QUERY),
            Param(name="reviewer_username", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="view", location=Location.QUERY),
            Param(name="draft", location=Location.QUERY),
            Param(name="wip", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="with_merge_status_recheck", location=Location.QUERY),
            Param(name="source_project_id", location=Location.QUERY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[reviewer_username]", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[my_reaction_emoji]", location=Location.QUERY),
            Param(name="not[reviewer_id]", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: List group merge requests"; each `not[...]` row is a query Param of its own.
    RestOperation(
        operation_id="ai-coding#list-group-merge-requests",
        method="GET",
        path="/groups/:id/merge_requests",
        params=(
            Param(name="approved_by_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approved_by_usernames", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="approver_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="deployed_after", location=Location.QUERY),
            Param(name="deployed_before", location=Location.QUERY),
            Param(name="merged_after", location=Location.QUERY),
            Param(name="merged_before", location=Location.QUERY),
            Param(name="environment", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="merge_user_id", location=Location.QUERY),
            Param(name="merge_user_username", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="non_archived", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="reviewer_id", location=Location.QUERY),
            Param(name="reviewer_username", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="source_project_id", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="view", location=Location.QUERY),
            Param(name="draft", location=Location.QUERY),
            Param(name="wip", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="with_merge_status_recheck", location=Location.QUERY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[reviewer_username]", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[my_reaction_emoji]", location=Location.QUERY),
            Param(name="not[reviewer_id]", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve merge request participants": a list GitLab pages, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-participants",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/participants",
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve merge request reviewers": a list GitLab pages, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-reviewers",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/reviewers",
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve merge request commits"; its table has a `page` row, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-commits",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/commits",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve merge request dependencies": a list GitLab pages, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-dependencies",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/blocks",
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Delete a merge request dependency".
    RestOperation(
        operation_id="ai-coding#delete-a-merge-request-dependency",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/blocks/:block_id",
    ),
    # "Merge requests API: Create a merge request dependency"; the two `conditional` rows are not `required`.
    RestOperation(
        operation_id="ai-coding#create-a-merge-request-dependency",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/blocks",
        params=(
            Param(name="blocking_merge_request_id", location=Location.BODY),
            Param(name="blocking_merge_request_iid", location=Location.BODY),
            Param(name="blocking_project_id", location=Location.BODY),
        ),
    ),
    # "Merge requests API: Retrieve blocked merge requests": a list GitLab pages, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-blocked-merge-requests",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/blockees",
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve merge request changes".
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-changes",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/changes",
        params=(
            Param(name="access_raw_diffs", location=Location.QUERY),
            Param(name="unidiff", location=Location.QUERY),
        ),
    ),
    # "Merge requests API: List merge request diffs".
    RestOperation(
        operation_id="ai-coding#list-merge-request-diffs",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/diffs",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="unidiff", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Show merge request raw diffs".
    RestOperation(
        operation_id="ai-coding#show-merge-request-raw-diffs",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/raw_diffs",
    ),
    # "Merge requests API: Create merge request pipeline".
    RestOperation(
        operation_id="ai-coding#create-merge-request-pipeline",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/pipelines",
        params=(Param(name="async", location=Location.BODY),),
    ),
    # "Merge requests API: Update a merge request"; here `add_labels` and `remove_labels` are strings.
    RestOperation(
        operation_id="ai-coding#update-a-merge-request",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid",
        params=(
            Param(name="add_labels", location=Location.BODY),
            Param(name="allow_collaboration", location=Location.BODY),
            Param(name="allow_maintainer_to_push", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="assignee_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="discussion_locked", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="merge_after", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="milestone", location=Location.BODY),
            Param(name="remove_labels", location=Location.BODY),
            Param(name="remove_source_branch", location=Location.BODY),
            Param(name="reviewer_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="squash", location=Location.BODY),
            Param(name="state_event", location=Location.BODY),
            Param(name="target_branch", location=Location.BODY),
            Param(name="title", location=Location.BODY),
            Param(name="approvals_before_merge", location=Location.BODY),
        ),
    ),
    # "Merge requests API: Delete a merge request".
    RestOperation(
        operation_id="ai-coding#delete-a-merge-request",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid",
    ),
    # "Merge requests API: Merge to default merge ref path".
    RestOperation(
        operation_id="ai-coding#merge-to-default-merge-ref-path",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/merge_ref",
    ),
    # "Merge requests API: Cancel merge when pipeline succeeds (deprecated)".
    RestOperation(
        operation_id="ai-coding#cancel-merge-when-pipeline-succeeds-deprecated",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/cancel_merge_when_pipeline_succeeds",
    ),
    # "Merge requests API: Cancel auto merge".
    RestOperation(
        operation_id="ai-coding#cancel-auto-merge",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/cancel_auto_merge",
    ),
    # "Merge requests API: List issues that close on merge".
    RestOperation(
        operation_id="ai-coding#list-issues-that-close-on-merge",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/closes_issues",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: List issues related to the merge request".
    RestOperation(
        operation_id="ai-coding#list-issues-related-to-the-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/related_issues",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Subscribe to a merge request".
    RestOperation(
        operation_id="ai-coding#subscribe-to-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/subscribe",
    ),
    # "Merge requests API: Unsubscribe from a merge request".
    RestOperation(
        operation_id="ai-coding#unsubscribe-from-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/unsubscribe",
    ),
    # "Merge requests API: Create a to-do item".
    RestOperation(
        operation_id="ai-coding#create-a-to-do-item",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/todo",
    ),
    # "Merge requests API: Retrieve merge request diff versions"; its table has a `page` row, so offset-paged.
    RestOperation(
        operation_id="ai-coding#retrieve-merge-request-diff-versions",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/versions",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge requests API: Retrieve a merge request diff version".
    RestOperation(
        operation_id="ai-coding#retrieve-a-merge-request-diff-version",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/versions/:version_id",
        params=(Param(name="unidiff", location=Location.QUERY),),
    ),
    # "Merge requests API: Set a time estimate for a merge request".
    RestOperation(
        operation_id="ai-coding#set-a-time-estimate-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/time_estimate",
        params=(Param(name="duration", location=Location.BODY, required=True),),
    ),
    # "Merge requests API: Reset the time estimate for a merge request".
    RestOperation(
        operation_id="ai-coding#reset-the-time-estimate-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/reset_time_estimate",
    ),
    # "Merge requests API: Add spent time for a merge request".
    RestOperation(
        operation_id="ai-coding#add-spent-time-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/add_spent_time",
        params=(
            Param(name="duration", location=Location.BODY, required=True),
            Param(name="summary", location=Location.BODY),
        ),
    ),
    # "Merge requests API: Reset spent time for a merge request".
    RestOperation(
        operation_id="ai-coding#reset-spent-time-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/reset_spent_time",
    ),
    # "Merge requests API: Retrieve time tracking statistics".
    RestOperation(
        operation_id="ai-coding#retrieve-time-tracking-statistics",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/time_stats",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        # "Merge requests API: Rebase a merge request": it rewrites the source branch and no subcommand gates it.
        ("PUT", "/projects/:id/merge_requests/:merge_request_iid/rebase"),
    }
)
