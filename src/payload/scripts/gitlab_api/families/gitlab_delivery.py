"""The ``gitlab-delivery`` endpoint family of the GitLab wrapper: the Sidekiq metrics, the Sidekiq queues and the
worker concurrency limits.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/gitlab-delivery.md`` (issue #13, design.md D1 and D5; issue #38, change.md AC-1 to
AC-5), in page order under a comment naming its section: the method, the path as ``operations-index.md`` writes it, and
one ``Param`` per query or body row, in table order:

- every row is ``Kind.SCALAR``; ``required`` is the Required column's ``yes``; every body is JSON and no record has
  ``fixed`` values;
- every record is ``Paging.NONE``: the Sidekiq "List" sections answer one object (AC-5).

``PENDING`` is empty: every key of this family's index rows is a record's.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Location, Param, RestOperation

FAMILY = "gitlab-delivery"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Sidekiq Metrics API: List all job queue metrics"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="gitlab-delivery#list-all-job-queue-metrics",
        method="GET",
        path="/sidekiq/queue_metrics",
    ),
    # "Sidekiq Metrics API: List all Sidekiq processes"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="gitlab-delivery#list-all-sidekiq-processes",
        method="GET",
        path="/sidekiq/process_metrics",
    ),
    # "Sidekiq Metrics API: Retrieve job completion metrics".
    RestOperation(
        operation_id="gitlab-delivery#retrieve-job-completion-metrics",
        method="GET",
        path="/sidekiq/job_stats",
    ),
    # "Sidekiq Metrics API: List all Sidekiq metrics"; it answers one object, so it is not paged (AC-5).
    RestOperation(
        operation_id="gitlab-delivery#list-all-sidekiq-metrics",
        method="GET",
        path="/sidekiq/compound_metrics",
    ),
    # "Sidekiq queues administration API: Delete jobs from a Sidekiq queue".
    RestOperation(
        operation_id="gitlab-delivery#delete-jobs-from-a-sidekiq-queue",
        method="DELETE",
        path="/admin/sidekiq/queues/:queue_name",
        params=(
            Param(name="user", location=Location.QUERY),
            Param(name="project", location=Location.QUERY),
            Param(name="root_namespace", location=Location.QUERY),
            Param(name="subscription_plan", location=Location.QUERY),
            Param(name="caller_id", location=Location.QUERY),
            Param(name="feature_category", location=Location.QUERY),
            Param(name="client_type", location=Location.QUERY),
            Param(name="client_name", location=Location.QUERY),
            Param(name="client_version", location=Location.QUERY),
            Param(name="worker_class", location=Location.QUERY),
        ),
    ),
    # "Sidekiq queues administration API: Retrieve a worker concurrency limit".
    RestOperation(
        operation_id="gitlab-delivery#retrieve-a-worker-concurrency-limit",
        method="GET",
        path="/admin/sidekiq/concurrency_limits/:worker_class",
    ),
    # "Sidekiq queues administration API: Update a worker concurrency override".
    RestOperation(
        operation_id="gitlab-delivery#update-a-worker-concurrency-override",
        method="PUT",
        path="/admin/sidekiq/concurrency_limits/:worker_class",
        params=(
            Param(name="limit", location=Location.BODY, required=True),
            Param(name="ttl", location=Location.BODY),
        ),
    ),
    # "Sidekiq queues administration API: Delete a worker concurrency override".
    RestOperation(
        operation_id="gitlab-delivery#delete-a-worker-concurrency-override",
        method="DELETE",
        path="/admin/sidekiq/concurrency_limits/:worker_class",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
