"""The ``apps`` family of the GitHub operations index: GitHub Apps and their installations, installation access tokens,
the Marketplace listing and its stubbed twin, OAuth application grants and tokens, and the app's webhook configuration
and deliveries.

Each record is the section of ``docs/api-reference/github/rest/apps.md`` its operation ID names: its method and path,
the names of its ``query`` rows, and the first-level fields of its request body (``permissions.contents`` is a field of
``permissions``). No path parameter of the family may contain ``/``, so every ``multi_segment`` is empty. A section
with a ``Paging:`` line pages by ``link``: ``apps/list-repos-accessible-to-installation`` and
``apps/list-installation-repos-for-authenticated-user`` hold their items under ``repositories``,
``apps/list-installations-for-authenticated-user`` under ``installations`` (``conventions.md`` "Lists wrapped in an
object"), and every other list is a bare array with no item key; every other record sends one request.

A record whose endpoint authenticates as the app (a JWT, or the client ID and secret, ``conventions.md``
"Authentication") is sent with the configured token like every record (issue #29 DL-002); no other credential is
read. Every record is sent by ``call <operation-id>`` (#28), ``{owner}`` and ``{repo}`` defaulting to the ``origin``
repository. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "apps"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/apps.md "Get the authenticated app": no parameters; 200 with an ``integration``.
    RestOperation(
        operation_id="apps/get-authenticated",
        method="GET",
        path="/app",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Create a GitHub App from a manifest": path parameters only; 201 with an object.
    RestOperation(
        operation_id="apps/create-from-manifest",
        method="POST",
        path="/app-manifests/{code}/conversions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List installation requests for the authenticated app": query ``per_page``, ``page``; 200 with an
    # array of ``integration-installation-request``; its ``Paging:`` line makes it page by ``link``, no item key.
    RestOperation(
        operation_id="apps/list-installation-requests-for-authenticated-app",
        method="GET",
        path="/app/installation-requests",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List installations for the authenticated app": query ``per_page``, ``page``, ``since``,
    # ``outdated``; 200 with an array of ``installation`` and a ``Link`` header, so it pages by ``link``, no item key.
    RestOperation(
        operation_id="apps/list-installations",
        method="GET",
        path="/app/installations",
        query_params=frozenset({"per_page", "page", "since", "outdated"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get an installation for the authenticated app": path parameters only; 200 with an ``installation``.
    RestOperation(
        operation_id="apps/get-installation",
        method="GET",
        path="/app/installations/{installation_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Delete an installation for the authenticated app": path parameters only; 204 on success.
    RestOperation(
        operation_id="apps/delete-installation",
        method="DELETE",
        path="/app/installations/{installation_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Create an installation access token for an app": optional body ``repositories``,
    # ``repository_ids`` and ``permissions`` (``permissions.<name>`` its members); 201 with an ``installation-token``.
    RestOperation(
        operation_id="apps/create-installation-access-token",
        method="POST",
        path="/app/installations/{installation_id}/access_tokens",
        query_params=frozenset(),
        body_params=frozenset({"repositories", "repository_ids", "permissions"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Suspend an app installation": path parameters only; 204 on success.
    RestOperation(
        operation_id="apps/suspend-installation",
        method="PUT",
        path="/app/installations/{installation_id}/suspended",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Unsuspend an app installation": path parameters only; 204 on success.
    RestOperation(
        operation_id="apps/unsuspend-installation",
        method="DELETE",
        path="/app/installations/{installation_id}/suspended",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Create a scoped access token": the first-level body fields (``permissions.<name>`` members of
    # ``permissions``); 200 with an ``authorization``.
    RestOperation(
        operation_id="apps/scope-token",
        method="POST",
        path="/applications/{client_id}/token/scoped",
        query_params=frozenset(),
        body_params=frozenset({"access_token", "target", "target_id", "repositories", "repository_ids", "permissions"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get an app": path parameters only; 200 with an ``integration``.
    RestOperation(
        operation_id="apps/get-by-slug",
        method="GET",
        path="/apps/{app_slug}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get an organization installation for the authenticated app": path parameters only; 200 with an
    # ``installation``.
    RestOperation(
        operation_id="apps/get-org-installation",
        method="GET",
        path="/orgs/{org}/installation",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a repository installation for the authenticated app": path parameters only; 200 with an
    # ``installation``.
    RestOperation(
        operation_id="apps/get-repo-installation",
        method="GET",
        path="/repos/{owner}/{repo}/installation",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a user installation for the authenticated app": path parameters only; 200 with an
    # ``installation``.
    RestOperation(
        operation_id="apps/get-user-installation",
        method="GET",
        path="/users/{username}/installation",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List repositories accessible to the app installation": query ``per_page``, ``page``; 200 with an
    # object holding the items in ``repositories`` and a ``Link`` header, so it pages by ``link``.
    RestOperation(
        operation_id="apps/list-repos-accessible-to-installation",
        method="GET",
        path="/installation/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Revoke an installation access token": no parameters; 204 on success.
    RestOperation(
        operation_id="apps/revoke-installation-access-token",
        method="DELETE",
        path="/installation/token",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List app installations accessible to the user access token": query ``per_page``, ``page``; 200
    # with an object holding the items in ``installations`` and a ``Link`` header, so it pages by ``link``.
    RestOperation(
        operation_id="apps/list-installations-for-authenticated-user",
        method="GET",
        path="/user/installations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="installations",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List repositories accessible to the user access token": query ``per_page``, ``page``; 200 with an
    # object holding the items in ``repositories`` and a ``Link`` header, so it pages by ``link``.
    RestOperation(
        operation_id="apps/list-installation-repos-for-authenticated-user",
        method="GET",
        path="/user/installations/{installation_id}/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Add a repository to an app installation": path parameters only; 204 on success.
    RestOperation(
        operation_id="apps/add-repo-to-installation-for-authenticated-user",
        method="PUT",
        path="/user/installations/{installation_id}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Remove a repository from an app installation": path parameters only; 204 on success.
    RestOperation(
        operation_id="apps/remove-repo-from-installation-for-authenticated-user",
        method="DELETE",
        path="/user/installations/{installation_id}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a subscription plan for an account": path parameters only; 200 with a ``marketplace-purchase``.
    RestOperation(
        operation_id="apps/get-subscription-plan-for-account",
        method="GET",
        path="/marketplace_listing/accounts/{account_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List plans": query ``per_page``, ``page``; 200 with an array of ``marketplace-listing-plan`` and a
    # ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-plans",
        method="GET",
        path="/marketplace_listing/plans",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List accounts for a plan": query ``sort``, ``direction``, ``per_page``, ``page``; 200 with an array
    # of ``marketplace-purchase`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-accounts-for-plan",
        method="GET",
        path="/marketplace_listing/plans/{plan_id}/accounts",
        query_params=frozenset({"sort", "direction", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a subscription plan for an account (stubbed)": path parameters only; 200 with a
    # ``marketplace-purchase``.
    RestOperation(
        operation_id="apps/get-subscription-plan-for-account-stubbed",
        method="GET",
        path="/marketplace_listing/stubbed/accounts/{account_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List plans (stubbed)": query ``per_page``, ``page``; 200 with an array of
    # ``marketplace-listing-plan`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-plans-stubbed",
        method="GET",
        path="/marketplace_listing/stubbed/plans",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List accounts for a plan (stubbed)": query ``sort``, ``direction``, ``per_page``, ``page``; 200
    # with an array of ``marketplace-purchase`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-accounts-for-plan-stubbed",
        method="GET",
        path="/marketplace_listing/stubbed/plans/{plan_id}/accounts",
        query_params=frozenset({"sort", "direction", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List subscriptions for the authenticated user": query ``per_page``, ``page``; 200 with an array of
    # ``user-marketplace-purchase`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-subscriptions-for-authenticated-user",
        method="GET",
        path="/user/marketplace_purchases",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List subscriptions for the authenticated user (stubbed)": query ``per_page``, ``page``; 200 with an
    # array of ``user-marketplace-purchase`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="apps/list-subscriptions-for-authenticated-user-stubbed",
        method="GET",
        path="/user/marketplace_purchases/stubbed",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Delete an app authorization": body ``access_token``; 204 on success.
    RestOperation(
        operation_id="apps/delete-authorization",
        method="DELETE",
        path="/applications/{client_id}/grant",
        query_params=frozenset(),
        body_params=frozenset({"access_token"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Check a token": body ``access_token``; 200 with an ``authorization``.
    RestOperation(
        operation_id="apps/check-token",
        method="POST",
        path="/applications/{client_id}/token",
        query_params=frozenset(),
        body_params=frozenset({"access_token"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Reset a token": body ``access_token``; 200 with an ``authorization``.
    RestOperation(
        operation_id="apps/reset-token",
        method="PATCH",
        path="/applications/{client_id}/token",
        query_params=frozenset(),
        body_params=frozenset({"access_token"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Delete an app token": body ``access_token``; 204 on success.
    RestOperation(
        operation_id="apps/delete-token",
        method="DELETE",
        path="/applications/{client_id}/token",
        query_params=frozenset(),
        body_params=frozenset({"access_token"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a webhook configuration for an app": no parameters; 200 with a ``webhook-config``.
    RestOperation(
        operation_id="apps/get-webhook-config-for-app",
        method="GET",
        path="/app/hook/config",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Update a webhook configuration for an app": body ``url``, ``content_type``, ``secret``,
    # ``insecure_ssl``; 200 with a ``webhook-config``.
    RestOperation(
        operation_id="apps/update-webhook-config-for-app",
        method="PATCH",
        path="/app/hook/config",
        query_params=frozenset(),
        body_params=frozenset({"url", "content_type", "secret", "insecure_ssl"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "List deliveries for an app webhook": query ``per_page``, ``cursor``, ``status``; 200 with an array
    # of ``hook-delivery-item``; its ``Paging:`` line (cursor-based) makes it page by ``link``, no item key.
    RestOperation(
        operation_id="apps/list-webhook-deliveries",
        method="GET",
        path="/app/hook/deliveries",
        query_params=frozenset({"per_page", "cursor", "status"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Get a delivery for an app webhook": path parameters only; 200 with a ``hook-delivery``.
    RestOperation(
        operation_id="apps/get-webhook-delivery",
        method="GET",
        path="/app/hook/deliveries/{delivery_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/apps.md "Redeliver a delivery for an app webhook": path parameters only; 202 with an object.
    RestOperation(
        operation_id="apps/redeliver-webhook-delivery",
        method="POST",
        path="/app/hook/deliveries/{delivery_id}/attempts",
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
