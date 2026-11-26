"""The ``oidc`` family of the GitHub operations index: the OIDC custom property inclusions of an enterprise and an
organization, and an organization's subject claim template.

The family has no file of its own: each record is the section of ``docs/api-reference/github/rest/actions.md``
("oidc") its operation ID names, in the order of that file: its method and path, and the first-level fields of its
request body; no section has a ``query`` row. No path parameter may contain ``/``, so ``multi_segment`` is empty, and
every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``. The two list sections answer an array with no
``Paging:`` line and no ``Link`` header, so every record is ``Paging.NONE`` and sends one request.

Every record is sent by ``call <operation-id>`` (#28); none writes a branch. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "oidc"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/actions.md "List OIDC custom property inclusions for an enterprise": path parameters only; an array, no
    # paging.
    RestOperation(
        operation_id="oidc/list-oidc-custom-property-inclusions-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/actions/oidc/customization/properties/repo",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create an OIDC custom property inclusion for an enterprise": body ``custom_property_name``; 201.
    RestOperation(
        operation_id="oidc/create-oidc-custom-property-inclusion-for-enterprise",
        method="POST",
        path="/enterprises/{enterprise}/actions/oidc/customization/properties/repo",
        query_params=frozenset(),
        body_params=frozenset({"custom_property_name"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an OIDC custom property inclusion for an enterprise": path parameters only; 204.
    RestOperation(
        operation_id="oidc/delete-oidc-custom-property-inclusion-for-enterprise",
        method="DELETE",
        path="/enterprises/{enterprise}/actions/oidc/customization/properties/repo/{custom_property_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List OIDC custom property inclusions for an organization": path parameters only; an array, no
    # paging.
    RestOperation(
        operation_id="oidc/list-oidc-custom-property-inclusions-for-org",
        method="GET",
        path="/orgs/{org}/actions/oidc/customization/properties/repo",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create an OIDC custom property inclusion for an organization": body ``custom_property_name``;
    # 201.
    RestOperation(
        operation_id="oidc/create-oidc-custom-property-inclusion-for-org",
        method="POST",
        path="/orgs/{org}/actions/oidc/customization/properties/repo",
        query_params=frozenset(),
        body_params=frozenset({"custom_property_name"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an OIDC custom property inclusion for an organization": path parameters only; 204.
    RestOperation(
        operation_id="oidc/delete-oidc-custom-property-inclusion-for-org",
        method="DELETE",
        path="/orgs/{org}/actions/oidc/customization/properties/repo/{custom_property_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get the customization template for an OIDC subject claim for an organization": path parameters
    # only; 200 with an ``oidc-custom-sub``.
    RestOperation(
        operation_id="oidc/get-oidc-custom-sub-template-for-org",
        method="GET",
        path="/orgs/{org}/actions/oidc/customization/sub",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set the customization template for an OIDC subject claim for an organization": body
    # ``include_claim_keys`` and ``use_immutable_subject``; 201.
    RestOperation(
        operation_id="oidc/update-oidc-custom-sub-template-for-org",
        method="PUT",
        path="/orgs/{org}/actions/oidc/customization/sub",
        query_params=frozenset(),
        body_params=frozenset({"include_claim_keys", "use_immutable_subject"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
