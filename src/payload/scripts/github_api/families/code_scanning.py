"""The ``code-scanning`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "code-scanning"
OPERATIONS = ()
PENDING = frozenset(
    {
        "code-scanning/commit-autofix",
        "code-scanning/create-autofix",
        "code-scanning/create-variant-analysis",
        "code-scanning/delete-analysis",
        "code-scanning/delete-codeql-database",
        "code-scanning/get-ai-scan-enablement",
        "code-scanning/get-ai-scan-enablement-for-org",
        "code-scanning/get-alert",
        "code-scanning/get-analysis",
        "code-scanning/get-autofix",
        "code-scanning/get-codeql-database",
        "code-scanning/get-default-setup",
        "code-scanning/get-sarif",
        "code-scanning/get-variant-analysis",
        "code-scanning/get-variant-analysis-repo-task",
        "code-scanning/list-alert-instances",
        "code-scanning/list-alerts-for-org",
        "code-scanning/list-alerts-for-repo",
        "code-scanning/list-codeql-databases",
        "code-scanning/list-recent-analyses",
        "code-scanning/update-ai-scan-enablement",
        "code-scanning/update-ai-scan-enablement-for-org",
        "code-scanning/update-alert",
        "code-scanning/update-default-setup",
        "code-scanning/upload-sarif",
    }
)
