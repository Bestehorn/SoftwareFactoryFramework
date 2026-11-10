"""The ``agent-automations`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "agent-automations"
OPERATIONS = ()
PENDING = frozenset(
    {
        "agent-automations/create-repo-automation",
        "agent-automations/create-repo-automation-task",
        "agent-automations/delete-repo-automation",
        "agent-automations/edit-repo-automation",
        "agent-automations/get-automation-revision",
        "agent-automations/get-repo-automation",
        "agent-automations/list-automation-revisions",
        "agent-automations/list-automations",
        "agent-automations/list-available-repo-automation-tools",
        "agent-automations/list-available-repo-automation-triggers",
        "agent-automations/list-repo-automation-tasks",
        "agent-automations/list-repo-automations",
    }
)
