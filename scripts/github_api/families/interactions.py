"""The ``interactions`` family of the GitHub operations index: the interaction restrictions of an organization, a
repository and the authenticated user's public repositories, and the pull request creation cap with its bypass list.

Each record is the section of ``docs/api-reference/github/rest/interactions.md`` its operation ID names: its method
and path and the first-level fields of its request body; no operation of the family has a query row. No section has a
``Paging:`` line, so every record sends one request, ``get-pull-request-bypass-list-for-repo`` too, whose ``200`` is
an array with no ``Link`` header. No path parameter of the family may contain ``/``, so ``multi_segment`` is empty
throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No operation of the family is
pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "interactions"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/interactions.md "Get interaction restrictions for an organization": path parameters only; 200 with an
    # ``interaction-limit-response`` or an object.
    RestOperation(
        operation_id="interactions/get-restrictions-for-org",
        method="GET",
        path="/orgs/{org}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Set interaction restrictions for an organization": body ``limit`` and ``expiry``; 200 with
    # an ``interaction-limit-response``.
    RestOperation(
        operation_id="interactions/set-restrictions-for-org",
        method="PUT",
        path="/orgs/{org}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset({"limit", "expiry"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Remove interaction restrictions for an organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="interactions/remove-restrictions-for-org",
        method="DELETE",
        path="/orgs/{org}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Get pull request creation cap for an org": path parameters only; 200 with an object.
    RestOperation(
        operation_id="interactions/get-pull-request-creation-cap-for-org",
        method="GET",
        path="/orgs/{org}/interaction-limits/pulls/creation-cap",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Update pull request creation cap for an org": body ``enabled``, ``max_open_pull_requests``
    # and ``include_drafts``; 200 with an object.
    RestOperation(
        operation_id="interactions/update-pull-request-creation-cap-for-org",
        method="PATCH",
        path="/orgs/{org}/interaction-limits/pulls/creation-cap",
        query_params=frozenset(),
        body_params=frozenset({"enabled", "max_open_pull_requests", "include_drafts"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Get interaction restrictions for a repository": path parameters only; 200 with an
    # ``interaction-limit-response`` or an object.
    RestOperation(
        operation_id="interactions/get-restrictions-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Set interaction restrictions for a repository": body ``limit`` and ``expiry``; 200 with an
    # ``interaction-limit-response``.
    RestOperation(
        operation_id="interactions/set-restrictions-for-repo",
        method="PUT",
        path="/repos/{owner}/{repo}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset({"limit", "expiry"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Remove interaction restrictions for a repository": path parameters only; 204 on success.
    RestOperation(
        operation_id="interactions/remove-restrictions-for-repo",
        method="DELETE",
        path="/repos/{owner}/{repo}/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Get pull request creation cap bypass list for a repository": path parameters only; 200 with
    # an array of ``simple-user``.
    RestOperation(
        operation_id="interactions/get-pull-request-bypass-list-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/interaction-limits/pulls/bypass-list",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Add users to the pull request creation cap bypass list for a repository": body ``users``;
    # 204 on success.
    RestOperation(
        operation_id="interactions/set-pull-request-bypass-list-for-repo",
        method="PUT",
        path="/repos/{owner}/{repo}/interaction-limits/pulls/bypass-list",
        query_params=frozenset(),
        body_params=frozenset({"users"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Remove users from the pull request creation cap bypass list for a repository": body
    # ``users``; 204 on success.
    RestOperation(
        operation_id="interactions/remove-pull-request-bypass-list-for-repo",
        method="DELETE",
        path="/repos/{owner}/{repo}/interaction-limits/pulls/bypass-list",
        query_params=frozenset(),
        body_params=frozenset({"users"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Get pull request creation cap for a repository": path parameters only; 200 with an object.
    RestOperation(
        operation_id="interactions/get-pull-request-creation-cap-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/interaction-limits/pulls/creation-cap",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Update pull request creation cap for a repository": body ``enabled``,
    # ``max_open_pull_requests`` and ``include_drafts``; 200 with an object.
    RestOperation(
        operation_id="interactions/update-pull-request-creation-cap-for-repo",
        method="PATCH",
        path="/repos/{owner}/{repo}/interaction-limits/pulls/creation-cap",
        query_params=frozenset(),
        body_params=frozenset({"enabled", "max_open_pull_requests", "include_drafts"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Get interaction restrictions for your public repositories": no parameters; 200 with an
    # ``interaction-limit-response`` or an object, or 204.
    RestOperation(
        operation_id="interactions/get-restrictions-for-authenticated-user",
        method="GET",
        path="/user/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Set interaction restrictions for your public repositories": body ``limit`` and ``expiry``;
    # 200 with an ``interaction-limit-response``.
    RestOperation(
        operation_id="interactions/set-restrictions-for-authenticated-user",
        method="PUT",
        path="/user/interaction-limits",
        query_params=frozenset(),
        body_params=frozenset({"limit", "expiry"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/interactions.md "Remove interaction restrictions from your public repositories": no parameters; 204 on
    # success.
    RestOperation(
        operation_id="interactions/remove-restrictions-for-authenticated-user",
        method="DELETE",
        path="/user/interaction-limits",
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
