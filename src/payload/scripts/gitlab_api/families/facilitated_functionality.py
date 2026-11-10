"""GitLab REST endpoint family facilitated-functionality: no records yet; each index key it owns is pending."""

FAMILY = "facilitated-functionality"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/events"),
        ("GET", "/projects/:project_id/events"),
        ("GET", "/users/:id/events"),
    }
)
