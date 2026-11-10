"""The ``interactions`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "interactions"
OPERATIONS = ()
PENDING = frozenset(
    {
        "interactions/get-pull-request-bypass-list-for-repo",
        "interactions/get-pull-request-creation-cap-for-org",
        "interactions/get-pull-request-creation-cap-for-repo",
        "interactions/get-restrictions-for-authenticated-user",
        "interactions/get-restrictions-for-org",
        "interactions/get-restrictions-for-repo",
        "interactions/remove-pull-request-bypass-list-for-repo",
        "interactions/remove-restrictions-for-authenticated-user",
        "interactions/remove-restrictions-for-org",
        "interactions/remove-restrictions-for-repo",
        "interactions/set-pull-request-bypass-list-for-repo",
        "interactions/set-restrictions-for-authenticated-user",
        "interactions/set-restrictions-for-org",
        "interactions/set-restrictions-for-repo",
        "interactions/update-pull-request-creation-cap-for-org",
        "interactions/update-pull-request-creation-cap-for-repo",
    }
)
