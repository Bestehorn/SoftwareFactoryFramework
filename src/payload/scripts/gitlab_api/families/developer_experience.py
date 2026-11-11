"""The ``developer-experience`` endpoint family of the GitLab wrapper: the examples of the REST API pages, and the
three tenant-scale References whose keys sort to this family.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/developer-experience.md`` or ``rest/tenant-scale.md`` (issue #13, design.md D1 and D5;
issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section: the method, the path as
``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- an ``array of string`` row (``topic``) is ``Kind.ARRAY``, a ``hash`` row (``custom_attributes``) ``HASH``, every
  other row ``SCALAR``; no row is required; every body is JSON and no record has ``fixed`` values;
- "Sudo" (by its ``page`` row), "List all projects" and "List all projects assigned to a topic" are ``Paging.OFFSET``,
  every other record ``Paging.NONE``.

The keys ``GET /projects`` and ``DELETE /projects/:id/share/:group_id`` are carried by rows of both pages; they sort to
this family, so ``tenant-scale#list-all-projects``, ``#list-all-projects-assigned-to-a-topic`` and
``#delete-a-shared-project-link-in-a-group`` are declared here, not in ``families/tenant_scale.py`` (issue #38,
DL-003), and one key is the endpoint of more than one record. "Namespaced paths" and "File path, branches, and tags
name" write literal example paths (project ``1``, ``diaspora/diaspora``).

A section with several endpoints has one record per endpoint, each with its Reference's ID (issue #63, design.md D1,
D8): the base record on its first ``/projects/:id/...`` endpoint, else on its first, then one per other endpoint in
the order the section's endpoint line lists them, each a copy of the base record but for its method, its path and any
``Param`` naming a path parameter of its own path. "File path, branches, and tags name" lists three literal endpoints,
none a ``/projects/:id/...`` one: its base record takes the first, and ``call --endpoint 'GET <path>'`` names each of
the other two, sent as written, ``%2F`` kept, with no path parameter and so no ``id`` default. ``PENDING`` is empty.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "developer-experience"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "REST API: Path parameters"; the key of `tenant-scale#delete-a-shared-project-link-in-a-group` too; the section
    # has no table.
    RestOperation(
        operation_id="developer-experience#path-parameters",
        method="DELETE",
        path="/projects/:id/share/:group_id",
    ),
    # "REST API: Namespaced paths"; a literal example path; the section has no table.
    RestOperation(
        operation_id="developer-experience#namespaced-paths",
        method="GET",
        path="/projects/diaspora%2Fdiaspora",
    ),
    # "REST API: File path, branches, and tags name"; its base record, on the first of its three literal example
    # endpoints.
    RestOperation(
        operation_id="developer-experience#file-path-branches-and-tags-name",
        method="GET",
        path="/projects/1/repository/files/src%2FREADME.md",
    ),
    # "REST API: File path, branches, and tags name"; its second endpoint, a copy of the base record (issue #63, D8).
    RestOperation(
        operation_id="developer-experience#file-path-branches-and-tags-name",
        method="GET",
        path="/projects/1/branches/my%2Fbranch/commits",
    ),
    # "REST API: File path, branches, and tags name"; its third endpoint, a copy of the base record (issue #63, D8).
    RestOperation(
        operation_id="developer-experience#file-path-branches-and-tags-name",
        method="GET",
        path="/projects/1/repository/tags/my%2Ftag",
    ),
    # "REST API authentication: Sudo"; paged by its `page` row.
    RestOperation(
        operation_id="developer-experience#sudo",
        method="GET",
        path="/projects",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="archived", location=Location.QUERY),
            Param(name="visibility", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="search_namespaces", location=Location.QUERY),
            Param(name="owned", location=Location.QUERY),
            Param(name="starred", location=Location.QUERY),
            Param(name="imported", location=Location.QUERY),
            Param(name="membership", location=Location.QUERY),
            Param(name="with_issues_enabled", location=Location.QUERY),
            Param(name="with_merge_requests_enabled", location=Location.QUERY),
            Param(name="with_programming_language", location=Location.QUERY),
            Param(name="min_access_level", location=Location.QUERY),
            Param(name="id_after", location=Location.QUERY),
            Param(name="id_before", location=Location.QUERY),
            Param(name="last_activity_after", location=Location.QUERY),
            Param(name="last_activity_before", location=Location.QUERY),
            Param(name="repository_storage", location=Location.QUERY),
            Param(name="topic", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="topic_id", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="include_pending_delete", location=Location.QUERY),
            Param(name="marked_for_deletion_on", location=Location.QUERY),
            Param(name="active", location=Location.QUERY),
            Param(name="wiki_checksum_failed", location=Location.QUERY),
            Param(name="repository_checksum_failed", location=Location.QUERY),
            Param(name="include_hidden", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="simple", location=Location.QUERY),
            Param(name="statistics", location=Location.QUERY),
            Param(name="with_custom_attributes", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Projects API: List all projects".
    RestOperation(
        operation_id="tenant-scale#list-all-projects",
        method="GET",
        path="/projects",
        params=(
            Param(name="archived", location=Location.QUERY),
            Param(name="custom_attributes", location=Location.QUERY, kind=Kind.HASH),
            Param(name="id_after", location=Location.QUERY),
            Param(name="id_before", location=Location.QUERY),
            Param(name="imported", location=Location.QUERY),
            Param(name="include_hidden", location=Location.QUERY),
            Param(name="include_pending_delete", location=Location.QUERY),
            Param(name="last_activity_after", location=Location.QUERY),
            Param(name="last_activity_before", location=Location.QUERY),
            Param(name="membership", location=Location.QUERY),
            Param(name="min_access_level", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="owned", location=Location.QUERY),
            Param(name="repository_checksum_failed", location=Location.QUERY),
            Param(name="repository_storage", location=Location.QUERY),
            Param(name="search_namespaces", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="simple", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="starred", location=Location.QUERY),
            Param(name="statistics", location=Location.QUERY),
            Param(name="topic_id", location=Location.QUERY),
            Param(name="topic", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="visibility", location=Location.QUERY),
            Param(name="wiki_checksum_failed", location=Location.QUERY),
            Param(name="with_custom_attributes", location=Location.QUERY),
            Param(name="with_issues_enabled", location=Location.QUERY),
            Param(name="with_merge_requests_enabled", location=Location.QUERY),
            Param(name="with_programming_language", location=Location.QUERY),
            Param(name="marked_for_deletion_on", location=Location.QUERY),
            Param(name="active", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Projects API: Delete a shared project link in a group".
    RestOperation(
        operation_id="tenant-scale#delete-a-shared-project-link-in-a-group",
        method="DELETE",
        path="/projects/:id/share/:group_id",
    ),
    # "Topics API: List all projects assigned to a topic".
    RestOperation(
        operation_id="tenant-scale#list-all-projects-assigned-to-a-topic",
        method="GET",
        path="/projects",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="archived", location=Location.QUERY),
            Param(name="visibility", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="search_namespaces", location=Location.QUERY),
            Param(name="owned", location=Location.QUERY),
            Param(name="starred", location=Location.QUERY),
            Param(name="imported", location=Location.QUERY),
            Param(name="membership", location=Location.QUERY),
            Param(name="with_issues_enabled", location=Location.QUERY),
            Param(name="with_merge_requests_enabled", location=Location.QUERY),
            Param(name="with_programming_language", location=Location.QUERY),
            Param(name="min_access_level", location=Location.QUERY),
            Param(name="id_after", location=Location.QUERY),
            Param(name="id_before", location=Location.QUERY),
            Param(name="last_activity_after", location=Location.QUERY),
            Param(name="last_activity_before", location=Location.QUERY),
            Param(name="repository_storage", location=Location.QUERY),
            Param(name="topic", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="topic_id", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="include_pending_delete", location=Location.QUERY),
            Param(name="marked_for_deletion_on", location=Location.QUERY),
            Param(name="active", location=Location.QUERY),
            Param(name="wiki_checksum_failed", location=Location.QUERY),
            Param(name="repository_checksum_failed", location=Location.QUERY),
            Param(name="include_hidden", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="simple", location=Location.QUERY),
            Param(name="statistics", location=Location.QUERY),
            Param(name="with_custom_attributes", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
