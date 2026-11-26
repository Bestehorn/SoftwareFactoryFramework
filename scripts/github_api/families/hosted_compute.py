"""The ``hosted-compute`` family of the GitHub operations index: an organization's hosted compute network
configurations and network settings.

Each record is the section of ``docs/api-reference/github/rest/orgs.md`` (its ``network-configurations`` part) its
operation ID names: its method and path, the names of its ``query`` rows, and the first-level fields of its request
body. ``hosted-compute/list-network-configurations-for-org`` alone pages, by ``link``: its ``Paging:`` line reads
"items in `network_configurations`", the key "Lists wrapped in an object" names for it. The two ``get-network-*``
records answer one object with a ``Link`` header, which is no list, so they are ``Paging.NONE`` (issue #33 DL-006),
as is every other record. No path parameter of the family may contain ``/``, so ``multi_segment`` is empty
throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "hosted-compute"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/orgs.md "List hosted compute network configurations for an organization": query ``page`` and ``per_page``
    # only; page-based, items in ``network_configurations``.
    RestOperation(
        operation_id="hosted-compute/list-network-configurations-for-org",
        method="GET",
        path="/orgs/{org}/settings/network-configurations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="network_configurations",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Create a hosted compute network configuration for an organization": the first-level body fields; 201
    # with a ``network-configuration``.
    RestOperation(
        operation_id="hosted-compute/create-network-configuration-for-org",
        method="POST",
        path="/orgs/{org}/settings/network-configurations",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "compute_service",
                "network_settings_ids",
                "failover_network_settings_ids",
                "failover_network_enabled",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get a hosted compute network configuration for an organization": path parameters only; 200 with a
    # ``network-configuration``; a ``Link`` header on one object, so it does not page.
    RestOperation(
        operation_id="hosted-compute/get-network-configuration-for-org",
        method="GET",
        path="/orgs/{org}/settings/network-configurations/{network_configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Update a hosted compute network configuration for an organization": the first-level body fields; 200
    # with a ``network-configuration``.
    RestOperation(
        operation_id="hosted-compute/update-network-configuration-for-org",
        method="PATCH",
        path="/orgs/{org}/settings/network-configurations/{network_configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "compute_service",
                "network_settings_ids",
                "failover_network_settings_ids",
                "failover_network_enabled",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Delete a hosted compute network configuration from an organization": path parameters only; 204 on
    # success.
    RestOperation(
        operation_id="hosted-compute/delete-network-configuration-from-org",
        method="DELETE",
        path="/orgs/{org}/settings/network-configurations/{network_configuration_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/orgs.md "Get a hosted compute network settings resource for an organization": path parameters only; 200 with
    # a ``network-settings``; a ``Link`` header on one object, so it does not page.
    RestOperation(
        operation_id="hosted-compute/get-network-settings-for-org",
        method="GET",
        path="/orgs/{org}/settings/network-settings/{network_settings_id}",
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
