"""The ``security-advisories`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "security-advisories"
OPERATIONS = ()
PENDING = frozenset(
    {
        "security-advisories/create-fork",
        "security-advisories/create-private-vulnerability-report",
        "security-advisories/create-repository-advisory",
        "security-advisories/create-repository-advisory-comment",
        "security-advisories/create-repository-advisory-cve-request",
        "security-advisories/get-global-advisory",
        "security-advisories/get-repository-advisory",
        "security-advisories/get-repository-advisory-comment",
        "security-advisories/list-global-advisories",
        "security-advisories/list-org-repository-advisories",
        "security-advisories/list-repository-advisories",
        "security-advisories/list-repository-advisory-comments",
        "security-advisories/update-repository-advisory",
        "security-advisories/update-repository-advisory-comment",
    }
)
