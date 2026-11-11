"""The ``actions`` family of the GitHub operations index: GitHub Actions (workflows, workflow runs and jobs,
artifacts, caches, runners, secrets, variables and permissions).

Each record is the section of ``docs/api-reference/github/rest/actions.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body. No ``actions/`` section has a
path parameter that may contain ``/``, so every ``multi_segment`` is empty. The file's ``oidc`` category holds two
``actions/`` operations, recorded here, and ``oidc/`` ones, which belong to another family.

A section with a ``Paging:`` line is ``Paging.LINK``: each answers with an object holding its items under the key the
line names after "items in" (``conventions.md`` "Lists wrapped in an object"), and the ``link`` header carries the
next page, by page number or, for the two concurrency-group lists, by cursor. The two sections that answer one object
with a ``Link`` header and have no ``Paging:`` line, ``actions/get-actions-cache-usage-for-org`` and
``actions/get-hosted-runner-for-org``, send one request (``Paging.NONE``).

The ``ci`` commands use five records (design D5):

- ``actions/list-repo-workflows`` (``list-workflows``), ``actions/list-workflow-runs-for-repo`` and
  ``actions/list-workflow-runs`` (``list-runs`` without and with ``--workflow``) are page-based lists that answer
  with an object, so their items sit under an item key, ``workflows`` or ``workflow_runs`` (``conventions.md``
  "Lists wrapped in an object"), and the ``link`` header carries the next page (``Paging.LINK``).
- ``actions/get-workflow-run`` (``get-run``, ``wait-run``) returns one run.
- ``actions/download-workflow-run-logs`` (``get-logs``) answers ``302`` to a pre-signed storage URL that lives for a
  minute (``conventions.md`` "Downloads and redirects"); ``get-logs`` sends its expanded path with
  ``Transport.download``, which follows the redirect without the credential and returns the archive's bytes.

Every record is also sent by ``call <operation-id>`` (#28); none is gated. The other ``302`` downloads,
``actions/download-artifact``, ``actions/download-job-logs-for-workflow-run``,
``actions/download-step-logs-for-workflow-run-job`` and ``actions/download-workflow-run-attempt-logs``, are plain
records: the transport follows the redirect without the credential and ``call`` prints the archive's bytes (#28 D3).
A secret write (``actions/create-or-update-org-secret``, ``-repo-secret``, ``-environment-secret``) sends
``encrypted_value`` and ``key_id`` as the caller gives them; the wrapper encrypts nothing (#31 DL-002).
``actions/create-workflow-dispatch`` starts a workflow and ``actions/review-pending-deployments-for-run`` approves or
rejects a deployment, so each acts as soon as it is called; the registration- and remove-token records print a live
runner token.

No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "actions"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/actions.md "List repository workflows": page-based, items in `workflows`.
    RestOperation(
        operation_id="actions/list-repo-workflows",
        method="GET",
        path="/repos/{owner}/{repo}/actions/workflows",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="workflows",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List workflow runs for a repository": page-based, items in `workflow_runs`.
    RestOperation(
        operation_id="actions/list-workflow-runs-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs",
        query_params=frozenset(
            {
                "actor",
                "branch",
                "event",
                "status",
                "per_page",
                "page",
                "created",
                "exclude_pull_requests",
                "check_suite_id",
                "head_sha",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="workflow_runs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List workflow runs for a workflow": page-based, items in `workflow_runs`; `workflow_id` is
    # the workflow's ID or its file name.
    RestOperation(
        operation_id="actions/list-workflow-runs",
        method="GET",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
        query_params=frozenset(
            {
                "actor",
                "branch",
                "event",
                "status",
                "per_page",
                "page",
                "created",
                "exclude_pull_requests",
                "check_suite_id",
                "head_sha",
            }
        ),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="workflow_runs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a workflow run": one `workflow-run` object.
    RestOperation(
        operation_id="actions/get-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}",
        query_params=frozenset({"exclude_pull_requests"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Download workflow run logs": path parameters only; `302` with a `Location`.
    RestOperation(
        operation_id="actions/download-workflow-run-logs",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List artifacts for a repository": page-based, items in `artifacts`.
    RestOperation(
        operation_id="actions/list-artifacts-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/artifacts",
        query_params=frozenset({"per_page", "page", "name"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="artifacts",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an artifact": path parameters only; 200 with an `artifact`.
    RestOperation(
        operation_id="actions/get-artifact",
        method="GET",
        path="/repos/{owner}/{repo}/actions/artifacts/{artifact_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an artifact": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-artifact",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/artifacts/{artifact_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Download an artifact": path parameters only; `302` with a `Location` to the archive, whose bytes
    # `call` prints (#28 D3).
    RestOperation(
        operation_id="actions/download-artifact",
        method="GET",
        path="/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/{archive_format}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List workflow run artifacts": page-based, items in `artifacts`.
    RestOperation(
        operation_id="actions/list-workflow-run-artifacts",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts",
        query_params=frozenset({"per_page", "page", "name", "direction"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="artifacts",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache retention limit for an enterprise": path parameters only; 200 with an
    # `actions-cache-retention-limit-for-enterprise`.
    RestOperation(
        operation_id="actions/get-actions-cache-retention-limit-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache retention limit for an enterprise": body `max_cache_retention_days`; 204
    # on success.
    RestOperation(
        operation_id="actions/set-actions-cache-retention-limit-for-enterprise",
        method="PUT",
        path="/enterprises/{enterprise}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_retention_days"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache storage limit for an enterprise": path parameters only; 200 with an
    # `actions-cache-storage-limit-for-enterprise`.
    RestOperation(
        operation_id="actions/get-actions-cache-storage-limit-for-enterprise",
        method="GET",
        path="/enterprises/{enterprise}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache storage limit for an enterprise": body `max_cache_size_gb`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-actions-cache-storage-limit-for-enterprise",
        method="PUT",
        path="/enterprises/{enterprise}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_size_gb"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache retention limit for an organization": path parameters only; 200 with an
    # `actions-cache-retention-limit-for-organization`.
    RestOperation(
        operation_id="actions/get-actions-cache-retention-limit-for-organization",
        method="GET",
        path="/organizations/{org}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache retention limit for an organization": body `max_cache_retention_days`;
    # 204 on success.
    RestOperation(
        operation_id="actions/set-actions-cache-retention-limit-for-organization",
        method="PUT",
        path="/organizations/{org}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_retention_days"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache storage limit for an organization": path parameters only; 200 with an
    # `actions-cache-storage-limit-for-organization`.
    RestOperation(
        operation_id="actions/get-actions-cache-storage-limit-for-organization",
        method="GET",
        path="/organizations/{org}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache storage limit for an organization": body `max_cache_size_gb`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-actions-cache-storage-limit-for-organization",
        method="PUT",
        path="/organizations/{org}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_size_gb"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache usage for an organization": path parameters only; 200 with an
    # `actions-cache-usage-org-enterprise` and a `Link` header but no `Paging:` line, so one request.
    RestOperation(
        operation_id="actions/get-actions-cache-usage-for-org",
        method="GET",
        path="/orgs/{org}/actions/cache/usage",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repositories with GitHub Actions cache usage for an organization": page-based, items in
    # `repository_cache_usages`.
    RestOperation(
        operation_id="actions/get-actions-cache-usage-by-repo-for-org",
        method="GET",
        path="/orgs/{org}/actions/cache/usage-by-repository",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repository_cache_usages",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache retention limit for a repository": path parameters only; 200 with an
    # `actions-cache-retention-limit-for-repository`.
    RestOperation(
        operation_id="actions/get-actions-cache-retention-limit-for-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache retention limit for a repository": body `max_cache_retention_days`; 204
    # on success.
    RestOperation(
        operation_id="actions/set-actions-cache-retention-limit-for-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/cache/retention-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_retention_days"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache storage limit for a repository": path parameters only; 200 with an
    # `actions-cache-storage-limit-for-repository`.
    RestOperation(
        operation_id="actions/get-actions-cache-storage-limit-for-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions cache storage limit for a repository": body `max_cache_size_gb`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-actions-cache-storage-limit-for-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/cache/storage-limit",
        query_params=frozenset(),
        body_params=frozenset({"max_cache_size_gb"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions cache usage for a repository": path parameters only; 200 with an
    # `actions-cache-usage-by-repository`.
    RestOperation(
        operation_id="actions/get-actions-cache-usage",
        method="GET",
        path="/repos/{owner}/{repo}/actions/cache/usage",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List GitHub Actions caches for a repository": page-based, items in `actions_caches`.
    RestOperation(
        operation_id="actions/get-actions-cache-list",
        method="GET",
        path="/repos/{owner}/{repo}/actions/caches",
        query_params=frozenset({"per_page", "page", "ref", "key", "sort", "direction"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="actions_caches",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete GitHub Actions caches for a repository (using a cache key)": query `key`, `ref`; 200 with
    # an `actions-cache-list`.
    RestOperation(
        operation_id="actions/delete-actions-cache-by-key",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/caches",
        query_params=frozenset({"key", "ref"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a GitHub Actions cache for a repository (using a cache ID)": path parameters only; 204 on
    # success.
    RestOperation(
        operation_id="actions/delete-actions-cache-by-id",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/caches/{cache_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List concurrency groups for a repository": `per_page` + cursor-based, items in
    # `concurrency_groups`; the `link` header's next target carries the cursor.
    RestOperation(
        operation_id="actions/list-concurrency-groups-for-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/concurrency_groups",
        query_params=frozenset({"per_page", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="concurrency_groups",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a concurrency group for a repository": query `ahead_of_run`, `ahead_of_job`; 200 with a
    # `concurrency-group`.
    RestOperation(
        operation_id="actions/get-concurrency-group-for-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/concurrency_groups/{concurrency_group_name}",
        query_params=frozenset({"ahead_of_run", "ahead_of_job"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List concurrency groups for a workflow run": `per_page` + cursor-based, items in
    # `concurrency_groups`; the `link` header's next target carries the cursor.
    RestOperation(
        operation_id="actions/list-concurrency-groups-for-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/concurrency_groups",
        query_params=frozenset({"per_page", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="concurrency_groups",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List GitHub-hosted runners for an organization": page-based, items in `runners`.
    RestOperation(
        operation_id="actions/list-hosted-runners-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runners",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a GitHub-hosted runner for an organization": body `name`, `image`, `size`,
    # `runner_group_id`, `maximum_runners`, `enable_static_ip`, `image_gen`; 201 with an `actions-hosted-runner`.
    RestOperation(
        operation_id="actions/create-hosted-runner-for-org",
        method="POST",
        path="/orgs/{org}/actions/hosted-runners",
        query_params=frozenset(),
        body_params=frozenset(
            {"name", "image", "size", "runner_group_id", "maximum_runners", "enable_static_ip", "image_gen"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List custom images for an organization": path parameters only; 200 with an object.
    RestOperation(
        operation_id="actions/list-custom-images-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/custom",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a custom image definition for GitHub Actions Hosted Runners": path parameters only; 200 with
    # an `actions-hosted-runner-custom-image`.
    RestOperation(
        operation_id="actions/get-custom-image-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a custom image from the organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-custom-image-from-org",
        method="DELETE",
        path="/orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List image versions of a custom image for an organization": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/list-custom-image-versions-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an image version of a custom image for GitHub Actions Hosted Runners": path parameters only;
    # 200 with an `actions-hosted-runner-custom-image-version`.
    RestOperation(
        operation_id="actions/get-custom-image-version-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions/{version}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an image version of custom image from the organization": path parameters only; 204 on
    # success.
    RestOperation(
        operation_id="actions/delete-custom-image-version-from-org",
        method="DELETE",
        path="/orgs/{org}/actions/hosted-runners/images/custom/{image_definition_id}/versions/{version}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub-owned images for GitHub-hosted runners in an organization": path parameters only; 200
    # with an object.
    RestOperation(
        operation_id="actions/get-hosted-runners-github-owned-images-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/github-owned",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get partner images for GitHub-hosted runners in an organization": path parameters only; 200 with
    # an object.
    RestOperation(
        operation_id="actions/get-hosted-runners-partner-images-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/images/partner",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get limits on GitHub-hosted runners for an organization": path parameters only; 200 with an
    # `actions-hosted-runner-limits`.
    RestOperation(
        operation_id="actions/get-hosted-runners-limits-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/limits",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub-hosted runners machine specs for an organization": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/get-hosted-runners-machine-specs-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/machine-sizes",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get platforms for GitHub-hosted runners in an organization": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/get-hosted-runners-platforms-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/platforms",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a GitHub-hosted runner for an organization": path parameters only; 200 with an
    # `actions-hosted-runner` and a `Link` header but no `Paging:` line, so one request.
    RestOperation(
        operation_id="actions/get-hosted-runner-for-org",
        method="GET",
        path="/orgs/{org}/actions/hosted-runners/{hosted_runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update a GitHub-hosted runner for an organization": body `name`, `runner_group_id`,
    # `maximum_runners`, `enable_static_ip`, `size`, `image_source`, `image_id`, `image_version`, `image_gen`; 200 with
    # an `actions-hosted-runner`.
    RestOperation(
        operation_id="actions/update-hosted-runner-for-org",
        method="PATCH",
        path="/orgs/{org}/actions/hosted-runners/{hosted_runner_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "runner_group_id",
                "maximum_runners",
                "enable_static_ip",
                "size",
                "image_source",
                "image_id",
                "image_version",
                "image_gen",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a GitHub-hosted runner for an organization": path parameters only; 202 with an
    # `actions-hosted-runner`.
    RestOperation(
        operation_id="actions/delete-hosted-runner-for-org",
        method="DELETE",
        path="/orgs/{org}/actions/hosted-runners/{hosted_runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get the customization template for an OIDC subject claim for a repository": path parameters only;
    # 200 with an `oidc-custom-sub-repo`.
    RestOperation(
        operation_id="actions/get-custom-oidc-sub-claim-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/oidc/customization/sub",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set the customization template for an OIDC subject claim for a repository": body `use_default`,
    # `include_claim_keys`, `use_immutable_subject`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/set-custom-oidc-sub-claim-for-repo",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/oidc/customization/sub",
        query_params=frozenset(),
        body_params=frozenset({"use_default", "include_claim_keys", "use_immutable_subject"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions permissions for an organization": path parameters only; 200 with an
    # `actions-organization-permissions`.
    RestOperation(
        operation_id="actions/get-github-actions-permissions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions permissions for an organization": body `enabled_repositories`,
    # `allowed_actions`, `sha_pinning_required`; 204 on success.
    RestOperation(
        operation_id="actions/set-github-actions-permissions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions",
        query_params=frozenset(),
        body_params=frozenset({"enabled_repositories", "allowed_actions", "sha_pinning_required"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get artifact and log retention settings for an organization": path parameters only; 200 with an
    # `actions-artifact-and-log-retention-response`.
    RestOperation(
        operation_id="actions/get-artifact-and-log-retention-settings-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/artifact-and-log-retention",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set artifact and log retention settings for an organization": body `days`; 204 on success.
    RestOperation(
        operation_id="actions/set-artifact-and-log-retention-settings-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/artifact-and-log-retention",
        query_params=frozenset(),
        body_params=frozenset({"days"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get fork PR contributor approval permissions for an organization": path parameters only; 200 with
    # an `actions-fork-pr-contributor-approval`.
    RestOperation(
        operation_id="actions/get-fork-pr-contributor-approval-permissions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/fork-pr-contributor-approval",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set fork PR contributor approval permissions for an organization": body `approval_policy`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-fork-pr-contributor-approval-permissions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/fork-pr-contributor-approval",
        query_params=frozenset(),
        body_params=frozenset({"approval_policy"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get private repo fork PR workflow settings for an organization": path parameters only; 200 with
    # an `actions-fork-pr-workflows-private-repos`.
    RestOperation(
        operation_id="actions/get-private-repo-fork-pr-workflows-settings-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/fork-pr-workflows-private-repos",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set private repo fork PR workflow settings for an organization": body
    # `run_workflows_from_fork_pull_requests`, `send_write_tokens_to_workflows`, `send_secrets_and_variables`,
    # `require_approval_for_fork_pr_workflows`; 204 on success.
    RestOperation(
        operation_id="actions/set-private-repo-fork-pr-workflows-settings-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/fork-pr-workflows-private-repos",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "run_workflows_from_fork_pull_requests",
                "send_write_tokens_to_workflows",
                "send_secrets_and_variables",
                "require_approval_for_fork_pr_workflows",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List selected repositories enabled for GitHub Actions in an organization": page-based, items in
    # `repositories`.
    RestOperation(
        operation_id="actions/list-selected-repositories-enabled-github-actions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set selected repositories enabled for GitHub Actions in an organization": body
    # `selected_repository_ids`; 204 on success.
    RestOperation(
        operation_id="actions/set-selected-repositories-enabled-github-actions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Enable a selected repository for GitHub Actions in an organization": path parameters only; 204 on
    # success.
    RestOperation(
        operation_id="actions/enable-selected-repository-github-actions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Disable a selected repository for GitHub Actions in an organization": path parameters only; 204
    # on success.
    RestOperation(
        operation_id="actions/disable-selected-repository-github-actions-organization",
        method="DELETE",
        path="/orgs/{org}/actions/permissions/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get allowed actions and reusable workflows for an organization": path parameters only; 200 with a
    # `selected-actions`.
    RestOperation(
        operation_id="actions/get-allowed-actions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/selected-actions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set allowed actions and reusable workflows for an organization": body `github_owned_allowed`,
    # `verified_allowed`, `patterns_allowed`; 204 on success.
    RestOperation(
        operation_id="actions/set-allowed-actions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/selected-actions",
        query_params=frozenset(),
        body_params=frozenset({"github_owned_allowed", "verified_allowed", "patterns_allowed"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get self-hosted runners settings for an organization": path parameters only; 200 with a
    # `self-hosted-runners-settings`.
    RestOperation(
        operation_id="actions/get-self-hosted-runners-permissions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/self-hosted-runners",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set self-hosted runners settings for an organization": body `enabled_repositories`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-self-hosted-runners-permissions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/self-hosted-runners",
        query_params=frozenset(),
        body_params=frozenset({"enabled_repositories"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repositories allowed to use self-hosted runners in an organization": page-based, items in
    # `repositories`.
    RestOperation(
        operation_id="actions/list-selected-repositories-self-hosted-runners-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/self-hosted-runners/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set repositories allowed to use self-hosted runners in an organization": body
    # `selected_repository_ids`; 204 on success.
    RestOperation(
        operation_id="actions/set-selected-repositories-self-hosted-runners-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/self-hosted-runners/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add a repository to the list of repositories allowed to use self-hosted runners in an
    # organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/enable-selected-repository-self-hosted-runners-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/self-hosted-runners/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove a repository from the list of repositories allowed to use self-hosted runners in an
    # organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/disable-selected-repository-self-hosted-runners-organization",
        method="DELETE",
        path="/orgs/{org}/actions/permissions/self-hosted-runners/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get default workflow permissions for an organization": path parameters only; 200 with an
    # `actions-get-default-workflow-permissions`.
    RestOperation(
        operation_id="actions/get-github-actions-default-workflow-permissions-organization",
        method="GET",
        path="/orgs/{org}/actions/permissions/workflow",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set default workflow permissions for an organization": body `default_workflow_permissions`,
    # `can_approve_pull_request_reviews`; 204 on success.
    RestOperation(
        operation_id="actions/set-github-actions-default-workflow-permissions-organization",
        method="PUT",
        path="/orgs/{org}/actions/permissions/workflow",
        query_params=frozenset(),
        body_params=frozenset({"default_workflow_permissions", "can_approve_pull_request_reviews"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get GitHub Actions permissions for a repository": path parameters only; 200 with an
    # `actions-repository-permissions`.
    RestOperation(
        operation_id="actions/get-github-actions-permissions-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set GitHub Actions permissions for a repository": body `enabled`, `allowed_actions`,
    # `sha_pinning_required`; 204 on success.
    RestOperation(
        operation_id="actions/set-github-actions-permissions-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions",
        query_params=frozenset(),
        body_params=frozenset({"enabled", "allowed_actions", "sha_pinning_required"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get the level of access for workflows outside of the repository": path parameters only; 200 with
    # an `actions-workflow-access-to-repository`.
    RestOperation(
        operation_id="actions/get-workflow-access-to-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/access",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set the level of access for workflows outside of the repository": body `access_level`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-workflow-access-to-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/access",
        query_params=frozenset(),
        body_params=frozenset({"access_level"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get artifact and log retention settings for a repository": path parameters only; 200 with an
    # `actions-artifact-and-log-retention-response`.
    RestOperation(
        operation_id="actions/get-artifact-and-log-retention-settings-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/artifact-and-log-retention",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set artifact and log retention settings for a repository": body `days`; 204 on success.
    RestOperation(
        operation_id="actions/set-artifact-and-log-retention-settings-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/artifact-and-log-retention",
        query_params=frozenset(),
        body_params=frozenset({"days"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get fork PR contributor approval permissions for a repository": path parameters only; 200 with an
    # `actions-fork-pr-contributor-approval`.
    RestOperation(
        operation_id="actions/get-fork-pr-contributor-approval-permissions-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/fork-pr-contributor-approval",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set fork PR contributor approval permissions for a repository": body `approval_policy`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-fork-pr-contributor-approval-permissions-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/fork-pr-contributor-approval",
        query_params=frozenset(),
        body_params=frozenset({"approval_policy"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get private repo fork PR workflow settings for a repository": path parameters only; 200 with an
    # `actions-fork-pr-workflows-private-repos`.
    RestOperation(
        operation_id="actions/get-private-repo-fork-pr-workflows-settings-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/fork-pr-workflows-private-repos",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set private repo fork PR workflow settings for a repository": body
    # `run_workflows_from_fork_pull_requests`, `send_write_tokens_to_workflows`, `send_secrets_and_variables`,
    # `require_approval_for_fork_pr_workflows`; 204 on success.
    RestOperation(
        operation_id="actions/set-private-repo-fork-pr-workflows-settings-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/fork-pr-workflows-private-repos",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "run_workflows_from_fork_pull_requests",
                "send_write_tokens_to_workflows",
                "send_secrets_and_variables",
                "require_approval_for_fork_pr_workflows",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get allowed actions and reusable workflows for a repository": path parameters only; 200 with a
    # `selected-actions`.
    RestOperation(
        operation_id="actions/get-allowed-actions-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/selected-actions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set allowed actions and reusable workflows for a repository": body `github_owned_allowed`,
    # `verified_allowed`, `patterns_allowed`; 204 on success.
    RestOperation(
        operation_id="actions/set-allowed-actions-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/selected-actions",
        query_params=frozenset(),
        body_params=frozenset({"github_owned_allowed", "verified_allowed", "patterns_allowed"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get default workflow permissions for a repository": path parameters only; 200 with an
    # `actions-get-default-workflow-permissions`.
    RestOperation(
        operation_id="actions/get-github-actions-default-workflow-permissions-repository",
        method="GET",
        path="/repos/{owner}/{repo}/actions/permissions/workflow",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set default workflow permissions for a repository": body `default_workflow_permissions`,
    # `can_approve_pull_request_reviews`; 204 on success.
    RestOperation(
        operation_id="actions/set-github-actions-default-workflow-permissions-repository",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/permissions/workflow",
        query_params=frozenset(),
        body_params=frozenset({"default_workflow_permissions", "can_approve_pull_request_reviews"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List organization Actions policies": page-based, items in `policies`.
    RestOperation(
        operation_id="actions/get-org-actions-policies",
        method="GET",
        path="/orgs/{org}/actions/policies",
        query_params=frozenset({"per_page", "page", "has_parents"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="policies",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create an organization Actions policy": body `name`, `enforcement`, `conditions`, `rules`; 201
    # with an `actions-policy`.
    RestOperation(
        operation_id="actions/create-org-actions-policy",
        method="POST",
        path="/orgs/{org}/actions/policies",
        query_params=frozenset(),
        body_params=frozenset({"name", "enforcement", "conditions", "rules"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an organization Actions policy": path parameters only; 200 with an `actions-policy`.
    RestOperation(
        operation_id="actions/get-org-actions-policy",
        method="GET",
        path="/orgs/{org}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update an organization Actions policy": body `name`, `enforcement`, `conditions`, `rules`; 200
    # with an `actions-policy`.
    RestOperation(
        operation_id="actions/update-org-actions-policy",
        method="PUT",
        path="/orgs/{org}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset({"name", "enforcement", "conditions", "rules"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an organization Actions policy": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-org-actions-policy",
        method="DELETE",
        path="/orgs/{org}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository Actions policies": page-based, items in `policies`.
    RestOperation(
        operation_id="actions/get-repo-actions-policies",
        method="GET",
        path="/repos/{owner}/{repo}/actions/policies",
        query_params=frozenset({"per_page", "page", "has_parents"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="policies",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a repository Actions policy": body `name`, `enforcement`, `conditions`, `rules`; 201 with
    # an `actions-policy`.
    RestOperation(
        operation_id="actions/create-repo-actions-policy",
        method="POST",
        path="/repos/{owner}/{repo}/actions/policies",
        query_params=frozenset(),
        body_params=frozenset({"name", "enforcement", "conditions", "rules"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a repository Actions policy": path parameters only; 200 with an `actions-policy`.
    RestOperation(
        operation_id="actions/get-repo-actions-policy",
        method="GET",
        path="/repos/{owner}/{repo}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update a repository Actions policy": body `name`, `enforcement`, `conditions`, `rules`; 200 with
    # an `actions-policy`.
    RestOperation(
        operation_id="actions/update-repo-actions-policy",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset({"name", "enforcement", "conditions", "rules"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a repository Actions policy": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-repo-actions-policy",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/policies/{policy_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List organization secrets": page-based, items in `secrets`.
    RestOperation(
        operation_id="actions/list-org-secrets",
        method="GET",
        path="/orgs/{org}/actions/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an organization public key": path parameters only; 200 with an `actions-public-key`.
    RestOperation(
        operation_id="actions/get-org-public-key",
        method="GET",
        path="/orgs/{org}/actions/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an organization secret": path parameters only; 200 with an `organization-actions-secret`.
    RestOperation(
        operation_id="actions/get-org-secret",
        method="GET",
        path="/orgs/{org}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create or update an organization secret": body `encrypted_value`, `key_id`, `visibility`,
    # `selected_repository_ids`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/create-or-update-org-secret",
        method="PUT",
        path="/orgs/{org}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id", "visibility", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an organization secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-org-secret",
        method="DELETE",
        path="/orgs/{org}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List selected repositories for an organization secret": page-based, items in `repositories`.
    RestOperation(
        operation_id="actions/list-selected-repos-for-org-secret",
        method="GET",
        path="/orgs/{org}/actions/secrets/{secret_name}/repositories",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set selected repositories for an organization secret": body `selected_repository_ids`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-selected-repos-for-org-secret",
        method="PUT",
        path="/orgs/{org}/actions/secrets/{secret_name}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add selected repository to an organization secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/add-selected-repo-to-org-secret",
        method="PUT",
        path="/orgs/{org}/actions/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove selected repository from an organization secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/remove-selected-repo-from-org-secret",
        method="DELETE",
        path="/orgs/{org}/actions/secrets/{secret_name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository organization secrets": page-based, items in `secrets`.
    RestOperation(
        operation_id="actions/list-repo-organization-secrets",
        method="GET",
        path="/repos/{owner}/{repo}/actions/organization-secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository secrets": page-based, items in `secrets`.
    RestOperation(
        operation_id="actions/list-repo-secrets",
        method="GET",
        path="/repos/{owner}/{repo}/actions/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a repository public key": path parameters only; 200 with an `actions-public-key`.
    RestOperation(
        operation_id="actions/get-repo-public-key",
        method="GET",
        path="/repos/{owner}/{repo}/actions/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a repository secret": path parameters only; 200 with an `actions-secret`.
    RestOperation(
        operation_id="actions/get-repo-secret",
        method="GET",
        path="/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create or update a repository secret": body `encrypted_value`, `key_id`; 201 with an
    # `empty-object`.
    RestOperation(
        operation_id="actions/create-or-update-repo-secret",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a repository secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-repo-secret",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List environment secrets": page-based, items in `secrets`.
    RestOperation(
        operation_id="actions/list-environment-secrets",
        method="GET",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="secrets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an environment public key": path parameters only; 200 with an `actions-public-key`.
    RestOperation(
        operation_id="actions/get-environment-public-key",
        method="GET",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets/public-key",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an environment secret": path parameters only; 200 with an `actions-secret`.
    RestOperation(
        operation_id="actions/get-environment-secret",
        method="GET",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create or update an environment secret": body `encrypted_value`, `key_id`; 201 with an
    # `empty-object`.
    RestOperation(
        operation_id="actions/create-or-update-environment-secret",
        method="PUT",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset({"encrypted_value", "key_id"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an environment secret": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-environment-secret",
        method="DELETE",
        path="/repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List self-hosted runner groups for an organization": page-based, items in `runner_groups`.
    RestOperation(
        operation_id="actions/list-self-hosted-runner-groups-for-org",
        method="GET",
        path="/orgs/{org}/actions/runner-groups",
        query_params=frozenset({"per_page", "page", "visible_to_repository"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runner_groups",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a self-hosted runner group for an organization": body `name`, `visibility`,
    # `selected_repository_ids`, `runners`, `allows_public_repositories`, `restricted_to_workflows`,
    # `selected_workflows`, `network_configuration_id`; 201 with a `runner-groups-org`.
    RestOperation(
        operation_id="actions/create-self-hosted-runner-group-for-org",
        method="POST",
        path="/orgs/{org}/actions/runner-groups",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "visibility",
                "selected_repository_ids",
                "runners",
                "allows_public_repositories",
                "restricted_to_workflows",
                "selected_workflows",
                "network_configuration_id",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a self-hosted runner group for an organization": path parameters only; 200 with a
    # `runner-groups-org`.
    RestOperation(
        operation_id="actions/get-self-hosted-runner-group-for-org",
        method="GET",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update a self-hosted runner group for an organization": body `name`, `visibility`,
    # `allows_public_repositories`, `restricted_to_workflows`, `selected_workflows`, `network_configuration_id`; 200
    # with a `runner-groups-org`.
    RestOperation(
        operation_id="actions/update-self-hosted-runner-group-for-org",
        method="PATCH",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "visibility",
                "allows_public_repositories",
                "restricted_to_workflows",
                "selected_workflows",
                "network_configuration_id",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a self-hosted runner group from an organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-self-hosted-runner-group-from-org",
        method="DELETE",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List GitHub-hosted runners in a group for an organization": page-based, items in `runners`.
    RestOperation(
        operation_id="actions/list-github-hosted-runners-in-group-for-org",
        method="GET",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/hosted-runners",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runners",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository access to a self-hosted runner group in an organization": page-based, items in
    # `repositories`.
    RestOperation(
        operation_id="actions/list-repo-access-to-self-hosted-runner-group-in-org",
        method="GET",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set repository access for a self-hosted runner group in an organization": body
    # `selected_repository_ids`; 204 on success.
    RestOperation(
        operation_id="actions/set-repo-access-to-self-hosted-runner-group-in-org",
        method="PUT",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add repository access to a self-hosted runner group in an organization": path parameters only;
    # 204 on success.
    RestOperation(
        operation_id="actions/add-repo-access-to-self-hosted-runner-group-in-org",
        method="PUT",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove repository access to a self-hosted runner group in an organization": path parameters only;
    # 204 on success.
    RestOperation(
        operation_id="actions/remove-repo-access-to-self-hosted-runner-group-in-org",
        method="DELETE",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List self-hosted runners in a group for an organization": page-based, items in `runners`.
    RestOperation(
        operation_id="actions/list-self-hosted-runners-in-group-for-org",
        method="GET",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/runners",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runners",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set self-hosted runners in a group for an organization": body `runners`; 204 on success.
    RestOperation(
        operation_id="actions/set-self-hosted-runners-in-group-for-org",
        method="PUT",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/runners",
        query_params=frozenset(),
        body_params=frozenset({"runners"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add a self-hosted runner to a group for an organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/add-self-hosted-runner-to-group-for-org",
        method="PUT",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove a self-hosted runner from a group for an organization": path parameters only; 204 on
    # success.
    RestOperation(
        operation_id="actions/remove-self-hosted-runner-from-group-for-org",
        method="DELETE",
        path="/orgs/{org}/actions/runner-groups/{runner_group_id}/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List self-hosted runners for an organization": page-based, items in `runners`.
    RestOperation(
        operation_id="actions/list-self-hosted-runners-for-org",
        method="GET",
        path="/orgs/{org}/actions/runners",
        query_params=frozenset({"name", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runners",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get runner version end-of-life schedule for an organization": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/get-runner-version-deprecation-for-org",
        method="GET",
        path="/orgs/{org}/actions/runners/deprecations/{version}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List runner applications for an organization": path parameters only; 200 with an array of
    # `runner-application`.
    RestOperation(
        operation_id="actions/list-runner-applications-for-org",
        method="GET",
        path="/orgs/{org}/actions/runners/downloads",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create configuration for a just-in-time runner for an organization": body `name`,
    # `runner_group_id`, `labels`, `work_folder`; 201 with an object.
    RestOperation(
        operation_id="actions/generate-runner-jitconfig-for-org",
        method="POST",
        path="/orgs/{org}/actions/runners/generate-jitconfig",
        query_params=frozenset(),
        body_params=frozenset({"name", "runner_group_id", "labels", "work_folder"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a registration token for an organization": path parameters only; 201 with an
    # `authentication-token`.
    RestOperation(
        operation_id="actions/create-registration-token-for-org",
        method="POST",
        path="/orgs/{org}/actions/runners/registration-token",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a remove token for an organization": path parameters only; 201 with an
    # `authentication-token`.
    RestOperation(
        operation_id="actions/create-remove-token-for-org",
        method="POST",
        path="/orgs/{org}/actions/runners/remove-token",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a self-hosted runner for an organization": path parameters only; 200 with a `runner`.
    RestOperation(
        operation_id="actions/get-self-hosted-runner-for-org",
        method="GET",
        path="/orgs/{org}/actions/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a self-hosted runner from an organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-self-hosted-runner-from-org",
        method="DELETE",
        path="/orgs/{org}/actions/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List labels for a self-hosted runner for an organization": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/list-labels-for-self-hosted-runner-for-org",
        method="GET",
        path="/orgs/{org}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add custom labels to a self-hosted runner for an organization": body `labels`; 200 with an
    # object.
    RestOperation(
        operation_id="actions/add-custom-labels-to-self-hosted-runner-for-org",
        method="POST",
        path="/orgs/{org}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset({"labels"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set custom labels for a self-hosted runner for an organization": body `labels`; 200 with an
    # object.
    RestOperation(
        operation_id="actions/set-custom-labels-for-self-hosted-runner-for-org",
        method="PUT",
        path="/orgs/{org}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset({"labels"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove all custom labels from a self-hosted runner for an organization": path parameters only;
    # 200 with an object.
    RestOperation(
        operation_id="actions/remove-all-custom-labels-from-self-hosted-runner-for-org",
        method="DELETE",
        path="/orgs/{org}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove a custom label from a self-hosted runner for an organization": path parameters only; 200
    # with an object.
    RestOperation(
        operation_id="actions/remove-custom-label-from-self-hosted-runner-for-org",
        method="DELETE",
        path="/orgs/{org}/actions/runners/{runner_id}/labels/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List self-hosted runners for a repository": page-based, items in `runners`.
    RestOperation(
        operation_id="actions/list-self-hosted-runners-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runners",
        query_params=frozenset({"name", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="runners",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get runner version end-of-life schedule for a repository": path parameters only; 200 with an
    # object.
    RestOperation(
        operation_id="actions/get-runner-version-deprecation-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runners/deprecations/{version}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List runner applications for a repository": path parameters only; 200 with an array of
    # `runner-application`.
    RestOperation(
        operation_id="actions/list-runner-applications-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runners/downloads",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create configuration for a just-in-time runner for a repository": body `name`, `runner_group_id`,
    # `labels`, `work_folder`; 201 with an object.
    RestOperation(
        operation_id="actions/generate-runner-jitconfig-for-repo",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runners/generate-jitconfig",
        query_params=frozenset(),
        body_params=frozenset({"name", "runner_group_id", "labels", "work_folder"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a registration token for a repository": path parameters only; 201 with an
    # `authentication-token`.
    RestOperation(
        operation_id="actions/create-registration-token-for-repo",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runners/registration-token",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a remove token for a repository": path parameters only; 201 with an
    # `authentication-token`.
    RestOperation(
        operation_id="actions/create-remove-token-for-repo",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runners/remove-token",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a self-hosted runner for a repository": path parameters only; 200 with a `runner`.
    RestOperation(
        operation_id="actions/get-self-hosted-runner-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a self-hosted runner from a repository": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-self-hosted-runner-from-repo",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List labels for a self-hosted runner for a repository": path parameters only; 200 with an object.
    RestOperation(
        operation_id="actions/list-labels-for-self-hosted-runner-for-repo",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add custom labels to a self-hosted runner for a repository": body `labels`; 200 with an object.
    RestOperation(
        operation_id="actions/add-custom-labels-to-self-hosted-runner-for-repo",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset({"labels"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set custom labels for a self-hosted runner for a repository": body `labels`; 200 with an object.
    RestOperation(
        operation_id="actions/set-custom-labels-for-self-hosted-runner-for-repo",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset({"labels"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove all custom labels from a self-hosted runner for a repository": path parameters only; 200
    # with an object.
    RestOperation(
        operation_id="actions/remove-all-custom-labels-from-self-hosted-runner-for-repo",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}/labels",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove a custom label from a self-hosted runner for a repository": path parameters only; 200 with
    # an object.
    RestOperation(
        operation_id="actions/remove-custom-label-from-self-hosted-runner-for-repo",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/runners/{runner_id}/labels/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List organization variables": page-based, items in `variables`.
    RestOperation(
        operation_id="actions/list-org-variables",
        method="GET",
        path="/orgs/{org}/actions/variables",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="variables",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create an organization variable": body `name`, `value`, `visibility`, `selected_repository_ids`;
    # 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/create-org-variable",
        method="POST",
        path="/orgs/{org}/actions/variables",
        query_params=frozenset(),
        body_params=frozenset({"name", "value", "visibility", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an organization variable": path parameters only; 200 with an `organization-actions-variable`.
    RestOperation(
        operation_id="actions/get-org-variable",
        method="GET",
        path="/orgs/{org}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update an organization variable": body `name`, `value`, `visibility`, `selected_repository_ids`;
    # 204 on success.
    RestOperation(
        operation_id="actions/update-org-variable",
        method="PATCH",
        path="/orgs/{org}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset({"name", "value", "visibility", "selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an organization variable": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-org-variable",
        method="DELETE",
        path="/orgs/{org}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List selected repositories for an organization variable": page-based, items in `repositories`.
    RestOperation(
        operation_id="actions/list-selected-repos-for-org-variable",
        method="GET",
        path="/orgs/{org}/actions/variables/{name}/repositories",
        query_params=frozenset({"page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="repositories",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Set selected repositories for an organization variable": body `selected_repository_ids`; 204 on
    # success.
    RestOperation(
        operation_id="actions/set-selected-repos-for-org-variable",
        method="PUT",
        path="/orgs/{org}/actions/variables/{name}/repositories",
        query_params=frozenset(),
        body_params=frozenset({"selected_repository_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Add selected repository to an organization variable": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/add-selected-repo-to-org-variable",
        method="PUT",
        path="/orgs/{org}/actions/variables/{name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Remove selected repository from an organization variable": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/remove-selected-repo-from-org-variable",
        method="DELETE",
        path="/orgs/{org}/actions/variables/{name}/repositories/{repository_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository organization variables": page-based, items in `variables`.
    RestOperation(
        operation_id="actions/list-repo-organization-variables",
        method="GET",
        path="/repos/{owner}/{repo}/actions/organization-variables",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="variables",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List repository variables": page-based, items in `variables`.
    RestOperation(
        operation_id="actions/list-repo-variables",
        method="GET",
        path="/repos/{owner}/{repo}/actions/variables",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="variables",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a repository variable": body `name`, `value`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/create-repo-variable",
        method="POST",
        path="/repos/{owner}/{repo}/actions/variables",
        query_params=frozenset(),
        body_params=frozenset({"name", "value"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a repository variable": path parameters only; 200 with an `actions-variable`.
    RestOperation(
        operation_id="actions/get-repo-variable",
        method="GET",
        path="/repos/{owner}/{repo}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update a repository variable": body `name`, `value`; 204 on success.
    RestOperation(
        operation_id="actions/update-repo-variable",
        method="PATCH",
        path="/repos/{owner}/{repo}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset({"name", "value"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a repository variable": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-repo-variable",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List environment variables": page-based, items in `variables`.
    RestOperation(
        operation_id="actions/list-environment-variables",
        method="GET",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="variables",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create an environment variable": body `name`, `value`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/create-environment-variable",
        method="POST",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables",
        query_params=frozenset(),
        body_params=frozenset({"name", "value"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get an environment variable": path parameters only; 200 with an `actions-variable`.
    RestOperation(
        operation_id="actions/get-environment-variable",
        method="GET",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Update an environment variable": body `name`, `value`; 204 on success.
    RestOperation(
        operation_id="actions/update-environment-variable",
        method="PATCH",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset({"name", "value"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete an environment variable": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-environment-variable",
        method="DELETE",
        path="/repos/{owner}/{repo}/environments/{environment_name}/variables/{name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a job for a workflow run": path parameters only; 200 with a `job`.
    RestOperation(
        operation_id="actions/get-job-for-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/jobs/{job_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Download job logs for a workflow run": path parameters only; `302` with a `Location` to the
    # archive, whose bytes `call` prints (#28 D3).
    RestOperation(
        operation_id="actions/download-job-logs-for-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/jobs/{job_id}/logs",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Download step logs for a workflow run job": path parameters only; `302` with a `Location` to the
    # archive, whose bytes `call` prints (#28 D3).
    RestOperation(
        operation_id="actions/download-step-logs-for-workflow-run-job",
        method="GET",
        path="/repos/{owner}/{repo}/actions/jobs/{job_id}/steps/{step_number}/logs",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List jobs for a workflow run attempt": page-based, items in `jobs`.
    RestOperation(
        operation_id="actions/list-jobs-for-workflow-run-attempt",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="jobs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "List jobs for a workflow run": page-based, items in `jobs`.
    RestOperation(
        operation_id="actions/list-jobs-for-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
        query_params=frozenset({"filter", "per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="jobs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Re-run a job from a workflow run": body `enable_debug_logging`, `enable_debugger`; 201 with an
    # `empty-object`.
    RestOperation(
        operation_id="actions/re-run-job-for-workflow-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/jobs/{job_id}/rerun",
        query_params=frozenset(),
        body_params=frozenset({"enable_debug_logging", "enable_debugger"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete a workflow run": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-workflow-run",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get the review history for a workflow run": path parameters only; 200 with an array of
    # `environment-approvals`.
    RestOperation(
        operation_id="actions/get-reviews-for-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/approvals",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Approve a workflow run for a fork pull request": path parameters only; 201 with an
    # `empty-object`.
    RestOperation(
        operation_id="actions/approve-workflow-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/approve",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a workflow run attempt": query `exclude_pull_requests`; 200 with a `workflow-run`.
    RestOperation(
        operation_id="actions/get-workflow-run-attempt",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}",
        query_params=frozenset({"exclude_pull_requests"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Download workflow run attempt logs": path parameters only; `302` with a `Location` to the
    # archive, whose bytes `call` prints (#28 D3).
    RestOperation(
        operation_id="actions/download-workflow-run-attempt-logs",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/logs",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Cancel a workflow run": path parameters only; 202 with an `empty-object`.
    RestOperation(
        operation_id="actions/cancel-workflow-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/cancel",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Review custom deployment protection rules for a workflow run": body `environment_name`,
    # `comment`, `state`; 204 on success.
    RestOperation(
        operation_id="actions/review-custom-gates-for-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/deployment_protection_rule",
        query_params=frozenset(),
        body_params=frozenset({"environment_name", "comment", "state"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Force cancel a workflow run": path parameters only; 202 with an `empty-object`.
    RestOperation(
        operation_id="actions/force-cancel-workflow-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/force-cancel",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Delete workflow run logs": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/delete-workflow-run-logs",
        method="DELETE",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get pending deployments for a workflow run": path parameters only; 200 with an array of
    # `pending-deployment`.
    RestOperation(
        operation_id="actions/get-pending-deployments-for-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Review pending deployments for a workflow run": body `environment_ids`, `state`, `comment`; 200
    # with an array of `deployment`.
    RestOperation(
        operation_id="actions/review-pending-deployments-for-run",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments",
        query_params=frozenset(),
        body_params=frozenset({"environment_ids", "state", "comment"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Re-run a workflow": body `enable_debug_logging`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/re-run-workflow",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
        query_params=frozenset(),
        body_params=frozenset({"enable_debug_logging"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Re-run failed jobs from a workflow run": body `enable_debug_logging`; 201 with an `empty-object`.
    RestOperation(
        operation_id="actions/re-run-workflow-failed-jobs",
        method="POST",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs",
        query_params=frozenset(),
        body_params=frozenset({"enable_debug_logging"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get workflow run usage": path parameters only; 200 with a `workflow-run-usage`.
    RestOperation(
        operation_id="actions/get-workflow-run-usage",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}/timing",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get a workflow": path parameters only; 200 with a `workflow`.
    RestOperation(
        operation_id="actions/get-workflow",
        method="GET",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Disable a workflow": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/disable-workflow",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/disable",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Create a workflow dispatch event": body `ref`, `inputs`, `return_run_details`; 200 with a
    # `workflow-dispatch-response`.
    RestOperation(
        operation_id="actions/create-workflow-dispatch",
        method="POST",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
        query_params=frozenset(),
        body_params=frozenset({"ref", "inputs", "return_run_details"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Enable a workflow": path parameters only; 204 on success.
    RestOperation(
        operation_id="actions/enable-workflow",
        method="PUT",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/enable",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/actions.md "Get workflow usage": path parameters only; 200 with a `workflow-usage`.
    RestOperation(
        operation_id="actions/get-workflow-usage",
        method="GET",
        path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/timing",
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
