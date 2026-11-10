"""The "Only in GraphQL" capabilities of the GitHub API (design D2, D5).

``OPERATIONS`` holds the ``GraphQLOperation`` records that serve a capability. Part 1 declares none, so every first
cell of the "Only in GraphQL" table of the GitHub API reference's GraphQL conventions is on
``PENDING_CAPABILITIES``, verbatim and in the table's order.
"""

OPERATIONS = ()
PENDING_CAPABILITIES = frozenset(
    {
        "Repository discussions",
        "Create, update, delete, copy or link a Projects v2 project",
        "Auto-merge on or off",
        "Draft to ready and back",
        "Resolve review threads",
        "Hide comments",
        "Move an issue to another repo",
        "Pin an issue",
        "Revert a PR",
        "Read a merge queue, remove an entry",
        "Sponsors",
        "Multi-file commit in one call",
        "Branch protection with wildcard patterns",
    }
)
