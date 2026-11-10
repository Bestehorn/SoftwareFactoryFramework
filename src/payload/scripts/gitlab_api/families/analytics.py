"""GitLab REST endpoint family analytics: no records yet; each index key it owns is pending."""

FAMILY = "analytics"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/projects/:id/alert_management_alerts/:alert_iid/metric_images/:image_id"),
        ("DELETE", "/projects/:id/error_tracking/client_keys/:key_id"),
        ("GET", "/admin/search/migrations"),
        ("GET", "/admin/search/migrations/:version_or_name"),
        ("GET", "/analytics/group_activity/issues_count"),
        ("GET", "/analytics/group_activity/merge_requests_count"),
        ("GET", "/analytics/group_activity/new_members_count"),
        ("GET", "/groups/:id/dora/metrics"),
        ("GET", "/groups/:id/search"),
        ("GET", "/projects/:id/alert_management_alerts/:alert_iid/metric_images"),
        ("GET", "/projects/:id/dora/metrics"),
        ("GET", "/projects/:id/error_tracking/client_keys"),
        ("GET", "/projects/:id/error_tracking/settings"),
        ("GET", "/projects/:id/search"),
        ("GET", "/projects/:id/search/semantic"),
        ("GET", "/search"),
        ("GET", "/usage_data/metric_definitions"),
        ("GET", "/usage_data/non_sql_metrics"),
        ("GET", "/usage_data/queries"),
        ("GET", "/usage_data/service_ping"),
        ("PATCH", "/projects/:id/error_tracking/settings"),
        ("POST", "/projects/:id/alert_management_alerts/:alert_iid/metric_images"),
        ("POST", "/projects/:id/error_tracking/client_keys"),
        ("POST", "/usage_data/track_event"),
        ("PUT", "/projects/:id/alert_management_alerts/:alert_iid/metric_images/:image_id"),
        ("PUT", "/projects/:id/error_tracking/settings"),
    }
)
