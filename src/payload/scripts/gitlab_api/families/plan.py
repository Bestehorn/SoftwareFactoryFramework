"""The ``plan`` endpoint family of the GitLab wrapper: issues, notes, labels, boards, epics, milestones and wikis.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/plan.md``
(issue #13, design.md D1 and D5): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query
or body attribute with the table's Type column as its ``Kind``. The first seven records are part 1's, the ones the
``issue`` and ``label`` commands compose (design.md D6): ``issue list``, ``show``, ``create``, ``comment``, ``start``,
``claim-check``, ``release``, ``label-add``, ``label-remove``, ``assign``, ``close`` and ``reopen``; ``label list`` and
``label create``. The others, in page order, give every other section of the page, the deprecated epic APIs included,
a record that ``call`` sends (issue #39; issue #41, design.md D6 and D8):

- a row whose ``In`` is ``form`` is a ``Kind.FILE`` ``Param``, whatever its Type; otherwise a Type holding ``array`` is
  ``ARRAY``, ``Hash`` or ``object`` is ``HASH``, and any other is ``SCALAR``; ``required`` is the Required column's
  ``yes``;
- a member row (``not[labels]``) is a query ``Param`` of its own beside its hash (``not``), as part 1 declares it;
- the combined row ``issue_iid/merge_request_iid/snippet_id`` of the emoji sections is declared as the table writes it;
- a ``GET`` section whose heading begins with "List" or "Get all" is ``Paging.OFFSET``; no plan list is keyset-only.

A section with several endpoints has one record, on its first endpoint under ``/projects/:id/``; ``PENDING`` holds the
others (the merge-request and snippet endpoints of the four emoji resource sections, and the group endpoints of the two
notification settings sections) and the keys of ``plan#clone-an-issue``, which creates an issue, and
``plan#create-a-merge-request-note``, whose ``/merge`` quick action merges: no subcommand sends either, and ``call``
refuses only an ID that names its subcommand (issue #39, DL-003). ``plan#promote-an-issue-to-an-epic`` has no record of
its own: its key is the one ``plan#create-an-issue-note`` declares, sent with ``/promote`` as its ``body``. No other
family links any of these keys.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "plan"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Issues API: List all project issues"; offset paging (keyset is offered as well, so not KEYSET).
    RestOperation(
        operation_id="plan#list-all-project-issues",
        method="GET",
        path="/projects/:id/issues",
        params=(
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="due_date", location=Location.QUERY),
            Param(name="epic_id", location=Location.QUERY),
            # The table spells this integer array `iids[]`; the ARRAY kind writes that suffix, so the name omits it.
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="issue_type", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="cursor", location=Location.QUERY),
            Param(name="closed_by_id", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Issues API: Retrieve a project issue".
    RestOperation(
        operation_id="plan#retrieve-a-project-issue",
        method="GET",
        path="/projects/:id/issues/:issue_iid",
    ),
    # "Issues API: Create an issue".
    RestOperation(
        operation_id="plan#create-an-issue",
        method="POST",
        path="/projects/:id/issues",
        params=(
            Param(name="assignee_id", location=Location.BODY),
            Param(name="assignee_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="confidential", location=Location.BODY),
            Param(name="created_at", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="discussion_to_resolve", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="epic_id", location=Location.BODY),
            Param(name="epic_iid", location=Location.BODY),
            Param(name="iid", location=Location.BODY),
            Param(name="issue_type", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="merge_request_to_resolve_discussions_of", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="milestone", location=Location.BODY),
            Param(name="severity", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="weight", location=Location.BODY),
            Param(name="add_labels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="remove_labels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="discussion_locked", location=Location.BODY),
        ),
    ),
    # "Issues API: Update an issue"; here `add_labels` and `remove_labels` are comma-separated strings, and
    # `assignee_ids` an integer array in which `0` unassigns.
    RestOperation(
        operation_id="plan#update-an-issue",
        method="PUT",
        path="/projects/:id/issues/:issue_iid",
        params=(
            Param(name="add_labels", location=Location.BODY),
            Param(name="assignee_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="confidential", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="discussion_locked", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="epic_id", location=Location.BODY),
            Param(name="epic_iid", location=Location.BODY),
            Param(name="issue_type", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="milestone", location=Location.BODY),
            Param(name="remove_labels", location=Location.BODY),
            Param(name="severity", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
            Param(name="state_event", location=Location.BODY),
            Param(name="title", location=Location.BODY),
            Param(name="updated_at", location=Location.BODY),
            Param(name="weight", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Notes API: Create an issue note"; the index's other row on this key ("Issues API: Promote an issue to an
    # epic") is this request with `/promote` as its `body`.
    RestOperation(
        operation_id="plan#create-an-issue-note",
        method="POST",
        path="/projects/:id/issues/:issue_iid/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
            Param(name="internal", location=Location.BODY),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Project labels API: List all project labels".
    RestOperation(
        operation_id="plan#list-all-project-labels",
        method="GET",
        path="/projects/:id/labels",
        params=(
            Param(name="with_counts", location=Location.QUERY),
            Param(name="include_ancestor_groups", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="archived", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project labels API: Create a project label".
    RestOperation(
        operation_id="plan#create-a-project-label",
        method="POST",
        path="/projects/:id/labels",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="color", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="priority", location=Location.BODY),
            Param(name="archived", location=Location.BODY),
        ),
    ),
    # "Emoji reactions API: List all emoji reactions for a resource"; its other endpoints stay on PENDING (one record
    # per Reference).
    RestOperation(
        operation_id="plan#list-all-emoji-reactions-for-a-resource",
        method="GET",
        path="/projects/:id/issues/:issue_iid/award_emoji",
        params=(
            Param(name="issue_iid/merge_request_iid/snippet_id", location=Location.QUERY, required=True),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Emoji reactions API: Retrieve an emoji reaction from a resource"; its other endpoints stay on PENDING (one record
    # per Reference).
    RestOperation(
        operation_id="plan#retrieve-an-emoji-reaction-from-a-resource",
        method="GET",
        path="/projects/:id/issues/:issue_iid/award_emoji/:award_id",
        params=(Param(name="issue_iid/merge_request_iid/snippet_id", location=Location.QUERY, required=True),),
    ),
    # "Emoji reactions API: Add an emoji reaction to a resource"; its other endpoints stay on PENDING (one record per
    # Reference).
    RestOperation(
        operation_id="plan#add-an-emoji-reaction-to-a-resource",
        method="POST",
        path="/projects/:id/issues/:issue_iid/award_emoji",
        params=(
            Param(name="issue_iid/merge_request_iid/snippet_id", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
        ),
    ),
    # "Emoji reactions API: Delete an emoji reaction from a resource"; its other endpoints stay on PENDING (one record
    # per Reference).
    RestOperation(
        operation_id="plan#delete-an-emoji-reaction-from-a-resource",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/award_emoji/:award_id",
        params=(Param(name="issue_iid/merge_request_iid/snippet_id", location=Location.QUERY, required=True),),
    ),
    # "Emoji reactions API: List all emoji reactions for a comment".
    RestOperation(
        operation_id="plan#list-all-emoji-reactions-for-a-comment",
        method="GET",
        path="/projects/:id/issues/:issue_iid/notes/:note_id/award_emoji",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Emoji reactions API: Retrieve an emoji reaction from a comment".
    RestOperation(
        operation_id="plan#retrieve-an-emoji-reaction-from-a-comment",
        method="GET",
        path="/projects/:id/issues/:issue_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "Emoji reactions API: Add an emoji reaction to a comment".
    RestOperation(
        operation_id="plan#add-an-emoji-reaction-to-a-comment",
        method="POST",
        path="/projects/:id/issues/:issue_iid/notes/:note_id/award_emoji",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "Emoji reactions API: Delete an emoji reaction from a comment".
    RestOperation(
        operation_id="plan#delete-an-emoji-reaction-from-a-comment",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "Epic Issues API (deprecated): List all issues for an epic".
    RestOperation(
        operation_id="plan#list-all-issues-for-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid/issues",
        paging=Paging.OFFSET,
    ),
    # "Epic Issues API (deprecated): Assign an issue to an epic".
    RestOperation(
        operation_id="plan#assign-an-issue-to-an-epic",
        method="POST",
        path="/groups/:id/epics/:epic_iid/issues/:issue_id",
    ),
    # "Epic Issues API (deprecated): Remove an issue from an epic".
    RestOperation(
        operation_id="plan#remove-an-issue-from-an-epic",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid/issues/:epic_issue_id",
    ),
    # "Epic Issues API (deprecated): Update an epic-issue association".
    RestOperation(
        operation_id="plan#update-an-epic-issue-association",
        method="PUT",
        path="/groups/:id/epics/:epic_iid/issues/:epic_issue_id",
        params=(
            Param(name="move_before_id", location=Location.BODY),
            Param(name="move_after_id", location=Location.BODY),
        ),
    ),
    # "Epic Links API (deprecated): List all child epics of an epic".
    RestOperation(
        operation_id="plan#list-all-child-epics-of-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid/epics",
        paging=Paging.OFFSET,
    ),
    # "Epic Links API (deprecated): Assign a child epic".
    RestOperation(
        operation_id="plan#assign-a-child-epic",
        method="POST",
        path="/groups/:id/epics/:epic_iid/epics/:child_epic_id",
    ),
    # "Epic Links API (deprecated): Create and assign a child epic".
    RestOperation(
        operation_id="plan#create-and-assign-a-child-epic",
        method="POST",
        path="/groups/:id/epics/:epic_iid/epics",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
        ),
    ),
    # "Epic Links API (deprecated): Re-order a child epic".
    RestOperation(
        operation_id="plan#re-order-a-child-epic",
        method="PUT",
        path="/groups/:id/epics/:epic_iid/epics/:child_epic_id",
        params=(
            Param(name="move_before_id", location=Location.BODY),
            Param(name="move_after_id", location=Location.BODY),
        ),
    ),
    # "Epic Links API (deprecated): Unassign a child epic".
    RestOperation(
        operation_id="plan#unassign-a-child-epic",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid/epics/:child_epic_id",
    ),
    # "Epics API (deprecated): List all group epics".
    RestOperation(
        operation_id="plan#list-all-group-epics",
        method="GET",
        path="/groups/:id/epics",
        params=(
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="include_ancestor_groups", location=Location.QUERY),
            Param(name="include_descendant_groups", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
        ),
        paging=Paging.OFFSET,
    ),
    # "Epics API (deprecated): Retrieve an epic".
    RestOperation(
        operation_id="plan#retrieve-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid",
    ),
    # "Epics API (deprecated): Create an epic".
    RestOperation(
        operation_id="plan#create-an-epic",
        method="POST",
        path="/groups/:id/epics",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="labels", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="color", location=Location.BODY),
            Param(name="confidential", location=Location.BODY),
            Param(name="created_at", location=Location.BODY),
            Param(name="start_date_is_fixed", location=Location.BODY),
            Param(name="start_date_fixed", location=Location.BODY),
            Param(name="due_date_is_fixed", location=Location.BODY),
            Param(name="due_date_fixed", location=Location.BODY),
            Param(name="parent_id", location=Location.BODY),
        ),
    ),
    # "Epics API (deprecated): Update an epic".
    RestOperation(
        operation_id="plan#update-an-epic",
        method="PUT",
        path="/groups/:id/epics/:epic_iid",
        params=(
            Param(name="add_labels", location=Location.BODY),
            Param(name="confidential", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="due_date_fixed", location=Location.BODY),
            Param(name="due_date_is_fixed", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="parent_id", location=Location.BODY),
            Param(name="remove_labels", location=Location.BODY),
            Param(name="start_date_fixed", location=Location.BODY),
            Param(name="start_date_is_fixed", location=Location.BODY),
            Param(name="state_event", location=Location.BODY),
            Param(name="title", location=Location.BODY),
            Param(name="updated_at", location=Location.BODY),
            Param(name="color", location=Location.BODY),
        ),
    ),
    # "Epics API (deprecated): Delete an epic".
    RestOperation(
        operation_id="plan#delete-an-epic",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid",
    ),
    # "Epics API (deprecated): Create a to-do item for an epic".
    RestOperation(
        operation_id="plan#create-a-to-do-item-for-an-epic",
        method="POST",
        path="/groups/:id/epics/:epic_iid/todo",
    ),
    # "GitLab To-Do List API: List all to-do items".
    RestOperation(
        operation_id="plan#list-all-to-do-items",
        method="GET",
        path="/todos",
        params=(
            Param(name="action", location=Location.QUERY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="project_id", location=Location.QUERY),
            Param(name="group_id", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="type", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "GitLab To-Do List API: Mark a to-do item as done".
    RestOperation(
        operation_id="plan#mark-a-to-do-item-as-done",
        method="POST",
        path="/todos/:id/mark_as_done",
    ),
    # "GitLab To-Do List API: Mark all to-do items as done".
    RestOperation(
        operation_id="plan#mark-all-to-do-items-as-done",
        method="POST",
        path="/todos/mark_as_done",
    ),
    # "GLQL API: Execute a GLQL query".
    RestOperation(
        operation_id="plan#execute-a-glql-query",
        method="POST",
        path="/glql",
        params=(
            Param(name="glql_yaml", location=Location.BODY, required=True),
            Param(name="after", location=Location.BODY),
            Param(name="fields", location=Location.BODY),
            Param(name="group", location=Location.BODY),
            Param(name="limit", location=Location.BODY),
            Param(name="project", location=Location.BODY),
            Param(name="sort", location=Location.BODY),
        ),
    ),
    # "GLQL API: Retrieve the GLQL schema".
    RestOperation(
        operation_id="plan#retrieve-the-glql-schema",
        method="GET",
        path="/glql/schema",
    ),
    # "Group epic boards API: List all epic boards in a group".
    RestOperation(
        operation_id="plan#list-all-epic-boards-in-a-group",
        method="GET",
        path="/groups/:id/epic_boards",
        paging=Paging.OFFSET,
    ),
    # "Group epic boards API: Retrieve a group epic board".
    RestOperation(
        operation_id="plan#retrieve-a-group-epic-board",
        method="GET",
        path="/groups/:id/epic_boards/:board_id",
    ),
    # "Group epic boards API: List group epic board lists".
    RestOperation(
        operation_id="plan#list-group-epic-board-lists",
        method="GET",
        path="/groups/:id/epic_boards/:board_id/lists",
        paging=Paging.OFFSET,
    ),
    # "Group epic boards API: Retrieve a group epic board list".
    RestOperation(
        operation_id="plan#retrieve-a-group-epic-board-list",
        method="GET",
        path="/groups/:id/epic_boards/:board_id/lists/:list_id",
    ),
    # "Group issue boards API: List all group issue boards in a group".
    RestOperation(
        operation_id="plan#list-all-group-issue-boards-in-a-group",
        method="GET",
        path="/groups/:id/boards",
        paging=Paging.OFFSET,
    ),
    # "Group issue boards API: Retrieve a group issue board".
    RestOperation(
        operation_id="plan#retrieve-a-group-issue-board",
        method="GET",
        path="/groups/:id/boards/:board_id",
    ),
    # "Group issue boards API: Create a group issue board".
    RestOperation(
        operation_id="plan#create-a-group-issue-board",
        method="POST",
        path="/groups/:id/boards",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "Group issue boards API: Update a group issue board".
    RestOperation(
        operation_id="plan#update-a-group-issue-board",
        method="PUT",
        path="/groups/:id/boards/:board_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="hide_backlog_list", location=Location.BODY),
            Param(name="hide_closed_list", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="weight", location=Location.BODY),
        ),
    ),
    # "Group issue boards API: Delete a group issue board".
    RestOperation(
        operation_id="plan#delete-a-group-issue-board",
        method="DELETE",
        path="/groups/:id/boards/:board_id",
    ),
    # "Group issue boards API: List group issue board lists".
    RestOperation(
        operation_id="plan#list-group-issue-board-lists",
        method="GET",
        path="/groups/:id/boards/:board_id/lists",
        paging=Paging.OFFSET,
    ),
    # "Group issue boards API: Retrieve a group issue board list".
    RestOperation(
        operation_id="plan#retrieve-a-group-issue-board-list",
        method="GET",
        path="/groups/:id/boards/:board_id/lists/:list_id",
    ),
    # "Group issue boards API: Create a group issue board list".
    RestOperation(
        operation_id="plan#create-a-group-issue-board-list",
        method="POST",
        path="/groups/:id/boards/:board_id/lists",
        params=(
            Param(name="label_id", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="iteration_id", location=Location.BODY),
            Param(name="status_id", location=Location.BODY),
        ),
    ),
    # "Group issue boards API: Update a group issue board list".
    RestOperation(
        operation_id="plan#update-a-group-issue-board-list",
        method="PUT",
        path="/groups/:id/boards/:board_id/lists/:list_id",
        params=(Param(name="position", location=Location.BODY, required=True),),
    ),
    # "Group issue boards API: Delete a group issue board list".
    RestOperation(
        operation_id="plan#delete-a-group-issue-board-list",
        method="DELETE",
        path="/groups/:id/boards/:board_id/lists/:list_id",
    ),
    # "Group iterations API: List all group iterations".
    RestOperation(
        operation_id="plan#list-all-group-iterations",
        method="GET",
        path="/groups/:id/iterations",
        params=(
            Param(name="state", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="in", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="include_ancestors", location=Location.QUERY),
            Param(name="include_descendants", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group labels API: List group labels".
    RestOperation(
        operation_id="plan#list-group-labels",
        method="GET",
        path="/groups/:id/labels",
        params=(
            Param(name="with_counts", location=Location.QUERY),
            Param(name="include_ancestor_groups", location=Location.QUERY),
            Param(name="include_descendant_groups", location=Location.QUERY),
            Param(name="only_group_labels", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="archived", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group labels API: Get a single group label".
    RestOperation(
        operation_id="plan#get-a-single-group-label",
        method="GET",
        path="/groups/:id/labels/:label_id",
        params=(
            Param(name="include_ancestor_groups", location=Location.QUERY),
            Param(name="include_descendant_groups", location=Location.QUERY),
            Param(name="only_group_labels", location=Location.QUERY),
        ),
    ),
    # "Group labels API: Create a new group label".
    RestOperation(
        operation_id="plan#create-a-new-group-label",
        method="POST",
        path="/groups/:id/labels",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="color", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="archived", location=Location.BODY),
        ),
    ),
    # "Group labels API: Update a group label".
    RestOperation(
        operation_id="plan#update-a-group-label",
        method="PUT",
        path="/groups/:id/labels/:label_id",
        params=(
            Param(name="new_name", location=Location.BODY),
            Param(name="color", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="archived", location=Location.BODY),
        ),
    ),
    # "Group labels API: Delete a group label".
    RestOperation(
        operation_id="plan#delete-a-group-label",
        method="DELETE",
        path="/groups/:id/labels/:label_id",
    ),
    # "Group labels API: Subscribe to a group label".
    RestOperation(
        operation_id="plan#subscribe-to-a-group-label",
        method="POST",
        path="/groups/:id/labels/:label_id/subscribe",
    ),
    # "Group labels API: Unsubscribe from a group label".
    RestOperation(
        operation_id="plan#unsubscribe-from-a-group-label",
        method="POST",
        path="/groups/:id/labels/:label_id/unsubscribe",
    ),
    # "Group Markdown uploads API: Upload a file to a group".
    RestOperation(
        operation_id="plan#upload-a-file-to-a-group",
        method="POST",
        path="/groups/:id/uploads",
        params=(Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "Group Markdown uploads API: List all uploads for a group".
    RestOperation(
        operation_id="plan#list-all-uploads-for-a-group",
        method="GET",
        path="/groups/:id/uploads",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group Markdown uploads API: Download an uploaded file by ID".
    RestOperation(
        operation_id="plan#download-an-uploaded-file-by-id",
        method="GET",
        path="/groups/:id/uploads/:upload_id",
    ),
    # "Group Markdown uploads API: Download an uploaded file by secret and filename".
    RestOperation(
        operation_id="plan#download-an-uploaded-file-by-secret-and-filename",
        method="GET",
        path="/groups/:id/uploads/:secret/:filename",
    ),
    # "Group Markdown uploads API: Delete an uploaded file by ID".
    RestOperation(
        operation_id="plan#delete-an-uploaded-file-by-id",
        method="DELETE",
        path="/groups/:id/uploads/:upload_id",
    ),
    # "Group Markdown uploads API: Delete an uploaded file by secret and filename".
    RestOperation(
        operation_id="plan#delete-an-uploaded-file-by-secret-and-filename",
        method="DELETE",
        path="/groups/:id/uploads/:secret/:filename",
    ),
    # "Group milestones API: List group milestones".
    RestOperation(
        operation_id="plan#list-group-milestones",
        method="GET",
        path="/groups/:id/milestones",
        params=(
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="state", location=Location.QUERY),
            Param(name="title", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="search_title", location=Location.QUERY),
            Param(name="include_parent_milestones", location=Location.QUERY),
            Param(name="include_ancestors", location=Location.QUERY),
            Param(name="include_descendants", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="containing_date", location=Location.QUERY),
            Param(name="start_date", location=Location.QUERY),
            Param(name="end_date", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group milestones API: Get single milestone".
    RestOperation(
        operation_id="plan#get-single-milestone",
        method="GET",
        path="/groups/:id/milestones/:milestone_id",
    ),
    # "Group milestones API: Create new milestone".
    RestOperation(
        operation_id="plan#create-new-milestone",
        method="POST",
        path="/groups/:id/milestones",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
        ),
    ),
    # "Group milestones API: Edit milestone".
    RestOperation(
        operation_id="plan#edit-milestone",
        method="PUT",
        path="/groups/:id/milestones/:milestone_id",
        params=(
            Param(name="title", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
            Param(name="state_event", location=Location.BODY),
        ),
    ),
    # "Group milestones API: Delete group milestone".
    RestOperation(
        operation_id="plan#delete-group-milestone",
        method="DELETE",
        path="/groups/:id/milestones/:milestone_id",
    ),
    # "Group milestones API: Get all issues assigned to a single milestone".
    RestOperation(
        operation_id="plan#get-all-issues-assigned-to-a-single-milestone",
        method="GET",
        path="/groups/:id/milestones/:milestone_id/issues",
        paging=Paging.OFFSET,
    ),
    # "Group milestones API: Get all merge requests assigned to a single milestone".
    RestOperation(
        operation_id="plan#get-all-merge-requests-assigned-to-a-single-milestone",
        method="GET",
        path="/groups/:id/milestones/:milestone_id/merge_requests",
        paging=Paging.OFFSET,
    ),
    # "Group milestones API: Get all burndown chart events for a single milestone".
    RestOperation(
        operation_id="plan#get-all-burndown-chart-events-for-a-single-milestone",
        method="GET",
        path="/groups/:id/milestones/:milestone_id/burndown_events",
        paging=Paging.OFFSET,
    ),
    # "Group wikis API: List wiki pages".
    RestOperation(
        operation_id="plan#list-wiki-pages",
        method="GET",
        path="/groups/:id/wikis",
        params=(Param(name="with_content", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Group wikis API: Retrieve a wiki page".
    RestOperation(
        operation_id="plan#retrieve-a-wiki-page",
        method="GET",
        path="/groups/:id/wikis/:slug",
        params=(
            Param(name="render_html", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
        ),
    ),
    # "Group wikis API: Create a wiki page".
    RestOperation(
        operation_id="plan#create-a-wiki-page",
        method="POST",
        path="/groups/:id/wikis",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="format", location=Location.BODY),
            Param(name="front_matter", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Group wikis API: Update a wiki page".
    RestOperation(
        operation_id="plan#update-a-wiki-page",
        method="PUT",
        path="/groups/:id/wikis/:slug",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="format", location=Location.BODY),
            Param(name="front_matter", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Group wikis API: Delete a wiki page".
    RestOperation(
        operation_id="plan#delete-a-wiki-page",
        method="DELETE",
        path="/groups/:id/wikis/:slug",
    ),
    # "Group wikis API: Upload an attachment to the wiki repository".
    RestOperation(
        operation_id="plan#upload-an-attachment-to-the-wiki-repository",
        method="POST",
        path="/groups/:id/wikis/attachments",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="branch", location=Location.BODY),
        ),
    ),
    # "Issue links API: List all issue links".
    RestOperation(
        operation_id="plan#list-all-issue-links",
        method="GET",
        path="/projects/:id/issues/:issue_iid/links",
        paging=Paging.OFFSET,
    ),
    # "Issue links API: Retrieve an issue link".
    RestOperation(
        operation_id="plan#retrieve-an-issue-link",
        method="GET",
        path="/projects/:id/issues/:issue_iid/links/:issue_link_id",
    ),
    # "Issue links API: Create an issue link".
    RestOperation(
        operation_id="plan#create-an-issue-link",
        method="POST",
        path="/projects/:id/issues/:issue_iid/links",
        params=(
            Param(name="target_project_id", location=Location.BODY, required=True),
            Param(name="target_issue_iid", location=Location.BODY, required=True),
            Param(name="link_type", location=Location.BODY),
        ),
    ),
    # "Issue links API: Delete an issue link".
    RestOperation(
        operation_id="plan#delete-an-issue-link",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/links/:issue_link_id",
        params=(Param(name="link_type", location=Location.QUERY),),
    ),
    # "Issues API: List all issues".
    RestOperation(
        operation_id="plan#list-all-issues",
        method="GET",
        path="/issues",
        params=(
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="due_date", location=Location.QUERY),
            Param(name="epic_id", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="in", location=Location.QUERY),
            Param(name="issue_type", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="non_archived", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="closed_by_id", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Issues API: List all group issues".
    RestOperation(
        operation_id="plan#list-all-group-issues",
        method="GET",
        path="/groups/:id/issues",
        params=(
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="due_date", location=Location.QUERY),
            Param(name="epic_id", location=Location.QUERY),
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="issue_type", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="non_archived", location=Location.QUERY),
            Param(name="not", location=Location.QUERY, kind=Kind.HASH),
            Param(name="order_by", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="closed_by_id", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Issues API: Retrieve an issue".
    RestOperation(
        operation_id="plan#retrieve-an-issue",
        method="GET",
        path="/issues/:id",
    ),
    # "Issues API: Delete an issue".
    RestOperation(
        operation_id="plan#delete-an-issue",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid",
    ),
    # "Issues API: Reorder an issue".
    RestOperation(
        operation_id="plan#reorder-an-issue",
        method="PUT",
        path="/projects/:id/issues/:issue_iid/reorder",
        params=(
            Param(name="move_after_id", location=Location.BODY),
            Param(name="move_before_id", location=Location.BODY),
        ),
    ),
    # "Issues API: Move an issue".
    RestOperation(
        operation_id="plan#move-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/move",
        params=(Param(name="to_project_id", location=Location.BODY, required=True),),
    ),
    # "Issues API: Subscribe to an issue".
    RestOperation(
        operation_id="plan#subscribe-to-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/subscribe",
    ),
    # "Issues API: Unsubscribe from an issue".
    RestOperation(
        operation_id="plan#unsubscribe-from-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/unsubscribe",
    ),
    # "Issues API: Create a to-do item for an issue".
    RestOperation(
        operation_id="plan#create-a-to-do-item-for-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/todo",
    ),
    # "Issues API: Set a time estimate for an issue".
    RestOperation(
        operation_id="plan#set-a-time-estimate-for-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/time_estimate",
        params=(Param(name="duration", location=Location.BODY, required=True),),
    ),
    # "Issues API: Reset the time estimate for an issue".
    RestOperation(
        operation_id="plan#reset-the-time-estimate-for-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/reset_time_estimate",
    ),
    # "Issues API: Add spent time for an issue".
    RestOperation(
        operation_id="plan#add-spent-time-for-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/add_spent_time",
        params=(
            Param(name="duration", location=Location.BODY, required=True),
            Param(name="summary", location=Location.BODY),
        ),
    ),
    # "Issues API: Reset spent time for an issue".
    RestOperation(
        operation_id="plan#reset-spent-time-for-an-issue",
        method="POST",
        path="/projects/:id/issues/:issue_iid/reset_spent_time",
    ),
    # "Issues API: Retrieve time tracking stats for an issue".
    RestOperation(
        operation_id="plan#retrieve-time-tracking-stats-for-an-issue",
        method="GET",
        path="/projects/:id/issues/:issue_iid/time_stats",
    ),
    # "Issues API: List all merge requests related to an issue".
    RestOperation(
        operation_id="plan#list-all-merge-requests-related-to-an-issue",
        method="GET",
        path="/projects/:id/issues/:issue_iid/related_merge_requests",
        paging=Paging.OFFSET,
    ),
    # "Issues API: List all merge requests that close an issue on merge".
    RestOperation(
        operation_id="plan#list-all-merge-requests-that-close-an-issue-on-merge",
        method="GET",
        path="/projects/:id/issues/:issue_iid/closed_by",
        paging=Paging.OFFSET,
    ),
    # "Issues API: List all participants in an issue".
    RestOperation(
        operation_id="plan#list-all-participants-in-an-issue",
        method="GET",
        path="/projects/:id/issues/:issue_iid/participants",
        paging=Paging.OFFSET,
    ),
    # "Issues API: Retrieve user agent details for an issue".
    RestOperation(
        operation_id="plan#retrieve-user-agent-details-for-an-issue",
        method="GET",
        path="/projects/:id/issues/:issue_iid/user_agent_detail",
    ),
    # "Issues API: Upload a metric image for an incident".
    RestOperation(
        operation_id="plan#upload-a-metric-image-for-an-incident",
        method="POST",
        path="/projects/:id/issues/:issue_iid/metric_images",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="url", location=Location.BODY),
            Param(name="url_text", location=Location.BODY),
        ),
    ),
    # "Issues API: List all metric images for an incident".
    RestOperation(
        operation_id="plan#list-all-metric-images-for-an-incident",
        method="GET",
        path="/projects/:id/issues/:issue_iid/metric_images",
        paging=Paging.OFFSET,
    ),
    # "Issues API: Update a metric image for an incident".
    RestOperation(
        operation_id="plan#update-a-metric-image-for-an-incident",
        method="PUT",
        path="/projects/:id/issues/:issue_iid/metric_images/:image_id",
        params=(
            Param(name="url", location=Location.BODY),
            Param(name="url_text", location=Location.BODY),
        ),
    ),
    # "Issues API: Delete a metric image from an incident".
    RestOperation(
        operation_id="plan#delete-a-metric-image-from-an-incident",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/metric_images/:image_id",
    ),
    # "Issues statistics API: Retrieve issues statistics for a user".
    RestOperation(
        operation_id="plan#retrieve-issues-statistics-for-a-user",
        method="GET",
        path="/issues_statistics",
        params=(
            Param(name="labels", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="epic_id", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="search", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
        ),
    ),
    # "Issues statistics API: Retrieve issues statistics for a group".
    RestOperation(
        operation_id="plan#retrieve-issues-statistics-for-a-group",
        method="GET",
        path="/groups/:id/issues_statistics",
        params=(
            Param(name="labels", location=Location.QUERY),
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="epic_id", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
        ),
    ),
    # "Issues statistics API: Retrieve issues statistics for a project".
    RestOperation(
        operation_id="plan#retrieve-issues-statistics-for-a-project",
        method="GET",
        path="/projects/:id/issues_statistics",
        params=(
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="labels", location=Location.QUERY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="milestone_id", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[milestone_id]", location=Location.QUERY),
            Param(name="not[iids]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[weight]", location=Location.QUERY),
            Param(name="not[iteration_id]", location=Location.QUERY),
            Param(name="not[iteration_title]", location=Location.QUERY),
            Param(name="weight", location=Location.QUERY),
            Param(name="epic_id", location=Location.QUERY),
            Param(name="health_status", location=Location.QUERY),
            Param(name="iteration_id", location=Location.QUERY),
            Param(name="iteration_title", location=Location.QUERY),
        ),
    ),
    # "Linked epics API (deprecated): List all related epic links for a group".
    RestOperation(
        operation_id="plan#list-all-related-epic-links-for-a-group",
        method="GET",
        path="/groups/:id/related_epic_links",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Linked epics API (deprecated): List all linked epics for an epic".
    RestOperation(
        operation_id="plan#list-all-linked-epics-for-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid/related_epics",
        paging=Paging.OFFSET,
    ),
    # "Linked epics API (deprecated): Create a related epic link".
    RestOperation(
        operation_id="plan#create-a-related-epic-link",
        method="POST",
        path="/groups/:id/epics/:epic_iid/related_epics",
        params=(
            Param(name="target_epic_iid", location=Location.BODY, required=True),
            Param(name="target_group_id", location=Location.BODY, required=True),
            Param(name="link_type", location=Location.BODY),
        ),
    ),
    # "Linked epics API (deprecated): Delete a related epic link".
    RestOperation(
        operation_id="plan#delete-a-related-epic-link",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid/related_epics/:related_epic_link_id",
    ),
    # "Markdown API: Render Markdown content".
    RestOperation(
        operation_id="plan#render-markdown-content",
        method="POST",
        path="/markdown",
        params=(
            Param(name="text", location=Location.BODY, required=True),
            Param(name="gfm", location=Location.BODY),
            Param(name="project", location=Location.BODY),
        ),
    ),
    # "Markdown uploads API: Create an upload".
    RestOperation(
        operation_id="plan#create-an-upload",
        method="POST",
        path="/projects/:id/uploads",
        params=(Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "Markdown uploads API: List uploads".
    RestOperation(
        operation_id="plan#list-uploads",
        method="GET",
        path="/projects/:id/uploads",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Markdown uploads API: Download an uploaded file by ID".
    RestOperation(
        operation_id="plan#download-an-uploaded-file-by-id-1",
        method="GET",
        path="/projects/:id/uploads/:upload_id",
    ),
    # "Markdown uploads API: Download an uploaded file by secret and filename".
    RestOperation(
        operation_id="plan#download-an-uploaded-file-by-secret-and-filename-1",
        method="GET",
        path="/projects/:id/uploads/:secret/:filename",
    ),
    # "Markdown uploads API: Delete an uploaded file by ID".
    RestOperation(
        operation_id="plan#delete-an-uploaded-file-by-id-1",
        method="DELETE",
        path="/projects/:id/uploads/:upload_id",
    ),
    # "Markdown uploads API: Delete an uploaded file by secret and filename".
    RestOperation(
        operation_id="plan#delete-an-uploaded-file-by-secret-and-filename-1",
        method="DELETE",
        path="/projects/:id/uploads/:secret/:filename",
    ),
    # "Mobile push subscriptions API: Register a device".
    RestOperation(
        operation_id="plan#register-a-device",
        method="POST",
        path="/user/push_subscriptions",
        params=(
            Param(name="device_token", location=Location.BODY, required=True),
            Param(name="platform", location=Location.BODY),
            Param(name="apns_environment", location=Location.BODY),
            Param(name="bundle_id", location=Location.BODY),
            Param(name="device_name", location=Location.BODY),
            Param(name="app_version", location=Location.BODY),
            Param(name="locale", location=Location.BODY),
            Param(name="payload_mode", location=Location.BODY),
        ),
    ),
    # "Mobile push subscriptions API: Unregister a device".
    RestOperation(
        operation_id="plan#unregister-a-device",
        method="DELETE",
        path="/user/push_subscriptions",
        params=(Param(name="device_token", location=Location.QUERY, required=True),),
    ),
    # "Notes API: List all issue notes".
    RestOperation(
        operation_id="plan#list-all-issue-notes",
        method="GET",
        path="/projects/:id/issues/:issue_iid/notes",
        params=(
            Param(name="activity_filter", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve an issue note".
    RestOperation(
        operation_id="plan#retrieve-an-issue-note",
        method="GET",
        path="/projects/:id/issues/:issue_iid/notes/:note_id",
    ),
    # "Notes API: Update an issue note".
    RestOperation(
        operation_id="plan#update-an-issue-note",
        method="PUT",
        path="/projects/:id/issues/:issue_iid/notes/:note_id",
        params=(
            Param(name="body", location=Location.BODY),
            Param(name="confidential", location=Location.BODY),
        ),
    ),
    # "Notes API: Delete an issue note".
    RestOperation(
        operation_id="plan#delete-an-issue-note",
        method="DELETE",
        path="/projects/:id/issues/:issue_iid/notes/:note_id",
    ),
    # "Notes API: List all snippet notes".
    RestOperation(
        operation_id="plan#list-all-snippet-notes",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/notes",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve a snippet note".
    RestOperation(
        operation_id="plan#retrieve-a-snippet-note",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id",
    ),
    # "Notes API: Create a snippet note".
    RestOperation(
        operation_id="plan#create-a-snippet-note",
        method="POST",
        path="/projects/:id/snippets/:snippet_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="created_at", location=Location.BODY),
        ),
    ),
    # "Notes API: Update a snippet note".
    RestOperation(
        operation_id="plan#update-a-snippet-note",
        method="PUT",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Notes API: Delete a snippet note".
    RestOperation(
        operation_id="plan#delete-a-snippet-note",
        method="DELETE",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id",
    ),
    # "Notes API: List all merge request notes".
    RestOperation(
        operation_id="plan#list-all-merge-request-notes",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/notes",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve a merge request note".
    RestOperation(
        operation_id="plan#retrieve-a-merge-request-note",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id",
    ),
    # "Notes API: Update a merge request note".
    RestOperation(
        operation_id="plan#update-a-merge-request-note",
        method="PUT",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
        ),
    ),
    # "Notes API: Delete a merge request note".
    RestOperation(
        operation_id="plan#delete-a-merge-request-note",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id",
    ),
    # "Notes API: List all epic notes".
    RestOperation(
        operation_id="plan#list-all-epic-notes",
        method="GET",
        path="/groups/:id/epics/:epic_id/notes",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve an epic note".
    RestOperation(
        operation_id="plan#retrieve-an-epic-note",
        method="GET",
        path="/groups/:id/epics/:epic_id/notes/:note_id",
    ),
    # "Notes API: Create an epic note".
    RestOperation(
        operation_id="plan#create-an-epic-note",
        method="POST",
        path="/groups/:id/epics/:epic_id/notes",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
            Param(name="internal", location=Location.BODY),
        ),
    ),
    # "Notes API: Update an epic note".
    RestOperation(
        operation_id="plan#update-an-epic-note",
        method="PUT",
        path="/groups/:id/epics/:epic_id/notes/:note_id",
        params=(
            Param(name="body", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
        ),
    ),
    # "Notes API: Delete an epic note".
    RestOperation(
        operation_id="plan#delete-an-epic-note",
        method="DELETE",
        path="/groups/:id/epics/:epic_id/notes/:note_id",
    ),
    # "Notes API: List all project wiki notes".
    RestOperation(
        operation_id="plan#list-all-project-wiki-notes",
        method="GET",
        path="/projects/:id/wiki_pages/:wiki_page_meta_id/notes",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve a wiki page note".
    RestOperation(
        operation_id="plan#retrieve-a-wiki-page-note",
        method="GET",
        path="/projects/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
    ),
    # "Notes API: Create a wiki page note".
    RestOperation(
        operation_id="plan#create-a-wiki-page-note",
        method="POST",
        path="/projects/:id/wiki_pages/:wiki_page_meta_id/notes",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Notes API: Update a wiki page note".
    RestOperation(
        operation_id="plan#update-a-wiki-page-note",
        method="PUT",
        path="/projects/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Notes API: Delete a wiki page note".
    RestOperation(
        operation_id="plan#delete-a-wiki-page-note",
        method="DELETE",
        path="/projects/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
    ),
    # "Notes API: List group wiki notes".
    RestOperation(
        operation_id="plan#list-group-wiki-notes",
        method="GET",
        path="/groups/:id/wiki_pages/:wiki_page_meta_id/notes",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Notes API: Retrieve a wiki page note".
    RestOperation(
        operation_id="plan#retrieve-a-wiki-page-note-1",
        method="GET",
        path="/groups/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
    ),
    # "Notes API: Create a wiki page note".
    RestOperation(
        operation_id="plan#create-a-wiki-page-note-1",
        method="POST",
        path="/groups/:id/wiki_pages/:wiki_page_meta_id/notes",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Notes API: Update a wiki page note".
    RestOperation(
        operation_id="plan#update-a-wiki-page-note-1",
        method="PUT",
        path="/groups/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
        params=(Param(name="body", location=Location.BODY, required=True),),
    ),
    # "Notes API: Delete a wiki page note".
    RestOperation(
        operation_id="plan#delete-a-wiki-page-note-1",
        method="DELETE",
        path="/groups/:id/wiki_pages/:wiki_page_meta_id/notes/:note_id",
    ),
    # "Notification settings API: Retrieve global notification settings".
    RestOperation(
        operation_id="plan#retrieve-global-notification-settings",
        method="GET",
        path="/notification_settings",
    ),
    # "Notification settings API: Update global notification settings".
    RestOperation(
        operation_id="plan#update-global-notification-settings",
        method="PUT",
        path="/notification_settings",
        params=(
            Param(name="approver", location=Location.BODY),
            Param(name="change_reviewer_merge_request", location=Location.BODY),
            Param(name="close_issue", location=Location.BODY),
            Param(name="close_merge_request", location=Location.BODY),
            Param(name="failed_pipeline", location=Location.BODY),
            Param(name="fixed_pipeline", location=Location.BODY),
            Param(name="issue_due", location=Location.BODY),
            Param(name="level", location=Location.BODY),
            Param(name="merge_merge_request", location=Location.BODY),
            Param(name="merge_when_pipeline_succeeds", location=Location.BODY),
            Param(name="moved_project", location=Location.BODY),
            Param(name="new_epic", location=Location.BODY),
            Param(name="new_issue", location=Location.BODY),
            Param(name="new_merge_request", location=Location.BODY),
            Param(name="new_note", location=Location.BODY),
            Param(name="new_release", location=Location.BODY),
            Param(name="notification_email", location=Location.BODY),
            Param(name="push_to_merge_request", location=Location.BODY),
            Param(name="reassign_issue", location=Location.BODY),
            Param(name="reassign_merge_request", location=Location.BODY),
            Param(name="reopen_issue", location=Location.BODY),
            Param(name="reopen_merge_request", location=Location.BODY),
            Param(name="success_pipeline", location=Location.BODY),
        ),
    ),
    # "Notification settings API: Retrieve notification settings"; its other endpoints stay on PENDING (one record per
    # Reference).
    RestOperation(
        operation_id="plan#retrieve-notification-settings",
        method="GET",
        path="/projects/:id/notification_settings",
    ),
    # "Notification settings API: Update group or project notification settings"; its other endpoints stay on PENDING
    # (one record per Reference).
    RestOperation(
        operation_id="plan#update-group-or-project-notification-settings",
        method="PUT",
        path="/projects/:id/notification_settings",
        params=(
            Param(name="approver", location=Location.BODY),
            Param(name="change_reviewer_merge_request", location=Location.BODY),
            Param(name="close_issue", location=Location.BODY),
            Param(name="close_merge_request", location=Location.BODY),
            Param(name="failed_pipeline", location=Location.BODY),
            Param(name="fixed_pipeline", location=Location.BODY),
            Param(name="issue_due", location=Location.BODY),
            Param(name="level", location=Location.BODY),
            Param(name="merge_merge_request", location=Location.BODY),
            Param(name="merge_when_pipeline_succeeds", location=Location.BODY),
            Param(name="moved_project", location=Location.BODY),
            Param(name="new_epic", location=Location.BODY),
            Param(name="new_issue", location=Location.BODY),
            Param(name="new_merge_request", location=Location.BODY),
            Param(name="new_note", location=Location.BODY),
            Param(name="new_release", location=Location.BODY),
            Param(name="push_to_merge_request", location=Location.BODY),
            Param(name="reassign_issue", location=Location.BODY),
            Param(name="reassign_merge_request", location=Location.BODY),
            Param(name="reopen_issue", location=Location.BODY),
            Param(name="reopen_merge_request", location=Location.BODY),
            Param(name="success_pipeline", location=Location.BODY),
        ),
    ),
    # "Pages API: Unpublish Pages".
    RestOperation(
        operation_id="plan#unpublish-pages",
        method="DELETE",
        path="/projects/:id/pages",
    ),
    # "Pages API: Retrieve Pages settings for a project".
    RestOperation(
        operation_id="plan#retrieve-pages-settings-for-a-project",
        method="GET",
        path="/projects/:id/pages",
    ),
    # "Pages API: Update Pages settings for a project".
    RestOperation(
        operation_id="plan#update-pages-settings-for-a-project",
        method="PATCH",
        path="/projects/:id/pages",
        params=(
            Param(name="pages_unique_domain_enabled", location=Location.BODY),
            Param(name="pages_https_only", location=Location.BODY),
            Param(name="pages_primary_domain", location=Location.BODY),
        ),
    ),
    # "Pages domains API: List all Pages domains".
    RestOperation(
        operation_id="plan#list-all-pages-domains",
        method="GET",
        path="/pages/domains",
        params=(
            Param(name="domain", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pages domains API: List all Pages domains in a project".
    RestOperation(
        operation_id="plan#list-all-pages-domains-in-a-project",
        method="GET",
        path="/projects/:id/pages/domains",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pages domains API: Retrieve a Pages domain".
    RestOperation(
        operation_id="plan#retrieve-a-pages-domain",
        method="GET",
        path="/projects/:id/pages/domains/:domain",
    ),
    # "Pages domains API: Create new Pages domain".
    RestOperation(
        operation_id="plan#create-new-pages-domain",
        method="POST",
        path="/projects/:id/pages/domains",
        params=(
            Param(name="domain", location=Location.BODY, required=True),
            Param(name="auto_ssl_enabled", location=Location.BODY),
            Param(name="certificate", location=Location.BODY, kind=Kind.FILE),
            Param(name="key", location=Location.BODY, kind=Kind.FILE),
            Param(name="user_provided_certificate", location=Location.BODY),
            Param(name="user_provided_key", location=Location.BODY),
        ),
    ),
    # "Pages domains API: Update Pages domain".
    RestOperation(
        operation_id="plan#update-pages-domain",
        method="PUT",
        path="/projects/:id/pages/domains/:domain",
        params=(
            Param(name="auto_ssl_enabled", location=Location.BODY),
            Param(name="certificate", location=Location.BODY, kind=Kind.FILE),
            Param(name="key", location=Location.BODY, kind=Kind.FILE),
        ),
    ),
    # "Pages domains API: Verify Pages domain".
    RestOperation(
        operation_id="plan#verify-pages-domain",
        method="PUT",
        path="/projects/:id/pages/domains/:domain/verify",
    ),
    # "Pages domains API: Delete Pages domain".
    RestOperation(
        operation_id="plan#delete-pages-domain",
        method="DELETE",
        path="/projects/:id/pages/domains/:domain",
    ),
    # "Project issue boards API: List all project issue boards".
    RestOperation(
        operation_id="plan#list-all-project-issue-boards",
        method="GET",
        path="/projects/:id/boards",
        paging=Paging.OFFSET,
    ),
    # "Project issue boards API: Retrieve an issue board".
    RestOperation(
        operation_id="plan#retrieve-an-issue-board",
        method="GET",
        path="/projects/:id/boards/:board_id",
    ),
    # "Project issue boards API: Create an issue board".
    RestOperation(
        operation_id="plan#create-an-issue-board",
        method="POST",
        path="/projects/:id/boards",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "Project issue boards API: Update an issue board".
    RestOperation(
        operation_id="plan#update-an-issue-board",
        method="PUT",
        path="/projects/:id/boards/:board_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="hide_backlog_list", location=Location.BODY),
            Param(name="hide_closed_list", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="labels", location=Location.BODY),
            Param(name="weight", location=Location.BODY),
        ),
    ),
    # "Project issue boards API: Delete an issue board".
    RestOperation(
        operation_id="plan#delete-an-issue-board",
        method="DELETE",
        path="/projects/:id/boards/:board_id",
    ),
    # "Project issue boards API: List all board lists in an issue board".
    RestOperation(
        operation_id="plan#list-all-board-lists-in-an-issue-board",
        method="GET",
        path="/projects/:id/boards/:board_id/lists",
        paging=Paging.OFFSET,
    ),
    # "Project issue boards API: Retrieve a board list".
    RestOperation(
        operation_id="plan#retrieve-a-board-list",
        method="GET",
        path="/projects/:id/boards/:board_id/lists/:list_id",
    ),
    # "Project issue boards API: Create a board list".
    RestOperation(
        operation_id="plan#create-a-board-list",
        method="POST",
        path="/projects/:id/boards/:board_id/lists",
        params=(
            Param(name="label_id", location=Location.BODY),
            Param(name="assignee_id", location=Location.BODY),
            Param(name="milestone_id", location=Location.BODY),
            Param(name="iteration_id", location=Location.BODY),
            Param(name="status_id", location=Location.BODY),
        ),
    ),
    # "Project issue boards API: Update a board list".
    RestOperation(
        operation_id="plan#update-a-board-list",
        method="PUT",
        path="/projects/:id/boards/:board_id/lists/:list_id",
        params=(Param(name="position", location=Location.BODY, required=True),),
    ),
    # "Project issue boards API: Delete a board list from a board".
    RestOperation(
        operation_id="plan#delete-a-board-list-from-a-board",
        method="DELETE",
        path="/projects/:id/boards/:board_id/lists/:list_id",
    ),
    # "Project iterations API: List all project iterations".
    RestOperation(
        operation_id="plan#list-all-project-iterations",
        method="GET",
        path="/projects/:id/iterations",
        params=(
            Param(name="state", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="in", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="include_ancestors", location=Location.QUERY),
            Param(name="include_descendants", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project labels API: Retrieve a project label".
    RestOperation(
        operation_id="plan#retrieve-a-project-label",
        method="GET",
        path="/projects/:id/labels/:label_id",
        params=(Param(name="include_ancestor_groups", location=Location.QUERY),),
    ),
    # "Project labels API: Delete a project label".
    RestOperation(
        operation_id="plan#delete-a-project-label",
        method="DELETE",
        path="/projects/:id/labels/:label_id",
    ),
    # "Project labels API: Update a project label".
    RestOperation(
        operation_id="plan#update-a-project-label",
        method="PUT",
        path="/projects/:id/labels/:label_id",
        params=(
            Param(name="new_name", location=Location.BODY, required=True),
            Param(name="color", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="priority", location=Location.BODY),
            Param(name="archived", location=Location.BODY),
        ),
    ),
    # "Project labels API: Promote a project label to a group label".
    RestOperation(
        operation_id="plan#promote-a-project-label-to-a-group-label",
        method="PUT",
        path="/projects/:id/labels/:label_id/promote",
    ),
    # "Project labels API: Subscribe to a project label".
    RestOperation(
        operation_id="plan#subscribe-to-a-project-label",
        method="POST",
        path="/projects/:id/labels/:label_id/subscribe",
    ),
    # "Project labels API: Unsubscribe from a project label".
    RestOperation(
        operation_id="plan#unsubscribe-from-a-project-label",
        method="POST",
        path="/projects/:id/labels/:label_id/unsubscribe",
    ),
    # "Project milestones API: List all project milestones".
    RestOperation(
        operation_id="plan#list-all-project-milestones",
        method="GET",
        path="/projects/:id/milestones",
        params=(
            Param(name="iids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="state", location=Location.QUERY),
            Param(name="title", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="search_title", location=Location.QUERY),
            Param(name="include_parent_milestones", location=Location.QUERY),
            Param(name="include_ancestors", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="containing_date", location=Location.QUERY),
            Param(name="start_date", location=Location.QUERY),
            Param(name="end_date", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project milestones API: Retrieve a milestone".
    RestOperation(
        operation_id="plan#retrieve-a-milestone",
        method="GET",
        path="/projects/:id/milestones/:milestone_id",
    ),
    # "Project milestones API: Create a milestone".
    RestOperation(
        operation_id="plan#create-a-milestone",
        method="POST",
        path="/projects/:id/milestones",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
        ),
    ),
    # "Project milestones API: Update a milestone".
    RestOperation(
        operation_id="plan#update-a-milestone",
        method="PUT",
        path="/projects/:id/milestones/:milestone_id",
        params=(
            Param(name="title", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="due_date", location=Location.BODY),
            Param(name="start_date", location=Location.BODY),
            Param(name="state_event", location=Location.BODY),
        ),
    ),
    # "Project milestones API: Delete a milestone".
    RestOperation(
        operation_id="plan#delete-a-milestone",
        method="DELETE",
        path="/projects/:id/milestones/:milestone_id",
    ),
    # "Project milestones API: List all issues for a milestone".
    RestOperation(
        operation_id="plan#list-all-issues-for-a-milestone",
        method="GET",
        path="/projects/:id/milestones/:milestone_id/issues",
        paging=Paging.OFFSET,
    ),
    # "Project milestones API: List all merge requests for a milestone".
    RestOperation(
        operation_id="plan#list-all-merge-requests-for-a-milestone",
        method="GET",
        path="/projects/:id/milestones/:milestone_id/merge_requests",
        paging=Paging.OFFSET,
    ),
    # "Project milestones API: Promote a milestone to group milestone".
    RestOperation(
        operation_id="plan#promote-a-milestone-to-group-milestone",
        method="POST",
        path="/projects/:id/milestones/:milestone_id/promote",
    ),
    # "Project milestones API: List all burndown chart events for a milestone".
    RestOperation(
        operation_id="plan#list-all-burndown-chart-events-for-a-milestone",
        method="GET",
        path="/projects/:id/milestones/:milestone_id/burndown_events",
        paging=Paging.OFFSET,
    ),
    # "Project wikis API: List all wiki pages".
    RestOperation(
        operation_id="plan#list-all-wiki-pages",
        method="GET",
        path="/projects/:id/wikis",
        params=(Param(name="with_content", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Project wikis API: Retrieve a wiki page".
    RestOperation(
        operation_id="plan#retrieve-a-wiki-page-1",
        method="GET",
        path="/projects/:id/wikis/:slug",
        params=(
            Param(name="render_html", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
        ),
    ),
    # "Project wikis API: Create a wiki page".
    RestOperation(
        operation_id="plan#create-a-wiki-page-1",
        method="POST",
        path="/projects/:id/wikis",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="format", location=Location.BODY),
            Param(name="front_matter", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Project wikis API: Update a wiki page".
    RestOperation(
        operation_id="plan#update-a-wiki-page-1",
        method="PUT",
        path="/projects/:id/wikis/:slug",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="format", location=Location.BODY),
            Param(name="front_matter", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Project wikis API: Delete a wiki page".
    RestOperation(
        operation_id="plan#delete-a-wiki-page-1",
        method="DELETE",
        path="/projects/:id/wikis/:slug",
    ),
    # "Project wikis API: Upload an attachment to the wiki repository".
    RestOperation(
        operation_id="plan#upload-an-attachment-to-the-wiki-repository-1",
        method="POST",
        path="/projects/:id/wikis/attachments",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="branch", location=Location.BODY),
        ),
    ),
    # "Resource iteration events API: List project issue iteration events".
    RestOperation(
        operation_id="plan#list-project-issue-iteration-events",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_iteration_events",
        paging=Paging.OFFSET,
    ),
    # "Resource iteration events API: Retrieve an issue iteration event".
    RestOperation(
        operation_id="plan#retrieve-an-issue-iteration-event",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_iteration_events/:resource_iteration_event_id",
    ),
    # "Resource label events API: List project issue label events".
    RestOperation(
        operation_id="plan#list-project-issue-label-events",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_label_events",
        paging=Paging.OFFSET,
    ),
    # "Resource label events API: Retrieve a single issue label event".
    RestOperation(
        operation_id="plan#retrieve-a-single-issue-label-event",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_label_events/:resource_label_event_id",
    ),
    # "Resource label events API: List group epic label events".
    RestOperation(
        operation_id="plan#list-group-epic-label-events",
        method="GET",
        path="/groups/:id/epics/:epic_id/resource_label_events",
        paging=Paging.OFFSET,
    ),
    # "Resource label events API: Retrieve a single epic label event".
    RestOperation(
        operation_id="plan#retrieve-a-single-epic-label-event",
        method="GET",
        path="/groups/:id/epics/:epic_id/resource_label_events/:resource_label_event_id",
    ),
    # "Resource label events API: List project merge request label events".
    RestOperation(
        operation_id="plan#list-project-merge-request-label-events",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_label_events",
        paging=Paging.OFFSET,
    ),
    # "Resource label events API: Retrieve a single merge request label event".
    RestOperation(
        operation_id="plan#retrieve-a-single-merge-request-label-event",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_label_events/:resource_label_event_id",
    ),
    # "Resource milestone events API: List project issue milestone events".
    RestOperation(
        operation_id="plan#list-project-issue-milestone-events",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_milestone_events",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Resource milestone events API: Retrieve a single issue milestone event".
    RestOperation(
        operation_id="plan#retrieve-a-single-issue-milestone-event",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_milestone_events/:resource_milestone_event_id",
    ),
    # "Resource milestone events API: List project merge request milestone events".
    RestOperation(
        operation_id="plan#list-project-merge-request-milestone-events",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_milestone_events",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Resource milestone events API: Retrieve a single merge request milestone event".
    RestOperation(
        operation_id="plan#retrieve-a-single-merge-request-milestone-event",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_milestone_events/:resource_milestone_event_id",
    ),
    # "Resource state events API: List project issue state events".
    RestOperation(
        operation_id="plan#list-project-issue-state-events",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_state_events",
        paging=Paging.OFFSET,
    ),
    # "Resource state events API: Retrieve a single issue state event".
    RestOperation(
        operation_id="plan#retrieve-a-single-issue-state-event",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_state_events/:resource_state_event_id",
    ),
    # "Resource state events API: List project merge request state events".
    RestOperation(
        operation_id="plan#list-project-merge-request-state-events",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_state_events",
        paging=Paging.OFFSET,
    ),
    # "Resource state events API: Retrieve a single merge request state event".
    RestOperation(
        operation_id="plan#retrieve-a-single-merge-request-state-event",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/resource_state_events/:resource_state_event_id",
    ),
    # "Resource state events API: List group epic state events".
    RestOperation(
        operation_id="plan#list-group-epic-state-events",
        method="GET",
        path="/groups/:id/epics/:epic_id/resource_state_events",
        paging=Paging.OFFSET,
    ),
    # "Resource state events API: Retrieve a single epic state event".
    RestOperation(
        operation_id="plan#retrieve-a-single-epic-state-event",
        method="GET",
        path="/groups/:id/epics/:epic_id/resource_state_events/:resource_state_event_id",
    ),
    # "Resource weight events API: List all project issue weight events".
    RestOperation(
        operation_id="plan#list-all-project-issue-weight-events",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_weight_events",
        paging=Paging.OFFSET,
    ),
    # "Resource weight events API: Retrieve single issue weight event".
    RestOperation(
        operation_id="plan#retrieve-single-issue-weight-event",
        method="GET",
        path="/projects/:id/issues/:issue_iid/resource_weight_events/:resource_weight_event_id",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("GET", "/groups/:id/notification_settings"),
        ("PUT", "/groups/:id/notification_settings"),
        ("POST", "/projects/:id/issues/:issue_iid/clone"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/award_emoji/:award_id"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/award_emoji/:award_id"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/notes"),
        ("GET", "/projects/:id/snippets/:snippet_id/award_emoji"),
        ("POST", "/projects/:id/snippets/:snippet_id/award_emoji"),
        ("DELETE", "/projects/:id/snippets/:snippet_id/award_emoji/:award_id"),
        ("GET", "/projects/:id/snippets/:snippet_id/award_emoji/:award_id"),
    }
)
