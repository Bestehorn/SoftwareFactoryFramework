"""The ``dependabot`` family of the GitHub operations index: Dependabot alerts, repository access, runner settings and
secrets.

Each record is the section of ``docs/api-reference/github/rest/dependabot.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body (``agent_assignment.model`` is a
field of ``agent_assignment``; a ``(body)`` constraint row names none). No path parameter of the family may contain
``/``, so no record has a multi-segment parameter. The eight sections with a ``Paging:`` line page by ``link``: the
three alert lists return a bare array, so they have no item key; the two repository-access lists hold their items in
``accessible_repositories`` (so the object's ``default_level`` is not printed), the two secret lists in ``secrets`` and
the selected-repository list in ``repositories``. Every other record sends one request.

A secret write's ``encrypted_value`` and ``key_id`` are sent as given: the caller encrypts the value with the key
``dependabot/get-org-public-key`` or ``dependabot/get-repo-public-key`` returns, and the wrapper encrypts nothing (#31
DL-002). Every record is sent by ``call <operation-id>`` (#28); none is gated. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "dependabot"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/dependabot.md "List Dependabot alerts for an enterprise": the filter, sort and cursor queries and
    # ``per_page``; 200 with an array of ``dependabot-alert-with-repository``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="dependabot/list-alerts-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/dependabot/alerts",
        query_params=frozenset(
            {
                "classification",
                "state",
                "severity",
                "ecosystem",
                "package",
                "epss_percentage",
                "has",
                "assignee",
                "scope",
                "relationship",
                "sort",
                "direction",
                "before",
                "after",
                "per_page",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "List Dependabot alerts for an organization": the filter, sort and cursor queries and
    # ``per_page``; 200 with an array of ``dependabot-alert-with-repository``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="dependabot/list-alerts-for-org",
        method="GET",
        path="/orgs/{org}/dependabot/alerts",
        query_params=frozenset(
            {
                "classification",
                "state",
                "severity",
                "ecosystem",
                "package",
                "epss_percentage",
                "artifact_registry_url",
                "artifact_registry",
                "has",
                "assignee",
                "runtime_risk",
                "scope",
                "relationship",
                "sort",
                "direction",
                "before",
                "after",
                "per_page",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "List Dependabot alerts for a repository": the filter, sort and cursor queries and
    # ``per_page``; 200 with an array of ``dependabot-alert``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="dependabot/list-alerts-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/alerts",
        query_params=frozenset(
            {
                "classification",
                "state",
                "severity",
                "ecosystem",
                "package",
                "manifest",
                "epss_percentage",
                "has",
                "assignee",
                "scope",
                "relationship",
                "sort",
                "direction",
                "before",
                "after",
                "per_page",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get a Dependabot alert": path parameters only; 200 with a ``dependabot-alert``.
    RestOperation(
        operation_id="dependabot/get-alert",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/alerts/{alert_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Update a Dependabot alert": the first-level body fields; 200 with a ``dependabot-alert``.
    RestOperation(
        operation_id="dependabot/update-alert",
        method="PATCH",
        path="/repos/{owner}/{repo}/dependabot/alerts/{alert_number}",
        query_params=frozenset(),
        body_params=frozenset({"state", "dismissed_reason", "dismissed_comment", "assignees", "agent_assignment"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Lists the repositories Dependabot can access in an enterprise": query ``page`` and
    # ``per_page``; 200 with a ``dependabot-repository-access-details``, its items in ``accessible_repositories``.
    RestOperation(
        operation_id="dependabot/repository-access-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/dependabot/repository-access",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="accessible_repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Updates Dependabot's repository access list for an enterprise": body
    # ``repository_ids_to_add`` and ``repository_ids_to_remove``; 204 on success.
    RestOperation(
        operation_id="dependabot/update-repository-access-for-enterprise",
        method="PATCH",
        path="/enterprises/{enterprise}/dependabot/repository-access",
        query_params=frozenset(),
        body_params=frozenset({"repository_ids_to_add", "repository_ids_to_remove"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Set the default repository access level for Dependabot in an enterprise": body
    # ``default_level``; 204 on success.
    RestOperation(
        operation_id="dependabot/set-repository-access-default-level-for-enterprise",
        method="PUT",
        path="/enterprises/{enterprise}/dependabot/repository-access/default-level",
        query_params=frozenset(),
        body_params=frozenset({"default_level"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Lists the repositories Dependabot can access in an organization": query ``page`` and
    # ``per_page``; 200 with a ``dependabot-repository-access-details``, its items in ``accessible_repositories``.
    RestOperation(
        operation_id="dependabot/repository-access-for-org",
        method="GET",
        path="/orgs/{org}/dependabot/repository-access",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="accessible_repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Updates Dependabot's repository access list for an organization": body
    # ``repository_ids_to_add`` and ``repository_ids_to_remove``; 204 on success.
    RestOperation(
        operation_id="dependabot/update-repository-access-for-org",
        method="PATCH",
        path="/orgs/{org}/dependabot/repository-access",
        query_params=frozenset(),
        body_params=frozenset({"repository_ids_to_add", "repository_ids_to_remove"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Set the default repository access level for Dependabot": body ``default_level``; 204 on
    # success.
    RestOperation(
        operation_id="dependabot/set-repository-access-default-level",
        method="PUT",
        path="/orgs/{org}/dependabot/repository-access/default-level",
        query_params=frozenset(),
        body_params=frozenset({"default_level"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get repository Dependabot runner settings": path parameters only; 200 with a
    # ``dependabot-runner-settings``.
    RestOperation(
        operation_id="dependabot/get-repository-runner-settings",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/runner-settings",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Set repository Dependabot runner settings": body ``runner_type``, ``runner_labels`` and
    # ``runner_group``; 200 with a ``dependabot-runner-settings``.
    RestOperation(
        operation_id="dependabot/set-repository-runner-settings",
        method="PUT",
        path="/repos/{owner}/{repo}/dependabot/runner-settings",
        query_params=frozenset(),
        body_params=frozenset({"runner_type", "runner_labels", "runner_group"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "List organization secrets": query ``per_page`` and ``page``; 200 with an object and a
    # ``Link`` header, its items in ``secrets``.
    RestOperation(
        operation_id="dependabot/list-org-secrets",
        method="GET",
        path="/orgs/{org}/dependabot/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get an organization public key": path parameters only; 200 with a ``dependabot-public-key``.
    RestOperation(
        operation_id="dependabot/get-org-public-key",
        method="GET",
        path="/orgs/{org}/dependabot/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get an organization secret": path parameters only; 200 with an
    # ``organization-dependabot-secret``.
    RestOperation(
        operation_id="dependabot/get-org-secret",
        method="GET",
        path="/orgs/{org}/dependabot/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Create or update an organization secret": body ``encrypted_value`` and ``key_id`` (sent as
    # given), ``visibility`` and ``selected_repository_ids``; 201 or 204.
    RestOperation(
        operation_id="dependabot/create-or-update-org-secret",
        method="PUT",
        path="/orgs/{org}/dependabot/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id", "visibility", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Delete an organization secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="dependabot/delete-org-secret",
        method="DELETE",
        path="/orgs/{org}/dependabot/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "List selected repositories for an organization secret": query ``page`` and ``per_page``;
    # 200 with an object, its items in ``repositories``.
    RestOperation(
        operation_id="dependabot/list-selected-repos-for-org-secret",
        method="GET",
        path="/orgs/{org}/dependabot/secrets/{secret_name}/repositories",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Set selected repositories for an organization secret": body ``selected_repository_ids``;
    # 204 on success.
    RestOperation(
        operation_id="dependabot/set-selected-repos-for-org-secret",
        method="PUT",
        path="/orgs/{org}/dependabot/secrets/{secret_name}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Add selected repository to an organization secret": path parameters only; 204 or 409.
    RestOperation(
        operation_id="dependabot/add-selected-repo-to-org-secret",
        method="PUT",
        path="/orgs/{org}/dependabot/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Remove selected repository from an organization secret": path parameters only; 204 or 409.
    RestOperation(
        operation_id="dependabot/remove-selected-repo-from-org-secret",
        method="DELETE",
        path="/orgs/{org}/dependabot/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "List repository secrets": query ``per_page`` and ``page``; 200 with an object and a ``Link``
    # header, its items in ``secrets``.
    RestOperation(
        operation_id="dependabot/list-repo-secrets",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get a repository public key": path parameters only; 200 with a ``dependabot-public-key``.
    RestOperation(
        operation_id="dependabot/get-repo-public-key",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Get a repository secret": path parameters only; 200 with a ``dependabot-secret``.
    RestOperation(
        operation_id="dependabot/get-repo-secret",
        method="GET",
        path="/repos/{owner}/{repo}/dependabot/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Create or update a repository secret": body ``encrypted_value`` and ``key_id`` (sent as
    # given); 201 or 204.
    RestOperation(
        operation_id="dependabot/create-or-update-repo-secret",
        method="PUT",
        path="/repos/{owner}/{repo}/dependabot/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependabot.md "Delete a repository secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="dependabot/delete-repo-secret",
        method="DELETE",
        path="/repos/{owner}/{repo}/dependabot/secrets/{secret_name}",
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
