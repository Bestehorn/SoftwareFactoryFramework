"""Tests for ``gitlab_api/families/create.py``, the ``create`` endpoint family of the GitLab wrapper (issue #35, the
create slice of the wrapper rewrite; ``change.md`` AC-1 to AC-4, AC-6 and AC-7).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/create.md``) and
``docs/api-reference/gitlab/rest/create.md`` (each section's endpoints, its heading, and the ``In``, ``Type`` and
``Required`` columns of its ``| Attribute | In | Type |`` table). What is pinned:

- AC-1 (as issue #63 design.md D9 restates it): ``PENDING`` is exactly the keys of the IDs kept pending;
  ``OPERATIONS`` declares every Reference of the family but the kept IDs (both References of ``GET /keys`` included),
  each key of an ID once; "Generate changelog data" has a record per endpoint, its base record (the first) first
  (issue #63 AC-1.1, AC-1.3, design.md D1, D8);
- AC-2, AC-3: the ``Kind`` of every ``Param`` that is not ``SCALAR`` or is a query member row (``range[end]``):
  ``ARRAY_OF_HASHES`` for an ``array of hashes`` row and the ``files`` of "Retrieve multiple blobs in a single
  request", ``ARRAY`` for any other Type holding ``array``, ``HASH`` for ``hash``; the ``required`` ``Param`` names,
  exactly the non-path rows whose Required reads ``yes``; a JSON body and no ``fixed`` pairs on every record;
- AC-4: the ``Paging.OFFSET`` records are exactly the ``GET`` sections headed "List" or with a ``page`` row, and no
  record is ``Paging.KEYSET``;
- AC-6: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``);
- AC-7: "Retrieve raw blob content", answered with bytes that are not UTF-8 as ``application/octet-stream``, exits 0
  and writes those bytes unchanged (read with ``capsysbinary``);
- issue #63 AC-3.1, AC-3.2, AC-8.3: "Delete a group SSH certificate" with ``--path id=7 --path id=12345`` sends one
  ``DELETE`` to ``/groups/7/ssh_certificates/12345``;
- issue #63 AC-4.1, AC-8.3: "Retrieve file archive from a repository" with ``--path format=<format>`` sends one ``GET``
  to ``archive.<format>`` for each format the docs page lists, and without ``--path format`` to ``archive``; no URL
  holds ``[``.

The names and ``In`` of every ``Param`` (AC-2) and one call of every record (AC-5) are proven by
``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_create.py`` (no network).
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
WRAPPER_MODULE = "gitlab_wrapper_create_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.create"
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
TOKEN = "glpat-gitlab-api-create-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
METHOD_GET = "GET"
METHOD_DELETE = "DELETE"
STATUS_NO_CONTENT = 204
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
TEXT_ENCODING = "utf-8"
DECODE_ERRORS = "replace"
HEADER_CONTENT_TYPE = "Content-Type"
# The configured token's header for the default token type, matched case-insensitively by `RecordedRequest.header`.
HEADER_PRIVATE_TOKEN = "PRIVATE-TOKEN"
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

# A path parameter as operations-index.md and rest/create.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The synthetic item each page holds; the wrapper prints every item as the host serves it.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` member names the tables hold (AC-3), and the marks of a member row's name (`range[end]`,
# `files:content`), as test/test_gitlab_wrapper_contract.py reads them.
KIND_SCALAR = "SCALAR"
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
MEMBER_MARKS = ("[", ":")

# AC-7: "Retrieve raw blob content" (`GET /projects/:id/repository/blobs/:sha/raw`), its `id` the configured project;
# the body starts as a PNG does and holds bytes that are no UTF-8 sequence.
OP_RETRIEVE_RAW_BLOB = "create#retrieve-raw-blob-content"
PATH_SHA = "sha"
BLOB_SHA = "7d70e02"
RAW_BLOB_URL = f"{REST_BASE}/projects/{PROJECT_ID}/repository/blobs/{BLOB_SHA}/raw"
NOT_UTF8_BYTES = b"\x89PNG\r\n\x1a\n\x00\xff\xfe\xfd"

# Issue #63 AC-3.2: "Delete a group SSH certificate" (`DELETE /groups/:id/ssh_certificates/:id`), the group's `id`
# given first and the certificate's second; GitLab answers `204`.
OP_DELETE_GROUP_SSH_CERTIFICATE = "create#delete-a-group-ssh-certificate"
SSH_CERTIFICATE_ID_VALUES: Tuple[str, ...] = ("id=7", "id=12345")
SSH_CERTIFICATE_URL = f"{REST_BASE}/groups/7/ssh_certificates/12345"

# Issue #63 AC-4.1: "Retrieve file archive from a repository" (`GET /projects/:id/repository/archive[.format]`), its
# `id` the configured project; the formats docs.gitlab.com `repositories` "Available options" lists (design.md D3),
# each given as `--path format=<format>` and sent as the suffix `.<format>`; without it the path ends at `archive`.
OP_RETRIEVE_FILE_ARCHIVE = "create#retrieve-file-archive-from-a-repository"
PATH_FORMAT = "format"
ARCHIVE_FORMATS: Tuple[str, ...] = ("bz2", "tar", "tar.bz2", "tar.gz", "tb2", "tbz", "tbz2", "zip")
ARCHIVE_URL = f"{REST_BASE}/projects/{PROJECT_ID}/repository/archive"
SUFFIX_SEPARATOR = "."
UNEXPANDED_MARK = "["
NO_FORMAT_CASE = "no-format"
ARCHIVE_BYTES = b"\x1f\x8b\x08\x00\xff\xfe\xfd"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: the Reference of every row linking rest/create.md, written `create#<anchor>`, sorted. The two
# rows of "Generate changelog data" share one Reference; `GET /keys` has two.
INDEX_REFERENCES: Tuple[str, ...] = (
    "create#add-a-group-ssh-certificate",
    "create#add-a-note-to-a-snippet-thread",
    "create#add-a-note-to-an-epic-thread",
    "create#add-a-note-to-an-issue-thread",
    "create#add-an-instance-ssh-certificate",
    "create#add-changelog-data-to-file",
    "create#add-note-to-a-commit-thread",
    "create#add-note-to-a-merge-request-thread",
    "create#add-push-rules-to-a-group",
    "create#add-push-rules-to-a-project",
    "create#apply-a-suggestion",
    "create#apply-multiple-suggestions",
    "create#cherry-pick-a-commit",
    "create#compare-branches-tags-or-commits",
    "create#create-a-commit",
    "create#create-a-commit-thread",
    "create#create-a-file-in-a-repository",
    "create#create-a-group-repository-storage-move",
    "create#create-a-merge-request-thread",
    "create#create-a-new-tag",
    "create#create-a-project-alias",
    "create#create-a-push-mirror",
    "create#create-a-snippet",
    "create#create-a-snippet-1",
    "create#create-a-snippet-thread",
    "create#create-an-epic-thread",
    "create#create-an-issue-thread",
    "create#create-group-repository-storage-moves-for-a-storage-shard",
    "create#create-repository-branch",
    "create#delete-a-commit-discussion-note",
    "create#delete-a-file-in-a-repository",
    "create#delete-a-group-ssh-certificate",
    "create#delete-a-merge-request-thread-note",
    "create#delete-a-project-alias",
    "create#delete-a-remote-mirror-from-a-project",
    "create#delete-a-snippet",
    "create#delete-a-snippet-thread-note",
    "create#delete-a-tag",
    "create#delete-all-merged-branches",
    "create#delete-an-epic-thread-note",
    "create#delete-an-instance-ssh-certificate",
    "create#delete-an-issue-thread-note",
    "create#delete-repository-branch",
    "create#delete-snippet",
    "create#delete-the-push-rules-of-a-group",
    "create#delete-the-push-rules-of-a-project",
    "create#force-push-mirror-update",
    "create#generate-changelog-data",
    "create#get-a-protected-tag-or-wildcard-protected-tag",
    "create#get-a-single-protected-branch-or-wildcard-protected-branch",
    "create#get-commit-sequence",
    "create#get-contributor-list",
    "create#get-file-blame-metadata-only",
    "create#get-file-metadata-only",
    "create#get-merge-base",
    "create#get-user-agent-details",
    "create#health",
    "create#list-all-commit-comments",
    "create#list-all-commit-discussion-items",
    "create#list-all-commit-discussions",
    "create#list-all-dockerfile-templates",
    "create#list-all-epic-discussion-items",
    "create#list-all-gitignore-templates",
    "create#list-all-group-repository-storage-moves",
    "create#list-all-group-ssh-certificates",
    "create#list-all-instance-ssh-certificates",
    "create#list-all-issue-discussion-items",
    "create#list-all-merge-request-discussion-items",
    "create#list-all-project-aliases",
    "create#list-all-project-repository-tags",
    "create#list-all-public-snippets",
    "create#list-all-references-a-commit-is-pushed-to",
    "create#list-all-remote-mirrors-for-a-project",
    "create#list-all-repository-branches",
    "create#list-all-repository-storage-moves-for-a-group",
    "create#list-all-repository-storage-moves-for-a-snippet",
    "create#list-all-repository-trees-in-a-project",
    "create#list-all-snippet-discussion-items",
    "create#list-all-snippet-repository-storage-moves",
    "create#list-all-snippets",
    "create#list-all-snippets-for-a-project",
    "create#list-all-snippets-for-current-user",
    "create#list-all-templates-of-a-particular-type",
    "create#list-commit-statuses",
    "create#list-merge-requests-associated-with-a-commit",
    "create#list-protected-branches",
    "create#list-protected-branches-1",
    "create#list-protected-tags",
    "create#list-repository-commits",
    "create#post-comment-to-commit",
    "create#protect-a-repository-tag",
    "create#protect-repository-branches",
    "create#protect-repository-branches-1",
    "create#resolve-a-merge-request-thread",
    "create#retrieve-a-blob-from-a-repository",
    "create#retrieve-a-commit",
    "create#retrieve-a-commit-discussion-item",
    "create#retrieve-a-file-from-a-repository",
    "create#retrieve-a-group-repository-storage-move",
    "create#retrieve-a-merge-request-discussion-item",
    "create#retrieve-a-project-alias",
    "create#retrieve-a-protected-branch-or-wildcard-protected-branch",
    "create#retrieve-a-public-key-for-a-remote-mirror",
    "create#retrieve-a-raw-file-from-a-repository",
    "create#retrieve-a-remote-mirror-for-a-project",
    "create#retrieve-a-repository-branch",
    "create#retrieve-a-repository-storage-move-for-a-group",
    "create#retrieve-a-repository-storage-move-for-a-snippet",
    "create#retrieve-a-single-dockerfile-template",
    "create#retrieve-a-single-gitignore-template",
    "create#retrieve-a-single-repository-tag",
    "create#retrieve-a-snippet",
    "create#retrieve-a-snippet-1",
    "create#retrieve-a-snippet-discussion-item",
    "create#retrieve-a-snippet-repository-storage-move",
    "create#retrieve-a-template-of-a-particular-type",
    "create#retrieve-an-epic-discussion-item",
    "create#retrieve-an-issue-discussion-item",
    "create#retrieve-changed-paths",
    "create#retrieve-commit-diff",
    "create#retrieve-commit-signature",
    "create#retrieve-diff-statistics",
    "create#retrieve-diverging-commit-counts",
    "create#retrieve-file-archive-from-a-repository",
    "create#retrieve-file-blame-history-from-a-repository",
    "create#retrieve-mr-approval-settings-for-a-group",
    "create#retrieve-mr-approval-settings-for-a-project",
    "create#retrieve-multiple-blobs-in-a-single-request",
    "create#retrieve-project-pull-mirror-details",
    "create#retrieve-public-signing-key",
    "create#retrieve-raw-blob-content",
    "create#retrieve-snippet-content",
    "create#retrieve-snippet-repository-file-content",
    "create#retrieve-the-push-rules-of-a-group",
    "create#retrieve-the-push-rules-of-a-project",
    "create#retrieve-the-statistics-of-the-last-30-days",
    "create#retrieve-user-agent-details",
    "create#retrieve-user-by-deploy-key-fingerprint",
    "create#retrieve-user-by-ssh-key-fingerprint",
    "create#retrieve-user-by-ssh-key-id",
    "create#retrieve-x509-signature-of-a-tag",
    "create#revert-a-commit",
    "create#schedule-a-repository-storage-move-for-a-snippet",
    "create#schedule-repository-storage-moves-for-all-snippets-on-a-storage-shard",
    "create#set-commit-pipeline-status",
    "create#single-snippet-contents",
    "create#snippet-repository-file-content",
    "create#start-the-pull-mirroring-process-for-a-project",
    "create#unprotect-repository-branches",
    "create#unprotect-repository-branches-1",
    "create#unprotect-repository-tags",
    "create#update-a-commit-thread-note",
    "create#update-a-file-in-a-repository",
    "create#update-a-merge-request-thread-note",
    "create#update-a-protected-branch",
    "create#update-a-protected-branch-1",
    "create#update-a-remote-mirror-in-a-project",
    "create#update-a-snippet",
    "create#update-a-snippet-thread-note",
    "create#update-a-submodule-reference",
    "create#update-an-epic-thread-note",
    "create#update-an-issue-thread-note",
    "create#update-group-mr-approval-settings",
    "create#update-project-mr-approval-settings",
    "create#update-project-pull-mirroring-settings",
    "create#update-push-rules-of-a-group",
    "create#update-push-rules-of-a-project",
    "create#update-snippet",
)

# AC-1: the IDs kept pending — the twelve that commit to, create or rewrite a branch — each with the one index row it
# has. Issue #63 declares the `archive[.format]` path and the group SSH certificate path with two `:id`.
KEPT_PENDING: Dict[str, Tuple[str, str]] = {
    "create#create-repository-branch": ("POST", "/projects/:id/repository/branches"),
    "create#create-a-commit": ("POST", "/projects/:id/repository/commits"),
    "create#cherry-pick-a-commit": ("POST", "/projects/:id/repository/commits/:sha/cherry_pick"),
    "create#revert-a-commit": ("POST", "/projects/:id/repository/commits/:sha/revert"),
    "create#add-changelog-data-to-file": ("POST", "/projects/:id/repository/changelog"),
    "create#create-a-file-in-a-repository": ("POST", "/projects/:id/repository/files/:file_path"),
    "create#update-a-file-in-a-repository": ("PUT", "/projects/:id/repository/files/:file_path"),
    "create#delete-a-file-in-a-repository": ("DELETE", "/projects/:id/repository/files/:file_path"),
    "create#update-a-submodule-reference": ("PUT", "/projects/:id/repository/submodules/:submodule"),
    "create#apply-a-suggestion": ("PUT", "/suggestions/:id/apply"),
    "create#apply-multiple-suggestions": ("PUT", "/suggestions/batch_apply"),
    "create#start-the-pull-mirroring-process-for-a-project": ("POST", "/projects/:id/mirror/pull"),
}
# "Generate changelog data" lists `GET .../changelog` first and `GET .../changelog.txt` second; its base record takes
# the first, and the record after it the second (issue #63, design.md D1, D8).
BASE_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "create#generate-changelog-data": ("GET", "/projects/:id/repository/changelog"),
}
OTHER_ENDPOINT_KEYS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "create#generate-changelog-data": (("GET", "/projects/:id/repository/changelog.txt"),),
}
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(KEPT_PENDING.values())

# rest/create.md: every query or body row of a declared record whose Kind is not SCALAR, and every query member row
# (`range[end]`, its own QUERY Param, AC-2), by record. A body member row (`position[base_sha]`, `files:content`,
# `files[].path`) is no Param. Every other row's Type is `string`, `integer`, `integer (int32)`, `integer or string`,
# `boolean`, `float` or `datetime`, a SCALAR; the `form` rows are the kept records'.
NON_SCALAR_PARAMS: Dict[str, Dict[str, str]] = {
    "create#create-a-commit-thread": {"position": KIND_HASH},
    "create#create-a-merge-request-thread": {"position": KIND_HASH},
    "create#create-a-push-mirror": {"host_keys": KIND_ARRAY},
    "create#create-a-snippet": {"files": KIND_ARRAY_OF_HASHES},
    "create#create-a-snippet-1": {"files": KIND_ARRAY_OF_HASHES},
    "create#get-merge-base": {"refs": KIND_ARRAY},
    "create#protect-a-repository-tag": {"allowed_to_create": KIND_ARRAY},
    "create#protect-repository-branches": {
        "allowed_to_merge": KIND_ARRAY,
        "allowed_to_push": KIND_ARRAY,
        "allowed_to_unprotect": KIND_ARRAY,
    },
    "create#protect-repository-branches-1": {
        "allowed_to_merge": KIND_ARRAY,
        "allowed_to_push": KIND_ARRAY,
        "allowed_to_unprotect": KIND_ARRAY,
    },
    "create#retrieve-file-blame-history-from-a-repository": {
        "range": KIND_HASH,
        "range[end]": KIND_SCALAR,
        "range[start]": KIND_SCALAR,
    },
    # The `files` row reads `array`, its members `files[].path` and `files[].ref`: an array of hashes (AC-3).
    "create#retrieve-multiple-blobs-in-a-single-request": {"files": KIND_ARRAY_OF_HASHES},
    "create#update-a-protected-branch": {
        "allowed_to_push": KIND_ARRAY,
        "allowed_to_merge": KIND_ARRAY,
        "allowed_to_unprotect": KIND_ARRAY,
    },
    "create#update-a-protected-branch-1": {
        "allowed_to_merge": KIND_ARRAY,
        "allowed_to_push": KIND_ARRAY,
        "allowed_to_unprotect": KIND_ARRAY,
    },
    "create#update-a-remote-mirror-in-a-project": {"host_keys": KIND_ARRAY},
    "create#update-a-snippet": {"files": KIND_ARRAY_OF_HASHES},
    "create#update-snippet": {"files": KIND_ARRAY_OF_HASHES},
}

# rest/create.md: the non-path rows of a declared record whose Required reads `yes`, by record, in table order; a
# record with none is not listed. `conditional` ("Update snippet" `files`) is not `yes`; a body member row
# (`files:content`, `position[base_sha]`) is no Param; the `name or context` row of "Set commit pipeline status" is
# no attribute (N skips a name holding ` or `).
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "create#add-a-group-ssh-certificate": ("key", "title"),
    "create#add-a-note-to-a-snippet-thread": ("body",),
    "create#add-a-note-to-an-epic-thread": ("body",),
    "create#add-a-note-to-an-issue-thread": ("body",),
    "create#add-an-instance-ssh-certificate": ("key", "title"),
    "create#add-note-to-a-commit-thread": ("body",),
    "create#add-note-to-a-merge-request-thread": ("body",),
    "create#compare-branches-tags-or-commits": ("from", "to"),
    "create#create-a-commit-thread": ("body",),
    "create#create-a-merge-request-thread": ("body",),
    "create#create-a-new-tag": ("ref", "tag_name"),
    "create#create-a-project-alias": ("name", "project_id"),
    "create#create-a-push-mirror": ("url",),
    "create#create-a-snippet": ("files", "title"),
    "create#create-a-snippet-1": ("title",),
    "create#create-a-snippet-thread": ("body",),
    "create#create-an-epic-thread": ("body",),
    "create#create-an-issue-thread": ("body",),
    "create#create-group-repository-storage-moves-for-a-storage-shard": ("source_storage_name",),
    "create#generate-changelog-data": ("version",),
    "create#get-file-blame-metadata-only": ("ref",),
    "create#get-file-metadata-only": ("ref",),
    "create#get-merge-base": ("refs",),
    "create#post-comment-to-commit": ("note",),
    "create#protect-a-repository-tag": ("name",),
    "create#protect-repository-branches": ("name",),
    "create#protect-repository-branches-1": ("name",),
    "create#resolve-a-merge-request-thread": ("resolved",),
    "create#retrieve-a-file-from-a-repository": ("ref",),
    "create#retrieve-changed-paths": ("from", "to"),
    "create#retrieve-diff-statistics": ("from", "to"),
    "create#retrieve-diverging-commit-counts": ("from", "to"),
    "create#retrieve-file-blame-history-from-a-repository": ("ref",),
    "create#retrieve-multiple-blobs-in-a-single-request": ("files",),
    "create#retrieve-user-by-deploy-key-fingerprint": ("fingerprint",),
    "create#retrieve-user-by-ssh-key-fingerprint": ("fingerprint",),
    "create#schedule-repository-storage-moves-for-all-snippets-on-a-storage-shard": ("source_storage_name",),
    "create#set-commit-pipeline-status": ("state",),
    "create#update-a-snippet-thread-note": ("body",),
    "create#update-an-epic-thread-note": ("body",),
    "create#update-an-issue-thread-note": ("body",),
}

# rest/create.md: every declared `GET` section headed "List", and the four not so headed whose table has a `page` row
# ("Get contributor list", "Retrieve changed paths", "Retrieve commit diff", "Retrieve diff statistics"), with its
# endpoint (AC-4).
LIST_ENDPOINTS: Tuple[Tuple[str, str], ...] = (
    ("create#get-contributor-list", "/projects/:id/repository/contributors"),
    ("create#list-all-commit-comments", "/projects/:id/repository/commits/:sha/comments"),
    ("create#list-all-commit-discussion-items", "/projects/:id/repository/commits/:commit_id/discussions"),
    ("create#list-all-commit-discussions", "/projects/:id/repository/commits/:sha/discussions"),
    ("create#list-all-dockerfile-templates", "/templates/dockerfiles"),
    ("create#list-all-epic-discussion-items", "/groups/:id/epics/:epic_id/discussions"),
    ("create#list-all-gitignore-templates", "/templates/gitignores"),
    ("create#list-all-group-repository-storage-moves", "/group_repository_storage_moves"),
    ("create#list-all-group-ssh-certificates", "/groups/:id/ssh_certificates"),
    ("create#list-all-instance-ssh-certificates", "/admin/ssh_certificates"),
    ("create#list-all-issue-discussion-items", "/projects/:id/issues/:issue_iid/discussions"),
    (
        "create#list-all-merge-request-discussion-items",
        "/projects/:id/merge_requests/:merge_request_iid/discussions",
    ),
    ("create#list-all-project-aliases", "/project_aliases"),
    ("create#list-all-project-repository-tags", "/projects/:id/repository/tags"),
    ("create#list-all-public-snippets", "/snippets/public"),
    ("create#list-all-references-a-commit-is-pushed-to", "/projects/:id/repository/commits/:sha/refs"),
    ("create#list-all-remote-mirrors-for-a-project", "/projects/:id/remote_mirrors"),
    ("create#list-all-repository-branches", "/projects/:id/repository/branches"),
    ("create#list-all-repository-storage-moves-for-a-group", "/groups/:group_id/repository_storage_moves"),
    ("create#list-all-repository-storage-moves-for-a-snippet", "/snippets/:snippet_id/repository_storage_moves"),
    ("create#list-all-repository-trees-in-a-project", "/projects/:id/repository/tree"),
    ("create#list-all-snippet-discussion-items", "/projects/:id/snippets/:snippet_id/discussions"),
    ("create#list-all-snippet-repository-storage-moves", "/snippet_repository_storage_moves"),
    ("create#list-all-snippets", "/snippets/all"),
    ("create#list-all-snippets-for-a-project", "/projects/:id/snippets"),
    ("create#list-all-snippets-for-current-user", "/snippets"),
    ("create#list-all-templates-of-a-particular-type", "/projects/:id/templates/:type"),
    ("create#list-commit-statuses", "/projects/:id/repository/commits/:sha/statuses"),
    ("create#list-merge-requests-associated-with-a-commit", "/projects/:id/repository/commits/:sha/merge_requests"),
    ("create#list-protected-branches", "/groups/:id/protected_branches"),
    ("create#list-protected-branches-1", "/projects/:id/protected_branches"),
    ("create#list-protected-tags", "/projects/:id/protected_tags"),
    ("create#list-repository-commits", "/projects/:id/repository/commits"),
    ("create#retrieve-changed-paths", "/projects/:id/repository/changed_paths"),
    ("create#retrieve-commit-diff", "/projects/:id/repository/commits/:sha/diff"),
    ("create#retrieve-diff-statistics", "/projects/:id/repository/diff_stats"),
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
    """Import ``gitlab_api.<name>`` (``families.create`` for the family) inside a test, after asserting its file."""
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


def endpoints_by_id(*, records: Sequence[Any]) -> Dict[str, Tuple[Tuple[str, str], ...]]:
    """``{operation_id: ((method, path), ...)}`` over ``records``, each ID's keys in declaration order."""
    declared: Dict[str, List[Tuple[str, str]]] = {}
    for record in records:
        declared.setdefault(record.operation_id, []).append((record.method, record.path))
    return {operation_id: tuple(keys) for operation_id, keys in declared.items()}


def repeated_keys(*, endpoints: Mapping[str, Sequence[Tuple[str, str]]]) -> List[Tuple[str, Tuple[str, str]]]:
    """Each ``(operation_id, key)`` that ``endpoints`` holds more than once for its ID, sorted."""
    return sorted(
        {(operation_id, key) for operation_id, keys in endpoints.items() for key in keys if list(keys).count(key) > 1}
    )


def archive_params() -> List[Any]:
    """One case per entry of ``ARCHIVE_FORMATS``, with its ``--path format=`` text and the URL it is sent to, and one
    case giving no format; each named by its format."""
    cases = [
        pytest.param(
            [OPTION_PATH, f"{PATH_FORMAT}{ASSIGNED}{archive_format}"],
            f"{ARCHIVE_URL}{SUFFIX_SEPARATOR}{archive_format}",
            id=archive_format,
        )
        for archive_format in ARCHIVE_FORMATS
    ]
    cases.append(pytest.param([], ARCHIVE_URL, id=NO_FORMAT_CASE))
    return cases


def is_member(*, name: str) -> bool:
    """Whether a ``Param`` name is a member row's (``range[end]``): it holds ``[`` or ``:``."""
    return any(mark in name for mark in MEMBER_MARKS)


def typed_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[str, Dict[str, str]]:
    """``{operation_id: {name: Kind name}}`` of every ``Param`` that is not SCALAR or is a member, over the records
    with any."""
    typed = {
        record.operation_id: {
            param.name: param.kind.name
            for param in record.params
            if param.kind is not registry.Kind.SCALAR or is_member(name=param.name)
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
    """One case per entry of ``LIST_ENDPOINTS``, named by its anchor."""
    return [
        pytest.param(operation_id, path, id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id, path in LIST_ENDPOINTS
    ]


# --- AC-1: what stays pending ---------------------------------------------------------------------------------------


def test_only_the_kept_keys_are_pending() -> None:
    """AC-1, UB-2, issue #63 AC-1.1, AC-1.3 (design.md D9): ``PENDING`` is the kept IDs' keys, and ``OPERATIONS``
    declares every index Reference of the family but the kept IDs, each key of an ID once; the changelog's ID has its
    base record first and then its second endpoint."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "create.PENDING is not the keys AC-1 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )
    endpoints = endpoints_by_id(records=family.OPERATIONS)
    repeated = repeated_keys(endpoints=endpoints)
    assert not repeated, f"create.OPERATIONS declares these keys of one ID more than once: {repeated}"
    expected = frozenset(INDEX_REFERENCES) - frozenset(KEPT_PENDING)
    assert frozenset(endpoints) == expected, "create.OPERATIONS does not declare the family's References (AC-1):\n" + (
        set_difference(declared=frozenset(endpoints), expected=expected)
    )
    bases = {operation_id: keys[0] for operation_id, keys in endpoints.items() if operation_id in BASE_ENDPOINTS}
    assert bases == BASE_ENDPOINTS, "the section's first record is not its base record (issue #63 D1):\n" + (
        mapping_difference(declared=bases, expected=BASE_ENDPOINTS)
    )
    others = {operation_id: keys[1:] for operation_id, keys in endpoints.items() if len(keys) > 1}
    assert others == OTHER_ENDPOINT_KEYS, "the records after a base record are not its section's other endpoints:\n" + (
        mapping_difference(declared=others, expected=OTHER_ENDPOINT_KEYS)
    )


# --- AC-2, AC-3: kinds, members, required attributes, bodies --------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-2, AC-3: the ``Param``s that are not ``SCALAR`` or are query members carry their row's ``Kind``; the
    ``Param``s declared ``required`` are exactly the non-path rows whose Required reads ``yes``; every record has a
    JSON body and no ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = typed_params(records=records, registry=registry)
    assert typed == NON_SCALAR_PARAMS, "the non-SCALAR and member Params are not the sections' (AC-2, AC-3):\n" + (
        mapping_difference(declared=typed, expected=NON_SCALAR_PARAMS)
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert required == expected_required, "required=True is not exactly the Required `yes` rows (AC-3):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    misbodied = [
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    ]
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-3): {misbodied}"


# --- AC-4, AC-6: the list records -----------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-4: the ``Paging.OFFSET`` records are exactly ``LIST_ENDPOINTS``' IDs, and no record is ``Paging.KEYSET``."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    offset = frozenset(record.operation_id for record in family.OPERATIONS if record.paging is registry.Paging.OFFSET)
    expected = frozenset(operation_id for operation_id, _ in LIST_ENDPOINTS)
    assert offset == expected, "the Paging.OFFSET records are not the sections' lists (AC-4):\n" + set_difference(
        declared=offset, expected=expected
    )
    keyset = sorted(record.operation_id for record in family.OPERATIONS if record.paging is registry.Paging.KEYSET)
    assert keyset == [], f"no create list is keyset-only (conventions.md 'Keyset-based'), yet KEYSET: {keyset}"


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_page(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6: ``call <id> --path NAME=VALUE ...`` against two pages, the second named by the first's ``x-next-page``,
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
        f"one JSON array of both items, in page order, as print_json writes it (AC-6):\n{captured.out}"
    )


# --- AC-7: a raw download -------------------------------------------------------------------------------------------


def test_a_raw_download_is_written_unchanged(
    project: Path, fake_gitlab: Any, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """AC-7: ``call create#retrieve-raw-blob-content --path sha=...``, answered with bytes that are not UTF-8 as
    ``application/octet-stream``, sends one ``GET`` to the configured project's blob, exits 0 and writes the bytes
    unchanged, no line end added."""
    argv = [OP_RETRIEVE_RAW_BLOB, OPTION_PATH, f"{PATH_SHA}{ASSIGNED}{BLOB_SHA}"]
    fake_gitlab.script(
        method=METHOD_GET,
        url=RAW_BLOB_URL,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
        body=NOT_UTF8_BYTES,
    )
    code = run_call(root=project, argv=argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, RAW_BLOB_URL)], "one GET to the blob's raw path, id the project"
    assert captured.out == NOT_UTF8_BYTES, (
        f"the body's bytes unchanged, no line end added (AC-7); standard output: {captured.out!r}"
    )


# --- Issue #63 AC-3.1, AC-3.2: one value per place ------------------------------------------------------------------


def test_each_id_of_the_certificate_path_takes_its_place(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #63 AC-3.1, AC-3.2, AC-8.3: ``call create#delete-a-group-ssh-certificate --path id=7 --path id=12345``
    sends one ``DELETE`` to ``/groups/7/ssh_certificates/12345``, the configured token in its header."""
    fake_gitlab.script(method=METHOD_DELETE, url=SSH_CERTIFICATE_URL, status=STATUS_NO_CONTENT)
    argv = [
        OP_DELETE_GROUP_SSH_CERTIFICATE,
        *(part for value in SSH_CERTIFICATE_ID_VALUES for part in (OPTION_PATH, value)),
    ]
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_DELETE, SSH_CERTIFICATE_URL)], (
        "one DELETE, the group's id at the first place and the certificate's at the second (AC-3.2)"
    )
    assert fake_gitlab.requests[0].header(name=HEADER_PRIVATE_TOKEN) == TOKEN, (
        "the configured token travels in its one header"
    )


# --- Issue #63 AC-4.1: the archive format ---------------------------------------------------------------------------


@pytest.mark.parametrize(argnames=("format_options", "url"), argvalues=archive_params())
def test_the_archive_format_is_sent_as_its_suffix(
    format_options: List[str], url: str, project: Path, fake_gitlab: Any, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """Issue #63 AC-4.1, AC-8.3: ``call create#retrieve-file-archive-from-a-repository --path format=<format>`` sends
    one ``GET`` to the configured project's ``archive.<format>``, and with no ``--path format`` to its ``archive``; no
    URL holds ``[``, and the configured token travels in its header."""
    fake_gitlab.script(
        method=METHOD_GET,
        url=url,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
        body=ARCHIVE_BYTES,
    )
    argv = [OP_RETRIEVE_FILE_ARCHIVE, *format_options]
    code = run_call(root=project, argv=argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, url)], "one GET, the format written as the path's suffix (AC-4.1)"
    unexpanded = [request.url for request in fake_gitlab.requests if UNEXPANDED_MARK in request.url]
    assert unexpanded == [], f"no URL holds the [.format] template (AC-4.1): {unexpanded}"
    assert fake_gitlab.requests[0].header(name=HEADER_PRIVATE_TOKEN) == TOKEN, (
        "the configured token travels in its one header"
    )
