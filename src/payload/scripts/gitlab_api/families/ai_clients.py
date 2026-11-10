"""GitLab REST endpoint family ai-clients: no records yet; each index key it owns is pending."""

FAMILY = "ai-clients"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("POST", "/chat/completions"),
    }
)
