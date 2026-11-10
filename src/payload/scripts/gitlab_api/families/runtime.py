"""GitLab REST endpoint family runtime: no records yet; each index key it owns is pending."""

FAMILY = "runtime"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/groups/:id/billable_members/:user_id"),
        ("DELETE", "/groups/:id/members/:user_id"),
        ("DELETE", "/groups/:id/members/:user_id/override"),
        ("DELETE", "/projects/:id/members/:user_id"),
        ("GET", "/groups/:id/billable_members"),
        ("GET", "/groups/:id/billable_members/:user_id/indirect"),
        ("GET", "/groups/:id/billable_members/:user_id/memberships"),
        ("GET", "/groups/:id/members"),
        ("GET", "/groups/:id/members/:user_id"),
        ("GET", "/groups/:id/members/all"),
        ("GET", "/groups/:id/members/all/:user_id"),
        ("GET", "/groups/:id/pending_members"),
        ("GET", "/projects/:id/members"),
        ("GET", "/projects/:id/members/:user_id"),
        ("GET", "/projects/:id/members/all"),
        ("GET", "/projects/:id/members/all/:user_id"),
        ("POST", "/groups/:id/members"),
        ("POST", "/groups/:id/members/:user_id/override"),
        ("POST", "/groups/:id/members/approve_all"),
        ("POST", "/projects/:id/members"),
        ("PUT", "/groups/:id/members/:member_id/approve"),
        ("PUT", "/groups/:id/members/:user_id"),
        ("PUT", "/groups/:id/members/:user_id/state"),
        ("PUT", "/projects/:id/members/:user_id"),
    }
)
