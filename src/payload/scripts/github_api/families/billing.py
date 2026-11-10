"""The ``billing`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "billing"
OPERATIONS = ()
PENDING = frozenset(
    {
        "billing/create-organization-budget",
        "billing/delete-budget-org",
        "billing/get-all-budgets-org",
        "billing/get-budget-org",
        "billing/get-github-billing-ai-credit-usage-report-org",
        "billing/get-github-billing-ai-credit-usage-report-user",
        "billing/get-github-billing-premium-request-usage-report-org",
        "billing/get-github-billing-premium-request-usage-report-user",
        "billing/get-github-billing-usage-report-org",
        "billing/get-github-billing-usage-report-user",
        "billing/get-github-billing-usage-summary-report-org",
        "billing/get-github-billing-usage-summary-report-user",
        "billing/update-budget-org",
    }
)
