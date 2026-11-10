"""The ``projects`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "projects"
OPERATIONS = ()
PENDING = frozenset(
    {
        "projects/add-field-for-org",
        "projects/add-field-for-user",
        "projects/add-item-for-org",
        "projects/add-item-for-user",
        "projects/create-draft-item-for-authenticated-user",
        "projects/create-draft-item-for-org",
        "projects/create-view-for-org",
        "projects/create-view-for-user",
        "projects/delete-item-for-org",
        "projects/delete-item-for-user",
        "projects/get-field-for-org",
        "projects/get-field-for-user",
        "projects/get-for-org",
        "projects/get-for-user",
        "projects/get-org-item",
        "projects/get-user-item",
        "projects/list-fields-for-org",
        "projects/list-fields-for-user",
        "projects/list-for-org",
        "projects/list-for-user",
        "projects/list-items-for-org",
        "projects/list-items-for-user",
        "projects/list-view-items-for-org",
        "projects/list-view-items-for-user",
        "projects/update-item-for-org",
        "projects/update-item-for-user",
    }
)
