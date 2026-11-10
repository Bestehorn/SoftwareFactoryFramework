"""The ``code-security`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "code-security"
OPERATIONS = ()
PENDING = frozenset(
    {
        "code-security/attach-configuration",
        "code-security/attach-enterprise-configuration",
        "code-security/create-configuration",
        "code-security/create-configuration-for-enterprise",
        "code-security/delete-configuration",
        "code-security/delete-configuration-for-enterprise",
        "code-security/detach-configuration",
        "code-security/get-configuration",
        "code-security/get-configuration-for-repository",
        "code-security/get-configurations-for-enterprise",
        "code-security/get-configurations-for-org",
        "code-security/get-default-configurations",
        "code-security/get-default-configurations-for-enterprise",
        "code-security/get-repositories-for-configuration",
        "code-security/get-repositories-for-enterprise-configuration",
        "code-security/get-single-configuration-for-enterprise",
        "code-security/set-configuration-as-default",
        "code-security/set-configuration-as-default-for-enterprise",
        "code-security/update-configuration",
        "code-security/update-enterprise-configuration",
    }
)
