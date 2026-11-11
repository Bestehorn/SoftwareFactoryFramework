"""The ``no-stage-assigned`` endpoint family of the GitLab wrapper: the group and project integrations APIs.

Each record is transcribed from its section of ``docs/api-reference/gitlab/rest/no-stage-assigned.md`` (issue #36;
issue #41, design.md D8): the method and the path as ``operations-index.md`` writes them, and one ``Param`` per row of
the section's attribute table, the rows marked "in OpenAPI only" and the deprecated rows included. Only the ``PUT``
sections ("Set up ..." and "Update integration for a ...") have a table, and every row of it is a body attribute:
``Kind.ARRAY`` for an ``array of strings`` row, ``Kind.SCALAR`` for every other, ``required`` where Required reads
``yes``. A "Get ..." or "Disable ..." section has no table, so its record declares no ``Param``. Every record sends a
JSON body and fixes no query value; the two "List all active integrations" records page by offset (``conventions.md``
"Pagination"). A secret attribute (``api_key``, ``token``, ``password``, ...) is given as ``-f`` text like any other
string. ``PENDING`` is empty: every index row of this family has its record.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "no-stage-assigned"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Group integrations API: List all active integrations".
    RestOperation(
        operation_id="no-stage-assigned#list-all-active-integrations",
        method="GET",
        path="/groups/:id/integrations",
        paging=Paging.OFFSET,
    ),
    # "Group integrations API: Set up Asana".
    RestOperation(
        operation_id="no-stage-assigned#set-up-asana",
        method="PUT",
        path="/groups/:id/integrations/asana",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Asana".
    RestOperation(
        operation_id="no-stage-assigned#disable-asana",
        method="DELETE",
        path="/groups/:id/integrations/asana",
    ),
    # "Group integrations API: Get Asana settings".
    RestOperation(
        operation_id="no-stage-assigned#get-asana-settings",
        method="GET",
        path="/groups/:id/integrations/asana",
    ),
    # "Group integrations API: Set up Assembla".
    RestOperation(
        operation_id="no-stage-assigned#set-up-assembla",
        method="PUT",
        path="/groups/:id/integrations/assembla",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Assembla".
    RestOperation(
        operation_id="no-stage-assigned#disable-assembla",
        method="DELETE",
        path="/groups/:id/integrations/assembla",
    ),
    # "Group integrations API: Get Assembla settings".
    RestOperation(
        operation_id="no-stage-assigned#get-assembla-settings",
        method="GET",
        path="/groups/:id/integrations/assembla",
    ),
    # "Group integrations API: Set up Atlassian Bamboo".
    RestOperation(
        operation_id="no-stage-assigned#set-up-atlassian-bamboo",
        method="PUT",
        path="/groups/:id/integrations/bamboo",
        params=(
            Param(name="bamboo_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="build_key", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Atlassian Bamboo".
    RestOperation(
        operation_id="no-stage-assigned#disable-atlassian-bamboo",
        method="DELETE",
        path="/groups/:id/integrations/bamboo",
    ),
    # "Group integrations API: Get Atlassian Bamboo settings".
    RestOperation(
        operation_id="no-stage-assigned#get-atlassian-bamboo-settings",
        method="GET",
        path="/groups/:id/integrations/bamboo",
    ),
    # "Group integrations API: Set up Bugzilla".
    RestOperation(
        operation_id="no-stage-assigned#set-up-bugzilla",
        method="PUT",
        path="/groups/:id/integrations/bugzilla",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Bugzilla".
    RestOperation(
        operation_id="no-stage-assigned#disable-bugzilla",
        method="DELETE",
        path="/groups/:id/integrations/bugzilla",
    ),
    # "Group integrations API: Get Bugzilla settings".
    RestOperation(
        operation_id="no-stage-assigned#get-bugzilla-settings",
        method="GET",
        path="/groups/:id/integrations/bugzilla",
    ),
    # "Group integrations API: Set up Buildkite".
    RestOperation(
        operation_id="no-stage-assigned#set-up-buildkite",
        method="PUT",
        path="/groups/:id/integrations/buildkite",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Buildkite".
    RestOperation(
        operation_id="no-stage-assigned#disable-buildkite",
        method="DELETE",
        path="/groups/:id/integrations/buildkite",
    ),
    # "Group integrations API: Get Buildkite settings".
    RestOperation(
        operation_id="no-stage-assigned#get-buildkite-settings",
        method="GET",
        path="/groups/:id/integrations/buildkite",
    ),
    # "Group integrations API: Set up Campfire Classic".
    RestOperation(
        operation_id="no-stage-assigned#set-up-campfire-classic",
        method="PUT",
        path="/groups/:id/integrations/campfire",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="room", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Campfire Classic".
    RestOperation(
        operation_id="no-stage-assigned#disable-campfire-classic",
        method="DELETE",
        path="/groups/:id/integrations/campfire",
    ),
    # "Group integrations API: Get Campfire Classic settings".
    RestOperation(
        operation_id="no-stage-assigned#get-campfire-classic-settings",
        method="GET",
        path="/groups/:id/integrations/campfire",
    ),
    # "Group integrations API: Set up ClickUp".
    RestOperation(
        operation_id="no-stage-assigned#set-up-clickup",
        method="PUT",
        path="/groups/:id/integrations/clickup",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable ClickUp".
    RestOperation(
        operation_id="no-stage-assigned#disable-clickup",
        method="DELETE",
        path="/groups/:id/integrations/clickup",
    ),
    # "Group integrations API: Get ClickUp settings".
    RestOperation(
        operation_id="no-stage-assigned#get-clickup-settings",
        method="GET",
        path="/groups/:id/integrations/clickup",
    ),
    # "Group integrations API: Set up Confluence Workspace".
    RestOperation(
        operation_id="no-stage-assigned#set-up-confluence-workspace",
        method="PUT",
        path="/groups/:id/integrations/confluence",
        params=(
            Param(name="confluence_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Confluence Workspace".
    RestOperation(
        operation_id="no-stage-assigned#disable-confluence-workspace",
        method="DELETE",
        path="/groups/:id/integrations/confluence",
    ),
    # "Group integrations API: Get Confluence Workspace settings".
    RestOperation(
        operation_id="no-stage-assigned#get-confluence-workspace-settings",
        method="GET",
        path="/groups/:id/integrations/confluence",
    ),
    # "Group integrations API: Set up a custom issue tracker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-a-custom-issue-tracker",
        method="PUT",
        path="/groups/:id/integrations/custom-issue-tracker",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable a custom issue tracker".
    RestOperation(
        operation_id="no-stage-assigned#disable-a-custom-issue-tracker",
        method="DELETE",
        path="/groups/:id/integrations/custom-issue-tracker",
    ),
    # "Group integrations API: Get custom issue tracker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-custom-issue-tracker-settings",
        method="GET",
        path="/groups/:id/integrations/custom-issue-tracker",
    ),
    # "Group integrations API: Set up Datadog".
    RestOperation(
        operation_id="no-stage-assigned#set-up-datadog",
        method="PUT",
        path="/groups/:id/integrations/datadog",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="datadog_env", location=Location.BODY),
            Param(name="datadog_service", location=Location.BODY),
            Param(name="datadog_site", location=Location.BODY),
            Param(name="datadog_tags", location=Location.BODY),
            Param(name="datadog_ci_visibility", location=Location.BODY),
            Param(name="archive_trace_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="build_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="subgroup_events", location=Location.BODY),
            Param(name="project_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Datadog".
    RestOperation(
        operation_id="no-stage-assigned#disable-datadog",
        method="DELETE",
        path="/groups/:id/integrations/datadog",
    ),
    # "Group integrations API: Get Datadog settings".
    RestOperation(
        operation_id="no-stage-assigned#get-datadog-settings",
        method="GET",
        path="/groups/:id/integrations/datadog",
    ),
    # "Group integrations API: Set up Diffblue Cover".
    RestOperation(
        operation_id="no-stage-assigned#set-up-diffblue-cover",
        method="PUT",
        path="/groups/:id/integrations/diffblue-cover",
        params=(
            Param(name="diffblue_license_key", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_name", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_secret", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Diffblue Cover".
    RestOperation(
        operation_id="no-stage-assigned#disable-diffblue-cover",
        method="DELETE",
        path="/groups/:id/integrations/diffblue-cover",
    ),
    # "Group integrations API: Get Diffblue Cover settings".
    RestOperation(
        operation_id="no-stage-assigned#get-diffblue-cover-settings",
        method="GET",
        path="/groups/:id/integrations/diffblue-cover",
    ),
    # "Group integrations API: Set up Discord Notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-discord-notifications",
        method="PUT",
        path="/groups/:id/integrations/discord",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="group_confidential_mentions_events", location=Location.BODY),
            Param(name="group_confidential_mentions_channel", location=Location.BODY),
            Param(name="group_mentions_events", location=Location.BODY),
            Param(name="group_mentions_channel", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Discord Notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-discord-notifications",
        method="DELETE",
        path="/groups/:id/integrations/discord",
    ),
    # "Group integrations API: Get Discord Notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-discord-notifications-settings",
        method="GET",
        path="/groups/:id/integrations/discord",
    ),
    # "Group integrations API: Set up Drone".
    RestOperation(
        operation_id="no-stage-assigned#set-up-drone",
        method="PUT",
        path="/groups/:id/integrations/drone-ci",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="drone_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Drone".
    RestOperation(
        operation_id="no-stage-assigned#disable-drone",
        method="DELETE",
        path="/groups/:id/integrations/drone-ci",
    ),
    # "Group integrations API: Get Drone settings".
    RestOperation(
        operation_id="no-stage-assigned#get-drone-settings",
        method="GET",
        path="/groups/:id/integrations/drone-ci",
    ),
    # "Group integrations API: Set up emails on push".
    RestOperation(
        operation_id="no-stage-assigned#set-up-emails-on-push",
        method="PUT",
        path="/groups/:id/integrations/emails-on-push",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="disable_diffs", location=Location.BODY),
            Param(name="send_from_committer_email", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable emails on push".
    RestOperation(
        operation_id="no-stage-assigned#disable-emails-on-push",
        method="DELETE",
        path="/groups/:id/integrations/emails-on-push",
    ),
    # "Group integrations API: Get emails on push settings".
    RestOperation(
        operation_id="no-stage-assigned#get-emails-on-push-settings",
        method="GET",
        path="/groups/:id/integrations/emails-on-push",
    ),
    # "Group integrations API: Set up EWM".
    RestOperation(
        operation_id="no-stage-assigned#set-up-ewm",
        method="PUT",
        path="/groups/:id/integrations/ewm",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable EWM".
    RestOperation(
        operation_id="no-stage-assigned#disable-ewm",
        method="DELETE",
        path="/groups/:id/integrations/ewm",
    ),
    # "Group integrations API: Get EWM settings".
    RestOperation(
        operation_id="no-stage-assigned#get-ewm-settings",
        method="GET",
        path="/groups/:id/integrations/ewm",
    ),
    # "Group integrations API: Set up an external wiki".
    RestOperation(
        operation_id="no-stage-assigned#set-up-an-external-wiki",
        method="PUT",
        path="/groups/:id/integrations/external-wiki",
        params=(
            Param(name="external_wiki_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable an external wiki".
    RestOperation(
        operation_id="no-stage-assigned#disable-an-external-wiki",
        method="DELETE",
        path="/groups/:id/integrations/external-wiki",
    ),
    # "Group integrations API: Get external wiki settings".
    RestOperation(
        operation_id="no-stage-assigned#get-external-wiki-settings",
        method="GET",
        path="/groups/:id/integrations/external-wiki",
    ),
    # "Group integrations API: Set up GitGuardian".
    RestOperation(
        operation_id="no-stage-assigned#set-up-gitguardian",
        method="PUT",
        path="/groups/:id/integrations/git-guardian",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable GitGuardian".
    RestOperation(
        operation_id="no-stage-assigned#disable-gitguardian",
        method="DELETE",
        path="/groups/:id/integrations/git-guardian",
    ),
    # "Group integrations API: Get GitGuardian settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitguardian-settings",
        method="GET",
        path="/groups/:id/integrations/git-guardian",
    ),
    # "Group integrations API: Set up GitHub".
    RestOperation(
        operation_id="no-stage-assigned#set-up-github",
        method="PUT",
        path="/groups/:id/integrations/github",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="repository_url", location=Location.BODY, required=True),
            Param(name="static_context", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable GitHub".
    RestOperation(
        operation_id="no-stage-assigned#disable-github",
        method="DELETE",
        path="/groups/:id/integrations/github",
    ),
    # "Group integrations API: Get GitHub settings".
    RestOperation(
        operation_id="no-stage-assigned#get-github-settings",
        method="GET",
        path="/groups/:id/integrations/github",
    ),
    # "Group integrations API: Update integration for a group".
    RestOperation(
        operation_id="no-stage-assigned#update-integration-for-a-group",
        method="PUT",
        path="/groups/:id/integrations/jira-cloud-app",
        params=(
            Param(name="jira_cloud_app_service_ids", location=Location.BODY),
            Param(name="jira_cloud_app_enable_deployment_gating", location=Location.BODY),
            Param(name="jira_cloud_app_deployment_gating_environments", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Get GitLab for Jira Cloud app settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitlab-for-jira-cloud-app-settings",
        method="GET",
        path="/groups/:id/integrations/jira-cloud-app",
    ),
    # "Group integrations API: Set up GitLab for Slack app".
    RestOperation(
        operation_id="no-stage-assigned#set-up-gitlab-for-slack-app",
        method="PUT",
        path="/groups/:id/integrations/gitlab-slack-application",
        params=(
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incidents_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable GitLab for Slack app".
    RestOperation(
        operation_id="no-stage-assigned#disable-gitlab-for-slack-app",
        method="DELETE",
        path="/groups/:id/integrations/gitlab-slack-application",
    ),
    # "Group integrations API: Get GitLab for Slack app settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitlab-for-slack-app-settings",
        method="GET",
        path="/groups/:id/integrations/gitlab-slack-application",
    ),
    # "Group integrations API: Set up Google Chat".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-chat",
        method="PUT",
        path="/groups/:id/integrations/hangouts-chat",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Google Chat".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-chat",
        method="DELETE",
        path="/groups/:id/integrations/hangouts-chat",
    ),
    # "Group integrations API: Get Google Chat settings".
    RestOperation(
        operation_id="no-stage-assigned#get-google-chat-settings",
        method="GET",
        path="/groups/:id/integrations/hangouts-chat",
    ),
    # "Group integrations API: Set up Google Artifact Management".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-artifact-management",
        method="PUT",
        path="/groups/:id/integrations/google-cloud-platform-artifact-registry",
        params=(
            Param(name="artifact_registry_project_id", location=Location.BODY, required=True),
            Param(name="artifact_registry_location", location=Location.BODY, required=True),
            Param(name="artifact_registry_repositories", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Google Artifact Management".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-artifact-management",
        method="DELETE",
        path="/groups/:id/integrations/google-cloud-platform-artifact-registry",
    ),
    # "Group integrations API: Get Google Artifact Management settings".
    RestOperation(
        operation_id="no-stage-assigned#get-google-artifact-management-settings",
        method="GET",
        path="/groups/:id/integrations/google-cloud-platform-artifact-registry",
    ),
    # "Group integrations API: Set up Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-cloud-identity-and-access-management",
        method="PUT",
        path="/groups/:id/integrations/google-cloud-platform-workload-identity-federation",
        params=(
            Param(name="workload_identity_federation_project_id", location=Location.BODY, required=True),
            Param(name="workload_identity_federation_project_number", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_id", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_provider_id", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-cloud-identity-and-access-management",
        method="DELETE",
        path="/groups/:id/integrations/google-cloud-platform-workload-identity-federation",
    ),
    # "Group integrations API: Get Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#get-google-cloud-identity-and-access-management",
        method="GET",
        path="/groups/:id/integration/google-cloud-platform-workload-identity-federation",
    ),
    # "Group integrations API: Set up Harbor".
    RestOperation(
        operation_id="no-stage-assigned#set-up-harbor",
        method="PUT",
        path="/groups/:id/integrations/harbor",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Harbor".
    RestOperation(
        operation_id="no-stage-assigned#disable-harbor",
        method="DELETE",
        path="/groups/:id/integrations/harbor",
    ),
    # "Group integrations API: Get Harbor settings".
    RestOperation(
        operation_id="no-stage-assigned#get-harbor-settings",
        method="GET",
        path="/groups/:id/integrations/harbor",
    ),
    # "Group integrations API: Set up irker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-irker",
        method="PUT",
        path="/groups/:id/integrations/irker",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="default_irc_uri", location=Location.BODY),
            Param(name="server_host", location=Location.BODY),
            Param(name="server_port", location=Location.BODY),
            Param(name="colorize_messages", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable irker".
    RestOperation(
        operation_id="no-stage-assigned#disable-irker",
        method="DELETE",
        path="/groups/:id/integrations/irker",
    ),
    # "Group integrations API: Get irker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-irker-settings",
        method="GET",
        path="/groups/:id/integrations/irker",
    ),
    # "Group integrations API: Set up JetBrains TeamCity".
    RestOperation(
        operation_id="no-stage-assigned#set-up-jetbrains-teamcity",
        method="PUT",
        path="/groups/:id/integrations/teamcity",
        params=(
            Param(name="teamcity_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="build_type", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable JetBrains TeamCity".
    RestOperation(
        operation_id="no-stage-assigned#disable-jetbrains-teamcity",
        method="DELETE",
        path="/groups/:id/integrations/teamcity",
    ),
    # "Group integrations API: Get JetBrains TeamCity settings".
    RestOperation(
        operation_id="no-stage-assigned#get-jetbrains-teamcity-settings",
        method="GET",
        path="/groups/:id/integrations/teamcity",
    ),
    # "Group integrations API: Set up Jira".
    RestOperation(
        operation_id="no-stage-assigned#set-up-jira",
        method="PUT",
        path="/groups/:id/integrations/jira",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="jira_auth_type", location=Location.BODY),
            Param(name="jira_issue_prefix", location=Location.BODY),
            Param(name="jira_issue_regex", location=Location.BODY),
            Param(name="jira_issue_transition_automatic", location=Location.BODY),
            Param(name="jira_issue_transition_id", location=Location.BODY),
            Param(name="commit_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="comment_on_event_enabled", location=Location.BODY),
            Param(name="issues_enabled", location=Location.BODY),
            Param(name="project_keys", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="vulnerabilities_enabled", location=Location.BODY),
            Param(name="vulnerabilities_issuetype", location=Location.BODY),
            Param(name="project_key", location=Location.BODY),
            Param(name="customize_jira_issue_enabled", location=Location.BODY),
            Param(name="jira_check_enabled", location=Location.BODY),
            Param(name="jira_exists_check_enabled", location=Location.BODY),
            Param(name="jira_assignee_check_enabled", location=Location.BODY),
            Param(name="jira_status_check_enabled", location=Location.BODY),
            Param(name="jira_allowed_statuses_as_string", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Jira".
    RestOperation(
        operation_id="no-stage-assigned#disable-jira",
        method="DELETE",
        path="/groups/:id/integrations/jira",
    ),
    # "Group integrations API: Get Jira settings".
    RestOperation(
        operation_id="no-stage-assigned#get-jira-settings",
        method="GET",
        path="/groups/:id/integrations/jira",
    ),
    # "Group integrations API: Set up Linear".
    RestOperation(
        operation_id="no-stage-assigned#set-up-linear",
        method="PUT",
        path="/groups/:id/integrations/linear",
        params=(
            Param(name="workspace_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Linear".
    RestOperation(
        operation_id="no-stage-assigned#disable-linear",
        method="DELETE",
        path="/groups/:id/integrations/linear",
    ),
    # "Group integrations API: Get Linear settings".
    RestOperation(
        operation_id="no-stage-assigned#get-linear-settings",
        method="GET",
        path="/groups/:id/integrations/linear",
    ),
    # "Group integrations API: Set up Matrix notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-matrix-notifications",
        method="PUT",
        path="/groups/:id/integrations/matrix",
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
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Matrix notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-matrix-notifications",
        method="DELETE",
        path="/groups/:id/integrations/matrix",
    ),
    # "Group integrations API: Get Matrix notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-matrix-notifications-settings",
        method="GET",
        path="/groups/:id/integrations/matrix",
    ),
    # "Group integrations API: Set up Mattermost notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mattermost-notifications",
        method="PUT",
        path="/groups/:id/integrations/mattermost",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Mattermost notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-mattermost-notifications",
        method="DELETE",
        path="/groups/:id/integrations/mattermost",
    ),
    # "Group integrations API: Get Mattermost notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mattermost-notifications-settings",
        method="GET",
        path="/groups/:id/integrations/mattermost",
    ),
    # "Group integrations API: Set up Mattermost slash commands".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mattermost-slash-commands",
        method="PUT",
        path="/groups/:id/integrations/mattermost-slash-commands",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Mattermost slash commands".
    RestOperation(
        operation_id="no-stage-assigned#disable-mattermost-slash-commands",
        method="DELETE",
        path="/groups/:id/integrations/mattermost-slash-commands",
    ),
    # "Group integrations API: Get Mattermost slash commands settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mattermost-slash-commands-settings",
        method="GET",
        path="/groups/:id/integrations/mattermost-slash-commands",
    ),
    # "Group integrations API: Set up Microsoft Teams notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-microsoft-teams-notifications",
        method="PUT",
        path="/groups/:id/integrations/microsoft-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Microsoft Teams notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-microsoft-teams-notifications",
        method="DELETE",
        path="/groups/:id/integrations/microsoft-teams",
    ),
    # "Group integrations API: Get Microsoft Teams notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-microsoft-teams-notifications-settings",
        method="GET",
        path="/groups/:id/integrations/microsoft-teams",
    ),
    # "Group integrations API: Set up Mock CI".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mock-ci",
        method="PUT",
        path="/groups/:id/integrations/mock-ci",
        params=(
            Param(name="mock_service_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Mock CI".
    RestOperation(
        operation_id="no-stage-assigned#disable-mock-ci",
        method="DELETE",
        path="/groups/:id/integrations/mock-ci",
    ),
    # "Group integrations API: Get Mock CI settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mock-ci-settings",
        method="GET",
        path="/groups/:id/integrations/mock-ci",
    ),
    # "Group integrations API: Set up Packagist".
    RestOperation(
        operation_id="no-stage-assigned#set-up-packagist",
        method="PUT",
        path="/groups/:id/integrations/packagist",
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
    # "Group integrations API: Disable Packagist".
    RestOperation(
        operation_id="no-stage-assigned#disable-packagist",
        method="DELETE",
        path="/groups/:id/integrations/packagist",
    ),
    # "Group integrations API: Get Packagist settings".
    RestOperation(
        operation_id="no-stage-assigned#get-packagist-settings",
        method="GET",
        path="/groups/:id/integrations/packagist",
    ),
    # "Group integrations API: Set up Phorge".
    RestOperation(
        operation_id="no-stage-assigned#set-up-phorge",
        method="PUT",
        path="/groups/:id/integrations/phorge",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Phorge".
    RestOperation(
        operation_id="no-stage-assigned#disable-phorge",
        method="DELETE",
        path="/groups/:id/integrations/phorge",
    ),
    # "Group integrations API: Get Phorge settings".
    RestOperation(
        operation_id="no-stage-assigned#get-phorge-settings",
        method="GET",
        path="/groups/:id/integrations/phorge",
    ),
    # "Group integrations API: Set up pipeline status emails".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pipeline-status-emails",
        method="PUT",
        path="/groups/:id/integrations/pipelines-email",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_child_pipelines", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable pipeline status emails".
    RestOperation(
        operation_id="no-stage-assigned#disable-pipeline-status-emails",
        method="DELETE",
        path="/groups/:id/integrations/pipelines-email",
    ),
    # "Group integrations API: Get pipeline status emails settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pipeline-status-emails-settings",
        method="GET",
        path="/groups/:id/integrations/pipelines-email",
    ),
    # "Group integrations API: Set up Pivotal Tracker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pivotal-tracker",
        method="PUT",
        path="/groups/:id/integrations/pivotaltracker",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Pivotal Tracker".
    RestOperation(
        operation_id="no-stage-assigned#disable-pivotal-tracker",
        method="DELETE",
        path="/groups/:id/integrations/pivotaltracker",
    ),
    # "Group integrations API: Get Pivotal Tracker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pivotal-tracker-settings",
        method="GET",
        path="/groups/:id/integrations/pivotaltracker",
    ),
    # "Group integrations API: Set up Pumble".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pumble",
        method="PUT",
        path="/groups/:id/integrations/pumble",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Pumble".
    RestOperation(
        operation_id="no-stage-assigned#disable-pumble",
        method="DELETE",
        path="/groups/:id/integrations/pumble",
    ),
    # "Group integrations API: Get Pumble settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pumble-settings",
        method="GET",
        path="/groups/:id/integrations/pumble",
    ),
    # "Group integrations API: Set up Pushover".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pushover",
        method="PUT",
        path="/groups/:id/integrations/pushover",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="user_key", location=Location.BODY, required=True),
            Param(name="priority", location=Location.BODY, required=True),
            Param(name="device", location=Location.BODY),
            Param(name="sound", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Pushover".
    RestOperation(
        operation_id="no-stage-assigned#disable-pushover",
        method="DELETE",
        path="/groups/:id/integrations/pushover",
    ),
    # "Group integrations API: Get Pushover settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pushover-settings",
        method="GET",
        path="/groups/:id/integrations/pushover",
    ),
    # "Group integrations API: Set up Redmine".
    RestOperation(
        operation_id="no-stage-assigned#set-up-redmine",
        method="PUT",
        path="/groups/:id/integrations/redmine",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Redmine".
    RestOperation(
        operation_id="no-stage-assigned#disable-redmine",
        method="DELETE",
        path="/groups/:id/integrations/redmine",
    ),
    # "Group integrations API: Get Redmine settings".
    RestOperation(
        operation_id="no-stage-assigned#get-redmine-settings",
        method="GET",
        path="/groups/:id/integrations/redmine",
    ),
    # "Group integrations API: Set up Slack notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-slack-notifications",
        method="PUT",
        path="/groups/:id/integrations/slack",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="commit_events", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="incidents_events", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Slack notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-slack-notifications",
        method="DELETE",
        path="/groups/:id/integrations/slack",
    ),
    # "Group integrations API: Get Slack notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-slack-notifications-settings",
        method="GET",
        path="/groups/:id/integrations/slack",
    ),
    # "Group integrations API: Set up Squash TM".
    RestOperation(
        operation_id="no-stage-assigned#set-up-squash-tm",
        method="PUT",
        path="/groups/:id/integrations/squash-tm",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Squash TM".
    RestOperation(
        operation_id="no-stage-assigned#disable-squash-tm",
        method="DELETE",
        path="/groups/:id/integrations/squash-tm",
    ),
    # "Group integrations API: Get Squash TM settings".
    RestOperation(
        operation_id="no-stage-assigned#get-squash-tm-settings",
        method="GET",
        path="/groups/:id/integrations/squash-tm",
    ),
    # "Group integrations API: Set up Telegram".
    RestOperation(
        operation_id="no-stage-assigned#set-up-telegram",
        method="PUT",
        path="/groups/:id/integrations/telegram",
        params=(
            Param(name="hostname", location=Location.BODY),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="room", location=Location.BODY, required=True),
            Param(name="thread", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY, required=True),
            Param(name="issues_events", location=Location.BODY, required=True),
            Param(name="confidential_issues_events", location=Location.BODY, required=True),
            Param(name="merge_requests_events", location=Location.BODY, required=True),
            Param(name="tag_push_events", location=Location.BODY, required=True),
            Param(name="note_events", location=Location.BODY, required=True),
            Param(name="confidential_note_events", location=Location.BODY, required=True),
            Param(name="pipeline_events", location=Location.BODY, required=True),
            Param(name="wiki_page_events", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Telegram".
    RestOperation(
        operation_id="no-stage-assigned#disable-telegram",
        method="DELETE",
        path="/groups/:id/integrations/telegram",
    ),
    # "Group integrations API: Get Telegram settings".
    RestOperation(
        operation_id="no-stage-assigned#get-telegram-settings",
        method="GET",
        path="/groups/:id/integrations/telegram",
    ),
    # "Group integrations API: Set up Unify Circuit".
    RestOperation(
        operation_id="no-stage-assigned#set-up-unify-circuit",
        method="PUT",
        path="/groups/:id/integrations/unify-circuit",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Unify Circuit".
    RestOperation(
        operation_id="no-stage-assigned#disable-unify-circuit",
        method="DELETE",
        path="/groups/:id/integrations/unify-circuit",
    ),
    # "Group integrations API: Get Unify Circuit settings".
    RestOperation(
        operation_id="no-stage-assigned#get-unify-circuit-settings",
        method="GET",
        path="/groups/:id/integrations/unify-circuit",
    ),
    # "Group integrations API: Set up Webex Teams".
    RestOperation(
        operation_id="no-stage-assigned#set-up-webex-teams",
        method="PUT",
        path="/groups/:id/integrations/webex-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable Webex Teams".
    RestOperation(
        operation_id="no-stage-assigned#disable-webex-teams",
        method="DELETE",
        path="/groups/:id/integrations/webex-teams",
    ),
    # "Group integrations API: Get Webex Teams settings".
    RestOperation(
        operation_id="no-stage-assigned#get-webex-teams-settings",
        method="GET",
        path="/groups/:id/integrations/webex-teams",
    ),
    # "Group integrations API: Set up YouTrack".
    RestOperation(
        operation_id="no-stage-assigned#set-up-youtrack",
        method="PUT",
        path="/groups/:id/integrations/youtrack",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Group integrations API: Disable YouTrack".
    RestOperation(
        operation_id="no-stage-assigned#disable-youtrack",
        method="DELETE",
        path="/groups/:id/integrations/youtrack",
    ),
    # "Group integrations API: Get YouTrack settings".
    RestOperation(
        operation_id="no-stage-assigned#get-youtrack-settings",
        method="GET",
        path="/groups/:id/integrations/youtrack",
    ),
    # "Project integrations API: List all active integrations".
    RestOperation(
        operation_id="no-stage-assigned#list-all-active-integrations-1",
        method="GET",
        path="/projects/:id/integrations",
        paging=Paging.OFFSET,
    ),
    # "Project integrations API: Set up Apple App Store Connect".
    RestOperation(
        operation_id="no-stage-assigned#set-up-apple-app-store-connect",
        method="PUT",
        path="/projects/:id/integrations/apple_app_store",
        params=(
            Param(name="app_store_issuer_id", location=Location.BODY, required=True),
            Param(name="app_store_key_id", location=Location.BODY, required=True),
            Param(name="app_store_private_key_file_name", location=Location.BODY, required=True),
            Param(name="app_store_private_key", location=Location.BODY, required=True),
            Param(name="app_store_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Apple App Store Connect".
    RestOperation(
        operation_id="no-stage-assigned#disable-apple-app-store-connect",
        method="DELETE",
        path="/projects/:id/integrations/apple_app_store",
    ),
    # "Project integrations API: Get Apple App Store Connect settings".
    RestOperation(
        operation_id="no-stage-assigned#get-apple-app-store-connect-settings",
        method="GET",
        path="/projects/:id/integrations/apple_app_store",
    ),
    # "Project integrations API: Set up Asana".
    RestOperation(
        operation_id="no-stage-assigned#set-up-asana-1",
        method="PUT",
        path="/projects/:id/integrations/asana",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Asana".
    RestOperation(
        operation_id="no-stage-assigned#disable-asana-1",
        method="DELETE",
        path="/projects/:id/integrations/asana",
    ),
    # "Project integrations API: Get Asana settings".
    RestOperation(
        operation_id="no-stage-assigned#get-asana-settings-1",
        method="GET",
        path="/projects/:id/integrations/asana",
    ),
    # "Project integrations API: Set up Assembla".
    RestOperation(
        operation_id="no-stage-assigned#set-up-assembla-1",
        method="PUT",
        path="/projects/:id/integrations/assembla",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Assembla".
    RestOperation(
        operation_id="no-stage-assigned#disable-assembla-1",
        method="DELETE",
        path="/projects/:id/integrations/assembla",
    ),
    # "Project integrations API: Get Assembla settings".
    RestOperation(
        operation_id="no-stage-assigned#get-assembla-settings-1",
        method="GET",
        path="/projects/:id/integrations/assembla",
    ),
    # "Project integrations API: Set up Atlassian Bamboo".
    RestOperation(
        operation_id="no-stage-assigned#set-up-atlassian-bamboo-1",
        method="PUT",
        path="/projects/:id/integrations/bamboo",
        params=(
            Param(name="bamboo_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="build_key", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Atlassian Bamboo".
    RestOperation(
        operation_id="no-stage-assigned#disable-atlassian-bamboo-1",
        method="DELETE",
        path="/projects/:id/integrations/bamboo",
    ),
    # "Project integrations API: Get Atlassian Bamboo settings".
    RestOperation(
        operation_id="no-stage-assigned#get-atlassian-bamboo-settings-1",
        method="GET",
        path="/projects/:id/integrations/bamboo",
    ),
    # "Project integrations API: Set up Bugzilla".
    RestOperation(
        operation_id="no-stage-assigned#set-up-bugzilla-1",
        method="PUT",
        path="/projects/:id/integrations/bugzilla",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Bugzilla".
    RestOperation(
        operation_id="no-stage-assigned#disable-bugzilla-1",
        method="DELETE",
        path="/projects/:id/integrations/bugzilla",
    ),
    # "Project integrations API: Get Bugzilla settings".
    RestOperation(
        operation_id="no-stage-assigned#get-bugzilla-settings-1",
        method="GET",
        path="/projects/:id/integrations/bugzilla",
    ),
    # "Project integrations API: Set up Buildkite".
    RestOperation(
        operation_id="no-stage-assigned#set-up-buildkite-1",
        method="PUT",
        path="/projects/:id/integrations/buildkite",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Buildkite".
    RestOperation(
        operation_id="no-stage-assigned#disable-buildkite-1",
        method="DELETE",
        path="/projects/:id/integrations/buildkite",
    ),
    # "Project integrations API: Get Buildkite settings".
    RestOperation(
        operation_id="no-stage-assigned#get-buildkite-settings-1",
        method="GET",
        path="/projects/:id/integrations/buildkite",
    ),
    # "Project integrations API: Set up Campfire Classic".
    RestOperation(
        operation_id="no-stage-assigned#set-up-campfire-classic-1",
        method="PUT",
        path="/projects/:id/integrations/campfire",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="subdomain", location=Location.BODY),
            Param(name="room", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Campfire Classic".
    RestOperation(
        operation_id="no-stage-assigned#disable-campfire-classic-1",
        method="DELETE",
        path="/projects/:id/integrations/campfire",
    ),
    # "Project integrations API: Get Campfire Classic settings".
    RestOperation(
        operation_id="no-stage-assigned#get-campfire-classic-settings-1",
        method="GET",
        path="/projects/:id/integrations/campfire",
    ),
    # "Project integrations API: Set up ClickUp".
    RestOperation(
        operation_id="no-stage-assigned#set-up-clickup-1",
        method="PUT",
        path="/projects/:id/integrations/clickup",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable ClickUp".
    RestOperation(
        operation_id="no-stage-assigned#disable-clickup-1",
        method="DELETE",
        path="/projects/:id/integrations/clickup",
    ),
    # "Project integrations API: Get ClickUp settings".
    RestOperation(
        operation_id="no-stage-assigned#get-clickup-settings-1",
        method="GET",
        path="/projects/:id/integrations/clickup",
    ),
    # "Project integrations API: Set up Confluence Workspace".
    RestOperation(
        operation_id="no-stage-assigned#set-up-confluence-workspace-1",
        method="PUT",
        path="/projects/:id/integrations/confluence",
        params=(
            Param(name="confluence_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Confluence Workspace".
    RestOperation(
        operation_id="no-stage-assigned#disable-confluence-workspace-1",
        method="DELETE",
        path="/projects/:id/integrations/confluence",
    ),
    # "Project integrations API: Get Confluence Workspace settings".
    RestOperation(
        operation_id="no-stage-assigned#get-confluence-workspace-settings-1",
        method="GET",
        path="/projects/:id/integrations/confluence",
    ),
    # "Project integrations API: Set up a custom issue tracker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-a-custom-issue-tracker-1",
        method="PUT",
        path="/projects/:id/integrations/custom-issue-tracker",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable a custom issue tracker".
    RestOperation(
        operation_id="no-stage-assigned#disable-a-custom-issue-tracker-1",
        method="DELETE",
        path="/projects/:id/integrations/custom-issue-tracker",
    ),
    # "Project integrations API: Get custom issue tracker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-custom-issue-tracker-settings-1",
        method="GET",
        path="/projects/:id/integrations/custom-issue-tracker",
    ),
    # "Project integrations API: Set up Datadog".
    RestOperation(
        operation_id="no-stage-assigned#set-up-datadog-1",
        method="PUT",
        path="/projects/:id/integrations/datadog",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="datadog_ci_visibility", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="datadog_env", location=Location.BODY),
            Param(name="datadog_service", location=Location.BODY),
            Param(name="datadog_site", location=Location.BODY),
            Param(name="datadog_tags", location=Location.BODY),
            Param(name="archive_trace_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="build_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="subgroup_events", location=Location.BODY),
            Param(name="project_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Datadog".
    RestOperation(
        operation_id="no-stage-assigned#disable-datadog-1",
        method="DELETE",
        path="/projects/:id/integrations/datadog",
    ),
    # "Project integrations API: Get Datadog settings".
    RestOperation(
        operation_id="no-stage-assigned#get-datadog-settings-1",
        method="GET",
        path="/projects/:id/integrations/datadog",
    ),
    # "Project integrations API: Set up Diffblue Cover".
    RestOperation(
        operation_id="no-stage-assigned#set-up-diffblue-cover-1",
        method="PUT",
        path="/projects/:id/integrations/diffblue-cover",
        params=(
            Param(name="diffblue_license_key", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_name", location=Location.BODY, required=True),
            Param(name="diffblue_access_token_secret", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Diffblue Cover".
    RestOperation(
        operation_id="no-stage-assigned#disable-diffblue-cover-1",
        method="DELETE",
        path="/projects/:id/integrations/diffblue-cover",
    ),
    # "Project integrations API: Get Diffblue Cover settings".
    RestOperation(
        operation_id="no-stage-assigned#get-diffblue-cover-settings-1",
        method="GET",
        path="/projects/:id/integrations/diffblue-cover",
    ),
    # "Project integrations API: Set up Discord Notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-discord-notifications-1",
        method="PUT",
        path="/projects/:id/integrations/discord",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="group_confidential_mentions_events", location=Location.BODY),
            Param(name="group_confidential_mentions_channel", location=Location.BODY),
            Param(name="group_mentions_events", location=Location.BODY),
            Param(name="group_mentions_channel", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Discord Notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-discord-notifications-1",
        method="DELETE",
        path="/projects/:id/integrations/discord",
    ),
    # "Project integrations API: Get Discord Notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-discord-notifications-settings-1",
        method="GET",
        path="/projects/:id/integrations/discord",
    ),
    # "Project integrations API: Set up Drone".
    RestOperation(
        operation_id="no-stage-assigned#set-up-drone-1",
        method="PUT",
        path="/projects/:id/integrations/drone-ci",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="drone_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Drone".
    RestOperation(
        operation_id="no-stage-assigned#disable-drone-1",
        method="DELETE",
        path="/projects/:id/integrations/drone-ci",
    ),
    # "Project integrations API: Get Drone settings".
    RestOperation(
        operation_id="no-stage-assigned#get-drone-settings-1",
        method="GET",
        path="/projects/:id/integrations/drone-ci",
    ),
    # "Project integrations API: Set up emails on push".
    RestOperation(
        operation_id="no-stage-assigned#set-up-emails-on-push-1",
        method="PUT",
        path="/projects/:id/integrations/emails-on-push",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="disable_diffs", location=Location.BODY),
            Param(name="send_from_committer_email", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable emails on push".
    RestOperation(
        operation_id="no-stage-assigned#disable-emails-on-push-1",
        method="DELETE",
        path="/projects/:id/integrations/emails-on-push",
    ),
    # "Project integrations API: Get emails on push settings".
    RestOperation(
        operation_id="no-stage-assigned#get-emails-on-push-settings-1",
        method="GET",
        path="/projects/:id/integrations/emails-on-push",
    ),
    # "Project integrations API: Set up EWM".
    RestOperation(
        operation_id="no-stage-assigned#set-up-ewm-1",
        method="PUT",
        path="/projects/:id/integrations/ewm",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable EWM".
    RestOperation(
        operation_id="no-stage-assigned#disable-ewm-1",
        method="DELETE",
        path="/projects/:id/integrations/ewm",
    ),
    # "Project integrations API: Get EWM settings".
    RestOperation(
        operation_id="no-stage-assigned#get-ewm-settings-1",
        method="GET",
        path="/projects/:id/integrations/ewm",
    ),
    # "Project integrations API: Set up an external wiki".
    RestOperation(
        operation_id="no-stage-assigned#set-up-an-external-wiki-1",
        method="PUT",
        path="/projects/:id/integrations/external-wiki",
        params=(
            Param(name="external_wiki_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable an external wiki".
    RestOperation(
        operation_id="no-stage-assigned#disable-an-external-wiki-1",
        method="DELETE",
        path="/projects/:id/integrations/external-wiki",
    ),
    # "Project integrations API: Get external wiki settings".
    RestOperation(
        operation_id="no-stage-assigned#get-external-wiki-settings-1",
        method="GET",
        path="/projects/:id/integrations/external-wiki",
    ),
    # "Project integrations API: Set up GitGuardian".
    RestOperation(
        operation_id="no-stage-assigned#set-up-gitguardian-1",
        method="PUT",
        path="/projects/:id/integrations/git-guardian",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable GitGuardian".
    RestOperation(
        operation_id="no-stage-assigned#disable-gitguardian-1",
        method="DELETE",
        path="/projects/:id/integrations/git-guardian",
    ),
    # "Project integrations API: Get GitGuardian settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitguardian-settings-1",
        method="GET",
        path="/projects/:id/integrations/git-guardian",
    ),
    # "Project integrations API: Set up GitHub".
    RestOperation(
        operation_id="no-stage-assigned#set-up-github-1",
        method="PUT",
        path="/projects/:id/integrations/github",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="repository_url", location=Location.BODY, required=True),
            Param(name="static_context", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable GitHub".
    RestOperation(
        operation_id="no-stage-assigned#disable-github-1",
        method="DELETE",
        path="/projects/:id/integrations/github",
    ),
    # "Project integrations API: Get GitHub settings".
    RestOperation(
        operation_id="no-stage-assigned#get-github-settings-1",
        method="GET",
        path="/projects/:id/integrations/github",
    ),
    # "Project integrations API: Update integration for a project".
    RestOperation(
        operation_id="no-stage-assigned#update-integration-for-a-project",
        method="PUT",
        path="/projects/:id/integrations/jira-cloud-app",
        params=(
            Param(name="jira_cloud_app_service_ids", location=Location.BODY),
            Param(name="jira_cloud_app_enable_deployment_gating", location=Location.BODY),
            Param(name="jira_cloud_app_deployment_gating_environments", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Get GitLab for Jira Cloud app settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitlab-for-jira-cloud-app-settings-1",
        method="GET",
        path="/projects/:id/integrations/jira-cloud-app",
    ),
    # "Project integrations API: Set up GitLab for Slack app".
    RestOperation(
        operation_id="no-stage-assigned#set-up-gitlab-for-slack-app-1",
        method="PUT",
        path="/projects/:id/integrations/gitlab-slack-application",
        params=(
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incidents_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable GitLab for Slack app".
    RestOperation(
        operation_id="no-stage-assigned#disable-gitlab-for-slack-app-1",
        method="DELETE",
        path="/projects/:id/integrations/gitlab-slack-application",
    ),
    # "Project integrations API: Get GitLab for Slack app settings".
    RestOperation(
        operation_id="no-stage-assigned#get-gitlab-for-slack-app-settings-1",
        method="GET",
        path="/projects/:id/integrations/gitlab-slack-application",
    ),
    # "Project integrations API: Set up Google Chat".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-chat-1",
        method="PUT",
        path="/projects/:id/integrations/hangouts-chat",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Google Chat".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-chat-1",
        method="DELETE",
        path="/projects/:id/integrations/hangouts-chat",
    ),
    # "Project integrations API: Get Google Chat settings".
    RestOperation(
        operation_id="no-stage-assigned#get-google-chat-settings-1",
        method="GET",
        path="/projects/:id/integrations/hangouts-chat",
    ),
    # "Project integrations API: Set up Google Artifact Management".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-artifact-management-1",
        method="PUT",
        path="/projects/:id/integrations/google-cloud-platform-artifact-registry",
        params=(
            Param(name="artifact_registry_project_id", location=Location.BODY, required=True),
            Param(name="artifact_registry_location", location=Location.BODY, required=True),
            Param(name="artifact_registry_repositories", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Google Artifact Management".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-artifact-management-1",
        method="DELETE",
        path="/projects/:id/integrations/google-cloud-platform-artifact-registry",
    ),
    # "Project integrations API: Get Google Artifact Management settings".
    RestOperation(
        operation_id="no-stage-assigned#get-google-artifact-management-settings-1",
        method="GET",
        path="/projects/:id/integrations/google-cloud-platform-artifact-registry",
    ),
    # "Project integrations API: Set up Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-cloud-identity-and-access-management-1",
        method="PUT",
        path="/projects/:id/integrations/google-cloud-platform-workload-identity-federation",
        params=(
            Param(name="workload_identity_federation_project_id", location=Location.BODY, required=True),
            Param(name="workload_identity_federation_project_number", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_id", location=Location.BODY, required=True),
            Param(name="workload_identity_pool_provider_id", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-cloud-identity-and-access-management-1",
        method="DELETE",
        path="/projects/:id/integrations/google-cloud-platform-workload-identity-federation",
    ),
    # "Project integrations API: Get Google Cloud Identity and Access Management".
    RestOperation(
        operation_id="no-stage-assigned#get-google-cloud-identity-and-access-management-1",
        method="GET",
        path="/projects/:id/integration/google-cloud-platform-workload-identity-federation",
    ),
    # "Project integrations API: Set up Google Play".
    RestOperation(
        operation_id="no-stage-assigned#set-up-google-play",
        method="PUT",
        path="/projects/:id/integrations/google-play",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="service_account_key", location=Location.BODY, required=True),
            Param(name="service_account_key_file_name", location=Location.BODY, required=True),
            Param(name="google_play_protected_refs", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Google Play".
    RestOperation(
        operation_id="no-stage-assigned#disable-google-play",
        method="DELETE",
        path="/projects/:id/integrations/google-play",
    ),
    # "Project integrations API: Get Google Play settings".
    RestOperation(
        operation_id="no-stage-assigned#get-google-play-settings",
        method="GET",
        path="/projects/:id/integrations/google-play",
    ),
    # "Project integrations API: Set up Harbor".
    RestOperation(
        operation_id="no-stage-assigned#set-up-harbor-1",
        method="PUT",
        path="/projects/:id/integrations/harbor",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Harbor".
    RestOperation(
        operation_id="no-stage-assigned#disable-harbor-1",
        method="DELETE",
        path="/projects/:id/integrations/harbor",
    ),
    # "Project integrations API: Get Harbor settings".
    RestOperation(
        operation_id="no-stage-assigned#get-harbor-settings-1",
        method="GET",
        path="/projects/:id/integrations/harbor",
    ),
    # "Project integrations API: Set up irker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-irker-1",
        method="PUT",
        path="/projects/:id/integrations/irker",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="default_irc_uri", location=Location.BODY),
            Param(name="server_host", location=Location.BODY),
            Param(name="server_port", location=Location.BODY),
            Param(name="colorize_messages", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable irker".
    RestOperation(
        operation_id="no-stage-assigned#disable-irker-1",
        method="DELETE",
        path="/projects/:id/integrations/irker",
    ),
    # "Project integrations API: Get irker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-irker-settings-1",
        method="GET",
        path="/projects/:id/integrations/irker",
    ),
    # "Project integrations API: Set up Jenkins".
    RestOperation(
        operation_id="no-stage-assigned#set-up-jenkins",
        method="PUT",
        path="/projects/:id/integrations/jenkins",
        params=(
            Param(name="jenkins_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="project_name", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Jenkins".
    RestOperation(
        operation_id="no-stage-assigned#disable-jenkins",
        method="DELETE",
        path="/projects/:id/integrations/jenkins",
    ),
    # "Project integrations API: Get Jenkins settings".
    RestOperation(
        operation_id="no-stage-assigned#get-jenkins-settings",
        method="GET",
        path="/projects/:id/integrations/jenkins",
    ),
    # "Project integrations API: Set up JetBrains TeamCity".
    RestOperation(
        operation_id="no-stage-assigned#set-up-jetbrains-teamcity-1",
        method="PUT",
        path="/projects/:id/integrations/teamcity",
        params=(
            Param(name="teamcity_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="build_type", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="push_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable JetBrains TeamCity".
    RestOperation(
        operation_id="no-stage-assigned#disable-jetbrains-teamcity-1",
        method="DELETE",
        path="/projects/:id/integrations/teamcity",
    ),
    # "Project integrations API: Get JetBrains TeamCity settings".
    RestOperation(
        operation_id="no-stage-assigned#get-jetbrains-teamcity-settings-1",
        method="GET",
        path="/projects/:id/integrations/teamcity",
    ),
    # "Project integrations API: Set up Jira issues".
    RestOperation(
        operation_id="no-stage-assigned#set-up-jira-issues",
        method="PUT",
        path="/projects/:id/integrations/jira",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="api_url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
            Param(name="password", location=Location.BODY, required=True),
            Param(name="jira_auth_type", location=Location.BODY),
            Param(name="jira_issue_prefix", location=Location.BODY),
            Param(name="jira_issue_regex", location=Location.BODY),
            Param(name="jira_issue_transition_automatic", location=Location.BODY),
            Param(name="jira_issue_transition_id", location=Location.BODY),
            Param(name="commit_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="comment_on_event_enabled", location=Location.BODY),
            Param(name="issues_enabled", location=Location.BODY),
            Param(name="project_keys", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="vulnerabilities_enabled", location=Location.BODY),
            Param(name="vulnerabilities_issuetype", location=Location.BODY),
            Param(name="project_key", location=Location.BODY),
            Param(name="customize_jira_issue_enabled", location=Location.BODY),
            Param(name="jira_check_enabled", location=Location.BODY),
            Param(name="jira_exists_check_enabled", location=Location.BODY),
            Param(name="jira_assignee_check_enabled", location=Location.BODY),
            Param(name="jira_status_check_enabled", location=Location.BODY),
            Param(name="jira_allowed_statuses_as_string", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Jira".
    RestOperation(
        operation_id="no-stage-assigned#disable-jira-1",
        method="DELETE",
        path="/projects/:id/integrations/jira",
    ),
    # "Project integrations API: Get Jira settings".
    RestOperation(
        operation_id="no-stage-assigned#get-jira-settings-1",
        method="GET",
        path="/projects/:id/integrations/jira",
    ),
    # "Project integrations API: Set up Linear".
    RestOperation(
        operation_id="no-stage-assigned#set-up-linear-1",
        method="PUT",
        path="/projects/:id/integrations/linear",
        params=(
            Param(name="workspace_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Linear".
    RestOperation(
        operation_id="no-stage-assigned#disable-linear-1",
        method="DELETE",
        path="/projects/:id/integrations/linear",
    ),
    # "Project integrations API: Get Linear settings".
    RestOperation(
        operation_id="no-stage-assigned#get-linear-settings-1",
        method="GET",
        path="/projects/:id/integrations/linear",
    ),
    # "Project integrations API: Set up Matrix notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-matrix-notifications-1",
        method="PUT",
        path="/projects/:id/integrations/matrix",
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
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Matrix notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-matrix-notifications-1",
        method="DELETE",
        path="/projects/:id/integrations/matrix",
    ),
    # "Project integrations API: Get Matrix notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-matrix-notifications-settings-1",
        method="GET",
        path="/projects/:id/integrations/matrix",
    ),
    # "Project integrations API: Set up Mattermost notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mattermost-notifications-1",
        method="PUT",
        path="/projects/:id/integrations/mattermost",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Mattermost notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-mattermost-notifications-1",
        method="DELETE",
        path="/projects/:id/integrations/mattermost",
    ),
    # "Project integrations API: Get Mattermost notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mattermost-notifications-settings-1",
        method="GET",
        path="/projects/:id/integrations/mattermost",
    ),
    # "Project integrations API: Set up Mattermost slash commands".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mattermost-slash-commands-1",
        method="PUT",
        path="/projects/:id/integrations/mattermost-slash-commands",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Mattermost slash commands".
    RestOperation(
        operation_id="no-stage-assigned#disable-mattermost-slash-commands-1",
        method="DELETE",
        path="/projects/:id/integrations/mattermost-slash-commands",
    ),
    # "Project integrations API: Get Mattermost slash commands settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mattermost-slash-commands-settings-1",
        method="GET",
        path="/projects/:id/integrations/mattermost-slash-commands",
    ),
    # "Project integrations API: Set up Microsoft Teams notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-microsoft-teams-notifications-1",
        method="PUT",
        path="/projects/:id/integrations/microsoft-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Microsoft Teams notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-microsoft-teams-notifications-1",
        method="DELETE",
        path="/projects/:id/integrations/microsoft-teams",
    ),
    # "Project integrations API: Get Microsoft Teams notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-microsoft-teams-notifications-settings-1",
        method="GET",
        path="/projects/:id/integrations/microsoft-teams",
    ),
    # "Project integrations API: Set up Mock CI".
    RestOperation(
        operation_id="no-stage-assigned#set-up-mock-ci-1",
        method="PUT",
        path="/projects/:id/integrations/mock-ci",
        params=(
            Param(name="mock_service_url", location=Location.BODY, required=True),
            Param(name="enable_ssl_verification", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Mock CI".
    RestOperation(
        operation_id="no-stage-assigned#disable-mock-ci-1",
        method="DELETE",
        path="/projects/:id/integrations/mock-ci",
    ),
    # "Project integrations API: Get Mock CI settings".
    RestOperation(
        operation_id="no-stage-assigned#get-mock-ci-settings-1",
        method="GET",
        path="/projects/:id/integrations/mock-ci",
    ),
    # "Project integrations API: Set up Packagist".
    RestOperation(
        operation_id="no-stage-assigned#set-up-packagist-1",
        method="PUT",
        path="/projects/:id/integrations/packagist",
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
    # "Project integrations API: Disable Packagist".
    RestOperation(
        operation_id="no-stage-assigned#disable-packagist-1",
        method="DELETE",
        path="/projects/:id/integrations/packagist",
    ),
    # "Project integrations API: Get Packagist settings".
    RestOperation(
        operation_id="no-stage-assigned#get-packagist-settings-1",
        method="GET",
        path="/projects/:id/integrations/packagist",
    ),
    # "Project integrations API: Set up Phorge".
    RestOperation(
        operation_id="no-stage-assigned#set-up-phorge-1",
        method="PUT",
        path="/projects/:id/integrations/phorge",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Phorge".
    RestOperation(
        operation_id="no-stage-assigned#disable-phorge-1",
        method="DELETE",
        path="/projects/:id/integrations/phorge",
    ),
    # "Project integrations API: Get Phorge settings".
    RestOperation(
        operation_id="no-stage-assigned#get-phorge-settings-1",
        method="GET",
        path="/projects/:id/integrations/phorge",
    ),
    # "Project integrations API: Set up pipeline status emails".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pipeline-status-emails-1",
        method="PUT",
        path="/projects/:id/integrations/pipelines-email",
        params=(
            Param(name="recipients", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_child_pipelines", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable pipeline status emails".
    RestOperation(
        operation_id="no-stage-assigned#disable-pipeline-status-emails-1",
        method="DELETE",
        path="/projects/:id/integrations/pipelines-email",
    ),
    # "Project integrations API: Get pipeline status emails settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pipeline-status-emails-settings-1",
        method="GET",
        path="/projects/:id/integrations/pipelines-email",
    ),
    # "Project integrations API: Set up Pivotal Tracker".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pivotal-tracker-1",
        method="PUT",
        path="/projects/:id/integrations/pivotaltracker",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="restrict_to_branch", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Pivotal Tracker".
    RestOperation(
        operation_id="no-stage-assigned#disable-pivotal-tracker-1",
        method="DELETE",
        path="/projects/:id/integrations/pivotaltracker",
    ),
    # "Project integrations API: Get Pivotal Tracker settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pivotal-tracker-settings-1",
        method="GET",
        path="/projects/:id/integrations/pivotaltracker",
    ),
    # "Project integrations API: Set up Pumble".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pumble-1",
        method="PUT",
        path="/projects/:id/integrations/pumble",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Pumble".
    RestOperation(
        operation_id="no-stage-assigned#disable-pumble-1",
        method="DELETE",
        path="/projects/:id/integrations/pumble",
    ),
    # "Project integrations API: Get Pumble settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pumble-settings-1",
        method="GET",
        path="/projects/:id/integrations/pumble",
    ),
    # "Project integrations API: Set up Pushover".
    RestOperation(
        operation_id="no-stage-assigned#set-up-pushover-1",
        method="PUT",
        path="/projects/:id/integrations/pushover",
        params=(
            Param(name="api_key", location=Location.BODY, required=True),
            Param(name="user_key", location=Location.BODY, required=True),
            Param(name="priority", location=Location.BODY, required=True),
            Param(name="device", location=Location.BODY),
            Param(name="sound", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Pushover".
    RestOperation(
        operation_id="no-stage-assigned#disable-pushover-1",
        method="DELETE",
        path="/projects/:id/integrations/pushover",
    ),
    # "Project integrations API: Get Pushover settings".
    RestOperation(
        operation_id="no-stage-assigned#get-pushover-settings-1",
        method="GET",
        path="/projects/:id/integrations/pushover",
    ),
    # "Project integrations API: Set up Redmine".
    RestOperation(
        operation_id="no-stage-assigned#set-up-redmine-1",
        method="PUT",
        path="/projects/:id/integrations/redmine",
        params=(
            Param(name="new_issue_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Redmine".
    RestOperation(
        operation_id="no-stage-assigned#disable-redmine-1",
        method="DELETE",
        path="/projects/:id/integrations/redmine",
    ),
    # "Project integrations API: Get Redmine settings".
    RestOperation(
        operation_id="no-stage-assigned#get-redmine-settings-1",
        method="GET",
        path="/projects/:id/integrations/redmine",
    ),
    # "Project integrations API: Set up Slack notifications".
    RestOperation(
        operation_id="no-stage-assigned#set-up-slack-notifications-1",
        method="PUT",
        path="/projects/:id/integrations/slack",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="username", location=Location.BODY),
            Param(name="channel", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="notify_only_default_branch", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified", location=Location.BODY),
            Param(name="labels_to_be_notified_behavior", location=Location.BODY),
            Param(name="alert_channel", location=Location.BODY),
            Param(name="alert_events", location=Location.BODY),
            Param(name="commit_events", location=Location.BODY),
            Param(name="confidential_issue_channel", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="confidential_note_channel", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="deployment_channel", location=Location.BODY),
            Param(name="deployment_events", location=Location.BODY),
            Param(name="incident_channel", location=Location.BODY),
            Param(name="incidents_events", location=Location.BODY),
            Param(name="issue_channel", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="job_events", location=Location.BODY),
            Param(name="merge_request_channel", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="note_channel", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="pipeline_channel", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="push_channel", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="tag_push_channel", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="wiki_page_channel", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="vulnerability_channel", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Slack notifications".
    RestOperation(
        operation_id="no-stage-assigned#disable-slack-notifications-1",
        method="DELETE",
        path="/projects/:id/integrations/slack",
    ),
    # "Project integrations API: Get Slack notifications settings".
    RestOperation(
        operation_id="no-stage-assigned#get-slack-notifications-settings-1",
        method="GET",
        path="/projects/:id/integrations/slack",
    ),
    # "Project integrations API: Set up Squash TM".
    RestOperation(
        operation_id="no-stage-assigned#set-up-squash-tm-1",
        method="PUT",
        path="/projects/:id/integrations/squash-tm",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Squash TM".
    RestOperation(
        operation_id="no-stage-assigned#disable-squash-tm-1",
        method="DELETE",
        path="/projects/:id/integrations/squash-tm",
    ),
    # "Project integrations API: Get Squash TM settings".
    RestOperation(
        operation_id="no-stage-assigned#get-squash-tm-settings-1",
        method="GET",
        path="/projects/:id/integrations/squash-tm",
    ),
    # "Project integrations API: Set up Telegram".
    RestOperation(
        operation_id="no-stage-assigned#set-up-telegram-1",
        method="PUT",
        path="/projects/:id/integrations/telegram",
        params=(
            Param(name="hostname", location=Location.BODY),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="room", location=Location.BODY, required=True),
            Param(name="thread", location=Location.BODY),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY, required=True),
            Param(name="issues_events", location=Location.BODY, required=True),
            Param(name="confidential_issues_events", location=Location.BODY, required=True),
            Param(name="merge_requests_events", location=Location.BODY, required=True),
            Param(name="tag_push_events", location=Location.BODY, required=True),
            Param(name="note_events", location=Location.BODY, required=True),
            Param(name="confidential_note_events", location=Location.BODY, required=True),
            Param(name="pipeline_events", location=Location.BODY, required=True),
            Param(name="wiki_page_events", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="incident_events", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
            Param(name="vulnerability_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Telegram".
    RestOperation(
        operation_id="no-stage-assigned#disable-telegram-1",
        method="DELETE",
        path="/projects/:id/integrations/telegram",
    ),
    # "Project integrations API: Get Telegram settings".
    RestOperation(
        operation_id="no-stage-assigned#get-telegram-settings-1",
        method="GET",
        path="/projects/:id/integrations/telegram",
    ),
    # "Project integrations API: Set up Unify Circuit".
    RestOperation(
        operation_id="no-stage-assigned#set-up-unify-circuit-1",
        method="PUT",
        path="/projects/:id/integrations/unify-circuit",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Unify Circuit".
    RestOperation(
        operation_id="no-stage-assigned#disable-unify-circuit-1",
        method="DELETE",
        path="/projects/:id/integrations/unify-circuit",
    ),
    # "Project integrations API: Get Unify Circuit settings".
    RestOperation(
        operation_id="no-stage-assigned#get-unify-circuit-settings-1",
        method="GET",
        path="/projects/:id/integrations/unify-circuit",
    ),
    # "Project integrations API: Set up Webex Teams".
    RestOperation(
        operation_id="no-stage-assigned#set-up-webex-teams-1",
        method="PUT",
        path="/projects/:id/integrations/webex-teams",
        params=(
            Param(name="webhook", location=Location.BODY, required=True),
            Param(name="notify_only_broken_pipelines", location=Location.BODY),
            Param(name="branches_to_be_notified", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
            Param(name="issues_events", location=Location.BODY),
            Param(name="confidential_issues_events", location=Location.BODY),
            Param(name="merge_requests_events", location=Location.BODY),
            Param(name="tag_push_events", location=Location.BODY),
            Param(name="note_events", location=Location.BODY),
            Param(name="confidential_note_events", location=Location.BODY),
            Param(name="pipeline_events", location=Location.BODY),
            Param(name="wiki_page_events", location=Location.BODY),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="notify_only_when_pipeline_status_changes", location=Location.BODY),
            Param(name="work_item_events", location=Location.BODY),
            Param(name="confidential_work_item_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable Webex Teams".
    RestOperation(
        operation_id="no-stage-assigned#disable-webex-teams-1",
        method="DELETE",
        path="/projects/:id/integrations/webex-teams",
    ),
    # "Project integrations API: Get Webex Teams settings".
    RestOperation(
        operation_id="no-stage-assigned#get-webex-teams-settings-1",
        method="GET",
        path="/projects/:id/integrations/webex-teams",
    ),
    # "Project integrations API: Set up YouTrack".
    RestOperation(
        operation_id="no-stage-assigned#set-up-youtrack-1",
        method="PUT",
        path="/projects/:id/integrations/youtrack",
        params=(
            Param(name="issues_url", location=Location.BODY, required=True),
            Param(name="project_url", location=Location.BODY, required=True),
            Param(name="use_inherited_settings", location=Location.BODY),
            Param(name="push_events", location=Location.BODY),
        ),
    ),
    # "Project integrations API: Disable YouTrack".
    RestOperation(
        operation_id="no-stage-assigned#disable-youtrack-1",
        method="DELETE",
        path="/projects/:id/integrations/youtrack",
    ),
    # "Project integrations API: Get YouTrack settings".
    RestOperation(
        operation_id="no-stage-assigned#get-youtrack-settings-1",
        method="GET",
        path="/projects/:id/integrations/youtrack",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
