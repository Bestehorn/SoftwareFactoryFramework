"""GitLab REST endpoint family deploy: no records yet; each index key it owns is pending."""

FAMILY = "deploy"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("GET", "/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name"),
        ("PUT", "/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name"),
        ("PUT", "/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name/authorize"),
    }
)
