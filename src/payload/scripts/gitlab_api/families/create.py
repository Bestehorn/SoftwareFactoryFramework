"""The ``create`` endpoint family of the GitLab wrapper: repositories, branches, commits, files, tags, snippets, mirrors
and discussions.

Each record is transcribed from its section of ``docs/api-reference/gitlab/rest/create.md`` (issue #13, design.md D1
and D5; issue #35): the method and the path as ``operations-index.md`` writes them, and one ``Param`` per query or body
row of the section's attribute table, the rows marked "in OpenAPI only" included. A body row that is part of another
(``position[base_sha]``, ``files:content``) is no ``Param``; a query row that is part of another (``range[start]``) is
a ``Param`` of its own as well. The Type column gives the ``Kind``: ``ARRAY_OF_HASHES`` for ``array of hashes`` and for
the ``files`` of "Retrieve multiple blobs in a single request", ``ARRAY`` for any other array, ``HASH`` for ``hash``,
``SCALAR`` for every other; ``required`` is set where Required reads ``yes``. Every record sends a JSON body and fixes
no query value. A ``GET`` section headed "List", or whose table has a ``page`` row, pages by offset (``conventions.md``
"Pagination"); none is keyset-only. ``GET /keys`` has two records, one per Reference; "Retrieve raw blob content"
answers with the blob's bytes, which ``call`` writes unchanged. Part 1's record is the one the ``delete-branch`` command
sends (design.md D6), whose branch name ``registry.expand`` writes as one encoded segment.

Three sections take a request form of issue #63 (its design.md D1 to D3, D8):

- a section with several endpoints has one record per endpoint, each with its Reference's ID: the base record on the
  first endpoint, then one per other endpoint in the order the section's endpoint line lists them, each a copy of the
  base record but for its method, its path and any ``Param`` naming a path parameter of its own path; "Generate
  changelog data" has two, ``changelog`` and then ``changelog.txt``, which ``call --endpoint`` names;
- "Delete a group SSH certificate" holds ``:id`` twice, the group's and then the certificate's: its
  ``positional_names`` is ``("id",)``, so each place takes its own ``--path id=`` value, in command-line order;
- "Retrieve file archive from a repository" ends in ``archive[.format]``: its ``suffix_values`` are the formats
  docs.gitlab.com ``repositories`` "Available options" lists, one given as ``--path format=``; without it the path ends
  at ``archive``.

``PENDING`` holds the ``(method, path)`` keys no record maps: those of the twelve IDs that commit to, create or rewrite
a branch (creating a branch, a commit, a cherry-pick or a revert; adding changelog data; creating, updating or deleting
a file; updating a submodule; applying one suggestion or several; starting a pull mirror), kept for issue #35's reason:
``call`` would send them ungated, since ``GATED_OPERATIONS`` refuses an ID only by naming the subcommand that sends it,
and no subcommand sends these. No other family links any of them.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "create"

OPERATIONS: Tuple[RestOperation, ...] = (
    # ".gitignore API: List all `.gitignore` templates".
    RestOperation(
        operation_id="create#list-all-gitignore-templates",
        method="GET",
        path="/templates/gitignores",
        paging=Paging.OFFSET,
    ),
    # ".gitignore API: Retrieve a single `.gitignore` template".
    RestOperation(
        operation_id="create#retrieve-a-single-gitignore-template",
        method="GET",
        path="/templates/gitignores/:key",
    ),
    # "Branches API: List all repository branches".
    RestOperation(
        operation_id="create#list-all-repository-branches",
        method="GET",
        path="/projects/:id/repository/branches",
        params=(
            Param(name="regex", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page_token", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Branches API: Retrieve a repository branch".
    RestOperation(
        operation_id="create#retrieve-a-repository-branch",
        method="GET",
        path="/projects/:id/repository/branches/:branch",
    ),
    # "Branches API: Delete repository branch": `id` and `branch` are path attributes, so the record has no Param.
    RestOperation(
        operation_id="create#delete-repository-branch",
        method="DELETE",
        path="/projects/:id/repository/branches/:branch",
    ),
    # "Branches API: Delete all merged branches".
    RestOperation(
        operation_id="create#delete-all-merged-branches",
        method="DELETE",
        path="/projects/:id/repository/merged_branches",
    ),
    # "Commits API: List repository commits".
    RestOperation(
        operation_id="create#list-repository-commits",
        method="GET",
        path="/projects/:id/repository/commits",
        params=(
            Param(name="all", location=Location.QUERY),
            Param(name="author", location=Location.QUERY),
            Param(name="first_parent", location=Location.QUERY),
            Param(name="follow", location=Location.QUERY),
            Param(name="order", location=Location.QUERY),
            Param(name="path", location=Location.QUERY),
            Param(name="ref_name", location=Location.QUERY),
            Param(name="since", location=Location.QUERY),
            Param(name="trailers", location=Location.QUERY),
            Param(name="until", location=Location.QUERY),
            Param(name="with_stats", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="pagination", location=Location.QUERY),
            Param(name="page_token", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: Retrieve a commit".
    RestOperation(
        operation_id="create#retrieve-a-commit",
        method="GET",
        path="/projects/:id/repository/commits/:sha",
        params=(Param(name="stats", location=Location.QUERY),),
    ),
    # "Commits API: List all references a commit is pushed to".
    RestOperation(
        operation_id="create#list-all-references-a-commit-is-pushed-to",
        method="GET",
        path="/projects/:id/repository/commits/:sha/refs",
        params=(
            Param(name="type", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: Get commit sequence".
    RestOperation(
        operation_id="create#get-commit-sequence",
        method="GET",
        path="/projects/:id/repository/commits/:sha/sequence",
        params=(Param(name="first_parent", location=Location.QUERY),),
    ),
    # "Commits API: Retrieve commit diff".
    RestOperation(
        operation_id="create#retrieve-commit-diff",
        method="GET",
        path="/projects/:id/repository/commits/:sha/diff",
        params=(
            Param(name="unidiff", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: List all commit comments".
    RestOperation(
        operation_id="create#list-all-commit-comments",
        method="GET",
        path="/projects/:id/repository/commits/:sha/comments",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: Post comment to commit".
    RestOperation(
        operation_id="create#post-comment-to-commit",
        method="POST",
        path="/projects/:id/repository/commits/:sha/comments",
        params=(
            Param(name="note", location=Location.BODY, required=True),
            Param(name="line", location=Location.BODY),
            Param(name="line_type", location=Location.BODY),
            Param(name="path", location=Location.BODY),
        ),
    ),
    # "Commits API: List all commit discussions".
    RestOperation(
        operation_id="create#list-all-commit-discussions",
        method="GET",
        path="/projects/:id/repository/commits/:sha/discussions",
        paging=Paging.OFFSET,
    ),
    # "Commits API: List commit statuses".
    RestOperation(
        operation_id="create#list-commit-statuses",
        method="GET",
        path="/projects/:id/repository/commits/:sha/statuses",
        params=(
            Param(name="all", location=Location.QUERY),
            Param(name="name", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="pipeline_id", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="stage", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: Set commit pipeline status".
    RestOperation(
        operation_id="create#set-commit-pipeline-status",
        method="POST",
        path="/projects/:id/statuses/:sha",
        params=(
            Param(name="state", location=Location.BODY, required=True),
            Param(name="coverage", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="pipeline_id", location=Location.BODY),
            Param(name="ref", location=Location.BODY),
            Param(name="target_url", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="context", location=Location.BODY),
        ),
    ),
    # "Commits API: List merge requests associated with a commit".
    RestOperation(
        operation_id="create#list-merge-requests-associated-with-a-commit",
        method="GET",
        path="/projects/:id/repository/commits/:sha/merge_requests",
        params=(
            Param(name="state", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Commits API: Retrieve commit signature".
    RestOperation(
        operation_id="create#retrieve-commit-signature",
        method="GET",
        path="/projects/:id/repository/commits/:sha/signature",
    ),
    # "Discussions API: List all issue discussion items".
    RestOperation(
        operation_id="create#list-all-issue-discussion-items",
        method="GET",
        path="/projects/:id/issues/:issue_iid/discussions",
        paging=Paging.OFFSET,
    ),
    # "Discussions API: Retrieve an issue discussion item".
    RestOperation(
        operation_id="create#retrieve-an-issue-discussion-item",
        method="GET",
        path="/projects/:id/issues/:issue_iid/discussions/:discussion_id",
    ),
    # "Discussions API: Create an issue thread".
    RestOperation(
        operation_id="create#create-an-issue-thread",
        method="POST",
        path="/projects/:id/issues/:issue_iid/discussions",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Add a note to an issue thread".
    RestOperation(
        operation_id="create#add-a-note-to-an-issue-thread",
        method="POST",
        path="/projects/:id/issues/:issue_iid/discussions/:discussion_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Update an issue thread note".
    RestOperation(
        operation_id="create#update-an-issue-thread-note",
        method="PUT",
        path="/projects/:id/issues/:issue_iid/discussions/:discussion_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Discussions API: Delete an issue thread note".
    RestOperation(
        operation_id="create#delete-an-issue-thread-note",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/discussions/:discussion_id/notes/:note_id",
    ),
    # "Discussions API: List all snippet discussion items".
    RestOperation(
        operation_id="create#list-all-snippet-discussion-items",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/discussions",
        paging=Paging.OFFSET,
    ),
    # "Discussions API: Retrieve a snippet discussion item".
    RestOperation(
        operation_id="create#retrieve-a-snippet-discussion-item",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/discussions/:discussion_id",
    ),
    # "Discussions API: Create a snippet thread".
    RestOperation(
        operation_id="create#create-a-snippet-thread",
        method="POST",
        path="/projects/:id/snippets/:snippet_id/discussions",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Add a note to a snippet thread".
    RestOperation(
        operation_id="create#add-a-note-to-a-snippet-thread",
        method="POST",
        path="/projects/:id/snippets/:snippet_id/discussions/:discussion_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Update a snippet thread note".
    RestOperation(
        operation_id="create#update-a-snippet-thread-note",
        method="PUT",
        path="/projects/:id/snippets/:snippet_id/discussions/:discussion_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Discussions API: Delete a snippet thread note".
    RestOperation(
        operation_id="create#delete-a-snippet-thread-note",
        method="DELETE",
        path="/projects/:id/snippets/:snippet_id/discussions/:discussion_id/notes/:note_id",
    ),
    # "Discussions API: List all epic discussion items".
    RestOperation(
        operation_id="create#list-all-epic-discussion-items",
        method="GET",
        path="/groups/:id/epics/:epic_id/discussions",
        paging=Paging.OFFSET,
    ),
    # "Discussions API: Retrieve an epic discussion item".
    RestOperation(
        operation_id="create#retrieve-an-epic-discussion-item",
        method="GET",
        path="/groups/:id/epics/:epic_id/discussions/:discussion_id",
    ),
    # "Discussions API: Create an epic thread".
    RestOperation(
        operation_id="create#create-an-epic-thread",
        method="POST",
        path="/groups/:id/epics/:epic_id/discussions",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Add a note to an epic thread".
    RestOperation(
        operation_id="create#add-a-note-to-an-epic-thread",
        method="POST",
        path="/groups/:id/epics/:epic_id/discussions/:discussion_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Update an epic thread note".
    RestOperation(
        operation_id="create#update-an-epic-thread-note",
        method="PUT",
        path="/groups/:id/epics/:epic_id/discussions/:discussion_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Discussions API: Delete an epic thread note".
    RestOperation(
        operation_id="create#delete-an-epic-thread-note",
        method="DELETE",
        path="/groups/:id/epics/:epic_id/discussions/:discussion_id/notes/:note_id",
    ),
    # "Discussions API: List all merge request discussion items".
    RestOperation(
        operation_id="create#list-all-merge-request-discussion-items",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions",
        paging=Paging.OFFSET,
    ),
    # "Discussions API: Retrieve a merge request discussion item".
    RestOperation(
        operation_id="create#retrieve-a-merge-request-discussion-item",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions/:discussion_id",
    ),
    # "Discussions API: Create a merge request thread".
    RestOperation(
        operation_id="create#create-a-merge-request-thread",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="commit_id", location=Location.BODY),
            Param(name="created_at", location=Location.BODY),
            Param(name="position", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Discussions API: Resolve a merge request thread".
    RestOperation(
        operation_id="create#resolve-a-merge-request-thread",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions/:discussion_id",
        params=(Param(name="resolved", location=Location.BODY, required=True),),
    ),
    # "Discussions API: Add note to a merge request thread".
    RestOperation(
        operation_id="create#add-note-to-a-merge-request-thread",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions/:discussion_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Update a merge request thread note".
    RestOperation(
        operation_id="create#update-a-merge-request-thread-note",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions/:discussion_id/notes/:note_id",
        params=(
            Param(name="body", location=Location.BODY),
            Param(name="resolved", location=Location.BODY),
        ),
    ),
    # "Discussions API: Delete a merge request thread note".
    RestOperation(
        operation_id="create#delete-a-merge-request-thread-note",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/discussions/:discussion_id/notes/:note_id",
    ),
    # "Discussions API: List all commit discussion items".
    RestOperation(
        operation_id="create#list-all-commit-discussion-items",
        method="GET",
        path="/projects/:id/repository/commits/:commit_id/discussions",
        paging=Paging.OFFSET,
    ),
    # "Discussions API: Retrieve a commit discussion item".
    RestOperation(
        operation_id="create#retrieve-a-commit-discussion-item",
        method="GET",
        path="/projects/:id/repository/commits/:commit_id/discussions/:discussion_id",
    ),
    # "Discussions API: Create a commit thread".
    RestOperation(
        operation_id="create#create-a-commit-thread",
        method="POST",
        path="/projects/:id/repository/commits/:commit_id/discussions",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
            Param(name="position", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Discussions API: Add note to a commit thread".
    RestOperation(
        operation_id="create#add-note-to-a-commit-thread",
        method="POST",
        path="/projects/:id/repository/commits/:commit_id/discussions/:discussion_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Discussions API: Update a commit thread note".
    RestOperation(
        operation_id="create#update-a-commit-thread-note",
        method="PUT",
        path="/projects/:id/repository/commits/:commit_id/discussions/:discussion_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY),),
    ),
    # "Discussions API: Delete a commit discussion note".
    RestOperation(
        operation_id="create#delete-a-commit-discussion-note",
        method="DELETE",
        path="/projects/:id/repository/commits/:commit_id/discussions/:discussion_id/notes/:note_id",
    ),
    # "Dockerfiles API: List all Dockerfile templates".
    RestOperation(
        operation_id="create#list-all-dockerfile-templates",
        method="GET",
        path="/templates/dockerfiles",
        paging=Paging.OFFSET,
    ),
    # "Dockerfiles API: Retrieve a single Dockerfile template".
    RestOperation(
        operation_id="create#retrieve-a-single-dockerfile-template",
        method="GET",
        path="/templates/dockerfiles/:key",
    ),
    # "Group push rules API: Retrieve the push rules of a group".
    RestOperation(
        operation_id="create#retrieve-the-push-rules-of-a-group",
        method="GET",
        path="/groups/:id/push_rule",
    ),
    # "Group push rules API: Add push rules to a group".
    RestOperation(
        operation_id="create#add-push-rules-to-a-group",
        method="POST",
        path="/groups/:id/push_rule",
        params=(
            Param(name="author_email_regex", location=Location.BODY),
            Param(name="branch_name_regex", location=Location.BODY),
            Param(name="commit_committer_check", location=Location.BODY),
            Param(name="commit_committer_name_check", location=Location.BODY),
            Param(name="commit_message_negative_regex", location=Location.BODY),
            Param(name="commit_message_regex", location=Location.BODY),
            Param(name="deny_delete_tag", location=Location.BODY),
            Param(name="file_name_regex", location=Location.BODY),
            Param(name="max_file_size", location=Location.BODY),
            Param(name="member_check", location=Location.BODY),
            Param(name="prevent_secrets", location=Location.BODY),
            Param(name="reject_non_dco_commits", location=Location.BODY),
            Param(name="reject_unsigned_commits", location=Location.BODY),
        ),
    ),
    # "Group push rules API: Update push rules of a group".
    RestOperation(
        operation_id="create#update-push-rules-of-a-group",
        method="PUT",
        path="/groups/:id/push_rule",
        params=(
            Param(name="author_email_regex", location=Location.BODY),
            Param(name="branch_name_regex", location=Location.BODY),
            Param(name="commit_committer_check", location=Location.BODY),
            Param(name="commit_committer_name_check", location=Location.BODY),
            Param(name="commit_message_negative_regex", location=Location.BODY),
            Param(name="commit_message_regex", location=Location.BODY),
            Param(name="deny_delete_tag", location=Location.BODY),
            Param(name="file_name_regex", location=Location.BODY),
            Param(name="max_file_size", location=Location.BODY),
            Param(name="member_check", location=Location.BODY),
            Param(name="prevent_secrets", location=Location.BODY),
            Param(name="reject_non_dco_commits", location=Location.BODY),
            Param(name="reject_unsigned_commits", location=Location.BODY),
        ),
    ),
    # "Group push rules API: Delete the push rules of a group".
    RestOperation(
        operation_id="create#delete-the-push-rules-of-a-group",
        method="DELETE",
        path="/groups/:id/push_rule",
    ),
    # "Group repository storage moves API: List all group repository storage moves".
    RestOperation(
        operation_id="create#list-all-group-repository-storage-moves",
        method="GET",
        path="/group_repository_storage_moves",
        paging=Paging.OFFSET,
    ),
    # "Group repository storage moves API: List all repository storage moves for a group".
    RestOperation(
        operation_id="create#list-all-repository-storage-moves-for-a-group",
        method="GET",
        path="/groups/:group_id/repository_storage_moves",
        paging=Paging.OFFSET,
    ),
    # "Group repository storage moves API: Retrieve a group repository storage move".
    RestOperation(
        operation_id="create#retrieve-a-group-repository-storage-move",
        method="GET",
        path="/group_repository_storage_moves/:repository_storage_id",
    ),
    # "Group repository storage moves API: Retrieve a repository storage move for a group".
    RestOperation(
        operation_id="create#retrieve-a-repository-storage-move-for-a-group",
        method="GET",
        path="/groups/:group_id/repository_storage_moves/:repository_storage_id",
    ),
    # "Group repository storage moves API: Create a group repository storage move".
    RestOperation(
        operation_id="create#create-a-group-repository-storage-move",
        method="POST",
        path="/groups/:group_id/repository_storage_moves",
        params=(Param(name="destination_storage_name", location=Location.BODY),),
    ),
    # "Group repository storage moves API: Create group repository storage moves for a storage shard".
    RestOperation(
        operation_id="create#create-group-repository-storage-moves-for-a-storage-shard",
        method="POST",
        path="/group_repository_storage_moves",
        params=(
            Param(name="source_storage_name", location=Location.BODY, required=True),
            Param(name="destination_storage_name", location=Location.BODY),
        ),
    ),
    # "Group SSH certificates API: List all group SSH certificates".
    RestOperation(
        operation_id="create#list-all-group-ssh-certificates",
        method="GET",
        path="/groups/:id/ssh_certificates",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group SSH certificates API: Add a group SSH certificate".
    RestOperation(
        operation_id="create#add-a-group-ssh-certificate",
        method="POST",
        path="/groups/:id/ssh_certificates",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
        ),
    ),
    # "Group SSH certificates API: Delete a group SSH certificate"; `:id` is the group's at its first place and the
    # certificate's at its second, each given its own value (issue #63, design.md D2).
    RestOperation(
        operation_id="create#delete-a-group-ssh-certificate",
        method="DELETE",
        path="/groups/:id/ssh_certificates/:id",
        positional_names=("id",),
    ),
    # "Group-level protected branches API: List protected branches".
    RestOperation(
        operation_id="create#list-protected-branches",
        method="GET",
        path="/groups/:id/protected_branches",
        params=(Param(name="search", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Group-level protected branches API: Get a single protected branch or wildcard protected branch".
    RestOperation(
        operation_id="create#get-a-single-protected-branch-or-wildcard-protected-branch",
        method="GET",
        path="/groups/:id/protected_branches/:name",
    ),
    # "Group-level protected branches API: Protect repository branches".
    RestOperation(
        operation_id="create#protect-repository-branches",
        method="POST",
        path="/groups/:id/protected_branches",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="allow_force_push", location=Location.BODY),
            Param(name="allowed_to_merge", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_push", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_unprotect", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="code_owner_approval_required", location=Location.BODY),
            Param(name="merge_access_level", location=Location.BODY),
            Param(name="push_access_level", location=Location.BODY),
            Param(name="unprotect_access_level", location=Location.BODY),
        ),
    ),
    # "Group-level protected branches API: Unprotect repository branches".
    RestOperation(
        operation_id="create#unprotect-repository-branches",
        method="DELETE",
        path="/groups/:id/protected_branches/:name",
    ),
    # "Group-level protected branches API: Update a protected branch".
    RestOperation(
        operation_id="create#update-a-protected-branch",
        method="PATCH",
        path="/groups/:id/protected_branches/:name",
        params=(
            Param(name="allow_force_push", location=Location.BODY),
            Param(name="allowed_to_push", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_merge", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_unprotect", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="code_owner_approval_required", location=Location.BODY),
        ),
    ),
    # "Instance SSH certificates API: List all instance SSH certificates".
    RestOperation(
        operation_id="create#list-all-instance-ssh-certificates",
        method="GET",
        path="/admin/ssh_certificates",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Instance SSH certificates API: Add an instance SSH certificate".
    RestOperation(
        operation_id="create#add-an-instance-ssh-certificate",
        method="POST",
        path="/admin/ssh_certificates",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
        ),
    ),
    # "Instance SSH certificates API: Delete an instance SSH certificate".
    RestOperation(
        operation_id="create#delete-an-instance-ssh-certificate",
        method="DELETE",
        path="/admin/ssh_certificates/:id",
    ),
    # "Keys API: Retrieve user by SSH key ID".
    RestOperation(
        operation_id="create#retrieve-user-by-ssh-key-id",
        method="GET",
        path="/keys/:id",
    ),
    # "Keys API: Retrieve user by SSH key fingerprint"; one of the two References of `GET /keys`.
    RestOperation(
        operation_id="create#retrieve-user-by-ssh-key-fingerprint",
        method="GET",
        path="/keys",
        params=(Param(name="fingerprint", location=Location.QUERY, required=True),),
    ),
    # "Keys API: Retrieve user by deploy key fingerprint"; one of the two References of `GET /keys`.
    RestOperation(
        operation_id="create#retrieve-user-by-deploy-key-fingerprint",
        method="GET",
        path="/keys",
        params=(Param(name="fingerprint", location=Location.QUERY, required=True),),
    ),
    # "Merge request approval settings API: Retrieve MR approval settings for a group".
    RestOperation(
        operation_id="create#retrieve-mr-approval-settings-for-a-group",
        method="GET",
        path="/groups/:id/merge_request_approval_setting",
    ),
    # "Merge request approval settings API: Update group MR approval settings".
    RestOperation(
        operation_id="create#update-group-mr-approval-settings",
        method="PUT",
        path="/groups/:id/merge_request_approval_setting",
        params=(
            Param(name="allow_author_approval", location=Location.BODY),
            Param(name="allow_committer_approval", location=Location.BODY),
            Param(name="allow_overrides_to_approver_list_per_merge_request", location=Location.BODY),
            Param(name="retain_approvals_on_push", location=Location.BODY),
            Param(name="require_reauthentication_to_approve", location=Location.BODY),
        ),
    ),
    # "Merge request approval settings API: Retrieve MR approval settings for a project".
    RestOperation(
        operation_id="create#retrieve-mr-approval-settings-for-a-project",
        method="GET",
        path="/projects/:id/merge_request_approval_setting",
    ),
    # "Merge request approval settings API: Update project MR approval settings".
    RestOperation(
        operation_id="create#update-project-mr-approval-settings",
        method="PUT",
        path="/projects/:id/merge_request_approval_setting",
        params=(
            Param(name="allow_author_approval", location=Location.BODY),
            Param(name="allow_committer_approval", location=Location.BODY),
            Param(name="allow_overrides_to_approver_list_per_merge_request", location=Location.BODY),
            Param(name="retain_approvals_on_push", location=Location.BODY),
            Param(name="selective_code_owner_removals", location=Location.BODY),
            Param(name="require_reauthentication_to_approve", location=Location.BODY),
        ),
    ),
    # "Project Aliases API: List all project aliases".
    RestOperation(
        operation_id="create#list-all-project-aliases",
        method="GET",
        path="/project_aliases",
        paging=Paging.OFFSET,
    ),
    # "Project Aliases API: Retrieve a project alias".
    RestOperation(
        operation_id="create#retrieve-a-project-alias",
        method="GET",
        path="/project_aliases/:name",
    ),
    # "Project Aliases API: Create a project alias".
    RestOperation(
        operation_id="create#create-a-project-alias",
        method="POST",
        path="/project_aliases",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="project_id", location=Location.BODY, required=True),
        ),
    ),
    # "Project Aliases API: Delete a project alias".
    RestOperation(
        operation_id="create#delete-a-project-alias",
        method="DELETE",
        path="/project_aliases/:name",
    ),
    # "Project push rules API: Retrieve the push rules of a project".
    RestOperation(
        operation_id="create#retrieve-the-push-rules-of-a-project",
        method="GET",
        path="/projects/:id/push_rule",
    ),
    # "Project push rules API: Add push rules to a project".
    RestOperation(
        operation_id="create#add-push-rules-to-a-project",
        method="POST",
        path="/projects/:id/push_rule",
        params=(
            Param(name="author_email_regex", location=Location.BODY),
            Param(name="branch_name_regex", location=Location.BODY),
            Param(name="commit_committer_check", location=Location.BODY),
            Param(name="commit_committer_name_check", location=Location.BODY),
            Param(name="commit_message_negative_regex", location=Location.BODY),
            Param(name="commit_message_regex", location=Location.BODY),
            Param(name="deny_delete_tag", location=Location.BODY),
            Param(name="file_name_regex", location=Location.BODY),
            Param(name="max_file_size", location=Location.BODY),
            Param(name="member_check", location=Location.BODY),
            Param(name="prevent_secrets", location=Location.BODY),
            Param(name="reject_non_dco_commits", location=Location.BODY),
            Param(name="reject_unsigned_commits", location=Location.BODY),
        ),
    ),
    # "Project push rules API: Update push rules of a project".
    RestOperation(
        operation_id="create#update-push-rules-of-a-project",
        method="PUT",
        path="/projects/:id/push_rule",
        params=(
            Param(name="author_email_regex", location=Location.BODY),
            Param(name="branch_name_regex", location=Location.BODY),
            Param(name="commit_committer_check", location=Location.BODY),
            Param(name="commit_committer_name_check", location=Location.BODY),
            Param(name="commit_message_negative_regex", location=Location.BODY),
            Param(name="commit_message_regex", location=Location.BODY),
            Param(name="deny_delete_tag", location=Location.BODY),
            Param(name="file_name_regex", location=Location.BODY),
            Param(name="max_file_size", location=Location.BODY),
            Param(name="member_check", location=Location.BODY),
            Param(name="prevent_secrets", location=Location.BODY),
            Param(name="reject_non_dco_commits", location=Location.BODY),
            Param(name="reject_unsigned_commits", location=Location.BODY),
        ),
    ),
    # "Project push rules API: Delete the push rules of a project".
    RestOperation(
        operation_id="create#delete-the-push-rules-of-a-project",
        method="DELETE",
        path="/projects/:id/push_rule",
    ),
    # "Project remote mirrors API: List all remote mirrors for a project".
    RestOperation(
        operation_id="create#list-all-remote-mirrors-for-a-project",
        method="GET",
        path="/projects/:id/remote_mirrors",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project remote mirrors API: Retrieve a remote mirror for a project".
    RestOperation(
        operation_id="create#retrieve-a-remote-mirror-for-a-project",
        method="GET",
        path="/projects/:id/remote_mirrors/:mirror_id",
    ),
    # "Project remote mirrors API: Retrieve a public key for a remote mirror".
    RestOperation(
        operation_id="create#retrieve-a-public-key-for-a-remote-mirror",
        method="GET",
        path="/projects/:id/remote_mirrors/:mirror_id/public_key",
    ),
    # "Project remote mirrors API: Create a push mirror".
    RestOperation(
        operation_id="create#create-a-push-mirror",
        method="POST",
        path="/projects/:id/remote_mirrors",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="auth_method", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="host_keys", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="keep_divergent_refs", location=Location.BODY),
            Param(name="mirror_branch_regex", location=Location.BODY),
            Param(name="only_protected_branches", location=Location.BODY),
        ),
    ),
    # "Project remote mirrors API: Update a remote mirror in a project".
    RestOperation(
        operation_id="create#update-a-remote-mirror-in-a-project",
        method="PUT",
        path="/projects/:id/remote_mirrors/:mirror_id",
        params=(
            Param(name="auth_method", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="host_keys", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="keep_divergent_refs", location=Location.BODY),
            Param(name="mirror_branch_regex", location=Location.BODY),
            Param(name="only_protected_branches", location=Location.BODY),
        ),
    ),
    # "Project remote mirrors API: Force push mirror update".
    RestOperation(
        operation_id="create#force-push-mirror-update",
        method="POST",
        path="/projects/:id/remote_mirrors/:mirror_id/sync",
    ),
    # "Project remote mirrors API: Delete a remote mirror from a project".
    RestOperation(
        operation_id="create#delete-a-remote-mirror-from-a-project",
        method="DELETE",
        path="/projects/:id/remote_mirrors/:mirror_id",
    ),
    # "Project snippets: List all snippets for a project".
    RestOperation(
        operation_id="create#list-all-snippets-for-a-project",
        method="GET",
        path="/projects/:id/snippets",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project snippets: Retrieve a snippet".
    RestOperation(
        operation_id="create#retrieve-a-snippet",
        method="GET",
        path="/projects/:id/snippets/:snippet_id",
    ),
    # "Project snippets: Create a snippet".
    RestOperation(
        operation_id="create#create-a-snippet",
        method="POST",
        path="/projects/:id/snippets",
        params=(
            Param(name="files", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="content", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="file_name", location=Location.BODY),
            Param(name="visibility", location=Location.BODY),
        ),
    ),
    # "Project snippets: Update a snippet".
    RestOperation(
        operation_id="create#update-a-snippet",
        method="PUT",
        path="/projects/:id/snippets/:snippet_id",
        params=(
            Param(name="content", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="file_name", location=Location.BODY),
            Param(name="files", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="title", location=Location.BODY),
            Param(name="visibility", location=Location.BODY),
        ),
    ),
    # "Project snippets: Delete a snippet".
    RestOperation(
        operation_id="create#delete-a-snippet",
        method="DELETE",
        path="/projects/:id/snippets/:snippet_id",
    ),
    # "Project snippets: Retrieve snippet content".
    RestOperation(
        operation_id="create#retrieve-snippet-content",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/raw",
    ),
    # "Project snippets: Retrieve snippet repository file content".
    RestOperation(
        operation_id="create#retrieve-snippet-repository-file-content",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/files/:ref/:file_path/raw",
    ),
    # "Project snippets: Retrieve user agent details".
    RestOperation(
        operation_id="create#retrieve-user-agent-details",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/user_agent_detail",
    ),
    # "Project statistics API: Retrieve the statistics of the last 30 days".
    RestOperation(
        operation_id="create#retrieve-the-statistics-of-the-last-30-days",
        method="GET",
        path="/projects/:id/statistics",
    ),
    # "Project templates API: List all templates of a particular type".
    RestOperation(
        operation_id="create#list-all-templates-of-a-particular-type",
        method="GET",
        path="/projects/:id/templates/:type",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project templates API: Retrieve a template of a particular type".
    RestOperation(
        operation_id="create#retrieve-a-template-of-a-particular-type",
        method="GET",
        path="/projects/:id/templates/:type/:name",
        params=(
            Param(name="fullname", location=Location.QUERY),
            Param(name="project", location=Location.QUERY),
            Param(name="source_template_project_id", location=Location.QUERY),
        ),
    ),
    # "Protected branches API: List protected branches".
    RestOperation(
        operation_id="create#list-protected-branches-1",
        method="GET",
        path="/projects/:id/protected_branches",
        params=(
            Param(name="search", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Protected branches API: Retrieve a protected branch or wildcard protected branch".
    RestOperation(
        operation_id="create#retrieve-a-protected-branch-or-wildcard-protected-branch",
        method="GET",
        path="/projects/:id/protected_branches/:name",
    ),
    # "Protected branches API: Protect repository branches".
    RestOperation(
        operation_id="create#protect-repository-branches-1",
        method="POST",
        path="/projects/:id/protected_branches",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="allow_force_push", location=Location.BODY),
            Param(name="allowed_to_merge", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_push", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_unprotect", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="code_owner_approval_required", location=Location.BODY),
            Param(name="merge_access_level", location=Location.BODY),
            Param(name="push_access_level", location=Location.BODY),
            Param(name="unprotect_access_level", location=Location.BODY),
        ),
    ),
    # "Protected branches API: Unprotect repository branches".
    RestOperation(
        operation_id="create#unprotect-repository-branches-1",
        method="DELETE",
        path="/projects/:id/protected_branches/:name",
    ),
    # "Protected branches API: Update a protected branch".
    RestOperation(
        operation_id="create#update-a-protected-branch-1",
        method="PATCH",
        path="/projects/:id/protected_branches/:name",
        params=(
            Param(name="allow_force_push", location=Location.BODY),
            Param(name="allowed_to_merge", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_push", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="allowed_to_unprotect", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="code_owner_approval_required", location=Location.BODY),
            Param(name="unprotect_access_level", location=Location.BODY),
        ),
    ),
    # "Protected tags API: List protected tags".
    RestOperation(
        operation_id="create#list-protected-tags",
        method="GET",
        path="/projects/:id/protected_tags",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Protected tags API: Get a protected tag or wildcard protected tag".
    RestOperation(
        operation_id="create#get-a-protected-tag-or-wildcard-protected-tag",
        method="GET",
        path="/projects/:id/protected_tags/:name",
    ),
    # "Protected tags API: Protect a repository tag".
    RestOperation(
        operation_id="create#protect-a-repository-tag",
        method="POST",
        path="/projects/:id/protected_tags",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="allowed_to_create", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="create_access_level", location=Location.BODY),
        ),
    ),
    # "Protected tags API: Unprotect repository tags".
    RestOperation(
        operation_id="create#unprotect-repository-tags",
        method="DELETE",
        path="/projects/:id/protected_tags/:name",
    ),
    # "Pull mirroring API: Retrieve project pull mirror details".
    RestOperation(
        operation_id="create#retrieve-project-pull-mirror-details",
        method="GET",
        path="/projects/:id/mirror/pull",
    ),
    # "Pull mirroring API: Update project pull mirroring settings".
    RestOperation(
        operation_id="create#update-project-pull-mirroring-settings",
        method="PUT",
        path="/projects/:id/mirror/pull",
        params=(
            Param(name="auth_password", location=Location.BODY),
            Param(name="auth_user", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="mirror_branch_regex", location=Location.BODY),
            Param(name="mirror_overwrites_diverged_branches", location=Location.BODY),
            Param(name="mirror_trigger_builds", location=Location.BODY),
            Param(name="only_mirror_protected_branches", location=Location.BODY),
            Param(name="url", location=Location.BODY),
        ),
    ),
    # "Repositories API: List all repository trees in a project".
    RestOperation(
        operation_id="create#list-all-repository-trees-in-a-project",
        method="GET",
        path="/projects/:id/repository/tree",
        params=(
            Param(name="page_token", location=Location.QUERY),
            Param(name="pagination", location=Location.QUERY),
            Param(name="path", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="recursive", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="with_last_commit", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Repositories API: Retrieve a blob from a repository".
    RestOperation(
        operation_id="create#retrieve-a-blob-from-a-repository",
        method="GET",
        path="/projects/:id/repository/blobs/:sha",
    ),
    # "Repositories API: Retrieve raw blob content"; the blob's bytes, which `call` writes unchanged.
    RestOperation(
        operation_id="create#retrieve-raw-blob-content",
        method="GET",
        path="/projects/:id/repository/blobs/:sha/raw",
    ),
    # "Repositories API: Retrieve multiple blobs in a single request"; the `files` row reads `array`, its members
    # `files[].path` and `files[].ref`, so an array of hashes.
    RestOperation(
        operation_id="create#retrieve-multiple-blobs-in-a-single-request",
        method="POST",
        path="/projects/:id/repository/blobs/batch",
        params=(Param(name="files", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),),
    ),
    # "Repositories API: Retrieve file archive from a repository"; its `[.format]` suffix takes one of the formats
    # docs.gitlab.com `repositories` "Available options" lists, or none (issue #63, design.md D3).
    RestOperation(
        operation_id="create#retrieve-file-archive-from-a-repository",
        method="GET",
        path="/projects/:id/repository/archive[.format]",
        params=(
            Param(name="exclude_paths", location=Location.QUERY),
            Param(name="include_lfs_blobs", location=Location.QUERY),
            Param(name="path", location=Location.QUERY),
            Param(name="sha", location=Location.QUERY),
            Param(name="ref_type", location=Location.QUERY),
        ),
        suffix_values=("bz2", "tar", "tar.bz2", "tar.gz", "tb2", "tbz", "tbz2", "zip"),
    ),
    # "Repositories API: Compare branches, tags, or commits".
    RestOperation(
        operation_id="create#compare-branches-tags-or-commits",
        method="GET",
        path="/projects/:id/repository/compare",
        params=(
            Param(name="from", location=Location.QUERY, required=True),
            Param(name="to", location=Location.QUERY, required=True),
            Param(name="from_project_id", location=Location.QUERY),
            Param(name="straight", location=Location.QUERY),
            Param(name="unidiff", location=Location.QUERY),
        ),
    ),
    # "Repositories API: Get contributor list".
    RestOperation(
        operation_id="create#get-contributor-list",
        method="GET",
        path="/projects/:id/repository/contributors",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Repositories API: Get merge base".
    RestOperation(
        operation_id="create#get-merge-base",
        method="GET",
        path="/projects/:id/repository/merge_base",
        params=(Param(name="refs", location=Location.QUERY, kind=Kind.ARRAY, required=True),),
    ),
    # "Repositories API: Retrieve diff statistics".
    RestOperation(
        operation_id="create#retrieve-diff-statistics",
        method="GET",
        path="/projects/:id/repository/diff_stats",
        params=(
            Param(name="from", location=Location.QUERY, required=True),
            Param(name="to", location=Location.QUERY, required=True),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Repositories API: Retrieve diverging commit counts".
    RestOperation(
        operation_id="create#retrieve-diverging-commit-counts",
        method="GET",
        path="/projects/:id/repository/diverging_commits",
        params=(
            Param(name="from", location=Location.QUERY, required=True),
            Param(name="to", location=Location.QUERY, required=True),
            Param(name="max_count", location=Location.QUERY),
        ),
    ),
    # "Repositories API: Retrieve changed paths".
    RestOperation(
        operation_id="create#retrieve-changed-paths",
        method="GET",
        path="/projects/:id/repository/changed_paths",
        params=(
            Param(name="from", location=Location.QUERY, required=True),
            Param(name="to", location=Location.QUERY, required=True),
            Param(name="find_renames", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Repositories API: Generate changelog data"; its base record, on the first of its two endpoints.
    RestOperation(
        operation_id="create#generate-changelog-data",
        method="GET",
        path="/projects/:id/repository/changelog",
        params=(
            Param(name="version", location=Location.QUERY, required=True),
            Param(name="config_file", location=Location.QUERY),
            Param(name="config_file_ref", location=Location.QUERY),
            Param(name="date", location=Location.QUERY),
            Param(name="from", location=Location.QUERY),
            Param(name="to", location=Location.QUERY),
            Param(name="trailer", location=Location.QUERY),
        ),
    ),
    # "Repositories API: Generate changelog data"; its second endpoint, a copy of the base record (issue #63, D1, D8).
    RestOperation(
        operation_id="create#generate-changelog-data",
        method="GET",
        path="/projects/:id/repository/changelog.txt",
        params=(
            Param(name="version", location=Location.QUERY, required=True),
            Param(name="config_file", location=Location.QUERY),
            Param(name="config_file_ref", location=Location.QUERY),
            Param(name="date", location=Location.QUERY),
            Param(name="from", location=Location.QUERY),
            Param(name="to", location=Location.QUERY),
            Param(name="trailer", location=Location.QUERY),
        ),
    ),
    # "Repositories API: Health".
    RestOperation(
        operation_id="create#health",
        method="GET",
        path="/projects/:id/repository/health",
        params=(Param(name="generate", location=Location.QUERY),),
    ),
    # "Repository files API: Retrieve a file from a repository".
    RestOperation(
        operation_id="create#retrieve-a-file-from-a-repository",
        method="GET",
        path="/projects/:id/repository/files/:file_path",
        params=(Param(name="ref", location=Location.QUERY, required=True),),
    ),
    # "Repository files API: Get file metadata only".
    RestOperation(
        operation_id="create#get-file-metadata-only",
        method="HEAD",
        path="/projects/:id/repository/files/:file_path",
        params=(Param(name="ref", location=Location.QUERY, required=True),),
    ),
    # "Repository files API: Retrieve file blame history from a repository"; `range` is a query hash, and its members
    # `range[start]` and `range[end]` query attributes of their own.
    RestOperation(
        operation_id="create#retrieve-file-blame-history-from-a-repository",
        method="GET",
        path="/projects/:id/repository/files/:file_path/blame",
        params=(
            Param(name="ref", location=Location.QUERY, required=True),
            Param(name="range", location=Location.QUERY, kind=Kind.HASH),
            Param(name="range[end]", location=Location.QUERY),
            Param(name="range[start]", location=Location.QUERY),
        ),
    ),
    # "Repository files API: Get file blame metadata only".
    RestOperation(
        operation_id="create#get-file-blame-metadata-only",
        method="HEAD",
        path="/projects/:id/repository/files/:file_path/blame",
        params=(Param(name="ref", location=Location.QUERY, required=True),),
    ),
    # "Repository files API: Retrieve a raw file from a repository".
    RestOperation(
        operation_id="create#retrieve-a-raw-file-from-a-repository",
        method="GET",
        path="/projects/:id/repository/files/:file_path/raw",
        params=(
            Param(name="lfs", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
        ),
    ),
    # "Snippet repository storage moves API: List all snippet repository storage moves".
    RestOperation(
        operation_id="create#list-all-snippet-repository-storage-moves",
        method="GET",
        path="/snippet_repository_storage_moves",
        paging=Paging.OFFSET,
    ),
    # "Snippet repository storage moves API: List all repository storage moves for a snippet".
    RestOperation(
        operation_id="create#list-all-repository-storage-moves-for-a-snippet",
        method="GET",
        path="/snippets/:snippet_id/repository_storage_moves",
        paging=Paging.OFFSET,
    ),
    # "Snippet repository storage moves API: Retrieve a snippet repository storage move".
    RestOperation(
        operation_id="create#retrieve-a-snippet-repository-storage-move",
        method="GET",
        path="/snippet_repository_storage_moves/:repository_storage_id",
    ),
    # "Snippet repository storage moves API: Retrieve a repository storage move for a snippet".
    RestOperation(
        operation_id="create#retrieve-a-repository-storage-move-for-a-snippet",
        method="GET",
        path="/snippets/:snippet_id/repository_storage_moves/:repository_storage_id",
    ),
    # "Snippet repository storage moves API: Schedule a repository storage move for a snippet".
    RestOperation(
        operation_id="create#schedule-a-repository-storage-move-for-a-snippet",
        method="POST",
        path="/snippets/:snippet_id/repository_storage_moves",
        params=(Param(name="destination_storage_name", location=Location.BODY),),
    ),
    # "Snippet repository storage moves API: Schedule repository storage moves for all snippets on a storage shard".
    RestOperation(
        operation_id="create#schedule-repository-storage-moves-for-all-snippets-on-a-storage-shard",
        method="POST",
        path="/snippet_repository_storage_moves",
        params=(
            Param(name="source_storage_name", location=Location.BODY, required=True),
            Param(name="destination_storage_name", location=Location.BODY),
        ),
    ),
    # "Snippets API: List all snippets for current user".
    RestOperation(
        operation_id="create#list-all-snippets-for-current-user",
        method="GET",
        path="/snippets",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Snippets API: Retrieve a snippet".
    RestOperation(
        operation_id="create#retrieve-a-snippet-1",
        method="GET",
        path="/snippets/:id",
    ),
    # "Snippets API: Single snippet contents".
    RestOperation(
        operation_id="create#single-snippet-contents",
        method="GET",
        path="/snippets/:id/raw",
    ),
    # "Snippets API: Snippet repository file content".
    RestOperation(
        operation_id="create#snippet-repository-file-content",
        method="GET",
        path="/snippets/:id/files/:ref/:file_path/raw",
    ),
    # "Snippets API: Create a snippet".
    RestOperation(
        operation_id="create#create-a-snippet-1",
        method="POST",
        path="/snippets",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="content", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="file_name", location=Location.BODY),
            Param(name="files", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="visibility", location=Location.BODY),
        ),
    ),
    # "Snippets API: Update snippet".
    RestOperation(
        operation_id="create#update-snippet",
        method="PUT",
        path="/snippets/:id",
        params=(
            Param(name="content", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="file_name", location=Location.BODY),
            Param(name="files", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="title", location=Location.BODY),
            Param(name="visibility", location=Location.BODY),
        ),
    ),
    # "Snippets API: Delete snippet".
    RestOperation(
        operation_id="create#delete-snippet",
        method="DELETE",
        path="/snippets/:id",
    ),
    # "Snippets API: List all public snippets".
    RestOperation(
        operation_id="create#list-all-public-snippets",
        method="GET",
        path="/snippets/public",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Snippets API: List all snippets".
    RestOperation(
        operation_id="create#list-all-snippets",
        method="GET",
        path="/snippets/all",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="repository_storage", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Snippets API: Get user agent details".
    RestOperation(
        operation_id="create#get-user-agent-details",
        method="GET",
        path="/snippets/:id/user_agent_detail",
    ),
    # "Tags API: List all project repository tags".
    RestOperation(
        operation_id="create#list-all-project-repository-tags",
        method="GET",
        path="/projects/:id/repository/tags",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="page_token", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Tags API: Retrieve a single repository tag".
    RestOperation(
        operation_id="create#retrieve-a-single-repository-tag",
        method="GET",
        path="/projects/:id/repository/tags/:tag_name",
    ),
    # "Tags API: Create a new tag".
    RestOperation(
        operation_id="create#create-a-new-tag",
        method="POST",
        path="/projects/:id/repository/tags",
        params=(
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="tag_name", location=Location.BODY, required=True),
            Param(name="message", location=Location.BODY),
        ),
    ),
    # "Tags API: Delete a tag".
    RestOperation(
        operation_id="create#delete-a-tag",
        method="DELETE",
        path="/projects/:id/repository/tags/:tag_name",
    ),
    # "Tags API: Retrieve X.509 signature of a tag".
    RestOperation(
        operation_id="create#retrieve-x509-signature-of-a-tag",
        method="GET",
        path="/projects/:id/repository/tags/:tag_name/signature",
    ),
    # "Web Commits API: Retrieve public signing key".
    RestOperation(
        operation_id="create#retrieve-public-signing-key",
        method="GET",
        path="/web_commits/public_key",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/projects/:id/mirror/pull"),
        ("POST", "/projects/:id/repository/branches"),
        ("POST", "/projects/:id/repository/changelog"),
        ("POST", "/projects/:id/repository/commits"),
        ("POST", "/projects/:id/repository/commits/:sha/cherry_pick"),
        ("POST", "/projects/:id/repository/commits/:sha/revert"),
        ("DELETE", "/projects/:id/repository/files/:file_path"),
        ("POST", "/projects/:id/repository/files/:file_path"),
        ("PUT", "/projects/:id/repository/files/:file_path"),
        ("PUT", "/projects/:id/repository/submodules/:submodule"),
        ("PUT", "/suggestions/:id/apply"),
        ("PUT", "/suggestions/batch_apply"),
    }
)
