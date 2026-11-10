"""GitLab REST endpoint family orbit: no records yet; each index key it owns is pending."""

FAMILY = "orbit"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/orbit/grep"),
        ("GET", "/orbit/skills"),
        ("GET", "/orbit/skills/:name"),
        ("GET", "/orbit/skills/:name/*path"),
        ("HEAD", "/orbit/skills/:name"),
        ("POST", "/orbit/context"),
        ("POST", "/orbit/query"),
        ("POST", "/orbit/query/:name"),
    }
)
