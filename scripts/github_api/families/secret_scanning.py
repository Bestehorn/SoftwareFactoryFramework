"""The ``secret-scanning`` family of the GitHub operations index: custom patterns, push protection and secret scanning
alerts.

Each record is the section of ``docs/api-reference/github/rest/secret-scanning.md`` its operation ID names: its method
and path, the names of its ``query`` rows, and the first-level fields of its request body (``patterns[].name`` is a
field of each ``patterns`` item; a ``(body)`` constraint row names none). No path parameter of the family may contain
``/``, so no record has a multi-segment parameter. The five sections with a ``Paging:`` line page by ``link`` and
return a bare array, so none has an item key: the two custom-pattern lists are cursor-based alone and take no
``per_page``, the two alert lists and ``secret-scanning/list-locations-for-alert`` take one. Every other record sends
one request, ``secret-scanning/list-org-pattern-configs`` (one object) included.

Every record is sent by ``call <operation-id>`` (#28); none is gated, so
``secret-scanning/create-push-protection-bypass`` is callable. The alert lists and ``secret-scanning/get-alert`` print
each alert's ``secret`` unless the call gives ``--query hide_secret=true``. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "secret-scanning"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/secret-scanning.md "List organization custom patterns": the filter, sort and cursor queries, no
    # ``per_page``; 200 with an array of ``secret-scanning-custom-pattern`` and a ``Link`` header, so it pages by
    # ``link`` with no item key.
    RestOperation(
        operation_id="secret-scanning/list-org-custom-patterns",
        method="GET",
        path="/orgs/{org}/secret-scanning/custom-patterns",
        query_params=frozenset({"state", "push_protection", "sort", "direction", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Bulk create organization custom patterns": body ``patterns`` (an array of patterns);
    # 201 with an object.
    RestOperation(
        operation_id="secret-scanning/bulk-create-org-custom-patterns",
        method="POST",
        path="/orgs/{org}/secret-scanning/custom-patterns",
        query_params=frozenset(),
        body_params=frozenset({"patterns"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Bulk delete organization custom patterns": a ``DELETE`` with a body, ``patterns`` and
    # ``post_delete_action``; 204 on success.
    RestOperation(
        operation_id="secret-scanning/bulk-delete-org-custom-patterns",
        method="DELETE",
        path="/orgs/{org}/secret-scanning/custom-patterns",
        query_params=frozenset(),
        body_params=frozenset({"patterns", "post_delete_action"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Update an organization custom pattern": the first-level body fields; 200 with a
    # ``secret-scanning-custom-pattern``.
    RestOperation(
        operation_id="secret-scanning/update-org-custom-pattern",
        method="PATCH",
        path="/orgs/{org}/secret-scanning/custom-patterns/{pattern_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {"pattern", "start_delimiter", "end_delimiter", "must_match", "must_not_match", "custom_pattern_version"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "List repository custom patterns": the filter, sort and cursor queries, no ``per_page``;
    # 200 with an array of ``secret-scanning-custom-pattern`` and a ``Link`` header, so it pages by ``link`` with no
    # item key.
    RestOperation(
        operation_id="secret-scanning/list-repo-custom-patterns",
        method="GET",
        path="/repos/{owner}/{repo}/secret-scanning/custom-patterns",
        query_params=frozenset({"state", "push_protection", "sort", "direction", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Bulk create repository custom patterns": body ``patterns`` (an array of patterns); 201
    # with an object.
    RestOperation(
        operation_id="secret-scanning/bulk-create-repo-custom-patterns",
        method="POST",
        path="/repos/{owner}/{repo}/secret-scanning/custom-patterns",
        query_params=frozenset(),
        body_params=frozenset({"patterns"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Bulk delete repository custom patterns": a ``DELETE`` with a body, ``patterns`` and
    # ``post_delete_action``; 204 on success.
    RestOperation(
        operation_id="secret-scanning/bulk-delete-repo-custom-patterns",
        method="DELETE",
        path="/repos/{owner}/{repo}/secret-scanning/custom-patterns",
        query_params=frozenset(),
        body_params=frozenset({"patterns", "post_delete_action"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Update a repository custom pattern": the first-level body fields; 200 with a
    # ``secret-scanning-custom-pattern``.
    RestOperation(
        operation_id="secret-scanning/update-repo-custom-pattern",
        method="PATCH",
        path="/repos/{owner}/{repo}/secret-scanning/custom-patterns/{pattern_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {"pattern", "start_delimiter", "end_delimiter", "must_match", "must_not_match", "custom_pattern_version"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "List organization pattern configurations": path parameters only; 200 with one
    # ``secret-scanning-pattern-configuration``, so it sends one request.
    RestOperation(
        operation_id="secret-scanning/list-org-pattern-configs",
        method="GET",
        path="/orgs/{org}/secret-scanning/pattern-configurations",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Update organization pattern configurations": body ``pattern_config_version``,
    # ``provider_pattern_settings`` and ``custom_pattern_settings``; 200 with an object.
    RestOperation(
        operation_id="secret-scanning/update-org-pattern-configs",
        method="PATCH",
        path="/orgs/{org}/secret-scanning/pattern-configurations",
        query_params=frozenset(),
        body_params=frozenset({"pattern_config_version", "provider_pattern_settings", "custom_pattern_settings"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "List secret scanning alerts for an organization": the filter, sort, page and cursor
    # queries; 200 with an array of ``organization-secret-scanning-alert`` and a ``Link`` header, so it pages by
    # ``link`` with no item key.
    RestOperation(
        operation_id="secret-scanning/list-alerts-for-org",
        method="GET",
        path="/orgs/{org}/secret-scanning/alerts",
        query_params=frozenset(
            {
                "state",
                "secret_type",
                "exclude_secret_types",
                "exclude_providers",
                "providers",
                "resolution",
                "assignee",
                "sort",
                "direction",
                "page",
                "per_page",
                "before",
                "after",
                "validity",
                "is_publicly_leaked",
                "is_multi_repo",
                "hide_secret",
                "is_bypassed",
                "included_metadata",
                "owner_email_hash",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "List secret scanning alerts for a repository": the filter, sort, page and cursor
    # queries; 200 with an array of ``secret-scanning-alert``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="secret-scanning/list-alerts-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/secret-scanning/alerts",
        query_params=frozenset(
            {
                "state",
                "secret_type",
                "exclude_secret_types",
                "exclude_providers",
                "providers",
                "resolution",
                "assignee",
                "sort",
                "direction",
                "page",
                "per_page",
                "before",
                "after",
                "validity",
                "is_publicly_leaked",
                "is_multi_repo",
                "hide_secret",
                "is_bypassed",
                "included_metadata",
                "owner_email_hash",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Get a secret scanning alert": query ``hide_secret``; 200 with a
    # ``secret-scanning-alert-with-metadata``.
    RestOperation(
        operation_id="secret-scanning/get-alert",
        method="GET",
        path="/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}",
        query_params=frozenset({"hide_secret"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Update a secret scanning alert": the first-level body fields; 200 with a
    # ``secret-scanning-alert-with-metadata``.
    RestOperation(
        operation_id="secret-scanning/update-alert",
        method="PATCH",
        path="/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}",
        query_params=frozenset(),
        body_params=frozenset({"state", "resolution", "resolution_comment", "assignee", "validity"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "List locations for a secret scanning alert": query ``page`` and ``per_page``; 200 with
    # an array of ``secret-scanning-location`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="secret-scanning/list-locations-for-alert",
        method="GET",
        path="/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Create a push protection bypass": body ``reason`` and ``placeholder_id``; 200 with a
    # ``secret-scanning-push-protection-bypass``.
    RestOperation(
        operation_id="secret-scanning/create-push-protection-bypass",
        method="POST",
        path="/repos/{owner}/{repo}/secret-scanning/push-protection-bypasses",
        query_params=frozenset(),
        body_params=frozenset({"reason", "placeholder_id"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/secret-scanning.md "Get secret scanning scan history for a repository": path parameters only; 200 with a
    # ``secret-scanning-scan-history``.
    RestOperation(
        operation_id="secret-scanning/get-scan-history",
        method="GET",
        path="/repos/{owner}/{repo}/secret-scanning/scan-history",
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
