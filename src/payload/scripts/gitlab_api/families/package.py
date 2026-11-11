"""The ``package`` endpoint family of the GitLab wrapper: the package registries and the container registry.

Each record is transcribed from its row of ``docs/api-reference/gitlab/operations-index.md`` and its section of
``rest/package.md`` (issue #43, design.md D6), in the page's order and under a comment naming the section's ``##`` and
``###`` headings. The operation ID is ``package#`` and the anchor of the row's Reference, a ``-1``, ``-2`` ... suffix
included; the method and the path are the row's, verbatim, with its ``*name`` globs, its ``/<route-prefix>``, its ``$``
and its hyphenated ``:module-name`` as the row writes them. An entry that lists two endpoints, each Conan v1 entry (the
instance endpoint, then the project one) and NuGet "Upload a package file", has one record per endpoint, in the order
it lists them (issue #63, design.md D1, D8): its base record, the first of its ID, maps the endpoint it lists first, and
the record after it the other, a copy of the base record but for its path and any ``Param`` naming a path parameter of
its own path. ``call`` sends the base record without ``--endpoint`` and the other when ``--endpoint`` names it (``call
package#upload-a-package-file-5 --endpoint 'PUT /projects/:id/packages/nuget/v2'``).

A record declares one ``Param`` per ``query``, ``body`` or ``form`` row of its section's table, in table order, named
as the row writes it (``Symbolchecksum``, ``terraform-get``): a ``query`` row in the query, a ``body`` or ``form`` row
in the body. A row that names a path parameter of the record's path, whatever its ``In``, is that path parameter and is
given with ``--path``, so it has no ``Param``: the ``body`` rows ``module-name``, ``module-system`` and
``module-version`` of "Upload module" are its path's three hyphenated names. A ``Param``'s ``Kind`` is the row's Type:
``ARRAY`` for ``array of string`` and ``string array``, ``HASH`` for ``object``, ``ARRAY_OF_HASHES`` for ``array of
object``, ``FILE`` for ``file``, ``SCALAR`` for every other Type; it is ``required`` where Required reads ``yes``, and a
``conditional`` row is not. Every record's ``body`` is ``BodyFormat.JSON``, which a ``FILE`` value makes multipart, and
no record fixes a query value. The ``GET`` records whose section has the ``page`` and ``per_page`` query rows page by
offset (``conventions.md`` "Offset-based") and declare both rows; every other record is ``Paging.NONE``.

A record whose path starts with ``/<route-prefix>/`` (the Debian release and index files, npm's package metadata and
dist-tags, NuGet's feeds, metadata, search and symbol files) holds the values of its page's ``<route-prefix>`` line,
verbatim and in line order (``DEBIAN_ROUTE_PREFIXES``, ``NPM_ROUTE_PREFIXES``, ``NUGET_ROUTE_PREFIXES``), and takes
``--route-prefix`` naming one of them; a ``:id`` of the value is then a path parameter of the call. Every other record
holds none.

Each upload takes the form GitLab Workhorse reads on its route (design.md D5). The routes whose request body Workhorse
stores (``requestBodyUploader``), and npm's dist-tag route, whose body Rails reads whole, take their body with
``--input``: the Conan v1 and v2 recipe and package file uploads, Debian's, Maven's and npm's "Upload a package file",
npm "Create or update a dist-tag" (its body the version as a JSON string), Ruby gems "Upload a gem" and Terraform
"Upload module". Each of these records carries its body's ``content_type``, ``CONTENT_TYPE_JSON`` for npm's two and
``CONTENT_TYPE_OCTET_STREAM`` for the others; its ``file`` row is the body and has no ``Param``, and every other
attribute is a ``Location.QUERY`` ``Param``, where it is sent. NuGet "Upload a package file" and "Upload a symbol
package file", Helm "Upload a chart", PyPI "Upload a package" and the Maven virtual registry's "Upload a package" take
their file with ``--file`` and send it, and every other body attribute, as a ``multipart/form-data`` body.

The two container registry records whose path starts with ``/http(s)://${CI_REGISTRY}``, "Delete image tags by
reference" and "Listing all container repositories", are sent to the registry's own host, not this API (issue #63,
design.md D4): ``registry.send`` passes them to ``gitlab_api/container_registry.py``, which asks the configured instance
for a registry token and sends the record's request with that token alone. Each ``${NAME}`` of the path is a path
parameter given with ``--path``, and each record holds the ``token_scope`` its registry token is asked for,
docs.gitlab.com ``container_registry``'s: ``repository:${CI_REGISTRY_IMAGE}:delete`` and ``registry:catalog:*``.
Neither section has an attribute table, so neither declares a ``Param``.

``PENDING`` holds the one key kept without a record, ``PUT /projects/:id/``: the project update "Change the visibility
of the container registry" names, which can also configure a pull mirror. A secret attribute (an upstream registry's
``password``) is given as text like any other value; the configured token travels only in its header, and the
registry token only to the registry.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation
from gitlab_api.transport import CONTENT_TYPE_JSON, CONTENT_TYPE_OCTET_STREAM

FAMILY = "package"

# "Debian API": the values of its `<route-prefix>` line, verbatim and in line order.
DEBIAN_ROUTE_PREFIXES: Tuple[str, ...] = ("/projects/:id/packages/debian", "/groups/:id/-/packages/debian")
# "npm API": the values of its `<route-prefix>` line, verbatim and in line order.
NPM_ROUTE_PREFIXES: Tuple[str, ...] = ("/packages/npm", "/projects/:id/packages/npm", "/groups/:id/-/packages/npm")
# "NuGet API": the values of its `<route-prefix>` line, verbatim and in line order.
NUGET_ROUTE_PREFIXES: Tuple[str, ...] = ("/groups/:id/-/packages/nuget", "/projects/:id/packages/nuget")
# "Container registry API": the scope of the registry token of "Delete image tags by reference" and of "Listing all
# container repositories", docs.gitlab.com `container_registry`'s, `${CI_REGISTRY_IMAGE}` the call's value (D4).
REGISTRY_DELETE_SCOPE = "repository:${CI_REGISTRY_IMAGE}:delete"
REGISTRY_CATALOG_SCOPE = "registry:catalog:*"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Composer API: Retrieve repository URL templates".
    RestOperation(
        operation_id="package#retrieve-repository-url-templates",
        method="GET",
        path="/group/:id/-/packages/composer/packages",
    ),
    # "Composer API: V1 packages list".
    RestOperation(
        operation_id="package#v1-packages-list",
        method="GET",
        path="/group/:id/-/packages/composer/p/:sha",
    ),
    # "Composer API: Retrieve V1 package metadata".
    RestOperation(
        operation_id="package#retrieve-v1-package-metadata",
        method="GET",
        path="/group/:id/-/packages/composer/:package_name$:sha",
    ),
    # "Composer API: Retrieve V2 package metadata".
    RestOperation(
        operation_id="package#retrieve-v2-package-metadata",
        method="GET",
        path="/group/:id/-/packages/composer/p2/:package_name",
    ),
    # "Composer API: Create a package".
    RestOperation(
        operation_id="package#create-a-package",
        method="POST",
        path="/projects/:id/packages/composer",
        params=(
            Param(name="tag", location=Location.BODY),
            Param(name="branch", location=Location.BODY),
        ),
    ),
    # "Composer API: Download a package archive".
    RestOperation(
        operation_id="package#download-a-package-archive",
        method="GET",
        path="/projects/:id/packages/composer/archives/:package_name",
        params=(Param(name="sha", location=Location.QUERY, required=True),),
    ),
    # "Conan v1 API: Create an authentication token".
    RestOperation(
        operation_id="package#create-an-authentication-token",
        method="GET",
        path="/packages/conan/v1/users/authenticate",
    ),
    # "Conan v1 API: Create an authentication token": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#create-an-authentication-token",
        method="GET",
        path="/projects/:id/packages/conan/v1/users/authenticate",
    ),
    # "Conan v1 API: Verify availability of a Conan repository".
    RestOperation(
        operation_id="package#verify-availability-of-a-conan-repository",
        method="GET",
        path="/packages/conan/v1/ping",
    ),
    # "Conan v1 API: Verify availability of a Conan repository": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#verify-availability-of-a-conan-repository",
        method="GET",
        path="/projects/:id/packages/conan/v1/ping",
    ),
    # "Conan v1 API: Search for a Conan package".
    RestOperation(
        operation_id="package#search-for-a-conan-package",
        method="GET",
        path="/packages/conan/v1/conans/search",
        params=(
            Param(name="q", location=Location.QUERY, required=True),
            Param(name="ignorecase", location=Location.QUERY),
        ),
    ),
    # "Conan v1 API: Search for a Conan package": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#search-for-a-conan-package",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/search",
        params=(
            Param(name="q", location=Location.QUERY, required=True),
            Param(name="ignorecase", location=Location.QUERY),
        ),
    ),
    # "Conan v1 API: Verify authentication credentials".
    RestOperation(
        operation_id="package#verify-authentication-credentials",
        method="GET",
        path="/packages/conan/v1/users/check_credentials",
    ),
    # "Conan v1 API: Verify authentication credentials": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#verify-authentication-credentials",
        method="GET",
        path="/projects/:id/packages/conan/v1/users/check_credentials",
    ),
    # "Conan v1 API: Retrieve a recipe snapshot".
    RestOperation(
        operation_id="package#retrieve-a-recipe-snapshot",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel",
    ),
    # "Conan v1 API: Retrieve a recipe snapshot": the project endpoint, the one its entry lists second, as the index
    # writes it (without `:package_name`).
    RestOperation(
        operation_id="package#retrieve-a-recipe-snapshot",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_version/:package_username/:package_channel",
    ),
    # "Conan v1 API: Retrieve a package snapshot".
    RestOperation(
        operation_id="package#retrieve-a-package-snapshot",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference",
    ),
    # "Conan v1 API: Retrieve a package snapshot": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-a-package-snapshot",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference",
    ),
    # "Conan v1 API: Retrieve a recipe manifest".
    RestOperation(
        operation_id="package#retrieve-a-recipe-manifest",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/digest",
    ),
    # "Conan v1 API: Retrieve a recipe manifest": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-a-recipe-manifest",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/digest",
    ),
    # "Conan v1 API: Retrieve a package manifest".
    RestOperation(
        operation_id="package#retrieve-a-package-manifest",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/digest",
    ),
    # "Conan v1 API: Retrieve a package manifest": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-a-package-manifest",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/digest",
    ),
    # "Conan v1 API: List all recipe download URLs".
    RestOperation(
        operation_id="package#list-all-recipe-download-urls",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/download_urls",
    ),
    # "Conan v1 API: List all recipe download URLs": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#list-all-recipe-download-urls",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/download_urls",
    ),
    # "Conan v1 API: List all package download URLs".
    RestOperation(
        operation_id="package#list-all-package-download-urls",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/download_urls",
    ),
    # "Conan v1 API: List all package download URLs": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#list-all-package-download-urls",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/download_urls",
    ),
    # "Conan v1 API: List all recipe upload URLs".
    RestOperation(
        operation_id="package#list-all-recipe-upload-urls",
        method="POST",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/upload_urls",
    ),
    # "Conan v1 API: List all recipe upload URLs": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#list-all-recipe-upload-urls",
        method="POST",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/upload_urls",
    ),
    # "Conan v1 API: List all package upload URLs".
    RestOperation(
        operation_id="package#list-all-package-upload-urls",
        method="POST",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/upload_urls",
    ),
    # "Conan v1 API: List all package upload URLs": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#list-all-package-upload-urls",
        method="POST",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/upload_urls",
    ),
    # "Conan v1 API: Retrieve a recipe file".
    RestOperation(
        operation_id="package#retrieve-a-recipe-file",
        method="GET",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
    ),
    # "Conan v1 API: Retrieve a recipe file": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-a-recipe-file",
        method="GET",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
    ),
    # "Conan v1 API: Upload a recipe file".
    RestOperation(
        operation_id="package#upload-a-recipe-file",
        method="PUT",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v1 API: Upload a recipe file": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#upload-a-recipe-file",
        method="PUT",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v1 API: Retrieve a package file".
    RestOperation(
        operation_id="package#retrieve-a-package-file",
        method="GET",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
    ),
    # "Conan v1 API: Retrieve a package file": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-a-package-file",
        method="GET",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
    ),
    # "Conan v1 API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file",
        method="PUT",
        path="/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v1 API: Upload a package file": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#upload-a-package-file",
        method="PUT",
        path="/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v1 API: Delete a recipe and package".
    RestOperation(
        operation_id="package#delete-a-recipe-and-package",
        method="DELETE",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel",
    ),
    # "Conan v1 API: Delete a recipe and package": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#delete-a-recipe-and-package",
        method="DELETE",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel",
    ),
    # "Conan v1 API: Retrieve package references metadata".
    RestOperation(
        operation_id="package#retrieve-package-references-metadata",
        method="GET",
        path="/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/search",
    ),
    # "Conan v1 API: Retrieve package references metadata": the project endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#retrieve-package-references-metadata",
        method="GET",
        path="/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/search",
    ),
    # "Conan v2 API: Create an authentication token".
    RestOperation(
        operation_id="package#create-an-authentication-token-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/users/authenticate",
    ),
    # "Conan v2 API: Verify authentication credentials".
    RestOperation(
        operation_id="package#verify-authentication-credentials-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/users/check_credentials",
    ),
    # "Conan v2 API: Search for a Conan package".
    RestOperation(
        operation_id="package#search-for-a-conan-package-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/search",
        params=(
            Param(name="query", location=Location.QUERY, required=True),
            Param(name="q", location=Location.QUERY, required=True),
            Param(name="ignorecase", location=Location.QUERY),
        ),
    ),
    # "Conan v2 API: Retrieve latest recipe revision".
    RestOperation(
        operation_id="package#retrieve-latest-recipe-revision",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/latest",
    ),
    # "Conan v2 API: List all recipe revisions".
    RestOperation(
        operation_id="package#list-all-recipe-revisions",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions",
    ),
    # "Conan v2 API: Delete a recipe revision".
    RestOperation(
        operation_id="package#delete-a-recipe-revision",
        method="DELETE",
        path="/projects/:id/packages/conan/conans/:package_name/package_version/:package_username/:package_channel/revisions/:recipe_revision",
        params=(Param(name="package_version", location=Location.QUERY, required=True),),
    ),
    # "Conan v2 API: List all recipe files".
    RestOperation(
        operation_id="package#list-all-recipe-files",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/files",
    ),
    # "Conan v2 API: Retrieve a recipe file".
    RestOperation(
        operation_id="package#retrieve-a-recipe-file-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/files/:file_name",
    ),
    # "Conan v2 API: Upload a recipe file".
    RestOperation(
        operation_id="package#upload-a-recipe-file-1",
        method="PUT",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/files/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v2 API: List all package revisions".
    RestOperation(
        operation_id="package#list-all-package-revisions",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions",
    ),
    # "Conan v2 API: Retrieve latest package revision".
    RestOperation(
        operation_id="package#retrieve-latest-package-revision",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/latest",
    ),
    # "Conan v2 API: Delete a package revision".
    RestOperation(
        operation_id="package#delete-a-package-revision",
        method="DELETE",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions/:package_revision",
    ),
    # "Conan v2 API: Retrieve a package file".
    RestOperation(
        operation_id="package#retrieve-a-package-file-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions/:package_revision/files/:file_name",
    ),
    # "Conan v2 API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file-1",
        method="PUT",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/packages/:conan_package_reference/revisions/:package_revision/files/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Conan v2 API: Retrieve package references metadata".
    RestOperation(
        operation_id="package#retrieve-package-references-metadata-1",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/search",
    ),
    # "Conan v2 API: Retrieve package references metadata by recipe revision".
    RestOperation(
        operation_id="package#retrieve-package-references-metadata-by-recipe-revision",
        method="GET",
        path="/projects/:id/packages/conan/v2/conans/:package_name/:package_version/:package_username/:package_channel/revisions/:recipe_revision/search",
    ),
    # "Container registry API: Within a project".
    RestOperation(
        operation_id="package#within-a-project",
        method="GET",
        path="/projects/:id/registry/repositories",
        params=(
            Param(name="tags", location=Location.QUERY),
            Param(name="tags_count", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Container registry API: Within a group".
    RestOperation(
        operation_id="package#within-a-group",
        method="GET",
        path="/groups/:id/registry/repositories",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Container registry API: Retrieve details of a single repository".
    RestOperation(
        operation_id="package#retrieve-details-of-a-single-repository",
        method="GET",
        path="/registry/repositories/:id",
        params=(
            Param(name="tags", location=Location.QUERY),
            Param(name="tags_count", location=Location.QUERY),
            Param(name="size", location=Location.QUERY),
        ),
    ),
    # "Container registry API: Delete registry repository".
    RestOperation(
        operation_id="package#delete-registry-repository",
        method="DELETE",
        path="/projects/:id/registry/repositories/:repository_id",
    ),
    # "Container registry API: List all registry repository tags in a project".
    RestOperation(
        operation_id="package#list-all-registry-repository-tags-in-a-project",
        method="GET",
        path="/projects/:id/registry/repositories/:repository_id/tags",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Container registry API: Retrieve details of a registry repository tag".
    RestOperation(
        operation_id="package#retrieve-details-of-a-registry-repository-tag",
        method="GET",
        path="/projects/:id/registry/repositories/:repository_id/tags/:tag_name",
    ),
    # "Container registry API: Delete a registry repository tag".
    RestOperation(
        operation_id="package#delete-a-registry-repository-tag",
        method="DELETE",
        path="/projects/:id/registry/repositories/:repository_id/tags/:tag_name",
    ),
    # "Container registry API: Delete registry repository tags in bulk".
    RestOperation(
        operation_id="package#delete-registry-repository-tags-in-bulk",
        method="DELETE",
        path="/projects/:id/registry/repositories/:repository_id/tags",
        params=(
            Param(name="keep_n", location=Location.QUERY),
            Param(name="name_regex", location=Location.QUERY),
            Param(name="name_regex_delete", location=Location.QUERY, required=True),
            Param(name="name_regex_keep", location=Location.QUERY),
            Param(name="older_than", location=Location.QUERY),
        ),
    ),
    # "Container registry API: Delete image tags by reference": on the registry's own host (issue #63, design.md D4).
    RestOperation(
        operation_id="package#delete-image-tags-by-reference",
        method="DELETE",
        path="/http(s)://${CI_REGISTRY}/v2/${CI_REGISTRY_IMAGE}/tags/reference/${CI_COMMIT_SHORT_SHA}",
        token_scope=REGISTRY_DELETE_SCOPE,
    ),
    # "Container registry API: Listing all container repositories": on the registry's own host (issue #63, D4).
    RestOperation(
        operation_id="package#listing-all-container-repositories",
        method="GET",
        path="/http(s)://${CI_REGISTRY}/v2/_catalog",
        token_scope=REGISTRY_CATALOG_SCOPE,
    ),
    # "Container registry protection tag rules API: List container registry protection tag rules".
    RestOperation(
        operation_id="package#list-container-registry-protection-tag-rules",
        method="GET",
        path="/projects/:id/registry/protection/tag/rules",
    ),
    # "Container registry protection tag rules API: Create a container registry protection tag rule".
    RestOperation(
        operation_id="package#create-a-container-registry-protection-tag-rule",
        method="POST",
        path="/projects/:id/registry/protection/tag/rules",
        params=(
            Param(name="tag_name_pattern", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_push", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_delete", location=Location.BODY, required=True),
        ),
    ),
    # "Container registry protection tag rules API: Update a container registry protection tag rule".
    RestOperation(
        operation_id="package#update-a-container-registry-protection-tag-rule",
        method="PATCH",
        path="/projects/:id/registry/protection/tag/rules/:protection_rule_id",
        params=(
            Param(name="minimum_access_level_for_delete", location=Location.BODY),
            Param(name="minimum_access_level_for_push", location=Location.BODY),
            Param(name="tag_name_pattern", location=Location.BODY),
        ),
    ),
    # "Container registry protection tag rules API: Delete a container registry protection tag rule".
    RestOperation(
        operation_id="package#delete-a-container-registry-protection-tag-rule",
        method="DELETE",
        path="/projects/:id/registry/protection/tag/rules/:protection_rule_id",
    ),
    # "Container repository protection rules API: List all container repository protection rules".
    RestOperation(
        operation_id="package#list-all-container-repository-protection-rules",
        method="GET",
        path="/projects/:id/registry/protection/repository/rules",
    ),
    # "Container repository protection rules API: Create a container repository protection rule".
    RestOperation(
        operation_id="package#create-a-container-repository-protection-rule",
        method="POST",
        path="/projects/:id/registry/protection/repository/rules",
        params=(
            Param(name="repository_path_pattern", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_delete", location=Location.BODY),
            Param(name="minimum_access_level_for_push", location=Location.BODY),
        ),
    ),
    # "Container repository protection rules API: Update a container repository protection rule".
    RestOperation(
        operation_id="package#update-a-container-repository-protection-rule",
        method="PATCH",
        path="/projects/:id/registry/protection/repository/rules/:protection_rule_id",
        params=(
            Param(name="minimum_access_level_for_delete", location=Location.BODY),
            Param(name="minimum_access_level_for_push", location=Location.BODY),
            Param(name="repository_path_pattern", location=Location.BODY),
        ),
    ),
    # "Container repository protection rules API: Delete a container repository protection rule".
    RestOperation(
        operation_id="package#delete-a-container-repository-protection-rule",
        method="DELETE",
        path="/projects/:id/registry/protection/repository/rules/:protection_rule_id",
    ),
    # "Container virtual registry API: List all virtual registries".
    RestOperation(
        operation_id="package#list-all-virtual-registries",
        method="GET",
        path="/groups/:id/-/virtual_registries/container/registries",
    ),
    # "Container virtual registry API: Create a virtual registry".
    RestOperation(
        operation_id="package#create-a-virtual-registry",
        method="POST",
        path="/groups/:id/-/virtual_registries/container/registries",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: Retrieve a virtual registry".
    RestOperation(
        operation_id="package#retrieve-a-virtual-registry",
        method="GET",
        path="/virtual_registries/container/registries/:id",
    ),
    # "Container virtual registry API: Update a virtual registry".
    RestOperation(
        operation_id="package#update-a-virtual-registry",
        method="PATCH",
        path="/virtual_registries/container/registries/:id",
        params=(
            Param(name="description", location=Location.BODY),
            Param(name="name", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: Delete a virtual registry".
    RestOperation(
        operation_id="package#delete-a-virtual-registry",
        method="DELETE",
        path="/virtual_registries/container/registries/:id",
    ),
    # "Container virtual registry API: Delete cache entries for a virtual registry".
    RestOperation(
        operation_id="package#delete-cache-entries-for-a-virtual-registry",
        method="DELETE",
        path="/virtual_registries/container/registries/:id/cache",
    ),
    # "Container virtual registry API: List all upstream registries for a top-level group".
    RestOperation(
        operation_id="package#list-all-upstream-registries-for-a-top-level-group",
        method="GET",
        path="/groups/:id/-/virtual_registries/container/upstreams",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="upstream_name", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Container virtual registry API: Test connection before creating an upstream registry".
    RestOperation(
        operation_id="package#test-connection-before-creating-an-upstream-registry",
        method="POST",
        path="/groups/:id/-/virtual_registries/container/upstreams/test",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: List all upstream registries for a virtual registry".
    RestOperation(
        operation_id="package#list-all-upstream-registries-for-a-virtual-registry",
        method="GET",
        path="/virtual_registries/container/registries/:id/upstreams",
    ),
    # "Container virtual registry API: Create an upstream registry".
    RestOperation(
        operation_id="package#create-an-upstream-registry",
        method="POST",
        path="/virtual_registries/container/registries/:id/upstreams",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: Retrieve an upstream registry".
    RestOperation(
        operation_id="package#retrieve-an-upstream-registry",
        method="GET",
        path="/virtual_registries/container/upstreams/:id",
    ),
    # "Container virtual registry API: Update an upstream registry".
    RestOperation(
        operation_id="package#update-an-upstream-registry",
        method="PATCH",
        path="/virtual_registries/container/upstreams/:id",
        params=(
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: Update an upstream registry position".
    RestOperation(
        operation_id="package#update-an-upstream-registry-position",
        method="PATCH",
        path="/virtual_registries/container/registry_upstreams/:id",
        params=(Param(name="position", location=Location.BODY, required=True),),
    ),
    # "Container virtual registry API: Delete an upstream registry".
    RestOperation(
        operation_id="package#delete-an-upstream-registry",
        method="DELETE",
        path="/virtual_registries/container/upstreams/:id",
    ),
    # "Container virtual registry API: Associate an upstream with a registry".
    RestOperation(
        operation_id="package#associate-an-upstream-with-a-registry",
        method="POST",
        path="/virtual_registries/container/registry_upstreams",
        params=(
            Param(name="registry_id", location=Location.BODY, required=True),
            Param(name="upstream_id", location=Location.BODY, required=True),
        ),
    ),
    # "Container virtual registry API: Disassociate an upstream from a registry".
    RestOperation(
        operation_id="package#disassociate-an-upstream-from-a-registry",
        method="DELETE",
        path="/virtual_registries/container/registry_upstreams/:id",
    ),
    # "Container virtual registry API: Delete cache entries for an upstream registry".
    RestOperation(
        operation_id="package#delete-cache-entries-for-an-upstream-registry",
        method="DELETE",
        path="/virtual_registries/container/upstreams/:id/cache",
    ),
    # "Container virtual registry API: Test connection to an upstream registry with override parameters".
    RestOperation(
        operation_id="package#test-connection-to-an-upstream-registry-with-override-parameters",
        method="POST",
        path="/virtual_registries/container/upstreams/:id/test",
        params=(
            Param(name="password", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Container virtual registry API: List upstream registry cache entries".
    RestOperation(
        operation_id="package#list-upstream-registry-cache-entries",
        method="GET",
        path="/virtual_registries/container/upstreams/:id/cache_entries",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Container virtual registry API: Delete an upstream registry cache entry".
    RestOperation(
        operation_id="package#delete-an-upstream-registry-cache-entry",
        method="DELETE",
        path="/virtual_registries/container/cache_entries/*id",
    ),
    # "Debian API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file-2",
        method="PUT",
        path="/projects/:id/packages/debian/:file_name",
        params=(
            Param(name="distribution", location=Location.QUERY),
            Param(name="component", location=Location.QUERY),
        ),
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Debian API: Download a package".
    RestOperation(
        operation_id="package#download-a-package",
        method="GET",
        path="/projects/:id/packages/debian/pool/:distribution/:letter/:package_name/:package_version/:file_name",
    ),
    # "Debian API: Download a distribution Release file".
    RestOperation(
        operation_id="package#download-a-distribution-release-file",
        method="GET",
        path="/<route-prefix>/dists/*distribution/Release",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a signed distribution Release file".
    RestOperation(
        operation_id="package#download-a-signed-distribution-release-file",
        method="GET",
        path="/<route-prefix>/dists/*distribution/InRelease",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a release file signature".
    RestOperation(
        operation_id="package#download-a-release-file-signature",
        method="GET",
        path="/<route-prefix>/dists/*distribution/Release.gpg",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a packages index".
    RestOperation(
        operation_id="package#download-a-packages-index",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/binary-:architecture/Packages",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a packages index by hash".
    RestOperation(
        operation_id="package#download-a-packages-index-by-hash",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/binary-:architecture/by-hash/SHA256/:file_sha256",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a Debian Installer packages index".
    RestOperation(
        operation_id="package#download-a-debian-installer-packages-index",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/debian-installer/binary-:architecture/Packages",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a Debian Installer packages index by hash".
    RestOperation(
        operation_id="package#download-a-debian-installer-packages-index-by-hash",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/debian-installer/binary-:architecture/by-hash/SHA256/:file_sha256",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a source packages index".
    RestOperation(
        operation_id="package#download-a-source-packages-index",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/source/Sources",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian API: Download a source packages index by hash".
    RestOperation(
        operation_id="package#download-a-source-packages-index-by-hash",
        method="GET",
        path="/<route-prefix>/dists/*distribution/:component/source/by-hash/SHA256/:file_sha256",
        route_prefixes=DEBIAN_ROUTE_PREFIXES,
    ),
    # "Debian group distributions API: List all Debian distributions in a group".
    RestOperation(
        operation_id="package#list-all-debian-distributions-in-a-group",
        method="GET",
        path="/groups/:id/-/debian_distributions",
        params=(
            Param(name="codename", location=Location.QUERY),
            Param(name="suite", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="origin", location=Location.QUERY),
            Param(name="label", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
            Param(name="description", location=Location.QUERY),
            Param(name="valid_time_duration_seconds", location=Location.QUERY),
            Param(name="components", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.QUERY, kind=Kind.ARRAY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Debian group distributions API: Retrieve a Debian group distribution".
    RestOperation(
        operation_id="package#retrieve-a-debian-group-distribution",
        method="GET",
        path="/groups/:id/-/debian_distributions/:codename",
    ),
    # "Debian group distributions API: Retrieve a Debian group distribution key".
    RestOperation(
        operation_id="package#retrieve-a-debian-group-distribution-key",
        method="GET",
        path="/groups/:id/-/debian_distributions/:codename/key.asc",
    ),
    # "Debian group distributions API: Create a Debian group distribution".
    RestOperation(
        operation_id="package#create-a-debian-group-distribution",
        method="POST",
        path="/groups/:id/-/debian_distributions",
        params=(
            Param(name="codename", location=Location.BODY, required=True),
            Param(name="suite", location=Location.BODY),
            Param(name="origin", location=Location.BODY),
            Param(name="label", location=Location.BODY),
            Param(name="version", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="valid_time_duration_seconds", location=Location.BODY),
            Param(name="components", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Debian group distributions API: Update a Debian group distribution".
    RestOperation(
        operation_id="package#update-a-debian-group-distribution",
        method="PUT",
        path="/groups/:id/-/debian_distributions/:codename",
        params=(
            Param(name="suite", location=Location.BODY),
            Param(name="origin", location=Location.BODY),
            Param(name="label", location=Location.BODY),
            Param(name="version", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="valid_time_duration_seconds", location=Location.BODY),
            Param(name="components", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Debian group distributions API: Delete a Debian group distribution".
    RestOperation(
        operation_id="package#delete-a-debian-group-distribution",
        method="DELETE",
        path="/groups/:id/-/debian_distributions/:codename",
        params=(
            Param(name="suite", location=Location.QUERY),
            Param(name="origin", location=Location.QUERY),
            Param(name="label", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
            Param(name="description", location=Location.QUERY),
            Param(name="valid_time_duration_seconds", location=Location.QUERY),
            Param(name="components", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.QUERY, kind=Kind.ARRAY),
        ),
    ),
    # "Debian project distributions API: List all Debian distributions in a project".
    RestOperation(
        operation_id="package#list-all-debian-distributions-in-a-project",
        method="GET",
        path="/projects/:id/debian_distributions",
        params=(
            Param(name="codename", location=Location.QUERY),
            Param(name="suite", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="origin", location=Location.QUERY),
            Param(name="label", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
            Param(name="description", location=Location.QUERY),
            Param(name="valid_time_duration_seconds", location=Location.QUERY),
            Param(name="components", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.QUERY, kind=Kind.ARRAY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Debian project distributions API: Retrieve a Debian project distribution".
    RestOperation(
        operation_id="package#retrieve-a-debian-project-distribution",
        method="GET",
        path="/projects/:id/debian_distributions/:codename",
    ),
    # "Debian project distributions API: Retrieve a Debian project distribution key".
    RestOperation(
        operation_id="package#retrieve-a-debian-project-distribution-key",
        method="GET",
        path="/projects/:id/debian_distributions/:codename/key.asc",
    ),
    # "Debian project distributions API: Create a Debian project distribution".
    RestOperation(
        operation_id="package#create-a-debian-project-distribution",
        method="POST",
        path="/projects/:id/debian_distributions",
        params=(
            Param(name="codename", location=Location.BODY, required=True),
            Param(name="suite", location=Location.BODY),
            Param(name="origin", location=Location.BODY),
            Param(name="label", location=Location.BODY),
            Param(name="version", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="valid_time_duration_seconds", location=Location.BODY),
            Param(name="components", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Debian project distributions API: Update a Debian project distribution".
    RestOperation(
        operation_id="package#update-a-debian-project-distribution",
        method="PUT",
        path="/projects/:id/debian_distributions/:codename",
        params=(
            Param(name="suite", location=Location.BODY),
            Param(name="origin", location=Location.BODY),
            Param(name="label", location=Location.BODY),
            Param(name="version", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="valid_time_duration_seconds", location=Location.BODY),
            Param(name="components", location=Location.BODY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.BODY, kind=Kind.ARRAY),
        ),
    ),
    # "Debian project distributions API: Delete a Debian project distribution".
    RestOperation(
        operation_id="package#delete-a-debian-project-distribution",
        method="DELETE",
        path="/projects/:id/debian_distributions/:codename",
        params=(
            Param(name="suite", location=Location.QUERY),
            Param(name="origin", location=Location.QUERY),
            Param(name="label", location=Location.QUERY),
            Param(name="version", location=Location.QUERY),
            Param(name="description", location=Location.QUERY),
            Param(name="valid_time_duration_seconds", location=Location.QUERY),
            Param(name="components", location=Location.QUERY, kind=Kind.ARRAY),
            Param(name="architectures", location=Location.QUERY, kind=Kind.ARRAY),
        ),
    ),
    # "Dependency Proxy API: Purge the dependency proxy for a group".
    RestOperation(
        operation_id="package#purge-the-dependency-proxy-for-a-group",
        method="DELETE",
        path="/groups/:id/dependency_proxy/cache",
    ),
    # "Go Proxy API: List".
    RestOperation(
        operation_id="package#list",
        method="GET",
        path="/projects/:id/packages/go/:module_name/@v/list",
    ),
    # "Go Proxy API: Version metadata".
    RestOperation(
        operation_id="package#version-metadata",
        method="GET",
        path="/projects/:id/packages/go/:module_name/@v/:module_version.info",
    ),
    # "Go Proxy API: Download module file".
    RestOperation(
        operation_id="package#download-module-file",
        method="GET",
        path="/projects/:id/packages/go/:module_name/@v/:module_version.mod",
    ),
    # "Go Proxy API: Download module source".
    RestOperation(
        operation_id="package#download-module-source",
        method="GET",
        path="/projects/:id/packages/go/:module_name/@v/:module_version.zip",
    ),
    # "Helm API: Download a chart index".
    RestOperation(
        operation_id="package#download-a-chart-index",
        method="GET",
        path="/projects/:id/packages/helm/:channel/index.yaml",
    ),
    # "Helm API: Download a chart".
    RestOperation(
        operation_id="package#download-a-chart",
        method="GET",
        path="/projects/:id/packages/helm/:channel/charts/:file_name.tgz",
    ),
    # "Helm API: Upload a chart".
    RestOperation(
        operation_id="package#upload-a-chart",
        method="POST",
        path="/projects/:id/packages/helm/api/:channel/charts",
        params=(Param(name="chart", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "Maven API: Download a package file for an instance".
    RestOperation(
        operation_id="package#download-a-package-file-for-an-instance",
        method="GET",
        path="/packages/maven/*path/:file_name",
    ),
    # "Maven API: Download a package file for a group".
    RestOperation(
        operation_id="package#download-a-package-file-for-a-group",
        method="GET",
        path="/groups/:id/-/packages/maven/*path/:file_name",
    ),
    # "Maven API: Download a package file for a project".
    RestOperation(
        operation_id="package#download-a-package-file-for-a-project",
        method="GET",
        path="/projects/:id/packages/maven/*path/:file_name",
    ),
    # "Maven API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file-3",
        method="PUT",
        path="/projects/:id/packages/maven/*path/:file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Maven virtual registry API: List all virtual registries".
    RestOperation(
        operation_id="package#list-all-virtual-registries-1",
        method="GET",
        path="/groups/:id/-/virtual_registries/packages/maven/registries",
    ),
    # "Maven virtual registry API: Create a virtual registry".
    RestOperation(
        operation_id="package#create-a-virtual-registry-1",
        method="POST",
        path="/groups/:id/-/virtual_registries/packages/maven/registries",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Retrieve a virtual registry".
    RestOperation(
        operation_id="package#retrieve-a-virtual-registry-1",
        method="GET",
        path="/virtual_registries/packages/maven/registries/:id",
    ),
    # "Maven virtual registry API: Update a virtual registry".
    RestOperation(
        operation_id="package#update-a-virtual-registry-1",
        method="PATCH",
        path="/virtual_registries/packages/maven/registries/:id",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="description", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Delete a virtual registry".
    RestOperation(
        operation_id="package#delete-a-virtual-registry-1",
        method="DELETE",
        path="/virtual_registries/packages/maven/registries/:id",
    ),
    # "Maven virtual registry API: Delete cache entries for a virtual registry".
    RestOperation(
        operation_id="package#delete-cache-entries-for-a-virtual-registry-1",
        method="DELETE",
        path="/virtual_registries/packages/maven/registries/:id/cache",
    ),
    # "Maven virtual registry API: List all upstream registries".
    RestOperation(
        operation_id="package#list-all-upstream-registries",
        method="GET",
        path="/groups/:id/-/virtual_registries/packages/maven/upstreams",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="upstream_name", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Maven virtual registry API: Test upstream registry connection before creation".
    RestOperation(
        operation_id="package#test-upstream-registry-connection-before-creation",
        method="POST",
        path="/groups/:id/-/virtual_registries/packages/maven/upstreams/test",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="password", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: List all upstream registries for a virtual registry".
    RestOperation(
        operation_id="package#list-all-upstream-registries-for-a-virtual-registry-1",
        method="GET",
        path="/virtual_registries/packages/maven/registries/:id/upstreams",
    ),
    # "Maven virtual registry API: Create an upstream registry".
    RestOperation(
        operation_id="package#create-an-upstream-registry-1",
        method="POST",
        path="/virtual_registries/packages/maven/registries/:id/upstreams",
        params=(
            Param(name="url", location=Location.BODY, required=True),
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="metadata_cache_validity_hours", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Create a local upstream registry".
    RestOperation(
        operation_id="package#create-a-local-upstream-registry",
        method="POST",
        path="/virtual_registries/packages/maven/registries/:id/local/upstreams",
        params=(
            Param(name="name", location=Location.BODY, required=True),
            Param(name="local_group_id", location=Location.BODY),
            Param(name="local_project_id", location=Location.BODY),
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="metadata_cache_validity_hours", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Retrieve a local upstream registry".
    RestOperation(
        operation_id="package#retrieve-a-local-upstream-registry",
        method="GET",
        path="/virtual_registries/packages/maven/local/upstreams/:id",
    ),
    # "Maven virtual registry API: Update a local upstream registry".
    RestOperation(
        operation_id="package#update-a-local-upstream-registry",
        method="PATCH",
        path="/virtual_registries/packages/maven/local/upstreams/:id",
        params=(
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="metadata_cache_validity_hours", location=Location.BODY),
            Param(name="name", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Delete a local upstream registry".
    RestOperation(
        operation_id="package#delete-a-local-upstream-registry",
        method="DELETE",
        path="/virtual_registries/packages/maven/local/upstreams/:id",
    ),
    # "Maven virtual registry API: Retrieve an upstream registry".
    RestOperation(
        operation_id="package#retrieve-an-upstream-registry-1",
        method="GET",
        path="/virtual_registries/packages/maven/upstreams/:id",
    ),
    # "Maven virtual registry API: Update an upstream registry".
    RestOperation(
        operation_id="package#update-an-upstream-registry-1",
        method="PATCH",
        path="/virtual_registries/packages/maven/upstreams/:id",
        params=(
            Param(name="cache_validity_hours", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="metadata_cache_validity_hours", location=Location.BODY),
            Param(name="name", location=Location.BODY),
            Param(name="password", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: Update an upstream registry position".
    RestOperation(
        operation_id="package#update-an-upstream-registry-position-1",
        method="PATCH",
        path="/virtual_registries/packages/maven/registry_upstreams/:id",
        params=(Param(name="position", location=Location.BODY, required=True),),
    ),
    # "Maven virtual registry API: Delete an upstream registry".
    RestOperation(
        operation_id="package#delete-an-upstream-registry-1",
        method="DELETE",
        path="/virtual_registries/packages/maven/upstreams/:id",
    ),
    # "Maven virtual registry API: Associate an upstream registry with a virtual registry".
    RestOperation(
        operation_id="package#associate-an-upstream-registry-with-a-virtual-registry",
        method="POST",
        path="/virtual_registries/packages/maven/registry_upstreams",
        params=(
            Param(name="registry_id", location=Location.BODY, required=True),
            Param(name="upstream_id", location=Location.BODY, required=True),
            Param(name="local_upstream_id", location=Location.BODY, required=True),
        ),
    ),
    # "Maven virtual registry API: Disassociate an upstream registry from a virtual registry".
    RestOperation(
        operation_id="package#disassociate-an-upstream-registry-from-a-virtual-registry",
        method="DELETE",
        path="/virtual_registries/packages/maven/registry_upstreams/:id",
    ),
    # "Maven virtual registry API: Delete cache entries for an upstream registry".
    RestOperation(
        operation_id="package#delete-cache-entries-for-an-upstream-registry-1",
        method="DELETE",
        path="/virtual_registries/packages/maven/upstreams/:id/cache",
    ),
    # "Maven virtual registry API: Test upstream registry connection".
    RestOperation(
        operation_id="package#test-upstream-registry-connection",
        method="GET",
        path="/virtual_registries/packages/maven/upstreams/:id/test",
    ),
    # "Maven virtual registry API: Test upstream registry connection with override parameters".
    RestOperation(
        operation_id="package#test-upstream-registry-connection-with-override-parameters",
        method="POST",
        path="/virtual_registries/packages/maven/upstreams/:id/test",
        params=(
            Param(name="password", location=Location.BODY),
            Param(name="url", location=Location.BODY),
            Param(name="username", location=Location.BODY),
        ),
    ),
    # "Maven virtual registry API: List all upstream registry cache entries".
    RestOperation(
        operation_id="package#list-all-upstream-registry-cache-entries",
        method="GET",
        path="/virtual_registries/packages/maven/upstreams/:id/cache_entries",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="search", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Maven virtual registry API: Delete an upstream registry cache entry".
    RestOperation(
        operation_id="package#delete-an-upstream-registry-cache-entry-1",
        method="DELETE",
        path="/virtual_registries/packages/maven/cache_entries/*id",
    ),
    # "Maven virtual registry API: Download a package".
    RestOperation(
        operation_id="package#download-a-package-1",
        method="GET",
        path="/virtual_registries/packages/maven/:id/*path",
    ),
    # "Maven virtual registry API: Upload a package".
    RestOperation(
        operation_id="package#upload-a-package",
        method="POST",
        path="/virtual_registries/packages/maven/:id/*path/upload",
        params=(Param(name="file", location=Location.BODY, kind=Kind.FILE, required=True),),
    ),
    # "npm API: Download a package".
    RestOperation(
        operation_id="package#download-a-package-2",
        method="GET",
        path="/projects/:id/packages/npm/:package_name/-/:file_name",
    ),
    # "npm API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file-4",
        method="PUT",
        path="/projects/:id/packages/npm/:package_name",
        params=(Param(name="versions", location=Location.QUERY, required=True),),
        content_type=CONTENT_TYPE_JSON,
    ),
    # "npm API: Retrieve package metadata".
    RestOperation(
        operation_id="package#retrieve-package-metadata",
        method="GET",
        path="/<route-prefix>/:package_name",
        route_prefixes=NPM_ROUTE_PREFIXES,
    ),
    # "npm API: List all dist-tags".
    RestOperation(
        operation_id="package#list-all-dist-tags",
        method="GET",
        path="/<route-prefix>/-/package/:package_name/dist-tags",
        route_prefixes=NPM_ROUTE_PREFIXES,
    ),
    # "npm API: Create or update a dist-tag".
    RestOperation(
        operation_id="package#create-or-update-a-dist-tag",
        method="PUT",
        path="/<route-prefix>/-/package/:package_name/dist-tags/:tag",
        params=(Param(name="version", location=Location.QUERY, required=True),),
        content_type=CONTENT_TYPE_JSON,
        route_prefixes=NPM_ROUTE_PREFIXES,
    ),
    # "npm API: Delete a dist-tag".
    RestOperation(
        operation_id="package#delete-a-dist-tag",
        method="DELETE",
        path="/<route-prefix>/-/package/:package_name/dist-tags/:tag",
        route_prefixes=NPM_ROUTE_PREFIXES,
    ),
    # "NuGet API: Retrieve a package index".
    RestOperation(
        operation_id="package#retrieve-a-package-index",
        method="GET",
        path="/projects/:id/packages/nuget/download/:package_name/index",
    ),
    # "NuGet API: Download a package file".
    RestOperation(
        operation_id="package#download-a-package-file",
        method="GET",
        path="/projects/:id/packages/nuget/download/:package_name/:package_version/:package_filename",
    ),
    # "NuGet API: Upload a package file".
    RestOperation(
        operation_id="package#upload-a-package-file-5",
        method="PUT",
        path="/projects/:id/packages/nuget",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="package_version", location=Location.BODY, required=True),
            Param(name="package_filename", location=Location.BODY, required=True),
            Param(name="package", location=Location.BODY, kind=Kind.FILE, required=True),
        ),
    ),
    # "NuGet API: Upload a package file": the `/v2` endpoint, the one its entry lists second.
    RestOperation(
        operation_id="package#upload-a-package-file-5",
        method="PUT",
        path="/projects/:id/packages/nuget/v2",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="package_version", location=Location.BODY, required=True),
            Param(name="package_filename", location=Location.BODY, required=True),
            Param(name="package", location=Location.BODY, kind=Kind.FILE, required=True),
        ),
    ),
    # "NuGet API: Upload a symbol package file".
    RestOperation(
        operation_id="package#upload-a-symbol-package-file",
        method="PUT",
        path="/projects/:id/packages/nuget/symbolpackage",
        params=(
            Param(name="package_name", location=Location.BODY, required=True),
            Param(name="package_version", location=Location.BODY, required=True),
            Param(name="package_filename", location=Location.BODY, required=True),
            Param(name="package", location=Location.BODY, kind=Kind.FILE, required=True),
        ),
    ),
    # "NuGet API: V2 source feed/protocol".
    RestOperation(
        operation_id="package#v2-source-feedprotocol",
        method="GET",
        path="/<route-prefix>/v2",
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: V3 source feed/protocol".
    RestOperation(
        operation_id="package#v3-source-feedprotocol",
        method="GET",
        path="/<route-prefix>/index",
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: Retrieve package metadata".
    RestOperation(
        operation_id="package#retrieve-package-metadata-1",
        method="GET",
        path="/<route-prefix>/metadata/:package_name/index",
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: Retrieve version metadata".
    RestOperation(
        operation_id="package#retrieve-version-metadata",
        method="GET",
        path="/<route-prefix>/metadata/:package_name/:package_version",
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: Search for packages".
    RestOperation(
        operation_id="package#search-for-packages",
        method="GET",
        path="/<route-prefix>/query",
        params=(
            Param(name="q", location=Location.QUERY, required=True),
            Param(name="skip", location=Location.QUERY),
            Param(name="take", location=Location.QUERY),
            Param(name="prerelease", location=Location.QUERY),
        ),
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: Delete a package".
    RestOperation(
        operation_id="package#delete-a-package",
        method="DELETE",
        path="/projects/:id/packages/nuget/:package_name/:package_version",
    ),
    # "NuGet API: Download a debugging symbol file `.pdb`".
    RestOperation(
        operation_id="package#download-a-debugging-symbol-file-pdb",
        method="GET",
        path="/<route-prefix>/symbolfiles/:file_name/:signature/:file_name",
        params=(Param(name="Symbolchecksum", location=Location.QUERY, required=True),),
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "NuGet API: $metadata endpoint".
    RestOperation(
        operation_id="package#metadata-endpoint",
        method="GET",
        path="/<route-prefix>/v2/$metadata",
        route_prefixes=NUGET_ROUTE_PREFIXES,
    ),
    # "Packages API: For a project".
    RestOperation(
        operation_id="package#for-a-project",
        method="GET",
        path="/projects/:id/packages",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="package_type", location=Location.QUERY),
            Param(name="package_name", location=Location.QUERY),
            Param(name="package_version", location=Location.QUERY),
            Param(name="include_versionless", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Packages API: For a group".
    RestOperation(
        operation_id="package#for-a-group",
        method="GET",
        path="/groups/:id/packages",
        params=(
            Param(name="exclude_subgroups", location=Location.QUERY),
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="package_type", location=Location.QUERY),
            Param(name="package_name", location=Location.QUERY),
            Param(name="package_version", location=Location.QUERY),
            Param(name="include_versionless", location=Location.QUERY),
            Param(name="status", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Packages API: Retrieve a project package".
    RestOperation(
        operation_id="package#retrieve-a-project-package",
        method="GET",
        path="/projects/:id/packages/:package_id",
    ),
    # "Packages API: List package files".
    RestOperation(
        operation_id="package#list-package-files",
        method="GET",
        path="/projects/:id/packages/:package_id/package_files",
        params=(
            Param(name="order_by", location=Location.QUERY),
            Param(name="sort", location=Location.QUERY),
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Packages API: List package pipelines".
    RestOperation(
        operation_id="package#list-package-pipelines",
        method="GET",
        path="/projects/:id/packages/:package_id/pipelines",
        params=(
            Param(name="page", location=Location.QUERY),
            Param(name="per_page", location=Location.QUERY),
            Param(name="cursor", location=Location.QUERY),
        ),
        paging=Paging.OFFSET,
    ),
    # "Packages API: Delete a project package".
    RestOperation(
        operation_id="package#delete-a-project-package",
        method="DELETE",
        path="/projects/:id/packages/:package_id",
    ),
    # "Packages API: Delete a package file".
    RestOperation(
        operation_id="package#delete-a-package-file",
        method="DELETE",
        path="/projects/:id/packages/:package_id/package_files/:package_file_id",
    ),
    # "Protected packages API: List all package protection rules".
    RestOperation(
        operation_id="package#list-all-package-protection-rules",
        method="GET",
        path="/projects/:id/packages/protection/rules",
    ),
    # "Protected packages API: Create a package protection rule".
    RestOperation(
        operation_id="package#create-a-package-protection-rule",
        method="POST",
        path="/projects/:id/packages/protection/rules",
        params=(
            Param(name="package_name_pattern", location=Location.BODY, required=True),
            Param(name="package_type", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_delete", location=Location.BODY, required=True),
            Param(name="minimum_access_level_for_push", location=Location.BODY, required=True),
        ),
    ),
    # "Protected packages API: Update a package protection rule".
    RestOperation(
        operation_id="package#update-a-package-protection-rule",
        method="PATCH",
        path="/projects/:id/packages/protection/rules/:package_protection_rule_id",
        params=(
            Param(name="package_name_pattern", location=Location.BODY),
            Param(name="package_type", location=Location.BODY),
            Param(name="minimum_access_level_for_delete", location=Location.BODY),
            Param(name="minimum_access_level_for_push", location=Location.BODY),
        ),
    ),
    # "Protected packages API: Delete a package protection rule".
    RestOperation(
        operation_id="package#delete-a-package-protection-rule",
        method="DELETE",
        path="/projects/:id/packages/protection/rules/:package_protection_rule_id",
    ),
    # "PyPI API: Download a package file for a group".
    RestOperation(
        operation_id="package#download-a-package-file-for-a-group-1",
        method="GET",
        path="/groups/:id/-/packages/pypi/files/:sha256/:file_identifier",
    ),
    # "PyPI API: List all packages for a group".
    RestOperation(
        operation_id="package#list-all-packages-for-a-group",
        method="GET",
        path="/groups/:id/-/packages/pypi/simple",
    ),
    # "PyPI API: Retrieve package descriptor for a group".
    RestOperation(
        operation_id="package#retrieve-package-descriptor-for-a-group",
        method="GET",
        path="/groups/:id/-/packages/pypi/simple/:package_name",
    ),
    # "PyPI API: Download a package file for a project".
    RestOperation(
        operation_id="package#download-a-package-file-for-a-project-1",
        method="GET",
        path="/projects/:id/packages/pypi/files/:sha256/:file_identifier",
    ),
    # "PyPI API: List all packages for a project".
    RestOperation(
        operation_id="package#list-all-packages-for-a-project",
        method="GET",
        path="/projects/:id/packages/pypi/simple",
    ),
    # "PyPI API: Retrieve package descriptor for a project".
    RestOperation(
        operation_id="package#retrieve-package-descriptor-for-a-project",
        method="GET",
        path="/projects/:id/packages/pypi/simple/:package_name",
    ),
    # "PyPI API: Upload a package".
    RestOperation(
        operation_id="package#upload-a-package-1",
        method="POST",
        path="/projects/:id/packages/pypi",
        params=(
            Param(name="requires_python", location=Location.BODY),
            Param(name="sha256_digest", location=Location.BODY),
            Param(name="content", location=Location.BODY, kind=Kind.FILE, required=True),
            Param(name="name", location=Location.BODY, required=True),
            Param(name="version", location=Location.BODY, required=True),
            Param(name="md5_digest", location=Location.BODY),
            Param(name="metadata_version", location=Location.BODY),
            Param(name="author_email", location=Location.BODY),
            Param(name="description", location=Location.BODY),
            Param(name="description_content_type", location=Location.BODY),
            Param(name="summary", location=Location.BODY),
            Param(name="keywords", location=Location.BODY),
        ),
    ),
    # "Ruby gems API: Download a gem file".
    RestOperation(
        operation_id="package#download-a-gem-file",
        method="GET",
        path="/projects/:id/packages/rubygems/gems/:file_name",
    ),
    # "Ruby gems API: Download a gemspec file".
    RestOperation(
        operation_id="package#download-a-gemspec-file",
        method="GET",
        path="/projects/:id/packages/rubygems/quick/Marshal.4.8/:file_name",
    ),
    # "Ruby gems API: Download a spec index file".
    RestOperation(
        operation_id="package#download-a-spec-index-file",
        method="GET",
        path="/projects/:id/packages/rubygems/:file_name",
    ),
    # "Ruby gems API: Retrieve dependencies".
    RestOperation(
        operation_id="package#retrieve-dependencies",
        method="GET",
        path="/projects/:id/packages/rubygems/api/v1/dependencies",
        params=(Param(name="gems", location=Location.QUERY),),
    ),
    # "Ruby gems API: Upload a gem".
    RestOperation(
        operation_id="package#upload-a-gem",
        method="POST",
        path="/projects/:id/packages/rubygems/api/v1/gems",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Terraform Module Registry API: List available versions for a specific module".
    RestOperation(
        operation_id="package#list-available-versions-for-a-specific-module",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/versions",
    ),
    # "Terraform Module Registry API: Retrieve latest version for a module".
    RestOperation(
        operation_id="package#retrieve-latest-version-for-a-module",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system",
    ),
    # "Terraform Module Registry API: Retrieve a specific version for a module".
    RestOperation(
        operation_id="package#retrieve-a-specific-version-for-a-module",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/1.0.0",
    ),
    # "Terraform Module Registry API: Retrieve download URL for latest module version".
    RestOperation(
        operation_id="package#retrieve-download-url-for-latest-module-version",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/download",
    ),
    # "Terraform Module Registry API: Retrieve download URL for a specific module version".
    RestOperation(
        operation_id="package#retrieve-download-url-for-a-specific-module-version",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/:module_version/download",
    ),
    # "Terraform Module Registry API: From a namespace".
    RestOperation(
        operation_id="package#from-a-namespace",
        method="GET",
        path="/packages/terraform/modules/v1/:module_namespace/:module_name/:module_system/:module_version/file",
    ),
    # "Terraform Module Registry API: From a project".
    RestOperation(
        operation_id="package#from-a-project",
        method="GET",
        path="/projects/:id/packages/terraform/modules/:module_name/:module_system/:module_version",
        params=(Param(name="terraform-get", location=Location.QUERY),),
    ),
    # "Terraform Module Registry API: Upload module".
    RestOperation(
        operation_id="package#upload-module",
        method="PUT",
        path="/projects/:id/packages/terraform/modules/:module-name/:module-system/:module-version/file",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
    # "Virtual registries cleanup policies API: Retrieve the cleanup policy for a group".
    RestOperation(
        operation_id="package#retrieve-the-cleanup-policy-for-a-group",
        method="GET",
        path="/groups/:id/-/virtual_registries/cleanup/policy",
    ),
    # "Virtual registries cleanup policies API: Create a cleanup policy".
    RestOperation(
        operation_id="package#create-a-cleanup-policy",
        method="POST",
        path="/groups/:id/-/virtual_registries/cleanup/policy",
        params=(
            Param(name="cadence", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="keep_n_days_after_download", location=Location.BODY),
            Param(name="notify_on_success", location=Location.BODY),
            Param(name="notify_on_failure", location=Location.BODY),
        ),
    ),
    # "Virtual registries cleanup policies API: Update a cleanup policy".
    RestOperation(
        operation_id="package#update-a-cleanup-policy",
        method="PATCH",
        path="/groups/:id/-/virtual_registries/cleanup/policy",
        params=(
            Param(name="cadence", location=Location.BODY),
            Param(name="enabled", location=Location.BODY),
            Param(name="keep_n_days_after_download", location=Location.BODY),
            Param(name="notify_on_success", location=Location.BODY),
            Param(name="notify_on_failure", location=Location.BODY),
        ),
    ),
    # "Virtual registries cleanup policies API: Delete a cleanup policy".
    RestOperation(
        operation_id="package#delete-a-cleanup-policy",
        method="DELETE",
        path="/groups/:id/-/virtual_registries/cleanup/policy",
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset(
    {
        # "Container registry API: Change the visibility of the container registry": the project update, which can
        # also configure a pull mirror (AC-1.3).
        ("PUT", "/projects/:id/"),
    }
)
