"""The ``private-registries`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "private-registries"
OPERATIONS = ()
PENDING = frozenset(
    {
        "private-registries/create-org-private-registry",
        "private-registries/delete-org-private-registry",
        "private-registries/get-org-private-registry",
        "private-registries/get-org-public-key",
        "private-registries/list-org-private-registries",
        "private-registries/update-org-private-registry",
    }
)
