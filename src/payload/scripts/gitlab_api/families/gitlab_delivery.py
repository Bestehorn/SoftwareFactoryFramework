"""GitLab REST endpoint family gitlab-delivery: no records yet; each index key it owns is pending."""

FAMILY = "gitlab-delivery"
OPERATIONS = ()
PENDING = frozenset(
    {
        ("DELETE", "/admin/sidekiq/concurrency_limits/:worker_class"),
        ("DELETE", "/admin/sidekiq/queues/:queue_name"),
        ("GET", "/admin/sidekiq/concurrency_limits/:worker_class"),
        ("GET", "/sidekiq/compound_metrics"),
        ("GET", "/sidekiq/job_stats"),
        ("GET", "/sidekiq/process_metrics"),
        ("GET", "/sidekiq/queue_metrics"),
        ("PUT", "/admin/sidekiq/concurrency_limits/:worker_class"),
    }
)
