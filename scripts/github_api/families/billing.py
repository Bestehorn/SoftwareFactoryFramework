"""The ``billing`` family of the GitHub operations index: an organization's budgets and the usage reports of an
organization or a user.

Each record is the section of ``docs/api-reference/github/rest/billing.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body (``budget_alerting.will_alert``
is a field of ``budget_alerting``). ``billing/get-all-budgets-org`` alone pages, by ``link``: its ``Paging:`` line
reads "items in `budgets`", the key "Lists wrapped in an object" names for it; every other section has no ``Paging:``
line, so its record sends one request. No path parameter of the family may contain ``/``, so ``multi_segment`` is
empty throughout, and every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

Every record is sent by ``call <operation-id>`` (#28), which refuses none of them. No ``sff-test-*`` repository has
the organization or the billing access these calls need (#28 D5), so the contract suite sends them to a fake host;
its unreachable-call test builds ``billing/update-budget-org`` as a slice writes it and declares it in place of this
module's record (issue #33 DL-005). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "billing"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/billing.md "Get all budgets for an organization": query ``scope`` and ``user``; page-based, items in
    # ``budgets``.
    RestOperation(
        operation_id="billing/get-all-budgets-org",
        method="GET",
        path="/organizations/{org}/settings/billing/budgets",
        query_params=frozenset({"page", "per_page", "scope", "user"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key="budgets",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Create a budget for an organization": the first-level body fields; 200 with a ``create-budget``.
    RestOperation(
        operation_id="billing/create-organization-budget",
        method="POST",
        path="/organizations/{org}/settings/billing/budgets",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "budget_amount",
                "prevent_further_usage",
                "budget_alerting",
                "budget_scope",
                "budget_entity_name",
                "budget_type",
                "budget_product_sku",
                "user",
                "expires_at",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get a budget by ID for an organization": path parameters only; 200 with a ``get-budget``.
    RestOperation(
        operation_id="billing/get-budget-org",
        method="GET",
        path="/organizations/{org}/settings/billing/budgets/{budget_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Update a budget for an organization": body ``budget_amount``, ``prevent_further_usage``,
    # ``budget_alerting`` and ``expires_at``; 200 with an ``update-budget``.
    RestOperation(
        operation_id="billing/update-budget-org",
        method="PATCH",
        path="/organizations/{org}/settings/billing/budgets/{budget_id}",
        query_params=frozenset(),
        body_params=frozenset({"budget_amount", "prevent_further_usage", "budget_alerting", "expires_at"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Delete a budget for an organization": path parameters only; 200 with a ``delete-budget``.
    RestOperation(
        operation_id="billing/delete-budget-org",
        method="DELETE",
        path="/organizations/{org}/settings/billing/budgets/{budget_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing AI credit usage report for an organization": the query rows; 200 with a
    # ``billing-ai-credit-usage-report-org``.
    RestOperation(
        operation_id="billing/get-github-billing-ai-credit-usage-report-org",
        method="GET",
        path="/organizations/{org}/settings/billing/ai_credit/usage",
        query_params=frozenset({"year", "month", "day", "user", "model", "product"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing premium request usage report for an organization": the query rows; 200 with a
    # ``billing-premium-request-usage-report-org``.
    RestOperation(
        operation_id="billing/get-github-billing-premium-request-usage-report-org",
        method="GET",
        path="/organizations/{org}/settings/billing/premium_request/usage",
        query_params=frozenset({"year", "month", "day", "user", "model", "product"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing usage report for an organization": query ``year``, ``month`` and ``day``; 200 with a
    # ``billing-usage-report``.
    RestOperation(
        operation_id="billing/get-github-billing-usage-report-org",
        method="GET",
        path="/organizations/{org}/settings/billing/usage",
        query_params=frozenset({"year", "month", "day"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing usage summary for an organization": the query rows; 200 with a
    # ``billing-usage-summary-report-org``.
    RestOperation(
        operation_id="billing/get-github-billing-usage-summary-report-org",
        method="GET",
        path="/organizations/{org}/settings/billing/usage/summary",
        query_params=frozenset({"year", "month", "day", "repository", "product", "sku"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing AI credit usage report for a user": the query rows; 200 with a
    # ``billing-ai-credit-usage-report-user``.
    RestOperation(
        operation_id="billing/get-github-billing-ai-credit-usage-report-user",
        method="GET",
        path="/users/{username}/settings/billing/ai_credit/usage",
        query_params=frozenset({"year", "month", "day", "model", "product"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing premium request usage report for a user": the query rows; 200 with a
    # ``billing-premium-request-usage-report-user``.
    RestOperation(
        operation_id="billing/get-github-billing-premium-request-usage-report-user",
        method="GET",
        path="/users/{username}/settings/billing/premium_request/usage",
        query_params=frozenset({"year", "month", "day", "model", "product"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing usage report for a user": query ``year``, ``month`` and ``day``; 200 with a
    # ``billing-usage-report-user``.
    RestOperation(
        operation_id="billing/get-github-billing-usage-report-user",
        method="GET",
        path="/users/{username}/settings/billing/usage",
        query_params=frozenset({"year", "month", "day"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/billing.md "Get billing usage summary for a user": the query rows; 200 with a
    # ``billing-usage-summary-report-user``.
    RestOperation(
        operation_id="billing/get-github-billing-usage-summary-report-user",
        method="GET",
        path="/users/{username}/settings/billing/usage/summary",
        query_params=frozenset({"year", "month", "day", "repository", "product", "sku"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
