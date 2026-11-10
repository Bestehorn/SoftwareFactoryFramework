"""The ``api-insights`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "api-insights"
OPERATIONS = ()
PENDING = frozenset(
    {
        "api-insights/get-route-stats-by-actor",
        "api-insights/get-subject-stats",
        "api-insights/get-summary-stats",
        "api-insights/get-summary-stats-by-actor",
        "api-insights/get-summary-stats-by-user",
        "api-insights/get-time-stats",
        "api-insights/get-time-stats-by-actor",
        "api-insights/get-time-stats-by-user",
        "api-insights/get-user-stats",
    }
)
