"""The ``analytics`` endpoint family of the GitLab wrapper: alert metric images, DORA metrics, Error Tracking,
group activity counts, the advanced search migrations, search and Service Ping.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/analytics.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section:
the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query, body or form row (a ``form`` row
is sent in the body), in table order:

- a row whose Notes begin "file upload" is ``Kind.FILE`` (the ``file`` of "Upload metric image", which makes that body
  multipart); otherwise an ``object`` row is ``HASH``, an ``array of strings`` row is ``ARRAY``, and every other row
  is ``SCALAR``; ``required`` is the Required column's ``yes``; every body is JSON and no record has ``fixed`` values;
- each ``not[...]`` row of the three searches has no ``not`` row, so it is a query ``Param`` of its own;
- a ``GET`` section headed "List" or with a ``page`` row (the three searches) is ``Paging.OFFSET``, every other record
  ``Paging.NONE``: "List all Service Ping SQL queries" and "List all non-SQL metrics" answer one object (AC-5).

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "analytics"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Alert management alerts API: Upload metric image"; `file` is a FILE (Notes "file upload"), so the body is
    # multipart.
    RestOperation(
        operation_id="analytics#upload-metric-image",
        method="POST",
        path="/projects/:id/alert_management_alerts/:alert_iid/metric_images",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="url", location=Location.BODY),
            Param(name="url_text", location=Location.BODY),
        ),
    ),
    # "Alert management alerts API: List all metric images".
    RestOperation(
        operation_id="analytics#list-all-metric-images",
        method="GET",
        path="/projects/:id/alert_management_alerts/:alert_iid/metric_images",
        paging=Paging.OFFSET,
    ),
    # "Alert management alerts API: Update a metric image".
    RestOperation(
        operation_id="analytics#update-a-metric-image",
        method="PUT",
        path="/projects/:id/alert_management_alerts/:alert_iid/metric_images/:image_id",
        params=(
            Param(name="url", location=Location.BODY),
            Param(name="url_text", location=Location.BODY),
        ),
    ),
    # "Alert management alerts API: Delete a metric image".
    RestOperation(
        operation_id="analytics#delete-a-metric-image",
        method="DELETE",
        path="/projects/:id/alert_management_alerts/:alert_iid/metric_images/:image_id",
    ),
    # "DevOps Research and Assessment (DORA) metrics API: Retrieve project-level DORA metrics".
    RestOperation(
        operation_id="analytics#retrieve-project-level-dora-metrics",
        method="GET",
        path="/projects/:id/dora/metrics",
        params=(
            Param(name="metric", location=Location.QUERY, required=True),
            Param(name="end_date", location=Location.QUERY),
            Param(name="environment_tiers", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="interval", location=Location.QUERY),
            Param(name="start_date", location=Location.QUERY),
        ),
    ),
    # "DevOps Research and Assessment (DORA) metrics API: Retrieve group-level DORA metrics".
    RestOperation(
        operation_id="analytics#retrieve-group-level-dora-metrics",
        method="GET",
        path="/groups/:id/dora/metrics",
        params=(
            Param(name="metric", location=Location.QUERY, required=True),
            Param(name="end_date", location=Location.QUERY),
            Param(name="environment_tiers", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="interval", location=Location.QUERY),
            Param(name="start_date", location=Location.QUERY),
        ),
    ),
    # "Error Tracking API: Retrieve Error Tracking settings".
    RestOperation(
        operation_id="analytics#retrieve-error-tracking-settings",
        method="GET",
        path="/projects/:id/error_tracking/settings",
    ),
    # "Error Tracking API: Create Error Tracking settings".
    RestOperation(
        operation_id="analytics#create-error-tracking-settings",
        method="PUT",
        path="/projects/:id/error_tracking/settings",
        params=(
            Param(name="active", location=Location.BODY, required=True),
            Param(name="integrated", location=Location.BODY, required=True),
        ),
    ),
    # "Error Tracking API: Update Error Tracking project settings".
    RestOperation(
        operation_id="analytics#update-error-tracking-project-settings",
        method="PATCH",
        path="/projects/:id/error_tracking/settings",
        params=(
            Param(name="active", location=Location.BODY, required=True),
            Param(name="integrated", location=Location.BODY),
        ),
    ),
    # "Error Tracking API: List all project client keys".
    RestOperation(
        operation_id="analytics#list-all-project-client-keys",
        method="GET",
        path="/projects/:id/error_tracking/client_keys",
        paging=Paging.OFFSET,
    ),
    # "Error Tracking API: Create a client key".
    RestOperation(
        operation_id="analytics#create-a-client-key",
        method="POST",
        path="/projects/:id/error_tracking/client_keys",
    ),
    # "Error Tracking API: Delete a client key".
    RestOperation(
        operation_id="analytics#delete-a-client-key",
        method="DELETE",
        path="/projects/:id/error_tracking/client_keys/:key_id",
    ),
    # "Group activity analytics API: Retrieve count of recently created issues for a group".
    RestOperation(
        operation_id="analytics#retrieve-count-of-recently-created-issues-for-a-group",
        method="GET",
        path="/analytics/group_activity/issues_count",
        params=(Param(name="group_path", location=Location.QUERY, required=True),),
    ),
    # "Group activity analytics API: Retrieve count of recently created merge requests for a group".
    RestOperation(
        operation_id="analytics#retrieve-count-of-recently-created-merge-requests-for-a-group",
        method="GET",
        path="/analytics/group_activity/merge_requests_count",
        params=(Param(name="group_path", location=Location.QUERY, required=True),),
    ),
    # "Group activity analytics API: Retrieve count of members recently added to a group".
    RestOperation(
        operation_id="analytics#retrieve-count-of-members-recently-added-to-a-group",
        method="GET",
        path="/analytics/group_activity/new_members_count",
        params=(Param(name="group_path", location=Location.QUERY, required=True),),
    ),
    # "Search admin API: List all advanced search migrations".
    RestOperation(
        operation_id="analytics#list-all-advanced-search-migrations",
        method="GET",
        path="/admin/search/migrations",
        paging=Paging.OFFSET,
    ),
    # "Search admin API: Retrieve an advanced search migration".
    RestOperation(
        operation_id="analytics#retrieve-an-advanced-search-migration",
        method="GET",
        path="/admin/search/migrations/:version_or_name",
    ),
    # "Search API: Search an instance"; each `not[...]` row has no `not` row, so it is a query Param of its own.
    RestOperation(
        operation_id="analytics#search-an-instance",
        method="GET",
        path="/search",
        params=(
            Param(name="scope", location=Location.QUERY, required=True),
            Param(name="search", location=Location.QUERY, required=True),
            Param(name="search_type", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="exclude_forks", location=Location.QUERY),
            Param(name="regex", location=Location.QUERY),
            Param(name="fields", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="include_archived", location=Location.QUERY),
            Param(name="num_context_lines", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="type", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="label_name", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[source_branch]", location=Location.QUERY),
            Param(name="not[target_branch]", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Search API: Search a group"; each `not[...]` row has no `not` row, so it is a query Param of its own.
    RestOperation(
        operation_id="analytics#search-a-group",
        method="GET",
        path="/groups/:id/search",
        params=(
            Param(name="scope", location=Location.QUERY, required=True),
            Param(name="search", location=Location.QUERY, required=True),
            Param(name="search_type", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="exclude_forks", location=Location.QUERY),
            Param(name="regex", location=Location.QUERY),
            Param(name="fields", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="include_archived", location=Location.QUERY),
            Param(name="num_context_lines", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="type", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="label_name", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[source_branch]", location=Location.QUERY),
            Param(name="not[target_branch]", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Search API: Search a project"; each `not[...]` row has no `not` row, so it is a query Param of its own.
    RestOperation(
        operation_id="analytics#search-a-project",
        method="GET",
        path="/projects/:id/search",
        params=(
            Param(name="scope", location=Location.QUERY, required=True),
            Param(name="search", location=Location.QUERY, required=True),
            Param(name="search_type", location=Location.QUERY),
            Param(name="confidential", location=Location.QUERY),
            Param(name="regex", location=Location.QUERY),
            Param(name="fields", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="num_context_lines", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="type", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="label_name", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[source_branch]", location=Location.QUERY),
            Param(name="not[target_branch]", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Search API: Semantic search".
    RestOperation(
        operation_id="analytics#semantic-search",
        method="GET",
        path="/projects/:id/search/semantic",
        params=(
            Param(name="q", location=Location.QUERY, required=True),
            Param(name="directory_path", location=Location.QUERY),
            Param(name="knn", location=Location.QUERY),
            Param(name="limit", location=Location.QUERY),
        ),
    ),
    # "Service Ping API: Export Service Ping data".
    RestOperation(
        operation_id="analytics#export-service-ping-data",
        method="GET",
        path="/usage_data/service_ping",
    ),
    # "Service Ping API: Export metric definitions".
    RestOperation(
        operation_id="analytics#export-metric-definitions",
        method="GET",
        path="/usage_data/metric_definitions",
        params=(Param(name="include_paths", location=Location.QUERY),),
    ),
    # "Service Ping API: List all Service Ping SQL queries"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="analytics#list-all-service-ping-sql-queries",
        method="GET",
        path="/usage_data/queries",
    ),
    # "Service Ping API: List all non-SQL metrics"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="analytics#list-all-non-sql-metrics",
        method="GET",
        path="/usage_data/non_sql_metrics",
    ),
    # "Service Ping API: Track internal events".
    RestOperation(
        operation_id="analytics#track-internal-events",
        method="POST",
        path="/usage_data/track_event",
        params=(
            Param(name="event", location=Location.BODY, required=True),
            Param(name="namespace_id", location=Location.BODY),
            Param(name="project_id", location=Location.BODY),
            Param(name="project_path", location=Location.BODY),
            Param(name="additional_properties", location=Location.BODY, kind=Kind.HASH),
            Param(name="send_to_snowplow", location=Location.BODY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
