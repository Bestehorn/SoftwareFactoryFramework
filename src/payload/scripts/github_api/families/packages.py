"""The ``packages`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "packages"
OPERATIONS = ()
PENDING = frozenset(
    {
        "packages/delete-package-for-authenticated-user",
        "packages/delete-package-for-org",
        "packages/delete-package-for-user",
        "packages/delete-package-version-for-authenticated-user",
        "packages/delete-package-version-for-org",
        "packages/delete-package-version-for-user",
        "packages/get-all-package-versions-for-package-owned-by-authenticated-user",
        "packages/get-all-package-versions-for-package-owned-by-org",
        "packages/get-all-package-versions-for-package-owned-by-user",
        "packages/get-package-for-authenticated-user",
        "packages/get-package-for-organization",
        "packages/get-package-for-user",
        "packages/get-package-version-for-authenticated-user",
        "packages/get-package-version-for-organization",
        "packages/get-package-version-for-user",
        "packages/list-docker-migration-conflicting-packages-for-authenticated-user",
        "packages/list-docker-migration-conflicting-packages-for-organization",
        "packages/list-docker-migration-conflicting-packages-for-user",
        "packages/list-packages-for-authenticated-user",
        "packages/list-packages-for-organization",
        "packages/list-packages-for-user",
        "packages/restore-package-for-authenticated-user",
        "packages/restore-package-for-org",
        "packages/restore-package-for-user",
        "packages/restore-package-version-for-authenticated-user",
        "packages/restore-package-version-for-org",
        "packages/restore-package-version-for-user",
    }
)
