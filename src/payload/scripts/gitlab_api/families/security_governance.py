"""GitLab REST endpoint family security-governance: no records yet; each index key it owns is pending."""

FAMILY = "security-governance"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("PUT", "/groups/:id/security_settings"),
    }
)
