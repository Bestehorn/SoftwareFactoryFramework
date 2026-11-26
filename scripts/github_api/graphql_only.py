"""The "Only in GraphQL" capabilities of the GitHub API (issue #30 design D1, D2, D5).

``OPERATIONS`` holds one ``GraphQLOperation`` per GraphQL operation serving a row of the "Only in GraphQL" table of
``docs/api-reference/github/graphql/conventions.md``: a capability has as many records as it has operations, and each
record's ``capability`` is its row's first cell, verbatim. Every row is served, so ``PENDING_CAPABILITIES`` is empty.

A record's operation ID is ``graphql/`` followed by the member it runs, without its arguments: the mutation's name
(``graphql/pinIssue``), or ``<Type>.<field>`` for a query (``graphql/Repository.mergeQueue``). It has the
``<family>/<name>`` shape of the REST index's IDs, no index ID has the family ``graphql``, and ``call`` reads the prefix
to send the record as GraphQL.

A document has one of two shapes:

- a query pages one connection, selected along one path below ``repository(owner: $owner, name: $name)``: its last
  field takes ``first: 100`` (the most ``conventions.md`` "Connections and cursor pagination" allows) and
  ``after: $after``, and selects ``nodes`` and ``pageInfo { hasNextPage endCursor }``. Its ``connection`` is the keys of
  that path, and ``Transport.graphql_nodes`` sets ``$after`` on every page.
- a mutation is ``mutation($input: <I>!) { <m>(input: $input) { clientMutationId <selection> } }``, ``<I>`` the input
  type the signature line of ``mutations.md`` names for ``<m>``. Its ``connection`` is ``()``, and the caller gives the
  whole input object, its node IDs included, as the one variable ``input``.

``graphql/enablePullRequestAutoMerge``, ``graphql/createCommitOnBranch``, ``graphql/revertPullRequest`` and
``graphql/transferIssue`` are refused by ``commands/call.py``'s ``GATED_OPERATIONS`` before any request: each is
declared here, so its capability is covered and its document is held to the reference, but it is never sent.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import GRAPHQL_ID_PREFIX, GraphQLOperation

# The first cells of the "Only in GraphQL" table, verbatim and in the table's order.
CAPABILITY_DISCUSSIONS = "Repository discussions"
CAPABILITY_PROJECTS_V2 = "Create, update, delete, copy or link a Projects v2 project"
CAPABILITY_AUTO_MERGE = "Auto-merge on or off"
CAPABILITY_DRAFT = "Draft to ready and back"
CAPABILITY_REVIEW_THREADS = "Resolve review threads"
CAPABILITY_HIDE_COMMENTS = "Hide comments"
CAPABILITY_TRANSFER_ISSUE = "Move an issue to another repo"
CAPABILITY_PIN_ISSUE = "Pin an issue"
CAPABILITY_REVERT = "Revert a PR"
CAPABILITY_MERGE_QUEUE = "Read a merge queue, remove an entry"
CAPABILITY_SPONSORS = "Sponsors"
CAPABILITY_MULTI_FILE_COMMIT = "Multi-file commit in one call"
CAPABILITY_BRANCH_PROTECTION = "Branch protection with wildcard patterns"


def _mutation(*, capability: str, name: str, input_type: str, selection: str) -> GraphQLOperation:
    """The record of the mutation ``name``: the ID ``graphql/<name>``, one ``$input`` of the non-null ``input_type``,
    and the payload's ``clientMutationId`` and ``selection``."""
    return GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}{name}",
        capability=capability,
        document=f"mutation($input: {input_type}!) {{ {name}(input: $input) {{ clientMutationId {selection} }} }}",
    )


OPERATIONS: Tuple[GraphQLOperation, ...] = (
    # Repository discussions: the discussions and their categories (a category's ID is createDiscussion's
    # categoryId), then the mutations that open, comment on and answer a discussion.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Repository.discussions",
        capability=CAPABILITY_DISCUSSIONS,
        document=(
            "query($owner: String!, $name: String!, $after: String) { repository(owner: $owner, name: $name) { "
            "discussions(first: 100, after: $after) { nodes { id number title } "
            "pageInfo { hasNextPage endCursor } } } }"
        ),
        connection=("repository", "discussions"),
    ),
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Repository.discussionCategories",
        capability=CAPABILITY_DISCUSSIONS,
        document=(
            "query($owner: String!, $name: String!, $after: String) { repository(owner: $owner, name: $name) { "
            "discussionCategories(first: 100, after: $after) { nodes { id name } "
            "pageInfo { hasNextPage endCursor } } } }"
        ),
        connection=("repository", "discussionCategories"),
    ),
    _mutation(
        capability=CAPABILITY_DISCUSSIONS,
        name="createDiscussion",
        input_type="CreateDiscussionInput",
        selection="discussion { id number }",
    ),
    _mutation(
        capability=CAPABILITY_DISCUSSIONS,
        name="addDiscussionComment",
        input_type="AddDiscussionCommentInput",
        selection="comment { id }",
    ),
    _mutation(
        capability=CAPABILITY_DISCUSSIONS,
        name="markDiscussionCommentAsAnswer",
        input_type="MarkDiscussionCommentAsAnswerInput",
        selection="discussion { id }",
    ),
    # Projects v2.
    _mutation(
        capability=CAPABILITY_PROJECTS_V2,
        name="createProjectV2",
        input_type="CreateProjectV2Input",
        selection="projectV2 { id number }",
    ),
    _mutation(
        capability=CAPABILITY_PROJECTS_V2,
        name="copyProjectV2",
        input_type="CopyProjectV2Input",
        selection="projectV2 { id number }",
    ),
    _mutation(
        capability=CAPABILITY_PROJECTS_V2,
        name="updateProjectV2",
        input_type="UpdateProjectV2Input",
        selection="projectV2 { id }",
    ),
    _mutation(
        capability=CAPABILITY_PROJECTS_V2,
        name="deleteProjectV2",
        input_type="DeleteProjectV2Input",
        selection="projectV2 { id }",
    ),
    _mutation(
        capability=CAPABILITY_PROJECTS_V2,
        name="linkProjectV2ToRepository",
        input_type="LinkProjectV2ToRepositoryInput",
        selection="repository { id }",
    ),
    # Auto-merge: enabling it is refused (design D5); merge-pr never turns it on.
    _mutation(
        capability=CAPABILITY_AUTO_MERGE,
        name="enablePullRequestAutoMerge",
        input_type="EnablePullRequestAutoMergeInput",
        selection="pullRequest { id }",
    ),
    _mutation(
        capability=CAPABILITY_AUTO_MERGE,
        name="disablePullRequestAutoMerge",
        input_type="DisablePullRequestAutoMergeInput",
        selection="pullRequest { id }",
    ),
    # Draft to ready and back.
    _mutation(
        capability=CAPABILITY_DRAFT,
        name="markPullRequestReadyForReview",
        input_type="MarkPullRequestReadyForReviewInput",
        selection="pullRequest { id isDraft }",
    ),
    _mutation(
        capability=CAPABILITY_DRAFT,
        name="convertPullRequestToDraft",
        input_type="ConvertPullRequestToDraftInput",
        selection="pullRequest { id isDraft }",
    ),
    # Review threads: a pull request's threads (a thread's ID is the mutations' threadId), then the mutations.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}PullRequest.reviewThreads",
        capability=CAPABILITY_REVIEW_THREADS,
        document=(
            "query($owner: String!, $name: String!, $number: Int!, $after: String) { "
            "repository(owner: $owner, name: $name) { pullRequest(number: $number) { "
            "reviewThreads(first: 100, after: $after) { nodes { id isResolved path } "
            "pageInfo { hasNextPage endCursor } } } } }"
        ),
        connection=("repository", "pullRequest", "reviewThreads"),
    ),
    _mutation(
        capability=CAPABILITY_REVIEW_THREADS,
        name="resolveReviewThread",
        input_type="ResolveReviewThreadInput",
        selection="thread { id isResolved }",
    ),
    _mutation(
        capability=CAPABILITY_REVIEW_THREADS,
        name="unresolveReviewThread",
        input_type="UnresolveReviewThreadInput",
        selection="thread { id isResolved }",
    ),
    # Hide comments.
    _mutation(
        capability=CAPABILITY_HIDE_COMMENTS,
        name="minimizeComment",
        input_type="MinimizeCommentInput",
        selection="minimizedComment { isMinimized minimizedReason }",
    ),
    _mutation(
        capability=CAPABILITY_HIDE_COMMENTS,
        name="unminimizeComment",
        input_type="UnminimizeCommentInput",
        selection="unminimizedComment { isMinimized }",
    ),
    # Moving an issue into another repository is refused (design D5).
    _mutation(
        capability=CAPABILITY_TRANSFER_ISSUE,
        name="transferIssue",
        input_type="TransferIssueInput",
        selection="issue { id number }",
    ),
    # Pin an issue.
    _mutation(
        capability=CAPABILITY_PIN_ISSUE,
        name="pinIssue",
        input_type="PinIssueInput",
        selection="issue { id }",
    ),
    _mutation(
        capability=CAPABILITY_PIN_ISSUE,
        name="unpinIssue",
        input_type="UnpinIssueInput",
        selection="issue { id }",
    ),
    # A revert commits to or creates a branch (requirements AC-3.1), so it is refused (design D5).
    _mutation(
        capability=CAPABILITY_REVERT,
        name="revertPullRequest",
        input_type="RevertPullRequestInput",
        selection="revertPullRequest { id number }",
    ),
    # The merge queue: its entries (a queued pull request's ID is dequeuePullRequest's id), then the removal.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Repository.mergeQueue",
        capability=CAPABILITY_MERGE_QUEUE,
        document=(
            "query($owner: String!, $name: String!, $branch: String, $after: String) { "
            "repository(owner: $owner, name: $name) { mergeQueue(branch: $branch) { "
            "entries(first: 100, after: $after) { nodes { id position state pullRequest { id number } } "
            "pageInfo { hasNextPage endCursor } } } } }"
        ),
        connection=("repository", "mergeQueue", "entries"),
    ),
    _mutation(
        capability=CAPABILITY_MERGE_QUEUE,
        name="dequeuePullRequest",
        input_type="DequeuePullRequestInput",
        selection="mergeQueueEntry { id }",
    ),
    # Sponsors.
    _mutation(
        capability=CAPABILITY_SPONSORS,
        name="createSponsorship",
        input_type="CreateSponsorshipInput",
        selection="sponsorship { id }",
    ),
    _mutation(
        capability=CAPABILITY_SPONSORS,
        name="createSponsorsTier",
        input_type="CreateSponsorsTierInput",
        selection="sponsorsTier { id }",
    ),
    # A commit to a branch is refused (requirements AC-3.1, design D5).
    _mutation(
        capability=CAPABILITY_MULTI_FILE_COMMIT,
        name="createCommitOnBranch",
        input_type="CreateCommitOnBranchInput",
        selection="commit { id }",
    ),
    # Branch protection with wildcard patterns.
    _mutation(
        capability=CAPABILITY_BRANCH_PROTECTION,
        name="createBranchProtectionRule",
        input_type="CreateBranchProtectionRuleInput",
        selection="branchProtectionRule { id }",
    ),
)

PENDING_CAPABILITIES: FrozenSet[str] = frozenset()
