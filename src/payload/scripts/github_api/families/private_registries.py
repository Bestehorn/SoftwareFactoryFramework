"""The ``private-registries`` family of the GitHub operations index: an organization's private registry
configurations.

Each record is the section of ``docs/api-reference/github/rest/private-registries.md`` its operation ID names, in the
order of the file: its method and path, the names of its ``query`` rows, and the first-level fields of its request
body. The create and update sections document the same fields, ``REGISTRY_FIELDS``; a write sends ``encrypted_value``
and ``key_id`` as given (#31 DL-002). No path parameter of the family may contain ``/``, so ``multi_segment`` is
empty, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

``private-registries/list-org-private-registries`` alone has a ``Paging:`` line: it pages by ``link``, its items in
``configurations`` (``conventions.md`` "Lists wrapped in an object"). ``private-registries/get-org-public-key`` sends a
``Link`` header on one object, not an array, so it sends one request, as every other record does.

Every record is sent by ``call <operation-id>`` (#28); none writes a branch. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "private-registries"

#: The first-level body fields of "Create a private registry for an organization" and "Update a private registry for
#: an organization".
REGISTRY_FIELDS: FrozenSet[str] = frozenset(
    {
        "registry_type",
        "url",
        "username",
        "replaces_base",
        "encrypted_value",
        "key_id",
        "visibility",
        "selected_repository_ids",
        "auth_type",
        "tenant_id",
        "client_id",
        "aws_region",
        "account_id",
        "role_name",
        "domain",
        "domain_owner",
        "jfrog_oidc_provider_name",
        "audience",
        "identity_mapping_name",
        "namespace",
        "service_slug",
        "api_host",
        "workload_identity_provider",
        "service_account",
    }
)

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/private-registries.md "List private registries for an organization": page-based, items in
    # ``configurations`` (with ``total_count``).
    RestOperation(
        operation_id="private-registries/list-org-private-registries",
        method="GET",
        path="/orgs/{org}/private-registries",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="configurations",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/private-registries.md "Create a private registry for an organization": the registry fields; 201.
    RestOperation(
        operation_id="private-registries/create-org-private-registry",
        method="POST",
        path="/orgs/{org}/private-registries",
        query_params=frozenset(),
        body_params=REGISTRY_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/private-registries.md "Get private registries public key for an organization": path parameters only; 200
    # with one object and a ``Link`` header, so it does not page.
    RestOperation(
        operation_id="private-registries/get-org-public-key",
        method="GET",
        path="/orgs/{org}/private-registries/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/private-registries.md "Get a private registry for an organization": path parameters only.
    RestOperation(
        operation_id="private-registries/get-org-private-registry",
        method="GET",
        path="/orgs/{org}/private-registries/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/private-registries.md "Update a private registry for an organization": the registry fields; 204.
    RestOperation(
        operation_id="private-registries/update-org-private-registry",
        method="PATCH",
        path="/orgs/{org}/private-registries/{secret_name}",
        query_params=frozenset(),
        body_params=REGISTRY_FIELDS,
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/private-registries.md "Delete a private registry for an organization": path parameters only; 204.
    RestOperation(
        operation_id="private-registries/delete-org-private-registry",
        method="DELETE",
        path="/orgs/{org}/private-registries/{secret_name}",
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
