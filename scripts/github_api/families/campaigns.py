"""The ``campaigns`` family of the GitHub operations index: an organization's security campaigns.

Each record is the section of ``docs/api-reference/github/rest/campaigns.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body
(``code_scanning_alerts[].repository_id`` is a field of each ``code_scanning_alerts`` item, and the ``(body)``
constraint row names no field). ``campaigns/list-org-campaigns`` alone pages, by ``link``: its ``200`` is a bare
array of ``campaign-summary`` with a ``Link`` header, and "Lists wrapped in an object" names no ``campaigns``
operation, so it has no item key; every other record sends one request. No path parameter of the family may contain
``/``, so ``multi_segment`` is empty throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28) but ``campaigns/create-campaign``: with ``generate_issues`` it
creates issues, so ``commands/call.py`` ``GATED_OPERATIONS`` maps it to no subcommand and ``call`` refuses it (issue
#33 AC-6). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "campaigns"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/campaigns.md "List campaigns for an organization": query ``direction``, ``state`` and ``sort``; page-based,
    # the body is the array.
    RestOperation(
        operation_id="campaigns/list-org-campaigns",
        method="GET",
        path="/orgs/{org}/campaigns",
        query_params=frozenset({"page", "per_page", "direction", "state", "sort"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/campaigns.md "Create a campaign for an organization": the first-level body fields; 200 with a
    # ``campaign-summary``; ``generate_issues`` makes the call create issues, so ``commands/call.py``
    # ``GATED_OPERATIONS`` refuses it.
    RestOperation(
        operation_id="campaigns/create-campaign",
        method="POST",
        path="/orgs/{org}/campaigns",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "name",
                "description",
                "managers",
                "team_managers",
                "ends_at",
                "contact_link",
                "code_scanning_alerts",
                "generate_issues",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/campaigns.md "Get a campaign for an organization": path parameters only; 200 with a ``campaign-summary``.
    RestOperation(
        operation_id="campaigns/get-campaign-summary",
        method="GET",
        path="/orgs/{org}/campaigns/{campaign_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/campaigns.md "Update a campaign": the first-level body fields; 200 with a ``campaign-summary``.
    RestOperation(
        operation_id="campaigns/update-campaign",
        method="PATCH",
        path="/orgs/{org}/campaigns/{campaign_number}",
        query_params=frozenset(),
        body_params=frozenset({"name", "description", "managers", "team_managers", "ends_at", "contact_link", "state"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/campaigns.md "Delete a campaign for an organization": path parameters only; 204 on success.
    RestOperation(
        operation_id="campaigns/delete-campaign",
        method="DELETE",
        path="/orgs/{org}/campaigns/{campaign_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
