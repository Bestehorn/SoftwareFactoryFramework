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
  ``Param`` of its own, so ``upload`` of "Export a project" is not required although ``upload[url]`` is; a bracketed
  row with no parent row, as each ``override_params[...]`` row of "Import a project from an AWS S3 bucket", one level
  deep or two (``override_params[container_expiration_policy_attributes][cadence]``), is a body ``Param`` under its
  full name, so that record's body is ``BodyFormat.FORM`` (issue #63, design.md D6);
- a ``GET`` section headed "List" is ``Paging.OFFSET`` and every other record ``Paging.NONE``; every other body is
  ``BodyFormat.JSON`` (a ``FILE`` value sends either as multipart), and no record has ``fixed`` values.

The data management, Geo and system hooks pages are offered on GitLab Self-Managed only; their records are proven by the
two halves of ``test/test_gitlab_wrapper_contract.py`` against the fake host (issue #41, design.md D5).

Four imports write into an existing project: "Import project resources" imports issues, milestones, merge requests or
pipelines into it, and the imports from a local archive, from a remote archive and from an AWS S3 bucket take
``overwrite``, which replaces it. "Import a project from an AWS S3 bucket" (``OP_IMPORT_FROM_S3``) has its record since
issue #63 (design.md D6), the other three (``OP_IMPORT_PROJECT_RESOURCES``,
``OP_IMPORT_A_PROJECT_FROM_A_LOCAL_ARCHIVE``, ``OP_IMPORT_A_PROJECT_FROM_A_REMOTE_ARCHIVE``) since issue #15: no
subcommand sends any of them, so ``commands/call.py``'s ``GATED_OPERATIONS`` maps each to ``None``, and ``call``
refuses it, ": no subcommand sends it", before any request is sent (issue #15 AC-3). The two archive imports have an
``override_params`` row, so each of their ``override_params[...]`` rows is its member and no ``Param``; a ``file.path``
row of "Import project resources" or of the local archive import is a ``Param`` of its own, as a ``.`` marks no
member. ``PENDING`` is empty: every index row of the family has its record.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import BodyFormat, Kind, Location, Paging, Param, RestOperation

FAMILY = "gitlab-dedicated"

# "Import a project from an AWS S3 bucket": `commands/call.py`'s `GATED_OPERATIONS` maps it to `None` (design.md D6).
OP_IMPORT_FROM_S3 = "gitlab-dedicated#import-a-project-from-an-aws-s3-bucket"
# The other imports that write into an existing project: `GATED_OPERATIONS` maps each to `None` (issue #15 AC-3).
OP_IMPORT_A_PROJECT_FROM_A_LOCAL_ARCHIVE = "gitlab-dedicated#import-a-project-from-a-local-archive"
OP_IMPORT_A_PROJECT_FROM_A_REMOTE_ARCHIVE = "gitlab-dedicated#import-a-project-from-a-remote-archive"
OP_IMPORT_PROJECT_RESOURCES = "gitlab-dedicated#import-project-resources"

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
    # "Project import and export API: Import a project from a local archive"; each `override_params[...]` row is a
    # member of `override_params`, and each `file.` row a Param of its own.
    RestOperation(
        operation_id=OP_IMPORT_A_PROJECT_FROM_A_LOCAL_ARCHIVE,
        method="POST",
        path="/projects/import",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="path", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY),
            Param(name="namespace", location=Location.BODY),
            Param(name="namespace_id", location=Location.BODY),
            Param(name="namespace_path", location=Location.BODY),
            Param(name="override_params", location=Location.BODY, kind=Kind.HASH),
            Param(name="overwrite", location=Location.BODY),
            Param(name="file.path", location=Location.BODY),
            Param(name="file.name", location=Location.BODY),
            Param(name="file.type", location=Location.BODY),
            Param(name="file.size", location=Location.BODY),
            Param(name="file.md5", location=Location.BODY),
            Param(name="file.sha1", location=Location.BODY),
            Param(name="file.sha256", location=Location.BODY),
            Param(name="file.etag", location=Location.BODY),
            Param(name="file.remote_id", location=Location.BODY),
            Param(name="file.remote_url", location=Location.BODY),
        ),
    ),
    # "Project import and export API: Import a project from a remote archive"; each `override_params[...]` row is a
    # member of `override_params`.
    RestOperation(
        operation_id=OP_IMPORT_A_PROJECT_FROM_A_REMOTE_ARCHIVE,
        method="POST",
        path="/projects/remote-import",
        params=(
            Param(name="path", location=Location.BODY, required=True),
            Param(name="url", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY),
            Param(name="namespace", location=Location.BODY),
            Param(name="namespace_id", location=Location.BODY),
            Param(name="namespace_path", location=Location.BODY),
            Param(name="overwrite", location=Location.BODY),
            Param(name="override_params", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Project import and export API: Import a project from an AWS S3 bucket"; no row has a parent row, so each
    # `override_params[...]` row is a body Param under its full name, and the body is a form (design.md D6).
    RestOperation(
        operation_id=OP_IMPORT_FROM_S3,
        method="POST",
        path="/projects/remote-import-s3",
        params=(
            Param(name="access_key_id", location=Location.BODY, required=True),
            Param(name="bucket_name", location=Location.BODY, required=True),
            Param(name="file_key", location=Location.BODY, required=True),
            Param(name="path", location=Location.BODY, required=True),
            Param(name="region", location=Location.BODY, required=True),
            Param(name="secret_access_key", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY),
            Param(name="namespace", location=Location.BODY),
            Param(name="namespace_id", location=Location.BODY),
            Param(name="namespace_path", location=Location.BODY),
            Param(name="overwrite", location=Location.BODY),
            Param(name="override_params[description]", location=Location.BODY),
            Param(name="override_params[build_git_strategy]", location=Location.BODY),
            Param(name="override_params[build_timeout]", location=Location.BODY),
            Param(name="override_params[auto_cancel_pending_pipelines]", location=Location.BODY),
            Param(name="override_params[ci_config_path]", location=Location.BODY),
            Param(name="override_params[service_desk_enabled]", location=Location.BODY),
            Param(name="override_params[issues_enabled]", location=Location.BODY),
            Param(name="override_params[merge_requests_enabled]", location=Location.BODY),
            Param(name="override_params[wiki_enabled]", location=Location.BODY),
            Param(name="override_params[jobs_enabled]", location=Location.BODY),
            Param(name="override_params[snippets_enabled]", location=Location.BODY),
            Param(name="override_params[issues_access_level]", location=Location.BODY),
            Param(name="override_params[repository_access_level]", location=Location.BODY),
            Param(name="override_params[merge_requests_access_level]", location=Location.BODY),
            Param(name="override_params[forking_access_level]", location=Location.BODY),
            Param(name="override_params[wiki_access_level]", location=Location.BODY),
            Param(name="override_params[builds_access_level]", location=Location.BODY),
            Param(name="override_params[snippets_access_level]", location=Location.BODY),
            Param(name="override_params[package_registry_access_level]", location=Location.BODY),
            Param(name="override_params[pages_access_level]", location=Location.BODY),
            Param(name="override_params[analytics_access_level]", location=Location.BODY),
            Param(name="override_params[container_registry_access_level]", location=Location.BODY),
            Param(name="override_params[security_and_compliance_access_level]", location=Location.BODY),
            Param(name="override_params[releases_access_level]", location=Location.BODY),
            Param(name="override_params[environments_access_level]", location=Location.BODY),
            Param(name="override_params[feature_flags_access_level]", location=Location.BODY),
            Param(name="override_params[infrastructure_access_level]", location=Location.BODY),
            Param(name="override_params[monitor_access_level]", location=Location.BODY),
            Param(name="override_params[model_experiments_access_level]", location=Location.BODY),
            Param(name="override_params[model_registry_access_level]", location=Location.BODY),
            Param(name="override_params[emails_disabled]", location=Location.BODY),
            Param(name="override_params[emails_enabled]", location=Location.BODY),
            Param(name="override_params[show_default_award_emojis]", location=Location.BODY),
            Param(name="override_params[show_diff_preview_in_email]", location=Location.BODY),
            Param(name="override_params[warn_about_potentially_unwanted_characters]", location=Location.BODY),
            Param(name="override_params[enforce_auth_checks_on_uploads]", location=Location.BODY),
            Param(name="override_params[shared_runners_enabled]", location=Location.BODY),
            Param(name="override_params[group_runners_enabled]", location=Location.BODY),
            Param(name="override_params[resource_group_default_process_mode]", location=Location.BODY),
            Param(name="override_params[resolve_outdated_diff_discussions]", location=Location.BODY),
            Param(name="override_params[remove_source_branch_after_merge]", location=Location.BODY),
            Param(name="override_params[packages_enabled]", location=Location.BODY),
            Param(name="override_params[container_registry_enabled]", location=Location.BODY),
            Param(name="override_params[container_expiration_policy_attributes][cadence]", location=Location.BODY),
            Param(name="override_params[container_expiration_policy_attributes][keep_n]", location=Location.BODY),
            Param(name="override_params[container_expiration_policy_attributes][older_than]", location=Location.BODY),
            Param(name="override_params[container_expiration_policy_attributes][name_regex]", location=Location.BODY),
            Param(
                name="override_params[container_expiration_policy_attributes][name_regex_keep]", location=Location.BODY
            ),
            Param(name="override_params[container_expiration_policy_attributes][enabled]", location=Location.BODY),
            Param(name="override_params[lfs_enabled]", location=Location.BODY),
            Param(name="override_params[visibility]", location=Location.BODY),
            Param(name="override_params[public_builds]", location=Location.BODY),
            Param(name="override_params[public_jobs]", location=Location.BODY),
            Param(name="override_params[request_access_enabled]", location=Location.BODY),
            Param(name="override_params[only_allow_merge_if_pipeline_succeeds]", location=Location.BODY),
            Param(name="override_params[allow_merge_on_skipped_pipeline]", location=Location.BODY),
            Param(name="override_params[only_allow_merge_if_all_discussions_are_resolved]", location=Location.BODY),
            Param(name="override_params[tag_list]", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="override_params[topics]", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="override_params[avatar]", location=Location.BODY, kind=Kind.FILE),
            Param(name="override_params[printing_merge_request_link_enabled]", location=Location.BODY),
            Param(name="override_params[merge_method]", location=Location.BODY),
            Param(name="override_params[suggestion_commit_message]", location=Location.BODY),
            Param(name="override_params[merge_commit_template]", location=Location.BODY),
            Param(name="override_params[squash_commit_template]", location=Location.BODY),
            Param(name="override_params[issue_branch_template]", location=Location.BODY),
            Param(name="override_params[auto_devops_enabled]", location=Location.BODY),
            Param(name="override_params[auto_devops_deploy_strategy]", location=Location.BODY),
            Param(name="override_params[autoclose_referenced_issues]", location=Location.BODY),
            Param(name="override_params[repository_storage]", location=Location.BODY),
            Param(name="override_params[squash_option]", location=Location.BODY),
            Param(name="override_params[mr_default_target_self]", location=Location.BODY),
            Param(name="override_params[mr_default_title_template]", location=Location.BODY),
            Param(name="override_params[cicd_catalog_enabled]", location=Location.BODY),
            Param(name="override_params[only_allow_merge_if_all_status_checks_passed]", location=Location.BODY),
            Param(name="override_params[approvals_before_merge]", location=Location.BODY),
            Param(name="override_params[mirror]", location=Location.BODY),
            Param(name="override_params[mirror_trigger_builds]", location=Location.BODY),
            Param(name="override_params[external_authorization_classification_label]", location=Location.BODY),
            Param(name="override_params[requirements_access_level]", location=Location.BODY),
            Param(name="override_params[prevent_merge_without_jira_issue]", location=Location.BODY),
            Param(name="override_params[auto_duo_code_review_enabled]", location=Location.BODY),
            Param(name="override_params[duo_remote_flows_enabled]", location=Location.BODY),
            Param(name="override_params[duo_sast_fp_detection_enabled]", location=Location.BODY),
            Param(name="override_params[duo_secret_detection_fp_enabled]", location=Location.BODY),
            Param(name="override_params[duo_dependency_bump_breaking_changes_enabled]", location=Location.BODY),
            Param(name="override_params[duo_sast_vr_workflow_enabled]", location=Location.BODY),
            Param(name="override_params[spp_repository_pipeline_access]", location=Location.BODY),
            Param(name="override_params[merge_request_title_regex]", location=Location.BODY),
            Param(name="override_params[merge_request_title_regex_description]", location=Location.BODY),
        ),
        body=BodyFormat.FORM,
    ),
    # "Project import and export API: Retrieve the status of a project import".
    RestOperation(
        operation_id="gitlab-dedicated#retrieve-the-status-of-a-project-import",
        method="GET",
        path="/projects/:id/import",
    ),
    # "Project import and export API: Import project resources"; each `file.` row is a Param of its own.
    RestOperation(
        operation_id=OP_IMPORT_PROJECT_RESOURCES,
        method="POST",
        path="/projects/import-relation",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="path", location=Location.BODY, required=True),
            Param(name="relation", location=Location.BODY, required=True),
            Param(name="file.path", location=Location.BODY),
            Param(name="file.name", location=Location.BODY),
            Param(name="file.type", location=Location.BODY),
            Param(name="file.size", location=Location.BODY),
            Param(name="file.md5", location=Location.BODY),
            Param(name="file.sha1", location=Location.BODY),
            Param(name="file.sha256", location=Location.BODY),
            Param(name="file.etag", location=Location.BODY),
            Param(name="file.remote_id", location=Location.BODY),
            Param(name="file.remote_url", location=Location.BODY),
        ),
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

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
