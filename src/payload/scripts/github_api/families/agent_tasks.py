"""The ``agent-tasks`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "agent-tasks"
OPERATIONS = ()
PENDING = frozenset(
    {
        "agent-tasks/create-task-in-repo",
        "agent-tasks/get-task-by-id",
        "agent-tasks/get-task-by-repo-and-id",
        "agent-tasks/list-tasks",
        "agent-tasks/list-tasks-for-repo",
    }
)
