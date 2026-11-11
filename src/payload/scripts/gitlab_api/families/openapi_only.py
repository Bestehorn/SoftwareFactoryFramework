"""The ``openapi-only`` endpoint family of the GitLab wrapper: the operations only GitLab's OpenAPI file names.

Each record is transcribed from its row of ``docs/api-reference/gitlab/operations-index.md`` and its section of
``rest/openapi-only.md`` (issue #40, design.md D4), in the page's order and under a comment naming the section's ``##``
and ``###`` headings. The operation ID is the row's Reference without ``rest/`` and ``.md``, a ``-1`` or ``-2`` suffix
included; the method and the path are the row's, verbatim, with its ``*name`` globs, its optional ``(...)`` groups, its
escaped parentheses (each backslash doubled in the literal) and its ``$`` as the row writes them (``registry.expand``,
design.md D1).

A record declares one ``Param`` per ``query``, ``body`` or ``form`` row of its section's table, in table order, named as
the row writes it (``$filter``, ``terraform-get``, ``ID``): a ``query`` row in the query, a ``body`` or ``form`` row in
the body. Its ``Kind`` is the row's Type: ``ARRAY`` for ``array of string``, ``HASH`` for ``object``,
``ARRAY_OF_HASHES`` for ``array of object``, ``FILE`` for ``file``, ``SCALAR`` for every other Type; it is ``required``
where Required reads ``yes``. A row that names a ``*name`` glob of the record's path, inside an optional group or not,
is that path parameter and is given with ``--path``, so it has no ``Param``; nor has a ``header`` row. Every record's
``body`` is ``BodyFormat.JSON``, which a ``FILE`` value makes multipart, and no record fixes a query value; the eight
``GET`` records whose section has the ``page`` and ``per_page`` query rows page by offset (``conventions.md``
"Offset-based") and declare both rows, every other is ``Paging.NONE``.

The uploads are the sections with a ``file`` row. ``openapi-only#upload-job-artifacts`` takes its ``file`` and
``metadata`` parts with ``--file`` and sends them, and every other body attribute, as a ``multipart/form-data`` body.
``openapi-only#upload-package-file``, ``openapi-only#upload-terraform-module-package-file`` and
``openapi-only#create-or-update-a-terraform-state`` take their body with ``--input``: Workhorse stores such a route's
request body unparsed (``requestBodyUploader``), so each record carries ``content_type=CONTENT_TYPE_OCTET_STREAM``, its
``file`` row is the body and has no ``Param``, and every other attribute is a ``Location.QUERY`` ``Param``, where it is
sent (design.md D5).

The page's three ``ml_models`` package-file keys (``download-an-ml_model-package-file``,
``workhorse-upload-model-package-file`` and ``workhorse-authorize-model-package-file``) are ``deploy``'s records
(``families/deploy.py``), so none is declared here. ``PENDING`` is empty: every other index row of this family has its
record. A secret attribute (a runner's ``token``, an integration's ``api_key``) is given as text like any other value;
the configured token travels only in its header.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation
from gitlab_api.transport import CONTENT_TYPE_OCTET_STREAM

FAMILY = "openapi-only"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "access_tokens: Rotate a group access token".
    RestOperation(
        operation_id="openapi-only#rotate-a-group-access-token",
        method="POST",
        path="/groups/:id/access_tokens/self/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "access_tokens: Retrieve a personal access token".
    RestOperation(
        operation_id="openapi-only#retrieve-a-personal-access-token",
        method="GET",
        path="/personal_access_tokens/self",
    ),
    # "access_tokens: Revoke a personal access token".
    RestOperation(
        operation_id="openapi-only#revoke-a-personal-access-token",
        method="DELETE",
        path="/personal_access_tokens/self",
    ),
    # "access_tokens: Rotate a personal access token".
    RestOperation(
        operation_id="openapi-only#rotate-a-personal-access-token",
        method="POST",
        path="/personal_access_tokens/self/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "access_tokens: Rotate a project access token".
    RestOperation(
        operation_id="openapi-only#rotate-a-project-access-token",
        method="POST",
        path="/projects/:id/access_tokens/self/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "alert_management: postApiV4ProjectsIdAlertManagementAlertsAlertIidMetricImagesAuthorize".
    RestOperation(
        operation_id="openapi-only#postapiv4projectsidalertmanagementalertsalertiidmetricimagesauthorize",
        method="POST",
        path="/projects/:id/alert_management_alerts/:alert_iid/metric_images/authorize",
    ),
    # "award_emoji: List all emoji reactions for an epic".
    RestOperation(
        operation_id="openapi-only#list-all-emoji-reactions-for-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid/award_emoji",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "award_emoji: Add an emoji reaction to an epic".
    RestOperation(
        operation_id="openapi-only#add-an-emoji-reaction-to-an-epic",
        method="POST",
        path="/groups/:id/epics/:epic_iid/award_emoji",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "award_emoji: Retrieve an emoji reaction from an epic".
    RestOperation(
        operation_id="openapi-only#retrieve-an-emoji-reaction-from-an-epic",
        method="GET",
        path="/groups/:id/epics/:epic_iid/award_emoji/:award_id",
    ),
    # "award_emoji: Delete an emoji reaction from an epic".
    RestOperation(
        operation_id="openapi-only#delete-an-emoji-reaction-from-an-epic",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid/award_emoji/:award_id",
    ),
    # "award_emoji: List all emoji reactions for an epic comment".
    RestOperation(
        operation_id="openapi-only#list-all-emoji-reactions-for-an-epic-comment",
        method="GET",
        path="/groups/:id/epics/:epic_iid/notes/:note_id/award_emoji",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "award_emoji: Add an emoji reaction to an epic comment".
    RestOperation(
        operation_id="openapi-only#add-an-emoji-reaction-to-an-epic-comment",
        method="POST",
        path="/groups/:id/epics/:epic_iid/notes/:note_id/award_emoji",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "award_emoji: Retrieve an emoji reaction from an epic comment".
    RestOperation(
        operation_id="openapi-only#retrieve-an-emoji-reaction-from-an-epic-comment",
        method="GET",
        path="/groups/:id/epics/:epic_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "award_emoji: Delete an emoji reaction from an epic comment".
    RestOperation(
        operation_id="openapi-only#delete-an-emoji-reaction-from-an-epic-comment",
        method="DELETE",
        path="/groups/:id/epics/:epic_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "award_emoji: List all emoji reactions for a merge request comment".
    RestOperation(
        operation_id="openapi-only#list-all-emoji-reactions-for-a-merge-request-comment",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id/award_emoji",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "award_emoji: Add an emoji reaction to a merge request comment".
    RestOperation(
        operation_id="openapi-only#add-an-emoji-reaction-to-a-merge-request-comment",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id/award_emoji",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "award_emoji: Retrieve an emoji reaction from a merge request comment".
    RestOperation(
        operation_id="openapi-only#retrieve-an-emoji-reaction-from-a-merge-request-comment",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "award_emoji: Delete an emoji reaction from a merge request comment".
    RestOperation(
        operation_id="openapi-only#delete-an-emoji-reaction-from-a-merge-request-comment",
        method="DELETE",
        path="/projects/:id/merge_requests/:merge_request_iid/notes/:note_id/award_emoji/:award_id",
    ),
    # "award_emoji: List all emoji reactions for a snippet comment".
    RestOperation(
        operation_id="openapi-only#list-all-emoji-reactions-for-a-snippet-comment",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "award_emoji: Add an emoji reaction to a snippet comment".
    RestOperation(
        operation_id="openapi-only#add-an-emoji-reaction-to-a-snippet-comment",
        method="POST",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "award_emoji: Retrieve an emoji reaction from a snippet comment".
    RestOperation(
        operation_id="openapi-only#retrieve-an-emoji-reaction-from-a-snippet-comment",
        method="GET",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji/:award_id",
    ),
    # "award_emoji: Delete an emoji reaction from a snippet comment".
    RestOperation(
        operation_id="openapi-only#delete-an-emoji-reaction-from-a-snippet-comment",
        method="DELETE",
        path="/projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji/:award_id",
    ),
    # "batched_background_operations: Get the list of batched background operations".
    RestOperation(
        operation_id="openapi-only#get-the-list-of-batched-background-operations",
        method="GET",
        path="/admin/batched_background_operations",
        params=(
            Param(name="database", location=Location.QUERY),
            Param(name="job_class_name", location=Location.QUERY),
        ),
    ),
    # "batched_background_operations: Retrieve a batched background operation".
    RestOperation(
        operation_id="openapi-only#retrieve-a-batched-background-operation",
        method="GET",
        path="/admin/batched_background_operations/:id",
        params=(Param(name="database", location=Location.QUERY),),
    ),
    # "batched_background_operations: Restart a batched background operation".
    RestOperation(
        operation_id="openapi-only#restart-a-batched-background-operation",
        method="PUT",
        path="/admin/batched_background_operations/:id/restart",
        params=(Param(name="database", location=Location.BODY),),
    ),
    # "batched_background_operations: Stop a batched background operation".
    RestOperation(
        operation_id="openapi-only#stop-a-batched-background-operation",
        method="PUT",
        path="/admin/batched_background_operations/:id/stop",
        params=(Param(name="database", location=Location.BODY),),
    ),
    # "branches: headApiV4ProjectsIdRepositoryBranchesBranch".
    RestOperation(
        operation_id="openapi-only#headapiv4projectsidrepositorybranchesbranch",
        method="HEAD",
        path="/projects/:id/repository/branches/:branch",
    ),
    # "branches: putApiV4ProjectsIdRepositoryBranchesBranchProtect".
    RestOperation(
        operation_id="openapi-only#putapiv4projectsidrepositorybranchesbranchprotect",
        method="PUT",
        path="/projects/:id/repository/branches/:branch/protect",
        params=(
            Param(name="developers_can_push", location=Location.BODY),
            Param(name="developers_can_merge", location=Location.BODY),
        ),
    ),
    # "branches: putApiV4ProjectsIdRepositoryBranchesBranchUnprotect".
    RestOperation(
        operation_id="openapi-only#putapiv4projectsidrepositorybranchesbranchunprotect",
        method="PUT",
        path="/projects/:id/repository/branches/:branch/unprotect",
    ),
    # "ci_catalog: Publish a new component project release as version to the CI/CD catalog".
    RestOperation(
        operation_id="openapi-only#publish-a-new-component-project-release-as-version-to-the-cicd-catalog",
        method="POST",
        path="/projects/:id/catalog/publish",
        params=(
            Param(name="version", location=Location.BODY, required=True),
            Param(name="metadata", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "ci_runners: Internal endpoint that deletes a runner manager by authentication token and system ID.".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-deletes-a-runner-manager-by-authentication-token-and-system-id",
        method="DELETE",
        path="/runners/managers",
        params=(
            Param(name="token", location=Location.QUERY, required=True),
            Param(name="system_id", location=Location.QUERY, required=True),
        ),
    ),
    # "container_registry: Receives notifications from the container registry when an operation occurs".
    RestOperation(
        operation_id="openapi-only#receives-notifications-from-the-container-registry-when-an-operation-occurs",
        method="POST",
        path="/container_registry_event/events",
    ),
    # "database_dictionary: getApiV4AdminDatabasesDatabaseNameDictionaryTablesTableName".
    RestOperation(
        operation_id="openapi-only#getapiv4admindatabasesdatabasenamedictionarytablestablename",
        method="GET",
        path="/admin/databases/:database_name/dictionary/tables/:table_name",
    ),
    # "database_dictionary: List dictionary tables".
    RestOperation(
        operation_id="openapi-only#list-dictionary-tables",
        method="GET",
        path="/databases/:database_name/dictionary/tables",
        params=(Param(name="table_size", location=Location.QUERY),),
    ),
    # "geo: Internal endpoint that reports persistent verification failures to the primary".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-reports-persistent-verification-failures-to-the-primary",
        method="POST",
        path="/geo/failures",
        params=(
            Param(name="geo_node_id", location=Location.BODY, required=True),
            Param(name="failures", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),
        ),
    ),
    # "geo: Query the GraphQL endpoint of an existing Geo node".
    RestOperation(
        operation_id="openapi-only#query-the-graphql-endpoint-of-an-existing-geo-node",
        method="POST",
        path="/geo/node_proxy/:id/graphql",
    ),
    # "geo: Determine if a Geo site should proxy requests".
    RestOperation(
        operation_id="openapi-only#determine-if-a-geo-site-should-proxy-requests",
        method="GET",
        path="/geo/proxy",
    ),
    # "geo: Internal endpoint that returns git-received-pack output for git push".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-returns-git-received-pack-output-for-git-push",
        method="POST",
        path="/geo/proxy_git_ssh/info_refs_receive_pack",
        params=(
            Param(name="secret_token", location=Location.BODY, required=True),
            Param(name="data", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "geo: Internal endpoint that returns info refs upload pack for clone or pull operations".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-returns-info-refs-upload-pack-for-clone-or-pull-operations",
        method="POST",
        path="/geo/proxy_git_ssh/info_refs_upload_pack",
        params=(
            Param(name="secret_token", location=Location.BODY, required=True),
            Param(name="data", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "geo: Internal endpoint that posts git-receive-pack for git push".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push",
        method="POST",
        path="/geo/proxy_git_ssh/receive_pack",
        params=(
            Param(name="secret_token", location=Location.BODY, required=True),
            Param(name="data", location=Location.BODY, kind=Kind.HASH, required=True),
            Param(name="output", location=Location.BODY, required=True),
        ),
    ),
    # "geo: Internal endpoint that posts git-upload-pack for clone or pull operations".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-posts-git-upload-pack-for-clone-or-pull-operations",
        method="POST",
        path="/geo/proxy_git_ssh/upload_pack",
        params=(
            Param(name="secret_token", location=Location.BODY, required=True),
            Param(name="data", location=Location.BODY, kind=Kind.HASH, required=True),
            Param(name="output", location=Location.BODY, required=True),
        ),
    ),
    # "geo: Used by secondary runners to verify the secondary instance has the very latest version".
    RestOperation(
        operation_id="openapi-only#used-by-secondary-runners-to-verify-the-secondary-instance-has-the-very-latest-version",
        method="GET",
        path="/geo/repositories/:gl_repository/pipeline_refs",
    ),
    # "geo: Internal endpoint that returns a replicable file".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-returns-a-replicable-file",
        method="GET",
        path="/geo/retrieve/:replicable_name/:replicable_id",
    ),
    # "geo: Internal endpoint that posts the current node status".
    RestOperation(
        operation_id="openapi-only#internal-endpoint-that-posts-the-current-node-status",
        method="POST",
        path="/geo/status",
        params=(Param(name="data", location=Location.BODY, kind=Kind.HASH),),
    ),
    # "group_import_and_export: Workhorse authorize the group import upload".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-group-import-upload",
        method="POST",
        path="/groups/import/authorize",
    ),
    # "groups: Workhorse authorization for the reassignment CSV file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorization-for-the-reassignment-csv-file",
        method="POST",
        path="/groups/:id/placeholder_reassignments/authorize",
    ),
    # "groups: postApiV4GroupsIdTransferToOrganization".
    RestOperation(
        operation_id="openapi-only#postapiv4groupsidtransfertoorganization",
        method="POST",
        path="/groups/:id/transfer_to_organization",
        params=(Param(name="organization_id", location=Location.BODY, required=True),),
    ),
    # "groups: Workhorse authorize the file upload".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-file-upload",
        method="POST",
        path="/groups/:id/uploads/authorize",
    ),
    # "hooks: Update a custom header".
    RestOperation(
        operation_id="openapi-only#update-a-custom-header",
        method="PUT",
        path="/hooks/:hook_id/custom_headers/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "hooks: Delete a custom header".
    RestOperation(
        operation_id="openapi-only#delete-a-custom-header",
        method="DELETE",
        path="/hooks/:hook_id/custom_headers/:key",
    ),
    # "integrations: Retrieve integration settings".
    RestOperation(
        operation_id="openapi-only#retrieve-integration-settings",
        method="GET",
        path="/groups/:id/integrations/:slug",
    ),
    # "integrations: Disable an integration".
    RestOperation(
        operation_id="openapi-only#disable-an-integration",
        method="DELETE",
        path="/groups/:id/integrations/:slug",
    ),
    # "integrations: Create or update the Apple App Store integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-apple-app-store-integration",
        method="PUT",
        path="/groups/:id/integrations/apple-app-store",
        params=(
            Param(name="app_store_issuer_id", location=Location.BODY, required=True),
            Param(name="app_store_key_id", location=Location.BODY, required=True),
            Param(name="app_store_private_key_file_name", location=Location.BODY, required=True),
            Param(name="app_store_private_key", location=Location.BODY, required=True),
            Param(name="app_store_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Google Play integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-google-play-integration",
        method="PUT",
        path="/groups/:id/integrations/google-play",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="service_account_key_file_name", location=Location.BODY, required=True),
            Param(name="service_account_key", location=Location.BODY, required=True),
            Param(name="google_play_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Jenkins integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-jenkins-integration",
        method="PUT",
        path="/groups/:id/integrations/jenkins",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="jenkins_url", location=Location.BODY, required=True),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Mock Monitoring integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mock-monitoring-integration",
        method="PUT",
        path="/groups/:id/integrations/mock-monitoring",
        params=(Param(name="use_inherited_settings", location=Location.BODY),),
    ),
    # "integrations: Create or update the Zentao integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-zentao-integration",
        method="PUT",
        path="/groups/:id/integrations/zentao",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="api_token", location=Location.BODY, required=True),
            Param(name="zentao_product_xid", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: postApiV4IntegrationsSlackEvents".
    RestOperation(
        operation_id="openapi-only#postapiv4integrationsslackevents",
        method="POST",
        path="/integrations/slack/events",
        params=(
            Param(name="token", location=Location.BODY),
            Param(name="team_id", location=Location.BODY),
            Param(name="api_app_id", location=Location.BODY),
            Param(name="event", location=Location.BODY, kind=Kind.HASH),
            Param(name="type", location=Location.BODY),
            Param(name="event_id", location=Location.BODY),
            Param(name="event_time", location=Location.BODY),
            Param(name="authed_users", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "integrations: Process Slack interaction events".
    RestOperation(
        operation_id="openapi-only#process-slack-interaction-events",
        method="POST",
        path="/integrations/slack/interactions",
    ),
    # "integrations: Get Slack interactive component options".
    RestOperation(
        operation_id="openapi-only#get-slack-interactive-component-options",
        method="POST",
        path="/integrations/slack/options",
    ),
    # "integrations: Retrieve integration settings".
    RestOperation(
        operation_id="openapi-only#retrieve-integration-settings-1",
        method="GET",
        path="/projects/:id/integrations/:slug",
    ),
    # "integrations: Disable an integration".
    RestOperation(
        operation_id="openapi-only#disable-an-integration-1",
        method="DELETE",
        path="/projects/:id/integrations/:slug",
    ),
    # "integrations: Create or update the Apple App Store integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-apple-app-store-integration-1",
        method="PUT",
        path="/projects/:id/integrations/apple-app-store",
        params=(
            Param(name="app_store_issuer_id", location=Location.BODY, required=True),
            Param(name="app_store_key_id", location=Location.BODY, required=True),
            Param(name="app_store_private_key_file_name", location=Location.BODY, required=True),
            Param(name="app_store_private_key", location=Location.BODY, required=True),
            Param(name="app_store_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Trigger a slash command for mattermost-slash-commands".
    RestOperation(
        operation_id="openapi-only#trigger-a-slash-command-for-mattermost-slash-commands",
        method="POST",
        path="/projects/:id/integrations/mattermost_slash_commands/trigger",
        params=(Param(name="token", location=Location.BODY, required=True),),
    ),
    # "integrations: Create or update the Mock Monitoring integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mock-monitoring-integration-1",
        method="PUT",
        path="/projects/:id/integrations/mock-monitoring",
        params=(Param(name="use_inherited_settings", location=Location.BODY),),
    ),
    # "integrations: Create or update the Zentao integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-zentao-integration-1",
        method="PUT",
        path="/projects/:id/integrations/zentao",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="api_token", location=Location.BODY, required=True),
            Param(name="zentao_product_xid", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: List all active integrations".
    RestOperation(
        operation_id="openapi-only#list-all-active-integrations",
        method="GET",
        path="/projects/:id/services",
    ),
    # "integrations: Retrieve integration settings".
    RestOperation(
        operation_id="openapi-only#retrieve-integration-settings-2",
        method="GET",
        path="/projects/:id/services/:slug",
    ),
    # "integrations: Disable an integration".
    RestOperation(
        operation_id="openapi-only#disable-an-integration-2",
        method="DELETE",
        path="/projects/:id/services/:slug",
    ),
    # "integrations: Create or update the Apple App Store integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-apple-app-store-integration-2",
        method="PUT",
        path="/projects/:id/services/apple-app-store",
        params=(
            Param(name="app_store_issuer_id", location=Location.BODY, required=True),
            Param(name="app_store_key_id", location=Location.BODY, required=True),
            Param(name="app_store_private_key_file_name", location=Location.BODY, required=True),
            Param(name="app_store_private_key", location=Location.BODY, required=True),
            Param(name="app_store_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Asana integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-asana-integration",
        method="PUT",
        path="/projects/:id/services/asana",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Assembla integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-assembla-integration",
        method="PUT",
        path="/projects/:id/services/assembla",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Bamboo integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-bamboo-integration",
        method="PUT",
        path="/projects/:id/services/bamboo",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="bamboo_url", location=Location.BODY, required=True),
            Param(name="build_key", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Bugzilla integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-bugzilla-integration",
        method="PUT",
        path="/projects/:id/services/bugzilla",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Buildkite integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-buildkite-integration",
        method="PUT",
        path="/projects/:id/services/buildkite",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Campfire integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-campfire-integration",
        method="PUT",
        path="/projects/:id/services/campfire",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="room", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Clickup integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-clickup-integration",
        method="PUT",
        path="/projects/:id/services/clickup",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Confluence integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-confluence-integration",
        method="PUT",
        path="/projects/:id/services/confluence",
        params=(
            Param(name="confluence_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Custom Issue Tracker integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-custom-issue-tracker-integration",
        method="PUT",
        path="/projects/:id/services/custom-issue-tracker",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Datadog integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-datadog-integration",
        method="PUT",
        path="/projects/:id/services/datadog",
        params=(
            Param(name="datadog_site", location=Location.BODY),
            Param(name="api_url", location=Location.BODY),
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="datadog_ci_visibility", location=Location.BODY),
            Param(name="archive_trace_events", location=Location.BODY),
            Param(name="datadog_service", location=Location.BODY),
            Param(name="datadog_env", location=Location.BODY),
            Param(name="datadog_tags", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="build_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="subgroup_events", location=Location.BODY),
            Param(name="project_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Diffblue Cover integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-diffblue-cover-integration",
        method="PUT",
        path="/projects/:id/services/diffblue-cover",
        params=(
            Param(name="diffblue_license_key", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_name", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_secret", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Discord integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-discord-integration",
        method="PUT",
        path="/projects/:id/services/discord",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Drone Ci integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-drone-ci-integration",
        method="PUT",
        path="/projects/:id/services/drone-ci",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="drone_url", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Emails On Push integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-emails-on-push-integration",
        method="PUT",
        path="/projects/:id/services/emails-on-push",
        params=(
            Param(name="send_from_committer_email", location=Location.BODY),
            Param(name="disable_diffs", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Ewm integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-ewm-integration",
        method="PUT",
        path="/projects/:id/services/ewm",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the External Wiki integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-external-wiki-integration",
        method="PUT",
        path="/projects/:id/services/external-wiki",
        params=(
            Param(name="external_wiki_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Git Guardian integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-git-guardian-integration",
        method="PUT",
        path="/projects/:id/services/git-guardian",
        params=(
            Param(name="api_url", location=Location.BODY),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Github integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-github-integration",
        method="PUT",
        path="/projects/:id/services/github",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="repository_url", location=Location.BODY, required=True),
            Param(name="static_context", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Gitlab Slack Application integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-gitlab-slack-application-integration",
        method="PUT",
        path="/projects/:id/services/gitlab-slack-application",
        params=(
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Google Cloud Platform Artifact Registry integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-google-cloud-platform-artifact-registry-integration",
        method="PUT",
        path="/projects/:id/services/google-cloud-platform-artifact-registry",
        params=(
            Param(name="artifact_registry_project_id", location=Location.BODY, required=True),
            Param(name="artifact_registry_repositories", location=Location.BODY, required=True),
            Param(name="artifact_registry_location", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Google Cloud Platform Workload Identity Federation integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-google-cloud-platform-workload-identity-federation-integration",
        method="PUT",
        path="/projects/:id/services/google-cloud-platform-workload-identity-federation",
        params=(
            Param(name="workload_identity_federation_project_id", location=Location.BODY, required=True),
            Param(name="workload_identity_federation_project_number", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_id", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_provider_id", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Google Play integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-google-play-integration-1",
        method="PUT",
        path="/projects/:id/services/google-play",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="service_account_key_file_name", location=Location.BODY, required=True),
            Param(name="service_account_key", location=Location.BODY, required=True),
            Param(name="google_play_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Hangouts Chat integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-hangouts-chat-integration",
        method="PUT",
        path="/projects/:id/services/hangouts-chat",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Harbor integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-harbor-integration",
        method="PUT",
        path="/projects/:id/services/harbor",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Irker integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-irker-integration",
        method="PUT",
        path="/projects/:id/services/irker",
        params=(
            Param(name="server_host", location=Location.BODY),
            Param(name="server_port", location=Location.BODY),
            Param(name="default_irc_uri", location=Location.BODY),
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="colorize_messages", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Jenkins integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-jenkins-integration-1",
        method="PUT",
        path="/projects/:id/services/jenkins",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="jenkins_url", location=Location.BODY, required=True),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Jira integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-jira-integration",
        method="PUT",
        path="/projects/:id/services/jira",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="jira_auth_type", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="jira_issue_regex", location=Location.BODY),
            Param(name="jira_issue_prefix", location=Location.BODY),
            Param(name="jira_issue_transition_id", location=Location.BODY),
            Param(name="issues_enabled", location=Location.BODY),
            Param(name="project_keys", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="vulnerabilities_enabled", location=Location.BODY),
            Param(name="vulnerabilities_issuetype", location=Location.BODY),
            Param(name="project_key", location=Location.BODY),
            Param(name="customize_jira_issue_enabled", location=Location.BODY),
            Param(name="jira_check_enabled", location=Location.BODY),
            Param(name="jira_exists_check_enabled", location=Location.BODY),
            Param(name="jira_assignee_check_enabled", location=Location.BODY),
            Param(name="jira_status_check_enabled", location=Location.BODY),
            Param(name="jira_allowed_statuses_as_string", location=Location.BODY),
            Param(name="comment_on_event_enabled", location=Location.BODY),
            Param(name="commit_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Jira Cloud App integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-jira-cloud-app-integration",
        method="PUT",
        path="/projects/:id/services/jira-cloud-app",
        params=(
            Param(name="jira_cloud_app_service_ids", location=Location.BODY),
            Param(name="jira_cloud_app_enable_deployment_gating", location=Location.BODY),
            Param(name="jira_cloud_app_deployment_gating_environments", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Linear integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-linear-integration",
        method="PUT",
        path="/projects/:id/services/linear",
        params=(
            Param(name="workspace_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Matrix integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-matrix-integration",
        method="PUT",
        path="/projects/:id/services/matrix",
        params=(
            Param(name="hostname", location=Location.BODY),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="room", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Mattermost integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mattermost-integration",
        method="PUT",
        path="/projects/:id/services/mattermost",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Mattermost Slash Commands integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mattermost-slash-commands-integration",
        method="PUT",
        path="/projects/:id/services/mattermost-slash-commands",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Trigger a slash command for mattermost-slash-commands".
    RestOperation(
        operation_id="openapi-only#trigger-a-slash-command-for-mattermost-slash-commands-1",
        method="POST",
        path="/projects/:id/services/mattermost_slash_commands/trigger",
        params=(Param(name="token", location=Location.BODY, required=True),),
    ),
    # "integrations: Create or update the Microsoft Teams integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-microsoft-teams-integration",
        method="PUT",
        path="/projects/:id/services/microsoft-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Mock Ci integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mock-ci-integration",
        method="PUT",
        path="/projects/:id/services/mock-ci",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="mock_service_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Mock Monitoring integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-mock-monitoring-integration-2",
        method="PUT",
        path="/projects/:id/services/mock-monitoring",
        params=(Param(name="use_inherited_settings", location=Location.BODY),),
    ),
    # "integrations: Create or update the Packagist integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-packagist-integration",
        method="PUT",
        path="/projects/:id/services/packagist",
        params=(
            Param(name="username", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="server", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Phorge integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-phorge-integration",
        method="PUT",
        path="/projects/:id/services/phorge",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Pipelines Email integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-pipelines-email-integration",
        method="PUT",
        path="/projects/:id/services/pipelines-email",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="notify_child_pipelines", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Pivotaltracker integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-pivotaltracker-integration",
        method="PUT",
        path="/projects/:id/services/pivotaltracker",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Pumble integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-pumble-integration",
        method="PUT",
        path="/projects/:id/services/pumble",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Pushover integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-pushover-integration",
        method="PUT",
        path="/projects/:id/services/pushover",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="user_key", location=Location.BODY, required=True),
            Param(name="device", location=Location.BODY),
            Param(name="priority", location=Location.BODY, required=True),
            Param(name="sound", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Redmine integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-redmine-integration",
        method="PUT",
        path="/projects/:id/services/redmine",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Slack integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-slack-integration",
        method="PUT",
        path="/projects/:id/services/slack",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Squash Tm integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-squash-tm-integration",
        method="PUT",
        path="/projects/:id/services/squash-tm",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Teamcity integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-teamcity-integration",
        method="PUT",
        path="/projects/:id/services/teamcity",
        params=(
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="teamcity_url", location=Location.BODY, required=True),
            Param(name="build_type", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Telegram integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-telegram-integration",
        method="PUT",
        path="/projects/:id/services/telegram",
        params=(
            Param(name="hostname", location=Location.BODY),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="room", location=Location.BODY, required=True),
            Param(name="thread", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Unify Circuit integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-unify-circuit-integration",
        method="PUT",
        path="/projects/:id/services/unify-circuit",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Webex Teams integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-webex-teams-integration",
        method="PUT",
        path="/projects/:id/services/webex-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Youtrack integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-youtrack-integration",
        method="PUT",
        path="/projects/:id/services/youtrack",
        params=(
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Create or update the Zentao integration".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-zentao-integration-2",
        method="PUT",
        path="/projects/:id/services/zentao",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="api_token", location=Location.BODY, required=True),
            Param(name="zentao_product_xid", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "integrations: Trigger a global slack command".
    RestOperation(
        operation_id="openapi-only#trigger-a-global-slack-command",
        method="POST",
        path="/slack/trigger",
        params=(Param(name="text", location=Location.BODY, required=True),),
    ),
    # "jira_connect_subscriptions: Subscribe a namespace to a JiraConnectInstallation".
    RestOperation(
        operation_id="openapi-only#subscribe-a-namespace-to-a-jiraconnectinstallation",
        method="POST",
        path="/integrations/jira_connect/subscriptions",
        params=(
            Param(name="jwt", location=Location.BODY, required=True),
            Param(name="namespace_path", location=Location.BODY, required=True),
        ),
    ),
    # "jira_forge_installation: Update the GitLab for Jira (Forge) installation instance URL".
    RestOperation(
        operation_id="openapi-only#update-the-gitlab-for-jira-forge-installation-instance-url",
        method="PUT",
        path="/integrations/jira_forge/installation",
        params=(Param(name="instance_url", location=Location.BODY),),
    ),
    # "jira_forge_installation: Register the GitLab for Jira (Forge) system token for direct dev-info sync".
    RestOperation(
        operation_id="openapi-only#register-the-gitlab-for-jira-forge-system-token-for-direct-dev-info-sync",
        method="POST",
        path="/integrations/jira_forge/installation/forge_token",
    ),
    # "jira_forge_subscriptions: List GitLab for Jira (Forge) namespace subscriptions".
    RestOperation(
        operation_id="openapi-only#list-gitlab-for-jira-forge-namespace-subscriptions",
        method="GET",
        path="/integrations/jira_forge/subscriptions",
    ),
    # "jira_forge_subscriptions: Create a GitLab for Jira (Forge) namespace subscription".
    RestOperation(
        operation_id="openapi-only#create-a-gitlab-for-jira-forge-namespace-subscription",
        method="POST",
        path="/integrations/jira_forge/subscriptions",
        params=(Param(name="namespace_path", location=Location.BODY, required=True),),
    ),
    # "jira_forge_subscriptions: Delete a GitLab for Jira (Forge) namespace subscription".
    RestOperation(
        operation_id="openapi-only#delete-a-gitlab-for-jira-forge-namespace-subscription",
        method="DELETE",
        path="/integrations/jira_forge/subscriptions/:id",
    ),
    # "jobs: putApiV4JobsId".
    RestOperation(
        operation_id="openapi-only#putapiv4jobsid",
        method="PUT",
        path="/jobs/:id",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="state", location=Location.BODY),
            Param(name="checksum", location=Location.BODY),
            Param(name="failure_reason", location=Location.BODY),
            Param(name="output", location=Location.BODY, kind=Kind.HASH),
            Param(name="exit_code", location=Location.BODY),
            Param(name="runtime_environment_key", location=Location.BODY),
        ),
    ),
    # "jobs: Download job artifacts".
    RestOperation(
        operation_id="openapi-only#download-job-artifacts",
        method="GET",
        path="/jobs/:id/artifacts",
        params=(
            Param(name="token", location=Location.QUERY),
            Param(name="direct_download", location=Location.QUERY),
        ),
    ),
    # "jobs: Upload job artifacts".
    RestOperation(
        operation_id="openapi-only#upload-job-artifacts",
        method="POST",
        path="/jobs/:id/artifacts",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="token", location=Location.BODY),
            Param(name="expire_in", location=Location.BODY),
            Param(name="artifact_type", location=Location.BODY),
            Param(name="artifact_format", location=Location.BODY),
            Param(name="metadata", location=Location.BODY, kind=Kind.FILE),
            Param(name="accessibility", location=Location.BODY),
        ),
    ),
    # "jobs: Authorize artifacts upload".
    RestOperation(
        operation_id="openapi-only#authorize-artifacts-upload",
        method="POST",
        path="/jobs/:id/artifacts/authorize",
        params=(
            Param(name="token", location=Location.BODY),
            Param(name="filesize", location=Location.BODY),
            Param(name="artifact_type", location=Location.BODY),
        ),
    ),
    # "jobs: Get the runtime environment key for a job".
    RestOperation(
        operation_id="openapi-only#get-the-runtime-environment-key-for-a-job",
        method="GET",
        path="/jobs/:id/runtime_environment_key",
        params=(Param(name="token", location=Location.QUERY),),
    ),
    # "jobs: patchApiV4JobsIdTrace".
    RestOperation(
        operation_id="openapi-only#patchapiv4jobsidtrace",
        method="PATCH",
        path="/jobs/:id/trace",
        params=(
            Param(name="token", location=Location.BODY),
            Param(name="debug_trace", location=Location.BODY),
        ),
    ),
    # "jobs: Request a job".
    RestOperation(
        operation_id="openapi-only#request-a-job",
        method="POST",
        path="/jobs/request",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="system_id", location=Location.BODY),
            Param(name="last_update", location=Location.BODY),
            Param(name="info", location=Location.BODY, kind=Kind.HASH),
            Param(name="session", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "merge_request_approvals: Change approval-related configuration".
    RestOperation(
        operation_id="openapi-only#change-approval-related-configuration",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/approvals",
        params=(Param(name="approvals_required", location=Location.BODY, required=True),),
    ),
    # "metric_images: Authorize metric image upload".
    RestOperation(
        operation_id="openapi-only#authorize-metric-image-upload",
        method="POST",
        path="/projects/:id/issues/:issue_iid/metric_images/authorize",
    ),
    # "namespaces: Update a namespace".
    RestOperation(
        operation_id="openapi-only#update-a-namespace",
        method="PUT",
        path="/namespaces/:id",
        params=(
            Param(name="shared_runners_minutes_limit", location=Location.BODY),
            Param(name="extra_shared_runners_minutes_limit", location=Location.BODY),
            Param(name="additional_purchased_storage_size", location=Location.BODY),
            Param(name="additional_purchased_storage_ends_on", location=Location.BODY),
            Param(name="gitlab_subscription_attributes", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "namespaces: Retrieve namespace subscription".
    RestOperation(
        operation_id="openapi-only#retrieve-namespace-subscription",
        method="GET",
        path="/namespaces/:id/gitlab_subscription",
    ),
    # "namespaces: Creates a storage limit exclusion for a Namespace".
    RestOperation(
        operation_id="openapi-only#creates-a-storage-limit-exclusion-for-a-namespace",
        method="POST",
        path="/namespaces/:id/storage/limit_exclusion",
        params=(Param(name="reason", location=Location.BODY, required=True),),
    ),
    # "namespaces: Removes a storage limit exclusion for a Namespace".
    RestOperation(
        operation_id="openapi-only#removes-a-storage-limit-exclusion-for-a-namespace",
        method="DELETE",
        path="/namespaces/:id/storage/limit_exclusion",
    ),
    # "namespaces: Retrieve all limit exclusions".
    RestOperation(
        operation_id="openapi-only#retrieve-all-limit-exclusions",
        method="GET",
        path="/namespaces/storage/limit_exclusions",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "offline_transfers: List all offline transfer exports".
    RestOperation(
        operation_id="openapi-only#list-all-offline-transfer-exports",
        method="GET",
        path="/offline_exports",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "offline_transfers: Start a new offline transfer export".
    RestOperation(
        operation_id="openapi-only#start-a-new-offline-transfer-export",
        method="POST",
        path="/offline_exports",
        params=(
            Param(name="bucket", location=Location.BODY, required=True),
            Param(name="aws_s3_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="s3_compatible_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_hmac_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_adc_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="entities", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),
        ),
    ),
    # "offline_transfers: Get offline transfer export details".
    RestOperation(
        operation_id="openapi-only#get-offline-transfer-export-details",
        method="GET",
        path="/offline_exports/:id",
    ),
    # "offline_transfers: Start a new offline transfer import".
    RestOperation(
        operation_id="openapi-only#start-a-new-offline-transfer-import",
        method="POST",
        path="/offline_imports",
        params=(
            Param(name="bucket", location=Location.BODY, required=True),
            Param(name="aws_s3_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="s3_compatible_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_hmac_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="gcs_adc_configuration", location=Location.BODY, kind=Kind.HASH),
            Param(name="export_prefix", location=Location.BODY, required=True),
            Param(name="entities", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),
        ),
    ),
    # "organizations: Soft-delete an organization".
    RestOperation(
        operation_id="openapi-only#soft-delete-an-organization",
        method="DELETE",
        path="/organizations/:id",
    ),
    # "packages: Download a package file".
    RestOperation(
        operation_id="openapi-only#download-a-package-file",
        method="GET",
        path="/projects/:id/packages/:package_id/package_files/:package_file_id/download",
    ),
    # "packages: Download package file".
    RestOperation(
        operation_id="openapi-only#download-package-file",
        method="GET",
        path="/projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name",
    ),
    # "packages: Upload package file".
    RestOperation(
        operation_id="openapi-only#upload-package-file",
        method="PUT",
        path="/projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name",
        params=(
            Param(name="status", location=Location.QUERY),
            Param(name="select", location=Location.QUERY),
        ),
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "packages: Workhorse authorize generic package file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-generic-package-file",
        method="PUT",
        path="/projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name/authorize",
        params=(Param(name="status", location=Location.BODY),),
    ),
    # "packages: Workhorse authorize the maven package file upload".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-maven-package-file-upload",
        method="PUT",
        path="/projects/:id/packages/maven/*path/:file_name/authorize",
    ),
    # "packages_cargo: Get the sparse index for a Cargo crate (1-character name)".
    RestOperation(
        operation_id="openapi-only#get-the-sparse-index-for-a-cargo-crate-1-character-name",
        method="GET",
        path="/projects/:id/packages/cargo/1/:package_name",
    ),
    # "packages_cargo: Get the sparse index for a Cargo crate (2-character name)".
    RestOperation(
        operation_id="openapi-only#get-the-sparse-index-for-a-cargo-crate-2-character-name",
        method="GET",
        path="/projects/:id/packages/cargo/2/:package_name",
    ),
    # "packages_cargo: Get the sparse index for a Cargo crate (3-character name)".
    RestOperation(
        operation_id="openapi-only#get-the-sparse-index-for-a-cargo-crate-3-character-name",
        method="GET",
        path="/projects/:id/packages/cargo/3/:first_char/:package_name",
    ),
    # "packages_cargo: Download a Cargo crate".
    RestOperation(
        operation_id="openapi-only#download-a-cargo-crate",
        method="GET",
        path="/projects/:id/packages/cargo/:package_name/:package_version/download",
    ),
    # "packages_cargo: Get the sparse index for a Cargo crate (4+ character name)".
    RestOperation(
        operation_id="openapi-only#get-the-sparse-index-for-a-cargo-crate-4-character-name",
        method="GET",
        path="/projects/:id/packages/cargo/:prefix_1/:prefix_2/:package_name",
    ),
    # "packages_cargo: Get config.json".
    RestOperation(
        operation_id="openapi-only#get-configjson",
        method="GET",
        path="/projects/:id/packages/cargo/config.json",
    ),
    # "packages_composer: Composer packages endpoint at group level for package versions metadata".
    RestOperation(
        operation_id="openapi-only#composer-packages-endpoint-at-group-level-for-package-versions-metadata",
        method="GET",
        path="/group/:id/-/packages/composer/*package_name",
    ),
    # "packages_conan: Workhorse authorize the Conan recipe file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-recipe-file",
        method="PUT",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name/authorize",
    ),
    # "packages_conan: Workhorse authorize the Conan package file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-package-file",
        method="PUT",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name/authorize",
    ),
    # "packages_conan: Retrieve a recipe snapshot".
    RestOperation(
        operation_id="openapi-only#retrieve-a-recipe-snapshot",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel",
    ),
    # "packages_conan: Workhorse authorize the Conan recipe file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-recipe-file-1",
        method="PUT",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name/authorize",
    ),
    # "packages_conan: Workhorse authorize the Conan package file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-package-file-1",
        method="PUT",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name/authorize",
    ),
    # "packages_conan: Delete recipe revision".
    RestOperation(
        operation_id="openapi-only#delete-recipe-revision",
        method="DELETE",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision",
    ),
    # "packages_conan: Workhorse authorize the Conan recipe file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-recipe-file-2",
        method="PUT",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/files/:file_name/authorize",
    ),
    # "packages_conan: List all package files".
    RestOperation(
        operation_id="openapi-only#list-all-package-files",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions/:package_revision/files",
    ),
    # "packages_conan: Workhorse authorize the Conan package file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-conan-package-file-2",
        method="PUT",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions/:package_revision/files/:file_name/authorize",
    ),
    # "packages_debian: The binary files index".
    RestOperation(
        operation_id="openapi-only#the-binary-files-index",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/binary-:architecture/Packages",
    ),
    # "packages_debian: The binary files index by hash".
    RestOperation(
        operation_id="openapi-only#the-binary-files-index-by-hash",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/binary-:architecture/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The installer (udeb) binary files index".
    RestOperation(
        operation_id="openapi-only#the-installer-udeb-binary-files-index",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/debian-installer/binary-:architecture/Packages",
    ),
    # "packages_debian: The installer (udeb) binary files index by hash".
    RestOperation(
        operation_id="openapi-only#the-installer-udeb-binary-files-index-by-hash",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/debian-installer/binary-:architecture/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The source files index".
    RestOperation(
        operation_id="openapi-only#the-source-files-index",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/source/Sources",
    ),
    # "packages_debian: The source files index by hash".
    RestOperation(
        operation_id="openapi-only#the-source-files-index-by-hash",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/:component/source/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The signed Release file".
    RestOperation(
        operation_id="openapi-only#the-signed-release-file",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/InRelease",
    ),
    # "packages_debian: The unsigned Release file".
    RestOperation(
        operation_id="openapi-only#the-unsigned-release-file",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/Release",
    ),
    # "packages_debian: The Release file signature".
    RestOperation(
        operation_id="openapi-only#the-release-file-signature",
        method="GET",
        path="/groups/:id/-/packages/debian/dists/*distribution/Release.gpg",
    ),
    # "packages_debian: Download Debian package".
    RestOperation(
        operation_id="openapi-only#download-debian-package",
        method="GET",
        path="/groups/:id/-/packages/debian/pool/:distribution/:project_id/:letter/:package_name/:package_version/:file_name",
    ),
    # "packages_debian: Authorize Debian package upload".
    RestOperation(
        operation_id="openapi-only#authorize-debian-package-upload",
        method="PUT",
        path="/projects/:id/packages/debian/:file_name/authorize",
        params=(
            Param(name="distribution", location=Location.BODY),
            Param(name="component", location=Location.BODY, required=True),
        ),
    ),
    # "packages_debian: The binary files index".
    RestOperation(
        operation_id="openapi-only#the-binary-files-index-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/binary-:architecture/Packages",
    ),
    # "packages_debian: The binary files index by hash".
    RestOperation(
        operation_id="openapi-only#the-binary-files-index-by-hash-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/binary-:architecture/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The installer (udeb) binary files index".
    RestOperation(
        operation_id="openapi-only#the-installer-udeb-binary-files-index-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/debian-installer/binary-:architecture/Packages",
    ),
    # "packages_debian: The installer (udeb) binary files index by hash".
    RestOperation(
        operation_id="openapi-only#the-installer-udeb-binary-files-index-by-hash-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/debian-installer/binary-:architecture/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The source files index".
    RestOperation(
        operation_id="openapi-only#the-source-files-index-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/source/Sources",
    ),
    # "packages_debian: The source files index by hash".
    RestOperation(
        operation_id="openapi-only#the-source-files-index-by-hash-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/:component/source/by-hash/SHA256/:file_sha256",
    ),
    # "packages_debian: The signed Release file".
    RestOperation(
        operation_id="openapi-only#the-signed-release-file-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/InRelease",
    ),
    # "packages_debian: The unsigned Release file".
    RestOperation(
        operation_id="openapi-only#the-unsigned-release-file-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/Release",
    ),
    # "packages_debian: The Release file signature".
    RestOperation(
        operation_id="openapi-only#the-release-file-signature-1",
        method="GET",
        path="/projects/:id/packages/debian/dists/*distribution/Release.gpg",
    ),
    # "packages_helm: Authorize a chart upload from workhorse".
    RestOperation(
        operation_id="openapi-only#authorize-a-chart-upload-from-workhorse",
        method="POST",
        path="/projects/:id/packages/helm/api/:channel/charts/authorize",
    ),
    # "packages_npm: NPM registry metadata endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-metadata-endpoint",
        method="GET",
        path="/groups/:id/-/packages/npm/*package_name",
    ),
    # "packages_npm: NPM registry bulk advisory endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-bulk-advisory-endpoint",
        method="POST",
        path="/groups/:id/-/packages/npm/-/npm/v1/security/advisories/bulk",
    ),
    # "packages_npm: NPM registry quick audit endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-quick-audit-endpoint",
        method="POST",
        path="/groups/:id/-/packages/npm/-/npm/v1/security/audits/quick",
    ),
    # "packages_npm: Get all tags for a given an NPM package".
    RestOperation(
        operation_id="openapi-only#get-all-tags-for-a-given-an-npm-package",
        method="GET",
        path="/groups/:id/-/packages/npm/-/package/*package_name/dist-tags",
    ),
    # "packages_npm: Create or Update the given tag for the given NPM package and version".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version",
        method="PUT",
        path="/groups/:id/-/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_npm: Deletes the given tag".
    RestOperation(
        operation_id="openapi-only#deletes-the-given-tag",
        method="DELETE",
        path="/groups/:id/-/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_npm: NPM registry metadata endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-metadata-endpoint-1",
        method="GET",
        path="/packages/npm/*package_name",
    ),
    # "packages_npm: NPM registry bulk advisory endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-bulk-advisory-endpoint-1",
        method="POST",
        path="/packages/npm/-/npm/v1/security/advisories/bulk",
    ),
    # "packages_npm: NPM registry quick audit endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-quick-audit-endpoint-1",
        method="POST",
        path="/packages/npm/-/npm/v1/security/audits/quick",
    ),
    # "packages_npm: Get all tags for a given an NPM package".
    RestOperation(
        operation_id="openapi-only#get-all-tags-for-a-given-an-npm-package-1",
        method="GET",
        path="/packages/npm/-/package/*package_name/dist-tags",
    ),
    # "packages_npm: Create or Update the given tag for the given NPM package and version".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version-1",
        method="PUT",
        path="/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_npm: Deletes the given tag".
    RestOperation(
        operation_id="openapi-only#deletes-the-given-tag-1",
        method="DELETE",
        path="/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_npm: NPM registry metadata endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-metadata-endpoint-2",
        method="GET",
        path="/projects/:id/packages/npm/*package_name",
    ),
    # "packages_npm: NPM registry bulk advisory endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-bulk-advisory-endpoint-2",
        method="POST",
        path="/projects/:id/packages/npm/-/npm/v1/security/advisories/bulk",
    ),
    # "packages_npm: NPM registry quick audit endpoint".
    RestOperation(
        operation_id="openapi-only#npm-registry-quick-audit-endpoint-2",
        method="POST",
        path="/projects/:id/packages/npm/-/npm/v1/security/audits/quick",
    ),
    # "packages_npm: Get all tags for a given an NPM package".
    RestOperation(
        operation_id="openapi-only#get-all-tags-for-a-given-an-npm-package-2",
        method="GET",
        path="/projects/:id/packages/npm/-/package/*package_name/dist-tags",
    ),
    # "packages_npm: Create or Update the given tag for the given NPM package and version".
    RestOperation(
        operation_id="openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version-2",
        method="PUT",
        path="/projects/:id/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_npm: Deletes the given tag".
    RestOperation(
        operation_id="openapi-only#deletes-the-given-tag-2",
        method="DELETE",
        path="/projects/:id/packages/npm/-/package/*package_name/dist-tags/:tag",
    ),
    # "packages_nuget: The NuGet V3 Feed Service Index".
    RestOperation(
        operation_id="openapi-only#the-nuget-v3-feed-service-index",
        method="GET",
        path="/groups/:id/-/packages/nuget/index",
    ),
    # "packages_nuget: The NuGet Metadata Service - Package name and version level".
    RestOperation(
        operation_id="openapi-only#the-nuget-metadata-service---package-name-and-version-level",
        method="GET",
        path="/groups/:id/-/packages/nuget/metadata/*package_name/*package_version",
    ),
    # "packages_nuget: The NuGet Metadata Service - Package name level".
    RestOperation(
        operation_id="openapi-only#the-nuget-metadata-service---package-name-level",
        method="GET",
        path="/groups/:id/-/packages/nuget/metadata/*package_name/index",
    ),
    # "packages_nuget: The NuGet Search Service".
    RestOperation(
        operation_id="openapi-only#the-nuget-search-service",
        method="GET",
        path="/groups/:id/-/packages/nuget/query",
        params=(
            Param(name="q", location=Location.QUERY),
            Param(name="skip", location=Location.QUERY),
            Param(name="take", location=Location.QUERY),
            Param(name="prerelease", location=Location.QUERY),
        ),
    ),
    # "packages_nuget: The NuGet Symbol File Download Endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-symbol-file-download-endpoint",
        method="GET",
        path="/groups/:id/-/packages/nuget/symbolfiles/*file_name/*signature/*same_file_name",
    ),
    # "packages_nuget: The NuGet V2 Feed Service Index".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-service-index",
        method="GET",
        path="/groups/:id/-/packages/nuget/v2",
    ),
    # "packages_nuget: The NuGet V2 Feed Package $metadata endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-package-metadata-endpoint",
        method="GET",
        path="/groups/:id/-/packages/nuget/v2/$metadata",
    ),
    # "packages_nuget: The NuGet Package Authorize endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-package-authorize-endpoint",
        method="PUT",
        path="/projects/:id/packages/nuget/authorize",
    ),
    # "packages_nuget: The NuGet V3 Feed Service Index".
    RestOperation(
        operation_id="openapi-only#the-nuget-v3-feed-service-index-1",
        method="GET",
        path="/projects/:id/packages/nuget/index",
    ),
    # "packages_nuget: The NuGet Metadata Service - Package name and version level".
    RestOperation(
        operation_id="openapi-only#the-nuget-metadata-service---package-name-and-version-level-1",
        method="GET",
        path="/projects/:id/packages/nuget/metadata/*package_name/*package_version",
    ),
    # "packages_nuget: The NuGet Metadata Service - Package name level".
    RestOperation(
        operation_id="openapi-only#the-nuget-metadata-service---package-name-level-1",
        method="GET",
        path="/projects/:id/packages/nuget/metadata/*package_name/index",
    ),
    # "packages_nuget: The NuGet Search Service".
    RestOperation(
        operation_id="openapi-only#the-nuget-search-service-1",
        method="GET",
        path="/projects/:id/packages/nuget/query",
        params=(
            Param(name="q", location=Location.QUERY),
            Param(name="skip", location=Location.QUERY),
            Param(name="take", location=Location.QUERY),
            Param(name="prerelease", location=Location.QUERY),
        ),
    ),
    # "packages_nuget: The NuGet Symbol File Download Endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-symbol-file-download-endpoint-1",
        method="GET",
        path="/projects/:id/packages/nuget/symbolfiles/*file_name/*signature/*same_file_name",
    ),
    # "packages_nuget: The NuGet Symbol Package Authorize endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-symbol-package-authorize-endpoint",
        method="PUT",
        path="/projects/:id/packages/nuget/symbolpackage/authorize",
    ),
    # "packages_nuget: The NuGet V2 Feed Service Index".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-service-index-1",
        method="GET",
        path="/projects/:id/packages/nuget/v2",
    ),
    # "packages_nuget: The NuGet V2 Feed Package $metadata endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-package-metadata-endpoint-1",
        method="GET",
        path="/projects/:id/packages/nuget/v2/$metadata",
    ),
    # "packages_nuget: The NuGet V2 Feed Package Authorize endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-package-authorize-endpoint",
        method="PUT",
        path="/projects/:id/packages/nuget/v2/authorize",
    ),
    # "packages_nuget: The NuGet V2 Feed Find Packages by ID endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-find-packages-by-id-endpoint",
        method="GET",
        path="/projects/:project_id/packages/nuget/v2/FindPackagesById\\(\\)",
        params=(Param(name="id", location=Location.QUERY, required=True),),
    ),
    # "packages_nuget: The NuGet V2 Feed Single Package Metadata endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-single-package-metadata-endpoint",
        method="GET",
        path="/projects/:project_id/packages/nuget/v2/Packages\\(Id='*package_name',Version='*package_version'\\)",
    ),
    # "packages_nuget: The NuGet V2 Feed Enumerate Packages endpoint".
    RestOperation(
        operation_id="openapi-only#the-nuget-v2-feed-enumerate-packages-endpoint",
        method="GET",
        path="/projects/:project_id/packages/nuget/v2/Packages\\(\\)",
        params=(Param(name="$filter", location=Location.QUERY, required=True),),
    ),
    # "packages_pypi: Authorize the PyPi package upload from workhorse".
    RestOperation(
        operation_id="openapi-only#authorize-the-pypi-package-upload-from-workhorse",
        method="POST",
        path="/projects/:id/packages/pypi/authorize",
    ),
    # "packages_rpm: Upload a RPM package".
    RestOperation(
        operation_id="openapi-only#upload-a-rpm-package",
        method="POST",
        path="/projects/:id/packages/rpm",
    ),
    # "packages_rpm: Download RPM package files".
    RestOperation(
        operation_id="openapi-only#download-rpm-package-files",
        method="GET",
        path="/projects/:id/packages/rpm/*package_file_id/*file_name",
    ),
    # "packages_rpm: Authorize package upload from workhorse".
    RestOperation(
        operation_id="openapi-only#authorize-package-upload-from-workhorse",
        method="POST",
        path="/projects/:id/packages/rpm/authorize",
    ),
    # "packages_rpm: Download repository metadata files".
    RestOperation(
        operation_id="openapi-only#download-repository-metadata-files",
        method="GET",
        path="/projects/:id/packages/rpm/repodata/*file_name",
    ),
    # "packages_rubygem: Authorize a gem upload from workhorse".
    RestOperation(
        operation_id="openapi-only#authorize-a-gem-upload-from-workhorse",
        method="POST",
        path="/projects/:id/packages/rubygems/api/v1/gems/authorize",
    ),
    # "pipelines: List all bridge jobs by pipeline".
    RestOperation(
        operation_id="openapi-only#list-all-bridge-jobs-by-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/bridges",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "project_import: Import a project from a Git URL".
    RestOperation(
        operation_id="openapi-only#import-a-project-from-a-git-url",
        method="POST",
        path="/projects/:id/import/git",
        params=(
            Param(name="import_url", location=Location.BODY, required=True),
            Param(name="import_url_user", location=Location.BODY),
            Param(name="import_url_password", location=Location.BODY),
        ),
    ),
    # "project_import: Authorize project relation import".
    RestOperation(
        operation_id="openapi-only#authorize-project-relation-import",
        method="POST",
        path="/projects/import-relation/authorize",
    ),
    # "project_import: Workhorse authorize the project import upload".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-project-import-upload",
        method="POST",
        path="/projects/import/authorize",
    ),
    # "projects: Create a CI configuration merge request".
    RestOperation(
        operation_id="openapi-only#create-a-ci-configuration-merge-request",
        method="POST",
        path="/projects/:id/create_ci_config",
    ),
    # "projects: getApiV4ProjectsIdPagesAccess".
    RestOperation(
        operation_id="openapi-only#getapiv4projectsidpagesaccess",
        method="GET",
        path="/projects/:id/pages_access",
    ),
    # "projects: Start a task to recalculate repository size for a project".
    RestOperation(
        operation_id="openapi-only#start-a-task-to-recalculate-repository-size-for-a-project",
        method="POST",
        path="/projects/:id/repository_size",
    ),
    # "projects: List all Terraform state protection rules for a project".
    RestOperation(
        operation_id="openapi-only#list-all-terraform-state-protection-rules-for-a-project",
        method="GET",
        path="/projects/:id/terraform/state_protection_rules",
    ),
    # "projects: Create a Terraform state protection rule for a project".
    RestOperation(
        operation_id="openapi-only#create-a-terraform-state-protection-rule-for-a-project",
        method="POST",
        path="/projects/:id/terraform/state_protection_rules",
        params=(
            Param(name="state_name", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_write", location=Location.BODY, required=True),
            Param(name="allowed_from", location=Location.BODY),
        ),
    ),
    # "projects: Update a Terraform state protection rule for a project".
    RestOperation(
        operation_id="openapi-only#update-a-terraform-state-protection-rule-for-a-project",
        method="PATCH",
        path="/projects/:id/terraform/state_protection_rules/:terraform_state_protection_rule_id",
        params=(
            Param(name="state_name", location=Location.BODY),
            Param(name="minimum_access_level_for_write", location=Location.BODY),
            Param(name="allowed_from", location=Location.BODY),
        ),
    ),
    # "projects: Delete a Terraform state protection rule".
    RestOperation(
        operation_id="openapi-only#delete-a-terraform-state-protection-rule",
        method="DELETE",
        path="/projects/:id/terraform/state_protection_rules/:terraform_state_protection_rule_id",
    ),
    # "projects: Workhorse authorize the file upload".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-the-file-upload-1",
        method="POST",
        path="/projects/:id/uploads/authorize",
    ),
    # "repositories: Retrieve file archive from a repository".
    RestOperation(
        operation_id="openapi-only#retrieve-file-archive-from-a-repository",
        method="GET",
        path="/projects/:id/repository/archive",
        params=(
            Param(name="sha", location=Location.QUERY),
            Param(name="ref_type", location=Location.QUERY),
            Param(name="format", location=Location.QUERY),
            Param(name="path", location=Location.QUERY),
            Param(name="include_lfs_blobs", location=Location.QUERY),
            Param(name="exclude_paths", location=Location.QUERY, kind=Kind.ARRAY),
        ),
    ),
    # "runners: List runner's projects".
    RestOperation(
        operation_id="openapi-only#list-runners-projects",
        method="GET",
        path="/runners/:id/projects",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "terraform: Get details about specific version of a module".
    RestOperation(
        operation_id="openapi-only#get-details-about-specific-version-of-a-module",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/*module_version",
    ),
    # "terraform: Download the latest version of a module".
    RestOperation(
        operation_id="openapi-only#download-the-latest-version-of-a-module",
        method="GET",
        path="/projects/:id/packages/terraform/modules/:module_name/:module_system",
        params=(Param(name="terraform-get", location=Location.QUERY),),
    ),
    # "terraform: Upload Terraform Module package file".
    RestOperation(
        operation_id="openapi-only#upload-terraform-module-package-file",
        method="PUT",
        path="/projects/:id/packages/terraform/modules/:module_name/:module_system/*module_version/file",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "terraform: Workhorse authorize Terraform Module package file".
    RestOperation(
        operation_id="openapi-only#workhorse-authorize-terraform-module-package-file",
        method="PUT",
        path="/projects/:id/packages/terraform/modules/:module_name/:module_system/*module_version/file/authorize",
    ),
    # "terraform: Retrieve a Terraform state".
    RestOperation(
        operation_id="openapi-only#retrieve-a-terraform-state",
        method="GET",
        path="/projects/:id/terraform/state/:name",
        params=(Param(name="ID", location=Location.QUERY),),
    ),
    # "terraform: Create or update a Terraform state".
    RestOperation(
        operation_id="openapi-only#create-or-update-a-terraform-state",
        method="POST",
        path="/projects/:id/terraform/state/:name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "terraform: Delete a Terraform state".
    RestOperation(
        operation_id="openapi-only#delete-a-terraform-state",
        method="DELETE",
        path="/projects/:id/terraform/state/:name",
    ),
    # "terraform: Authorize Terraform state upload".
    RestOperation(
        operation_id="openapi-only#authorize-terraform-state-upload",
        method="POST",
        path="/projects/:id/terraform/state/:name/authorize",
    ),
    # "terraform: Lock a Terraform state".
    RestOperation(
        operation_id="openapi-only#lock-a-terraform-state",
        method="POST",
        path="/projects/:id/terraform/state/:name/lock",
        params=(
            Param(name="ID", location=Location.BODY, required=True),
            Param(name="Operation", location=Location.BODY, required=True),
            Param(name="Info", location=Location.BODY, required=True),
            Param(name="Who", location=Location.BODY, required=True),
            Param(name="Version", location=Location.BODY, required=True),
            Param(name="Created", location=Location.BODY, required=True),
            Param(name="Path", location=Location.BODY, required=True),
        ),
    ),
    # "terraform: Unlock a Terraform state".
    RestOperation(
        operation_id="openapi-only#unlock-a-terraform-state",
        method="DELETE",
        path="/projects/:id/terraform/state/:name/lock",
        params=(Param(name="ID", location=Location.QUERY),),
    ),
    # "terraform: Retrieve a Terraform state version".
    RestOperation(
        operation_id="openapi-only#retrieve-a-terraform-state-version",
        method="GET",
        path="/projects/:id/terraform/state/:name/versions/:serial",
    ),
    # "terraform: Delete a Terraform state version".
    RestOperation(
        operation_id="openapi-only#delete-a-terraform-state-version",
        method="DELETE",
        path="/projects/:id/terraform/state/:name/versions/:serial",
    ),
    # "unleash: getApiV4FeatureFlagsUnleashProjectId".
    RestOperation(
        operation_id="openapi-only#getapiv4featureflagsunleashprojectid",
        method="GET",
        path="/feature_flags/unleash/:project_id",
        params=(
            Param(name="instance_id", location=Location.QUERY),
            Param(name="app_name", location=Location.QUERY),
        ),
    ),
    # "unleash: getApiV4FeatureFlagsUnleashProjectIdClientFeatures".
    RestOperation(
        operation_id="openapi-only#getapiv4featureflagsunleashprojectidclientfeatures",
        method="GET",
        path="/feature_flags/unleash/:project_id/client/features",
        params=(
            Param(name="instance_id", location=Location.QUERY),
            Param(name="app_name", location=Location.QUERY),
        ),
    ),
    # "unleash: postApiV4FeatureFlagsUnleashProjectIdClientMetrics".
    RestOperation(
        operation_id="openapi-only#postapiv4featureflagsunleashprojectidclientmetrics",
        method="POST",
        path="/feature_flags/unleash/:project_id/client/metrics",
        params=(
            Param(name="instance_id", location=Location.BODY),
            Param(name="app_name", location=Location.BODY),
        ),
    ),
    # "unleash: postApiV4FeatureFlagsUnleashProjectIdClientRegister".
    RestOperation(
        operation_id="openapi-only#postapiv4featureflagsunleashprojectidclientregister",
        method="POST",
        path="/feature_flags/unleash/:project_id/client/register",
        params=(
            Param(name="instance_id", location=Location.BODY),
            Param(name="app_name", location=Location.BODY),
        ),
    ),
    # "unleash: Get a list of features (v2 client support)".
    RestOperation(
        operation_id="openapi-only#get-a-list-of-features-v2-client-support",
        method="GET",
        path="/feature_flags/unleash/:project_id/features",
        params=(
            Param(name="instance_id", location=Location.QUERY),
            Param(name="app_name", location=Location.QUERY),
        ),
    ),
    # "usage_data: Track usage data event".
    RestOperation(
        operation_id="openapi-only#track-usage-data-event",
        method="POST",
        path="/usage_data/increment_counter",
        params=(Param(name="event", location=Location.BODY, required=True),),
    ),
    # "usage_data: postApiV4UsageDataIncrementUniqueUsers".
    RestOperation(
        operation_id="openapi-only#postapiv4usagedataincrementuniqueusers",
        method="POST",
        path="/usage_data/increment_unique_users",
        params=(Param(name="event", location=Location.BODY, required=True),),
    ),
    # "usage_data: Track multiple internal GitLab events".
    RestOperation(
        operation_id="openapi-only#track-multiple-internal-gitlab-events",
        method="POST",
        path="/usage_data/track_events",
        params=(Param(name="events", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
