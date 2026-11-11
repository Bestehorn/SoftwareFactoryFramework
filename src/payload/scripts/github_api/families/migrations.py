"""The ``migrations`` family of the GitHub operations index: the migrations of an organization and of
the authenticated user, their archives and locked repositories, and the deprecated Source Imports API.

Each record is its section of ``docs/api-reference/github/rest/migrations.md`` (``orgs``, ``source-imports``,
``users``), in the order of its sections: the operation line's method and path, the ``query`` rows of its
``Parameter`` table, and the first-level names of its JSON request body. No path parameter row reads "may contain
``/``", so ``multi_segment`` is empty; every record sends ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The four list sections with a ``Paging:`` line are ``Paging.LINK`` with no item key: each body is the array.
``migrations/get-commit-authors`` and ``migrations/get-large-files`` answer an array with no ``Paging:`` line and no
``Link`` header, so they are ``Paging.NONE`` like every other record and send one request.

``migrations/download-archive-for-org`` and ``migrations/get-archive-for-authenticated-user`` answer ``302``; they are
plain records (issue #33 Residuals). The eight records of the ``source-imports`` sections,
``migrations/get-import-status`` to ``migrations/set-lfs-preference``, are declared as their sections document them;
those sections read them deprecated, with a removal date of 2024-04-12. Every record is sent by
``call <operation-id>`` (#28); no operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "migrations"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/migrations.md "List organization migrations": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="migrations/list-for-org",
        method="GET",
        path="/orgs/{org}/migrations",
        query_params=frozenset({"per_page", "page", "exclude"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Start an organization migration"
    RestOperation(
        operation_id="migrations/start-for-org",
        method="POST",
        path="/orgs/{org}/migrations",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "repositories",
                "lock_repositories",
                "exclude_metadata",
                "exclude_git_data",
                "exclude_attachments",
                "exclude_releases",
                "exclude_owner_projects",
                "org_metadata_only",
                "exclude",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Get an organization migration status"
    RestOperation(
        operation_id="migrations/get-status-for-org",
        method="GET",
        path="/orgs/{org}/migrations/{migration_id}",
        query_params=frozenset({"exclude"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Download an organization migration archive": answers ``302``, a plain record (issue #33
    # Residuals).
    RestOperation(
        operation_id="migrations/download-archive-for-org",
        method="GET",
        path="/orgs/{org}/migrations/{migration_id}/archive",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Delete an organization migration archive"
    RestOperation(
        operation_id="migrations/delete-archive-for-org",
        method="DELETE",
        path="/orgs/{org}/migrations/{migration_id}/archive",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Unlock an organization repository"
    RestOperation(
        operation_id="migrations/unlock-repo-for-org",
        method="DELETE",
        path="/orgs/{org}/migrations/{migration_id}/repos/{repo_name}/lock",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "List repositories in an organization migration": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="migrations/list-repos-for-org",
        method="GET",
        path="/orgs/{org}/migrations/{migration_id}/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Get an import status"
    RestOperation(
        operation_id="migrations/get-import-status",
        method="GET",
        path="/repos/{owner}/{repo}/import",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Start an import"
    RestOperation(
        operation_id="migrations/start-import",
        method="PUT",
        path="/repos/{owner}/{repo}/import",
        query_params=frozenset(),
        body_params=frozenset({"vcs_url", "vcs", "vcs_username", "vcs_password", "tfvc_project"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Update an import"
    RestOperation(
        operation_id="migrations/update-import",
        method="PATCH",
        path="/repos/{owner}/{repo}/import",
        query_params=frozenset(),
        body_params=frozenset({"vcs_username", "vcs_password", "vcs", "tfvc_project"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Cancel an import"
    RestOperation(
        operation_id="migrations/cancel-import",
        method="DELETE",
        path="/repos/{owner}/{repo}/import",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Get commit authors": an array with no ``Paging:`` line, one request.
    RestOperation(
        operation_id="migrations/get-commit-authors",
        method="GET",
        path="/repos/{owner}/{repo}/import/authors",
        query_params=frozenset({"since"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Map a commit author"
    RestOperation(
        operation_id="migrations/map-commit-author",
        method="PATCH",
        path="/repos/{owner}/{repo}/import/authors/{author_id}",
        query_params=frozenset(),
        body_params=frozenset({"email", "name"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Get large files": an array with no ``Paging:`` line, one request.
    RestOperation(
        operation_id="migrations/get-large-files",
        method="GET",
        path="/repos/{owner}/{repo}/import/large_files",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Update Git LFS preference"
    RestOperation(
        operation_id="migrations/set-lfs-preference",
        method="PATCH",
        path="/repos/{owner}/{repo}/import/lfs",
        query_params=frozenset(),
        body_params=frozenset({"use_lfs"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "List user migrations": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="migrations/list-for-authenticated-user",
        method="GET",
        path="/user/migrations",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Start a user migration"
    RestOperation(
        operation_id="migrations/start-for-authenticated-user",
        method="POST",
        path="/user/migrations",
        query_params=frozenset(),
        body_params=frozenset(
            {
                "lock_repositories",
                "exclude_metadata",
                "exclude_git_data",
                "exclude_attachments",
                "exclude_releases",
                "exclude_owner_projects",
                "org_metadata_only",
                "exclude",
                "repositories",
            }
        ),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Get a user migration status"
    RestOperation(
        operation_id="migrations/get-status-for-authenticated-user",
        method="GET",
        path="/user/migrations/{migration_id}",
        query_params=frozenset({"exclude"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Download a user migration archive": answers ``302``, a plain record (issue #33 Residuals).
    RestOperation(
        operation_id="migrations/get-archive-for-authenticated-user",
        method="GET",
        path="/user/migrations/{migration_id}/archive",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Delete a user migration archive"
    RestOperation(
        operation_id="migrations/delete-archive-for-authenticated-user",
        method="DELETE",
        path="/user/migrations/{migration_id}/archive",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "Unlock a user repository"
    RestOperation(
        operation_id="migrations/unlock-repo-for-authenticated-user",
        method="DELETE",
        path="/user/migrations/{migration_id}/repos/{repo_name}/lock",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/migrations.md "List repositories for a user migration": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="migrations/list-repos-for-authenticated-user",
        method="GET",
        path="/user/migrations/{migration_id}/repositories",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
