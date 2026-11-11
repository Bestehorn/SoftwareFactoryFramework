"""The ``fulfillment`` endpoint family of the GitLab wrapper: LDAP group links, licenses and SCIM identities.

Each record is transcribed from the attribute table of its section of ``docs/api-reference/gitlab/rest/fulfillment.md``
(issue #13, design.md D1 and D5; issue #38, change.md AC-1 to AC-5), in page order under a comment naming its section:
the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body row, in table order:

- every row is ``Kind.SCALAR``; ``required`` is the Required column's ``yes``; every body is JSON and no record has
  ``fixed`` values;
- "List all LDAP group links" and "List all licenses" are ``Paging.OFFSET``, every other record ``Paging.NONE``.

A section with several endpoints has one record: "Delete an LDAP group link (deprecated)" lists
``/groups/:id/ldap_group_links/:cn`` and ``/groups/:id/ldap_group_links/:provider/:cn``, and its record takes the first.
``PENDING`` holds the second, the one other endpoint of such a section.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Location, Paging, Param, RestOperation

FAMILY = "fulfillment"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "LDAP group links: List all LDAP group links".
    RestOperation(
        operation_id="fulfillment#list-all-ldap-group-links",
        method="GET",
        path="/groups/:id/ldap_group_links",
        paging=Paging.OFFSET,
    ),
    # "LDAP group links: Add an LDAP group link with CN or filter".
    RestOperation(
        operation_id="fulfillment#add-an-ldap-group-link-with-cn-or-filter",
        method="POST",
        path="/groups/:id/ldap_group_links",
        params=(
            Param(name="group_access", location=Location.BODY, required=True),
            Param(name="provider", location=Location.BODY, required=True),
            Param(name="cn", location=Location.BODY, required=True),
            Param(name="filter", location=Location.BODY, required=True),
            Param(name="member_role_id", location=Location.BODY),
        ),
    ),
    # "LDAP group links: Delete an LDAP group link with CN or filter".
    RestOperation(
        operation_id="fulfillment#delete-an-ldap-group-link-with-cn-or-filter",
        method="DELETE",
        path="/groups/:id/ldap_group_links",
        params=(
            Param(name="provider", location=Location.QUERY, required=True),
            Param(name="cn", location=Location.QUERY, required=True),
            Param(name="filter", location=Location.QUERY, required=True),
        ),
    ),
    # "LDAP group links: Delete an LDAP group link (deprecated)"; the first of its two endpoints; `DELETE
    # /groups/:id/ldap_group_links/:provider/:cn` stays pending.
    RestOperation(
        operation_id="fulfillment#delete-an-ldap-group-link-deprecated",
        method="DELETE",
        path="/groups/:id/ldap_group_links/:cn",
    ),
    # "License API: Retrieve license information".
    RestOperation(
        operation_id="fulfillment#retrieve-license-information",
        method="GET",
        path="/license",
    ),
    # "License API: List all licenses".
    RestOperation(
        operation_id="fulfillment#list-all-licenses",
        method="GET",
        path="/licenses",
        paging=Paging.OFFSET,
    ),
    # "License API: Retrieve a license".
    RestOperation(
        operation_id="fulfillment#retrieve-a-license",
        method="GET",
        path="/license/:id",
    ),
    # "License API: Create a license".
    RestOperation(
        operation_id="fulfillment#create-a-license",
        method="POST",
        path="/license",
        params=(Param(name="license", location=Location.BODY, required=True),),
    ),
    # "License API: Delete a license".
    RestOperation(
        operation_id="fulfillment#delete-a-license",
        method="DELETE",
        path="/license/:id",
    ),
    # "License API: Trigger recalculation of billable users".
    RestOperation(
        operation_id="fulfillment#trigger-recalculation-of-billable-users",
        method="PUT",
        path="/license/:id/refresh_billable_users",
    ),
    # "License API: Retrieve license usage information".
    RestOperation(
        operation_id="fulfillment#retrieve-license-usage-information",
        method="GET",
        path="/license/usage_export.csv",
    ),
    # "SCIM API: Retrieve SCIM identities for a group".
    RestOperation(
        operation_id="fulfillment#retrieve-scim-identities-for-a-group",
        method="GET",
        path="/groups/:id/scim/identities",
    ),
    # "SCIM API: Retrieve a single SCIM identity".
    RestOperation(
        operation_id="fulfillment#retrieve-a-single-scim-identity",
        method="GET",
        path="/groups/:id/scim/:uid",
    ),
    # "SCIM API: Update `extern_uid` field for a SCIM identity"; the path names the group `:groups_id`, and the table
    # has an `id` body row, each transcribed as written.
    RestOperation(
        operation_id="fulfillment#update-extern_uid-field-for-a-scim-identity",
        method="PATCH",
        path="/groups/:groups_id/scim/:uid",
        params=(Param(name="id", location=Location.BODY, required=True),),
    ),
    # "SCIM API: Delete a single SCIM identity".
    RestOperation(
        operation_id="fulfillment#delete-a-single-scim-identity",
        method="DELETE",
        path="/groups/:id/scim/:uid",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("DELETE", "/groups/:id/ldap_group_links/:provider/:cn"),
    }
)
