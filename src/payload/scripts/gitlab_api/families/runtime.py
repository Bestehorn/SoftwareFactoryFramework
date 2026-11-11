"""The ``runtime`` endpoint family of the GitLab wrapper: the members of groups and projects, billable and pending
members, membership states and overrides.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/runtime.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section:
the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- an ``array of integers`` row (``user_ids``, ``skip_users``) is ``Kind.ARRAY``, every other row ``SCALAR``;
  ``required`` is the Required column's ``yes`` (the ``conditional`` rows of the two removals are not); every body is
  JSON and no record has ``fixed`` values;
- a ``GET`` section headed "List" or with a ``page`` row is ``Paging.OFFSET``, every other record ``Paging.NONE``.

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "runtime"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Groups members API: List all group members".
    RestOperation(
        operation_id="runtime#list-all-group-members",
        method="GET",
        path="/groups/:id/members",
        params=(
            Param(name="query", location=Location.QUERY),
            Param(name="user_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="skip_users", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="show_seat_info", location=Location.QUERY),
            Param(name="with_saml_identity", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Groups members API: List all group members, including inherited and invited members".
    RestOperation(
        operation_id="runtime#list-all-group-members-including-inherited-and-invited-members",
        method="GET",
        path="/groups/:id/members/all",
        params=(
            Param(name="query", location=Location.QUERY),
            Param(name="user_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="show_seat_info", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Groups members API: Retrieve a group member".
    RestOperation(
        operation_id="runtime#retrieve-a-group-member",
        method="GET",
        path="/groups/:id/members/:user_id",
    ),
    # "Groups members API: Retrieve a group member, including inherited and invited members".
    RestOperation(
        operation_id="runtime#retrieve-a-group-member-including-inherited-and-invited-members",
        method="GET",
        path="/groups/:id/members/all/:user_id",
    ),
    # "Groups members API: List all billable group members".
    RestOperation(
        operation_id="runtime#list-all-billable-group-members",
        method="GET",
        path="/groups/:id/billable_members",
        params=(
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Groups members API: List all memberships for a billable group member".
    RestOperation(
        operation_id="runtime#list-all-memberships-for-a-billable-group-member",
        method="GET",
        path="/groups/:id/billable_members/:user_id/memberships",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Groups members API: List all indirect memberships for a billable group member".
    RestOperation(
        operation_id="runtime#list-all-indirect-memberships-for-a-billable-group-member",
        method="GET",
        path="/groups/:id/billable_members/:user_id/indirect",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Groups members API: Remove a billable group member".
    RestOperation(
        operation_id="runtime#remove-a-billable-group-member",
        method="DELETE",
        path="/groups/:id/billable_members/:user_id",
    ),
    # "Groups members API: Change group membership state for a user".
    RestOperation(
        operation_id="runtime#change-group-membership-state-for-a-user",
        method="PUT",
        path="/groups/:id/members/:user_id/state",
        params=(Param(name="state", location=Location.BODY, required=True),),
    ),
    # "Groups members API: Add a group member".
    RestOperation(
        operation_id="runtime#add-a-group-member",
        method="POST",
        path="/groups/:id/members",
        params=(
            Param(name="user_id", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="access_level", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="invite_source", location=Location.BODY),
            Param(name="member_role_id", location=Location.BODY),
        ),
    ),
    # "Groups members API: Update a group member".
    RestOperation(
        operation_id="runtime#update-a-group-member",
        method="PUT",
        path="/groups/:id/members/:user_id",
        params=(
            Param(name="access_level", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="member_role_id", location=Location.BODY),
        ),
    ),
    # "Groups members API: Set override flag for a member of a group".
    RestOperation(
        operation_id="runtime#set-override-flag-for-a-member-of-a-group",
        method="POST",
        path="/groups/:id/members/:user_id/override",
    ),
    # "Groups members API: Remove override for a member of a group".
    RestOperation(
        operation_id="runtime#remove-override-for-a-member-of-a-group",
        method="DELETE",
        path="/groups/:id/members/:user_id/override",
    ),
    # "Groups members API: Remove a group member".
    RestOperation(
        operation_id="runtime#remove-a-group-member",
        method="DELETE",
        path="/groups/:id/members/:user_id",
        params=(
            Param(name="skip_subresources", location=Location.QUERY),
            Param(name="unassign_issuables", location=Location.QUERY),
        ),
    ),
    # "Groups members API: Approve a group member".
    RestOperation(
        operation_id="runtime#approve-a-group-member",
        method="PUT",
        path="/groups/:id/members/:member_id/approve",
    ),
    # "Groups members API: Approve all pending group members".
    RestOperation(
        operation_id="runtime#approve-all-pending-group-members",
        method="POST",
        path="/groups/:id/members/approve_all",
    ),
    # "Groups members API: List all pending group members in a group and its subgroups and projects".
    RestOperation(
        operation_id="runtime#list-all-pending-group-members-in-a-group-and-its-subgroups-and-projects",
        method="GET",
        path="/groups/:id/pending_members",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Projects members API: List all direct members of a project".
    RestOperation(
        operation_id="runtime#list-all-direct-members-of-a-project",
        method="GET",
        path="/projects/:id/members",
        params=(
            Param(name="query", location=Location.QUERY),
            Param(name="user_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="skip_users", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="show_seat_info", location=Location.QUERY),
            Param(name="with_saml_identity", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Projects members API: List all members of a project".
    RestOperation(
        operation_id="runtime#list-all-members-of-a-project",
        method="GET",
        path="/projects/:id/members/all",
        params=(
            Param(name="query", location=Location.QUERY),
            Param(name="user_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="show_seat_info", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Projects members API: Retrieve a direct member of a project".
    RestOperation(
        operation_id="runtime#retrieve-a-direct-member-of-a-project",
        method="GET",
        path="/projects/:id/members/:user_id",
    ),
    # "Projects members API: Retrieve a member of a project".
    RestOperation(
        operation_id="runtime#retrieve-a-member-of-a-project",
        method="GET",
        path="/projects/:id/members/all/:user_id",
    ),
    # "Projects members API: Add a member to a project".
    RestOperation(
        operation_id="runtime#add-a-member-to-a-project",
        method="POST",
        path="/projects/:id/members",
        params=(
            Param(name="user_id", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="access_level", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="invite_source", location=Location.BODY),
            Param(name="member_role_id", location=Location.BODY),
        ),
    ),
    # "Projects members API: Update a member of a project".
    RestOperation(
        operation_id="runtime#update-a-member-of-a-project",
        method="PUT",
        path="/projects/:id/members/:user_id",
        params=(
            Param(name="access_level", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="member_role_id", location=Location.BODY),
        ),
    ),
    # "Projects members API: Remove a direct member of a project".
    RestOperation(
        operation_id="runtime#remove-a-direct-member-of-a-project",
        method="DELETE",
        path="/projects/:id/members/:user_id",
        params=(
            Param(name="skip_subresources", location=Location.QUERY),
            Param(name="unassign_issuables", location=Location.QUERY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
