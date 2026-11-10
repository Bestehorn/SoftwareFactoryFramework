"""GitLab REST endpoint family developer-experience: no records yet; each index key it owns is pending."""

FAMILY = "developer-experience"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/projects/:id/share/:group_id"),
        ("GET", "/projects"),
        ("GET", "/projects/1/branches/my%2Fbranch/commits"),
        ("GET", "/projects/1/repository/files/src%2FREADME.md"),
        ("GET", "/projects/1/repository/tags/my%2Ftag"),
        ("GET", "/projects/diaspora%2Fdiaspora"),
    }
)
