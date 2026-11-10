"""The ``oidc`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "oidc"
OPERATIONS = ()
PENDING = frozenset(
    {
        "oidc/create-oidc-custom-property-inclusion-for-enterprise",
        "oidc/create-oidc-custom-property-inclusion-for-org",
        "oidc/delete-oidc-custom-property-inclusion-for-enterprise",
        "oidc/delete-oidc-custom-property-inclusion-for-org",
        "oidc/get-oidc-custom-sub-template-for-org",
        "oidc/list-oidc-custom-property-inclusions-for-enterprise",
        "oidc/list-oidc-custom-property-inclusions-for-org",
        "oidc/update-oidc-custom-sub-template-for-org",
    }
)
