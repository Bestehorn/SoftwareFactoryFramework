"""The ``agents`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "agents"
OPERATIONS = ()
PENDING = frozenset(
    {
        "agents/add-selected-repo-to-org-secret",
        "agents/add-selected-repo-to-org-variable",
        "agents/create-or-update-org-secret",
        "agents/create-or-update-repo-secret",
        "agents/create-org-variable",
        "agents/create-repo-variable",
        "agents/delete-org-secret",
        "agents/delete-org-variable",
        "agents/delete-repo-secret",
        "agents/delete-repo-variable",
        "agents/get-org-public-key",
        "agents/get-org-secret",
        "agents/get-org-variable",
        "agents/get-repo-public-key",
        "agents/get-repo-secret",
        "agents/get-repo-variable",
        "agents/list-org-secrets",
        "agents/list-org-variables",
        "agents/list-repo-organization-secrets",
        "agents/list-repo-organization-variables",
        "agents/list-repo-secrets",
        "agents/list-repo-variables",
        "agents/list-selected-repos-for-org-secret",
        "agents/list-selected-repos-for-org-variable",
        "agents/remove-selected-repo-from-org-secret",
        "agents/remove-selected-repo-from-org-variable",
        "agents/set-selected-repos-for-org-secret",
        "agents/set-selected-repos-for-org-variable",
        "agents/update-org-variable",
        "agents/update-repo-variable",
    }
)
