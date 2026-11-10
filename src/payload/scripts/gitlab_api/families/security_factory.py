"""GitLab REST endpoint family security-factory: no records yet; each index key it owns is pending."""

FAMILY = "security-factory"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/projects/:id/dependencies"),
        ("GET", "/projects/:id/security_settings"),
        ("GET", "/templates/licenses"),
        ("GET", "/templates/licenses/:key"),
        ("PUT", "/projects/:id/security_settings"),
    }
)
