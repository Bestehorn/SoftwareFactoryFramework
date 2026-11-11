"""The ``security-risk-management`` endpoint family of the GitLab wrapper: security policy settings, dependency list
exports, external status checks, the policy store, vulnerabilities, vulnerability exports and vulnerability findings.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/security-risk-management.md`` (issue #42, the security slice of the wrapper rewrite;
issue #41 design.md D8): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body
attribute with the table's Type column as its ``Kind`` (``object`` a ``HASH``, ``array`` and ``string array`` an
``ARRAY``). A ``GET`` section headed "List", and "Retrieve project external status check services", pages by offset;
every other record does not page. "Create a dependency list export" has three endpoints and one ID, so it has one
record per endpoint (issue #63, design.md D1, D8): its base record, the first of its ID, maps the ``/projects/:id/``
endpoint its endpoint line lists first, and the records after it the line's other two, in its order, each a copy of the
base record but for its path and any ``Param`` naming a path parameter of its own path. ``call`` sends the base record
without ``--endpoint`` and another when ``--endpoint 'POST /groups/:id/dependency_list_exports'`` names it. Every index
key of the family has its record, so ``PENDING`` is empty.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "security-risk-management"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Compliance and policy settings API: Retrieve security policy settings"; the section has no attribute table.
    RestOperation(
        operation_id="security-risk-management#retrieve-security-policy-settings",
        method="GET",
        path="/admin/security/compliance_policy_settings",
    ),
    # "Compliance and policy settings API: Update security policy settings".
    RestOperation(
        operation_id="security-risk-management#update-security-policy-settings",
        method="PUT",
        path="/admin/security/compliance_policy_settings",
        params=(Param(name="csp_namespace_id", location=Location.BODY, required=True),),
    ),
    # "Dependency list export API: Create a dependency list export"; the base record, its `/projects/:id/` endpoint.
    RestOperation(
        operation_id="security-risk-management#create-a-dependency-list-export",
        method="POST",
        path="/projects/:id/dependency_list_exports",
        params=(
            Param(name="export_type", location=Location.BODY, required=True),
            Param(name="send_email", location=Location.BODY),
        ),
    ),
    # "Dependency list export API: Create a dependency list export"; its group endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="security-risk-management#create-a-dependency-list-export",
        method="POST",
        path="/groups/:id/dependency_list_exports",
        params=(
            Param(name="export_type", location=Location.BODY, required=True),
            Param(name="send_email", location=Location.BODY),
        ),
    ),
    # "Dependency list export API: Create a dependency list export"; its pipeline endpoint (issue #63, design.md D8).
    RestOperation(
        operation_id="security-risk-management#create-a-dependency-list-export",
        method="POST",
        path="/pipelines/:id/dependency_list_exports",
        params=(
            Param(name="export_type", location=Location.BODY, required=True),
            Param(name="send_email", location=Location.BODY),
        ),
    ),
    # "Dependency list export API: Retrieve a single dependency list export".
    RestOperation(
        operation_id="security-risk-management#retrieve-a-single-dependency-list-export",
        method="GET",
        path="/dependency_list_exports/:id",
    ),
    # "Dependency list export API: Download dependency list export"; the answer is printed as its bytes (DL-002).
    RestOperation(
        operation_id="security-risk-management#download-dependency-list-export",
        method="GET",
        path="/dependency_list_exports/:id/download",
    ),
    # "External Status Checks API: Retrieve project external status check services"; offset paging (DL-006).
    RestOperation(
        operation_id="security-risk-management#retrieve-project-external-status-check-services",
        method="GET",
        path="/projects/:id/external_status_checks",
        paging=Paging.OFFSET,
    ),
    # "External Status Checks API: Create external status check service"; `shared_secret` is passed in argv.
    RestOperation(
        operation_id="security-risk-management#create-external-status-check-service",
        method="POST",
        path="/projects/:id/external_status_checks",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="external_url", location=Location.BODY, required=True),
            Param(name="shared_secret", location=Location.BODY),
            Param(name="protected_branch_ids", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "External Status Checks API: Update external status check service"; `shared_secret` is passed in argv.
    RestOperation(
        operation_id="security-risk-management#update-external-status-check-service",
        method="PUT",
        path="/projects/:id/external_status_checks/:check_id",
        params=(
            Param(name="name", location=Location.BODY),
            Param(name="external_url", location=Location.BODY),
            Param(name="shared_secret", location=Location.BODY),
            Param(name="protected_branch_ids", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "External Status Checks API: Delete external status check service".
    RestOperation(
        operation_id="security-risk-management#delete-external-status-check-service",
        method="DELETE",
        path="/projects/:id/external_status_checks/:check_id",
    ),
    # "External Status Checks API: List all status checks for a merge request".
    RestOperation(
        operation_id="security-risk-management#list-all-status-checks-for-a-merge-request",
        method="GET",
        path="/projects/:id/merge_requests/:merge_request_iid/status_checks",
        paging=Paging.OFFSET,
    ),
    # "External Status Checks API: Set status of an external status check".
    RestOperation(
        operation_id="security-risk-management#set-status-of-an-external-status-check",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/status_check_responses",
        params=(
            Param(name="sha", location=Location.BODY, required=True),
            Param(name="external_status_check_id", location=Location.BODY, required=True),
            Param(name="status", location=Location.BODY),
        ),
    ),
    # "External Status Checks API: Retry failed status check for a merge request".
    RestOperation(
        operation_id="security-risk-management#retry-failed-status-check-for-a-merge-request",
        method="POST",
        path="/projects/:id/merge_requests/:merge_request_iid/status_checks/:external_status_check_id/retry",
    ),
    # "Policy store API: List all triggers"; the section has no attribute table.
    RestOperation(
        operation_id="security-risk-management#list-all-triggers",
        method="GET",
        path="/security/policy_store/triggers",
        paging=Paging.OFFSET,
    ),
    # "Policy store API: List all actions"; the section has no attribute table.
    RestOperation(
        operation_id="security-risk-management#list-all-actions",
        method="GET",
        path="/security/policy_store/actions",
        paging=Paging.OFFSET,
    ),
    # "Policy store API: List all rule kinds"; the section has no attribute table.
    RestOperation(
        operation_id="security-risk-management#list-all-rule-kinds",
        method="GET",
        path="/security/policy_store/rules",
        paging=Paging.OFFSET,
    ),
    # "Policy store API: List all organization policies".
    RestOperation(
        operation_id="security-risk-management#list-all-organization-policies",
        method="GET",
        path="/organizations/:id/security/policy_store",
        params=(
            Param(name="lifecycle_state", location=Location.QUERY),
            Param(name="namespace_ids", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="trigger_type", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Policy store API: Retrieve an organization policy".
    RestOperation(
        operation_id="security-risk-management#retrieve-an-organization-policy",
        method="GET",
        path="/organizations/:id/security/policy_store/:policy_id",
    ),
    # "Policy store API: Create an organization policy".
    RestOperation(
        operation_id="security-risk-management#create-an-organization-policy",
        method="POST",
        path="/organizations/:id/security/policy_store",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="rules", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="trigger_type", location=Location.BODY, required=True),
            Param(name="actions", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="lifecycle_state", location=Location.BODY),
            Param(name="mode", location=Location.BODY),
            Param(name="policy_scope", location=Location.BODY, kind=Kind.HASH),
            Param(name="scope_rego", location=Location.BODY),
        ),
    ),
    # "Policy store API: Update an organization policy".
    RestOperation(
        operation_id="security-risk-management#update-an-organization-policy",
        method="PATCH",
        path="/organizations/:id/security/policy_store/:policy_id",
        params=(
            Param(name="actions", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="lifecycle_state", location=Location.BODY),
            Param(name="mode", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="policy_scope", location=Location.BODY, kind=Kind.HASH),
            Param(name="rules", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="scope_rego", location=Location.BODY),
            Param(name="trigger_type", location=Location.BODY),
        ),
    ),
    # "Policy store API: Delete an organization policy".
    RestOperation(
        operation_id="security-risk-management#delete-an-organization-policy",
        method="DELETE",
        path="/organizations/:id/security/policy_store/:policy_id",
    ),
    # "Policy store API: List all group policies".
    RestOperation(
        operation_id="security-risk-management#list-all-group-policies",
        method="GET",
        path="/groups/:id/security/policy_store",
        params=(
            Param(name="lifecycle_state", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="trigger_type", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Policy store API: Retrieve a group policy".
    RestOperation(
        operation_id="security-risk-management#retrieve-a-group-policy",
        method="GET",
        path="/groups/:id/security/policy_store/:policy_id",
    ),
    # "Policy store API: Create a group policy".
    RestOperation(
        operation_id="security-risk-management#create-a-group-policy",
        method="POST",
        path="/groups/:id/security/policy_store",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="rules", location=Location.BODY, kind=Kind.ARRAY, required=True),
            Param(name="trigger_type", location=Location.BODY, required=True),
            Param(name="actions", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="lifecycle_state", location=Location.BODY),
            Param(name="mode", location=Location.BODY),
            Param(name="policy_scope", location=Location.BODY, kind=Kind.HASH),
            Param(name="scope_rego", location=Location.BODY),
        ),
    ),
    # "Policy store API: Update a group policy".
    RestOperation(
        operation_id="security-risk-management#update-a-group-policy",
        method="PATCH",
        path="/groups/:id/security/policy_store/:policy_id",
        params=(
            Param(name="actions", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="description", location=Location.BODY),
            Param(name="lifecycle_state", location=Location.BODY),
            Param(name="mode", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="policy_scope", location=Location.BODY, kind=Kind.HASH),
            Param(name="rules", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="scope_rego", location=Location.BODY),
            Param(name="trigger_type", location=Location.BODY),
        ),
    ),
    # "Policy store API: Delete a group policy".
    RestOperation(
        operation_id="security-risk-management#delete-a-group-policy",
        method="DELETE",
        path="/groups/:id/security/policy_store/:policy_id",
    ),
    # "Project vulnerabilities API: List project vulnerabilities".
    RestOperation(
        operation_id="security-risk-management#list-project-vulnerabilities",
        method="GET",
        path="/projects/:id/vulnerabilities",
        paging=Paging.OFFSET,
    ),
    # "Project vulnerabilities API: Create a vulnerability".
    RestOperation(
        operation_id="security-risk-management#create-a-vulnerability",
        method="POST",
        path="/projects/:id/vulnerabilities",
        params=(Param(name="finding_id", location=Location.BODY, required=True),),
    ),
    # "Vulnerabilities API: Retrieve a vulnerability".
    RestOperation(
        operation_id="security-risk-management#retrieve-a-vulnerability",
        method="GET",
        path="/vulnerabilities/:id",
    ),
    # "Vulnerabilities API: Confirm a vulnerability".
    RestOperation(
        operation_id="security-risk-management#confirm-a-vulnerability",
        method="POST",
        path="/vulnerabilities/:id/confirm",
    ),
    # "Vulnerabilities API: Resolve a vulnerability".
    RestOperation(
        operation_id="security-risk-management#resolve-a-vulnerability",
        method="POST",
        path="/vulnerabilities/:id/resolve",
    ),
    # "Vulnerabilities API: Dismiss a vulnerability".
    RestOperation(
        operation_id="security-risk-management#dismiss-a-vulnerability",
        method="POST",
        path="/vulnerabilities/:id/dismiss",
    ),
    # "Vulnerabilities API: Revert a vulnerability to the detected state".
    RestOperation(
        operation_id="security-risk-management#revert-a-vulnerability-to-the-detected-state",
        method="POST",
        path="/vulnerabilities/:id/revert",
    ),
    # "Vulnerability archive export API: Create an export for archived vulnerabilities".
    RestOperation(
        operation_id="security-risk-management#create-an-export-for-archived-vulnerabilities",
        method="POST",
        path="/security/projects/:id/vulnerability_archive_exports",
        params=(
            Param(name="start_date", location=Location.BODY, required=True),
            Param(name="end_date", location=Location.BODY, required=True),
            Param(name="export_format", location=Location.BODY),
        ),
    ),
    # "Vulnerability archive export API: Retrieve a vulnerability archive export".
    RestOperation(
        operation_id="security-risk-management#retrieve-a-vulnerability-archive-export",
        method="GET",
        path="/security/vulnerability_archive_exports/:id",
    ),
    # "Vulnerability archive export API: Download a vulnerability archive export"; the answer is printed as its
    # bytes (DL-002).
    RestOperation(
        operation_id="security-risk-management#download-a-vulnerability-archive-export",
        method="GET",
        path="/security/vulnerability_archive_exports/:id/download",
    ),
    # "Vulnerability export API: Create a project-level vulnerability export".
    RestOperation(
        operation_id="security-risk-management#create-a-project-level-vulnerability-export",
        method="POST",
        path="/security/projects/:id/vulnerability_exports",
        params=(
            Param(name="send_email", location=Location.BODY),
            Param(name="export_format", location=Location.BODY),
            Param(name="report_data", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Vulnerability export API: Create a group-level vulnerability export".
    RestOperation(
        operation_id="security-risk-management#create-a-group-level-vulnerability-export",
        method="POST",
        path="/security/groups/:id/vulnerability_exports",
        params=(
            Param(name="export_format", location=Location.BODY),
            Param(name="report_data", location=Location.BODY, kind=Kind.HASH),
        ),
    ),
    # "Vulnerability export API: Create an instance-level vulnerability export"; the section has no attribute table.
    RestOperation(
        operation_id="security-risk-management#create-an-instance-level-vulnerability-export",
        method="POST",
        path="/security/vulnerability_exports",
    ),
    # "Vulnerability export API: Retrieve a vulnerability export".
    RestOperation(
        operation_id="security-risk-management#retrieve-a-vulnerability-export",
        method="GET",
        path="/security/vulnerability_exports/:id",
    ),
    # "Vulnerability export API: Download a vulnerability export"; the answer is printed as its bytes (DL-002).
    RestOperation(
        operation_id="security-risk-management#download-a-vulnerability-export",
        method="GET",
        path="/security/vulnerability_exports/:id/download",
    ),
    # "Vulnerability Findings API: List all project vulnerability findings"; `report_type` and `severity` are string
    # arrays.
    RestOperation(
        operation_id="security-risk-management#list-all-project-vulnerability-findings",
        method="GET",
        path="/projects/:id/vulnerability_findings",
        params=(
            Param(name="report_type", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="scope", location=Location.QUERY),
            Param(name="severity", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="pipeline_id", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
)

# Every index key of the family has its record: the two endpoints this held are records of "Create a dependency list
# export" (issue #63 AC-1.1, AC-1.3).
PENDING: FrozenSet[Tuple[str, str]] = frozenset()
