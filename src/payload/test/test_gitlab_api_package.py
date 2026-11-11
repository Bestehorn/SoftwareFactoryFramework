"""Tests for ``gitlab_api/families/package.py``: the records of the package stage group, and the route-prefix,
hyphenated-name, glob and upload forms they declare (issue #43, design.md D5 to D7; AC-1.1 to AC-1.7, AC-2.1 to AC-2.3,
AC-2.5, AC-3.1 to AC-3.3, AC-4.1, AC-4.2 and AC-4.4), the container-registry calls of issue #63 (its design.md D4,
D8 and D9; #63 AC-1.1, AC-1.3, AC-5.2, AC-5.3, AC-8.3 and UB-2), and the record of the key #43 kept, refused (issue
#15 AC-1 to AC-3).

What is pinned:

- ``PENDING`` is empty; the records' operation IDs are every Reference of the index rows that link
  ``rest/package.md``, each key declared once, the only records on the registry's own host are its two keys', and the
  one record of ``/projects/:id/`` is "Change the visibility of the container registry"'s ``PUT`` (AC-1.1, AC-1.7,
  restated by #63 design.md D9 for #63 AC-1.1 and D8, and by issue #15 AC-1 and AC-2);
- "Change the visibility of the container registry", which writes into an existing project, is the record
  ``registry.lookup`` returns for its ID, and ``call`` refuses it: exit 2, no request, an ERROR record naming the ID
  and saying that no subcommand sends it (issue #15 AC-3);
- an entry listing two endpoints maps the one it lists first, then the other, which is on no ``PENDING`` (AC-1.2,
  restated by #63 design.md D9 for #63 D1 and D8);
- every ``Param`` is typed as its row: the ``Kind`` of its Type, ``required`` where Required reads ``yes``; the raw-body
  uploads declare their body's media type and send every ``Param`` in the query; every record has a JSON body and no
  ``fixed`` pairs (AC-1.4, AC-4.2); no ``Param`` names a path parameter, ``:module-name`` included (AC-1.5);
- the thirteen ``GET`` records whose entry has the ``page`` and ``per_page`` query rows are ``Paging.OFFSET`` and
  declare both rows, every other record is ``Paging.NONE`` (AC-1.6); each, called against two pages, the second asked
  for by ``x-next-page``, prints the items of both as one JSON array (AC-4.4);
- a prefix record of each prefix page holds its page's values and is sent under each of them, a ``:id`` of the value
  one encoded segment or the configured project (AC-2.1, AC-2.2, AC-2.3, AC-2.5);
- the hyphenated names of "Upload module" are sent as one segment each, and a glob record without a prefix is sent with
  its slashes, refused for a ``..`` part and for no value (AC-3.1, AC-3.2, AC-3.3);
- each ``--file`` upload sends the file as the part its attribute names, and each raw upload sends the ``--input``
  bytes, ``\\r\\n`` and ``\\xff`` included, unchanged as its body; a raw-body record refuses ``--file`` (AC-4.2);
- a container-registry record is sent as ``GET /user``, ``GET /projects/<project_id>``, the ``/jwt/auth`` request for
  its scope with ``Authorization: Basic`` of the login and the configured token as its only credential, then its own
  request to the registry of the project's ``container_registry_image_prefix`` with ``Authorization: Bearer`` of the
  registry token alone (#63 AC-5.2, UB-2); a registry token that cannot be obtained — a ``GET /user`` answer without a
  string ``username`` and a registry host holding ``?``, a backslash or white space among the ways — sends only the
  steps up to the failing one and nothing to the registry, and exits 1 (#63 AC-5.3); no log record holds the configured
  token, the Base64 of the login and the token, or the registry token, nor the body of a refused ``/jwt/auth`` answer.

Every expected ID, key, ``Kind``, required name, prefix value, paged ID, media type, URL and body is a literal table
transcribed from ``docs/api-reference/gitlab/operations-index.md`` and ``rest/package.md`` (the container-registry
URLs and answers from #63 design.md D4 and docs.gitlab.com ``container_registry``), never read from the records. The
names and ``In`` of every ``Param``, and one call of every record, are proven by
``test/test_gitlab_wrapper_contract.py``.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test; the fake serves the registry's origin as it serves the configured one.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_package.py`` (no network).
"""

from __future__ import annotations

import base64
import importlib
import importlib.util
import json
import logging
import sys
import urllib.parse
from collections import Counter
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_package_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.package"
REGISTRY = "registry"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CALL = "call"
REST_BASE = fixtures.REST_BASE

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_TOKEN_TYPE = "token_type"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-package-test"  # pragma: allowlist secret
TOKEN_TYPE_BEARER = "bearer"
PROJECT_ID = 4242

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_REFUSED = 2
STATUS_OK = 200
STATUS_CREATED = 201
STATUS_ACCEPTED = 202
STATUS_UNAUTHORIZED = 401
STATUS_NOT_FOUND = 404
TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "Content-Disposition"
HEADER_NEXT_PAGE = "x-next-page"
HEADER_SEPARATOR = ":"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
# RFC 7578 / RFC 2046 section 5.1.1: the boundary parameter, a part's name and filename, the delimiter's dashes.
PARAM_BOUNDARY = "boundary"
PARAM_NAME = "name"
PARAM_FILENAME = "filename"
CRLF = b"\r\n"
DASHES = b"--"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

METHOD_GET = "GET"
METHOD_PUT = "PUT"
METHOD_POST = "POST"
METHOD_DELETE = "DELETE"
# The options of `call` (#41 design.md D2; #40 design.md D5 `--input`; design.md D3 `--route-prefix`). `id` defaults
# to the configured project on a path starting `/projects/:id`, a routed one included (AC-2.3).
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "-f"
OPTION_FILE = "--file"
OPTION_INPUT = "--input"
OPTION_ROUTE_PREFIX = "--route-prefix"
ASSIGNED = "="
# Transport.pages: OFFSET adds `per_page=MAX_PER_PAGE` to the first request, and the next page's request sets `page` to
# the `x-next-page` value (#13 AC-2.5).
FIRST_PAGE_QUERY = "?per_page=100"
NEXT_PAGE = "2"
SECOND_PAGE_QUERY = f"?per_page=100&page={NEXT_PAGE}"
LAST_PAGE = ""
# The offset paging rows a paged record declares (conventions.md "Offset-based").
PAGING_ROWS: Tuple[str, ...] = ("page", "per_page")

# The `registry.Kind`, `registry.Paging` and `registry.Location` member names the tables hold.
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_FILE = "FILE"
PAGING_OFFSET = "OFFSET"
LOCATION_QUERY = "QUERY"

# AC-1.3, restated by #63 design.md D9 and issue #15 AC-1: the container registry's own host, whose keys only the two
# records of `REGISTRY_RECORDS` have (#63 AC-1.1, D8), and the project update, whose path only the record of
# `PROJECT_UPDATE_RECORDS` has.
REGISTRY_HOST_PREFIX = "/http(s)://"
PROJECT_UPDATE_PATH = "/projects/:id/"

# --- The tables, transcribed from the reference -----------------------------------------------------------------

# The record of the key #43 kept (its design.md D6 "The kept keys"; AC-1.3), "Change the visibility of the container
# registry" (Container registry API), by ID: the method and path of its index row (issue #15 AC-1). Its section's rows
# include a pull mirror's (`mirror`, `import_url`; #43 DL-006), so it writes into an existing project and `call` refuses
# it (issue #15 AC-3).
OP_CHANGE_REGISTRY_VISIBILITY = "package#change-the-visibility-of-the-container-registry"
PROJECT_UPDATE_RECORDS: Dict[str, Tuple[str, str]] = {OP_CHANGE_REGISTRY_VISIBILITY: ("PUT", "/projects/:id/")}

# The two records on the registry's own host (#63 AC-1.1, design.md D8), by ID: the method and path of their index rows.
OP_DELETE_IMAGE_TAGS = "package#delete-image-tags-by-reference"
OP_LIST_CONTAINER_REPOSITORIES = "package#listing-all-container-repositories"
REGISTRY_RECORDS: Dict[str, Tuple[str, str]] = {
    OP_DELETE_IMAGE_TAGS: (
        "DELETE",
        "/http(s)://${CI_REGISTRY}/v2/${CI_REGISTRY_IMAGE}/tags/reference/${CI_COMMIT_SHORT_SHA}",
    ),
    OP_LIST_CONTAINER_REPOSITORIES: ("GET", "/http(s)://${CI_REGISTRY}/v2/_catalog"),
}

# The Reference of every row of operations-index.md that links rest/package.md, written `package#<anchor>`, once each,
# in the page order of rest/package.md; restated by #63 design.md D9, "Delete image tags by reference" and "Listing all
# container repositories" included (#63 AC-1.1, D8), and by issue #15 AC-1, "Change the visibility of the container
# registry" included. A Conan v1 Reference, and NuGet "Upload a package file", carries two rows (AC-1.2), and #63
# declares a record for each (`RECORD_IDS`).
OPERATION_IDS: Tuple[str, ...] = (
    # Composer API
    "package#retrieve-repository-url-templates",
    "package#v1-packages-list",
    "package#retrieve-v1-package-metadata",
    "package#retrieve-v2-package-metadata",
    "package#create-a-package",
    "package#download-a-package-archive",
    # Conan v1 API
    "package#create-an-authentication-token",
    "package#verify-availability-of-a-conan-repository",
    "package#search-for-a-conan-package",
    "package#verify-authentication-credentials",
    "package#retrieve-a-recipe-snapshot",
    "package#retrieve-a-package-snapshot",
    "package#retrieve-a-recipe-manifest",
    "package#retrieve-a-package-manifest",
    "package#list-all-recipe-download-urls",
    "package#list-all-package-download-urls",
    "package#list-all-recipe-upload-urls",
    "package#list-all-package-upload-urls",
    "package#retrieve-a-recipe-file",
    "package#upload-a-recipe-file",
    "package#retrieve-a-package-file",
    "package#upload-a-package-file",
    "package#delete-a-recipe-and-package",
    "package#retrieve-package-references-metadata",
    # Conan v2 API
    "package#create-an-authentication-token-1",
    "package#verify-authentication-credentials-1",
    "package#search-for-a-conan-package-1",
    "package#retrieve-latest-recipe-revision",
    "package#list-all-recipe-revisions",
    "package#delete-a-recipe-revision",
    "package#list-all-recipe-files",
    "package#retrieve-a-recipe-file-1",
    "package#upload-a-recipe-file-1",
    "package#list-all-package-revisions",
    "package#retrieve-latest-package-revision",
    "package#delete-a-package-revision",
    "package#retrieve-a-package-file-1",
    "package#upload-a-package-file-1",
    "package#retrieve-package-references-metadata-1",
    "package#retrieve-package-references-metadata-by-recipe-revision",
    # Container registry API
    OP_CHANGE_REGISTRY_VISIBILITY,
    "package#within-a-project",
    "package#within-a-group",
    "package#retrieve-details-of-a-single-repository",
    "package#delete-registry-repository",
    "package#list-all-registry-repository-tags-in-a-project",
    "package#retrieve-details-of-a-registry-repository-tag",
    "package#delete-a-registry-repository-tag",
    "package#delete-registry-repository-tags-in-bulk",
    OP_DELETE_IMAGE_TAGS,
    OP_LIST_CONTAINER_REPOSITORIES,
    # Container registry protection tag rules API
    "package#list-container-registry-protection-tag-rules",
    "package#create-a-container-registry-protection-tag-rule",
    "package#update-a-container-registry-protection-tag-rule",
    "package#delete-a-container-registry-protection-tag-rule",
    # Container repository protection rules API
    "package#list-all-container-repository-protection-rules",
    "package#create-a-container-repository-protection-rule",
    "package#update-a-container-repository-protection-rule",
    "package#delete-a-container-repository-protection-rule",
    # Container virtual registry API
    "package#list-all-virtual-registries",
    "package#create-a-virtual-registry",
    "package#retrieve-a-virtual-registry",
    "package#update-a-virtual-registry",
    "package#delete-a-virtual-registry",
    "package#delete-cache-entries-for-a-virtual-registry",
    "package#list-all-upstream-registries-for-a-top-level-group",
    "package#test-connection-before-creating-an-upstream-registry",
    "package#list-all-upstream-registries-for-a-virtual-registry",
    "package#create-an-upstream-registry",
    "package#retrieve-an-upstream-registry",
    "package#update-an-upstream-registry",
    "package#update-an-upstream-registry-position",
    "package#delete-an-upstream-registry",
    "package#associate-an-upstream-with-a-registry",
    "package#disassociate-an-upstream-from-a-registry",
    "package#delete-cache-entries-for-an-upstream-registry",
    "package#test-connection-to-an-upstream-registry-with-override-parameters",
    "package#list-upstream-registry-cache-entries",
    "package#delete-an-upstream-registry-cache-entry",
    # Debian API
    "package#upload-a-package-file-2",
    "package#download-a-package",
    "package#download-a-distribution-release-file",
    "package#download-a-signed-distribution-release-file",
    "package#download-a-release-file-signature",
    "package#download-a-packages-index",
    "package#download-a-packages-index-by-hash",
    "package#download-a-debian-installer-packages-index",
    "package#download-a-debian-installer-packages-index-by-hash",
    "package#download-a-source-packages-index",
    "package#download-a-source-packages-index-by-hash",
    # Debian group distributions API
    "package#list-all-debian-distributions-in-a-group",
    "package#retrieve-a-debian-group-distribution",
    "package#retrieve-a-debian-group-distribution-key",
    "package#create-a-debian-group-distribution",
    "package#update-a-debian-group-distribution",
    "package#delete-a-debian-group-distribution",
    # Debian project distributions API
    "package#list-all-debian-distributions-in-a-project",
    "package#retrieve-a-debian-project-distribution",
    "package#retrieve-a-debian-project-distribution-key",
    "package#create-a-debian-project-distribution",
    "package#update-a-debian-project-distribution",
    "package#delete-a-debian-project-distribution",
    # Dependency Proxy API
    "package#purge-the-dependency-proxy-for-a-group",
    # Go Proxy API
    "package#list",
    "package#version-metadata",
    "package#download-module-file",
    "package#download-module-source",
    # Helm API
    "package#download-a-chart-index",
    "package#download-a-chart",
    "package#upload-a-chart",
    # Maven API
    "package#download-a-package-file-for-an-instance",
    "package#download-a-package-file-for-a-group",
    "package#download-a-package-file-for-a-project",
    "package#upload-a-package-file-3",
    # Maven virtual registry API
    "package#list-all-virtual-registries-1",
    "package#create-a-virtual-registry-1",
    "package#retrieve-a-virtual-registry-1",
    "package#update-a-virtual-registry-1",
    "package#delete-a-virtual-registry-1",
    "package#delete-cache-entries-for-a-virtual-registry-1",
    "package#list-all-upstream-registries",
    "package#test-upstream-registry-connection-before-creation",
    "package#list-all-upstream-registries-for-a-virtual-registry-1",
    "package#create-an-upstream-registry-1",
    "package#create-a-local-upstream-registry",
    "package#retrieve-a-local-upstream-registry",
    "package#update-a-local-upstream-registry",
    "package#delete-a-local-upstream-registry",
    "package#retrieve-an-upstream-registry-1",
    "package#update-an-upstream-registry-1",
    "package#update-an-upstream-registry-position-1",
    "package#delete-an-upstream-registry-1",
    "package#associate-an-upstream-registry-with-a-virtual-registry",
    "package#disassociate-an-upstream-registry-from-a-virtual-registry",
    "package#delete-cache-entries-for-an-upstream-registry-1",
    "package#test-upstream-registry-connection",
    "package#test-upstream-registry-connection-with-override-parameters",
    "package#list-all-upstream-registry-cache-entries",
    "package#delete-an-upstream-registry-cache-entry-1",
    "package#download-a-package-1",
    "package#upload-a-package",
    # npm API
    "package#download-a-package-2",
    "package#upload-a-package-file-4",
    "package#retrieve-package-metadata",
    "package#list-all-dist-tags",
    "package#create-or-update-a-dist-tag",
    "package#delete-a-dist-tag",
    # NuGet API
    "package#retrieve-a-package-index",
    "package#download-a-package-file",
    "package#upload-a-package-file-5",
    "package#upload-a-symbol-package-file",
    "package#v2-source-feedprotocol",
    "package#v3-source-feedprotocol",
    "package#retrieve-package-metadata-1",
    "package#retrieve-version-metadata",
    "package#search-for-packages",
    "package#delete-a-package",
    "package#download-a-debugging-symbol-file-pdb",
    "package#metadata-endpoint",
    # Packages API
    "package#for-a-project",
    "package#for-a-group",
    "package#retrieve-a-project-package",
    "package#list-package-files",
    "package#list-package-pipelines",
    "package#delete-a-project-package",
    "package#delete-a-package-file",
    # Protected packages API
    "package#list-all-package-protection-rules",
    "package#create-a-package-protection-rule",
    "package#update-a-package-protection-rule",
    "package#delete-a-package-protection-rule",
    # PyPI API
    "package#download-a-package-file-for-a-group-1",
    "package#list-all-packages-for-a-group",
    "package#retrieve-package-descriptor-for-a-group",
    "package#download-a-package-file-for-a-project-1",
    "package#list-all-packages-for-a-project",
    "package#retrieve-package-descriptor-for-a-project",
    "package#upload-a-package-1",
    # Ruby gems API
    "package#download-a-gem-file",
    "package#download-a-gemspec-file",
    "package#download-a-spec-index-file",
    "package#retrieve-dependencies",
    "package#upload-a-gem",
    # Terraform Module Registry API
    "package#list-available-versions-for-a-specific-module",
    "package#retrieve-latest-version-for-a-module",
    "package#retrieve-a-specific-version-for-a-module",
    "package#retrieve-download-url-for-latest-module-version",
    "package#retrieve-download-url-for-a-specific-module-version",
    "package#from-a-namespace",
    "package#from-a-project",
    "package#upload-module",
    # Virtual registries cleanup policies API
    "package#retrieve-the-cleanup-policy-for-a-group",
    "package#create-a-cleanup-policy",
    "package#update-a-cleanup-policy",
    "package#delete-a-cleanup-policy",
)

# The records the calls name.
OP_LIST_DIST_TAGS = "package#list-all-dist-tags"  # GET /<route-prefix>/-/package/:package_name/dist-tags
OP_DEBIAN_RELEASE_FILE = (
    "package#download-a-distribution-release-file"  # GET /<route-prefix>/dists/*distribution/Release
)
OP_NUGET_SEARCH = "package#search-for-packages"  # GET /<route-prefix>/query
OP_UPLOAD_MODULE = "package#upload-module"
OP_MAVEN_PROJECT_DOWNLOAD = (
    "package#download-a-package-file-for-a-project"  # GET /projects/:id/packages/maven/*path/:file_name
)
OP_CONAN_V1_UPLOAD_RECIPE_FILE = "package#upload-a-recipe-file"
OP_CONAN_V1_UPLOAD_PACKAGE_FILE = "package#upload-a-package-file"
OP_CONAN_V2_UPLOAD_RECIPE_FILE = "package#upload-a-recipe-file-1"
OP_CONAN_V2_UPLOAD_PACKAGE_FILE = "package#upload-a-package-file-1"
OP_DEBIAN_UPLOAD = "package#upload-a-package-file-2"
OP_MAVEN_UPLOAD = "package#upload-a-package-file-3"
OP_NPM_UPLOAD = "package#upload-a-package-file-4"
OP_NUGET_UPLOAD = "package#upload-a-package-file-5"
OP_NPM_DIST_TAG = "package#create-or-update-a-dist-tag"
OP_GEM_UPLOAD = "package#upload-a-gem"
OP_NUGET_SYMBOL_UPLOAD = "package#upload-a-symbol-package-file"
OP_PYPI_UPLOAD = "package#upload-a-package-1"
OP_HELM_UPLOAD = "package#upload-a-chart"
OP_MAVEN_VIRTUAL_UPLOAD = "package#upload-a-package"


class TwoEndpoints(NamedTuple):
    """The two endpoints an entry lists, as ``(method, path)`` keys: the ``first``, which its base record maps (AC-1.2),
    and the ``other``, which #63 maps with a record after it (#63 design.md D1, D8)."""

    first: Tuple[str, str]
    other: Tuple[str, str]


# AC-1.2: every Conan v1 entry, and NuGet "Upload a package file", with the endpoints its heading lists, in its order.
FIRST_ENDPOINTS: Dict[str, TwoEndpoints] = {
    "package#create-an-authentication-token": TwoEndpoints(
        first=("GET", "/packages/conan/v1/users/authenticate"),
        other=("GET", "/projects/:id/packages/conan/v1/users/authenticate"),
    ),
    "package#verify-availability-of-a-conan-repository": TwoEndpoints(
        first=("GET", "/packages/conan/v1/ping"),
        other=("GET", "/projects/:id/packages/conan/v1/ping"),
    ),
    "package#search-for-a-conan-package": TwoEndpoints(
        first=("GET", "/packages/conan/v1/conans/search"),
        other=("GET", "/projects/:id/packages/conan/v1/conans/search"),
    ),
    "package#verify-authentication-credentials": TwoEndpoints(
        first=("GET", "/packages/conan/v1/users/check_credentials"),
        other=("GET", "/projects/:id/packages/conan/v1/users/check_credentials"),
    ),
    "package#retrieve-a-recipe-snapshot": TwoEndpoints(
        first=("GET", "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel"),
        other=("GET", "/projects/:id/packages/conan/v1/conans/:package_version/:package_username/:package_channel"),
    ),
    "package#retrieve-a-package-snapshot": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference",
        ),
    ),
    "package#retrieve-a-recipe-manifest": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/digest",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/digest",
        ),
    ),
    "package#retrieve-a-package-manifest": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/digest",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/digest",
        ),
    ),
    "package#list-all-recipe-download-urls": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/download_urls",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/download_urls",
        ),
    ),
    "package#list-all-package-download-urls": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/download_urls",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/download_urls",
        ),
    ),
    "package#list-all-recipe-upload-urls": TwoEndpoints(
        first=(
            "POST",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/upload_urls",
        ),
        other=(
            "POST",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/upload_urls",
        ),
    ),
    "package#list-all-package-upload-urls": TwoEndpoints(
        first=(
            "POST",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/upload_urls",
        ),
        other=(
            "POST",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/packages/:conan_package_reference/upload_urls",
        ),
    ),
    "package#retrieve-a-recipe-file": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        ),
    ),
    "package#upload-a-recipe-file": TwoEndpoints(
        first=(
            "PUT",
            "/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        ),
        other=(
            "PUT",
            "/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/export/:file_name",
        ),
    ),
    "package#retrieve-a-package-file": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        ),
    ),
    "package#upload-a-package-file": TwoEndpoints(
        first=(
            "PUT",
            "/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        ),
        other=(
            "PUT",
            "/projects/:id/packages/conan/v1/files/:package_name/:package_version/:package_username/:package_channel/:recipe_revision/package/:conan_package_reference/:package_revision/:file_name",
        ),
    ),
    "package#delete-a-recipe-and-package": TwoEndpoints(
        first=("DELETE", "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel"),
        other=(
            "DELETE",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel",
        ),
    ),
    "package#retrieve-package-references-metadata": TwoEndpoints(
        first=(
            "GET",
            "/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/search",
        ),
        other=(
            "GET",
            "/projects/:id/packages/conan/v1/conans/:package_name/:package_version/:package_username/:package_channel/search",
        ),
    ),
    OP_NUGET_UPLOAD: TwoEndpoints(
        first=("PUT", "/projects/:id/packages/nuget"),
        other=("PUT", "/projects/:id/packages/nuget/v2"),
    ),
}

# The ID of every record, once per record (#63 design.md D9: "each key once"): a two-endpoint entry's ID twice, for its
# base record and the record of its other endpoint (#63 D1, D8), every other ID once.
RECORD_IDS: Tuple[str, ...] = (*OPERATION_IDS, *FIRST_ENDPOINTS)

# Every `Param` whose Kind is not SCALAR, by record: the `query` and `body` rows typed `array of string` or `string
# array` (ARRAY) — `components` and `architectures` of the Debian distribution list, create, update and delete entries
# — and the `form` rows typed `file` (FILE) of the `--file` uploads (design.md D5). A raw-body record's `file` row is
# its body, no Param (design.md D6). The page's one `object` row (HASH) and its other `array of string` and `file`
# rows are those of "Change the visibility of the container registry" (issue #15 AC-1). Every other row is `string`,
# `integer`, `integer (int32)` or `boolean`, a SCALAR.
DEBIAN_DISTRIBUTION_ARRAYS: Dict[str, str] = {"components": KIND_ARRAY, "architectures": KIND_ARRAY}
KINDS: Dict[str, Dict[str, str]] = {
    OP_CHANGE_REGISTRY_VISIBILITY: {
        "container_expiration_policy_attributes": KIND_HASH,
        "tag_list": KIND_ARRAY,
        "topics": KIND_ARRAY,
        "avatar": KIND_FILE,
        "ci_id_token_sub_claim_components": KIND_ARRAY,
    },
    "package#list-all-debian-distributions-in-a-group": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#create-a-debian-group-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#update-a-debian-group-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#delete-a-debian-group-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#list-all-debian-distributions-in-a-project": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#create-a-debian-project-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#update-a-debian-project-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    "package#delete-a-debian-project-distribution": DEBIAN_DISTRIBUTION_ARRAYS,
    OP_HELM_UPLOAD: {"chart": KIND_FILE},
    OP_MAVEN_VIRTUAL_UPLOAD: {"file": KIND_FILE},
    OP_NUGET_UPLOAD: {"package": KIND_FILE},
    OP_NUGET_SYMBOL_UPLOAD: {"package": KIND_FILE},
    OP_PYPI_UPLOAD: {"content": KIND_FILE},
}

# The `query`, `body` and `form` rows whose Required reads `yes`, by record, in table order. A record with none is not
# listed. No `Param`, so never required (design.md D6): a `path` row (the Conan v1 `id` reads `conditional`); a row
# naming a path parameter of the record's path ("Upload module"'s `module-name`, `module-system`, `module-version`); a
# raw-body record's `file` row. `conditional` is not `yes` ("Create a local upstream registry").
REQUIRED: Dict[str, Tuple[str, ...]] = {
    "package#download-a-package-archive": ("sha",),
    "package#search-for-a-conan-package": ("q",),
    "package#search-for-a-conan-package-1": ("query", "q"),
    "package#delete-a-recipe-revision": ("package_version",),
    "package#delete-registry-repository-tags-in-bulk": ("name_regex_delete",),
    "package#create-a-container-registry-protection-tag-rule": (
        "tag_name_pattern",
        "minimum_access_level_for_push",
        "minimum_access_level_for_delete",
    ),
    "package#create-a-container-repository-protection-rule": ("repository_path_pattern",),
    "package#create-a-virtual-registry": ("name",),
    "package#test-connection-before-creating-an-upstream-registry": ("url",),
    "package#create-an-upstream-registry": ("url", "name"),
    "package#update-an-upstream-registry-position": ("position",),
    "package#associate-an-upstream-with-a-registry": ("registry_id", "upstream_id"),
    "package#create-a-debian-group-distribution": ("codename",),
    "package#create-a-debian-project-distribution": ("codename",),
    OP_HELM_UPLOAD: ("chart",),
    "package#create-a-virtual-registry-1": ("name",),
    "package#update-a-virtual-registry-1": ("name",),
    "package#test-upstream-registry-connection-before-creation": ("url",),
    "package#create-an-upstream-registry-1": ("url",),
    "package#create-a-local-upstream-registry": ("name",),
    "package#update-an-upstream-registry-position-1": ("position",),
    "package#associate-an-upstream-registry-with-a-virtual-registry": (
        "registry_id",
        "upstream_id",
        "local_upstream_id",
    ),
    OP_MAVEN_VIRTUAL_UPLOAD: ("file",),
    OP_NPM_UPLOAD: ("versions",),
    OP_NPM_DIST_TAG: ("version",),
    OP_NUGET_UPLOAD: ("package_name", "package_version", "package_filename", "package"),
    OP_NUGET_SYMBOL_UPLOAD: ("package_name", "package_version", "package_filename", "package"),
    OP_NUGET_SEARCH: ("q",),
    "package#download-a-debugging-symbol-file-pdb": ("Symbolchecksum",),
    "package#create-a-package-protection-rule": (
        "package_name_pattern",
        "package_type",
        "minimum_access_level_for_delete",
        "minimum_access_level_for_push",
    ),
    OP_PYPI_UPLOAD: ("content", "name", "version"),
}

# The raw-body records and the media type of their body (design.md D5): each upload whose Workhorse route is
# `requestBodyUploader`, and npm "Create or update a dist-tag", whose body Rails reads whole; npm's two are JSON.
RAW_BODIES: Dict[str, str] = {
    OP_CONAN_V1_UPLOAD_RECIPE_FILE: CONTENT_TYPE_OCTET_STREAM,
    OP_CONAN_V1_UPLOAD_PACKAGE_FILE: CONTENT_TYPE_OCTET_STREAM,
    OP_CONAN_V2_UPLOAD_RECIPE_FILE: CONTENT_TYPE_OCTET_STREAM,
    OP_CONAN_V2_UPLOAD_PACKAGE_FILE: CONTENT_TYPE_OCTET_STREAM,
    OP_DEBIAN_UPLOAD: CONTENT_TYPE_OCTET_STREAM,
    OP_MAVEN_UPLOAD: CONTENT_TYPE_OCTET_STREAM,
    OP_NPM_UPLOAD: CONTENT_TYPE_JSON,
    OP_NPM_DIST_TAG: CONTENT_TYPE_JSON,
    OP_GEM_UPLOAD: CONTENT_TYPE_OCTET_STREAM,
    OP_UPLOAD_MODULE: CONTENT_TYPE_OCTET_STREAM,
}

# The `GET` records whose entry has the `query` rows `page` and `per_page` (design.md D6 "The paged records").
OP_WITHIN_A_PROJECT = "package#within-a-project"
OP_WITHIN_A_GROUP = "package#within-a-group"
OP_LIST_REPOSITORY_TAGS = "package#list-all-registry-repository-tags-in-a-project"
OP_LIST_CONTAINER_GROUP_UPSTREAMS = "package#list-all-upstream-registries-for-a-top-level-group"
OP_LIST_CONTAINER_CACHE_ENTRIES = "package#list-upstream-registry-cache-entries"
OP_LIST_GROUP_DEBIAN_DISTRIBUTIONS = "package#list-all-debian-distributions-in-a-group"
OP_LIST_PROJECT_DEBIAN_DISTRIBUTIONS = "package#list-all-debian-distributions-in-a-project"
OP_LIST_MAVEN_GROUP_UPSTREAMS = "package#list-all-upstream-registries"
OP_LIST_MAVEN_CACHE_ENTRIES = "package#list-all-upstream-registry-cache-entries"
OP_FOR_A_PROJECT = "package#for-a-project"
OP_FOR_A_GROUP = "package#for-a-group"
OP_LIST_PACKAGE_FILES = "package#list-package-files"
OP_LIST_PACKAGE_PIPELINES = "package#list-package-pipelines"
PAGED_RECORDS: Dict[str, str] = {
    OP_WITHIN_A_PROJECT: PAGING_OFFSET,
    OP_WITHIN_A_GROUP: PAGING_OFFSET,
    OP_LIST_REPOSITORY_TAGS: PAGING_OFFSET,
    OP_LIST_CONTAINER_GROUP_UPSTREAMS: PAGING_OFFSET,
    OP_LIST_CONTAINER_CACHE_ENTRIES: PAGING_OFFSET,
    OP_LIST_GROUP_DEBIAN_DISTRIBUTIONS: PAGING_OFFSET,
    OP_LIST_PROJECT_DEBIAN_DISTRIBUTIONS: PAGING_OFFSET,
    OP_LIST_MAVEN_GROUP_UPSTREAMS: PAGING_OFFSET,
    OP_LIST_MAVEN_CACHE_ENTRIES: PAGING_OFFSET,
    OP_FOR_A_PROJECT: PAGING_OFFSET,
    OP_FOR_A_GROUP: PAGING_OFFSET,
    OP_LIST_PACKAGE_FILES: PAGING_OFFSET,
    OP_LIST_PACKAGE_PIPELINES: PAGING_OFFSET,
}

# The values of each page's `<route-prefix>` line, verbatim and in line order (rest/package.md "Debian API", "npm
# API", "NuGet API"; AC-2.1).
DEBIAN_ROUTE_PREFIXES: Tuple[str, ...] = ("/projects/:id/packages/debian", "/groups/:id/-/packages/debian")
NPM_ROUTE_PREFIXES: Tuple[str, ...] = ("/packages/npm", "/projects/:id/packages/npm", "/groups/:id/-/packages/npm")
NUGET_ROUTE_PREFIXES: Tuple[str, ...] = ("/groups/:id/-/packages/nuget", "/projects/:id/packages/nuget")

# --- The calls ----------------------------------------------------------------------------------------------------

# Response keys of an answer the fake host serves.
FIELD_ID = "id"
FIELD_MESSAGE = "message"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})
ANSWER: Dict[str, Any] = {FIELD_ID: 1}
UPLOAD_ANSWER: Dict[str, Any] = {FIELD_MESSAGE: "201 Created"}


class ListCase(NamedTuple):
    """A call of a paged record and the URL of its list before the query, which each page request extends."""

    argv: Tuple[str, ...]
    url: str


# AC-4.4: every paged record of D6, its path values given (`id` the configured project on a `/projects/:id` path).
LIST_CASES = (
    pytest.param(
        ListCase(argv=(OP_WITHIN_A_PROJECT,), url=f"{REST_BASE}/projects/{PROJECT_ID}/registry/repositories"),
        id="within-a-project",
    ),
    pytest.param(
        ListCase(argv=(OP_WITHIN_A_GROUP, OPTION_PATH, "id=12"), url=f"{REST_BASE}/groups/12/registry/repositories"),
        id="within-a-group",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_REPOSITORY_TAGS, OPTION_PATH, "repository_id=3"),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/registry/repositories/3/tags",
        ),
        id="list-all-registry-repository-tags-in-a-project",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_CONTAINER_GROUP_UPSTREAMS, OPTION_PATH, "id=12"),
            url=f"{REST_BASE}/groups/12/-/virtual_registries/container/upstreams",
        ),
        id="list-all-upstream-registries-for-a-top-level-group",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_CONTAINER_CACHE_ENTRIES, OPTION_PATH, "id=6"),
            url=f"{REST_BASE}/virtual_registries/container/upstreams/6/cache_entries",
        ),
        id="list-upstream-registry-cache-entries",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_GROUP_DEBIAN_DISTRIBUTIONS, OPTION_PATH, "id=12"),
            url=f"{REST_BASE}/groups/12/-/debian_distributions",
        ),
        id="list-all-debian-distributions-in-a-group",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_PROJECT_DEBIAN_DISTRIBUTIONS,), url=f"{REST_BASE}/projects/{PROJECT_ID}/debian_distributions"
        ),
        id="list-all-debian-distributions-in-a-project",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_MAVEN_GROUP_UPSTREAMS, OPTION_PATH, "id=12"),
            url=f"{REST_BASE}/groups/12/-/virtual_registries/packages/maven/upstreams",
        ),
        id="list-all-upstream-registries",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_MAVEN_CACHE_ENTRIES, OPTION_PATH, "id=6"),
            url=f"{REST_BASE}/virtual_registries/packages/maven/upstreams/6/cache_entries",
        ),
        id="list-all-upstream-registry-cache-entries",
    ),
    pytest.param(
        ListCase(argv=(OP_FOR_A_PROJECT,), url=f"{REST_BASE}/projects/{PROJECT_ID}/packages"),
        id="for-a-project",
    ),
    pytest.param(
        ListCase(argv=(OP_FOR_A_GROUP, OPTION_PATH, "id=12"), url=f"{REST_BASE}/groups/12/packages"),
        id="for-a-group",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_PACKAGE_FILES, OPTION_PATH, "package_id=9"),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/9/package_files",
        ),
        id="list-package-files",
    ),
    pytest.param(
        ListCase(
            argv=(OP_LIST_PACKAGE_PIPELINES, OPTION_PATH, "package_id=9"),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/9/pipelines",
        ),
        id="list-package-pipelines",
    ),
)


class PrefixCase(NamedTuple):
    """A call of a prefix record under one of its page's values: the record, the arguments after its ID, the one
    request it sends (its method and URL, the query included), and the values of the record's page."""

    operation_id: str
    arguments: Tuple[str, ...]
    method: str
    url: str
    route_prefixes: Tuple[str, ...]


# AC-2.2, AC-2.3, AC-2.5 (design.md Correctness Properties, the AC-2.2 table): one row per prefix value of one record of
# each prefix page. A `:id` of the value is a path parameter of the call; under a `/projects/:id` value a call with no
# `id` sends the configured project.
DIST_TAGS_PATH: Tuple[str, ...] = (OPTION_PATH, "package_name=pkg")
RELEASE_FILE_PATH: Tuple[str, ...] = (OPTION_PATH, "distribution=stable")
SEARCH_QUERY: Tuple[str, ...] = (OPTION_QUERY, "q=pkg")
PREFIX_CASES = (
    pytest.param(
        PrefixCase(
            operation_id=OP_LIST_DIST_TAGS,
            arguments=(*DIST_TAGS_PATH, OPTION_ROUTE_PREFIX, "/packages/npm"),
            method=METHOD_GET,
            url=f"{REST_BASE}/packages/npm/-/package/pkg/dist-tags",
            route_prefixes=NPM_ROUTE_PREFIXES,
        ),
        id="npm-instance",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_LIST_DIST_TAGS,
            arguments=(*DIST_TAGS_PATH, OPTION_ROUTE_PREFIX, "/groups/:id/-/packages/npm", OPTION_PATH, "id=7"),
            method=METHOD_GET,
            url=f"{REST_BASE}/groups/7/-/packages/npm/-/package/pkg/dist-tags",
            route_prefixes=NPM_ROUTE_PREFIXES,
        ),
        id="npm-group",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_LIST_DIST_TAGS,
            arguments=(
                *DIST_TAGS_PATH,
                OPTION_ROUTE_PREFIX,
                "/groups/:id/-/packages/npm",
                OPTION_PATH,
                "id=my-group/sub",
            ),
            method=METHOD_GET,
            url=f"{REST_BASE}/groups/my-group%2Fsub/-/packages/npm/-/package/pkg/dist-tags",
            route_prefixes=NPM_ROUTE_PREFIXES,
        ),
        id="npm-group-full-path-one-encoded-segment",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_LIST_DIST_TAGS,
            arguments=(*DIST_TAGS_PATH, OPTION_ROUTE_PREFIX, "/projects/:id/packages/npm"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/npm/-/package/pkg/dist-tags",
            route_prefixes=NPM_ROUTE_PREFIXES,
        ),
        id="npm-project-the-configured-project",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_DEBIAN_RELEASE_FILE,
            arguments=(*RELEASE_FILE_PATH, OPTION_ROUTE_PREFIX, "/projects/:id/packages/debian"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/debian/dists/stable/Release",
            route_prefixes=DEBIAN_ROUTE_PREFIXES,
        ),
        id="debian-project-the-configured-project",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_DEBIAN_RELEASE_FILE,
            arguments=(*RELEASE_FILE_PATH, OPTION_ROUTE_PREFIX, "/groups/:id/-/packages/debian", OPTION_PATH, "id=7"),
            method=METHOD_GET,
            url=f"{REST_BASE}/groups/7/-/packages/debian/dists/stable/Release",
            route_prefixes=DEBIAN_ROUTE_PREFIXES,
        ),
        id="debian-group",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_NUGET_SEARCH,
            arguments=(*SEARCH_QUERY, OPTION_ROUTE_PREFIX, "/groups/:id/-/packages/nuget", OPTION_PATH, "id=7"),
            method=METHOD_GET,
            url=f"{REST_BASE}/groups/7/-/packages/nuget/query?q=pkg",
            route_prefixes=NUGET_ROUTE_PREFIXES,
        ),
        id="nuget-group",
    ),
    pytest.param(
        PrefixCase(
            operation_id=OP_NUGET_SEARCH,
            arguments=(*SEARCH_QUERY, OPTION_ROUTE_PREFIX, "/projects/:id/packages/nuget"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/nuget/query?q=pkg",
            route_prefixes=NUGET_ROUTE_PREFIXES,
        ),
        id="nuget-project-the-configured-project",
    ),
)

# AC-3.1: "Upload module" with its three hyphenated names, `id` the configured project.
UPLOAD_MODULE_PATH: Tuple[str, ...] = (
    OPTION_PATH,
    "module-name=infra",
    OPTION_PATH,
    "module-system=aws",
    OPTION_PATH,
    "module-version=1.0.0",
)
UPLOAD_MODULE_URL = f"{REST_BASE}/projects/{PROJECT_ID}/packages/terraform/modules/infra/aws/1.0.0/file"


class GlobCase(NamedTuple):
    """A call of the Maven project download, a glob record with no prefix: the arguments after its ID, the exit code,
    the requests it sends, and a text one ERROR record holds (``None`` for a call that is sent)."""

    arguments: Tuple[str, ...]
    code: int
    sent: Tuple[Tuple[str, str], ...]
    logged: Optional[str]


# AC-3.2 (#40 AC-2.1, AC-2.2, AC-2.4): the glob written with its `/`, a `..` part refused by `registry.expand` (exit 1),
# and the glob left without a value refused by `check_parameters` (exit 2), each refusal with no request.
MAVEN_FILE_NAME_PATH: Tuple[str, ...] = (OPTION_PATH, "file_name=app-1.0.jar")
MAVEN_GLOB_PATH: Tuple[str, ...] = (OPTION_PATH, "path=com/example/app/1.0")
MAVEN_PROJECT_FILE_URL = f"{REST_BASE}/projects/{PROJECT_ID}/packages/maven/com/example/app/1.0/app-1.0.jar"
GLOB_CASES = (
    pytest.param(
        GlobCase(
            arguments=(*MAVEN_GLOB_PATH, *MAVEN_FILE_NAME_PATH),
            code=EXIT_OK,
            sent=((METHOD_GET, MAVEN_PROJECT_FILE_URL),),
            logged=None,
        ),
        id="glob-holding-slashes",
    ),
    pytest.param(
        GlobCase(
            arguments=(OPTION_PATH, "path=com/../app", *MAVEN_FILE_NAME_PATH),
            code=EXIT_API_ERROR,
            sent=(),
            logged="*path",
        ),
        id="glob-part-dot-dot-refused",
    ),
    pytest.param(
        GlobCase(
            arguments=MAVEN_FILE_NAME_PATH,
            code=EXIT_REFUSED,
            sent=(),
            logged="the path parameter path has no value",
        ),
        id="glob-without-a-value-refused",
    ),
)

# AC-4.2: bytes a text-layer read would translate (`\r\n`) or fail to decode (`\xff`).
UPLOAD_BYTES = b"PK\x03\x04 first line\r\nsecond line\n\xff\xfe\x00 last"
UPLOAD_FILE_NAME = "upload.bin"


class UploadCase(NamedTuple):
    """A ``--file`` upload (design.md D5): the record, its path arguments, the ``FILE`` attribute and the name of the
    file given for it, each required body attribute given with ``-f``, and the one request it sends."""

    operation_id: str
    arguments: Tuple[str, ...]
    attribute: str
    file_name: str
    fields: Tuple[Tuple[str, str], ...]
    method: str
    url: str


# AC-4.2: D5's `--file` records, each given its path values, its file and every required body attribute.
UPLOAD_CASES = (
    pytest.param(
        UploadCase(
            operation_id=OP_NUGET_UPLOAD,
            arguments=(),
            attribute="package",
            file_name="mypackage.1.0.0.nupkg",
            fields=(
                ("package_name", "MyPackage"),
                ("package_version", "1.0.0"),
                ("package_filename", "mypackage.1.0.0.nupkg"),
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/nuget",
        ),
        id="upload-a-package-file-5",
    ),
    pytest.param(
        UploadCase(
            operation_id=OP_NUGET_SYMBOL_UPLOAD,
            arguments=(),
            attribute="package",
            file_name="mypackage.1.0.0.snupkg",
            fields=(
                ("package_name", "MyPackage"),
                ("package_version", "1.0.0"),
                ("package_filename", "mypackage.1.0.0.snupkg"),
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/nuget/symbolpackage",
        ),
        id="upload-a-symbol-package-file",
    ),
    pytest.param(
        UploadCase(
            operation_id=OP_PYPI_UPLOAD,
            arguments=(),
            attribute="content",
            file_name="mypkg-1.0.0.tar.gz",
            fields=(("name", "mypkg"), ("version", "1.0.0")),
            method=METHOD_POST,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/pypi",
        ),
        id="upload-a-package-1",
    ),
    pytest.param(
        UploadCase(
            operation_id=OP_HELM_UPLOAD,
            arguments=(OPTION_PATH, "channel=stable"),
            attribute="chart",
            file_name="mychart-0.1.0.tgz",
            fields=(),
            method=METHOD_POST,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/helm/api/stable/charts",
        ),
        id="upload-a-chart",
    ),
    pytest.param(
        UploadCase(
            operation_id=OP_MAVEN_VIRTUAL_UPLOAD,
            arguments=(OPTION_PATH, "id=5", OPTION_PATH, "path=foo/bar/mypkg/1.0/mypkg-1.0.jar"),
            attribute="file",
            file_name="mypkg-1.0.jar",
            fields=(),
            method=METHOD_POST,
            url=f"{REST_BASE}/virtual_registries/packages/maven/5/foo/bar/mypkg/1.0/mypkg-1.0.jar/upload",
        ),
        id="upload-a-package",
    ),
)


class RawUploadCase(NamedTuple):
    """A raw-body upload (design.md D5): the record, the arguments after its ID but ``--input``, the one request it
    sends (its method and URL, the query included), its body's media type, and the ``FILE`` attribute whose
    ``--file``, given in place of ``--input``, the record refuses (``None``: not called so)."""

    operation_id: str
    arguments: Tuple[str, ...]
    method: str
    url: str
    content_type: str
    refused_file: Optional[str] = None


# AC-4.2: D5's raw-body records, each given its path values; Debian's upload also its two query attributes, the npm
# dist-tag its route prefix. A Conan path is written with every value one segment.
CONAN_RECIPE_PATH: Tuple[str, ...] = (
    OPTION_PATH,
    "package_name=pkg",
    OPTION_PATH,
    "package_version=1.0",
    OPTION_PATH,
    "package_username=user",
    OPTION_PATH,
    "package_channel=stable",
    OPTION_PATH,
    "recipe_revision=0",
)
CONAN_RECIPE_FILE: Tuple[str, ...] = (OPTION_PATH, "file_name=conanfile.py")
CONAN_PACKAGE_FILE: Tuple[str, ...] = (
    OPTION_PATH,
    "conan_package_reference=ref",
    OPTION_PATH,
    "package_revision=0",
    OPTION_PATH,
    "file_name=conan_package.tgz",
)
RAW_UPLOAD_CASES = (
    pytest.param(
        RawUploadCase(
            operation_id=OP_CONAN_V1_UPLOAD_RECIPE_FILE,
            arguments=(*CONAN_RECIPE_PATH, *CONAN_RECIPE_FILE),
            method=METHOD_PUT,
            url=f"{REST_BASE}/packages/conan/v1/files/pkg/1.0/user/stable/0/export/conanfile.py",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-recipe-file",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_CONAN_V1_UPLOAD_PACKAGE_FILE,
            arguments=(*CONAN_RECIPE_PATH, *CONAN_PACKAGE_FILE),
            method=METHOD_PUT,
            url=f"{REST_BASE}/packages/conan/v1/files/pkg/1.0/user/stable/0/package/ref/0/conan_package.tgz",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-package-file",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_CONAN_V2_UPLOAD_RECIPE_FILE,
            arguments=(*CONAN_RECIPE_PATH, *CONAN_RECIPE_FILE),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/conan/v2/conans/pkg/1.0/user/stable/revisions/0/files/conanfile.py",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-recipe-file-1",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_CONAN_V2_UPLOAD_PACKAGE_FILE,
            arguments=(*CONAN_RECIPE_PATH, *CONAN_PACKAGE_FILE),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/conan/v2/conans/pkg/1.0/user/stable/revisions/0/packages/ref/revisions/0/files/conan_package.tgz",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-package-file-1",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_DEBIAN_UPLOAD,
            arguments=(
                OPTION_PATH,
                "file_name=mypkg.deb",
                OPTION_QUERY,
                "distribution=sid",
                OPTION_QUERY,
                "component=main",
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/debian/mypkg.deb?distribution=sid&component=main",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-package-file-2",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_MAVEN_UPLOAD,
            arguments=(*MAVEN_GLOB_PATH, *MAVEN_FILE_NAME_PATH),
            method=METHOD_PUT,
            url=MAVEN_PROJECT_FILE_URL,
            content_type=CONTENT_TYPE_OCTET_STREAM,
            refused_file="file",
        ),
        id="upload-a-package-file-3",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_NPM_UPLOAD,
            arguments=(OPTION_PATH, "package_name=pkg"),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/npm/pkg",
            content_type=CONTENT_TYPE_JSON,
        ),
        id="upload-a-package-file-4",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_NPM_DIST_TAG,
            arguments=(
                OPTION_PATH,
                "package_name=pkg",
                OPTION_PATH,
                "tag=stable",
                OPTION_ROUTE_PREFIX,
                "/projects/:id/packages/npm",
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/npm/-/package/pkg/dist-tags/stable",
            content_type=CONTENT_TYPE_JSON,
        ),
        id="create-or-update-a-dist-tag",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_GEM_UPLOAD,
            arguments=(),
            method=METHOD_POST,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/rubygems/api/v1/gems",
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-a-gem",
    ),
    pytest.param(
        RawUploadCase(
            operation_id=OP_UPLOAD_MODULE,
            arguments=UPLOAD_MODULE_PATH,
            method=METHOD_PUT,
            url=UPLOAD_MODULE_URL,
            content_type=CONTENT_TYPE_OCTET_STREAM,
        ),
        id="upload-module",
    ),
)

# --- The container registry (#63 design.md D4; #63 AC-5.2, AC-5.3, UB-2) -------------------------------------------

# The answer fields D4's steps read: step 1's login (`GET /user`), step 2's image prefix ("Retrieve a project"), whose
# text before the first `/` is the registry's host, and step 3's registry token (`/jwt/auth`); the registry's error
# shape (the OCI distribution spec's `errors`).
FIELD_USERNAME = "username"
FIELD_IMAGE_PREFIX = "container_registry_image_prefix"
FIELD_REGISTRY_TOKEN = "token"  # an answer field name, not a secret
FIELD_REPOSITORIES = "repositories"
FIELD_ERRORS = "errors"
FIELD_CODE = "code"
USERNAME = "package-test-user"
IMAGE_PREFIX = "registry.example.com/group/project"
REGISTRY_TOKEN = "registry-token-for-the-package-test"  # pragma: allowlist secret

# The credential headers, by lower-cased name (conventions.md "Credential types"); what each request carries: the
# configured `PRIVATE-TOKEN` on the configured host's API, `Authorization: Basic` of `<login>:<token>` (RFC 7617
# section 2) on `/jwt/auth`, `Authorization: Bearer` of the registry token on the registry (D4 steps 1 to 4).
HEADER_PRIVATE_TOKEN = "private-token"
HEADER_JOB_TOKEN = "job-token"
HEADER_AUTHORIZATION = "authorization"
CREDENTIAL_HEADER_NAMES = frozenset({HEADER_PRIVATE_TOKEN, HEADER_JOB_TOKEN, HEADER_AUTHORIZATION})
LOGIN_AND_TOKEN_BASE64 = base64.b64encode(s=f"{USERNAME}:{TOKEN}".encode(encoding=TEXT_ENCODING)).decode(
    encoding=ASCII_ENCODING
)
CONFIGURED_CREDENTIAL = {HEADER_PRIVATE_TOKEN: TOKEN}
BASIC_CREDENTIAL = {HEADER_AUTHORIZATION: f"Basic {LOGIN_AND_TOKEN_BASE64}"}
BEARER_CREDENTIAL = {HEADER_AUTHORIZATION: f"Bearer {REGISTRY_TOKEN}"}
# The texts no request off the configured host, and no log record, may hold (UB-2; D4 "AC-5.3").
CONFIGURED_SECRETS: Dict[str, str] = {
    "the configured token": TOKEN,
    "the Base64 of <login>:<token>": LOGIN_AND_TOKEN_BASE64,
}
SECRETS: Dict[str, str] = {**CONFIGURED_SECRETS, "the registry token": REGISTRY_TOKEN}

# The requests of D4's four steps: `GET /user`, `GET /projects/<project_id>`, `/jwt/auth` with the record's scope
# (`repository:group/project:delete`, `registry:catalog:*`) in its query, then the registry's own request.
HOST_ROOT = f"https://{fixtures.HOST}"
REGISTRY_ORIGIN = "https://registry.example.com"
USER_URL = f"{REST_BASE}/user"
PROJECT_URL = f"{REST_BASE}/projects/{PROJECT_ID}"
DELETE_TAGS_JWT_URL = f"{HOST_ROOT}/jwt/auth?service=container_registry&scope=repository%3Agroup%2Fproject%3Adelete"
CATALOG_JWT_URL = f"{HOST_ROOT}/jwt/auth?service=container_registry&scope=registry%3Acatalog%3A%2A"
DELETE_TAGS_URL = f"{REGISTRY_ORIGIN}/v2/group/project/tags/reference/1a2b3c4"
CATALOG_URL = f"{REGISTRY_ORIGIN}/v2/_catalog"
DELETE_TAGS_ARGV: Tuple[str, ...] = (
    OP_DELETE_IMAGE_TAGS,
    OPTION_PATH,
    "CI_REGISTRY_IMAGE=group/project",
    OPTION_PATH,
    "CI_COMMIT_SHORT_SHA=1a2b3c4",
)
CATALOG_ANSWER: Dict[str, Any] = {FIELD_REPOSITORIES: ["group/project"]}
MANIFEST_UNKNOWN_ANSWER: Dict[str, Any] = {
    FIELD_ERRORS: [{FIELD_CODE: "MANIFEST_UNKNOWN", FIELD_MESSAGE: "manifest unknown"}]
}


class Answer(NamedTuple):
    """A scripted answer of the configured host: its status and its JSON body."""

    status: int
    body: Any


USER_ANSWER = Answer(status=STATUS_OK, body={FIELD_ID: 7, FIELD_USERNAME: USERNAME})
PROJECT_ANSWER = Answer(status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: IMAGE_PREFIX})
JWT_ANSWER = Answer(status=STATUS_OK, body={FIELD_REGISTRY_TOKEN: REGISTRY_TOKEN})
UNAUTHORIZED_ANSWER = Answer(status=STATUS_UNAUTHORIZED, body={FIELD_MESSAGE: "401 Unauthorized"})


class RegistryCase(NamedTuple):
    """A call of a container-registry record (#63 AC-5.2): the arguments after ``call``, the ``/jwt/auth`` URL of its
    scope, the method and URL of its registry request, the registry's answer to it, the exit code, and the JSON value
    that prints (``None``: nothing prints)."""

    argv: Tuple[str, ...]
    jwt_url: str
    method: str
    url: str
    answer: Answer
    code: int
    printed: Any = None


# #63 AC-5.2 (design.md Correctness Properties): each registry record sent, and the delete answered 404 at step 4.
REGISTRY_CASES = (
    pytest.param(
        RegistryCase(
            argv=DELETE_TAGS_ARGV,
            jwt_url=DELETE_TAGS_JWT_URL,
            method=METHOD_DELETE,
            url=DELETE_TAGS_URL,
            answer=Answer(status=STATUS_ACCEPTED, body=None),
            code=EXIT_OK,
        ),
        id="delete-image-tags-by-reference",
    ),
    pytest.param(
        RegistryCase(
            argv=(OP_LIST_CONTAINER_REPOSITORIES,),
            jwt_url=CATALOG_JWT_URL,
            method=METHOD_GET,
            url=CATALOG_URL,
            answer=Answer(status=STATUS_OK, body=CATALOG_ANSWER),
            code=EXIT_OK,
            printed=CATALOG_ANSWER,
        ),
        id="listing-all-container-repositories",
    ),
    pytest.param(
        RegistryCase(
            argv=DELETE_TAGS_ARGV,
            jwt_url=DELETE_TAGS_JWT_URL,
            method=METHOD_DELETE,
            url=DELETE_TAGS_URL,
            answer=Answer(status=STATUS_NOT_FOUND, body=MANIFEST_UNKNOWN_ANSWER),
            code=EXIT_API_ERROR,
        ),
        id="delete-image-tags-answered-404",
    ),
)


class NoTokenCase(NamedTuple):
    """A delete-by-reference call whose registry token cannot be obtained (#63 AC-5.3): the requests it sends — those
    of D4's steps up to the failing one, its own included — the configured ``token_type`` (``None``: none configured,
    so ``private``), and the answers of steps 1 to 3."""

    sent: Tuple[Tuple[str, str], ...]
    token_type: Optional[str] = None
    user: Answer = USER_ANSWER
    project: Answer = PROJECT_ANSWER
    jwt: Answer = JWT_ANSWER


STEP_1_SENT: Tuple[Tuple[str, str], ...] = ((METHOD_GET, USER_URL),)
STEPS_1_TO_2_SENT: Tuple[Tuple[str, str], ...] = (*STEP_1_SENT, (METHOD_GET, PROJECT_URL))
STEPS_1_TO_3_SENT: Tuple[Tuple[str, str], ...] = (*STEPS_1_TO_2_SENT, (METHOD_GET, DELETE_TAGS_JWT_URL))

# #63 AC-5.3 (design.md Correctness Properties): a `bearer` token (no step is sent); `GET /user` answering 401, or
# answering without a string `username` (D4 step 1); a project answer without `container_registry_image_prefix`, or with
# one whose registry host is empty or holds `#`, `@`, `?`, a backslash or white space (D4 step 2); `/jwt/auth` answering
# 401, or `{}`.
NO_TOKEN_CASES = (
    pytest.param(NoTokenCase(sent=(), token_type=TOKEN_TYPE_BEARER), id="bearer-token"),
    pytest.param(NoTokenCase(sent=STEP_1_SENT, user=UNAUTHORIZED_ANSWER), id="user-answers-401"),
    pytest.param(
        NoTokenCase(sent=STEP_1_SENT, user=Answer(status=STATUS_OK, body={FIELD_ID: 7})),
        id="user-answer-without-a-username",
    ),
    pytest.param(
        NoTokenCase(sent=STEP_1_SENT, user=Answer(status=STATUS_OK, body={FIELD_ID: 7, FIELD_USERNAME: 7})),
        id="user-answer-with-a-username-that-is-not-a-string",
    ),
    pytest.param(
        NoTokenCase(sent=STEPS_1_TO_2_SENT, project=Answer(status=STATUS_OK, body={FIELD_ID: PROJECT_ID})),
        id="no-image-prefix",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: ""}),
        ),
        id="empty-image-prefix",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "/group/project"}),
        ),
        id="image-prefix-without-a-host",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(
                status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "registry.example.com#/x"}
            ),
        ),
        id="image-prefix-host-with-a-fragment",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(
                status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "user@registry.example.com/x"}
            ),
        ),
        id="image-prefix-host-with-userinfo",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(
                status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "registry.example.com?x/g"}
            ),
        ),
        id="image-prefix-host-with-a-query",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(
                status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "registry.example.com\\x/g"}
            ),
        ),
        id="image-prefix-host-with-a-backslash",
    ),
    pytest.param(
        NoTokenCase(
            sent=STEPS_1_TO_2_SENT,
            project=Answer(status=STATUS_OK, body={FIELD_ID: PROJECT_ID, FIELD_IMAGE_PREFIX: "registry example.com/g"}),
        ),
        id="image-prefix-host-with-white-space",
    ),
    pytest.param(NoTokenCase(sent=STEPS_1_TO_3_SENT, jwt=UNAUTHORIZED_ANSWER), id="jwt-auth-answers-401"),
    pytest.param(
        NoTokenCase(sent=STEPS_1_TO_3_SENT, jwt=Answer(status=STATUS_OK, body={})),
        id="jwt-auth-answers-no-token",
    ),
)

# #63 design.md D4 step 3, "AC-5.3": a `/jwt/auth` success answer that is not a JSON object, or whose `token` is not a
# non-empty string, is refused naming the URL and the field, never quoting its body, which may hold the registry token;
# the marker stands for such a body, which no log record and no standard error may hold.
JWT_ANSWER_MARKER = "jwt-auth-answer-marker-for-the-package-test"  # pragma: allowlist secret


class JwtAnswer(NamedTuple):
    """A ``/jwt/auth`` success answer of the configured host: its headers and its body, sent verbatim when text."""

    headers: Tuple[Tuple[str, str], ...]
    body: Any


UNUSABLE_JWT_ANSWERS = (
    pytest.param(
        JwtAnswer(headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON),), body=f"{{not JSON: {JWT_ANSWER_MARKER}"),
        id="claims-json-but-is-not-json",
    ),
    pytest.param(JwtAnswer(headers=(), body=[JWT_ANSWER_MARKER]), id="a-json-array"),
    pytest.param(
        JwtAnswer(headers=(), body={FIELD_REGISTRY_TOKEN: "", FIELD_MESSAGE: JWT_ANSWER_MARKER}), id="an-empty-token"
    ),
)

# --- The refused writer (issue #15 AC-3) ----------------------------------------------------------------------------

# A call of "Change the visibility of the container registry" with a value for its one path parameter and its section's
# `container_registry_access_level`; the section has no required row but `id`.
CHANGE_REGISTRY_VISIBILITY_ARGV: Tuple[str, ...] = (
    OP_CHANGE_REGISTRY_VISIBILITY,
    OPTION_PATH,
    f"id={PROJECT_ID}",
    OPTION_RAW_FIELD,
    "container_registry_access_level=private",
)
# The end of the refusal of an ID `GATED_OPERATIONS` maps to `None` (issue #44 design.md D6).
NO_SUBCOMMAND_SENDS_IT = ": no subcommand sends it"


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory; the entry script reads ``config/gitlab.json`` under it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` (``families.package`` for the family) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str], token_type: Optional[str] = None) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's; ``token_type`` when one is given, else none, which is
    ``private``) under ``root``, the working directory, and return the exit code of the product's
    ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    if token_type is not None:
        config[FIELD_TOKEN_TYPE] = token_type
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


def media_type(*, value: Optional[str]) -> Optional[str]:
    """The media type of a ``Content-Type`` value, lower-cased and without its parameters; ``None`` without one."""
    if value is None:
        return None
    message = Message()
    message[HEADER_CONTENT_TYPE] = value
    return message.get_content_type()


class Part(NamedTuple):
    """One part of a ``multipart/form-data`` body: its ``name``, its ``filename`` (``None`` for a form field) and its
    content, unchanged."""

    name: str
    filename: Optional[str]
    content: bytes


def part_disposition(*, head: bytes) -> Message:
    """The ``Content-Disposition`` header of one multipart part's header block, parsed."""
    message = Message()
    for line in head.split(sep=CRLF):
        name, _, value = line.decode(encoding=TEXT_ENCODING).partition(HEADER_SEPARATOR)
        if name.strip().lower() == HEADER_CONTENT_DISPOSITION.lower():
            message[HEADER_CONTENT_DISPOSITION] = value.strip()
    return message


def multipart_parts(*, body: bytes, content_type: str) -> List[Part]:
    """The parts of a ``multipart/form-data`` body in body order (RFC 7578, RFC 2046 section 5.1.1): each delimiter but
    the first follows a CRLF, which belongs to it, and the close delimiter ends in ``--``."""
    header = Message()
    header[HEADER_CONTENT_TYPE] = content_type
    boundary = header.get_param(param=PARAM_BOUNDARY)
    assert isinstance(boundary, str) and boundary, f"a multipart Content-Type names its boundary: {content_type!r}"
    delimiter = CRLF + DASHES + boundary.encode(encoding=ASCII_ENCODING)
    parts: List[Part] = []
    for section in (CRLF + body).split(sep=delimiter)[1:]:
        if section.startswith(DASHES):
            break
        head, _, content = section[len(CRLF) :].partition(CRLF + CRLF)
        disposition = part_disposition(head=head)
        name = disposition.get_param(param=PARAM_NAME, header=HEADER_CONTENT_DISPOSITION)
        filename = disposition.get_param(param=PARAM_FILENAME, header=HEADER_CONTENT_DISPOSITION)
        parts.append(Part(name=str(name), filename=None if filename is None else str(filename), content=content))
    return parts


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
    return "\n".join(lines)


def count_difference(*, declared: Sequence[Any], expected: Sequence[Any]) -> str:
    """Each item ``declared`` holds fewer or more times than ``expected``, sorted, one occurrence per line."""
    declared_counts = Counter(declared)
    expected_counts = Counter(expected)
    lines = [f"missing: {item!r}" for item in sorted((expected_counts - declared_counts).elements())]
    lines.extend(f"not expected: {item!r}" for item in sorted((declared_counts - expected_counts).elements()))
    return "\n".join(lines)


def mapping_difference(*, declared: Mapping[Any, Any], expected: Mapping[Any, Any]) -> str:
    """The keys ``declared`` lacks or has beyond ``expected``, and each key whose value differs."""
    lines = [set_difference(declared=set(declared), expected=set(expected))]
    lines.extend(
        f"{key!r}: declared {declared[key]!r}, expected {expected[key]!r}"
        for key in sorted(set(declared) & set(expected))
        if declared[key] != expected[key]
    )
    return "\n".join(line for line in lines if line)


def non_scalar_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[str, Dict[str, str]]:
    """``{operation_id: {name: Kind name}}`` of every ``Param`` whose Kind is not SCALAR, over the records with any."""
    typed = {
        record.operation_id: {
            param.name: param.kind.name for param in record.params if param.kind is not registry.Kind.SCALAR
        }
        for record in records
    }
    return {operation_id: names for operation_id, names in typed.items() if names}


def required_params(*, records: Sequence[Any]) -> Dict[str, FrozenSet[str]]:
    """``{operation_id: names}`` of every ``Param`` declared ``required=True``, over the records with any."""
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required) for record in records
    }
    return {operation_id: names for operation_id, names in required.items() if names}


def write_upload(*, root: Path, file_name: str) -> Path:
    """``UPLOAD_BYTES`` written as ``file_name`` under ``root``; the file written."""
    upload = root / file_name
    upload.write_bytes(data=UPLOAD_BYTES)
    return upload


def script_steps(*, fake: Any, jwt_url: str, user: Answer, project: Answer, jwt: Answer) -> None:
    """Script the configured host's answers to #63 design.md D4's steps 1 to 3 at their exact URLs: ``GET /user``,
    ``GET /projects/<project_id>`` and the ``/jwt/auth`` request at ``jwt_url``."""
    fake.script(method=METHOD_GET, url=USER_URL, status=user.status, body=user.body)
    fake.script(method=METHOD_GET, url=PROJECT_URL, status=project.status, body=project.body)
    fake.script(method=METHOD_GET, url=jwt_url, status=jwt.status, body=jwt.body)


def credentials_sent(*, request: Any) -> Dict[str, str]:
    """Every credential header the recorded request carried, by lower-cased name."""
    return {name.lower(): value for name, value in request.headers.items() if name.lower() in CREDENTIAL_HEADER_NAMES}


def secrets_in(*, texts: Sequence[str], secrets: Mapping[str, str]) -> List[str]:
    """The name of each of ``secrets`` whose value one of ``texts`` holds."""
    return [name for name, secret in secrets.items() if any(secret in text for text in texts)]


def reported_texts(*, caplog: pytest.LogCaptureFixture, err: str) -> List[str]:
    """What the call reported: the message of every log record, every record as captured (its exception text
    included), and standard error."""
    return [*(record.getMessage() for record in caplog.records), caplog.text, err]


def off_host_requests(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every recorded request whose host is not the configured one, in order."""
    return [
        (method, url) for method, url in sent(fake=fake) if urllib.parse.urlsplit(url=url).hostname != fixtures.HOST
    ]


# --- AC-1.1, AC-1.7, issue #15 AC-1, AC-2: nothing is pending ---------------------------------------------------------


def test_nothing_is_pending() -> None:
    """AC-1.1, AC-1.7, restated by #63 design.md D9 (#63 AC-1.1, AC-1.3) and by issue #15 AC-1, AC-2: ``PENDING`` is
    empty; ``OPERATIONS`` declares the records of every Reference of the family's index rows, one per Reference and two
    for a two-endpoint entry, each key once (each such entry's records start with its base record:
    ``test_a_two_endpoint_entry_maps_its_first_endpoint``); the records on the registry host are its two keys', and the
    one record whose path is ``/projects/:id/`` is "Change the visibility of the container registry"'s ``PUT``."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"PENDING holds {len(pending)} key(s); each has its record (issue #15 AC-2): {pending}"
    declared = [record.operation_id for record in family.OPERATIONS]
    assert sorted(declared) == sorted(RECORD_IDS), (
        f"OPERATIONS declares {len(declared)} record(s), the index has {len(RECORD_IDS)} to map: one per Reference, "
        "two for a two-endpoint entry (AC-1.1; #63 AC-1.1, design.md D1, D8):\n"
        + count_difference(declared=declared, expected=RECORD_IDS)
    )
    keys = [(record.method, record.path) for record in family.OPERATIONS]
    repeated = sorted(key for key, count in Counter(keys).items() if count > 1)
    assert repeated == [], f"each key is declared once (#63 design.md D1, D9): {repeated}"
    on_registry_host = {
        record.operation_id: (record.method, record.path)
        for record in family.OPERATIONS
        if record.path.startswith(REGISTRY_HOST_PREFIX)
    }
    assert on_registry_host == REGISTRY_RECORDS, (
        "the records on the registry host are its two keys' (#63 AC-1.1, design.md D8):\n"
        + mapping_difference(declared=on_registry_host, expected=REGISTRY_RECORDS)
    )
    project_updates = {
        record.operation_id: (record.method, record.path)
        for record in family.OPERATIONS
        if record.path == PROJECT_UPDATE_PATH
    }
    assert project_updates == PROJECT_UPDATE_RECORDS, (
        "the one record of the project update's path is its index row's (issue #15 AC-1):\n"
        + mapping_difference(declared=project_updates, expected=PROJECT_UPDATE_RECORDS)
    )


# --- AC-1.2: a two-endpoint entry maps its first endpoint -------------------------------------------------------------


def test_a_two_endpoint_entry_maps_its_first_endpoint() -> None:
    """AC-1.2, restated by #63 design.md D9 (#63 AC-1.1, D1, D8): the records of every Conan v1 entry, and of NuGet
    "Upload a package file", map the endpoint its entry lists first, its base record, then the entry's other endpoint,
    which is on no ``PENDING``."""
    family = gitlab_module(name=FAMILY_MODULE)
    mapped: Dict[str, List[Tuple[str, str]]] = {}
    for record in family.OPERATIONS:
        if record.operation_id in FIRST_ENDPOINTS:
            mapped.setdefault(record.operation_id, []).append((record.method, record.path))
    expected = {operation_id: [endpoints.first, endpoints.other] for operation_id, endpoints in FIRST_ENDPOINTS.items()}
    assert mapped == expected, (
        "a two-endpoint entry's records map its first endpoint, then its other one (AC-1.2; #63 design.md D1, D8):\n"
        + mapping_difference(declared=mapped, expected=expected)
    )
    still_pending = sorted(
        endpoints.other for endpoints in FIRST_ENDPOINTS.values() if endpoints.other in family.PENDING
    )
    assert still_pending == [], (
        f"the other endpoint of a two-endpoint entry is on no PENDING (#63 AC-1.1): {still_pending}"
    )


# --- AC-1.4, AC-4.2: every Param typed as its row ---------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-1.4, AC-4.2: the ``Param``s that are not ``Kind.SCALAR`` carry the ``Kind`` of their row's Type; the
    ``Param``s declared ``required`` are the rows whose Required reads ``yes``; the raw-body records, and only they,
    declare their body's media type and send every ``Param`` in the query; every record has a JSON body and no
    ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = non_scalar_params(records=records, registry=registry)
    assert typed == KINDS, "the Params that are not Kind.SCALAR are not the rows' (AC-1.4):\n" + mapping_difference(
        declared=typed, expected=KINDS
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED.items()}
    assert required == expected_required, "required=True is not exactly where Required reads `yes` (AC-1.4):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    raw_bodies = {record.operation_id: record.content_type for record in records if record.content_type is not None}
    assert raw_bodies == RAW_BODIES, "the records with a content_type are not the raw-body uploads (AC-4.2):\n" + (
        mapping_difference(declared=raw_bodies, expected=RAW_BODIES)
    )
    misplaced = [
        (record.operation_id, param.name, param.location.name)
        for record in records
        if record.operation_id in RAW_BODIES
        for param in record.params
        if param.location.name != LOCATION_QUERY
    ]
    assert misplaced == [], f"a raw-body record sends every Param in the query (design.md D6): {misplaced}"
    misbodied = [
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    ]
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-1.4): {misbodied}"


# --- AC-1.5: no Param names a path parameter --------------------------------------------------------------------------


def test_no_param_names_a_path_parameter() -> None:
    """AC-1.5: no ``Param`` of any record names a path parameter of its record's path, a ``*name`` glob or a hyphenated
    ``:name`` included, whatever the row's ``In``; "Upload module", whose ``body`` rows are its three path parameters,
    declares no ``Param``."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    assert records, "package.OPERATIONS declares no record, so no Param can be checked (AC-1.5)"
    clashes = [
        (record.operation_id, param.name)
        for record in records
        for param in record.params
        if param.name in registry.placeholders(path=record.path)
    ]
    assert clashes == [], f"a Param names a path parameter of its record's path (AC-1.5): {clashes}"
    by_id = {record.operation_id: record for record in records}
    assert OP_UPLOAD_MODULE in by_id, f"no record declares {OP_UPLOAD_MODULE} (AC-1.1)"
    upload_module_params = [param.name for param in by_id[OP_UPLOAD_MODULE].params]
    assert upload_module_params == [], (
        f"{OP_UPLOAD_MODULE} declares no Param: its body rows are its path parameters (AC-1.5): {upload_module_params}"
    )


# --- AC-1.6, AC-4.4: only the list records are paged ------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-1.6: the thirteen list records are ``Paging.OFFSET`` and declare their ``page`` and ``per_page`` query rows;
    every other record is ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    paged = {record.operation_id: record.paging.name for record in records if record.paging is not registry.Paging.NONE}
    assert paged == PAGED_RECORDS, "the records not Paging.NONE are not the list records (AC-1.6):\n" + (
        mapping_difference(declared=paged, expected=PAGED_RECORDS)
    )
    rows = [registry.Param(name=name, location=registry.Location.QUERY) for name in PAGING_ROWS]
    undeclared = {
        record.operation_id: [row.name for row in rows if row not in record.params]
        for record in records
        if record.operation_id in PAGED_RECORDS
    }
    missing = {operation_id: names for operation_id, names in undeclared.items() if names}
    assert missing == {}, f"each paged record declares its page and per_page query rows (AC-1.6): {missing}"


@pytest.mark.parametrize(argnames="case", argvalues=LIST_CASES)
def test_a_list_record_prints_every_page(
    case: ListCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4.4: two pages scripted at their exact URLs, the second named by the first's ``x-next-page``; the call exits
    0, every scripted page is served, and the items of both print as one JSON array."""
    first_page = f"{case.url}{FIRST_PAGE_QUERY}"
    second_page = f"{case.url}{SECOND_PAGE_QUERY}"
    fake_gitlab.script(
        method=METHOD_GET, url=first_page, headers=((HEADER_NEXT_PAGE, NEXT_PAGE),), body=[PAGE_ITEMS[0]]
    )
    fake_gitlab.script(
        method=METHOD_GET, url=second_page, headers=((HEADER_NEXT_PAGE, LAST_PAGE),), body=[PAGE_ITEMS[1]]
    )
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_page), (METHOD_GET, second_page)], (
        "each page requested as Transport.pages does (#13 AC-2.5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of every item of both pages, in page order, as print_json writes it (AC-4.4):\n{captured.out}"
    )


# --- AC-2.1, AC-2.2, AC-2.3, AC-2.5: a prefix record under each of its values ----------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=PREFIX_CASES)
def test_a_prefix_record_is_sent_under_each_of_its_values(
    case: PrefixCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.1, AC-2.2, AC-2.3, AC-2.5: ``call <id> ... --route-prefix <value>`` exits 0 and sends one request, the
    record's path with ``/<route-prefix>`` replaced by the value and each ``:id`` of it one encoded segment or the
    configured project; the record holds its page's values, in line order."""
    fake_gitlab.script_next(body=ANSWER)
    argv = (case.operation_id, *case.arguments)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], (
        "the one request is sent under the route prefix the call names (AC-2.2, AC-2.3)"
    )
    family = gitlab_module(name=FAMILY_MODULE)
    declared = {
        record.operation_id: tuple(record.route_prefixes)
        for record in family.OPERATIONS
        if record.operation_id == case.operation_id
    }
    assert declared == {case.operation_id: case.route_prefixes}, (
        f"the record holds its page's route prefixes, verbatim and in line order (AC-2.1): {declared}"
    )


# --- AC-3.1, AC-3.3: the hyphenated names -----------------------------------------------------------------------------


def test_the_hyphenated_names_are_sent_as_one_segment_each(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3.1, AC-3.3: ``call package#upload-module --path module-name=infra --path module-system=aws --path
    module-version=1.0.0 --input <the bytes>`` sends one ``PUT`` to the configured project's module file, each
    hyphenated name one segment, whose body is the bytes."""
    upload = write_upload(root=project, file_name=UPLOAD_FILE_NAME)
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    argv = (OP_UPLOAD_MODULE, *UPLOAD_MODULE_PATH, OPTION_INPUT, str(upload))
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_PUT, UPLOAD_MODULE_URL)], (
        "each hyphenated name is one path parameter, written as one segment (AC-3.1)"
    )
    assert fake_gitlab.requests[0].body == UPLOAD_BYTES, "the body is the --input bytes unchanged (AC-4.2)"


# --- AC-3.2, AC-3.3: a glob record without a prefix -------------------------------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=GLOB_CASES)
def test_a_glob_record_is_sent_with_its_slashes(
    case: GlobCase,
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-3.2, AC-3.3: the Maven project download writes its ``*path`` with each ``/`` kept; a ``..`` part is refused
    by ``registry.expand`` (exit 1) and a missing ``path`` by the parameter check (exit 2), each with no request and
    an ERROR record saying why."""
    fake_gitlab.script_next(body=ANSWER)
    argv = (OP_MAVEN_PROJECT_DOWNLOAD, *case.arguments)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == case.code, f"call {list(argv)} exits {case.code}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == list(case.sent), "the requests the call sends (AC-3.2)"
    if case.logged is None:
        return
    messages = error_messages(caplog=caplog)
    assert any(case.logged in message for message in messages), (
        f"an ERROR record holds {case.logged!r} (#40 AC-2.2, AC-2.4): {messages}"
    )


# --- AC-4.2: the uploads ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=UPLOAD_CASES)
def test_an_upload_sends_the_file_as_its_part(
    case: UploadCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4.2: ``--file <attribute>=<path>`` and each required body attribute with ``-f`` send one
    ``multipart/form-data`` request: the part the attribute names carries a ``filename`` and the file's bytes
    unchanged, and each ``-f`` attribute is a part with no ``filename`` holding its text."""
    upload = write_upload(root=project, file_name=case.file_name)
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    fields = tuple(argument for name, text in case.fields for argument in (OPTION_RAW_FIELD, f"{name}{ASSIGNED}{text}"))
    argv = (case.operation_id, *case.arguments, OPTION_FILE, f"{case.attribute}{ASSIGNED}{upload}", *fields)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "one request to the record's route"
    request = fake_gitlab.requests[0]
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == CONTENT_TYPE_MULTIPART, f"the body's Content-Type: {content_type!r}"
    assert request.body is not None, "the upload carries a body"
    parts = {part.name: part for part in multipart_parts(body=request.body, content_type=str(content_type))}
    expected_names = sorted((case.attribute, *(name for name, _ in case.fields)))
    assert sorted(parts) == expected_names, f"the parts sent: {sorted(parts)}"
    assert parts[case.attribute].filename == case.file_name, "the file part carries the file's name"
    assert parts[case.attribute].content == UPLOAD_BYTES, "the file part holds the file's bytes unchanged (AC-4.2)"
    for name, text in case.fields:
        assert parts[name].filename is None, f"the -f attribute {name} is a form field, with no filename"
        assert parts[name].content == text.encode(encoding=TEXT_ENCODING), (
            f"the -f attribute {name}'s part holds its text"
        )


@pytest.mark.parametrize(argnames="case", argvalues=RAW_UPLOAD_CASES)
def test_a_raw_upload_sends_the_bytes_as_its_body(
    case: RawUploadCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4.2: ``--input <path>`` sends one request, its method and URL the record's with the query given, whose
    ``Content-Type`` is the record's media type and whose body is the file's bytes unchanged; the Maven upload, given
    ``--file file=<path>`` in place of ``--input``, exits 2 with no request."""
    upload = write_upload(root=project, file_name=UPLOAD_FILE_NAME)
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    argv = (case.operation_id, *case.arguments, OPTION_INPUT, str(upload))
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "one request to the record's route, query included"
    request = fake_gitlab.requests[0]
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == case.content_type, f"the body's Content-Type: {content_type!r}"
    assert request.body == UPLOAD_BYTES, "the body is the --input bytes unchanged, \\r\\n and \\xff included (AC-4.2)"
    if case.refused_file is None:
        return
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    multipart_argv = (case.operation_id, *case.arguments, OPTION_FILE, f"{case.refused_file}{ASSIGNED}{upload}")
    refused = run_call(root=project, argv=multipart_argv)
    refusal = capsys.readouterr()
    assert refused == EXIT_REFUSED, (
        f"call {list(multipart_argv)} exits {EXIT_REFUSED}, got {refused}: a raw-body record takes no --file "
        f"(design.md D5); stderr:\n{refusal.err}"
    )
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "the refused --file call sends no request (AC-4.2)"


# --- #63 AC-5.2, AC-5.3, UB-2: the container registry --------------------------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=REGISTRY_CASES)
def test_a_registry_record_is_sent_to_the_registry_with_its_token(
    case: RegistryCase,
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """#63 AC-5.2, UB-2 (design.md D4): the call sends, in order, ``GET /user`` and ``GET /projects/<project_id>`` with
    the configured header, the ``/jwt/auth`` request for the record's scope with ``Authorization: Basic`` of
    ``<username>:<token>`` as its only credential header, then the record's request to the registry of the project's
    ``container_registry_image_prefix``, each ``${NAME}`` written, with ``Authorization: Bearer <registry token>`` as
    its only credential and neither the configured token nor its Base64 credential; it exits 0 and prints the
    registry's answer, or, answered 404, exits 1; no log record holds the configured token, the Base64 of the login
    and the token, or the registry token."""
    caplog.set_level(level=logging.DEBUG)
    script_steps(fake=fake_gitlab, jwt_url=case.jwt_url, user=USER_ANSWER, project=PROJECT_ANSWER, jwt=JWT_ANSWER)
    fake_gitlab.script(method=case.method, url=case.url, status=case.answer.status, body=case.answer.body)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == case.code, f"call {list(case.argv)} exits {case.code}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [
        (METHOD_GET, USER_URL),
        (METHOD_GET, PROJECT_URL),
        (METHOD_GET, case.jwt_url),
        (case.method, case.url),
    ], "the login, the project's registry, the registry token for the record's scope, then the registry (D4 steps 1-4)"
    user_request, project_request, jwt_request, registry_request = fake_gitlab.requests
    assert credentials_sent(request=user_request) == CONFIGURED_CREDENTIAL, "step 1 carries the configured header"
    assert credentials_sent(request=project_request) == CONFIGURED_CREDENTIAL, "step 2 carries the configured header"
    assert credentials_sent(request=jwt_request) == BASIC_CREDENTIAL, (
        "/jwt/auth carries Basic of <username>:<token> as its only credential header (D4 step 3, RFC 7617)"
    )
    assert credentials_sent(request=registry_request) == BEARER_CREDENTIAL, (
        "the registry request carries the registry token as its only credential (D4 step 4)"
    )
    registry_texts = [registry_request.url, *registry_request.headers.values()]
    assert secrets_in(texts=registry_texts, secrets=CONFIGURED_SECRETS) == [], (
        "the configured token reaches no request off the configured origin (UB-2)"
    )
    expected_out = "" if case.printed is None else printed_json(value=case.printed)
    assert captured.out == expected_out, f"what the call prints:\n{captured.out}"
    reported = secrets_in(texts=reported_texts(caplog=caplog, err=captured.err), secrets=SECRETS)
    assert reported == [], f"no log record holds a secret (D4 AC-5.3, UB-2): {reported}"


@pytest.mark.parametrize(argnames="case", argvalues=NO_TOKEN_CASES)
def test_no_registry_token_sends_nothing_to_the_registry(
    case: NoTokenCase,
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """#63 AC-5.3, UB-2 (design.md D4): a delete-by-reference call whose registry token cannot be obtained — a
    ``bearer`` token, an error answer, or an answer without the field its step reads or with a registry host the step
    refuses — exits 1 with an ERROR record; it sends nothing to the registry, and exactly the requests of the steps up
    to the failing one, its own included; no log record holds the configured token, the Base64 of the login and the
    token, or the registry token."""
    caplog.set_level(level=logging.DEBUG)
    script_steps(fake=fake_gitlab, jwt_url=DELETE_TAGS_JWT_URL, user=case.user, project=case.project, jwt=case.jwt)
    fake_gitlab.script(method=METHOD_DELETE, url=DELETE_TAGS_URL, status=STATUS_ACCEPTED)
    code = run_call(root=project, argv=DELETE_TAGS_ARGV, token_type=case.token_type)
    captured = capsys.readouterr()
    assert code == EXIT_API_ERROR, (
        f"call {list(DELETE_TAGS_ARGV)} exits {EXIT_API_ERROR}, got {code} (AC-5.3); stderr:\n{captured.err}"
    )
    assert off_host_requests(fake=fake_gitlab) == [], "nothing is sent to the registry (AC-5.3, AC-8.3)"
    assert sent(fake=fake_gitlab) == list(case.sent), "the requests of the steps up to the failing one (D4)"
    assert error_messages(caplog=caplog), "an ERROR record says why the registry token was not obtained (#41 AC-1.7)"
    reported = secrets_in(texts=reported_texts(caplog=caplog, err=captured.err), secrets=SECRETS)
    assert reported == [], f"no log record holds a secret (D4 AC-5.3, UB-2): {reported}"


@pytest.mark.parametrize(argnames="answer", argvalues=UNUSABLE_JWT_ANSWERS)
def test_a_refused_jwt_auth_answer_is_never_reported(
    answer: JwtAnswer,
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """#63 AC-5.3, UB-2 (design.md D4 step 3): a delete-by-reference call whose ``/jwt/auth`` success answer is not a
    JSON object, or holds no non-empty string ``token``, exits 1 with an ERROR record after the requests of steps 1 to
    3 and sends nothing to the registry; no log record and no standard error holds that answer's body, the configured
    token, the Base64 of the login and the token, or the registry token."""
    caplog.set_level(level=logging.DEBUG)
    fake_gitlab.script(method=METHOD_GET, url=USER_URL, status=USER_ANSWER.status, body=USER_ANSWER.body)
    fake_gitlab.script(method=METHOD_GET, url=PROJECT_URL, status=PROJECT_ANSWER.status, body=PROJECT_ANSWER.body)
    fake_gitlab.script(
        method=METHOD_GET, url=DELETE_TAGS_JWT_URL, status=STATUS_OK, headers=answer.headers, body=answer.body
    )
    fake_gitlab.script(method=METHOD_DELETE, url=DELETE_TAGS_URL, status=STATUS_ACCEPTED)
    code = run_call(root=project, argv=DELETE_TAGS_ARGV)
    captured = capsys.readouterr()
    assert code == EXIT_API_ERROR, (
        f"call {list(DELETE_TAGS_ARGV)} exits {EXIT_API_ERROR}, got {code} (AC-5.3); stderr:\n{captured.err}"
    )
    assert off_host_requests(fake=fake_gitlab) == [], "nothing is sent to the registry (AC-5.3, AC-8.3)"
    assert sent(fake=fake_gitlab) == list(STEPS_1_TO_3_SENT), "the requests of steps 1 to 3, its own included (D4)"
    assert error_messages(caplog=caplog), "an ERROR record says why the registry token was not obtained (#41 AC-1.7)"
    withheld = {**SECRETS, "the /jwt/auth answer's body": JWT_ANSWER_MARKER}
    reported = secrets_in(texts=reported_texts(caplog=caplog, err=captured.err), secrets=withheld)
    assert reported == [], f"no log record and no standard error holds these (D4 AC-5.3, UB-2): {reported}"


# --- Issue #15 AC-1, AC-3: the writing record is refused ------------------------------------------------------------


def test_a_writing_record_is_refused(
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Issue #15 AC-1, AC-3: ``registry.lookup`` returns the record of "Change the visibility of the container
    registry", ``PUT /projects/:id/``; ``call`` given it, with a value for its path parameter, exits 2, sends no request
    and prints nothing, and one ERROR record names the ID and ends ": no subcommand sends it" (issue #44 design.md
    D6)."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    declared = {
        record.operation_id: (record.method, record.path)
        for record in family.OPERATIONS
        if record.operation_id == OP_CHANGE_REGISTRY_VISIBILITY
    }
    assert declared == PROJECT_UPDATE_RECORDS, (
        f"package.OPERATIONS declares {OP_CHANGE_REGISTRY_VISIBILITY} at its index row's key (issue #15 AC-1): "
        f"{declared}"
    )
    record = registry.lookup(operation_id=OP_CHANGE_REGISTRY_VISIBILITY)
    looked_up = {record.operation_id: (record.method, record.path)}
    assert looked_up == PROJECT_UPDATE_RECORDS, f"registry.lookup returns the family's record (AC-3): {looked_up}"
    fake_gitlab.script_next(body=ANSWER)
    code = run_call(root=project, argv=CHANGE_REGISTRY_VISIBILITY_ARGV)
    captured = capsys.readouterr()
    assert code == EXIT_REFUSED, (
        f"call {list(CHANGE_REGISTRY_VISIBILITY_ARGV)} exits {EXIT_REFUSED}, got {code} (issue #15 AC-3); "
        f"stderr:\n{captured.err}"
    )
    assert sent(fake=fake_gitlab) == [], "the refused call sends no request (issue #15 AC-3)"
    assert captured.out == "", f"a refusal prints nothing on standard output:\n{captured.out}"
    messages = error_messages(caplog=caplog)
    assert any(
        OP_CHANGE_REGISTRY_VISIBILITY in message and message.endswith(NO_SUBCOMMAND_SENDS_IT) for message in messages
    ), (
        f"one ERROR record names {OP_CHANGE_REGISTRY_VISIBILITY!r} and ends {NO_SUBCOMMAND_SENDS_IT!r}: the gate "
        f"refuses a record that writes into an existing project (issue #15 AC-3); logged: {messages!r}"
    )
