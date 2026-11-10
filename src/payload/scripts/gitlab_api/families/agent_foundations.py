"""GitLab REST endpoint family agent-foundations: no records yet; each index key it owns is pending."""

FAMILY = "agent-foundations"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/ai/duo_workflows/workflows/:workflow_id/trace.jsonl"),
        ("GET", "/ai/duo_workflows/workflows/agent_privileges"),
        ("POST", "/admin/ai_catalog/seed_external_agents"),
        ("POST", "/ai/duo_workflows/workflows"),
        ("POST", "/ai/duo_workflows/workflows/:workflow_id/restart"),
    }
)
