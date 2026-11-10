"""The ``dependabot`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "dependabot"
OPERATIONS = ()
PENDING = frozenset(
    {
        "dependabot/add-selected-repo-to-org-secret",
        "dependabot/create-or-update-org-secret",
        "dependabot/create-or-update-repo-secret",
        "dependabot/delete-org-secret",
        "dependabot/delete-repo-secret",
        "dependabot/get-alert",
        "dependabot/get-org-public-key",
        "dependabot/get-org-secret",
        "dependabot/get-repo-public-key",
        "dependabot/get-repo-secret",
        "dependabot/get-repository-runner-settings",
        "dependabot/list-alerts-for-enterprise",
        "dependabot/list-alerts-for-org",
        "dependabot/list-alerts-for-repo",
        "dependabot/list-org-secrets",
        "dependabot/list-repo-secrets",
        "dependabot/list-selected-repos-for-org-secret",
        "dependabot/remove-selected-repo-from-org-secret",
        "dependabot/repository-access-for-enterprise",
        "dependabot/repository-access-for-org",
        "dependabot/set-repository-access-default-level",
        "dependabot/set-repository-access-default-level-for-enterprise",
        "dependabot/set-repository-runner-settings",
        "dependabot/set-selected-repos-for-org-secret",
        "dependabot/update-alert",
        "dependabot/update-repository-access-for-enterprise",
        "dependabot/update-repository-access-for-org",
    }
)
