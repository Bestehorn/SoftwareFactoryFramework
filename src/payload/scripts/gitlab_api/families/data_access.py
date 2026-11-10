"""GitLab REST endpoint family data-access: no records yet; each index key it owns is pending."""

FAMILY = "data-access"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/admin/batched_background_migrations"),
        ("GET", "/admin/batched_background_migrations/:id"),
        ("GET", "/admin/migrations/pending"),
        ("POST", "/admin/migrations/:version/mark"),
        ("PUT", "/admin/batched_background_migrations/:id/pause"),
        ("PUT", "/admin/batched_background_migrations/:id/resume"),
    }
)
