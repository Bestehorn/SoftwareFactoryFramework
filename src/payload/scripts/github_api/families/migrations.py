"""The ``migrations`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "migrations"
OPERATIONS = ()
PENDING = frozenset(
    {
        "migrations/cancel-import",
        "migrations/delete-archive-for-authenticated-user",
        "migrations/delete-archive-for-org",
        "migrations/download-archive-for-org",
        "migrations/get-archive-for-authenticated-user",
        "migrations/get-commit-authors",
        "migrations/get-import-status",
        "migrations/get-large-files",
        "migrations/get-status-for-authenticated-user",
        "migrations/get-status-for-org",
        "migrations/list-for-authenticated-user",
        "migrations/list-for-org",
        "migrations/list-repos-for-authenticated-user",
        "migrations/list-repos-for-org",
        "migrations/map-commit-author",
        "migrations/set-lfs-preference",
        "migrations/start-for-authenticated-user",
        "migrations/start-for-org",
        "migrations/start-import",
        "migrations/unlock-repo-for-authenticated-user",
        "migrations/unlock-repo-for-org",
        "migrations/update-import",
    }
)
