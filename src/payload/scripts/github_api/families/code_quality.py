"""The ``code-quality`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "code-quality"
OPERATIONS = ()
PENDING = frozenset(
    {
        "code-quality/get-finding",
        "code-quality/get-setup",
        "code-quality/list-findings-for-repo",
        "code-quality/update-setup",
    }
)
