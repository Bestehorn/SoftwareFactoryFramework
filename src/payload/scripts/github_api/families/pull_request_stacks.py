"""The ``pull-request-stacks`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "pull-request-stacks"
OPERATIONS = ()
PENDING = frozenset(
    {
        "pull-request-stacks/add",
        "pull-request-stacks/create",
        "pull-request-stacks/get",
        "pull-request-stacks/list",
        "pull-request-stacks/unstack",
    }
)
