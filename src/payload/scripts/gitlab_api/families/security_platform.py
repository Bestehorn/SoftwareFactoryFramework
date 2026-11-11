"""The ``security-platform`` endpoint family of the GitLab wrapper: attestations, the CI/CD job token scope, the
Dependency Firewall, project-level secure files and Secrets Manager access tokens.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/security-platform.md`` (issue #42, the security slice of the wrapper rewrite;
issue #41 design.md D8): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body
attribute with the table's Type column as its ``Kind`` (a ``form`` row is sent in the body). A ``GET`` section headed
"List" pages by offset; every other record does not page. Every section has one endpoint, so each index key of the
family has its record and ``PENDING`` is empty.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "security-platform"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Attestations API: List all attestations".
    RestOperation(
        operation_id="security-platform#list-all-attestations",
        method="GET",
        path="/projects/:id/attestations/:subject_digest",
        paging=Paging.OFFSET,
    ),
    # "Attestations API: Download an attestation"; the answer is printed as its bytes (DL-002).
    RestOperation(
        operation_id="security-platform#download-an-attestation",
        method="GET",
        path="/projects/:id/attestations/:attestation_iid/download",
    ),
    # "CI/CD job token scope API: Retrieve the CI/CD job token access settings for a project".
    RestOperation(
        operation_id="security-platform#retrieve-the-cicd-job-token-access-settings-for-a-project",
        method="GET",
        path="/projects/:id/job_token_scope",
    ),
    # "CI/CD job token scope API: Update the CI/CD job token access settings for a project".
    RestOperation(
        operation_id="security-platform#update-the-cicd-job-token-access-settings-for-a-project",
        method="PATCH",
        path="/projects/:id/job_token_scope",
        params=(Param(name="enabled", location=Location.BODY, required=True),),
    ),
    # "CI/CD job token scope API: List all projects in a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#list-all-projects-in-a-cicd-job-token-allowlist",
        method="GET",
        path="/projects/:id/job_token_scope/allowlist",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "CI/CD job token scope API: Add a project to a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#add-a-project-to-a-cicd-job-token-allowlist",
        method="POST",
        path="/projects/:id/job_token_scope/allowlist",
        params=(Param(name="target_project_id", location=Location.BODY, required=True),),
    ),
    # "CI/CD job token scope API: Delete a project from a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#delete-a-project-from-a-cicd-job-token-allowlist",
        method="DELETE",
        path="/projects/:id/job_token_scope/allowlist/:target_project_id",
    ),
    # "CI/CD job token scope API: List all groups in a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#list-all-groups-in-a-cicd-job-token-allowlist",
        method="GET",
        path="/projects/:id/job_token_scope/groups_allowlist",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "CI/CD job token scope API: Add a group to a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#add-a-group-to-a-cicd-job-token-allowlist",
        method="POST",
        path="/projects/:id/job_token_scope/groups_allowlist",
        params=(Param(name="target_group_id", location=Location.BODY, required=True),),
    ),
    # "CI/CD job token scope API: Delete a group from a CI/CD job token allowlist".
    RestOperation(
        operation_id="security-platform#delete-a-group-from-a-cicd-job-token-allowlist",
        method="DELETE",
        path="/projects/:id/job_token_scope/groups_allowlist/:target_group_id",
    ),
    # "Dependency Firewall API: Retrieve status of Dependency Firewall for a project".
    RestOperation(
        operation_id="security-platform#retrieve-status-of-dependency-firewall-for-a-project",
        method="GET",
        path="/projects/:id/dependency_firewall/enablement",
    ),
    # "Dependency Firewall API: Evaluate a package against Dependency Firewall policies for a project".
    RestOperation(
        operation_id="security-platform#evaluate-a-package-against-dependency-firewall-policies-for-a-project",
        method="POST",
        path="/projects/:id/dependency_firewall/evaluate",
        params=(
            Param(name="ecosystem", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="version", location=Location.BODY, required=True),
            Param(name="operation", location=Location.BODY),
        ),
    ),
    # "Project-level Secure Files API: List all secure files for a project".
    RestOperation(
        operation_id="security-platform#list-all-secure-files-for-a-project",
        method="GET",
        path="/projects/:project_id/secure_files",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Project-level Secure Files API: Retrieve details of a secure file".
    RestOperation(
        operation_id="security-platform#retrieve-details-of-a-secure-file",
        method="GET",
        path="/projects/:project_id/secure_files/:id",
    ),
    # "Project-level Secure Files API: Create a secure file"; `file` is the `form` row noted "file upload", so a call
    # that passes it is sent as a multipart body.
    RestOperation(
        operation_id="security-platform#create-a-secure-file",
        method="POST",
        path="/projects/:project_id/secure_files",
        params=(
            Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="name", location=Location.BODY, required=True),
        ),
    ),
    # "Project-level Secure Files API: Download a secure file"; the answer is printed as its bytes (DL-002).
    RestOperation(
        operation_id="security-platform#download-a-secure-file",
        method="GET",
        path="/projects/:project_id/secure_files/:id/download",
    ),
    # "Project-level Secure Files API: Delete a secure file".
    RestOperation(
        operation_id="security-platform#delete-a-secure-file",
        method="DELETE",
        path="/projects/:project_id/secure_files/:id",
    ),
    # "Secrets Manager API: Create a Secrets Manager access token for a project"; the printed answer holds the JWT
    # `provider.vault.auth.jwt.token`.
    RestOperation(
        operation_id="security-platform#create-a-secrets-manager-access-token-for-a-project",
        method="POST",
        path="/projects/:id/secrets_manager/access_token",
    ),
    # "Secrets Manager API: Create a Secrets Manager access token for a group".
    RestOperation(
        operation_id="security-platform#create-a-secrets-manager-access-token-for-a-group",
        method="POST",
        path="/groups/:id/secrets_manager/access_token",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
