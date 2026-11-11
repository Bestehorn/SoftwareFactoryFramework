"""The ``codespaces`` family of the GitHub operations index: codespaces and their machine types, an
organization's Codespaces access and codespaces, and the Codespaces secrets of an organization, a repository and the
authenticated user.

Each record is its section of ``docs/api-reference/github/rest/codespaces.md``, in the order of its sections: the
operation line's method and path, the ``query`` rows of its ``Parameter`` table, and the first-level names of its JSON
request body, a leading variant label removed (``{variant 1}.repository_id`` names ``repository_id``,
``{variant 2}.pull_request.repository_id`` names ``pull_request``). No path parameter row reads "may contain ``/``", so
``multi_segment`` is empty; every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The nine sections with a ``Paging:`` line are ``Paging.LINK``, each with the key after "items in" as its ``item_key``
(``codespaces``, ``devcontainers``, ``secrets`` or ``repositories``; ``conventions.md`` "Lists wrapped in an object").
``codespaces/get-org-secret`` answers one object with a ``Link`` header, which does not page (issue #33 DL-006), so it
is ``Paging.NONE`` like every other record and sends one request.

Every record is sent by ``call <operation-id>`` (#28), which refuses ``codespaces/export-for-authenticated-user``, the
record of this family whose call writes a branch (issue #33 AC-6), by ``commands/call.py`` ``GATED_OPERATIONS``. The
secret writes send ``encrypted_value`` and ``key_id`` as given (#31 DL-002). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "codespaces"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/codespaces.md "List codespaces in a repository for the authenticated user": pages by ``link``, its items in
    # ``codespaces``.
    RestOperation(
        operation_id="codespaces/list-in-repository-for-authenticated-user",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="codespaces",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create a codespace in a repository"
    RestOperation(
        operation_id="codespaces/create-with-repo-for-authenticated-user",
        method="POST",
        path="/repos/{owner}/{repo}/codespaces",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "ref",
                "location",
                "geo",
                "client_ip",
                "machine",
                "devcontainer_path",
                "multi_repo_permissions_opt_out",
                "working_directory",
                "idle_timeout_minutes",
                "display_name",
                "retention_period_minutes",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List devcontainer configurations in a repository for the authenticated user": pages by
    # ``link``, its items in ``devcontainers``.
    RestOperation(
        operation_id="codespaces/list-devcontainers-in-repository-for-authenticated-user",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/devcontainers",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="devcontainers",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get default attributes for a codespace"
    RestOperation(
        operation_id="codespaces/pre-flight-with-repo-for-authenticated-user",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/new",
        query_params=frozenset({"ref", "client_ip"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Check if permissions defined by a devcontainer have been accepted by the authenticated user"
    RestOperation(
        operation_id="codespaces/check-permissions-for-devcontainer",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/permissions_check",
        query_params=frozenset({"ref", "devcontainer_path"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create a codespace from a pull request"
    RestOperation(
        operation_id="codespaces/create-with-pr-for-authenticated-user",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/codespaces",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "location",
                "geo",
                "client_ip",
                "machine",
                "devcontainer_path",
                "multi_repo_permissions_opt_out",
                "working_directory",
                "idle_timeout_minutes",
                "display_name",
                "retention_period_minutes",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List codespaces for the authenticated user": pages by ``link``, its items in ``codespaces``.
    RestOperation(
        operation_id="codespaces/list-for-authenticated-user",
        method="GET",
        path="/user/codespaces",
        query_params=frozenset({"per_page", "page", "repository_id"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="codespaces",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/create-for-authenticated-user",
        method="POST",
        path="/user/codespaces",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "repository_id",
                "ref",
                "location",
                "geo",
                "client_ip",
                "machine",
                "devcontainer_path",
                "multi_repo_permissions_opt_out",
                "working_directory",
                "idle_timeout_minutes",
                "display_name",
                "retention_period_minutes",
                "pull_request",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/get-for-authenticated-user",
        method="GET",
        path="/user/codespaces/{codespace_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Update a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/update-for-authenticated-user",
        method="PATCH",
        path="/user/codespaces/{codespace_name}",
        query_params=frozenset(),
        body_params=frozenset({"machine", "display_name", "recent_folders"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Delete a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/delete-for-authenticated-user",
        method="DELETE",
        path="/user/codespaces/{codespace_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Export a codespace for the authenticated user": ``call`` refuses it, its call writes a branch
    # (issue #33 AC-6).
    RestOperation(
        operation_id="codespaces/export-for-authenticated-user",
        method="POST",
        path="/user/codespaces/{codespace_name}/exports",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get details about a codespace export"
    RestOperation(
        operation_id="codespaces/get-export-details-for-authenticated-user",
        method="GET",
        path="/user/codespaces/{codespace_name}/exports/{export_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create a repository from an unpublished codespace"
    RestOperation(
        operation_id="codespaces/publish-for-authenticated-user",
        method="POST",
        path="/user/codespaces/{codespace_name}/publish",
        query_params=frozenset(),
        body_params=frozenset({"name", "private"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Start a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/start-for-authenticated-user",
        method="POST",
        path="/user/codespaces/{codespace_name}/start",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Stop a codespace for the authenticated user"
    RestOperation(
        operation_id="codespaces/stop-for-authenticated-user",
        method="POST",
        path="/user/codespaces/{codespace_name}/stop",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List available machine types for a repository"
    RestOperation(
        operation_id="codespaces/repo-machines-for-authenticated-user",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/machines",
        query_params=frozenset({"location", "client_ip", "ref"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List machine types for a codespace"
    RestOperation(
        operation_id="codespaces/codespace-machines-for-authenticated-user",
        method="GET",
        path="/user/codespaces/{codespace_name}/machines",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List organization secrets": pages by ``link``, its items in ``secrets``.
    RestOperation(
        operation_id="codespaces/list-org-secrets",
        method="GET",
        path="/orgs/{org}/codespaces/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get an organization public key"
    RestOperation(
        operation_id="codespaces/get-org-public-key",
        method="GET",
        path="/orgs/{org}/codespaces/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get an organization secret": one object with a ``Link`` header, which does not page (DL-006).
    RestOperation(
        operation_id="codespaces/get-org-secret",
        method="GET",
        path="/orgs/{org}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create or update an organization secret"
    RestOperation(
        operation_id="codespaces/create-or-update-org-secret",
        method="PUT",
        path="/orgs/{org}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id", "visibility", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Delete an organization secret"
    RestOperation(
        operation_id="codespaces/delete-org-secret",
        method="DELETE",
        path="/orgs/{org}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List selected repositories for an organization secret": pages by ``link``, its items in
    # ``repositories``.
    RestOperation(
        operation_id="codespaces/list-selected-repos-for-org-secret",
        method="GET",
        path="/orgs/{org}/codespaces/secrets/{secret_name}/repositories",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Set selected repositories for an organization secret"
    RestOperation(
        operation_id="codespaces/set-selected-repos-for-org-secret",
        method="PUT",
        path="/orgs/{org}/codespaces/secrets/{secret_name}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Add selected repository to an organization secret"
    RestOperation(
        operation_id="codespaces/add-selected-repo-to-org-secret",
        method="PUT",
        path="/orgs/{org}/codespaces/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Remove selected repository from an organization secret"
    RestOperation(
        operation_id="codespaces/remove-selected-repo-from-org-secret",
        method="DELETE",
        path="/orgs/{org}/codespaces/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List codespaces for the organization": pages by ``link``, its items in ``codespaces``.
    RestOperation(
        operation_id="codespaces/list-in-organization",
        method="GET",
        path="/orgs/{org}/codespaces",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="codespaces",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Manage access control for organization codespaces"
    RestOperation(
        operation_id="codespaces/set-codespaces-access",
        method="PUT",
        path="/orgs/{org}/codespaces/access",
        query_params=frozenset(),
        body_params=frozenset({"visibility", "selected_usernames"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Add users to Codespaces access for an organization"
    RestOperation(
        operation_id="codespaces/set-codespaces-access-users",
        method="POST",
        path="/orgs/{org}/codespaces/access/selected_users",
        query_params=frozenset(),
        body_params=frozenset({"selected_usernames"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Remove users from Codespaces access for an organization"
    RestOperation(
        operation_id="codespaces/delete-codespaces-access-users",
        method="DELETE",
        path="/orgs/{org}/codespaces/access/selected_users",
        query_params=frozenset(),
        body_params=frozenset({"selected_usernames"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List codespaces for a user in organization": pages by ``link``, its items in ``codespaces``.
    RestOperation(
        operation_id="codespaces/get-codespaces-for-user-in-org",
        method="GET",
        path="/orgs/{org}/members/{username}/codespaces",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="codespaces",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Delete a codespace from the organization"
    RestOperation(
        operation_id="codespaces/delete-from-organization",
        method="DELETE",
        path="/orgs/{org}/members/{username}/codespaces/{codespace_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Stop a codespace for an organization user"
    RestOperation(
        operation_id="codespaces/stop-in-organization",
        method="POST",
        path="/orgs/{org}/members/{username}/codespaces/{codespace_name}/stop",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List repository secrets": pages by ``link``, its items in ``secrets``.
    RestOperation(
        operation_id="codespaces/list-repo-secrets",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get a repository public key"
    RestOperation(
        operation_id="codespaces/get-repo-public-key",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get a repository secret"
    RestOperation(
        operation_id="codespaces/get-repo-secret",
        method="GET",
        path="/repos/{owner}/{repo}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create or update a repository secret"
    RestOperation(
        operation_id="codespaces/create-or-update-repo-secret",
        method="PUT",
        path="/repos/{owner}/{repo}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Delete a repository secret"
    RestOperation(
        operation_id="codespaces/delete-repo-secret",
        method="DELETE",
        path="/repos/{owner}/{repo}/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List secrets for the authenticated user": pages by ``link``, its items in ``secrets``.
    RestOperation(
        operation_id="codespaces/list-secrets-for-authenticated-user",
        method="GET",
        path="/user/codespaces/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get public key for the authenticated user"
    RestOperation(
        operation_id="codespaces/get-public-key-for-authenticated-user",
        method="GET",
        path="/user/codespaces/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Get a secret for the authenticated user"
    RestOperation(
        operation_id="codespaces/get-secret-for-authenticated-user",
        method="GET",
        path="/user/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Create or update a secret for the authenticated user"
    RestOperation(
        operation_id="codespaces/create-or-update-secret-for-authenticated-user",
        method="PUT",
        path="/user/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Delete a secret for the authenticated user"
    RestOperation(
        operation_id="codespaces/delete-secret-for-authenticated-user",
        method="DELETE",
        path="/user/codespaces/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "List selected repositories for a user secret"
    RestOperation(
        operation_id="codespaces/list-repositories-for-secret-for-authenticated-user",
        method="GET",
        path="/user/codespaces/secrets/{secret_name}/repositories",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Set selected repositories for a user secret"
    RestOperation(
        operation_id="codespaces/set-repositories-for-secret-for-authenticated-user",
        method="PUT",
        path="/user/codespaces/secrets/{secret_name}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Add a selected repository to a user secret"
    RestOperation(
        operation_id="codespaces/add-repository-for-secret-for-authenticated-user",
        method="PUT",
        path="/user/codespaces/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/codespaces.md "Remove a selected repository from a user secret"
    RestOperation(
        operation_id="codespaces/remove-repository-for-secret-for-authenticated-user",
        method="DELETE",
        path="/user/codespaces/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
