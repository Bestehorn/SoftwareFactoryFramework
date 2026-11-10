"""The ``dependency-graph`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "dependency-graph"
OPERATIONS = ()
PENDING = frozenset(
    {
        "dependency-graph/create-repository-snapshot",
        "dependency-graph/diff-range",
        "dependency-graph/export-sbom",
        "dependency-graph/fetch-sbom-report",
        "dependency-graph/generate-sbom-report",
    }
)
