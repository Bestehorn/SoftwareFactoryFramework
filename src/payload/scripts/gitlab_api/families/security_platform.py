"""GitLab REST endpoint family security-platform: no records yet; each index key it owns is pending."""

FAMILY = "security-platform"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/projects/:id/job_token_scope/allowlist/:target_project_id"),
        ("DELETE", "/projects/:id/job_token_scope/groups_allowlist/:target_group_id"),
        ("DELETE", "/projects/:project_id/secure_files/:id"),
        ("GET", "/projects/:id/attestations/:attestation_iid/download"),
        ("GET", "/projects/:id/attestations/:subject_digest"),
        ("GET", "/projects/:id/dependency_firewall/enablement"),
        ("GET", "/projects/:id/job_token_scope"),
        ("GET", "/projects/:id/job_token_scope/allowlist"),
        ("GET", "/projects/:id/job_token_scope/groups_allowlist"),
        ("GET", "/projects/:project_id/secure_files"),
        ("GET", "/projects/:project_id/secure_files/:id"),
        ("GET", "/projects/:project_id/secure_files/:id/download"),
        ("PATCH", "/projects/:id/job_token_scope"),
        ("POST", "/groups/:id/secrets_manager/access_token"),
        ("POST", "/projects/:id/dependency_firewall/evaluate"),
        ("POST", "/projects/:id/job_token_scope/allowlist"),
        ("POST", "/projects/:id/job_token_scope/groups_allowlist"),
        ("POST", "/projects/:id/secrets_manager/access_token"),
        ("POST", "/projects/:project_id/secure_files"),
    }
)
