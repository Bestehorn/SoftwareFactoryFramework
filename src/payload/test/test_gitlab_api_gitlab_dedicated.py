"""Tests for ``gitlab_api/families/gitlab_dedicated.py``, the ``gitlab-dedicated`` endpoint family of the GitLab
wrapper (issue #38, the remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5, AC-7 and
AC-8).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/gitlab-dedicated.md``) and
``docs/api-reference/gitlab/rest/gitlab-dedicated.md`` (each section's endpoint, its heading, and the ``In``, ``Type``,
``Required`` and ``Notes`` columns of its ``| Attribute | In | Type |`` table). Every section of the page has one
endpoint, the one its index row carries. What is pinned:

- AC-1: ``OPERATIONS`` as ``{operation_id: (method, path)}``, each ID once, is every index row of the family but the
  four AC-2 keeps;
- AC-2: ``PENDING`` is exactly the keys of the four imports kept pending (DL-005: "Import project resources" and the
  local and remote archive imports write into an existing project; the S3 import has two-level rows), and no record
  declares their IDs;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``FILE`` for a row whose Notes begin "file upload",
  ``ARRAY_OF_HASHES`` for ``array of object`` and the ``entities`` of "Start a group or project migration", ``HASH``
  for ``hash``, ``Hash`` or ``object``, ``ARRAY`` for any other Type holding ``array`` or ``Array``); the ``required``
  names, exactly the non-path rows whose Required reads ``yes`` (a member row, ``configuration[url]`` or
  ``upload[url]``, is carried by its parent and is no ``Param``); a JSON body and no ``fixed`` pairs on every record;
- AC-5: the ``Paging.OFFSET`` records are exactly the ``GET`` sections headed "List" (every ``GET`` section with a
  ``page`` row is among them), every other record ``Paging.NONE``;
- AC-7: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``);
- AC-8: "Download a project export", answered with bytes that are not UTF-8 as ``application/octet-stream``, exits 0
  and writes those bytes unchanged (read with ``capsysbinary``).

The names and ``In`` of every ``Param`` (AC-3) and one call of every record (AC-6) are proven by
``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_gitlab_dedicated.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_gitlab_dedicated_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.gitlab_dedicated"
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
TOKEN = "glpat-gitlab-api-gitlab-dedicated-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
METHOD_GET = "GET"
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
TEXT_ENCODING = "utf-8"
DECODE_ERRORS = "replace"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_NEXT_PAGE = "x-next-page"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
# The query of a list's first page: the transport adds `per_page=100` (conventions.md "Offset-based", #13 AC-2.5), and
# the next page repeats it with `page` set to the `x-next-page` value.
FIRST_PAGE_QUERY = "per_page=100"
NEXT_PAGE = "2"
NEXT_PAGE_QUERY = f"page={NEXT_PAGE}"
LAST_PAGE = ""  # an empty `x-next-page`: no next page
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

# A path parameter as operations-index.md and rest/gitlab-dedicated.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The synthetic item each page holds; the wrapper prints every item as the host serves it.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind`, `registry.Paging` and `registry.BodyFormat` member names the tables hold (AC-4, AC-5).
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
KIND_FILE = "FILE"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"
BODY_JSON = "JSON"

# AC-8: "Download a project export" (`GET /projects/:id/export/download`), its `id` the configured project; the body
# starts as a gzip archive does and holds bytes that are no UTF-8 sequence.
OP_DOWNLOAD_PROJECT_EXPORT = "gitlab-dedicated#download-a-project-export"
PROJECT_EXPORT_URL = f"{REST_BASE}/projects/{PROJECT_ID}/export/download"
NOT_UTF8_BYTES = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\xff\xfe\xfd"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: every row linking rest/gitlab-dedicated.md but AC-2's four, as `gitlab-dedicated#<anchor>` and
# its method and path, in index order. Each Reference carries one row, and its section that one endpoint (AC-1).
RECORD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "gitlab-dedicated#retrieve-information-about-a-model-record": ("GET", "/admin/data_management/:model_name/:id"),
    "gitlab-dedicated#recalculate-the-checksum-of-a-model-record": (
        "PUT",
        "/admin/data_management/:model_name/:record_identifier/checksum",
    ),
    "gitlab-dedicated#recalculate-checksums-for-model-records": ("PUT", "/admin/data_management/:model_name/checksum"),
    "gitlab-dedicated#retrieve-model-information": ("GET", "/admin/data_management/:model_name"),
    "gitlab-dedicated#cancel-a-migration": ("POST", "/bulk_imports/:id/cancel"),
    "gitlab-dedicated#list-failed-import-records-for-a-migration-entity": (
        "GET",
        "/bulk_imports/:id/entities/:entity_id/failures",
    ),
    "gitlab-dedicated#retrieve-a-group-or-project-migration-entity": ("GET", "/bulk_imports/:id/entities/:entity_id"),
    "gitlab-dedicated#list-group-or-project-migration-entities": ("GET", "/bulk_imports/:id/entities"),
    "gitlab-dedicated#retrieve-a-group-or-project-migration": ("GET", "/bulk_imports/:id"),
    "gitlab-dedicated#list-all-group-or-project-migration-entities": ("GET", "/bulk_imports/entities"),
    "gitlab-dedicated#list-all-group-or-project-migrations": ("GET", "/bulk_imports"),
    "gitlab-dedicated#start-a-group-or-project-migration": ("POST", "/bulk_imports"),
    "gitlab-dedicated#repair-a-geo-node": ("POST", "/geo_nodes/:id/repair"),
    "gitlab-dedicated#update-a-geo-node": ("PUT", "/geo_nodes/:id"),
    "gitlab-dedicated#delete-a-geo-node": ("DELETE", "/geo_nodes/:id"),
    "gitlab-dedicated#list-all-geo-node-statuses": ("GET", "/geo_nodes/status"),
    "gitlab-dedicated#list-all-geo-nodes": ("GET", "/geo_nodes"),
    "gitlab-dedicated#create-a-geo-node": ("POST", "/geo_nodes"),
    "gitlab-dedicated#repair-a-geo-site": ("POST", "/geo_sites/:id/repair"),
    "gitlab-dedicated#retrieve-a-geo-site-status": ("GET", "/geo_sites/:id/status"),
    "gitlab-dedicated#retrieve-a-geo-site": ("GET", "/geo_sites/:id"),
    "gitlab-dedicated#update-a-geo-site": ("PUT", "/geo_sites/:id"),
    "gitlab-dedicated#delete-a-geo-site": ("DELETE", "/geo_sites/:id"),
    "gitlab-dedicated#list-all-geo-site-statuses": ("GET", "/geo_sites/status"),
    "gitlab-dedicated#list-all-geo-sites": ("GET", "/geo_sites"),
    "gitlab-dedicated#create-a-geo-site": ("POST", "/geo_sites"),
    "gitlab-dedicated#retrieve-a-group-export-download": ("GET", "/groups/:id/export/download"),
    "gitlab-dedicated#download-an-export": ("GET", "/groups/:id/export_relations/download"),
    "gitlab-dedicated#retrieve-the-status-of-an-export": ("GET", "/groups/:id/export_relations/status"),
    "gitlab-dedicated#schedule-a-new-export-for-a-group": ("POST", "/groups/:id/export_relations"),
    "gitlab-dedicated#create-a-group-export": ("POST", "/groups/:id/export"),
    "gitlab-dedicated#update-a-custom-header": ("PUT", "/groups/:id/hooks/:hook_id/custom_headers/:key"),
    "gitlab-dedicated#delete-a-custom-header": ("DELETE", "/groups/:id/hooks/:hook_id/custom_headers/:key"),
    "gitlab-dedicated#resend-group-hook-event": ("POST", "/groups/:id/hooks/:hook_id/events/:hook_event_id/resend"),
    "gitlab-dedicated#list-all-group-hook-events": ("GET", "/groups/:id/hooks/:hook_id/events"),
    "gitlab-dedicated#trigger-a-test-group-hook": ("POST", "/groups/:id/hooks/:hook_id/test/:trigger"),
    "gitlab-dedicated#update-a-url-variable": ("PUT", "/groups/:id/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#delete-a-url-variable": ("DELETE", "/groups/:id/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#retrieve-a-group-hook": ("GET", "/groups/:id/hooks/:hook_id"),
    "gitlab-dedicated#update-a-group-hook": ("PUT", "/groups/:id/hooks/:hook_id"),
    "gitlab-dedicated#delete-a-group-hook": ("DELETE", "/groups/:id/hooks/:hook_id"),
    "gitlab-dedicated#list-all-group-hooks": ("GET", "/groups/:id/hooks"),
    "gitlab-dedicated#create-a-group-hook": ("POST", "/groups/:id/hooks"),
    "gitlab-dedicated#retrieve-pending-reassignments": ("GET", "/groups/:id/placeholder_reassignments"),
    "gitlab-dedicated#reassign-placeholders": ("POST", "/groups/:id/placeholder_reassignments"),
    "gitlab-dedicated#create-a-group-import": ("POST", "/groups/import"),
    "gitlab-dedicated#set-a-url-variable-1": ("PUT", "/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#delete-a-url-variable-2": ("DELETE", "/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#update-system-hook": ("PUT", "/hooks/:hook_id"),
    "gitlab-dedicated#retrieve-system-hook": ("GET", "/hooks/:id"),
    "gitlab-dedicated#test-system-hook": ("POST", "/hooks/:id"),
    "gitlab-dedicated#delete-system-hook": ("DELETE", "/hooks/:id"),
    "gitlab-dedicated#list-all-system-hooks": ("GET", "/hooks"),
    "gitlab-dedicated#add-new-system-hook": ("POST", "/hooks"),
    "gitlab-dedicated#import-repository-from-bitbucket-server": ("POST", "/import/bitbucket_server"),
    "gitlab-dedicated#import-repository-from-bitbucket-cloud": ("POST", "/import/bitbucket"),
    "gitlab-dedicated#cancel-github-project-import": ("POST", "/import/github/cancel"),
    "gitlab-dedicated#import-github-gists-into-gitlab-snippets": ("POST", "/import/github/gists"),
    "gitlab-dedicated#import-repository-from-github": ("POST", "/import/github"),
    "gitlab-dedicated#download-a-project-export": ("GET", "/projects/:id/export/download"),
    "gitlab-dedicated#download-an-export-1": ("GET", "/projects/:id/export_relations/download"),
    "gitlab-dedicated#retrieve-the-status-of-an-export-1": ("GET", "/projects/:id/export_relations/status"),
    "gitlab-dedicated#schedule-a-new-export-for-a-project": ("POST", "/projects/:id/export_relations"),
    "gitlab-dedicated#retrieve-the-status-of-a-project-export": ("GET", "/projects/:id/export"),
    "gitlab-dedicated#export-a-project": ("POST", "/projects/:id/export"),
    "gitlab-dedicated#set-a-custom-header": ("PUT", "/projects/:id/hooks/:hook_id/custom_headers/:key"),
    "gitlab-dedicated#delete-a-custom-header-1": ("DELETE", "/projects/:id/hooks/:hook_id/custom_headers/:key"),
    "gitlab-dedicated#resend-a-project-webhook-event": (
        "POST",
        "/projects/:id/hooks/:hook_id/events/:hook_event_id/resend",
    ),
    "gitlab-dedicated#list-project-webhook-events": ("GET", "/projects/:id/hooks/:hook_id/events"),
    "gitlab-dedicated#trigger-a-test-project-webhook": ("POST", "/projects/:id/hooks/:hook_id/test/:trigger"),
    "gitlab-dedicated#set-a-url-variable": ("PUT", "/projects/:id/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#delete-a-url-variable-1": ("DELETE", "/projects/:id/hooks/:hook_id/url_variables/:key"),
    "gitlab-dedicated#retrieve-a-project-webhook": ("GET", "/projects/:id/hooks/:hook_id"),
    "gitlab-dedicated#update-a-project-webhook": ("PUT", "/projects/:id/hooks/:hook_id"),
    "gitlab-dedicated#delete-project-webhook": ("DELETE", "/projects/:id/hooks/:hook_id"),
    "gitlab-dedicated#list-webhooks-for-a-project": ("GET", "/projects/:id/hooks"),
    "gitlab-dedicated#add-a-webhook-to-a-project": ("POST", "/projects/:id/hooks"),
    "gitlab-dedicated#retrieve-the-status-of-a-project-import": ("GET", "/projects/:id/import"),
    "gitlab-dedicated#retrieve-the-status-of-a-project-resource-import": ("GET", "/projects/:id/relation-imports"),
}

# AC-2, DL-005: the four imports kept pending, each with the one index row it has — "Import project resources" and the
# imports from a local and a remote archive (they write into an existing project), and the import from an AWS S3
# bucket (two-level `override_params[...][...]` rows). No section of the page has a second endpoint.
KEPT_PENDING: Dict[str, Tuple[str, str]] = {
    "gitlab-dedicated#import-project-resources": ("POST", "/projects/import-relation"),
    "gitlab-dedicated#import-a-project-from-a-local-archive": ("POST", "/projects/import"),
    "gitlab-dedicated#import-a-project-from-an-aws-s3-bucket": ("POST", "/projects/remote-import-s3"),
    "gitlab-dedicated#import-a-project-from-a-remote-archive": ("POST", "/projects/remote-import"),
}
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(KEPT_PENDING.values())

# rest/gitlab-dedicated.md: every query, body or form row of a record whose Kind is not SCALAR, by (record ID, name)
# (AC-4). `array` and `Array` rows are ARRAY, but `entities` of "Start a group or project migration" (its members
# `entities[source_type]`, ...); `array of strings` is ARRAY; `array of object` is ARRAY_OF_HASHES; `hash`, `Hash` and
# `object` are HASH; a `file upload` row is FILE whatever its Type (`String`, `file`). A member row
# (`configuration[url]`, `upload[http_method]`) is no Param. Every other row's Type is `string`, `String`, `integer`,
# `Integer`, `integer (int32)`, `integer or string`, `Integer or string`, `string or integer`, `boolean` or `Boolean`,
# a SCALAR.
NON_SCALAR_PARAMS: Dict[Tuple[str, str], str] = {
    ("gitlab-dedicated#retrieve-model-information", "identifiers"): KIND_ARRAY,
    ("gitlab-dedicated#recalculate-checksums-for-model-records", "identifiers"): KIND_ARRAY,
    ("gitlab-dedicated#create-a-geo-node", "selective_sync_shards"): KIND_ARRAY,
    ("gitlab-dedicated#create-a-geo-node", "selective_sync_namespace_ids"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-geo-node", "selective_sync_shards"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-geo-node", "selective_sync_namespace_ids"): KIND_ARRAY,
    ("gitlab-dedicated#create-a-geo-site", "selective_sync_shards"): KIND_ARRAY,
    ("gitlab-dedicated#create-a-geo-site", "selective_sync_namespace_ids"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-geo-site", "selective_sync_shards"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-geo-site", "selective_sync_namespace_ids"): KIND_ARRAY,
    ("gitlab-dedicated#start-a-group-or-project-migration", "configuration"): KIND_HASH,
    ("gitlab-dedicated#start-a-group-or-project-migration", "entities"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#create-a-group-import", "file"): KIND_FILE,
    ("gitlab-dedicated#reassign-placeholders", "file"): KIND_FILE,
    ("gitlab-dedicated#create-a-group-hook", "custom_headers"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-group-hook", "custom_headers"): KIND_ARRAY,
    ("gitlab-dedicated#import-repository-from-github", "optional_stages"): KIND_HASH,
    ("gitlab-dedicated#export-a-project", "excluded_relations"): KIND_ARRAY,
    ("gitlab-dedicated#export-a-project", "upload"): KIND_HASH,
    ("gitlab-dedicated#add-a-webhook-to-a-project", "custom_headers"): KIND_ARRAY,
    ("gitlab-dedicated#add-a-webhook-to-a-project", "url_variables"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#update-a-project-webhook", "custom_headers"): KIND_ARRAY,
    ("gitlab-dedicated#update-a-project-webhook", "url_variables"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#add-new-system-hook", "url_variables"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#add-new-system-hook", "custom_headers"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#update-system-hook", "url_variables"): KIND_ARRAY_OF_HASHES,
    ("gitlab-dedicated#update-system-hook", "custom_headers"): KIND_ARRAY_OF_HASHES,
}

# rest/gitlab-dedicated.md: the non-path rows of a record whose Required reads `yes`, by record, in table order; a
# record with none is not listed (AC-4). A member row whose Required reads `yes` (`configuration[url]`,
# `entities[source_type]`, `upload[url]`) is carried by its parent, so `upload` of "Export a project", whose own row
# is not required, is not required either.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "gitlab-dedicated#retrieve-information-about-a-model-record": ("record_identifier",),
    "gitlab-dedicated#create-a-geo-node": ("name", "url"),
    "gitlab-dedicated#create-a-geo-site": ("name", "url"),
    "gitlab-dedicated#start-a-group-or-project-migration": ("configuration", "entities"),
    "gitlab-dedicated#create-a-group-import": ("file", "name", "path"),
    "gitlab-dedicated#reassign-placeholders": ("file",),
    "gitlab-dedicated#download-an-export": ("relation",),
    "gitlab-dedicated#create-a-group-hook": ("url",),
    "gitlab-dedicated#update-a-group-hook": ("url",),
    "gitlab-dedicated#update-a-custom-header": ("value",),
    "gitlab-dedicated#update-a-url-variable": ("value",),
    "gitlab-dedicated#import-repository-from-github": ("personal_access_token", "repo_id", "target_namespace"),
    "gitlab-dedicated#cancel-github-project-import": ("project_id",),
    "gitlab-dedicated#import-github-gists-into-gitlab-snippets": ("personal_access_token",),
    "gitlab-dedicated#import-repository-from-bitbucket-server": (
        "bitbucket_server_project",
        "bitbucket_server_repo",
        "bitbucket_server_url",
        "bitbucket_server_username",
        "personal_access_token",
    ),
    "gitlab-dedicated#import-repository-from-bitbucket-cloud": (
        "bitbucket_api_token",
        "bitbucket_email",
        "repo_path",
        "target_namespace",
    ),
    "gitlab-dedicated#download-an-export-1": ("relation",),
    "gitlab-dedicated#add-a-webhook-to-a-project": ("url",),
    "gitlab-dedicated#update-a-project-webhook": ("url",),
    "gitlab-dedicated#set-a-custom-header": ("value",),
    "gitlab-dedicated#set-a-url-variable": ("value",),
    "gitlab-dedicated#add-new-system-hook": ("url",),
    "gitlab-dedicated#set-a-url-variable-1": ("value",),
}

# rest/gitlab-dedicated.md: every `GET` section headed "List", in page order (AC-5). The seven whose table has a `page`
# row ("List all group or project migrations", "List all group or project migration entities", "List group or project
# migration entities", "List all group hook events", "List webhooks for a project", "List project webhook events",
# "List all system hooks") are among them; no list of the page answers one object.
LIST_IDS: Tuple[str, ...] = (
    "gitlab-dedicated#list-all-geo-nodes",
    "gitlab-dedicated#list-all-geo-node-statuses",
    "gitlab-dedicated#list-all-geo-sites",
    "gitlab-dedicated#list-all-geo-site-statuses",
    "gitlab-dedicated#list-all-group-or-project-migrations",
    "gitlab-dedicated#list-all-group-or-project-migration-entities",
    "gitlab-dedicated#list-group-or-project-migration-entities",
    "gitlab-dedicated#list-failed-import-records-for-a-migration-entity",
    "gitlab-dedicated#list-all-group-hooks",
    "gitlab-dedicated#list-all-group-hook-events",
    "gitlab-dedicated#list-webhooks-for-a-project",
    "gitlab-dedicated#list-project-webhook-events",
    "gitlab-dedicated#list-all-system-hooks",
)


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
    """Import ``gitlab_api.<name>`` (``families.gitlab_dedicated`` for the family) inside a test, after asserting its
    file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
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


def typed_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[Tuple[str, str], str]:
    """``{(operation_id, name): Kind name}`` of every ``Param`` whose Kind is not SCALAR."""
    return {
        (record.operation_id, param.name): param.kind.name
        for record in records
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }


def required_params(*, records: Sequence[Any]) -> Dict[str, FrozenSet[str]]:
    """``{operation_id: names}`` of every ``Param`` declared ``required=True``, over the records with any."""
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required) for record in records
    }
    return {operation_id: names for operation_id, names in required.items() if names}


def path_values(*, path: str) -> Dict[str, str]:
    """A distinct number for each placeholder of ``path``, in path order: ``101``, ``102``, ..."""
    names = dict.fromkeys(match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=path))
    return {name: str(FIRST_PATH_VALUE + position) for position, name in enumerate(names)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each placeholder replaced by its value (the values are digits, so nothing is encoded)."""
    return PLACEHOLDER.sub(repl=lambda match: values[match.group(GROUP_NAME)], string=path)


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def script_page(*, fake: Any, url: str, item: Mapping[str, Any], next_page: str) -> None:
    """Script one JSON page for ``GET url``: a one-item array, ``x-next-page`` set to ``next_page``."""
    fake.script(
        method=METHOD_GET,
        url=url,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON), (HEADER_NEXT_PAGE, next_page)),
        body=json.dumps(obj=[item]).encode(encoding=TEXT_ENCODING),
    )


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def list_params() -> List[Any]:
    """One case per entry of ``LIST_IDS`` with its path from ``RECORD_ENDPOINTS``, named by its anchor."""
    return [
        pytest.param(operation_id, RECORD_ENDPOINTS[operation_id][1], id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id in LIST_IDS
    ]


# --- AC-1: the records ------------------------------------------------------------------------------------------


def test_every_reference_has_its_record() -> None:
    """AC-1, UB-2: ``OPERATIONS`` as ``{operation_id: (method, path)}``, each ID once, is ``RECORD_ENDPOINTS``: every
    index row of the family but AC-2's four."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared = [(record.operation_id, (record.method, record.path)) for record in family.OPERATIONS]
    identifiers = [operation_id for operation_id, _ in declared]
    repeated = sorted({operation_id for operation_id in identifiers if identifiers.count(operation_id) > 1})
    assert not repeated, f"gitlab_dedicated.OPERATIONS declares these IDs more than once: {repeated}"
    endpoints = dict(declared)
    assert endpoints == RECORD_ENDPOINTS, "gitlab_dedicated.OPERATIONS is not the family's index rows (AC-1):\n" + (
        mapping_difference(declared=endpoints, expected=RECORD_ENDPOINTS)
    )


# --- AC-2: what stays pending ---------------------------------------------------------------------------------------


def test_only_the_kept_keys_are_pending() -> None:
    """AC-2, UB-2: ``PENDING`` is exactly the keys of the four imports kept pending, and no record declares their
    IDs."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "gitlab_dedicated.PENDING is not the keys AC-2 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )
    declared_kept = sorted(record.operation_id for record in family.OPERATIONS if record.operation_id in KEPT_PENDING)
    assert declared_kept == [], f"the IDs kept pending have no record (AC-2): {declared_kept}"


# --- AC-4: kinds, required attributes, bodies -----------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-4: the ``Param``s that are not ``SCALAR`` carry their row's ``Kind``; the ``Param``s declared ``required``
    are exactly the non-path rows whose Required reads ``yes``; every record's body is ``BodyFormat.JSON`` and its
    ``fixed`` is empty."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = typed_params(records=records, registry=registry)
    assert typed == NON_SCALAR_PARAMS, "the Params that are not Kind.SCALAR are not the sections' (AC-4):\n" + (
        mapping_difference(declared=typed, expected=NON_SCALAR_PARAMS)
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert required == expected_required, "required=True is not exactly the Required `yes` rows (AC-4):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    bodies = {record.operation_id: record.body.name for record in records}
    expected_bodies = {operation_id: BODY_JSON for operation_id in RECORD_ENDPOINTS}
    assert bodies == expected_bodies, "every record's body is BodyFormat.JSON (AC-4):\n" + mapping_difference(
        declared=bodies, expected=expected_bodies
    )
    fixed = {record.operation_id: record.fixed for record in records if record.fixed}
    assert fixed == {}, f"every record's fixed is empty (AC-4): {fixed}"


# --- AC-5, AC-7: the list records -----------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-5: every ``LIST_IDS`` record is ``Paging.OFFSET`` and every other record ``Paging.NONE``; none is
    ``Paging.KEYSET``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paging = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {
        operation_id: PAGING_OFFSET if operation_id in LIST_IDS else PAGING_NONE for operation_id in RECORD_ENDPOINTS
    }
    assert paging == expected, "the records' Paging is not the sections' (AC-5):\n" + mapping_difference(
        declared=paging, expected=expected
    )


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_page(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-7: ``call <id> --path NAME=VALUE ...`` against two pages, the second named by the first's ``x-next-page``,
    exits 0, requests both pages at their exact URLs and prints both items as one JSON array."""
    values = path_values(path=path)
    argv = [
        operation_id,
        *(part for name, value in values.items() for part in (OPTION_PATH, f"{name}{ASSIGNED}{value}")),
    ]
    first_url = f"{REST_BASE}{expanded(path=path, values=values)}?{FIRST_PAGE_QUERY}"
    next_url = f"{first_url}&{NEXT_PAGE_QUERY}"
    script_page(fake=fake_gitlab, url=first_url, item=PAGE_ITEMS[0], next_page=NEXT_PAGE)
    script_page(fake=fake_gitlab, url=next_url, item=PAGE_ITEMS[1], next_page=LAST_PAGE)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_url), (METHOD_GET, next_url)], (
        "each page requested as Transport.pages does (#13 AC-2.5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-7):\n{captured.out}"
    )


# --- AC-8: a download -----------------------------------------------------------------------------------------------


def test_a_download_is_written_unchanged(
    project: Path, fake_gitlab: Any, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """AC-8: ``call gitlab-dedicated#download-a-project-export``, answered with bytes that are not UTF-8 as
    ``application/octet-stream``, sends one ``GET`` to the configured project's export, exits 0 and writes the bytes
    unchanged, no line end added."""
    argv = [OP_DOWNLOAD_PROJECT_EXPORT]
    fake_gitlab.script(
        method=METHOD_GET,
        url=PROJECT_EXPORT_URL,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
        body=NOT_UTF8_BYTES,
    )
    code = run_call(root=project, argv=argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, PROJECT_EXPORT_URL)], "one GET to the export, id the project"
    assert captured.out == NOT_UTF8_BYTES, (
        f"the body's bytes unchanged, no line end added (AC-8); standard output: {captured.out!r}"
    )
