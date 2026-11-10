"""The ``checks`` family of the GitHub operations index: the record ``get-pr-checks`` sends for a PR's check runs.

``checks/list-for-ref`` is its row of ``docs/api-reference/github/operations-index.md`` with the query names of the
``rest/checks.md`` section that row links. It is a wrapped list (``conventions.md`` "Lists wrapped in an object"):
the runs sit under ``check_runs``, paged by the ``link`` header; ``ref`` may hold ``/`` (``conventions.md`` "Path
parameters"). Every other operation ID of the family is on ``PENDING`` (design D2).
"""

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "checks"

OPERATIONS = (
    RestOperation(
        operation_id="checks/list-for-ref",
        method="GET",
        path="/repos/{owner}/{repo}/commits/{ref}/check-runs",
        query_params=frozenset({"check_name", "status", "filter", "per_page", "page", "app_id"}),
        body_params=frozenset(),
        multi_segment=frozenset({"ref"}),
        paging=Paging.LINK,
        item_key="check_runs",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING = frozenset(
    {
        "checks/create",
        "checks/create-suite",
        "checks/get",
        "checks/get-suite",
        "checks/list-annotations",
        "checks/list-for-suite",
        "checks/list-suites-for-ref",
        "checks/rerequest-run",
        "checks/rerequest-suite",
        "checks/set-suites-preferences",
        "checks/update",
    }
)
