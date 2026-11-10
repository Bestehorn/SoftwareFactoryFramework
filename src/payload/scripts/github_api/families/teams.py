"""The ``teams`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "teams"
OPERATIONS = ()
PENDING = frozenset(
    {
        "teams/add-member-legacy",
        "teams/add-or-update-membership-for-user-in-org",
        "teams/add-or-update-membership-for-user-legacy",
        "teams/add-or-update-repo-permissions-in-org",
        "teams/add-or-update-repo-permissions-legacy",
        "teams/check-permissions-for-repo-in-org",
        "teams/check-permissions-for-repo-legacy",
        "teams/create",
        "teams/delete-in-org",
        "teams/delete-legacy",
        "teams/get-by-name",
        "teams/get-legacy",
        "teams/get-member-legacy",
        "teams/get-membership-for-user-in-org",
        "teams/get-membership-for-user-legacy",
        "teams/list",
        "teams/list-child-in-org",
        "teams/list-child-legacy",
        "teams/list-for-authenticated-user",
        "teams/list-members-in-org",
        "teams/list-members-legacy",
        "teams/list-pending-invitations-in-org",
        "teams/list-pending-invitations-legacy",
        "teams/list-repos-in-org",
        "teams/list-repos-legacy",
        "teams/remove-member-legacy",
        "teams/remove-membership-for-user-in-org",
        "teams/remove-membership-for-user-legacy",
        "teams/remove-repo-in-org",
        "teams/remove-repo-legacy",
        "teams/update-in-org",
        "teams/update-legacy",
    }
)
