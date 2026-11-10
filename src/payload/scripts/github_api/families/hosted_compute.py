"""The ``hosted-compute`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "hosted-compute"
OPERATIONS = ()
PENDING = frozenset(
    {
        "hosted-compute/create-network-configuration-for-org",
        "hosted-compute/delete-network-configuration-from-org",
        "hosted-compute/get-network-configuration-for-org",
        "hosted-compute/get-network-settings-for-org",
        "hosted-compute/list-network-configurations-for-org",
        "hosted-compute/update-network-configuration-for-org",
    }
)
