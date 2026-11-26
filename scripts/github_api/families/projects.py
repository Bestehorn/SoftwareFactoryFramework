"""The ``projects`` family of the GitHub operations index: the projects (``projectsV2``) of an
organization and of a user, with their draft items, fields, items and views.

Each record is its section of ``docs/api-reference/github/rest/projects.md`` (``drafts``, ``fields``, ``items``,
``projects``, ``views``), in the order of its sections: the operation line's method and path, the ``query`` rows of
its ``Parameter`` table, and the first-level names of its JSON request body, a leading variant label removed
(``{single_select}.single_select_options[].name`` names ``single_select_options``). No path parameter row reads "may
contain ``/``", so ``multi_segment`` is empty; every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The eight list sections with a ``Paging:`` line page by ``per_page`` and an ``after``/``before`` cursor with a
``Link`` header; they are ``Paging.LINK`` with no item key (each body is the array), and the ``rel="next"`` target
carries the cursor. The ``get-`` sections answer one object with a ``Link`` header, which does not page (issue #33
DL-006), so they are ``Paging.NONE`` like every other record and send one request.

``projects/create-draft-item-for-org`` and ``projects/create-draft-item-for-authenticated-user`` add a draft item to a
project and write no branch; they are declared (#28 Security "Destructive operations"). Every record is sent by
``call <operation-id>`` (#28); no operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "projects"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/projects.md "Create draft item for organization owned project"
    RestOperation(
        operation_id="projects/create-draft-item-for-org",
        method="POST",
        path="/orgs/{org}/projectsV2/{project_number}/drafts",
        query_params=frozenset(),
        body_params=frozenset({"title", "body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Create draft item for user owned project"
    RestOperation(
        operation_id="projects/create-draft-item-for-authenticated-user",
        method="POST",
        path="/user/{user_id}/projectsV2/{project_number}/drafts",
        query_params=frozenset(),
        body_params=frozenset({"title", "body"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List project fields for organization": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-fields-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}/fields",
        query_params=frozenset({"per_page", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Add a field to an organization-owned project."
    RestOperation(
        operation_id="projects/add-field-for-org",
        method="POST",
        path="/orgs/{org}/projectsV2/{project_number}/fields",
        query_params=frozenset(),
        body_params=frozenset(
            {"issue_field_id", "name", "data_type", "single_select_options", "iteration_configuration"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get project field for organization": one object with a ``Link`` header, which does not page
    # (DL-006).
    RestOperation(
        operation_id="projects/get-field-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}/fields/{field_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List project fields for user": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-fields-for-user",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}/fields",
        query_params=frozenset({"per_page", "before", "after"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Add field to user owned project"
    RestOperation(
        operation_id="projects/add-field-for-user",
        method="POST",
        path="/users/{username}/projectsV2/{project_number}/fields",
        query_params=frozenset(),
        body_params=frozenset({"name", "data_type", "single_select_options", "iteration_configuration"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get project field for user": one object with a ``Link`` header, which does not page (DL-006).
    RestOperation(
        operation_id="projects/get-field-for-user",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}/fields/{field_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List items for an organization owned project": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-items-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}/items",
        query_params=frozenset({"q", "fields", "before", "after", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Add item to organization owned project"
    RestOperation(
        operation_id="projects/add-item-for-org",
        method="POST",
        path="/orgs/{org}/projectsV2/{project_number}/items",
        query_params=frozenset(),
        body_params=frozenset({"type", "id", "owner", "repo", "number"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get an item for an organization owned project": one object with a ``Link`` header, which does
    # not page (DL-006).
    RestOperation(
        operation_id="projects/get-org-item",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset({"fields"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Update project item for organization"
    RestOperation(
        operation_id="projects/update-item-for-org",
        method="PATCH",
        path="/orgs/{org}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset(),
        body_params=frozenset({"fields"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Delete project item for organization"
    RestOperation(
        operation_id="projects/delete-item-for-org",
        method="DELETE",
        path="/orgs/{org}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List items for an organization project view": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-view-items-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}/views/{view_number}/items",
        query_params=frozenset({"fields", "before", "after", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List items for a user owned project": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-items-for-user",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}/items",
        query_params=frozenset({"before", "after", "per_page", "q", "fields"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Add item to user owned project"
    RestOperation(
        operation_id="projects/add-item-for-user",
        method="POST",
        path="/users/{username}/projectsV2/{project_number}/items",
        query_params=frozenset(),
        body_params=frozenset({"type", "id", "owner", "repo", "number"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get an item for a user owned project": one object with a ``Link`` header, which does not page
    # (DL-006).
    RestOperation(
        operation_id="projects/get-user-item",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset({"fields"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Update project item for user"
    RestOperation(
        operation_id="projects/update-item-for-user",
        method="PATCH",
        path="/users/{username}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset(),
        body_params=frozenset({"fields"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Delete project item for user"
    RestOperation(
        operation_id="projects/delete-item-for-user",
        method="DELETE",
        path="/users/{username}/projectsV2/{project_number}/items/{item_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List items for a user project view": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-view-items-for-user",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}/views/{view_number}/items",
        query_params=frozenset({"fields", "before", "after", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List projects for organization": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2",
        query_params=frozenset({"q", "before", "after", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get project for organization": one object with a ``Link`` header, which does not page (DL-006).
    RestOperation(
        operation_id="projects/get-for-org",
        method="GET",
        path="/orgs/{org}/projectsV2/{project_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "List projects for user": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="projects/list-for-user",
        method="GET",
        path="/users/{username}/projectsV2",
        query_params=frozenset({"q", "before", "after", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Get project for user": one object with a ``Link`` header, which does not page (DL-006).
    RestOperation(
        operation_id="projects/get-for-user",
        method="GET",
        path="/users/{username}/projectsV2/{project_number}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Create a view for an organization-owned project"
    RestOperation(
        operation_id="projects/create-view-for-org",
        method="POST",
        path="/orgs/{org}/projectsV2/{project_number}/views",
        query_params=frozenset(),
        body_params=frozenset(
            {"name", "layout", "filter", "visible_fields", "sort_by", "group_by", "vertical_group_by"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/projects.md "Create a view for a user-owned project"
    RestOperation(
        operation_id="projects/create-view-for-user",
        method="POST",
        path="/users/{user_id}/projectsV2/{project_number}/views",
        query_params=frozenset(),
        body_params=frozenset(
            {"name", "layout", "filter", "visible_fields", "sort_by", "group_by", "vertical_group_by"}
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
