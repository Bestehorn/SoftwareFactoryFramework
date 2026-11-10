"""The ``classroom`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "classroom"
OPERATIONS = ()
PENDING = frozenset(
    {
        "classroom/get-a-classroom",
        "classroom/get-an-assignment",
        "classroom/get-assignment-grades",
        "classroom/list-accepted-assignments-for-an-assignment",
        "classroom/list-assignments-for-a-classroom",
        "classroom/list-classrooms",
    }
)
