"""The ``teams`` family of the GitHub operations index: an organization's teams, their members, memberships, pending
invitations, repositories and child teams, each addressed by ``{org}`` and ``{team_slug}`` or by the legacy
``{team_id}``, and the teams of the authenticated user.

Each record is the section of ``docs/api-reference/github/rest/teams.md`` its operation ID names: its method and path,
the names of its ``query`` rows, and the first-level fields of its request body. No path parameter of the family may
contain ``/``, so every ``multi_segment`` is empty. Every list section reads "the response body is the array" and names
a ``Link`` header, so its record pages by ``link`` with no item key; every other record sends one request.
``teams/check-permissions-for-repo-in-org`` sends ``ACCEPT_JSON`` like every record, not the
``application/vnd.github.v3.repository+json`` its section names (issue #29 ``change.md`` Residuals).

Every record is sent by ``call <operation-id>`` (#28), ``{owner}`` and ``{repo}`` defaulting to the ``origin``
repository. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "teams"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/teams.md "List pending team invitations": query ``per_page``, ``page``; 200 with an array of
    # ``organization-invitation`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-pending-invitations-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/invitations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List team members": query ``role``, ``per_page``, ``page``; 200 with an array of ``team-member``
    # and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-members-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/members",
        query_params=frozenset({"role", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Get team membership for a user": path parameters only; 200 with a ``team-membership``.
    RestOperation(
        operation_id="teams/get-membership-for-user-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Add or update team membership for a user": optional body ``role``; 200 with a ``team-membership``.
    RestOperation(
        operation_id="teams/add-or-update-membership-for-user-in-org",
        method="PUT",
        path="/orgs/{org}/teams/{team_slug}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset({"role"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Remove team membership for a user": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/remove-membership-for-user-in-org",
        method="DELETE",
        path="/orgs/{org}/teams/{team_slug}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List pending team invitations (Legacy)": query ``per_page``, ``page``; 200 with an array of
    # ``organization-invitation`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-pending-invitations-legacy",
        method="GET",
        path="/teams/{team_id}/invitations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List team members (Legacy)": query ``role``, ``per_page``, ``page``; 200 with an array of
    # ``team-member`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-members-legacy",
        method="GET",
        path="/teams/{team_id}/members",
        query_params=frozenset({"role", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Get team member (Legacy)": path parameters only; 204 or 404.
    RestOperation(
        operation_id="teams/get-member-legacy",
        method="GET",
        path="/teams/{team_id}/members/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Add team member (Legacy)": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/add-member-legacy",
        method="PUT",
        path="/teams/{team_id}/members/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Remove team member (Legacy)": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/remove-member-legacy",
        method="DELETE",
        path="/teams/{team_id}/members/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Get team membership for a user (Legacy)": path parameters only; 200 with a ``team-membership``.
    RestOperation(
        operation_id="teams/get-membership-for-user-legacy",
        method="GET",
        path="/teams/{team_id}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Add or update team membership for a user (Legacy)": optional body ``role``; 200 with a
    # ``team-membership``.
    RestOperation(
        operation_id="teams/add-or-update-membership-for-user-legacy",
        method="PUT",
        path="/teams/{team_id}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset({"role"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Remove team membership for a user (Legacy)": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/remove-membership-for-user-legacy",
        method="DELETE",
        path="/teams/{team_id}/memberships/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List teams": query ``per_page``, ``page``, ``team_type``; 200 with an array of ``team`` and a
    # ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list",
        method="GET",
        path="/orgs/{org}/teams",
        query_params=frozenset({"per_page", "page", "team_type"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Create a team": the first-level body fields; 201 with a ``team-full``.
    RestOperation(
        operation_id="teams/create",
        method="POST",
        path="/orgs/{org}/teams",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "description",
                "maintainers",
                "repo_names",
                "privacy",
                "notification_setting",
                "permission",
                "parent_team_id",
                "parent_team_slug",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Get a team by name": path parameters only; 200 with a ``team-full``.
    RestOperation(
        operation_id="teams/get-by-name",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Update a team": the first-level body fields; 200 or 201 with a ``team-full``.
    RestOperation(
        operation_id="teams/update-in-org",
        method="PATCH",
        path="/orgs/{org}/teams/{team_slug}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "description",
                "privacy",
                "notification_setting",
                "permission",
                "parent_team_id",
                "parent_team_slug",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Delete a team": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/delete-in-org",
        method="DELETE",
        path="/orgs/{org}/teams/{team_slug}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List team repositories": query ``per_page``, ``page``; 200 with an array of ``minimal-repository``
    # and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-repos-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/repos",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Check team permissions for a repository": path parameters only; 200 with a ``team-repository``.
    # The section names ``application/vnd.github.v3.repository+json``; the record sends ``ACCEPT_JSON`` (Residuals).
    RestOperation(
        operation_id="teams/check-permissions-for-repo-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Add or update team repository permissions": optional body ``permission``; 204 on success.
    RestOperation(
        operation_id="teams/add-or-update-repo-permissions-in-org",
        method="PUT",
        path="/orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset({"permission"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Remove a repository from a team": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/remove-repo-in-org",
        method="DELETE",
        path="/orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List child teams": query ``per_page``, ``page``; 200 with an array of ``team`` and a ``Link``
    # header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-child-in-org",
        method="GET",
        path="/orgs/{org}/teams/{team_slug}/teams",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Get a team (Legacy)": path parameters only; 200 with a ``team-full``.
    RestOperation(
        operation_id="teams/get-legacy",
        method="GET",
        path="/teams/{team_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Update a team (Legacy)": the first-level body fields; 200 or 201 with a ``team-full``.
    RestOperation(
        operation_id="teams/update-legacy",
        method="PATCH",
        path="/teams/{team_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "description",
                "privacy",
                "notification_setting",
                "permission",
                "parent_team_id",
                "parent_team_slug",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Delete a team (Legacy)": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/delete-legacy",
        method="DELETE",
        path="/teams/{team_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List team repositories (Legacy)": query ``per_page``, ``page``; 200 with an array of
    # ``minimal-repository`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-repos-legacy",
        method="GET",
        path="/teams/{team_id}/repos",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Check team permissions for a repository (Legacy)": path parameters only; 200 with a
    # ``team-repository``.
    RestOperation(
        operation_id="teams/check-permissions-for-repo-legacy",
        method="GET",
        path="/teams/{team_id}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Add or update team repository permissions (Legacy)": optional body ``permission``; 204 on success.
    RestOperation(
        operation_id="teams/add-or-update-repo-permissions-legacy",
        method="PUT",
        path="/teams/{team_id}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset({"permission"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "Remove a repository from a team (Legacy)": path parameters only; 204 on success.
    RestOperation(
        operation_id="teams/remove-repo-legacy",
        method="DELETE",
        path="/teams/{team_id}/repos/{owner}/{repo}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List child teams (Legacy)": query ``per_page``, ``page``; 200 with an array of ``team`` and a
    # ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-child-legacy",
        method="GET",
        path="/teams/{team_id}/teams",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/teams.md "List teams for the authenticated user": query ``per_page``, ``page``; 200 with an array of
    # ``team-full`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="teams/list-for-authenticated-user",
        method="GET",
        path="/user/teams",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
