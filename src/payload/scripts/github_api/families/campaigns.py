"""The ``campaigns`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "campaigns"
OPERATIONS = ()
PENDING = frozenset(
    {
        "campaigns/create-campaign",
        "campaigns/delete-campaign",
        "campaigns/get-campaign-summary",
        "campaigns/list-org-campaigns",
        "campaigns/update-campaign",
    }
)
