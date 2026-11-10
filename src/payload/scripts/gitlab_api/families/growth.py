"""GitLab REST endpoint family growth: no records yet; each index key it owns is pending."""

FAMILY = "growth"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/broadcast_messages/:id"),
        ("DELETE", "/experiments/:experiment_name/assignments"),
        ("DELETE", "/experiments/:name/cache"),
        ("GET", "/broadcast_messages"),
        ("GET", "/broadcast_messages/:id"),
        ("GET", "/experiments"),
        ("GET", "/experiments/:experiment_name/assignments"),
        ("POST", "/broadcast_messages"),
        ("POST", "/experiments/:experiment_name/assignments"),
        ("PUT", "/broadcast_messages/:id"),
    }
)
