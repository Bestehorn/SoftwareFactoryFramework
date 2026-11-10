"""The ``search`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "search"
OPERATIONS = ()
PENDING = frozenset(
    {
        "search/code",
        "search/commits",
        "search/issues-and-pull-requests",
        "search/labels",
        "search/repos",
        "search/topics",
        "search/users",
    }
)
