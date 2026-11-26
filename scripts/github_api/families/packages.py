"""The ``packages`` family of the GitHub operations index: the packages and package versions of an
organization, of the authenticated user and of a user, and their lists of packages in conflict during a Docker
migration.

Each record is its section of ``docs/api-reference/github/rest/packages.md``, in the order of its sections: the
operation line's method and path and the ``query`` rows of its ``Parameter`` table; no section documents a request
body. No path parameter row reads "may contain ``/``", so ``multi_segment`` is empty; every record sends
``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``.

The five sections with a ``Paging:`` line are ``Paging.LINK`` with no item key: each body is the array. The three
``packages/list-docker-migration-conflicting-packages-*`` sections and
``packages/get-all-package-versions-for-package-owned-by-user`` answer an array with no ``Paging:`` line, so they are
``Paging.NONE`` like every other record and send one request.

The ``packages/delete-*`` records delete a package or one of its versions and the ``packages/restore-*`` records
restore one; they write no branch and are declared (#28 Security "Destructive operations"). Every record is sent by
``call <operation-id>`` (#28); no operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "packages"

OPERATIONS: Tuple[RestOperation, ...] = (
    # rest/packages.md "Get list of conflicting packages during Docker migration for organization": an array with no
    # ``Paging:`` line, one request.
    RestOperation(
        operation_id="packages/list-docker-migration-conflicting-packages-for-organization",
        method="GET",
        path="/orgs/{org}/docker/conflicts",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List packages for an organization": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="packages/list-packages-for-organization",
        method="GET",
        path="/orgs/{org}/packages",
        query_params=frozenset({"package_type", "visibility", "page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package for an organization"
    RestOperation(
        operation_id="packages/get-package-for-organization",
        method="GET",
        path="/orgs/{org}/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete a package for an organization"
    RestOperation(
        operation_id="packages/delete-package-for-org",
        method="DELETE",
        path="/orgs/{org}/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore a package for an organization"
    RestOperation(
        operation_id="packages/restore-package-for-org",
        method="POST",
        path="/orgs/{org}/packages/{package_type}/{package_name}/restore",
        query_params=frozenset({"token"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List package versions for a package owned by an organization": pages by ``link``; the body is
    # the array.
    RestOperation(
        operation_id="packages/get-all-package-versions-for-package-owned-by-org",
        method="GET",
        path="/orgs/{org}/packages/{package_type}/{package_name}/versions",
        query_params=frozenset({"page", "per_page", "state"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package version for an organization"
    RestOperation(
        operation_id="packages/get-package-version-for-organization",
        method="GET",
        path="/orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete package version for an organization"
    RestOperation(
        operation_id="packages/delete-package-version-for-org",
        method="DELETE",
        path="/orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore package version for an organization"
    RestOperation(
        operation_id="packages/restore-package-version-for-org",
        method="POST",
        path="/orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}/restore",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get list of conflicting packages during Docker migration for authenticated-user": an array with
    # no ``Paging:`` line, one request.
    RestOperation(
        operation_id="packages/list-docker-migration-conflicting-packages-for-authenticated-user",
        method="GET",
        path="/user/docker/conflicts",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List packages for the authenticated user's namespace": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="packages/list-packages-for-authenticated-user",
        method="GET",
        path="/user/packages",
        query_params=frozenset({"package_type", "visibility", "page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package for the authenticated user"
    RestOperation(
        operation_id="packages/get-package-for-authenticated-user",
        method="GET",
        path="/user/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete a package for the authenticated user"
    RestOperation(
        operation_id="packages/delete-package-for-authenticated-user",
        method="DELETE",
        path="/user/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore a package for the authenticated user"
    RestOperation(
        operation_id="packages/restore-package-for-authenticated-user",
        method="POST",
        path="/user/packages/{package_type}/{package_name}/restore",
        query_params=frozenset({"token"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List package versions for a package owned by the authenticated user": pages by ``link``; the
    # body is the array.
    RestOperation(
        operation_id="packages/get-all-package-versions-for-package-owned-by-authenticated-user",
        method="GET",
        path="/user/packages/{package_type}/{package_name}/versions",
        query_params=frozenset({"page", "per_page", "state"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package version for the authenticated user"
    RestOperation(
        operation_id="packages/get-package-version-for-authenticated-user",
        method="GET",
        path="/user/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete a package version for the authenticated user"
    RestOperation(
        operation_id="packages/delete-package-version-for-authenticated-user",
        method="DELETE",
        path="/user/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore a package version for the authenticated user"
    RestOperation(
        operation_id="packages/restore-package-version-for-authenticated-user",
        method="POST",
        path="/user/packages/{package_type}/{package_name}/versions/{package_version_id}/restore",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get list of conflicting packages during Docker migration for user": an array with no ``Paging:``
    # line, one request.
    RestOperation(
        operation_id="packages/list-docker-migration-conflicting-packages-for-user",
        method="GET",
        path="/users/{username}/docker/conflicts",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List packages for a user": pages by ``link``; the body is the array.
    RestOperation(
        operation_id="packages/list-packages-for-user",
        method="GET",
        path="/users/{username}/packages",
        query_params=frozenset({"package_type", "visibility", "page", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package for a user"
    RestOperation(
        operation_id="packages/get-package-for-user",
        method="GET",
        path="/users/{username}/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete a package for a user"
    RestOperation(
        operation_id="packages/delete-package-for-user",
        method="DELETE",
        path="/users/{username}/packages/{package_type}/{package_name}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore a package for a user"
    RestOperation(
        operation_id="packages/restore-package-for-user",
        method="POST",
        path="/users/{username}/packages/{package_type}/{package_name}/restore",
        query_params=frozenset({"token"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "List package versions for a package owned by a user": an array with no ``Paging:`` line, one
    # request.
    RestOperation(
        operation_id="packages/get-all-package-versions-for-package-owned-by-user",
        method="GET",
        path="/users/{username}/packages/{package_type}/{package_name}/versions",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Get a package version for a user"
    RestOperation(
        operation_id="packages/get-package-version-for-user",
        method="GET",
        path="/users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Delete package version for a user"
    RestOperation(
        operation_id="packages/delete-package-version-for-user",
        method="DELETE",
        path="/users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/packages.md "Restore package version for a user"
    RestOperation(
        operation_id="packages/restore-package-version-for-user",
        method="POST",
        path="/users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}/restore",
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
