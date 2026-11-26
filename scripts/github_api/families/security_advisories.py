"""The ``security-advisories`` family of the GitHub operations index: the global advisories and a repository's
security advisories, their comments, CVE requests and temporary private forks.

Each record is the section of ``docs/api-reference/github/rest/security-advisories.md`` its operation ID names, in the
order of the file: its method and path, the names of its ``query`` rows, and the first-level fields of its request
body (``vulnerabilities[].package`` is a field of each ``vulnerabilities`` item). No path parameter of the family may
contain ``/``, so ``multi_segment`` is empty, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The four sections with a ``Paging:`` line page by ``link`` with no item key, the response body being the array: the
three advisory lists by ``per_page`` and a cursor, ``security-advisories/list-repository-advisory-comments`` by page.
Every other record sends one request.

Every record is sent by ``call <operation-id>`` (#28). ``security-advisories/create-fork`` creates a temporary private
fork, a repository, and writes no branch, so ``call`` does not refuse it (issue #33 Residuals). No operation of the
family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "security-advisories"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/security-advisories.md "List global security advisories": ``per_page`` + cursor; 200 with an array of
    # ``global-advisory``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="security-advisories/list-global-advisories",
        method="GET",
        path="/advisories",
        query_params=frozenset(
            {
                "ghsa_id",
                "type",
                "cve_id",
                "ecosystem",
                "severity",
                "cwes",
                "is_withdrawn",
                "affects",
                "published",
                "updated",
                "modified",
                "epss_percentage",
                "epss_percentile",
                "before",
                "after",
                "direction",
                "per_page",
                "sort",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Get a global security advisory": path parameters only; 200 with a
    # ``global-advisory``.
    RestOperation(
        operation_id="security-advisories/get-global-advisory",
        method="GET",
        path="/advisories/{ghsa_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "List repository security advisories for an organization": ``per_page`` + cursor;
    # 200 with an array of ``repository-advisory``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="security-advisories/list-org-repository-advisories",
        method="GET",
        path="/orgs/{org}/security-advisories",
        query_params=frozenset({"direction", "sort", "before", "after", "per_page", "state"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "List repository security advisories": ``per_page`` + cursor; 200 with an array of
    # ``repository-advisory``, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="security-advisories/list-repository-advisories",
        method="GET",
        path="/repos/{owner}/{repo}/security-advisories",
        query_params=frozenset({"direction", "sort", "before", "after", "per_page", "state"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Create a repository security advisory": the first-level body fields; 201 with a
    # ``repository-advisory``.
    RestOperation(
        operation_id="security-advisories/create-repository-advisory",
        method="POST",
        path="/repos/{owner}/{repo}/security-advisories",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "summary",
                "description",
                "cve_id",
                "vulnerabilities",
                "cwe_ids",
                "credits",
                "severity",
                "cvss_vector_string",
                "start_private_fork",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Privately report a security vulnerability": the first-level body fields; 201 with a
    # ``repository-advisory``.
    RestOperation(
        operation_id="security-advisories/create-private-vulnerability-report",
        method="POST",
        path="/repos/{owner}/{repo}/security-advisories/reports",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "summary",
                "description",
                "vulnerabilities",
                "cwe_ids",
                "severity",
                "cvss_vector_string",
                "start_private_fork",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Get a repository security advisory": path parameters only; 200 with a
    # ``repository-advisory``.
    RestOperation(
        operation_id="security-advisories/get-repository-advisory",
        method="GET",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Update a repository security advisory": the first-level body fields; 200 with a
    # ``repository-advisory``.
    RestOperation(
        operation_id="security-advisories/update-repository-advisory",
        method="PATCH",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "summary",
                "description",
                "cve_id",
                "vulnerabilities",
                "cwe_ids",
                "credits",
                "severity",
                "cvss_vector_string",
                "state",
                "collaborating_users",
                "collaborating_teams",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "List repository security advisory comments": page-based; 200 with an array of
    # ``repository-advisory-comment`` and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="security-advisories/list-repository-advisory-comments",
        method="GET",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/comments",
        query_params=frozenset({"since", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Create a repository advisory comment": body ``body``; 201.
    RestOperation(
        operation_id="security-advisories/create-repository-advisory-comment",
        method="POST",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/comments",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Get a repository advisory comment": path parameters only.
    RestOperation(
        operation_id="security-advisories/get-repository-advisory-comment",
        method="GET",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Update a repository advisory comment": body ``body``.
    RestOperation(
        operation_id="security-advisories/update-repository-advisory-comment",
        method="PATCH",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/comments/{comment_id}",
        query_params=frozenset(),
        body_params=frozenset({"body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Request a CVE for a repository security advisory": path parameters only; 202.
    RestOperation(
        operation_id="security-advisories/create-repository-advisory-cve-request",
        method="POST",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/cve",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/security-advisories.md "Create a temporary private fork": path parameters only; 202 with a
    # ``full-repository``.
    RestOperation(
        operation_id="security-advisories/create-fork",
        method="POST",
        path="/repos/{owner}/{repo}/security-advisories/{ghsa_id}/forks",
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
