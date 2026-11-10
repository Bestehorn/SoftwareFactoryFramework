"""The ``activity`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "activity"
OPERATIONS = ()
PENDING = frozenset(
    {
        "activity/check-repo-is-starred-by-authenticated-user",
        "activity/delete-repo-subscription",
        "activity/delete-thread-subscription",
        "activity/get-feeds",
        "activity/get-repo-subscription",
        "activity/get-stargazer-count-for-repo",
        "activity/get-stargazer-history-for-repo",
        "activity/get-thread",
        "activity/get-thread-subscription-for-authenticated-user",
        "activity/list-events-for-authenticated-user",
        "activity/list-notifications-for-authenticated-user",
        "activity/list-org-events-for-authenticated-user",
        "activity/list-public-events",
        "activity/list-public-events-for-repo-network",
        "activity/list-public-events-for-user",
        "activity/list-public-org-events",
        "activity/list-received-events-for-user",
        "activity/list-received-public-events-for-user",
        "activity/list-repo-events",
        "activity/list-repo-notifications-for-authenticated-user",
        "activity/list-repos-starred-by-authenticated-user",
        "activity/list-repos-starred-by-user",
        "activity/list-repos-watched-by-user",
        "activity/list-stargazers-for-repo",
        "activity/list-watched-repos-for-authenticated-user",
        "activity/list-watchers-for-repo",
        "activity/mark-notifications-as-read",
        "activity/mark-repo-notifications-as-read",
        "activity/mark-thread-as-done",
        "activity/mark-thread-as-read",
        "activity/set-repo-subscription",
        "activity/set-thread-subscription",
        "activity/star-repo-for-authenticated-user",
        "activity/unstar-repo-for-authenticated-user",
    }
)
