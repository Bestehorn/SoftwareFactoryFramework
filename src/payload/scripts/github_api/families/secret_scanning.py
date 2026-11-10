"""The ``secret-scanning`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "secret-scanning"
OPERATIONS = ()
PENDING = frozenset(
    {
        "secret-scanning/bulk-create-org-custom-patterns",
        "secret-scanning/bulk-create-repo-custom-patterns",
        "secret-scanning/bulk-delete-org-custom-patterns",
        "secret-scanning/bulk-delete-repo-custom-patterns",
        "secret-scanning/create-push-protection-bypass",
        "secret-scanning/get-alert",
        "secret-scanning/get-scan-history",
        "secret-scanning/list-alerts-for-org",
        "secret-scanning/list-alerts-for-repo",
        "secret-scanning/list-locations-for-alert",
        "secret-scanning/list-org-custom-patterns",
        "secret-scanning/list-org-pattern-configs",
        "secret-scanning/list-repo-custom-patterns",
        "secret-scanning/update-alert",
        "secret-scanning/update-org-custom-pattern",
        "secret-scanning/update-org-pattern-configs",
        "secret-scanning/update-repo-custom-pattern",
    }
)
