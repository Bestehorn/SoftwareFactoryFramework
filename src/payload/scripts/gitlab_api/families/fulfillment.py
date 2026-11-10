"""GitLab REST endpoint family fulfillment: no records yet; each index key it owns is pending."""

FAMILY = "fulfillment"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/groups/:id/ldap_group_links"),
        ("DELETE", "/groups/:id/ldap_group_links/:cn"),
        ("DELETE", "/groups/:id/ldap_group_links/:provider/:cn"),
        ("DELETE", "/groups/:id/scim/:uid"),
        ("DELETE", "/license/:id"),
        ("GET", "/groups/:id/ldap_group_links"),
        ("GET", "/groups/:id/scim/:uid"),
        ("GET", "/groups/:id/scim/identities"),
        ("GET", "/license"),
        ("GET", "/license/:id"),
        ("GET", "/license/usage_export.csv"),
        ("GET", "/licenses"),
        ("PATCH", "/groups/:groups_id/scim/:uid"),
        ("POST", "/groups/:id/ldap_group_links"),
        ("POST", "/license"),
        ("PUT", "/license/:id/refresh_billable_users"),
    }
)
