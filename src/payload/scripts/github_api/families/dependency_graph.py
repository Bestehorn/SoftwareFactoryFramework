"""The ``dependency-graph`` family of the GitHub operations index: dependency review, dependency submission and SBOMs.

Each record is the section of ``docs/api-reference/github/rest/dependency-graph.md`` its operation ID names: its method
and path, the names of its ``query`` rows, and the first-level fields of its request body (``job.id`` is a field of
``job``, ``manifests.*.name`` one of ``manifests``). No path parameter of the family may contain ``/``, so
``multi_segment`` is empty, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

No section has a ``Paging:`` line. ``dependency-graph/diff-range`` answers ``200`` with an array and a ``Link`` header,
so it pages by ``link`` with no item key (issue #33 DL-006). ``dependency-graph/export-sbom`` sends a ``Link`` header
on one object, not an array, so it sends one request, as every other record does.
``dependency-graph/fetch-sbom-report`` answers ``202`` or a ``302`` with a ``Location`` header; it is declared as a
plain record (#28 D3, issue #33 Residuals).

Every record is sent by ``call <operation-id>`` (#28); none writes a branch. No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "dependency-graph"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/dependency-graph.md "Get a diff of the dependencies between commits": query ``name``; 200 with an array of
    # objects and a ``Link`` header, so it pages by ``link`` with no item key.
    RestOperation(
        operation_id="dependency-graph/diff-range",
        method="GET",
        path="/repos/{owner}/{repo}/dependency-graph/compare/{basehead}",
        query_params=frozenset({"name"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependency-graph.md "Create a snapshot of dependencies for a repository": the first-level body fields; 201.
    RestOperation(
        operation_id="dependency-graph/create-repository-snapshot",
        method="POST",
        path="/repos/{owner}/{repo}/dependency-graph/snapshots",
        query_params=frozenset(),
        body_params=frozenset({"version", "job", "sha", "ref", "detector", "metadata", "manifests", "scanned"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependency-graph.md "Export a software bill of materials (SBOM) for a repository.": path parameters only;
    # 200 with one ``dependency-graph-spdx-sbom`` and a ``Link`` header, so it does not page.
    RestOperation(
        operation_id="dependency-graph/export-sbom",
        method="GET",
        path="/repos/{owner}/{repo}/dependency-graph/sbom",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependency-graph.md "Fetch a software bill of materials (SBOM) for a repository.": path parameters only;
    # 202, or 302 with a ``Location`` header.
    RestOperation(
        operation_id="dependency-graph/fetch-sbom-report",
        method="GET",
        path="/repos/{owner}/{repo}/dependency-graph/sbom/fetch-report/{sbom_uuid}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/dependency-graph.md "Request generation of a software bill of materials (SBOM) for a repository.": path
    # parameters only; 201.
    RestOperation(
        operation_id="dependency-graph/generate-sbom-report",
        method="GET",
        path="/repos/{owner}/{repo}/dependency-graph/sbom/generate-report",
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
