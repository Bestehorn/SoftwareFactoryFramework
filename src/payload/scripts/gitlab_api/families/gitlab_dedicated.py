"""The ``gitlab-dedicated`` endpoint family of the GitLab wrapper: data management, Geo nodes and sites, migration by
direct transfer, group and project import and export, the GitHub and Bitbucket importers, and group, project and system
webhooks.

Each record is transcribed, in page order, from the attribute table of its section of
``docs/api-reference/gitlab/rest/gitlab-dedicated.md`` (issue #38; issue #41, design.md D5 and D8): the method, the path
as ``operations-index.md`` writes it, and one ``Param`` per query or body row, a ``form`` row being a body ``Param``.
Every section of the page has one endpoint, the one its record declares.

- a row whose Notes begin "file upload" is ``Kind.FILE``, whatever its Type; ``array of object`` is ``ARRAY_OF_HASHES``,
  and so is ``entities`` of "Start a group or project migration", whose ``entities[...]`` rows are the members of each
  item; ``hash``, ``Hash`` and ``object`` are ``HASH``; any other Type holding ``array`` or ``Array`` is ``ARRAY``;
  every other is ``SCALAR``; ``required`` is the Required column's ``yes``;
- a member row (``configuration[url]``, ``entities[source_type]``, ``upload[url]``) is carried by its parent and is no
  ``Param`` of its own, so ``upload`` of "Export a project" is not required although ``upload[url]`` is;
- a ``GET`` section headed "List" is ``Paging.OFFSET`` and every other record ``Paging.NONE``; every body is
  ``BodyFormat.JSON`` (a ``FILE`` value sends it as multipart), and no record has ``fixed`` values.

The data management, Geo and system hooks pages are offered on GitLab Self-Managed only; their records are proven by the
two halves of ``test/test_gitlab_wrapper_contract.py`` against the fake host (issue #41, design.md D5).

``PENDING`` holds the keys of the four imports that have no record (issue #38, DL-005). "Import project resources" and
the imports from a local and from a remote archive write into an existing project: the first imports issues, milestones,
merge requests or pipelines into it, and the other two take ``overwrite``, which replaces it; no subcommand sends any of
them, and ``call`` refuses only an ID a gated subcommand sends. "Import a project from an AWS S3 bucket" has two-level
``override_params[...][...]`` rows, which no ``Param`` can name. No other family links any of these keys.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "gitlab-dedicated"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Data management API: Retrieve model information".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-model-information",
        method="GET",
        path="/admin/data_management/:model_name",
        params=(
            Param(name="checksum_state", location=Location.QUERY),
            Param(name="identifiers", location=Location.QUERY, kind=Kind.ARRAY),
        ),
    ),
    # "Data management API: Recalculate checksums for model records".
    RestOperation(
        operation_id="gitlab-dedicated#recalculate-checksums-for-model-records",
        method="PUT",
        path="/admin/data_management/:model_name/checksum",
        params=(
            Param(name="checksum_state", location=Location.BODY),
            Param(name="identifiers", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Data management API: Retrieve information about a model record".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-information-about-a-model-record",
        method="GET",
        path="/admin/data_management/:model_name/:id",
        params=(Param(name="record_identifier", location=Location.QUERY, required=True),),
    ),
    # "Data management API: Recalculate the checksum of a model record".
    RestOperation(
        operation_id="gitlab-dedicated#recalculate-the-checksum-of-a-model-record",
        method="PUT",
        path="/admin/data_management/:model_name/:record_identifier/checksum",
    ),
    # "Geo Nodes API (deprecated): Create a Geo node".
    RestOperation(
        operation_id="gitlab-dedicated#create-a-geo-node",
        method="POST",
        path="/geo_nodes",
        params=(
            Param(name="primary", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="url", location=Location.BODY, required=True),
            Param(name="internal_url", location=Location.BODY),
            Param(name="files_max_capacity", location=Location.BODY),
            Param(name="repos_max_capacity", location=Location.BODY),
            Param(name="verification_max_capacity", location=Location.BODY),
            Param(name="container_repositories_max_capacity", location=Location.BODY),
            Param(name="sync_object_storage", location=Location.BODY),
            Param(name="selective_sync_type", location=Location.BODY),
            Param(name="selective_sync_shards", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="selective_sync_namespace_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="minimum_reverification_interval", location=Location.BODY),
            Param(name="blob_download_timeout", location=Location.BODY),
        ),
    ),
    # "Geo Nodes API (deprecated): List all Geo nodes".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-geo-nodes",
        method="GET",
        path="/geo_nodes",
        paging=Paging.OFFSET,
    ),
    # "Geo Nodes API (deprecated): Update a Geo node".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-geo-node",
        method="PUT",
        path="/geo_nodes/:id",
        params=(
            Param(name="enabled", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="internal_url", location=Location.BODY),
            Param(name="files_max_capacity", location=Location.BODY),
            Param(name="repos_max_capacity", location=Location.BODY),
            Param(name="verification_max_capacity", location=Location.BODY),
            Param(name="container_repositories_max_capacity", location=Location.BODY),
            Param(name="sync_object_storage", location=Location.BODY),
            Param(name="selective_sync_type", location=Location.BODY),
            Param(name="selective_sync_shards", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="selective_sync_namespace_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="minimum_reverification_interval", location=Location.BODY),
            Param(name="blob_download_timeout", location=Location.BODY),
        ),
    ),
    # "Geo Nodes API (deprecated): Delete a Geo node".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-geo-node",
        method="DELETE",
        path="/geo_nodes/:id",
    ),
    # "Geo Nodes API (deprecated): Repair a Geo node".
    RestOperation(
        operation_id="gitlab-dedicated#repair-a-geo-node",
        method="POST",
        path="/geo_nodes/:id/repair",
    ),
    # "Geo Nodes API (deprecated): List all Geo node statuses".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-geo-node-statuses",
        method="GET",
        path="/geo_nodes/status",
        paging=Paging.OFFSET,
    ),
    # "Geo sites API: Create a Geo site".
    RestOperation(
        operation_id="gitlab-dedicated#create-a-geo-site",
        method="POST",
        path="/geo_sites",
        params=(
            Param(name="primary", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="url", location=Location.BODY, required=True),
            Param(name="internal_url", location=Location.BODY),
            Param(name="files_max_capacity", location=Location.BODY),
            Param(name="repos_max_capacity", location=Location.BODY),
            Param(name="verification_max_capacity", location=Location.BODY),
            Param(name="container_repositories_max_capacity", location=Location.BODY),
            Param(name="sync_object_storage", location=Location.BODY),
            Param(name="selective_sync_type", location=Location.BODY),
            Param(name="selective_sync_shards", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="selective_sync_namespace_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="minimum_reverification_interval", location=Location.BODY),
            Param(name="blob_download_timeout", location=Location.BODY),
        ),
    ),
    # "Geo sites API: List all Geo sites".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-geo-sites",
        method="GET",
        path="/geo_sites",
        paging=Paging.OFFSET,
    ),
    # "Geo sites API: Retrieve a Geo site".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-geo-site",
        method="GET",
        path="/geo_sites/:id",
    ),
    # "Geo sites API: Update a Geo site".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-geo-site",
        method="PUT",
        path="/geo_sites/:id",
        params=(
            Param(name="enabled", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="internal_url", location=Location.BODY),
            Param(name="files_max_capacity", location=Location.BODY),
            Param(name="repos_max_capacity", location=Location.BODY),
            Param(name="verification_max_capacity", location=Location.BODY),
            Param(name="container_repositories_max_capacity", location=Location.BODY),
            Param(name="selective_sync_type", location=Location.BODY),
            Param(name="selective_sync_shards", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="selective_sync_namespace_ids", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="minimum_reverification_interval", location=Location.BODY),
            Param(name="blob_download_timeout", location=Location.BODY),
        ),
    ),
    # "Geo sites API: Delete a Geo site".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-geo-site",
        method="DELETE",
        path="/geo_sites/:id",
    ),
    # "Geo sites API: Repair a Geo site".
    RestOperation(
        operation_id="gitlab-dedicated#repair-a-geo-site",
        method="POST",
        path="/geo_sites/:id/repair",
    ),
    # "Geo sites API: List all Geo site statuses".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-geo-site-statuses",
        method="GET",
        path="/geo_sites/status",
        paging=Paging.OFFSET,
    ),
    # "Geo sites API: Retrieve a Geo site status".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-geo-site-status",
        method="GET",
        path="/geo_sites/:id/status",
    ),
    # "Group and project migration by direct transfer API: Start a group or project migration".
    RestOperation(
        operation_id="gitlab-dedicated#start-a-group-or-project-migration",
        method="POST",
        path="/bulk_imports",
        params=(
            Param(name="configuration", location=Location.BODY, kind=Kind.HASH, required=True),
            Param(name="entities", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),
        ),
    ),
    # "Group and project migration by direct transfer API: List all group or project migrations".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-group-or-project-migrations",
        method="GET",
        path="/bulk_imports",
        params=(
            Param(name="per_page", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group and project migration by direct transfer API: List all group or project migration entities".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-group-or-project-migration-entities",
        method="GET",
        path="/bulk_imports/entities",
        params=(
            Param(name="per_page", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group and project migration by direct transfer API: Retrieve a group or project migration".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-group-or-project-migration",
        method="GET",
        path="/bulk_imports/:id",
    ),
    # "Group and project migration by direct transfer API: List group or project migration entities".
    RestOperation(
        operation_id="gitlab-dedicated#list-group-or-project-migration-entities",
        method="GET",
        path="/bulk_imports/:id/entities",
        params=(
            Param(name="per_page", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group and project migration by direct transfer API: Retrieve a group or project migration entity".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-group-or-project-migration-entity",
        method="GET",
        path="/bulk_imports/:id/entities/:entity_id",
    ),
    # "Group and project migration by direct transfer API: List failed import records for a migration entity".
    RestOperation(
        operation_id="gitlab-dedicated#list-failed-import-records-for-a-migration-entity",
        method="GET",
        path="/bulk_imports/:id/entities/:entity_id/failures",
        paging=Paging.OFFSET,
    ),
    # "Group and project migration by direct transfer API: Cancel a migration".
    RestOperation(
        operation_id="gitlab-dedicated#cancel-a-migration",
        method="POST",
        path="/bulk_imports/:id/cancel",
    ),
    # "Group import and export API: Create a group export".
    RestOperation(
        operation_id="gitlab-dedicated#create-a-group-export",
        method="POST",
        path="/groups/:id/export",
    ),
    # "Group import and export API: Retrieve a group export download".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-group-export-download",
        method="GET",
        path="/groups/:id/export/download",
    ),
    # "Group import and export API: Create a group import".
    RestOperation(
        operation_id="gitlab-dedicated#create-a-group-import",
        method="POST",
        path="/groups/import",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="path", location=Location.BODY, required=True),
            Param(name="parent_id", location=Location.BODY),
            Param(name="organization_id", location=Location.BODY),
        ),
    ),
    # "Group placeholder reassignments API: Retrieve pending reassignments".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-pending-reassignments",
        method="GET",
        path="/groups/:id/placeholder_reassignments",
    ),
    # "Group placeholder reassignments API: Reassign placeholders".
    RestOperation(
        operation_id="gitlab-dedicated#reassign-placeholders",
        method="POST",
        path="/groups/:id/placeholder_reassignments",
        params=(Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "Group relations export API: Schedule a new export for a group".
    RestOperation(
        operation_id="gitlab-dedicated#schedule-a-new-export-for-a-group",
        method="POST",
        path="/groups/:id/export_relations",
        params=(Param(name="batched", location=Location.BODY),),
    ),
    # "Group relations export API: Retrieve the status of an export".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-an-export",
        method="GET",
        path="/groups/:id/export_relations/status",
        params=(Param(name="relation", location=Location.QUERY),),
    ),
    # "Group relations export API: Download an export".
    RestOperation(
        operation_id="gitlab-dedicated#download-an-export",
        method="GET",
        path="/groups/:id/export_relations/download",
        params=(
            Param(name="relation", location=Location.QUERY, required=True),
            Param(name="batched", location=Location.QUERY),
            Param(name="batch_number", location=Location.QUERY),
        ),
    ),
    # "Group webhooks API: List all group hooks".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-group-hooks",
        method="GET",
        path="/groups/:id/hooks",
        paging=Paging.OFFSET,
    ),
    # "Group webhooks API: Retrieve a group hook".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-group-hook",
        method="GET",
        path="/groups/:id/hooks/:hook_id",
    ),
    # "Group webhooks API: List all group hook events".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-group-hook-events",
        method="GET",
        path="/groups/:id/hooks/:hook_id/events",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group webhooks API: Resend group hook event".
    RestOperation(
        operation_id="gitlab-dedicated#resend-group-hook-event",
        method="POST",
        path="/groups/:id/hooks/:hook_id/events/:hook_event_id/resend",
    ),
    # "Group webhooks API: Create a group hook".
    RestOperation(
        operation_id="gitlab-dedicated#create-a-group-hook",
        method="POST",
        path="/groups/:id/hooks",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="duo_flow_callback_enabled", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="feature_flag_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="member_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="milestone_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="project_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="releases_events", location=Location.BODY),
            Param(name="resource_access_token_events", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="subgroup_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
        ),
    ),
    # "Group webhooks API: Update a group hook".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-group-hook",
        method="PUT",
        path="/groups/:id/hooks/:hook_id",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="duo_flow_callback_enabled", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="feature_flag_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="member_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="milestone_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="project_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="releases_events", location=Location.BODY),
            Param(name="resource_access_token_events", location=Location.BODY),
            Param(name="service_access_tokens_expiration_enforced", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="subgroup_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
        ),
    ),
    # "Group webhooks API: Delete a group hook".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-group-hook",
        method="DELETE",
        path="/groups/:id/hooks/:hook_id",
    ),
    # "Group webhooks API: Trigger a test group hook".
    RestOperation(
        operation_id="gitlab-dedicated#trigger-a-test-group-hook",
        method="POST",
        path="/groups/:id/hooks/:hook_id/test/:trigger",
    ),
    # "Group webhooks API: Update a custom header".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-custom-header",
        method="PUT",
        path="/groups/:id/hooks/:hook_id/custom_headers/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "Group webhooks API: Delete a custom header".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-custom-header",
        method="DELETE",
        path="/groups/:id/hooks/:hook_id/custom_headers/:key",
    ),
    # "Group webhooks API: Update a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-url-variable",
        method="PUT",
        path="/groups/:id/hooks/:hook_id/url_variables/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "Group webhooks API: Delete a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-url-variable",
        method="DELETE",
        path="/groups/:id/hooks/:hook_id/url_variables/:key",
    ),
    # "Import API: Import repository from GitHub".
    RestOperation(
        operation_id="gitlab-dedicated#import-repository-from-github",
        method="POST",
        path="/import/github",
        params=(
            Param(name="personal_access_token", location=Location.BODY, required=True),
            Param(name="repo_id", location=Location.BODY, required=True),
            Param(name="target_namespace", location=Location.BODY, required=True),
            Param(name="github_hostname", location=Location.BODY),
            Param(name="new_name", location=Location.BODY),
            Param(name="optional_stages", location=Location.BODY, kind=Kind.HASH),
            Param(name="pagination_limit", location=Location.BODY),
            Param(name="timeout_strategy", location=Location.BODY),
        ),
    ),
    # "Import API: Cancel GitHub project import".
    RestOperation(
        operation_id="gitlab-dedicated#cancel-github-project-import",
        method="POST",
        path="/import/github/cancel",
        params=(Param(name="project_id", location=Location.BODY, required=True),),
    ),
    # "Import API: Import GitHub gists into GitLab snippets".
    RestOperation(
        operation_id="gitlab-dedicated#import-github-gists-into-gitlab-snippets",
        method="POST",
        path="/import/github/gists",
        params=(Param(name="personal_access_token", location=Location.BODY, required=True),),
    ),
    # "Import API: Import repository from Bitbucket Server".
    RestOperation(
        operation_id="gitlab-dedicated#import-repository-from-bitbucket-server",
        method="POST",
        path="/import/bitbucket_server",
        params=(
            Param(name="bitbucket_server_project", location=Location.BODY, required=True),
            Param(name="bitbucket_server_repo", location=Location.BODY, required=True),
            Param(name="bitbucket_server_url", location=Location.BODY, required=True),
            Param(name="bitbucket_server_username", location=Location.BODY, required=True),
            Param(name="personal_access_token", location=Location.BODY, required=True),
            Param(name="new_name", location=Location.BODY),
            Param(name="target_namespace", location=Location.BODY),
            Param(name="timeout_strategy", location=Location.BODY),
            Param(name="new_namespace", location=Location.BODY),
        ),
    ),
    # "Import API: Import repository from Bitbucket Cloud".
    RestOperation(
        operation_id="gitlab-dedicated#import-repository-from-bitbucket-cloud",
        method="POST",
        path="/import/bitbucket",
        params=(
            Param(name="bitbucket_api_token", location=Location.BODY, required=True),
            Param(name="bitbucket_email", location=Location.BODY, required=True),
            Param(name="repo_path", location=Location.BODY, required=True),
            Param(name="target_namespace", location=Location.BODY, required=True),
            Param(name="new_name", location=Location.BODY),
        ),
    ),
    # "Project import and export API: Export a project".
    RestOperation(
        operation_id="gitlab-dedicated#export-a-project",
        method="POST",
        path="/projects/:id/export",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="excluded_relations", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="upload", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Project import and export API: Retrieve the status of a project export".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-a-project-export",
        method="GET",
        path="/projects/:id/export",
    ),
    # "Project import and export API: Download a project export".
    RestOperation(
        operation_id="gitlab-dedicated#download-a-project-export",
        method="GET",
        path="/projects/:id/export/download",
    ),
    # "Project import and export API: Retrieve the status of a project import".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-a-project-import",
        method="GET",
        path="/projects/:id/import",
    ),
    # "Project import and export API: Retrieve the status of a project resource import".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-a-project-resource-import",
        method="GET",
        path="/projects/:id/relation-imports",
    ),
    # "Project relations export API: Schedule a new export for a project".
    RestOperation(
        operation_id="gitlab-dedicated#schedule-a-new-export-for-a-project",
        method="POST",
        path="/projects/:id/export_relations",
        params=(Param(name="batched", location=Location.BODY),),
    ),
    # "Project relations export API: Retrieve the status of an export".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-an-export-1",
        method="GET",
        path="/projects/:id/export_relations/status",
        params=(Param(name="relation", location=Location.QUERY),),
    ),
    # "Project relations export API: Download an export".
    RestOperation(
        operation_id="gitlab-dedicated#download-an-export-1",
        method="GET",
        path="/projects/:id/export_relations/download",
        params=(
            Param(name="relation", location=Location.QUERY, required=True),
            Param(name="batched", location=Location.QUERY),
            Param(name="batch_number", location=Location.QUERY),
        ),
    ),
    # "Project webhooks API: List webhooks for a project".
    RestOperation(
        operation_id="gitlab-dedicated#list-webhooks-for-a-project",
        method="GET",
        path="/projects/:id/hooks",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project webhooks API: Retrieve a project webhook".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-a-project-webhook",
        method="GET",
        path="/projects/:id/hooks/:hook_id",
    ),
    # "Project webhooks API: List project webhook events".
    RestOperation(
        operation_id="gitlab-dedicated#list-project-webhook-events",
        method="GET",
        path="/projects/:id/hooks/:hook_id/events",
        params=(
            Param(name="status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project webhooks API: Resend a project webhook event".
    RestOperation(
        operation_id="gitlab-dedicated#resend-a-project-webhook-event",
        method="POST",
        path="/projects/:id/hooks/:hook_id/events/:hook_event_id/resend",
    ),
    # "Project webhooks API: Add a webhook to a project".
    RestOperation(
        operation_id="gitlab-dedicated#add-a-webhook-to-a-project",
        method="POST",
        path="/projects/:id/hooks",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="duo_flow_callback_enabled", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="feature_flag_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="milestone_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="releases_events", location=Location.BODY),
            Param(name="resource_access_token_events", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="resource_deploy_token_events", location=Location.BODY),
            Param(name="emoji_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="url_variables", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Project webhooks API: Update a project webhook".
    RestOperation(
        operation_id="gitlab-dedicated#update-a-project-webhook",
        method="PUT",
        path="/projects/:id/hooks/:hook_id",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="duo_flow_callback_enabled", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="feature_flag_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="milestone_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="releases_events", location=Location.BODY),
            Param(name="resource_access_token_events", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="resource_deploy_token_events", location=Location.BODY),
            Param(name="emoji_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="url_variables", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Project webhooks API: Delete project webhook".
    RestOperation(
        operation_id="gitlab-dedicated#delete-project-webhook",
        method="DELETE",
        path="/projects/:id/hooks/:hook_id",
    ),
    # "Project webhooks API: Trigger a test project webhook".
    RestOperation(
        operation_id="gitlab-dedicated#trigger-a-test-project-webhook",
        method="POST",
        path="/projects/:id/hooks/:hook_id/test/:trigger",
    ),
    # "Project webhooks API: Set a custom header".
    RestOperation(
        operation_id="gitlab-dedicated#set-a-custom-header",
        method="PUT",
        path="/projects/:id/hooks/:hook_id/custom_headers/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "Project webhooks API: Delete a custom header".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-custom-header-1",
        method="DELETE",
        path="/projects/:id/hooks/:hook_id/custom_headers/:key",
    ),
    # "Project webhooks API: Set a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#set-a-url-variable",
        method="PUT",
        path="/projects/:id/hooks/:hook_id/url_variables/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "Project webhooks API: Delete a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-url-variable-1",
        method="DELETE",
        path="/projects/:id/hooks/:hook_id/url_variables/:key",
    ),
    # "System hooks API: List all system hooks".
    RestOperation(
        operation_id="gitlab-dedicated#list-all-system-hooks",
        method="GET",
        path="/hooks",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "System hooks API: Retrieve system hook".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-system-hook",
        method="GET",
        path="/hooks/:id",
    ),
    # "System hooks API: Add new system hook".
    RestOperation(
        operation_id="gitlab-dedicated#add-new-system-hook",
        method="POST",
        path="/hooks",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="repository_update_events", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="url_variables", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "System hooks API: Update system hook".
    RestOperation(
        operation_id="gitlab-dedicated#update-system-hook",
        method="PUT",
        path="/hooks/:hook_id",
        params=(
            Param(name="branch_filter_strategy", location=Location.BODY),
            Param(name="custom_webhook_template", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_events_branch_filter", location=Location.BODY),
            Param(name="repository_update_events", location=Location.BODY),
            Param(name="signing_token", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="token", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="url_variables", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
            Param(name="custom_headers", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "System hooks API: Test system hook".
    RestOperation(
        operation_id="gitlab-dedicated#test-system-hook",
        method="POST",
        path="/hooks/:id",
    ),
    # "System hooks API: Delete system hook".
    RestOperation(
        operation_id="gitlab-dedicated#delete-system-hook",
        method="DELETE",
        path="/hooks/:id",
    ),
    # "System hooks API: Set a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#set-a-url-variable-1",
        method="PUT",
        path="/hooks/:hook_id/url_variables/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "System hooks API: Delete a URL variable".
    RestOperation(
        operation_id="gitlab-dedicated#delete-a-url-variable-2",
        method="DELETE",
        path="/hooks/:hook_id/url_variables/:key",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/projects/import"),
        ("POST", "/projects/import-relation"),
        ("POST", "/projects/remote-import"),
        ("POST", "/projects/remote-import-s3"),
    }
)
