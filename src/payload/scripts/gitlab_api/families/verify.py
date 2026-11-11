"""The ``verify`` endpoint family of the GitLab wrapper: CI/CD — pipelines, jobs, runners, variables, environments,
deployments, releases and clusters.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/verify.md``
(issue #13, design.md D1 and D5; issue #37): the method, the path as ``operations-index.md`` writes it, and one
``Param`` per query or body row of the table (a ``form`` row is a body row). A member row (``strategies:name``,
``assets:links``, ``platform_kubernetes_attributes[api_url]``, ``test_splits[].path``) is part of its parent's value,
not a ``Param`` of its own; a ``not[...]`` row with no ``not`` row is its own query ``Param``. The Type column gives
the ``Kind``: ``ARRAY_OF_HASHES`` for ``array of hashes``, ``array of hash`` and ``array of strategy JSON objects``,
``ARRAY`` for any other Type holding ``array``, ``HASH`` for ``hash`` and ``object``, ``SCALAR`` for every other; a
``Param`` is ``required`` where Required reads ``yes``. Every record sends a JSON body and fixes no query value. A
``GET`` section headed "List ..." pages by offset (``conventions.md`` "Pagination"), but "List pipelines", which pages
by keyset only, and "List all scopes for a runner controller", which answers one object and is not paged. The first
four records are part 1's, the ones the ``pipeline`` commands compose (design.md D6): ``pipeline status``,
``pipeline log`` and ``pipeline wait``; every other record follows in page order. A secret (a variable value, a
runner, trigger or job token) is given as ``-f`` or ``--query`` text like any other string.

The two ``*artifact_path`` downloads have their records since issue #15, and ``call`` sends each: ``registry.expand``
writes the glob with each ``/`` of its value kept and each part between them one encoded segment (issue #40, design.md
D1; issue #15 AC-4). "Add a merge request to a merge train" (``OP_ADD_A_MERGE_REQUEST_TO_A_MERGE_TRAIN``) has its
record since issue #15 too: it merges, and no subcommand sends it, so ``commands/call.py``'s ``GATED_OPERATIONS`` maps
it to ``None``, and ``call`` refuses it, ": no subcommand sends it", before any request is sent (issue #15 AC-3).
``PENDING`` is empty. A section with several endpoints ("Metadata API", "Get the latest release", "List all of a
group's runners") has one record per endpoint, all of its ID, in the order its endpoint line lists them (issue #63,
design.md D1, D8): the first, its base record, and after it each other, a copy of the base record but for its path and
any ``Param`` naming a path parameter of its own path, so both ``permalink/latest/...`` records take the base's required
``suffix_path``. ``call`` sends the base record without ``--endpoint`` and another when ``--endpoint 'GET /version'``
names it. The section "Runners API" has no record: each of its endpoints has a section and a record of its own. No
other family links any of these keys.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "verify"

# "Add a merge request to a merge train": it merges, and `commands/call.py`'s `GATED_OPERATIONS` maps it to `None`
# (issue #15 AC-3).
OP_ADD_A_MERGE_REQUEST_TO_A_MERGE_TRAIN = "verify#add-a-merge-request-to-a-merge-train"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Pipelines API: List project pipelines".
    RestOperation(
        operation_id="verify#list-project-pipelines",
        method="GET",
        path="/projects/:id/pipelines",
        params=(
            Param(name="name", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="sha", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="source", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="username", location=Location.QUERY),
            Param(name="yaml_errors", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pipelines API: Retrieve a single pipeline".
    RestOperation(
        operation_id="verify#retrieve-a-single-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id",
    ),
    # "Jobs API: List all jobs by pipeline"; `scope` is "string or array of strings", declared ARRAY so one scope
    # is sent as `scope[]=failed`.
    RestOperation(
        operation_id="verify#list-all-jobs-by-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/jobs",
        params=(
            Param(name="include_retried", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Jobs API: Retrieve a log file for a job"; the trace is plain text, which the transport returns as text.
    RestOperation(
        operation_id="verify#retrieve-a-log-file-for-a-job",
        method="GET",
        path="/projects/:id/jobs/:job_id/trace",
        params=(
            Param(name="byte_offset", location=Location.QUERY),
            Param(name="byte_limit", location=Location.QUERY),
        ),
    ),
    # "CI Lint API: Validate CI/CD configuration".
    RestOperation(
        operation_id="verify#validate-cicd-configuration",
        method="POST",
        path="/projects/:id/ci/lint",
        params=(
            Param(name="content", location=Location.BODY, required=True),
            Param(name="dry_run", location=Location.BODY),
            Param(name="include_jobs", location=Location.BODY),
            Param(name="ref", location=Location.BODY),
        ),
    ),
    # "CI Lint API: Validate existing CI/CD configuration".
    RestOperation(
        operation_id="verify#validate-existing-cicd-configuration",
        method="GET",
        path="/projects/:id/ci/lint",
        params=(
            Param(name="content_ref", location=Location.QUERY),
            Param(name="dry_run", location=Location.QUERY),
            Param(name="dry_run_ref", location=Location.QUERY),
            Param(name="include_jobs", location=Location.QUERY),
            Param(name="ref", location=Location.QUERY),
            Param(name="sha", location=Location.QUERY),
        ),
    ),
    # "CI/CD templates API: List all CI/CD templates".
    RestOperation(
        operation_id="verify#list-all-cicd-templates",
        method="GET",
        path="/templates/gitlab_ci_ymls",
        paging=Paging.OFFSET,
    ),
    # "CI/CD templates API: Retrieve details of a CI/CD template".
    RestOperation(
        operation_id="verify#retrieve-details-of-a-cicd-template",
        method="GET",
        path="/templates/gitlab_ci_ymls/:key",
    ),
    # "Cluster discovery API (certificate-based) (deprecated): Retrieve certificate-based clusters".
    RestOperation(
        operation_id="verify#retrieve-certificate-based-clusters",
        method="GET",
        path="/discover-cert-based-clusters",
        params=(Param(name="group_id", location=Location.QUERY, required=True),),
    ),
    # "Deploy keys API: List all deploy keys".
    RestOperation(
        operation_id="verify#list-all-deploy-keys",
        method="GET",
        path="/deploy_keys",
        params=(
            Param(name="public", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deploy keys API: Add deploy key".
    RestOperation(
        operation_id="verify#add-deploy-key",
        method="POST",
        path="/deploy_keys",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Deploy keys API: List deploy keys for project".
    RestOperation(
        operation_id="verify#list-deploy-keys-for-project",
        method="GET",
        path="/projects/:id/deploy_keys",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deploy keys API: List project deploy keys for user".
    RestOperation(
        operation_id="verify#list-project-deploy-keys-for-user",
        method="GET",
        path="/users/:id_or_username/project_deploy_keys",
        paging=Paging.OFFSET,
    ),
    # "Deploy keys API: Retrieve a deploy key".
    RestOperation(
        operation_id="verify#retrieve-a-deploy-key",
        method="GET",
        path="/projects/:id/deploy_keys/:key_id",
    ),
    # "Deploy keys API: Add a deploy key for a project".
    RestOperation(
        operation_id="verify#add-a-deploy-key-for-a-project",
        method="POST",
        path="/projects/:id/deploy_keys",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="title", location=Location.BODY, required=True),
            Param(name="can_push", location=Location.BODY),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Deploy keys API: Update a deploy key".
    RestOperation(
        operation_id="verify#update-a-deploy-key",
        method="PUT",
        path="/projects/:id/deploy_keys/:key_id",
        params=(
            Param(name="can_push", location=Location.BODY),
            Param(name="title", location=Location.BODY),
        ),
    ),
    # "Deploy keys API: Delete a deploy key".
    RestOperation(
        operation_id="verify#delete-a-deploy-key",
        method="DELETE",
        path="/projects/:id/deploy_keys/:key_id",
    ),
    # "Deploy keys API: Enable a deploy key".
    RestOperation(
        operation_id="verify#enable-a-deploy-key",
        method="POST",
        path="/projects/:id/deploy_keys/:key_id/enable",
    ),
    # "Deploy tokens API: List all deploy tokens".
    RestOperation(
        operation_id="verify#list-all-deploy-tokens",
        method="GET",
        path="/deploy_tokens",
        params=(
            Param(name="active", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deploy tokens API: List project deploy tokens".
    RestOperation(
        operation_id="verify#list-project-deploy-tokens",
        method="GET",
        path="/projects/:id/deploy_tokens",
        params=(
            Param(name="active", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deploy tokens API: Retrieve a project deploy token".
    RestOperation(
        operation_id="verify#retrieve-a-project-deploy-token",
        method="GET",
        path="/projects/:id/deploy_tokens/:token_id",
    ),
    # "Deploy tokens API: Create a project deploy token".
    RestOperation(
        operation_id="verify#create-a-project-deploy-token",
        method="POST",
        path="/projects/:id/deploy_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Deploy tokens API: Delete a project deploy token".
    RestOperation(
        operation_id="verify#delete-a-project-deploy-token",
        method="DELETE",
        path="/projects/:id/deploy_tokens/:token_id",
    ),
    # "Deploy tokens API: List group deploy tokens".
    RestOperation(
        operation_id="verify#list-group-deploy-tokens",
        method="GET",
        path="/groups/:id/deploy_tokens",
        params=(
            Param(name="active", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deploy tokens API: Retrieve a group deploy token".
    RestOperation(
        operation_id="verify#retrieve-a-group-deploy-token",
        method="GET",
        path="/groups/:id/deploy_tokens/:token_id",
    ),
    # "Deploy tokens API: Create a group deploy token".
    RestOperation(
        operation_id="verify#create-a-group-deploy-token",
        method="POST",
        path="/groups/:id/deploy_tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="scopes", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="expires_at", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Deploy tokens API: Delete a group deploy token".
    RestOperation(
        operation_id="verify#delete-a-group-deploy-token",
        method="DELETE",
        path="/groups/:id/deploy_tokens/:token_id",
    ),
    # "Deployments API: List all project deployments".
    RestOperation(
        operation_id="verify#list-all-project-deployments",
        method="GET",
        path="/projects/:id/deployments",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="finished_after", location=Location.QUERY),
            Param(name="finished_before", location=Location.QUERY),
            Param(name="environment", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deployments API: Retrieve a deployment".
    RestOperation(
        operation_id="verify#retrieve-a-deployment",
        method="GET",
        path="/projects/:id/deployments/:deployment_id",
    ),
    # "Deployments API: Create a deployment".
    RestOperation(
        operation_id="verify#create-a-deployment",
        method="POST",
        path="/projects/:id/deployments",
        params=(
            Param(name="environment", location=Location.BODY, required=True),
            Param(name="sha", location=Location.BODY, required=True),
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="tag", location=Location.BODY, required=True),
            Param(name="status", location=Location.BODY, required=True),
        ),
    ),
    # "Deployments API: Update a deployment".
    RestOperation(
        operation_id="verify#update-a-deployment",
        method="PUT",
        path="/projects/:id/deployments/:deployment_id",
        params=(Param(name="status", location=Location.BODY, required=True),),
    ),
    # "Deployments API: Delete a deployment".
    RestOperation(
        operation_id="verify#delete-a-deployment",
        method="DELETE",
        path="/projects/:id/deployments/:deployment_id",
    ),
    # "Deployments API: List all merge requests associated with a deployment".
    RestOperation(
        operation_id="verify#list-all-merge-requests-associated-with-a-deployment",
        method="GET",
        path="/projects/:id/deployments/:deployment_id/merge_requests",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="author_id", location=Location.QUERY),
            Param(name="author_username", location=Location.QUERY),
            Param(name="assignee_id", location=Location.QUERY),
            Param(name="assignee_username", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="reviewer_username", location=Location.QUERY),
            Param(name="labels", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="milestone", location=Location.QUERY),
            Param(name="my_reaction_emoji", location=Location.QUERY),
            Param(name="reviewer_id", location=Location.QUERY),
            Param(name="state", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="with_labels_details", location=Location.QUERY),
            Param(name="with_merge_status_recheck", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="merged_after", location=Location.QUERY),
            Param(name="merged_before", location=Location.QUERY),
            Param(name="view", location=Location.QUERY),
            Param(name="scope", location=Location.QUERY),
            Param(name="source_branch", location=Location.QUERY),
            Param(name="source_project_id", location=Location.QUERY),
            Param(name="target_branch", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="in", location=Location.QUERY),
            Param(name="wip", location=Location.QUERY),
            Param(name="draft", location=Location.QUERY),
            Param(name="not[author_id]", location=Location.QUERY),
            Param(name="not[author_username]", location=Location.QUERY),
            Param(name="not[assignee_id]", location=Location.QUERY),
            Param(name="not[assignee_username]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[reviewer_username]", location=Location.QUERY),
            Param(name="not[labels]", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="not[milestone]", location=Location.QUERY),
            Param(name="not[my_reaction_emoji]", location=Location.QUERY),
            Param(name="not[reviewer_id]", location=Location.QUERY),
            Param(name="deployed_before", location=Location.QUERY),
            Param(name="deployed_after", location=Location.QUERY),
            Param(name="environment", location=Location.QUERY),
            Param(name="merge_user_id", location=Location.QUERY),
            Param(name="merge_user_username", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Deployments API: Approve or reject a deployment".
    RestOperation(
        operation_id="verify#approve-or-reject-a-deployment",
        method="POST",
        path="/projects/:id/deployments/:deployment_id/approval",
        params=(
            Param(name="status", location=Location.BODY, required=True),
            Param(name="comment", location=Location.BODY),
            Param(name="represented_as", location=Location.BODY),
        ),
    ),
    # "Environments API: List all environments".
    RestOperation(
        operation_id="verify#list-all-environments",
        method="GET",
        path="/projects/:id/environments",
        params=(
            Param(name="name", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
            Param(name="states", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Environments API: Retrieve an environment".
    RestOperation(
        operation_id="verify#retrieve-an-environment",
        method="GET",
        path="/projects/:id/environments/:environment_id",
    ),
    # "Environments API: Create an environment".
    RestOperation(
        operation_id="verify#create-an-environment",
        method="POST",
        path="/projects/:id/environments",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="external_url", location=Location.BODY),
            Param(name="tier", location=Location.BODY),
            Param(name="cluster_agent_id", location=Location.BODY),
            Param(name="kubernetes_namespace", location=Location.BODY),
            Param(name="flux_resource_path", location=Location.BODY),
            Param(name="auto_stop_setting", location=Location.BODY),
        ),
    ),
    # "Environments API: Update an existing environment".
    RestOperation(
        operation_id="verify#update-an-existing-environment",
        method="PUT",
        path="/projects/:id/environments/:environments_id",
        params=(
            Param(name="environment_id", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="external_url", location=Location.BODY),
            Param(name="tier", location=Location.BODY),
            Param(name="cluster_agent_id", location=Location.BODY),
            Param(name="kubernetes_namespace", location=Location.BODY),
            Param(name="flux_resource_path", location=Location.BODY),
            Param(name="auto_stop_setting", location=Location.BODY),
        ),
    ),
    # "Environments API: Delete an environment".
    RestOperation(
        operation_id="verify#delete-an-environment",
        method="DELETE",
        path="/projects/:id/environments/:environment_id",
    ),
    # "Environments API: Delete multiple stopped review apps".
    RestOperation(
        operation_id="verify#delete-multiple-stopped-review-apps",
        method="DELETE",
        path="/projects/:id/environments/review_apps",
        params=(
            Param(name="before", location=Location.QUERY),
            Param(name="limit", location=Location.QUERY),
            Param(name="dry_run", location=Location.QUERY),
        ),
    ),
    # "Environments API: Stop an environment".
    RestOperation(
        operation_id="verify#stop-an-environment",
        method="POST",
        path="/projects/:id/environments/:environment_id/stop",
        params=(Param(name="force", location=Location.BODY),),
    ),
    # "Environments API: Stop stale environments".
    RestOperation(
        operation_id="verify#stop-stale-environments",
        method="POST",
        path="/projects/:id/environments/stop_stale",
        params=(Param(name="before", location=Location.BODY, required=True),),
    ),
    # "Feature flag API: List feature flags for a project".
    RestOperation(
        operation_id="verify#list-feature-flags-for-a-project",
        method="GET",
        path="/projects/:id/feature_flags",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Feature flag API: Retrieve a feature flag".
    RestOperation(
        operation_id="verify#retrieve-a-feature-flag",
        method="GET",
        path="/projects/:id/feature_flags/:feature_flag_name",
    ),
    # "Feature flag API: Create a feature flag".
    RestOperation(
        operation_id="verify#create-a-feature-flag",
        method="POST",
        path="/projects/:id/feature_flags",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="version", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="active", location=Location.BODY),
            Param(name="strategies", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Feature flag API: Update a feature flag".
    RestOperation(
        operation_id="verify#update-a-feature-flag",
        method="PUT",
        path="/projects/:id/feature_flags/:feature_flag_name",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="active", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="strategies", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Feature flag API: Delete a feature flag".
    RestOperation(
        operation_id="verify#delete-a-feature-flag",
        method="DELETE",
        path="/projects/:id/feature_flags/:feature_flag_name",
    ),
    # "Feature flag API: Retrieve feature flag settings".
    RestOperation(
        operation_id="verify#retrieve-feature-flag-settings",
        method="GET",
        path="/projects/:id/feature_flags_settings",
    ),
    # "Feature flag API: Update feature flag settings".
    RestOperation(
        operation_id="verify#update-feature-flag-settings",
        method="PUT",
        path="/projects/:id/feature_flags_settings",
        params=(Param(name="minimum_role", location=Location.BODY, required=True),),
    ),
    # "Feature flag user lists API: List all feature flag user lists for a project".
    RestOperation(
        operation_id="verify#list-all-feature-flag-user-lists-for-a-project",
        method="GET",
        path="/projects/:id/feature_flags_user_lists",
        params=(
            Param(name="search", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Feature flag user lists API: Create a feature flag user list".
    RestOperation(
        operation_id="verify#create-a-feature-flag-user-list",
        method="POST",
        path="/projects/:id/feature_flags_user_lists",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="user_xids", location=Location.BODY, required=True),
        ),
    ),
    # "Feature flag user lists API: Retrieve a feature flag user list".
    RestOperation(
        operation_id="verify#retrieve-a-feature-flag-user-list",
        method="GET",
        path="/projects/:id/feature_flags_user_lists/:iid",
    ),
    # "Feature flag user lists API: Update a feature flag user list".
    RestOperation(
        operation_id="verify#update-a-feature-flag-user-list",
        method="PUT",
        path="/projects/:id/feature_flags_user_lists/:iid",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="user_xids", location=Location.BODY),
        ),
    ),
    # "Feature flag user lists API: Delete feature flag user list".
    RestOperation(
        operation_id="verify#delete-feature-flag-user-list",
        method="DELETE",
        path="/projects/:id/feature_flags_user_lists/:iid",
    ),
    # "Feature flags API: List all feature flags".
    RestOperation(
        operation_id="verify#list-all-feature-flags",
        method="GET",
        path="/features",
        paging=Paging.OFFSET,
    ),
    # "Feature flags API: List all feature flag definitions".
    RestOperation(
        operation_id="verify#list-all-feature-flag-definitions",
        method="GET",
        path="/features/definitions",
        paging=Paging.OFFSET,
    ),
    # "Feature flags API: Create or update a feature flag".
    RestOperation(
        operation_id="verify#create-or-update-a-feature-flag",
        method="POST",
        path="/features/:name",
        params=(
            Param(name="value", location=Location.BODY, required=True),
            Param(name="key", location=Location.BODY),
            Param(name="feature_group", location=Location.BODY),
            Param(name="user", location=Location.BODY),
            Param(name="group", location=Location.BODY),
            Param(name="namespace", location=Location.BODY),
            Param(name="project", location=Location.BODY),
            Param(name="organization", location=Location.BODY),
            Param(name="repository", location=Location.BODY),
            Param(name="runner", location=Location.BODY),
            Param(name="force", location=Location.BODY),
            Param(name="endpoint", location=Location.BODY),
        ),
    ),
    # "Feature flags API: Set percentage of actors rollout".
    RestOperation(
        operation_id="verify#set-percentage-of-actors-rollout",
        method="POST",
        path="/features/my_user_feature",
    ),
    # "Feature flags API: Delete a feature".
    RestOperation(
        operation_id="verify#delete-a-feature",
        method="DELETE",
        path="/features/:name",
    ),
    # "Freeze Periods API: List freeze periods".
    RestOperation(
        operation_id="verify#list-freeze-periods",
        method="GET",
        path="/projects/:id/freeze_periods",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Freeze Periods API: Retrieve a freeze period".
    RestOperation(
        operation_id="verify#retrieve-a-freeze-period",
        method="GET",
        path="/projects/:id/freeze_periods/:freeze_period_id",
    ),
    # "Freeze Periods API: Create a freeze period".
    RestOperation(
        operation_id="verify#create-a-freeze-period",
        method="POST",
        path="/projects/:id/freeze_periods",
        params=(
            Param(name="freeze_start", location=Location.BODY, required=True),
            Param(name="freeze_end", location=Location.BODY, required=True),
            Param(name="cron_timezone", location=Location.BODY),
        ),
    ),
    # "Freeze Periods API: Update a freeze period".
    RestOperation(
        operation_id="verify#update-a-freeze-period",
        method="PUT",
        path="/projects/:id/freeze_periods/:freeze_period_id",
        params=(
            Param(name="freeze_start", location=Location.BODY),
            Param(name="freeze_end", location=Location.BODY),
            Param(name="cron_timezone", location=Location.BODY),
        ),
    ),
    # "Freeze Periods API: Delete a freeze period".
    RestOperation(
        operation_id="verify#delete-a-freeze-period",
        method="DELETE",
        path="/projects/:id/freeze_periods/:freeze_period_id",
    ),
    # "Group clusters API (certificate-based) (deprecated): List group clusters".
    RestOperation(
        operation_id="verify#list-group-clusters",
        method="GET",
        path="/groups/:id/clusters",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group clusters API (certificate-based) (deprecated): Retrieve a group cluster".
    RestOperation(
        operation_id="verify#retrieve-a-group-cluster",
        method="GET",
        path="/groups/:id/clusters/:cluster_id",
    ),
    # "Group clusters API (certificate-based) (deprecated): Create a group cluster".
    RestOperation(
        operation_id="verify#create-a-group-cluster",
        method="POST",
        path="/groups/:id/clusters/user",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="domain", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "Group clusters API (certificate-based) (deprecated): Update a group cluster".
    RestOperation(
        operation_id="verify#update-a-group-cluster",
        method="PUT",
        path="/groups/:id/clusters/:cluster_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="domain", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Group clusters API (certificate-based) (deprecated): Delete a group cluster".
    RestOperation(
        operation_id="verify#delete-a-group-cluster",
        method="DELETE",
        path="/groups/:id/clusters/:cluster_id",
    ),
    # "Group release API: List all releases in a group".
    RestOperation(
        operation_id="verify#list-all-releases-in-a-group",
        method="GET",
        path="/groups/:id/releases",
        params=(
            Param(name="sort", location=Location.QUERY),
            Param(name="simple", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group-level protected environments API: List all group-level protected environments".
    RestOperation(
        operation_id="verify#list-all-group-level-protected-environments",
        method="GET",
        path="/groups/:id/protected_environments",
        paging=Paging.OFFSET,
    ),
    # "Group-level protected environments API: Retrieve a single protected environment".
    RestOperation(
        operation_id="verify#retrieve-a-single-protected-environment",
        method="GET",
        path="/groups/:id/protected_environments/:name",
    ),
    # "Group-level protected environments API: Protect a single environment".
    RestOperation(
        operation_id="verify#protect-a-single-environment",
        method="POST",
        path="/groups/:id/protected_environments",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="deploy_access_levels", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="approval_rules", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Group-level protected environments API: Update a protected environment".
    RestOperation(
        operation_id="verify#update-a-protected-environment",
        method="PUT",
        path="/groups/:id/protected_environments/:name",
        params=(
            Param(name="deploy_access_levels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="required_approval_count", location=Location.BODY),
            Param(name="approval_rules", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Group-level protected environments API: Unprotect a single environment".
    RestOperation(
        operation_id="verify#unprotect-a-single-environment",
        method="DELETE",
        path="/groups/:id/protected_environments/:name",
    ),
    # "Group-level Variables API: List all group variables".
    RestOperation(
        operation_id="verify#list-all-group-variables",
        method="GET",
        path="/groups/:id/variables",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Group-level Variables API: Retrieve details of a group variable".
    RestOperation(
        operation_id="verify#retrieve-details-of-a-group-variable",
        method="GET",
        path="/groups/:id/variables/:key",
        params=(Param(name="filter", location=Location.QUERY, kind=Kind.HASH),),
    ),
    # "Group-level Variables API: Create a group variable".
    RestOperation(
        operation_id="verify#create-a-group-variable",
        method="POST",
        path="/groups/:id/variables",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="value", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="masked", location=Location.BODY),
            Param(name="masked_and_hidden", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Group-level Variables API: Update a group variable".
    RestOperation(
        operation_id="verify#update-a-group-variable",
        method="PUT",
        path="/groups/:id/variables/:key",
        params=(
            Param(name="value", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="filter", location=Location.BODY, kind=Kind.HASH),
            Param(name="masked", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Group-level Variables API: Delete a group variable".
    RestOperation(
        operation_id="verify#delete-a-group-variable",
        method="DELETE",
        path="/groups/:id/variables/:key",
        params=(Param(name="filter", location=Location.QUERY, kind=Kind.HASH),),
    ),
    # "Instance clusters API (certificate-based) (deprecated): List instance clusters".
    RestOperation(
        operation_id="verify#list-instance-clusters",
        method="GET",
        path="/admin/clusters",
        paging=Paging.OFFSET,
    ),
    # "Instance clusters API (certificate-based) (deprecated): Retrieve a single instance cluster".
    RestOperation(
        operation_id="verify#retrieve-a-single-instance-cluster",
        method="GET",
        path="/admin/clusters/:cluster_id",
    ),
    # "Instance clusters API (certificate-based) (deprecated): Create an instance cluster".
    RestOperation(
        operation_id="verify#create-an-instance-cluster",
        method="POST",
        path="/admin/clusters/add",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="domain", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "Instance clusters API (certificate-based) (deprecated): Update an instance cluster".
    RestOperation(
        operation_id="verify#update-an-instance-cluster",
        method="PUT",
        path="/admin/clusters/:cluster_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="domain", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Instance clusters API (certificate-based) (deprecated): Delete instance cluster".
    RestOperation(
        operation_id="verify#delete-instance-cluster",
        method="DELETE",
        path="/admin/clusters/:cluster_id",
    ),
    # "Instance-level CI/CD variables API: List all instance variables".
    RestOperation(
        operation_id="verify#list-all-instance-variables",
        method="GET",
        path="/admin/ci/variables",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Instance-level CI/CD variables API: Retrieve instance variable details".
    RestOperation(
        operation_id="verify#retrieve-instance-variable-details",
        method="GET",
        path="/admin/ci/variables/:key",
    ),
    # "Instance-level CI/CD variables API: Create instance variable".
    RestOperation(
        operation_id="verify#create-instance-variable",
        method="POST",
        path="/admin/ci/variables",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="value", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="masked", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Instance-level CI/CD variables API: Update instance variable".
    RestOperation(
        operation_id="verify#update-instance-variable",
        method="PUT",
        path="/admin/ci/variables/:key",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="masked", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="value", location=Location.BODY, required=True),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Instance-level CI/CD variables API: Delete instance variable".
    RestOperation(
        operation_id="verify#delete-instance-variable",
        method="DELETE",
        path="/admin/ci/variables/:key",
    ),
    # "Job Artifacts API: Download job artifacts by job ID".
    RestOperation(
        operation_id="verify#download-job-artifacts-by-job-id",
        method="GET",
        path="/projects/:id/jobs/:job_id/artifacts",
        params=(
            Param(name="file_type", location=Location.QUERY),
            Param(name="job_token", location=Location.QUERY),
        ),
    ),
    # "Job Artifacts API: Download job artifacts by reference name".
    RestOperation(
        operation_id="verify#download-job-artifacts-by-reference-name",
        method="GET",
        path="/projects/:id/jobs/artifacts/:ref_name/download",
        params=(
            Param(name="job", location=Location.QUERY, required=True),
            Param(name="job_token", location=Location.QUERY),
            Param(name="search_recent_successful_pipelines", location=Location.QUERY),
        ),
    ),
    # "Job Artifacts API: Download a single artifact file by job ID"; `*artifact_path` is a glob, its value's `/` kept.
    RestOperation(
        operation_id="verify#download-a-single-artifact-file-by-job-id",
        method="GET",
        path="/projects/:id/jobs/:job_id/artifacts/*artifact_path",
        params=(Param(name="job_token", location=Location.QUERY),),
    ),
    # "Job Artifacts API: List all files in the artifacts archive".
    RestOperation(
        operation_id="verify#list-all-files-in-the-artifacts-archive",
        method="GET",
        path="/projects/:id/jobs/:job_id/artifacts/tree",
        params=(
            Param(name="path", location=Location.QUERY),
            Param(name="recursive", location=Location.QUERY),
            Param(name="job_token", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Job Artifacts API: Download a single artifact file by reference name"; `*artifact_path` is a glob, its value's
    # `/` kept.
    RestOperation(
        operation_id="verify#download-a-single-artifact-file-by-reference-name",
        method="GET",
        path="/projects/:id/jobs/artifacts/:ref_name/raw/*artifact_path",
        params=(
            Param(name="job", location=Location.QUERY, required=True),
            Param(name="job_token", location=Location.QUERY),
            Param(name="search_recent_successful_pipelines", location=Location.QUERY),
        ),
    ),
    # "Job Artifacts API: Keep job artifacts".
    RestOperation(
        operation_id="verify#keep-job-artifacts",
        method="POST",
        path="/projects/:id/jobs/:job_id/artifacts/keep",
    ),
    # "Job Artifacts API: Delete job artifacts".
    RestOperation(
        operation_id="verify#delete-job-artifacts",
        method="DELETE",
        path="/projects/:id/jobs/:job_id/artifacts",
    ),
    # "Job Artifacts API: Delete all job artifacts in a project".
    RestOperation(
        operation_id="verify#delete-all-job-artifacts-in-a-project",
        method="DELETE",
        path="/projects/:id/artifacts",
    ),
    # "Jobs API: List all jobs for a project".
    RestOperation(
        operation_id="verify#list-all-jobs-for-a-project",
        method="GET",
        path="/projects/:id/jobs",
        params=(
            Param(name="scope", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="ref", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Jobs API: List all trigger jobs by pipeline".
    RestOperation(
        operation_id="verify#list-all-trigger-jobs-by-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/trigger_jobs",
        params=(
            Param(name="scope", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Jobs API: Retrieve a job by job token".
    RestOperation(
        operation_id="verify#retrieve-a-job-by-job-token",
        method="GET",
        path="/job",
    ),
    # "Jobs API: Retrieve GitLab agent for Kubernetes by `CI_JOB_TOKEN`".
    RestOperation(
        operation_id="verify#retrieve-gitlab-agent-for-kubernetes-by-ci_job_token",
        method="GET",
        path="/job/allowed_agents",
        params=(Param(name="CI_JOB_TOKEN", location=Location.QUERY, required=True),),
    ),
    # "Jobs API: Retrieve a job by job ID".
    RestOperation(
        operation_id="verify#retrieve-a-job-by-job-id",
        method="GET",
        path="/projects/:id/jobs/:job_id",
    ),
    # "Jobs API: Cancel a job".
    RestOperation(
        operation_id="verify#cancel-a-job",
        method="POST",
        path="/projects/:id/jobs/:job_id/cancel",
        params=(Param(name="force", location=Location.BODY),),
    ),
    # "Jobs API: Retry a job".
    RestOperation(
        operation_id="verify#retry-a-job",
        method="POST",
        path="/projects/:id/jobs/:job_id/retry",
        params=(
            Param(name="job_inputs", location=Location.BODY, kind=Kind.HASH),
            Param(name="inputs", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Jobs API: Erase a job".
    RestOperation(
        operation_id="verify#erase-a-job",
        method="POST",
        path="/projects/:id/jobs/:job_id/erase",
    ),
    # "Jobs API: Run a job".
    RestOperation(
        operation_id="verify#run-a-job",
        method="POST",
        path="/projects/:id/jobs/:job_id/play",
        params=(
            Param(name="job_inputs", location=Location.BODY, kind=Kind.HASH),
            Param(name="job_variables_attributes", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES),
        ),
    ),
    # "Kubernetes agent API: List all agents".
    RestOperation(
        operation_id="verify#list-all-agents",
        method="GET",
        path="/projects/:id/cluster_agents",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Kubernetes agent API: Retrieve an agent".
    RestOperation(
        operation_id="verify#retrieve-an-agent",
        method="GET",
        path="/projects/:id/cluster_agents/:agent_id",
    ),
    # "Kubernetes agent API: Create an agent".
    RestOperation(
        operation_id="verify#create-an-agent",
        method="POST",
        path="/projects/:id/cluster_agents",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "Kubernetes agent API: Delete an agent".
    RestOperation(
        operation_id="verify#delete-an-agent",
        method="DELETE",
        path="/projects/:id/cluster_agents/:agent_id",
    ),
    # "Kubernetes agent API: List all agent tokens".
    RestOperation(
        operation_id="verify#list-all-agent-tokens",
        method="GET",
        path="/projects/:id/cluster_agents/:agent_id/tokens",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Kubernetes agent API: Retrieve an agent token".
    RestOperation(
        operation_id="verify#retrieve-an-agent-token",
        method="GET",
        path="/projects/:id/cluster_agents/:agent_id/tokens/:token_id",
    ),
    # "Kubernetes agent API: Create an agent token".
    RestOperation(
        operation_id="verify#create-an-agent-token",
        method="POST",
        path="/projects/:id/cluster_agents/:agent_id/tokens",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
        ),
    ),
    # "Kubernetes agent API: Revoke an agent token".
    RestOperation(
        operation_id="verify#revoke-an-agent-token",
        method="DELETE",
        path="/projects/:id/cluster_agents/:agent_id/tokens/:token_id",
    ),
    # "Kubernetes agent API: List all URL configurations".
    RestOperation(
        operation_id="verify#list-all-url-configurations",
        method="GET",
        path="/projects/:id/cluster_agents/:agent_id/url_configurations",
        paging=Paging.OFFSET,
    ),
    # "Kubernetes agent API: Retrieve a URL configuration".
    RestOperation(
        operation_id="verify#retrieve-a-url-configuration",
        method="GET",
        path="/projects/:id/cluster_agents/:agent_id/url_configurations/:url_configuration_id",
    ),
    # "Kubernetes agent API: Create a URL configuration".
    RestOperation(
        operation_id="verify#create-a-url-configuration",
        method="POST",
        path="/projects/:id/cluster_agents/:agent_id/url_configurations",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="client_cert", location=Location.BODY),
            Param(name="client_key", location=Location.BODY),
            Param(name="ca_cert", location=Location.BODY),
            Param(name="tls_host", location=Location.BODY),
        ),
    ),
    # "Kubernetes agent API: Delete a URL configuration".
    RestOperation(
        operation_id="verify#delete-a-url-configuration",
        method="DELETE",
        path="/projects/:id/cluster_agents/:agent_id/url_configurations/:url_configuration_id",
    ),
    # "Merge trains API: List all merge trains for a project".
    RestOperation(
        operation_id="verify#list-all-merge-trains-for-a-project",
        method="GET",
        path="/projects/:id/merge_trains",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge trains API: List all merge requests in a merge train".
    RestOperation(
        operation_id="verify#list-all-merge-requests-in-a-merge-train",
        method="GET",
        path="/projects/:id/merge_trains/:target_branch",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Merge trains API: Retrieve merge train status".
    RestOperation(
        operation_id="verify#retrieve-merge-train-status",
        method="GET",
        path="/projects/:id/merge_trains/merge_requests/:merge_request_iid",
    ),
    # "Merge trains API: Add a merge request to a merge train".
    RestOperation(
        operation_id=OP_ADD_A_MERGE_REQUEST_TO_A_MERGE_TRAIN,
        method="POST",
        path="/projects/:id/merge_trains/merge_requests/:merge_request_iid",
        params=(
            Param(name="auto_merge", location=Location.BODY),
            Param(name="sha", location=Location.BODY),
            Param(name="squash", location=Location.BODY),
            Param(name="when_pipeline_succeeds", location=Location.BODY),
        ),
    ),
    # "Metadata API: Metadata API"; the base record, the first of its two endpoints.
    RestOperation(
        operation_id="verify#metadata-api-1",
        method="GET",
        path="/metadata",
    ),
    # "Metadata API: Metadata API"; its second endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="verify#metadata-api-1",
        method="GET",
        path="/version",
    ),
    # "Pipeline schedules API: List all pipeline schedules".
    RestOperation(
        operation_id="verify#list-all-pipeline-schedules",
        method="GET",
        path="/projects/:id/pipeline_schedules",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pipeline schedules API: Retrieve a pipeline schedule".
    RestOperation(
        operation_id="verify#retrieve-a-pipeline-schedule",
        method="GET",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id",
    ),
    # "Pipeline schedules API: List all pipelines triggered by a pipeline schedule".
    RestOperation(
        operation_id="verify#list-all-pipelines-triggered-by-a-pipeline-schedule",
        method="GET",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/pipelines",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pipeline schedules API: Create a new pipeline schedule".
    RestOperation(
        operation_id="verify#create-a-new-pipeline-schedule",
        method="POST",
        path="/projects/:id/pipeline_schedules",
        params=(
            Param(name="cron", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY, required=True),
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="active", location=Location.BODY),
            Param(name="cron_timezone", location=Location.BODY),
            Param(name="inputs", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Pipeline schedules API: Update a pipeline schedule".
    RestOperation(
        operation_id="verify#update-a-pipeline-schedule",
        method="PUT",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id",
        params=(
            Param(name="active", location=Location.BODY),
            Param(name="cron_timezone", location=Location.BODY),
            Param(name="cron", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="ref", location=Location.BODY),
            Param(name="inputs", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Pipeline schedules API: Update ownership of a pipeline schedule".
    RestOperation(
        operation_id="verify#update-ownership-of-a-pipeline-schedule",
        method="POST",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/take_ownership",
    ),
    # "Pipeline schedules API: Delete a pipeline schedule".
    RestOperation(
        operation_id="verify#delete-a-pipeline-schedule",
        method="DELETE",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id",
    ),
    # "Pipeline schedules API: Run a pipeline schedule immediately".
    RestOperation(
        operation_id="verify#run-a-pipeline-schedule-immediately",
        method="POST",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/play",
    ),
    # "Pipeline schedules API: Create a variable for a pipeline schedule".
    RestOperation(
        operation_id="verify#create-a-variable-for-a-pipeline-schedule",
        method="POST",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/variables",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="value", location=Location.BODY, required=True),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Pipeline schedules API: Retrieve a variable for a pipeline schedule".
    RestOperation(
        operation_id="verify#retrieve-a-variable-for-a-pipeline-schedule",
        method="GET",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/variables/:key",
    ),
    # "Pipeline schedules API: Update a variable for a pipeline schedule".
    RestOperation(
        operation_id="verify#update-a-variable-for-a-pipeline-schedule",
        method="PUT",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/variables/:key",
        params=(
            Param(name="value", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Pipeline schedules API: Delete a variable for a pipeline schedule".
    RestOperation(
        operation_id="verify#delete-a-variable-for-a-pipeline-schedule",
        method="DELETE",
        path="/projects/:id/pipeline_schedules/:pipeline_schedule_id/variables/:key",
    ),
    # "Pipeline trigger tokens API: List project trigger tokens".
    RestOperation(
        operation_id="verify#list-project-trigger-tokens",
        method="GET",
        path="/projects/:id/triggers",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Pipeline trigger tokens API: Retrieve trigger token details".
    RestOperation(
        operation_id="verify#retrieve-trigger-token-details",
        method="GET",
        path="/projects/:id/triggers/:trigger_id",
    ),
    # "Pipeline trigger tokens API: Create a trigger token".
    RestOperation(
        operation_id="verify#create-a-trigger-token",
        method="POST",
        path="/projects/:id/triggers",
        params=(
            Param(name="description", location=Location.BODY, required=True),
            Param(name="expires_at", location=Location.BODY),
        ),
    ),
    # "Pipeline trigger tokens API: Update a pipeline trigger token".
    RestOperation(
        operation_id="verify#update-a-pipeline-trigger-token",
        method="PUT",
        path="/projects/:id/triggers/:trigger_id",
        params=(Param(name="description", location=Location.BODY),),
    ),
    # "Pipeline trigger tokens API: Delete a pipeline trigger token".
    RestOperation(
        operation_id="verify#delete-a-pipeline-trigger-token",
        method="DELETE",
        path="/projects/:id/triggers/:trigger_id",
    ),
    # "Pipeline trigger tokens API: Trigger a pipeline with a token".
    RestOperation(
        operation_id="verify#trigger-a-pipeline-with-a-token",
        method="POST",
        path="/projects/:id/trigger/pipeline",
        params=(
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="token", location=Location.BODY, required=True),
            Param(name="variables", location=Location.BODY, kind=Kind.HASH),
            Param(name="inputs", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Pipelines API: List pipelines"; keyset paging only (conventions.md "Keyset-based").
    RestOperation(
        operation_id="verify#list-pipelines",
        method="GET",
        path="/pipelines",
        params=(
            Param(name="created_after", location=Location.QUERY),
            Param(name="created_before", location=Location.QUERY),
            Param(name="cursor", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="source", location=Location.QUERY),
        ),
        paging=Paging.KEYSET,
    ),
    # "Pipelines API: Retrieve the latest pipeline".
    RestOperation(
        operation_id="verify#retrieve-the-latest-pipeline",
        method="GET",
        path="/projects/:id/pipelines/latest",
        params=(Param(name="ref", location=Location.QUERY),),
    ),
    # "Pipelines API: Retrieve pipeline variables".
    RestOperation(
        operation_id="verify#retrieve-pipeline-variables",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/variables",
    ),
    # "Pipelines API: Retrieve a test report for a pipeline".
    RestOperation(
        operation_id="verify#retrieve-a-test-report-for-a-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/test_report",
    ),
    # "Pipelines API: Retrieve a test report summary for a pipeline".
    RestOperation(
        operation_id="verify#retrieve-a-test-report-summary-for-a-pipeline",
        method="GET",
        path="/projects/:id/pipelines/:pipeline_id/test_report_summary",
    ),
    # "Pipelines API: Create a new pipeline".
    RestOperation(
        operation_id="verify#create-a-new-pipeline",
        method="POST",
        path="/projects/:id/pipeline",
        params=(
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="variables", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="inputs", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Pipelines API: Retry jobs in a pipeline".
    RestOperation(
        operation_id="verify#retry-jobs-in-a-pipeline",
        method="POST",
        path="/projects/:id/pipelines/:pipeline_id/retry",
    ),
    # "Pipelines API: Cancel all jobs for a pipeline".
    RestOperation(
        operation_id="verify#cancel-all-jobs-for-a-pipeline",
        method="POST",
        path="/projects/:id/pipelines/:pipeline_id/cancel",
    ),
    # "Pipelines API: Delete a pipeline".
    RestOperation(
        operation_id="verify#delete-a-pipeline",
        method="DELETE",
        path="/projects/:id/pipelines/:pipeline_id",
    ),
    # "Pipelines API: Update pipeline metadata".
    RestOperation(
        operation_id="verify#update-pipeline-metadata",
        method="PUT",
        path="/projects/:id/pipelines/:pipeline_id/metadata",
        params=(Param(name="name", location=Location.BODY, required=True),),
    ),
    # "Project clusters API (certificate-based) (deprecated): List all clusters in a project".
    RestOperation(
        operation_id="verify#list-all-clusters-in-a-project",
        method="GET",
        path="/projects/:id/clusters",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project clusters API (certificate-based) (deprecated): Retrieve a cluster from a project".
    RestOperation(
        operation_id="verify#retrieve-a-cluster-from-a-project",
        method="GET",
        path="/projects/:id/clusters/:cluster_id",
    ),
    # "Project clusters API (certificate-based) (deprecated): Add a cluster to a project".
    RestOperation(
        operation_id="verify#add-a-cluster-to-a-project",
        method="POST",
        path="/projects/:id/clusters/user",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="domain", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH, required=True),
        ),
    ),
    # "Project clusters API (certificate-based) (deprecated): Update a cluster in a project".
    RestOperation(
        operation_id="verify#update-a-cluster-in-a-project",
        method="PUT",
        path="/projects/:id/clusters/:cluster_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="domain", location=Location.BODY),
            Param(name="management_project_id", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="managed", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="namespace_per_environment", location=Location.BODY),
            Param(name="platform_kubernetes_attributes", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Project clusters API (certificate-based) (deprecated): Delete cluster from a project".
    RestOperation(
        operation_id="verify#delete-cluster-from-a-project",
        method="DELETE",
        path="/projects/:id/clusters/:cluster_id",
    ),
    # "Project release API: List Releases".
    RestOperation(
        operation_id="verify#list-releases",
        method="GET",
        path="/projects/:id/releases",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="include_html_description", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="updated_before", location=Location.QUERY),
            Param(name="updated_after", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project release API: Get a Release by a tag name".
    RestOperation(
        operation_id="verify#get-a-release-by-a-tag-name",
        method="GET",
        path="/projects/:id/releases/:tag_name",
        params=(Param(name="include_html_description", location=Location.QUERY),),
    ),
    # "Project release API: Download a release asset".
    RestOperation(
        operation_id="verify#download-a-release-asset",
        method="GET",
        path="/projects/:id/releases/:tag_name/downloads/:direct_asset_path",
    ),
    # "Project release API: Get the latest release"; the base record, the first of its three endpoints.
    RestOperation(
        operation_id="verify#get-the-latest-release",
        method="GET",
        path="/projects/:id/releases/permalink/latest",
        params=(Param(name="suffix_path", location=Location.QUERY, required=True),),
    ),
    # "Project release API: Get the latest release"; its second endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="verify#get-the-latest-release",
        method="GET",
        path="/projects/:id/releases/permalink/latest/evidence",
        params=(Param(name="suffix_path", location=Location.QUERY, required=True),),
    ),
    # "Project release API: Get the latest release"; its third endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="verify#get-the-latest-release",
        method="GET",
        path="/projects/:id/releases/permalink/latest/downloads/bin/asset.exe",
        params=(Param(name="suffix_path", location=Location.QUERY, required=True),),
    ),
    # "Project release API: Create a release".
    RestOperation(
        operation_id="verify#create-a-release",
        method="POST",
        path="/projects/:id/releases",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="tag_name", location=Location.BODY, required=True),
            Param(name="tag_message", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="ref", location=Location.BODY, required=True),
            Param(name="milestones", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="released_at", location=Location.BODY),
            Param(name="assets", location=Location.BODY, kind=Kind.HASH),
            Param(name="milestone_ids", location=Location.BODY),
            Param(name="legacy_catalog_publish", location=Location.BODY),
        ),
    ),
    # "Project release API: Collect release evidence".
    RestOperation(
        operation_id="verify#collect-release-evidence",
        method="POST",
        path="/projects/:id/releases/:tag_name/evidence",
    ),
    # "Project release API: Update a release".
    RestOperation(
        operation_id="verify#update-a-release",
        method="PUT",
        path="/projects/:id/releases/:tag_name",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="milestones", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="released_at", location=Location.BODY),
            Param(name="milestone_ids", location=Location.BODY),
        ),
    ),
    # "Project release API: Delete a Release".
    RestOperation(
        operation_id="verify#delete-a-release",
        method="DELETE",
        path="/projects/:id/releases/:tag_name",
    ),
    # "Project-level CI/CD variables API: List project variables".
    RestOperation(
        operation_id="verify#list-project-variables",
        method="GET",
        path="/projects/:id/variables",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project-level CI/CD variables API: Retrieve a single variable".
    RestOperation(
        operation_id="verify#retrieve-a-single-variable",
        method="GET",
        path="/projects/:id/variables/:key",
        params=(Param(name="filter", location=Location.QUERY, kind=Kind.HASH),),
    ),
    # "Project-level CI/CD variables API: Create a variable".
    RestOperation(
        operation_id="verify#create-a-variable",
        method="POST",
        path="/projects/:id/variables",
        params=(
            Param(name="key", location=Location.BODY, required=True),
            Param(name="value", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="masked", location=Location.BODY),
            Param(name="masked_and_hidden", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Project-level CI/CD variables API: Update a variable".
    RestOperation(
        operation_id="verify#update-a-variable",
        method="PUT",
        path="/projects/:id/variables/:key",
        params=(
            Param(name="value", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="environment_scope", location=Location.BODY),
            Param(name="filter", location=Location.BODY, kind=Kind.HASH),
            Param(name="masked", location=Location.BODY),
            Param(name="protected", location=Location.BODY),
            Param(name="raw", location=Location.BODY),
            Param(name="variable_type", location=Location.BODY),
        ),
    ),
    # "Project-level CI/CD variables API: Delete a variable".
    RestOperation(
        operation_id="verify#delete-a-variable",
        method="DELETE",
        path="/projects/:id/variables/:key",
        params=(Param(name="filter", location=Location.QUERY, kind=Kind.HASH),),
    ),
    # "Protected environments API: List protected environments".
    RestOperation(
        operation_id="verify#list-protected-environments",
        method="GET",
        path="/projects/:id/protected_environments",
        paging=Paging.OFFSET,
    ),
    # "Protected environments API: Get a single protected environment".
    RestOperation(
        operation_id="verify#get-a-single-protected-environment",
        method="GET",
        path="/projects/:id/protected_environments/:name",
    ),
    # "Protected environments API: Protect a single environment".
    RestOperation(
        operation_id="verify#protect-a-single-environment-1",
        method="POST",
        path="/projects/:id/protected_environments",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="deploy_access_levels", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="approval_rules", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Protected environments API: Update a protected environment".
    RestOperation(
        operation_id="verify#update-a-protected-environment-1",
        method="PUT",
        path="/projects/:id/protected_environments/:name",
        params=(
            Param(name="deploy_access_levels", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="approval_rules", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Protected environments API: Unprotect a single environment".
    RestOperation(
        operation_id="verify#unprotect-a-single-environment-1",
        method="DELETE",
        path="/projects/:id/protected_environments/:name",
    ),
    # "Release links API: List all release links".
    RestOperation(
        operation_id="verify#list-all-release-links",
        method="GET",
        path="/projects/:id/releases/:tag_name/assets/links",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Release links API: Retrieve a release link".
    RestOperation(
        operation_id="verify#retrieve-a-release-link",
        method="GET",
        path="/projects/:id/releases/:tag_name/assets/links/:link_id",
    ),
    # "Release links API: Create a release link".
    RestOperation(
        operation_id="verify#create-a-release-link",
        method="POST",
        path="/projects/:id/releases/:tag_name/assets/links",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="url", location=Location.BODY, required=True),
            Param(name="direct_asset_path", location=Location.BODY),
            Param(name="link_type", location=Location.BODY),
            Param(name="filepath", location=Location.BODY),
        ),
    ),
    # "Release links API: Update a release link".
    RestOperation(
        operation_id="verify#update-a-release-link",
        method="PUT",
        path="/projects/:id/releases/:tag_name/assets/links/:link_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="direct_asset_path", location=Location.BODY),
            Param(name="link_type", location=Location.BODY),
            Param(name="filepath", location=Location.BODY),
        ),
    ),
    # "Release links API: Delete a release link".
    RestOperation(
        operation_id="verify#delete-a-release-link",
        method="DELETE",
        path="/projects/:id/releases/:tag_name/assets/links/:link_id",
    ),
    # "Resource group API: List all resource groups".
    RestOperation(
        operation_id="verify#list-all-resource-groups",
        method="GET",
        path="/projects/:id/resource_groups",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Resource group API: Retrieve a resource group".
    RestOperation(
        operation_id="verify#retrieve-a-resource-group",
        method="GET",
        path="/projects/:id/resource_groups/:key",
    ),
    # "Resource group API: Retrieve current job for a resource group".
    RestOperation(
        operation_id="verify#retrieve-current-job-for-a-resource-group",
        method="GET",
        path="/projects/:id/resource_groups/:key/current_job",
    ),
    # "Resource group API: List upcoming jobs for a specific resource group".
    RestOperation(
        operation_id="verify#list-upcoming-jobs-for-a-specific-resource-group",
        method="GET",
        path="/projects/:id/resource_groups/:key/upcoming_jobs",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Resource group API: Update a resource group".
    RestOperation(
        operation_id="verify#update-a-resource-group",
        method="PUT",
        path="/projects/:id/resource_groups/:key",
        params=(Param(name="process_mode", location=Location.BODY),),
    ),
    # "Runner controller tokens API: List all runner controller tokens".
    RestOperation(
        operation_id="verify#list-all-runner-controller-tokens",
        method="GET",
        path="/runner_controllers/:id/tokens",
        paging=Paging.OFFSET,
    ),
    # "Runner controller tokens API: Retrieve a single runner controller token".
    RestOperation(
        operation_id="verify#retrieve-a-single-runner-controller-token",
        method="GET",
        path="/runner_controllers/:id/tokens/:token_id",
    ),
    # "Runner controller tokens API: Create a runner controller token".
    RestOperation(
        operation_id="verify#create-a-runner-controller-token",
        method="POST",
        path="/runner_controllers/:id/tokens",
        params=(Param(name="description", location=Location.BODY, required=True),),
    ),
    # "Runner controller tokens API: Revoke a runner controller token".
    RestOperation(
        operation_id="verify#revoke-a-runner-controller-token",
        method="DELETE",
        path="/runner_controllers/:id/tokens/:token_id",
    ),
    # "Runner controller tokens API: Rotate a runner controller token".
    RestOperation(
        operation_id="verify#rotate-a-runner-controller-token",
        method="POST",
        path="/runner_controllers/:id/tokens/:token_id/rotate",
    ),
    # "Runner controllers API: List all runner controllers".
    RestOperation(
        operation_id="verify#list-all-runner-controllers",
        method="GET",
        path="/runner_controllers",
        paging=Paging.OFFSET,
    ),
    # "Runner controllers API: Retrieve a single runner controller".
    RestOperation(
        operation_id="verify#retrieve-a-single-runner-controller",
        method="GET",
        path="/runner_controllers/:id",
    ),
    # "Runner controllers API: Register a runner controller".
    RestOperation(
        operation_id="verify#register-a-runner-controller",
        method="POST",
        path="/runner_controllers",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="state", location=Location.BODY),
        ),
    ),
    # "Runner controllers API: Update a runner controller".
    RestOperation(
        operation_id="verify#update-a-runner-controller",
        method="PUT",
        path="/runner_controllers/:id",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="state", location=Location.BODY),
        ),
    ),
    # "Runner controllers API: Delete a runner controller".
    RestOperation(
        operation_id="verify#delete-a-runner-controller",
        method="DELETE",
        path="/runner_controllers/:id",
    ),
    # "Runner controllers API: List all scopes for a runner controller"; it answers one object, so it is not paged.
    RestOperation(
        operation_id="verify#list-all-scopes-for-a-runner-controller",
        method="GET",
        path="/runner_controllers/:id/scopes",
    ),
    # "Runner controllers API: Add instance scope".
    RestOperation(
        operation_id="verify#add-instance-scope",
        method="POST",
        path="/runner_controllers/:id/scopes/instance",
    ),
    # "Runner controllers API: Remove instance scope".
    RestOperation(
        operation_id="verify#remove-instance-scope",
        method="DELETE",
        path="/runner_controllers/:id/scopes/instance",
    ),
    # "Runner controllers API: Add runner scope".
    RestOperation(
        operation_id="verify#add-runner-scope",
        method="POST",
        path="/runner_controllers/:id/scopes/runners/:runner_id",
    ),
    # "Runner controllers API: Remove runner scope".
    RestOperation(
        operation_id="verify#remove-runner-scope",
        method="DELETE",
        path="/runner_controllers/:id/scopes/runners/:runner_id",
    ),
    # "Runners API: List all available runners".
    RestOperation(
        operation_id="verify#list-all-available-runners",
        method="GET",
        path="/runners",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="type", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="paused", location=Location.QUERY),
            Param(name="tag_list", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="version_prefix", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: List all runners".
    RestOperation(
        operation_id="verify#list-all-runners",
        method="GET",
        path="/runners/all",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="type", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="paused", location=Location.QUERY),
            Param(name="tag_list", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="version_prefix", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: Retrieve runner's details".
    RestOperation(
        operation_id="verify#retrieve-runners-details",
        method="GET",
        path="/runners/:id",
        params=(Param(name="include_projects", location=Location.QUERY),),
    ),
    # "Runners API: Update runner's details".
    RestOperation(
        operation_id="verify#update-runners-details",
        method="PUT",
        path="/runners/:id",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="active", location=Location.BODY),
            Param(name="paused", location=Location.BODY),
            Param(name="tag_list", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="run_untagged", location=Location.BODY),
            Param(name="locked", location=Location.BODY),
            Param(name="access_level", location=Location.BODY),
            Param(name="maximum_timeout", location=Location.BODY),
            Param(name="maintenance_note", location=Location.BODY),
            Param(name="runner_id", location=Location.BODY, required=True),
        ),
    ),
    # "Runners API: List all jobs processed by a runner".
    RestOperation(
        operation_id="verify#list-all-jobs-processed-by-a-runner",
        method="GET",
        path="/runners/:id/jobs",
        params=(
            Param(name="system_id", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="cursor", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: List all runner's managers".
    RestOperation(
        operation_id="verify#list-all-runners-managers",
        method="GET",
        path="/runners/:id/managers",
        paging=Paging.OFFSET,
    ),
    # "Runners API: List all of a project's runners".
    RestOperation(
        operation_id="verify#list-all-of-a-projects-runners",
        method="GET",
        path="/projects/:id/runners",
        params=(
            Param(name="scope", location=Location.QUERY),
            Param(name="type", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="paused", location=Location.QUERY),
            Param(name="tag_list", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="version_prefix", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: Assign a runner to project".
    RestOperation(
        operation_id="verify#assign-a-runner-to-project",
        method="POST",
        path="/projects/:id/runners",
        params=(Param(name="runner_id", location=Location.BODY, required=True),),
    ),
    # "Runners API: Unassign a runner from project".
    RestOperation(
        operation_id="verify#unassign-a-runner-from-project",
        method="DELETE",
        path="/projects/:id/runners/:runner_id",
    ),
    # "Runners API: List all of a group's runners"; the base record, the first of its two endpoints.
    RestOperation(
        operation_id="verify#list-all-of-a-groups-runners",
        method="GET",
        path="/groups/:id/runners",
        params=(
            Param(name="type", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="paused", location=Location.QUERY),
            Param(name="tag_list", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="version_prefix", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: List all of a group's runners"; its second endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="verify#list-all-of-a-groups-runners",
        method="GET",
        path="/groups/:id/runners/all",
        params=(
            Param(name="type", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="paused", location=Location.QUERY),
            Param(name="tag_list", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="version_prefix", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Runners API: Create a runner".
    RestOperation(
        operation_id="verify#create-a-runner",
        method="POST",
        path="/runners",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
            Param(name="info", location=Location.BODY, kind=Kind.HASH),
            Param(name="active", location=Location.BODY),
            Param(name="paused", location=Location.BODY),
            Param(name="locked", location=Location.BODY),
            Param(name="run_untagged", location=Location.BODY),
            Param(name="tag_list", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="access_level", location=Location.BODY),
            Param(name="maximum_timeout", location=Location.BODY),
            Param(name="maintainer_note", location=Location.BODY),
            Param(name="maintenance_note", location=Location.BODY),
        ),
    ),
    # "Runners API: Delete a runner by ID".
    RestOperation(
        operation_id="verify#delete-a-runner-by-id",
        method="DELETE",
        path="/runners/:id",
    ),
    # "Runners API: Delete a runner by authentication token".
    RestOperation(
        operation_id="verify#delete-a-runner-by-authentication-token",
        method="DELETE",
        path="/runners",
        params=(Param(name="token", location=Location.QUERY, required=True),),
    ),
    # "Runners API: Verify authentication for a registered runner".
    RestOperation(
        operation_id="verify#verify-authentication-for-a-registered-runner",
        method="POST",
        path="/runners/verify",
        params=(
            Param(name="token", location=Location.BODY, required=True),
            Param(name="system_id", location=Location.BODY),
        ),
    ),
    # "Runners API: Reset instance's runner registration token".
    RestOperation(
        operation_id="verify#reset-instances-runner-registration-token",
        method="POST",
        path="/runners/reset_registration_token",
    ),
    # "Runners API: Reset project's runner registration token".
    RestOperation(
        operation_id="verify#reset-projects-runner-registration-token",
        method="POST",
        path="/projects/:id/runners/reset_registration_token",
    ),
    # "Runners API: Reset group's runner registration token".
    RestOperation(
        operation_id="verify#reset-groups-runner-registration-token",
        method="POST",
        path="/groups/:id/runners/reset_registration_token",
    ),
    # "Runners API: Reset runner's authentication token by using the runner ID".
    RestOperation(
        operation_id="verify#reset-runners-authentication-token-by-using-the-runner-id",
        method="POST",
        path="/runners/:id/reset_authentication_token",
    ),
    # "Runners API: Reset runner's authentication token by using the current token".
    RestOperation(
        operation_id="verify#reset-runners-authentication-token-by-using-the-current-token",
        method="POST",
        path="/runners/reset_authentication_token",
        params=(Param(name="token", location=Location.BODY, required=True),),
    ),
    # "Runners API: Discover Job Router information".
    RestOperation(
        operation_id="verify#discover-job-router-information",
        method="GET",
        path="/runners/router/discovery",
    ),
    # "Test balancing API: Initialize test balancing for a parallel job".
    RestOperation(
        operation_id="verify#initialize-test-balancing-for-a-parallel-job",
        method="POST",
        path="/job/test_balancing/initialize",
        params=(Param(name="test_splits", location=Location.BODY, kind=Kind.ARRAY_OF_HASHES, required=True),),
    ),
    # "Test balancing API: Request the next batch of tests".
    RestOperation(
        operation_id="verify#request-the-next-batch-of-tests",
        method="POST",
        path="/job/test_balancing/request",
        params=(
            Param(name="run_id", location=Location.BODY),
            Param(name="seq", location=Location.BODY),
        ),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
