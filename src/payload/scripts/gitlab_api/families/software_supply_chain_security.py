"""The ``software-supply-chain-security`` endpoint family of the GitLab wrapper: users, tokens, access requests,
service accounts, audit events, applications and the instance settings.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/software-supply-chain-security.md`` (issue #13, design.md D1 and D5): the method, the
path as ``operations-index.md`` writes it, and one ``Param`` per query or body attribute with the table's Type column as
its ``Kind``. Part 1 declares the two records the ``issue start`` and ``issue assign`` commands compose (design.md D6):
the authenticated user (``GET /user``) and the user list filtered by ``username`` (``GET /users``). Each key has more
than one row in the index (the regular-user and the administrator sections; ``GET /user`` also under "Access GitLab
API with access token"), and the one record maps them all.

Issue #42 (``change.md`` AC-1 to AC-5) adds one record for every other key of the family, in page order, its ID the
Reference of the key's row; of two rows on one key the record is the first section ("Update application appearance",
"Retrieve a single user as a regular user"), and a section with several endpoints is recorded first by its
``/projects/:id/`` endpoint, else its first: its base record. A ``form`` row is a BODY ``Param``; a ``name[].…`` row is
part of its parent, no ``Param``. A row noted "file upload" and ``avatar`` of ``PUT /user/avatar``, ``POST /users`` and
``PUT /users/:id`` are ``Kind.FILE``, an ``array`` row with ``name[].…`` rows ``ARRAY_OF_HASHES``, any other Type naming
an array ``ARRAY``. A ``GET`` section headed "List" or "Get all" is ``Paging.OFFSET`` but "List all token
associations", which answers one object. The administrator sections have no record of their own (DL-005).

Issue #63 (``design.md`` D1, D4, D5, D8) records the keys #42 left pending. Each other endpoint of a section with
several is a record with the section's ID, declared after its base record in the order the section's endpoint line
lists them, with the base record's ``Param``s less any naming a path parameter of its own path, and its ``body`` and
``paging``; ``call --endpoint 'METHOD path'`` names it, and a call naming none sends the base record. "Retrieve the
token information" keeps its path ``https://HOST/oauth/token/info``, which ``registry.base_of`` reads as the configured
host's root, outside ``/api/v4``. Each name the ``- Request headers:`` line of "Set status of an external control"
marks ``(required)`` is a required ``Location.HEADER`` ``Param``, spelled as the line spells it, after the table's
rows; ``call --header NAME=VALUE`` gives it. ``PENDING`` is empty: every key of the family has its record.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "software-supply-chain-security"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Users API: As a regular user" (`GET /user`): the section has no attribute table, so the record has no Param.
    RestOperation(
        operation_id="software-supply-chain-security#as-a-regular-user-1",
        method="GET",
        path="/user",
    ),
    # "Users API: As a regular user" (`GET /users`): a list endpoint, offset-paged (conventions.md "Pagination": the
    # users endpoint also offers keyset, and offset pagination reaches 50,000 records).
    RestOperation(
        operation_id="software-supply-chain-security#as-a-regular-user",
        method="GET",
        path="/users",
        params=(
            Param(name="username", location=Location.QUERY),
            Param(name="public_email", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="active", location=Location.QUERY),
            Param(name="external", location=Location.QUERY),
            Param(name="blocked", location=Location.QUERY),
            Param(name="humans", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="exclude_active", location=Location.QUERY),
            Param(name="exclude_external", location=Location.QUERY),
            Param(name="exclude_humans", location=Location.QUERY),
            Param(name="exclude_internal", location=Location.QUERY),
            Param(name="without_project_bots", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Application appearance API: Retrieve application appearance".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-application-appearance",
        method="GET",
        path="/application/appearance",
    ),
    # "Application appearance API: Update application appearance"; of the key's two rows the record is this section
    # (AC-1); the four `form` rows noted "file upload" are FILE, so a call that gives one is sent multipart.
    RestOperation(
        operation_id="software-supply-chain-security#update-application-appearance",
        method="PUT",
        path="/application/appearance",
        params=(
            Param(name="title", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="pwa_name", location=Location.BODY),
            Param(name="pwa_short_name", location=Location.BODY),
            Param(name="pwa_description", location=Location.BODY),
            Param(name="pwa_icon", location=Location.BODY, kind=Kind.FILE),
            Param(name="logo", location=Location.BODY, kind=Kind.FILE),
            Param(name="header_logo", location=Location.BODY, kind=Kind.FILE),
            Param(name="favicon", location=Location.BODY, kind=Kind.FILE),
            Param(name="member_guidelines", location=Location.BODY),
            Param(name="new_project_guidelines", location=Location.BODY),
            Param(name="profile_image_guidelines", location=Location.BODY),
            Param(name="header_message", location=Location.BODY),
            Param(name="footer_message", location=Location.BODY),
            Param(name="message_background_color", location=Location.BODY),
            Param(name="message_font_color", location=Location.BODY),
            Param(name="email_header_and_footer_enabled", location=Location.BODY),
            Param(name="site_name", location=Location.BODY),
        ),
    ),
    # "Application settings API: Retrieve details on current application settings".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-details-on-current-application-settings",
        method="GET",
        path="/application/settings",
    ),
    # "Application settings API: Update application settings"; the section has no attribute table, so the record has no
    # Param.
    RestOperation(
        operation_id="software-supply-chain-security#update-application-settings",
        method="PUT",
        path="/application/settings",
    ),
    # "Application statistics API: Retrieve application statistics".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-application-statistics",
        method="GET",
        path="/application/statistics",
    ),
    # "Applications API: Create an application".
    RestOperation(
        operation_id="software-supply-chain-security#create-an-application",
        method="POST",
        path="/applications",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="redirect_uri", location=Location.BODY, required=True),
            Param(name="scopes", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
            Param(name="granular_scopes", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Applications API: List all applications".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-applications",
        method="GET",
        path="/applications",
        paging=Paging.OFFSET,
    ),
    # "Applications API: Delete an application".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-application",
        method="DELETE",
        path="/applications/:id",
    ),
    # "Applications API: Renew an application secret".
    RestOperation(
        operation_id="software-supply-chain-security#renew-an-application-secret",
        method="POST",
        path="/applications/:id/renew-secret",
    ),
    # "Audit events API: List all instance audit events".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-instance-audit-events",
        method="GET",
        path="/audit_events",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="entity_type", location=Location.QUERY),
            Param(name="entity_id", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Audit events API: Retrieve an instance audit event".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-an-instance-audit-event",
        method="GET",
        path="/audit_events/:id",
    ),
    # "Audit events API: List all group audit events".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-group-audit-events",
        method="GET",
        path="/groups/:id/audit_events",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Audit events API: Retrieve a group audit event".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-group-audit-event",
        method="GET",
        path="/groups/:id/audit_events/:audit_event_id",
    ),
    # "Audit events API: List all project audit events".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-project-audit-events",
        method="GET",
        path="/projects/:id/audit_events",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Audit events API: Retrieve a project audit event".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-project-audit-event",
        method="GET",
        path="/projects/:id/audit_events/:audit_event_id",
    ),
    # "Avatar API: Retrieve user account avatar".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-user-account-avatar",
        method="GET",
        path="/avatar",
        params=(
            Param(name="email", location=Location.QUERY, required=True),
            Param(name="size", location=Location.QUERY),
        ),
    ),
    # "Custom Attributes API: List all custom attributes"; of the section's endpoints the base record is its
    # `/projects/:id/` endpoint, its `/users/:id/` and `/groups/:id/` endpoints the records after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#list-all-custom-attributes",
        method="GET",
        path="/projects/:id/custom_attributes",
        paging=Paging.OFFSET,
    ),
    RestOperation(
        operation_id="software-supply-chain-security#list-all-custom-attributes",
        method="GET",
        path="/users/:id/custom_attributes",
        paging=Paging.OFFSET,
    ),
    RestOperation(
        operation_id="software-supply-chain-security#list-all-custom-attributes",
        method="GET",
        path="/groups/:id/custom_attributes",
        paging=Paging.OFFSET,
    ),
    # "Custom Attributes API: Retrieve a custom attribute"; of the section's endpoints the base record is its
    # `/projects/:id/` endpoint, its `/users/:id/` and `/groups/:id/` endpoints the records after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-custom-attribute",
        method="GET",
        path="/projects/:id/custom_attributes/:key",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-custom-attribute",
        method="GET",
        path="/users/:id/custom_attributes/:key",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-custom-attribute",
        method="GET",
        path="/groups/:id/custom_attributes/:key",
    ),
    # "Custom Attributes API: Update a custom attribute"; of the section's endpoints the base record is its
    # `/projects/:id/` endpoint, its `/users/:id/` and `/groups/:id/` endpoints the records after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#update-a-custom-attribute",
        method="PUT",
        path="/projects/:id/custom_attributes/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    RestOperation(
        operation_id="software-supply-chain-security#update-a-custom-attribute",
        method="PUT",
        path="/users/:id/custom_attributes/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    RestOperation(
        operation_id="software-supply-chain-security#update-a-custom-attribute",
        method="PUT",
        path="/groups/:id/custom_attributes/:key",
        params=(Param(name="value", location=Location.BODY, required=True),),
    ),
    # "Custom Attributes API: Delete custom attribute"; of the section's endpoints the base record is its
    # `/projects/:id/` endpoint, its `/users/:id/` and `/groups/:id/` endpoints the records after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#delete-custom-attribute",
        method="DELETE",
        path="/projects/:id/custom_attributes/:key",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#delete-custom-attribute",
        method="DELETE",
        path="/users/:id/custom_attributes/:key",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#delete-custom-attribute",
        method="DELETE",
        path="/groups/:id/custom_attributes/:key",
    ),
    # "External controls API: Set status of an external control"; each name its `- Request headers:` line marks
    # `(required)` is a required HEADER Param, after the table's `status` row (#63 D5, D8).
    RestOperation(
        operation_id="software-supply-chain-security#set-status-of-an-external-control",
        method="PATCH",
        path="/projects/:id/compliance_external_controls/:external_control_id/status",
        params=(
            Param(name="status", location=Location.BODY, required=True),
            Param(name="X-Gitlab-Timestamp", location=Location.HEADER, required=True),
            Param(name="X-Gitlab-Nonce", location=Location.HEADER, required=True),
            Param(name="X-Gitlab-Hmac-Sha256", location=Location.HEADER, required=True),
        ),
    ),
    # "Google Cloud integration API: Workload identity federation creation script".
    RestOperation(
        operation_id="software-supply-chain-security#workload-identity-federation-creation-script",
        method="GET",
        path="/projects/:id/google_cloud/setup/wlif.sh",
        params=(
            Param(name="google_cloud_project_id", location=Location.QUERY, required=True),
            Param(name="google_cloud_workload_identity_pool_id", location=Location.QUERY),
            Param(name="google_cloud_workload_identity_pool_display_name", location=Location.QUERY),
            Param(name="google_cloud_workload_identity_pool_provider_id", location=Location.QUERY),
            Param(name="google_cloud_workload_identity_pool_provider_display_name", location=Location.QUERY),
        ),
    ),
    # "Google Cloud integration API: Script to set up a Google Cloud integration".
    RestOperation(
        operation_id="software-supply-chain-security#script-to-set-up-a-google-cloud-integration",
        method="GET",
        path="/projects/:id/google_cloud/setup/integrations.sh",
        params=(
            Param(name="enable_google_cloud_artifact_registry", location=Location.QUERY, required=True),
            Param(name="google_cloud_artifact_registry_project_id", location=Location.QUERY, required=True),
        ),
    ),
    # "Google Cloud integration API: Script to configure a Google Cloud project for runner provisioning".
    RestOperation(
        operation_id=(
            "software-supply-chain-security#script-to-configure-a-google-cloud-project-for-runner-provisioning"
        ),
        method="GET",
        path="/projects/:id/google_cloud/setup/runner_deployment_project.sh",
        params=(Param(name="google_cloud_project_id", location=Location.QUERY, required=True),),
    ),
    # "Group access tokens API: List all group access tokens".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-group-access-tokens",
        method="GET",
        path="/groups/:id/access_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group access tokens API: Retrieve details on a group access token".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-details-on-a-group-access-token",
        method="GET",
        path="/groups/:id/access_tokens/:token_id",
    ),
    # "Group access tokens API: Create a group access token".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-group-access-token",
        method="POST",
        path="/groups/:id/access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="access_level", location=Location.BODY),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Group access tokens API: Rotate a group access token".
    RestOperation(
        operation_id="software-supply-chain-security#rotate-a-group-access-token",
        method="POST",
        path="/groups/:id/access_tokens/:token_id/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "Group access tokens API: Revoke a group access token".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-group-access-token",
        method="DELETE",
        path="/groups/:id/access_tokens/:token_id",
    ),
    # "Group and project access requests API: List all access requests for a group or project"; of the section's
    # endpoints the base record is its `/projects/:id/` endpoint, its `/groups/:id/` endpoint the record after it (#63
    # D1).
    RestOperation(
        operation_id="software-supply-chain-security#list-all-access-requests-for-a-group-or-project",
        method="GET",
        path="/projects/:id/access_requests",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    RestOperation(
        operation_id="software-supply-chain-security#list-all-access-requests-for-a-group-or-project",
        method="GET",
        path="/groups/:id/access_requests",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group and project access requests API: Request access to a group or project"; of the section's endpoints the
    # base record is its `/projects/:id/` endpoint, its `/groups/:id/` endpoint the record after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#request-access-to-a-group-or-project",
        method="POST",
        path="/projects/:id/access_requests",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#request-access-to-a-group-or-project",
        method="POST",
        path="/groups/:id/access_requests",
    ),
    # "Group and project access requests API: Approve an access request"; of the section's endpoints the base record is
    # its `/projects/:id/` endpoint, its `/groups/:id/` endpoint the record after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#approve-an-access-request",
        method="PUT",
        path="/projects/:id/access_requests/:user_id/approve",
        params=(Param(name="access_level", location=Location.BODY),),
    ),
    RestOperation(
        operation_id="software-supply-chain-security#approve-an-access-request",
        method="PUT",
        path="/groups/:id/access_requests/:user_id/approve",
        params=(Param(name="access_level", location=Location.BODY),),
    ),
    # "Group and project access requests API: Deny an access request"; of the section's endpoints the base record is
    # its `/projects/:id/` endpoint, its `/groups/:id/` endpoint the record after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#deny-an-access-request",
        method="DELETE",
        path="/projects/:id/access_requests/:user_id",
    ),
    RestOperation(
        operation_id="software-supply-chain-security#deny-an-access-request",
        method="DELETE",
        path="/groups/:id/access_requests/:user_id",
    ),
    # "Group enterprise users API: List all enterprise users".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-enterprise-users",
        method="GET",
        path="/groups/:id/enterprise_users",
        params=(
            Param(name="username", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="active", location=Location.QUERY),
            Param(name="blocked", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="two_factor", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group enterprise users API: Retrieve an enterprise user".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-an-enterprise-user",
        method="GET",
        path="/groups/:id/enterprise_users/:user_id",
    ),
    # "Group enterprise users API: Update an enterprise user".
    RestOperation(
        operation_id="software-supply-chain-security#update-an-enterprise-user",
        method="PATCH",
        path="/groups/:id/enterprise_users/:user_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="email", location=Location.BODY),
            Param(name="projects_limit", location=Location.BODY),
            Param(name="can_create_group", location=Location.BODY),
        ),
    ),
    # "Group enterprise users API: Delete an enterprise user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-enterprise-user",
        method="DELETE",
        path="/groups/:id/enterprise_users/:user_id",
        params=(Param(name="hard_delete", location=Location.QUERY),),
    ),
    # "Group enterprise users API: Disable two-factor authentication for an enterprise user".
    RestOperation(
        operation_id="software-supply-chain-security#disable-two-factor-authentication-for-an-enterprise-user",
        method="PATCH",
        path="/groups/:id/enterprise_users/:user_id/disable_two_factor",
    ),
    # "Member roles API: Get all instance member roles".
    RestOperation(
        operation_id="software-supply-chain-security#get-all-instance-member-roles",
        method="GET",
        path="/member_roles",
        paging=Paging.OFFSET,
    ),
    # "Member roles API: Create an instance member role".
    RestOperation(
        operation_id="software-supply-chain-security#create-an-instance-member-role",
        method="POST",
        path="/member_roles",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="base_access_level", location=Location.BODY, required=True),
            Param(name="admin_cicd_variables", location=Location.BODY),
            Param(name="admin_compliance_framework", location=Location.BODY),
            Param(name="admin_group_member", location=Location.BODY),
            Param(name="admin_merge_request", location=Location.BODY),
            Param(name="admin_push_rules", location=Location.BODY),
            Param(name="admin_terraform_state", location=Location.BODY),
            Param(name="admin_vulnerability", location=Location.BODY),
            Param(name="admin_web_hook", location=Location.BODY),
            Param(name="archive_project", location=Location.BODY),
            Param(name="archive_subgroup", location=Location.BODY),
            Param(name="manage_deploy_tokens", location=Location.BODY),
            Param(name="manage_group_access_tokens", location=Location.BODY),
            Param(name="manage_merge_request_settings", location=Location.BODY),
            Param(name="manage_project_access_tokens", location=Location.BODY),
            Param(name="manage_security_policy_link", location=Location.BODY),
            Param(name="read_code", location=Location.BODY),
            Param(name="read_runners", location=Location.BODY),
            Param(name="read_dependency", location=Location.BODY),
            Param(name="read_vulnerability", location=Location.BODY),
            Param(name="remove_group", location=Location.BODY),
            Param(name="remove_project", location=Location.BODY),
        ),
    ),
    # "Member roles API: Delete an instance member role".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-instance-member-role",
        method="DELETE",
        path="/member_roles/:member_role_id",
    ),
    # "Member roles API: Get all group member roles".
    RestOperation(
        operation_id="software-supply-chain-security#get-all-group-member-roles",
        method="GET",
        path="/groups/:id/member_roles",
        paging=Paging.OFFSET,
    ),
    # "Member roles API: Add a member role to a group".
    RestOperation(
        operation_id="software-supply-chain-security#add-a-member-role-to-a-group",
        method="POST",
        path="/groups/:id/member_roles",
        params=(
            Param(name="admin_cicd_variables", location=Location.BODY),
            Param(name="admin_compliance_framework", location=Location.BODY),
            Param(name="admin_group_member", location=Location.BODY),
            Param(name="admin_merge_request", location=Location.BODY),
            Param(name="admin_push_rules", location=Location.BODY),
            Param(name="admin_terraform_state", location=Location.BODY),
            Param(name="admin_vulnerability", location=Location.BODY),
            Param(name="admin_web_hook", location=Location.BODY),
            Param(name="archive_project", location=Location.BODY),
            Param(name="archive_subgroup", location=Location.BODY),
            Param(name="manage_deploy_tokens", location=Location.BODY),
            Param(name="manage_group_access_tokens", location=Location.BODY),
            Param(name="manage_merge_request_settings", location=Location.BODY),
            Param(name="manage_project_access_tokens", location=Location.BODY),
            Param(name="manage_security_policy_link", location=Location.BODY),
            Param(name="read_code", location=Location.BODY),
            Param(name="read_runners", location=Location.BODY),
            Param(name="read_dependency", location=Location.BODY),
            Param(name="read_vulnerability", location=Location.BODY),
            Param(name="remove_group", location=Location.BODY),
            Param(name="remove_project", location=Location.BODY),
        ),
    ),
    # "Member roles API: Remove member role of a group".
    RestOperation(
        operation_id="software-supply-chain-security#remove-member-role-of-a-group",
        method="DELETE",
        path="/groups/:id/member_roles/:member_role_id",
    ),
    # "OAuth 2.0 identity provider API: Retrieve the token information"; its path starts `https://HOST`, so it is sent
    # on the configured host's root, outside `/api/v4` (#63 D4). The section has no attribute table, so no Param.
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-the-token-information",
        method="GET",
        path="https://HOST/oauth/token/info",
    ),
    # "Personal access tokens API: List all personal access tokens".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-personal-access-tokens",
        method="GET",
        path="/personal_access_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="user_id", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Personal access tokens API: Retrieve a personal access token".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-personal-access-token",
        method="GET",
        path="/personal_access_tokens/:id",
    ),
    # "Personal access tokens API: Rotate a personal access token".
    RestOperation(
        operation_id="software-supply-chain-security#rotate-a-personal-access-token",
        method="POST",
        path="/personal_access_tokens/:id/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "Personal access tokens API: Revoke a personal access token".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-personal-access-token",
        method="DELETE",
        path="/personal_access_tokens/:id",
    ),
    # "Personal access tokens API: List all token associations"; it answers one object, so the record is not paged.
    RestOperation(
        operation_id="software-supply-chain-security#list-all-token-associations",
        method="GET",
        path="/personal_access_tokens/self/associations",
        params=(
            Param(name="min_access_level", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
    ),
    # "Plan limits API: Retrieve current plan limits".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-current-plan-limits",
        method="GET",
        path="/application/plan_limits",
        params=(Param(name="plan_name", location=Location.QUERY),),
    ),
    # "Plan limits API: Update plan limits".
    RestOperation(
        operation_id="software-supply-chain-security#update-plan-limits",
        method="PUT",
        path="/application/plan_limits",
        params=(
            Param(name="plan_name", location=Location.BODY, required=True),
            Param(name="ci_instance_level_variables", location=Location.BODY),
            Param(name="ci_pipeline_size", location=Location.BODY),
            Param(name="ci_pipeline_variables_count", location=Location.BODY),
            Param(name="ci_variable_value_size", location=Location.BODY),
            Param(name="ci_variable_file_value_size", location=Location.BODY),
            Param(name="ci_active_jobs", location=Location.BODY),
            Param(name="ci_project_subscriptions", location=Location.BODY),
            Param(name="ci_pipeline_schedules", location=Location.BODY),
            Param(name="ci_needs_size_limit", location=Location.BODY),
            Param(name="ci_registered_group_runners", location=Location.BODY),
            Param(name="ci_registered_project_runners", location=Location.BODY),
            Param(name="dotenv_size", location=Location.BODY),
            Param(name="dotenv_variables", location=Location.BODY),
            Param(name="cargo_max_file_size", location=Location.BODY),
            Param(name="conan_max_file_size", location=Location.BODY),
            Param(name="enforcement_limit", location=Location.BODY),
            Param(name="generic_packages_max_file_size", location=Location.BODY),
            Param(name="helm_max_file_size", location=Location.BODY),
            Param(name="maven_max_file_size", location=Location.BODY),
            Param(name="notification_limit", location=Location.BODY),
            Param(name="npm_max_file_size", location=Location.BODY),
            Param(name="nuget_max_file_size", location=Location.BODY),
            Param(name="organization_hooks", location=Location.BODY),
            Param(name="integration_executions", location=Location.BODY),
            Param(name="integration_executions_datadog", location=Location.BODY),
            Param(name="max_pipelines_per_merge_train", location=Location.BODY),
            Param(name="pipeline_hierarchy_size", location=Location.BODY),
            Param(name="pypi_max_file_size", location=Location.BODY),
            Param(name="service_desk_outbound_emails_per_hour", location=Location.BODY),
            Param(name="service_desk_outbound_emails_per_day", location=Location.BODY),
            Param(name="terraform_module_max_file_size", location=Location.BODY),
            Param(name="storage_size_limit", location=Location.BODY),
            Param(name="web_hook_calls", location=Location.BODY),
            Param(name="web_hook_calls_low", location=Location.BODY),
            Param(name="web_hook_calls_mid", location=Location.BODY),
        ),
    ),
    # "Project access tokens API: List all project access tokens".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-project-access-tokens",
        method="GET",
        path="/projects/:id/access_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project access tokens API: Retrieve details on a project access token".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-details-on-a-project-access-token",
        method="GET",
        path="/projects/:id/access_tokens/:token_id",
    ),
    # "Project access tokens API: Create a project access token".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-project-access-token",
        method="POST",
        path="/projects/:id/access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="access_level", location=Location.BODY),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Project access tokens API: Rotate a project access token".
    RestOperation(
        operation_id="software-supply-chain-security#rotate-a-project-access-token",
        method="POST",
        path="/projects/:id/access_tokens/:token_id/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "Project access tokens API: Revoke a project access token".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-project-access-token",
        method="DELETE",
        path="/projects/:id/access_tokens/:token_id",
    ),
    # "SAML API: List all SAML identities for a group".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-saml-identities-for-a-group",
        method="GET",
        path="/groups/:id/saml/identities",
        paging=Paging.OFFSET,
    ),
    # "SAML API: Retrieve a single SAML identity".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-single-saml-identity",
        method="GET",
        path="/groups/:id/saml/:uid",
    ),
    # "SAML API: Update `extern_uid` field for a SAML identity".
    RestOperation(
        operation_id="software-supply-chain-security#update-extern_uid-field-for-a-saml-identity",
        method="PATCH",
        path="/groups/:id/saml/:uid",
    ),
    # "SAML API: Delete a single SAML identity".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-single-saml-identity",
        method="DELETE",
        path="/groups/:id/saml/:uid",
    ),
    # "SAML API: List all SAML group links".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-saml-group-links",
        method="GET",
        path="/groups/:id/saml_group_links",
        paging=Paging.OFFSET,
    ),
    # "SAML API: Retrieve a SAML group link".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-saml-group-link",
        method="GET",
        path="/groups/:id/saml_group_links/:saml_group_name",
        params=(Param(name="provider", location=Location.QUERY),),
    ),
    # "SAML API: Add a SAML group link".
    RestOperation(
        operation_id="software-supply-chain-security#add-a-saml-group-link",
        method="POST",
        path="/groups/:id/saml_group_links",
        params=(
            Param(name="saml_group_name", location=Location.BODY, required=True),
            Param(name="access_level", location=Location.BODY, required=True),
            Param(name="member_role_id", location=Location.BODY),
            Param(name="provider", location=Location.BODY),
        ),
    ),
    # "SAML API: Delete a SAML group link".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-saml-group-link",
        method="DELETE",
        path="/groups/:id/saml_group_links/:saml_group_name",
        params=(Param(name="provider", location=Location.QUERY),),
    ),
    # "Service accounts API: List all instance service accounts".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-instance-service-accounts",
        method="GET",
        path="/service_accounts",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Service accounts API: Create an instance service account".
    RestOperation(
        operation_id="software-supply-chain-security#create-an-instance-service-account",
        method="POST",
        path="/service_accounts",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
            Param(name="external", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Update an instance service account".
    RestOperation(
        operation_id="software-supply-chain-security#update-an-instance-service-account",
        method="PATCH",
        path="/service_accounts/:id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
            Param(name="external", location=Location.BODY),
        ),
    ),
    # "Service accounts API: List all group service accounts".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-group-service-accounts",
        method="GET",
        path="/groups/:id/service_accounts",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Service accounts API: Retrieve a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-group-service-account",
        method="GET",
        path="/groups/:id/service_accounts/:user_id",
    ),
    # "Service accounts API: Create a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-group-service-account",
        method="POST",
        path="/groups/:id/service_accounts",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Update a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#update-a-group-service-account",
        method="PATCH",
        path="/groups/:id/service_accounts/:user_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Delete a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-group-service-account",
        method="DELETE",
        path="/groups/:id/service_accounts/:user_id",
        params=(Param(name="hard_delete", location=Location.QUERY),),
    ),
    # "Service accounts API: List all personal access tokens for a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-personal-access-tokens-for-a-group-service-account",
        method="GET",
        path="/groups/:id/service_accounts/:user_id/personal_access_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Service accounts API: Create a personal access token for a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-personal-access-token-for-a-group-service-account",
        method="POST",
        path="/groups/:id/service_accounts/:user_id/personal_access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Revoke a personal access token for a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-personal-access-token-for-a-group-service-account",
        method="DELETE",
        path="/groups/:id/service_accounts/:user_id/personal_access_tokens/:token_id",
    ),
    # "Service accounts API: Rotate a personal access token for a group service account".
    RestOperation(
        operation_id="software-supply-chain-security#rotate-a-personal-access-token-for-a-group-service-account",
        method="POST",
        path="/groups/:id/service_accounts/:user_id/personal_access_tokens/:token_id/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "Service accounts API: List all project service accounts".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-project-service-accounts",
        method="GET",
        path="/projects/:id/service_accounts",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Service accounts API: Retrieve a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-project-service-account",
        method="GET",
        path="/projects/:id/service_accounts/:user_id",
    ),
    # "Service accounts API: Create a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-project-service-account",
        method="POST",
        path="/projects/:id/service_accounts",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Update a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#update-a-project-service-account",
        method="PATCH",
        path="/projects/:id/service_accounts/:user_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="email", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Delete a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-project-service-account",
        method="DELETE",
        path="/projects/:id/service_accounts/:user_id",
        params=(Param(name="hard_delete", location=Location.QUERY),),
    ),
    # "Service accounts API: List all personal access tokens for a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-personal-access-tokens-for-a-project-service-account",
        method="GET",
        path="/projects/:id/service_accounts/:user_id/personal_access_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Service accounts API: Create a personal access token for a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-personal-access-token-for-a-project-service-account",
        method="POST",
        path="/projects/:id/service_accounts/:user_id/personal_access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Service accounts API: Revoke a personal access token for a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-personal-access-token-for-a-project-service-account",
        method="DELETE",
        path="/projects/:id/service_accounts/:user_id/personal_access_tokens/:token_id",
    ),
    # "Service accounts API: Rotate a personal access token for a project service account".
    RestOperation(
        operation_id="software-supply-chain-security#rotate-a-personal-access-token-for-a-project-service-account",
        method="POST",
        path="/projects/:id/service_accounts/:user_id/personal_access_tokens/:token_id/rotate",
        params=(Param(name="expires_at", location=Location.BODY),),
    ),
    # "Token information API: Retrieve token information".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-token-information",
        method="POST",
        path="/admin/token",
        params=(Param(name="token", location=Location.BODY, required=True),),
    ),
    # "Token information API: Revoke a token".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-token",
        method="DELETE",
        path="/admin/token",
        params=(Param(name="token", location=Location.QUERY, required=True),),
    ),
    # "User Applications API: Create an application".
    RestOperation(
        operation_id="software-supply-chain-security#create-an-application-1",
        method="POST",
        path="/user/applications",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="redirect_uri", location=Location.BODY, required=True),
            Param(name="scopes", location=Location.BODY, required=True),
            Param(name="confidential", location=Location.BODY),
        ),
    ),
    # "User Applications API: List all applications".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-applications-1",
        method="GET",
        path="/user/applications",
        paging=Paging.OFFSET,
    ),
    # "User Applications API: Retrieve a specific application".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-specific-application",
        method="GET",
        path="/user/applications/:id",
    ),
    # "User Applications API: Update an application".
    RestOperation(
        operation_id="software-supply-chain-security#update-an-application",
        method="PUT",
        path="/user/applications/:id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="scopes", location=Location.BODY),
        ),
    ),
    # "User Applications API: Delete an application".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-application-1",
        method="DELETE",
        path="/user/applications/:id",
    ),
    # "User email addresses API: List all email addresses".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-email-addresses",
        method="GET",
        path="/user/emails",
        paging=Paging.OFFSET,
    ),
    # "User email addresses API: List all email addresses for a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-email-addresses-for-a-user",
        method="GET",
        path="/users/:id/emails",
        paging=Paging.OFFSET,
    ),
    # "User email addresses API: Retrieve details on an email address".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-details-on-an-email-address",
        method="GET",
        path="/user/emails/:email_id",
    ),
    # "User email addresses API: Add an email address".
    RestOperation(
        operation_id="software-supply-chain-security#add-an-email-address",
        method="POST",
        path="/user/emails",
        params=(Param(name="email", location=Location.BODY, required=True),),
    ),
    # "User email addresses API: Add an email address for a user".
    RestOperation(
        operation_id="software-supply-chain-security#add-an-email-address-for-a-user",
        method="POST",
        path="/users/:id/emails",
        params=(
            Param(name="email", location=Location.BODY, required=True),
            Param(name="skip_confirmation", location=Location.BODY),
        ),
    ),
    # "User email addresses API: Delete an email address".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-email-address",
        method="DELETE",
        path="/user/emails/:email_id",
    ),
    # "User email addresses API: Delete an email address for a user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-email-address-for-a-user",
        method="DELETE",
        path="/users/:id/emails/:email_id",
    ),
    # "User follow and unfollow API: Follow a user".
    RestOperation(
        operation_id="software-supply-chain-security#follow-a-user",
        method="POST",
        path="/users/:id/follow",
    ),
    # "User follow and unfollow API: Unfollow a user".
    RestOperation(
        operation_id="software-supply-chain-security#unfollow-a-user",
        method="POST",
        path="/users/:id/unfollow",
    ),
    # "User follow and unfollow API: List all accounts that follow a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-accounts-that-follow-a-user",
        method="GET",
        path="/users/:id/followers",
        paging=Paging.OFFSET,
    ),
    # "User follow and unfollow API: List all accounts followed by a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-accounts-followed-by-a-user",
        method="GET",
        path="/users/:id/following",
        paging=Paging.OFFSET,
    ),
    # "User moderation API: Approve access to a user".
    RestOperation(
        operation_id="software-supply-chain-security#approve-access-to-a-user",
        method="POST",
        path="/users/:id/approve",
    ),
    # "User moderation API: Reject access to a user".
    RestOperation(
        operation_id="software-supply-chain-security#reject-access-to-a-user",
        method="POST",
        path="/users/:id/reject",
    ),
    # "User moderation API: Deactivate a user".
    RestOperation(
        operation_id="software-supply-chain-security#deactivate-a-user",
        method="POST",
        path="/users/:id/deactivate",
    ),
    # "User moderation API: Reactivate a user".
    RestOperation(
        operation_id="software-supply-chain-security#reactivate-a-user",
        method="POST",
        path="/users/:id/activate",
    ),
    # "User moderation API: Block access to a user".
    RestOperation(
        operation_id="software-supply-chain-security#block-access-to-a-user",
        method="POST",
        path="/users/:id/block",
    ),
    # "User moderation API: Unblock access to a user".
    RestOperation(
        operation_id="software-supply-chain-security#unblock-access-to-a-user",
        method="POST",
        path="/users/:id/unblock",
    ),
    # "User moderation API: Ban a user".
    RestOperation(
        operation_id="software-supply-chain-security#ban-a-user",
        method="POST",
        path="/users/:id/ban",
    ),
    # "User moderation API: Unban a user".
    RestOperation(
        operation_id="software-supply-chain-security#unban-a-user",
        method="POST",
        path="/users/:id/unban",
    ),
    # "User SSH and GPG keys API: List all SSH keys".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-ssh-keys",
        method="GET",
        path="/user/keys",
        paging=Paging.OFFSET,
    ),
    # "User SSH and GPG keys API: List all SSH keys for a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-ssh-keys-for-a-user",
        method="GET",
        path="/users/:id_or_username/keys",
        paging=Paging.OFFSET,
    ),
    # "User SSH and GPG keys API: Retrieve an SSH key".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-an-ssh-key",
        method="GET",
        path="/user/keys/:key_id",
    ),
    # "User SSH and GPG keys API: Retrieve an SSH key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-an-ssh-key-for-a-user",
        method="GET",
        path="/users/:id/keys/:key_id",
    ),
    # "User SSH and GPG keys API: Add an SSH key".
    RestOperation(
        operation_id="software-supply-chain-security#add-an-ssh-key",
        method="POST",
        path="/user/keys",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="key", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="usage_type", location=Location.BODY),
        ),
    ),
    # "User SSH and GPG keys API: Add an SSH key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#add-an-ssh-key-for-a-user",
        method="POST",
        path="/users/:id/keys",
        params=(
            Param(name="title", location=Location.BODY, required=True),
            Param(name="key", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="usage_type", location=Location.BODY),
        ),
    ),
    # "User SSH and GPG keys API: Delete an SSH key".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-ssh-key",
        method="DELETE",
        path="/user/keys/:key_id",
    ),
    # "User SSH and GPG keys API: Delete an SSH key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-an-ssh-key-for-a-user",
        method="DELETE",
        path="/users/:id/keys/:key_id",
    ),
    # "User SSH and GPG keys API: List all GPG keys".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-gpg-keys",
        method="GET",
        path="/user/gpg_keys",
        paging=Paging.OFFSET,
    ),
    # "User SSH and GPG keys API: List all GPG keys for a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-gpg-keys-for-a-user",
        method="GET",
        path="/users/:id/gpg_keys",
        paging=Paging.OFFSET,
    ),
    # "User SSH and GPG keys API: Retrieve a GPG key".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-gpg-key",
        method="GET",
        path="/user/gpg_keys/:key_id",
    ),
    # "User SSH and GPG keys API: Retrieve a GPG key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-gpg-key-for-a-user",
        method="GET",
        path="/users/:id/gpg_keys/:key_id",
    ),
    # "User SSH and GPG keys API: Add a GPG key".
    RestOperation(
        operation_id="software-supply-chain-security#add-a-gpg-key",
        method="POST",
        path="/user/gpg_keys",
        params=(Param(name="key", location=Location.BODY, required=True),),
    ),
    # "User SSH and GPG keys API: Add a GPG key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#add-a-gpg-key-for-a-user",
        method="POST",
        path="/users/:id/gpg_keys",
        params=(Param(name="key", location=Location.BODY, required=True),),
    ),
    # "User SSH and GPG keys API: Delete a GPG key".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-gpg-key",
        method="DELETE",
        path="/user/gpg_keys/:key_id",
    ),
    # "User SSH and GPG keys API: Delete a GPG key for a user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-gpg-key-for-a-user",
        method="DELETE",
        path="/users/:id/gpg_keys/:key_id",
    ),
    # "User tokens API: Create a personal access token for a user".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-personal-access-token-for-a-user",
        method="POST",
        path="/users/:user_id/personal_access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="expires_at", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="granular_scopes", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "User tokens API: Create a personal access token".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-personal-access-token",
        method="POST",
        path="/user/personal_access_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="expires_at", location=Location.BODY),
            Param(name="granular_scopes", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "User tokens API: List all impersonation tokens for a user".
    RestOperation(
        operation_id="software-supply-chain-security#list-all-impersonation-tokens-for-a-user",
        method="GET",
        path="/users/:user_id/impersonation_tokens",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="expires_after", location=Location.QUERY),
            Param(name="expires_before", location=Location.QUERY),
            Param(name="last_used_after", location=Location.QUERY),
            Param(name="last_used_before", location=Location.QUERY),
            Param(name="revoked", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "User tokens API: Retrieve an impersonation token for a user".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-an-impersonation-token-for-a-user",
        method="GET",
        path="/users/:user_id/impersonation_tokens/:impersonation_token_id",
    ),
    # "User tokens API: Create an impersonation token".
    RestOperation(
        operation_id="software-supply-chain-security#create-an-impersonation-token",
        method="POST",
        path="/users/:user_id/impersonation_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="expires_at", location=Location.BODY, required=True),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="granular_scopes", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "User tokens API: Revoke an impersonation token".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-an-impersonation-token",
        method="DELETE",
        path="/users/:user_id/impersonation_tokens/:impersonation_token_id",
    ),
    # "Users API: Retrieve a single user as a regular user"; of the key's two rows the record is this section, not "As
    # an administrator" (AC-1).
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-a-single-user-as-a-regular-user",
        method="GET",
        path="/users/:id",
    ),
    # "Users API: Create a user"; `avatar` is a FILE (a `WorkhorseFile`, conventions.md "Avatars").
    RestOperation(
        operation_id="software-supply-chain-security#create-a-user",
        method="POST",
        path="/users",
        params=(
            Param(name="username", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="email", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY),
            Param(name="admin", location=Location.BODY),
            Param(name="auditor", location=Location.BODY),
            Param(name="avatar", location=Location.BODY, kind=Kind.FILE),
            Param(name="bio", location=Location.BODY),
            Param(name="can_create_group", location=Location.BODY),
            Param(name="color_scheme_id", location=Location.BODY),
            Param(name="commit_email", location=Location.BODY),
            Param(name="extern_uid", location=Location.BODY),
            Param(name="external", location=Location.BODY),
            Param(name="extra_shared_runners_minutes_limit", location=Location.BODY),
            Param(name="force_random_password", location=Location.BODY),
            Param(name="group_id_for_saml", location=Location.BODY),
            Param(name="linkedin", location=Location.BODY),
            Param(name="location", location=Location.BODY),
            Param(name="note", location=Location.BODY),
            Param(name="organization", location=Location.BODY),
            Param(name="private_profile", location=Location.BODY),
            Param(name="projects_limit", location=Location.BODY),
            Param(name="pronouns", location=Location.BODY),
            Param(name="provider", location=Location.BODY),
            Param(name="public_email", location=Location.BODY),
            Param(name="reset_password", location=Location.BODY),
            Param(name="shared_runners_minutes_limit", location=Location.BODY),
            Param(name="skip_confirmation", location=Location.BODY),
            Param(name="theme_id", location=Location.BODY),
            Param(name="twitter", location=Location.BODY),
            Param(name="discord", location=Location.BODY),
            Param(name="github", location=Location.BODY),
            Param(name="view_diffs_file_by_file", location=Location.BODY),
            Param(name="website_url", location=Location.BODY),
        ),
    ),
    # "Users API: Modify a user"; `avatar` is a FILE (a `WorkhorseFile`, conventions.md "Avatars").
    RestOperation(
        operation_id="software-supply-chain-security#modify-a-user",
        method="PUT",
        path="/users/:id",
        params=(
            Param(name="admin", location=Location.BODY),
            Param(name="auditor", location=Location.BODY),
            Param(name="avatar", location=Location.BODY, kind=Kind.FILE),
            Param(name="bio", location=Location.BODY),
            Param(name="can_create_group", location=Location.BODY),
            Param(name="color_scheme_id", location=Location.BODY),
            Param(name="commit_email", location=Location.BODY),
            Param(name="email", location=Location.BODY),
            Param(name="extern_uid", location=Location.BODY),
            Param(name="external", location=Location.BODY),
            Param(name="extra_shared_runners_minutes_limit", location=Location.BODY),
            Param(name="group_id_for_saml", location=Location.BODY),
            Param(name="linkedin", location=Location.BODY),
            Param(name="location", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="note", location=Location.BODY),
            Param(name="organization", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="private_profile", location=Location.BODY),
            Param(name="projects_limit", location=Location.BODY),
            Param(name="pronouns", location=Location.BODY),
            Param(name="provider", location=Location.BODY),
            Param(name="public_email", location=Location.BODY),
            Param(name="shared_runners_minutes_limit", location=Location.BODY),
            Param(name="skip_reconfirmation", location=Location.BODY),
            Param(name="theme_id", location=Location.BODY),
            Param(name="twitter", location=Location.BODY),
            Param(name="discord", location=Location.BODY),
            Param(name="github", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="view_diffs_file_by_file", location=Location.BODY),
            Param(name="website_url", location=Location.BODY),
        ),
    ),
    # "Users API: Delete a user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-a-user",
        method="DELETE",
        path="/users/:id",
        params=(Param(name="hard_delete", location=Location.QUERY),),
    ),
    # "Users API: Retrieve your user status".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-your-user-status",
        method="GET",
        path="/user/status",
    ),
    # "Users API: Retrieve the status of a user".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-the-status-of-a-user",
        method="GET",
        path="/users/:id_or_username/status",
    ),
    # "Users API: Set your user status"; of the section's endpoints the base record is its first, `PUT /user/status`,
    # and `PATCH /user/status` the record after it (#63 D1).
    RestOperation(
        operation_id="software-supply-chain-security#set-your-user-status",
        method="PUT",
        path="/user/status",
        params=(
            Param(name="emoji", location=Location.BODY),
            Param(name="message", location=Location.BODY),
            Param(name="availability", location=Location.BODY),
            Param(name="clear_status_after", location=Location.BODY),
        ),
    ),
    RestOperation(
        operation_id="software-supply-chain-security#set-your-user-status",
        method="PATCH",
        path="/user/status",
        params=(
            Param(name="emoji", location=Location.BODY),
            Param(name="message", location=Location.BODY),
            Param(name="availability", location=Location.BODY),
            Param(name="clear_status_after", location=Location.BODY),
        ),
    ),
    # "Users API: Retrieve your user preferences".
    RestOperation(
        operation_id="software-supply-chain-security#retrieve-your-user-preferences",
        method="GET",
        path="/user/preferences",
    ),
    # "Users API: Update your user preferences".
    RestOperation(
        operation_id="software-supply-chain-security#update-your-user-preferences",
        method="PUT",
        path="/user/preferences",
        params=(
            Param(name="view_diffs_file_by_file", location=Location.BODY, required=True),
            Param(name="show_whitespace_in_diffs", location=Location.BODY, required=True),
            Param(name="pass_user_identities_to_ci_jwt", location=Location.BODY, required=True),
            Param(name="emoji_skin_tone", location=Location.BODY),
        ),
    ),
    # "Users API: Upload an avatar for yourself"; `avatar` is a FILE (a `WorkhorseFile`, conventions.md "Avatars").
    RestOperation(
        operation_id="software-supply-chain-security#upload-an-avatar-for-yourself",
        method="PUT",
        path="/user/avatar",
        params=(Param(name="avatar", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "Users API: Retrieve a count of your assigned issues, merge requests, and reviews".
    RestOperation(
        operation_id=(
            "software-supply-chain-security#retrieve-a-count-of-your-assigned-issues-merge-requests-and-reviews"
        ),
        method="GET",
        path="/user_counts",
    ),
    # "Users API: Retrieve a count of a user's projects, groups, issues, and merge requests".
    RestOperation(
        operation_id=(
            "software-supply-chain-security#retrieve-a-count-of-a-users-projects-groups-issues-and-merge-requests"
        ),
        method="GET",
        path="/users/:id/associations_count",
    ),
    # "Users API: List a user's activity".
    RestOperation(
        operation_id="software-supply-chain-security#list-a-users-activity",
        method="GET",
        path="/user/activities",
        params=(Param(name="from", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Users API: List projects and groups that a user is a member of".
    RestOperation(
        operation_id="software-supply-chain-security#list-projects-and-groups-that-a-user-is-a-member-of",
        method="GET",
        path="/users/:id/memberships",
        params=(Param(name="type", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Users API: Disable two-factor authentication for a user".
    RestOperation(
        operation_id="software-supply-chain-security#disable-two-factor-authentication-for-a-user",
        method="PATCH",
        path="/users/:id/disable_two_factor",
    ),
    # "Users API: Create a runner linked to a user".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-runner-linked-to-a-user",
        method="POST",
        path="/user/runners",
        params=(
            Param(name="runner_type", location=Location.BODY, required=True),
            Param(name="group_id", location=Location.BODY),
            Param(name="project_id", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="paused", location=Location.BODY),
            Param(name="locked", location=Location.BODY),
            Param(name="run_untagged", location=Location.BODY),
            Param(name="tag_list", location=Location.BODY),
            Param(name="access_level", location=Location.BODY),
            Param(name="maximum_timeout", location=Location.BODY),
            Param(name="maintenance_note", location=Location.BODY),
            Param(name="token_expires_at", location=Location.BODY),
            Param(name="token_rotation_deadline", location=Location.BODY),
        ),
    ),
    # "Users API: Delete authentication identity from a user".
    RestOperation(
        operation_id="software-supply-chain-security#delete-authentication-identity-from-a-user",
        method="DELETE",
        path="/users/:id/identities/:provider",
    ),
    # "Users API: Create a Support PIN".
    RestOperation(
        operation_id="software-supply-chain-security#create-a-support-pin",
        method="POST",
        path="/user/support_pin",
    ),
    # "Users API: Get details on a Support PIN".
    RestOperation(
        operation_id="software-supply-chain-security#get-details-on-a-support-pin",
        method="GET",
        path="/user/support_pin",
    ),
    # "Users API: Get a Support PIN for a user".
    RestOperation(
        operation_id="software-supply-chain-security#get-a-support-pin-for-a-user",
        method="GET",
        path="/users/:id/support_pin",
    ),
    # "Users API: Revoke a Support PIN for a user".
    RestOperation(
        operation_id="software-supply-chain-security#revoke-a-support-pin-for-a-user",
        method="POST",
        path="/users/:id/support_pin/revoke",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
