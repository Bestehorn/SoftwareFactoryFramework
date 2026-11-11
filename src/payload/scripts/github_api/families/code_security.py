"""The ``code-security`` family of the GitHub operations index: the code security configurations of an enterprise, an
organization and a repository.

Each record is the section of ``docs/api-reference/github/rest/code-security.md`` its operation ID names, in the order
of the file: its method and path, the names of its ``query`` rows, and the first-level fields of its request body
(``code_scanning_options.allow_advanced`` is a field of ``code_scanning_options``). The create and update sections of
one owner document the same first-level fields: ``ENTERPRISE_CONFIGURATION_FIELDS`` for an enterprise's, and
``ORGANIZATION_CONFIGURATION_FIELDS`` for an organization's, which adds three. No path parameter of the family may
contain ``/``, so ``multi_segment`` is empty, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The four sections with a ``Paging:`` line (``per_page`` and a cursor, the response body the array) page by ``link``
with no item key. ``code-security/get-default-configurations`` and its enterprise twin answer an array with no
``Paging:`` line and no ``Link`` header, so they send one request, as every other record does.

Every record is sent by ``call <operation-id>`` (#28); none writes a branch. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "code-security"

#: The first-level body fields of "Create a code security configuration for an enterprise" and "Update a custom code
#: security configuration for an enterprise".
ENTERPRISE_CONFIGURATION_FIELDS: FrozenSet[str] = frozenset(
    {
        "name",
        "description",
        "advanced_security",
        "code_security",
        "dependency_graph",
        "dependency_graph_autosubmit_action",
        "dependency_graph_autosubmit_action_options",
        "dependabot_alerts",
        "dependabot_reachability",
        "dependabot_security_updates",
        "code_scanning_options",
        "code_scanning_default_setup",
        "code_scanning_default_setup_options",
        "code_scanning_delegated_alert_dismissal",
        "secret_protection",
        "secret_scanning",
        "secret_scanning_push_protection",
        "secret_scanning_validity_checks",
        "secret_scanning_non_provider_patterns",
        "secret_scanning_generic_secrets",
        "secret_scanning_generic_secrets_push_protection",
        "secret_scanning_delegated_alert_dismissal",
        "secret_scanning_extended_metadata",
        "private_vulnerability_reporting",
        "enforcement",
    }
)

#: The first-level body fields of "Create a code security configuration" and "Update a code security configuration":
#: the enterprise's and three more.
ORGANIZATION_CONFIGURATION_FIELDS: FrozenSet[str] = ENTERPRISE_CONFIGURATION_FIELDS | frozenset(
    {
        "dependabot_delegated_alert_dismissal",
        "secret_scanning_delegated_bypass",
        "secret_scanning_delegated_bypass_options",
    }
)

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/code-security.md "Get code security configurations for an enterprise": ``per_page`` + cursor; 200 with an
    # array of ``code-security-configuration``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-security/get-configurations-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/code-security/configurations",
        query_params=frozenset({"per_page", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Create a code security configuration for an enterprise": the enterprise's fields; 201.
    RestOperation(
        operation_id="code-security/create-configuration-for-enterprise",
        method="POST",
        path="/enterprises/{enterprise}/code-security/configurations",
        query_params=frozenset(),
        body_params=ENTERPRISE_CONFIGURATION_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get default code security configurations for an enterprise": an array, no paging.
    RestOperation(
        operation_id="code-security/get-default-configurations-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/code-security/configurations/defaults",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Retrieve a code security configuration of an enterprise": path parameters only.
    RestOperation(
        operation_id="code-security/get-single-configuration-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Update a custom code security configuration for an enterprise": the enterprise's fields.
    RestOperation(
        operation_id="code-security/update-enterprise-configuration",
        method="PATCH",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=ENTERPRISE_CONFIGURATION_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Delete a code security configuration for an enterprise": path parameters only; 204.
    RestOperation(
        operation_id="code-security/delete-configuration-for-enterprise",
        method="DELETE",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Attach an enterprise configuration to repositories": body ``scope``; 202.
    RestOperation(
        operation_id="code-security/attach-enterprise-configuration",
        method="POST",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}/attach",
        query_params=frozenset(),
        body_params=frozenset({"scope"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Set a code security configuration as a default for an enterprise": body
    # ``default_for_new_repos``.
    RestOperation(
        operation_id="code-security/set-configuration-as-default-for-enterprise",
        method="PUT",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}/defaults",
        query_params=frozenset(),
        body_params=frozenset({"default_for_new_repos"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get repositories associated with an enterprise code security configuration":
    # ``per_page`` + cursor; 200 with an array, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-security/get-repositories-for-enterprise-configuration",
        method="GET",
        path="/enterprises/{enterprise}/code-security/configurations/{configuration_id}/repositories",
        query_params=frozenset({"per_page", "before", "after", "status"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get code security configurations for an organization": ``per_page`` + cursor; 200 with
    # an array, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-security/get-configurations-for-org",
        method="GET",
        path="/orgs/{org}/code-security/configurations",
        query_params=frozenset({"target_type", "per_page", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Create a code security configuration": the organization's fields; 201.
    RestOperation(
        operation_id="code-security/create-configuration",
        method="POST",
        path="/orgs/{org}/code-security/configurations",
        query_params=frozenset(),
        body_params=ORGANIZATION_CONFIGURATION_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get default code security configurations": an array, no paging.
    RestOperation(
        operation_id="code-security/get-default-configurations",
        method="GET",
        path="/orgs/{org}/code-security/configurations/defaults",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Detach configurations from repositories": body ``selected_repository_ids``; 204.
    RestOperation(
        operation_id="code-security/detach-configuration",
        method="DELETE",
        path="/orgs/{org}/code-security/configurations/detach",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get a code security configuration": path parameters only.
    RestOperation(
        operation_id="code-security/get-configuration",
        method="GET",
        path="/orgs/{org}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Update a code security configuration": the organization's fields.
    RestOperation(
        operation_id="code-security/update-configuration",
        method="PATCH",
        path="/orgs/{org}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=ORGANIZATION_CONFIGURATION_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Delete a code security configuration": path parameters only; 204.
    RestOperation(
        operation_id="code-security/delete-configuration",
        method="DELETE",
        path="/orgs/{org}/code-security/configurations/{configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Attach a configuration to repositories": body ``scope`` and ``selected_repository_ids``;
    # 202.
    RestOperation(
        operation_id="code-security/attach-configuration",
        method="POST",
        path="/orgs/{org}/code-security/configurations/{configuration_id}/attach",
        query_params=frozenset(),
        body_params=frozenset({"scope", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Set a code security configuration as a default for an organization": body
    # ``default_for_new_repos``.
    RestOperation(
        operation_id="code-security/set-configuration-as-default",
        method="PUT",
        path="/orgs/{org}/code-security/configurations/{configuration_id}/defaults",
        query_params=frozenset(),
        body_params=frozenset({"default_for_new_repos"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get repositories associated with a code security configuration": ``per_page`` + cursor;
    # 200 with an array, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-security/get-repositories-for-configuration",
        method="GET",
        path="/orgs/{org}/code-security/configurations/{configuration_id}/repositories",
        query_params=frozenset({"per_page", "before", "after", "status"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-security.md "Get the code security configuration associated with a repository": path parameters only.
    RestOperation(
        operation_id="code-security/get-configuration-for-repository",
        method="GET",
        path="/repos/{owner}/{repo}/code-security-configuration",
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
