"""The ``agent-merge`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "agent-merge"
OPERATIONS = ()
PENDING = frozenset(
    {
        "agent-merge/delete-agent-merge-enrollment",
        "agent-merge/get-agent-merge-enrollment",
        "agent-merge/put-agent-merge-enrollment",
    }
)
