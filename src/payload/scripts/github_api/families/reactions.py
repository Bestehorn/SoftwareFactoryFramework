"""The ``reactions`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "reactions"
OPERATIONS = ()
PENDING = frozenset(
    {
        "reactions/create-for-commit-comment",
        "reactions/create-for-issue",
        "reactions/create-for-issue-comment",
        "reactions/create-for-pull-request-review-comment",
        "reactions/create-for-release",
        "reactions/delete-for-commit-comment",
        "reactions/delete-for-issue",
        "reactions/delete-for-issue-comment",
        "reactions/delete-for-pull-request-comment",
        "reactions/delete-for-release",
        "reactions/list-for-commit-comment",
        "reactions/list-for-issue",
        "reactions/list-for-issue-comment",
        "reactions/list-for-pull-request-review-comment",
        "reactions/list-for-release",
    }
)
