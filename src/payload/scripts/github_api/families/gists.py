"""The ``gists`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "gists"
OPERATIONS = ()
PENDING = frozenset(
    {
        "gists/check-is-starred",
        "gists/create",
        "gists/create-comment",
        "gists/delete",
        "gists/delete-comment",
        "gists/fork",
        "gists/get",
        "gists/get-comment",
        "gists/get-revision",
        "gists/list",
        "gists/list-comments",
        "gists/list-commits",
        "gists/list-for-user",
        "gists/list-forks",
        "gists/list-public",
        "gists/list-starred",
        "gists/star",
        "gists/unstar",
        "gists/update",
        "gists/update-comment",
    }
)
