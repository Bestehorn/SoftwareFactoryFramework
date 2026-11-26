"""The ``code-scanning`` family of the GitHub operations index: alerts, autofixes, analyses, SARIF uploads, CodeQL
databases and variant analyses, the default setup, and the AI scan settings.

Each record is the section of ``docs/api-reference/github/rest/code-scanning.md`` its operation ID names: its method
and path, the names of its ``query`` rows, and the first-level fields of its request body (a ``(body)`` row of Type
``constraint`` names no field). No path parameter of the family may contain ``/``, so no record has a
``multi_segment`` name. Four records page by ``link``, each ``200`` the array itself, so none has an item key:
``code-scanning/list-alerts-for-org``, ``code-scanning/list-alerts-for-repo``, ``code-scanning/list-alert-instances``
and ``code-scanning/list-recent-analyses``. ``code-scanning/list-codeql-databases`` documents no paging, so it sends
one request, as every other record does.

Every record sends the default media type: ``code-scanning/get-analysis`` and ``code-scanning/get-codeql-database``
print their JSON form, not the ``application/sarif+json`` analysis or the ``application/zip`` database (#31
DL-005). ``code-scanning/upload-sarif`` takes its Base64 ``sarif`` as a field value. Every record is sent by
``call <operation-id>`` (#28) but ``code-scanning/commit-autofix``: it commits to ``target_ref``, a branch write no
subcommand sends (#31 DL-003), so ``commands/call.py`` ``GATED_OPERATIONS`` maps it to no subcommand and ``call``
refuses it (issue #14 AC-3). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "code-scanning"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/code-scanning.md "Get the AI Scan setting for an organization": path parameters only; 200 with a
    # ``code-scanning-ai-scan-org-settings``.
    RestOperation(
        operation_id="code-scanning/get-ai-scan-enablement-for-org",
        method="GET",
        path="/orgs/{org}/code-scanning/ai-scan",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Update the AI Scan setting for an organization": body ``pr_scan``; 200 with a
    # ``code-scanning-ai-scan-org-settings``.
    RestOperation(
        operation_id="code-scanning/update-ai-scan-enablement-for-org",
        method="PATCH",
        path="/orgs/{org}/code-scanning/ai-scan",
        query_params=frozenset(),
        body_params=frozenset({"pr_scan"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "List code scanning alerts for an organization": 200 with an array and a ``Link`` header,
    # so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="code-scanning/list-alerts-for-org",
        method="GET",
        path="/orgs/{org}/code-scanning/alerts",
        query_params=frozenset(
            {
                "tool_name",
                "tool_guid",
                "before",
                "after",
                "page",
                "per_page",
                "direction",
                "state",
                "sort",
                "severity",
                "assignees",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get AI Scan enablement for a repository": path parameters only; 200 with a
    # ``code-scanning-ai-scan-enablement``.
    RestOperation(
        operation_id="code-scanning/get-ai-scan-enablement",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/ai-scan",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Update AI Scan enablement for a repository": body ``pr_scan``; 200 with a
    # ``code-scanning-ai-scan-enablement``.
    RestOperation(
        operation_id="code-scanning/update-ai-scan-enablement",
        method="PATCH",
        path="/repos/{owner}/{repo}/code-scanning/ai-scan",
        query_params=frozenset(),
        body_params=frozenset({"pr_scan"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "List code scanning alerts for a repository": 200 with an array, so it pages by ``link``
    # with no item key.
    RestOperation(
        operation_id="code-scanning/list-alerts-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/alerts",
        query_params=frozenset(
            {
                "tool_name",
                "tool_guid",
                "page",
                "per_page",
                "ref",
                "pr",
                "direction",
                "before",
                "after",
                "sort",
                "state",
                "severity",
                "assignees",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get a code scanning alert": path parameters only; 200 with a ``code-scanning-alert``.
    RestOperation(
        operation_id="code-scanning/get-alert",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Update a code scanning alert": the first-level body fields, its ``(body)`` constraint row
    # naming none; 200 with a ``code-scanning-alert``.
    RestOperation(
        operation_id="code-scanning/update-alert",
        method="PATCH",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}",
        query_params=frozenset(),
        body_params=frozenset({"state", "dismissed_reason", "dismissed_comment", "create_request", "assignees"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get the status of an autofix for a code scanning alert": path parameters only; 200 with a
    # ``code-scanning-autofix``.
    RestOperation(
        operation_id="code-scanning/get-autofix",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Create an autofix for a code scanning alert": path parameters only, no body; 200 or 202
    # with a ``code-scanning-autofix``.
    RestOperation(
        operation_id="code-scanning/create-autofix",
        method="POST",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Commit an autofix for a code scanning alert": body ``target_ref`` and ``message``; 201
    # with a ``code-scanning-autofix-commits-response``; it commits to ``target_ref``, so ``commands/call.py``
    # ``GATED_OPERATIONS`` refuses it.
    RestOperation(
        operation_id="code-scanning/commit-autofix",
        method="POST",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/autofix/commits",
        query_params=frozenset(),
        body_params=frozenset({"target_ref", "message"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "List instances of a code scanning alert": 200 with an array, so it pages by ``link`` with
    # no item key.
    RestOperation(
        operation_id="code-scanning/list-alert-instances",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances",
        query_params=frozenset({"page", "per_page", "ref", "pr"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "List code scanning analyses for a repository": 200 with an array, so it pages by ``link``
    # with no item key.
    RestOperation(
        operation_id="code-scanning/list-recent-analyses",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/analyses",
        query_params=frozenset(
            {"tool_name", "tool_guid", "page", "per_page", "pr", "ref", "sarif_id", "direction", "sort"}
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get a code scanning analysis for a repository": path parameters only; 200 with a
    # ``code-scanning-analysis``, its ``application/sarif+json`` form not asked for (#31 DL-005).
    RestOperation(
        operation_id="code-scanning/get-analysis",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/analyses/{analysis_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Delete a code scanning analysis from a repository": query ``confirm_delete``; 200 with a
    # ``code-scanning-analysis-deletion``.
    RestOperation(
        operation_id="code-scanning/delete-analysis",
        method="DELETE",
        path="/repos/{owner}/{repo}/code-scanning/analyses/{analysis_id}",
        query_params=frozenset({"confirm_delete"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "List CodeQL databases for a repository": 200 with an array and no ``Paging:`` line, so it
    # sends one request.
    RestOperation(
        operation_id="code-scanning/list-codeql-databases",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/codeql/databases",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get a CodeQL database for a repository": path parameters only; 200 with a
    # ``code-scanning-codeql-database``, its ``application/zip`` form not asked for (#31 DL-005).
    RestOperation(
        operation_id="code-scanning/get-codeql-database",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/codeql/databases/{language}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Delete a CodeQL database": path parameters only; 204 on success.
    RestOperation(
        operation_id="code-scanning/delete-codeql-database",
        method="DELETE",
        path="/repos/{owner}/{repo}/code-scanning/codeql/databases/{language}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Create a CodeQL variant analysis": the first-level body fields, its ``(body)`` constraint
    # row naming none; 201 with a ``code-scanning-variant-analysis``.
    RestOperation(
        operation_id="code-scanning/create-variant-analysis",
        method="POST",
        path="/repos/{owner}/{repo}/code-scanning/codeql/variant-analyses",
        query_params=frozenset(),
        body_params=frozenset({"language", "query_pack", "repositories", "repository_lists", "repository_owners"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get the summary of a CodeQL variant analysis": path parameters only; 200 with a
    # ``code-scanning-variant-analysis``.
    RestOperation(
        operation_id="code-scanning/get-variant-analysis",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get the analysis status of a repository in a CodeQL variant analysis": path parameters
    # only; 200 with a ``code-scanning-variant-analysis-repo-task``.
    RestOperation(
        operation_id="code-scanning/get-variant-analysis-repo-task",
        method="GET",
        path=(
            "/repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}"
            "/repos/{repo_owner}/{repo_name}"
        ),
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get a code scanning default setup configuration": path parameters only; 200 with a
    # ``code-scanning-default-setup``.
    RestOperation(
        operation_id="code-scanning/get-default-setup",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/default-setup",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Update a code scanning default setup configuration": the first-level body fields; 200
    # with an ``empty-object`` or 202 with a ``code-scanning-default-setup-update-response``.
    RestOperation(
        operation_id="code-scanning/update-default-setup",
        method="PATCH",
        path="/repos/{owner}/{repo}/code-scanning/default-setup",
        query_params=frozenset(),
        body_params=frozenset({"state", "runner_type", "runner_label", "query_suite", "threat_model", "languages"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Upload an analysis as SARIF data": the first-level body fields, ``sarif`` a Base64
    # string; 202 with a ``code-scanning-sarifs-receipt``.
    RestOperation(
        operation_id="code-scanning/upload-sarif",
        method="POST",
        path="/repos/{owner}/{repo}/code-scanning/sarifs",
        query_params=frozenset(),
        body_params=frozenset({"commit_sha", "ref", "sarif", "checkout_uri", "started_at", "tool_name", "validate"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/code-scanning.md "Get information about a SARIF upload": path parameters only; 200 with a
    # ``code-scanning-sarifs-status``.
    RestOperation(
        operation_id="code-scanning/get-sarif",
        method="GET",
        path="/repos/{owner}/{repo}/code-scanning/sarifs/{sarif_id}",
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
