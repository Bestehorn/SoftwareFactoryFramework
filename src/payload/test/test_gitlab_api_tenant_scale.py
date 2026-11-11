"""Tests for ``gitlab_api/families/tenant_scale.py``, the ``tenant-scale`` endpoint family of the GitLab wrapper (issue
#38, the remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5, AC-7 and AC-8).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/tenant-scale.md``) and
``docs/api-reference/gitlab/rest/tenant-scale.md`` (each section's endpoints, its heading, and the ``In``, ``Type``,
``Required`` and ``Notes`` columns of its ``| Attribute | In | Type |`` table). What is pinned:

- AC-1, UB-2 (as issue #63 design.md D9 restates them): ``OPERATIONS``, each ID's first record as
  ``{operation_id: (method, path)}``, each key of an ID once, is ``RECORDS``: every Reference of the family, each with
  its section's endpoint, of several the ``/projects/:id/...`` one, the four ``/groups/:id/manage/..._access_tokens/
  :id...`` IDs among them (issue #63 AC-1.1); each Invitations section then has a record for its ``/groups/:id/...``
  endpoint (``OTHER_ENDPOINT_KEYS``). The three References whose keys V's ``key_families`` gives
  ``developer_experience`` (DL-003: ``GET /projects`` and ``DELETE /projects/:id/share/:group_id`` are also carried by
  ``rest/developer-experience.md`` rows) are declared there, not here: ``tenant-scale#list-all-projects``,
  ``#list-all-projects-assigned-to-a-topic`` and ``#delete-a-shared-project-link-in-a-group``;
- AC-2: ``PENDING`` is empty: the keys it held are records (issue #63 AC-1.1, AC-1.3);
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``FILE`` for a Notes cell beginning "file upload",
  ``ARRAY_OF_HASHES`` for ``array of object``, ``HASH`` for ``hash`` or ``object``, ``ARRAY`` for any other Type holding
  ``array``); the ``required`` ``Param``s, exactly the query, body and form rows whose Required reads ``yes``; a JSON
  body and no ``fixed`` pairs on every record;
- AC-5: the ``Paging.OFFSET`` records are exactly the ``GET`` sections headed "List" or with a ``page`` row, every other
  record ``Paging.NONE`` (none ``KEYSET``);
- AC-7: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``);
- AC-8: "Download snapshot of a Git repository", answered with bytes that are not UTF-8 as
  ``application/octet-stream``, exits 0 and writes those bytes unchanged (read with ``capsysbinary``);
- issue #63 AC-3.1, AC-3.2, AC-8.3: each of the four token records, called with ``--path id=7 --path id=self``, sends
  one request whose path holds ``7`` at the group's place and ``self`` at the token's.

The names and ``In`` of every ``Param`` (AC-3) and one call of every record (AC-6) are proven by
``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_tenant_scale.py`` (no network).
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
WRAPPER_MODULE = "gitlab_wrapper_tenant_scale_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.tenant_scale"
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
TOKEN = "glpat-gitlab-api-tenant-scale-test"  # pragma: allowlist secret
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

# A path parameter as operations-index.md and rest/tenant-scale.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The synthetic item each page holds; the wrapper prints every item as the host serves it.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind`, `registry.BodyFormat` and `registry.Paging` member names the tables hold.
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
KIND_FILE = "FILE"
BODY_JSON = "JSON"
NO_FIXED: Tuple[Tuple[str, str], ...] = ()
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"

# AC-8: "Download snapshot of a Git repository" (`GET /projects/:id/snapshot`), its `id` the configured project; the
# body holds bytes that are no UTF-8 sequence.
OP_DOWNLOAD_SNAPSHOT = "tenant-scale#download-snapshot-of-a-git-repository"
SNAPSHOT_URL = f"{REST_BASE}/projects/{PROJECT_ID}/snapshot"
NOT_UTF8_BYTES = b"snapshot.git/\x00\x00\x00\xff\xfe\xfd\x80"

# Issue #63 AC-3.1, AC-3.2: each record whose path holds `:id` twice (rest/tenant-scale.md "Revoke ..." and "Rotate ...
# for an enterprise user"), its two `id` values given in path order — the group `7`, then the token `self` (the
# sections' Values) — and the method and path it is sent with. A revoke is answered `204`, a rotation with the token.
POSITIONAL_ID_VALUES: Tuple[str, ...] = ("id=7", "id=self")
TOKEN_PATH_CASES: Tuple[Tuple[str, str, str], ...] = (
    (
        "tenant-scale#revoke-a-personal-access-token-for-an-enterprise-user",
        "DELETE",
        "/groups/7/manage/personal_access_tokens/self",
    ),
    (
        "tenant-scale#revoke-a-group-or-project-access-token-for-an-enterprise-user",
        "DELETE",
        "/groups/7/manage/resource_access_tokens/self",
    ),
    (
        "tenant-scale#rotate-a-personal-access-token-for-an-enterprise-user",
        "POST",
        "/groups/7/manage/personal_access_tokens/self/rotate",
    ),
    (
        "tenant-scale#rotate-a-group-or-project-access-token-for-an-enterprise-user",
        "POST",
        "/groups/7/manage/resource_access_tokens/self/rotate",
    ),
)
ROTATED_TOKEN_ANSWER: Dict[str, Any] = {FIELD_ID: 1}

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# AC-1: every Reference of an operations-index.md row linking rest/tenant-scale.md, written `tenant-scale#<anchor>`,
# whose record this family declares, with its section's endpoint, in the page's section order: its first record, the
# base record. Of the Invitations sections, each listing `/groups/:id/...` then `/projects/:id/...`, the base record
# takes the `/projects/:id/...` one.
# "Schedule a group for deletion" and "Delete a group permanently" share `DELETE /groups/:id`; "List all groups" and
# "Search for a group" share `GET /groups`; "Update a project" and "Upload a project avatar" share `PUT /projects/:id`.
RECORDS: Dict[str, Tuple[str, str]] = {
    # Group badges API
    "tenant-scale#list-all-group-badges": ("GET", "/groups/:id/badges"),
    "tenant-scale#retrieve-a-group-badge": ("GET", "/groups/:id/badges/:badge_id"),
    "tenant-scale#create-a-group-badge": ("POST", "/groups/:id/badges"),
    "tenant-scale#update-a-group-badge": ("PUT", "/groups/:id/badges/:badge_id"),
    "tenant-scale#delete-a-group-badge": ("DELETE", "/groups/:id/badges/:badge_id"),
    "tenant-scale#retrieve-a-group-badge-preview": ("GET", "/groups/:id/badges/render"),
    # Groups API
    "tenant-scale#retrieve-a-group": ("GET", "/groups/:id"),
    "tenant-scale#list-all-groups": ("GET", "/groups"),
    "tenant-scale#search-for-a-group": ("GET", "/groups"),
    "tenant-scale#list-projects": ("GET", "/groups/:id/projects"),
    "tenant-scale#list-shared-projects": ("GET", "/groups/:id/projects/shared"),
    "tenant-scale#delete-a-shared-project": ("DELETE", "/groups/:id/shared_projects/:project_id"),
    "tenant-scale#list-all-saml-users": ("GET", "/groups/:id/saml_users"),
    "tenant-scale#list-provisioned-users": ("GET", "/groups/:id/provisioned_users"),
    "tenant-scale#list-subgroups": ("GET", "/groups/:id/subgroups"),
    "tenant-scale#list-descendant-groups": ("GET", "/groups/:id/descendant_groups"),
    "tenant-scale#list-shared-groups": ("GET", "/groups/:id/groups/shared"),
    "tenant-scale#list-invited-groups": ("GET", "/groups/:id/invited_groups"),
    "tenant-scale#create-a-group": ("POST", "/groups"),
    "tenant-scale#schedule-a-group-for-deletion": ("DELETE", "/groups/:id"),
    "tenant-scale#delete-a-group-permanently": ("DELETE", "/groups/:id"),
    "tenant-scale#restore-a-group-marked-for-deletion": ("POST", "/groups/:id/restore"),
    "tenant-scale#archive-a-group": ("POST", "/groups/:id/archive"),
    "tenant-scale#unarchive-a-group": ("POST", "/groups/:id/unarchive"),
    "tenant-scale#transfer-a-group": ("POST", "/groups/:id/transfer"),
    "tenant-scale#list-all-locations-available-for-group-transfer": ("GET", "/groups/:id/transfer_locations"),
    "tenant-scale#transfer-a-project-to-a-group": ("POST", "/groups/:id/projects/:project_id"),
    "tenant-scale#create-a-group-invitation": ("POST", "/groups/:id/share"),
    "tenant-scale#delete-a-group-invitation": ("DELETE", "/groups/:id/share/:group_id"),
    "tenant-scale#update-group-attributes": ("PUT", "/groups/:id"),
    "tenant-scale#download-a-group-avatar": ("GET", "/groups/:id/avatar"),
    "tenant-scale#sync-a-group-with-ldap": ("POST", "/groups/:id/ldap_sync"),
    "tenant-scale#list-all-personal-access-tokens-for-a-group": ("GET", "/groups/:id/manage/personal_access_tokens"),
    "tenant-scale#list-all-group-and-project-access-tokens-for-a-group": (
        "GET",
        "/groups/:id/manage/resource_access_tokens",
    ),
    "tenant-scale#list-all-ssh-keys-for-a-group": ("GET", "/groups/:id/manage/ssh_keys"),
    # Issue #63 AC-3.1: the four IDs whose path holds `:id` twice, the group's and the token's.
    "tenant-scale#revoke-a-personal-access-token-for-an-enterprise-user": (
        "DELETE",
        "/groups/:id/manage/personal_access_tokens/:id",
    ),
    "tenant-scale#revoke-a-group-or-project-access-token-for-an-enterprise-user": (
        "DELETE",
        "/groups/:id/manage/resource_access_tokens/:id",
    ),
    "tenant-scale#delete-an-ssh-key-for-an-enterprise-user": ("DELETE", "/groups/:id/manage/ssh_keys/:key_id"),
    "tenant-scale#rotate-a-personal-access-token-for-an-enterprise-user": (
        "POST",
        "/groups/:id/manage/personal_access_tokens/:id/rotate",
    ),
    "tenant-scale#rotate-a-group-or-project-access-token-for-an-enterprise-user": (
        "POST",
        "/groups/:id/manage/resource_access_tokens/:id/rotate",
    ),
    # Invitations API
    "tenant-scale#add-a-member-to-a-group-or-project": ("POST", "/projects/:id/invitations"),
    "tenant-scale#list-all-pending-invitations-for-a-group-or-project": ("GET", "/projects/:id/invitations"),
    "tenant-scale#update-an-invitation-to-a-group-or-project": ("PUT", "/projects/:id/invitations/:email"),
    "tenant-scale#delete-an-invitation-to-a-group-or-project": ("DELETE", "/projects/:id/invitations/:email"),
    # Namespaces API
    "tenant-scale#list-all-namespaces": ("GET", "/namespaces"),
    "tenant-scale#retrieve-namespace-details": ("GET", "/namespaces/:id"),
    "tenant-scale#verify-namespace-availability": ("GET", "/namespaces/:namespace/exists"),
    # Organizations API
    "tenant-scale#create-an-organization": ("POST", "/organizations"),
    "tenant-scale#restore-an-organization": ("POST", "/organizations/:id/restore"),
    "tenant-scale#transfer-users-to-an-organization": ("POST", "/organizations/:id/transfer_users"),
    # Project badges API
    "tenant-scale#list-all-badges-of-a-project": ("GET", "/projects/:id/badges"),
    "tenant-scale#retrieve-a-badge-of-a-project": ("GET", "/projects/:id/badges/:badge_id"),
    "tenant-scale#create-a-badge-for-a-project": ("POST", "/projects/:id/badges"),
    "tenant-scale#update-a-badge-of-a-project": ("PUT", "/projects/:id/badges/:badge_id"),
    "tenant-scale#delete-a-badge-from-a-project": ("DELETE", "/projects/:id/badges/:badge_id"),
    "tenant-scale#preview-a-badge-from-a-project": ("GET", "/projects/:id/badges/render"),
    # Project forks API
    "tenant-scale#create-a-fork-of-a-project": ("POST", "/projects/:id/fork"),
    "tenant-scale#list-all-forks-of-a-project": ("GET", "/projects/:id/forks"),
    "tenant-scale#create-a-fork-relationship": ("POST", "/projects/:id/fork/:forked_from_id"),
    "tenant-scale#delete-a-fork-relationship": ("DELETE", "/projects/:id/fork"),
    # Project repository storage moves API
    "tenant-scale#list-all-project-repository-storage-moves": ("GET", "/project_repository_storage_moves"),
    "tenant-scale#list-all-repository-storage-moves-for-a-project": (
        "GET",
        "/projects/:project_id/repository_storage_moves",
    ),
    "tenant-scale#retrieve-a-project-repository-storage-move": (
        "GET",
        "/project_repository_storage_moves/:repository_storage_id",
    ),
    "tenant-scale#retrieve-a-repository-storage-move-for-a-project": (
        "GET",
        "/projects/:project_id/repository_storage_moves/:repository_storage_id",
    ),
    "tenant-scale#create-a-repository-storage-move-for-a-project": (
        "POST",
        "/projects/:project_id/repository_storage_moves",
    ),
    "tenant-scale#create-repository-storage-moves-for-all-projects-on-a-storage-shard": (
        "POST",
        "/project_repository_storage_moves",
    ),
    # Project starring API
    "tenant-scale#list-projects-starred-by-a-user": ("GET", "/users/:user_id/starred_projects"),
    "tenant-scale#list-users-who-starred-a-project": ("GET", "/projects/:id/starrers"),
    "tenant-scale#star-a-project": ("POST", "/projects/:id/star"),
    "tenant-scale#unstar-a-project": ("POST", "/projects/:id/unstar"),
    # Projects API
    "tenant-scale#retrieve-a-project": ("GET", "/projects/:id"),
    "tenant-scale#list-all-personal-projects-for-a-user": ("GET", "/users/:user_id/projects"),
    "tenant-scale#list-all-projects-contributions-for-a-user": ("GET", "/users/:user_id/contributed_projects"),
    "tenant-scale#list-all-members-of-a-project": ("GET", "/projects/:id/users"),
    "tenant-scale#list-all-ancestor-groups": ("GET", "/projects/:id/groups"),
    "tenant-scale#list-all-groups-available-to-invite-to-a-project": ("GET", "/projects/:id/share_locations"),
    "tenant-scale#list-all-invited-groups-in-a-project": ("GET", "/projects/:id/invited_groups"),
    "tenant-scale#retrieve-programming-language-usage-information": ("GET", "/projects/:id/languages"),
    "tenant-scale#create-a-project": ("POST", "/projects"),
    "tenant-scale#create-a-project-for-a-user": ("POST", "/projects/user/:user_id"),
    "tenant-scale#update-a-project": ("PUT", "/projects/:id"),
    "tenant-scale#import-members": ("POST", "/projects/:id/import_project_members/:project_id"),
    "tenant-scale#archive-a-project": ("POST", "/projects/:id/archive"),
    "tenant-scale#unarchive-a-project": ("POST", "/projects/:id/unarchive"),
    "tenant-scale#delete-a-project": ("DELETE", "/projects/:id"),
    "tenant-scale#restore-a-project-marked-for-deletion": ("POST", "/projects/:id/restore"),
    "tenant-scale#transfer-a-project-to-a-new-namespace": ("PUT", "/projects/:id/transfer"),
    "tenant-scale#list-groups-available-for-project-transfer": ("GET", "/projects/:id/transfer_locations"),
    "tenant-scale#upload-a-project-avatar": ("PUT", "/projects/:id"),
    "tenant-scale#download-a-project-avatar": ("GET", "/projects/:id/avatar"),
    "tenant-scale#share-a-project-with-a-group": ("POST", "/projects/:id/share"),
    "tenant-scale#start-the-housekeeping-task-for-a-project": ("POST", "/projects/:id/housekeeping"),
    "tenant-scale#real-time-security-scan": ("POST", "/projects/:id/security_scans/sast/scan"),
    "tenant-scale#download-snapshot-of-a-git-repository": ("GET", "/projects/:id/snapshot"),
    "tenant-scale#retrieve-the-path-to-repository-storage": ("GET", "/projects/:id/storage"),
    # Topics API
    "tenant-scale#list-all-topics": ("GET", "/topics"),
    "tenant-scale#retrieve-a-topic": ("GET", "/topics/:id"),
    "tenant-scale#create-a-project-topic": ("POST", "/topics"),
    "tenant-scale#update-a-project-topic": ("PUT", "/topics/:id"),
    "tenant-scale#delete-a-project-topic": ("DELETE", "/topics/:id"),
    "tenant-scale#merge-topics": ("POST", "/topics/merge"),
}

# The endpoint each Invitations section lists before the `/projects/:id/...` one its base record takes: the one record
# after the base record of its ID (issue #63, design.md D1, D8).
OTHER_ENDPOINT_KEYS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "tenant-scale#add-a-member-to-a-group-or-project": (("POST", "/groups/:id/invitations"),),
    "tenant-scale#list-all-pending-invitations-for-a-group-or-project": (("GET", "/groups/:id/invitations"),),
    "tenant-scale#update-an-invitation-to-a-group-or-project": (("PUT", "/groups/:id/invitations/:email"),),
    "tenant-scale#delete-an-invitation-to-a-group-or-project": (("DELETE", "/groups/:id/invitations/:email"),),
}
# AC-2 as issue #63 AC-1.1 restates it: nothing of the family stays pending.
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset()

# AC-4: every query, body or form row of a declared record whose Kind is not SCALAR, as `(operation_id, name)`, in the
# page's order. `FILE`: the `avatar` rows, whose Notes read "file upload (multipart/form-data)" (Type `mixed`, `file`,
# or `string` in "Upload a project avatar"); `ARRAY_OF_HASHES`: `array of object`; `HASH`: `hash`, `object`; `ARRAY`:
# `array`, `array of integer(s)`, `array of string(s)`, `integer array`. Every other row's Type is `string`, `integer`,
# `integer (int32)`, `integer or string`, `boolean`, `boolean/string`, `date`, `datetime` or a dated `string`, a SCALAR
# (issue #63: the rotations' one non-path row, `expires_at`, is a `date`; the revokes have none).
NON_SCALAR_KINDS: Dict[Tuple[str, str], str] = {
    ("tenant-scale#list-all-groups", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#search-for-a-group", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#list-subgroups", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#list-descendant-groups", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#list-shared-groups", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#list-invited-groups", "relation"): KIND_ARRAY,
    ("tenant-scale#create-a-group", "avatar"): KIND_FILE,
    ("tenant-scale#create-a-group", "default_branch_protection_defaults"): KIND_HASH,
    ("tenant-scale#create-a-group", "ai_settings_attributes"): KIND_HASH,
    ("tenant-scale#create-a-group", "foundational_agents_statuses"): KIND_ARRAY_OF_HASHES,
    ("tenant-scale#update-group-attributes", "avatar"): KIND_FILE,
    ("tenant-scale#update-group-attributes", "default_branch_protection_defaults"): KIND_HASH,
    ("tenant-scale#update-group-attributes", "unique_project_download_limit_allowlist"): KIND_ARRAY,
    ("tenant-scale#update-group-attributes", "unique_project_download_limit_alertlist"): KIND_ARRAY,
    ("tenant-scale#update-group-attributes", "ai_settings_attributes"): KIND_HASH,
    ("tenant-scale#update-group-attributes", "foundational_agents_statuses"): KIND_ARRAY_OF_HASHES,
    ("tenant-scale#update-group-attributes", "enabled_foundational_flows"): KIND_ARRAY,
    ("tenant-scale#update-group-attributes", "duo_namespace_access_rules"): KIND_ARRAY_OF_HASHES,
    ("tenant-scale#create-an-organization", "avatar"): KIND_FILE,
    ("tenant-scale#transfer-users-to-an-organization", "user_ids"): KIND_ARRAY,
    ("tenant-scale#list-all-forks-of-a-project", "topic"): KIND_ARRAY,
    ("tenant-scale#list-projects-starred-by-a-user", "topic"): KIND_ARRAY,
    ("tenant-scale#list-all-personal-projects-for-a-user", "topic"): KIND_ARRAY,
    ("tenant-scale#list-all-members-of-a-project", "skip_users"): KIND_ARRAY,
    ("tenant-scale#list-all-ancestor-groups", "skip_groups"): KIND_ARRAY,
    ("tenant-scale#list-all-invited-groups-in-a-project", "relation"): KIND_ARRAY,
    ("tenant-scale#create-a-project", "avatar"): KIND_FILE,
    ("tenant-scale#create-a-project", "container_expiration_policy_attributes"): KIND_HASH,
    ("tenant-scale#create-a-project", "tag_list"): KIND_ARRAY,
    ("tenant-scale#create-a-project", "topics"): KIND_ARRAY,
    ("tenant-scale#create-a-project-for-a-user", "avatar"): KIND_FILE,
    ("tenant-scale#create-a-project-for-a-user", "tag_list"): KIND_ARRAY,
    ("tenant-scale#create-a-project-for-a-user", "topics"): KIND_ARRAY,
    ("tenant-scale#create-a-project-for-a-user", "container_expiration_policy_attributes"): KIND_HASH,
    ("tenant-scale#update-a-project", "avatar"): KIND_FILE,
    ("tenant-scale#update-a-project", "ci_id_token_sub_claim_components"): KIND_ARRAY,
    ("tenant-scale#update-a-project", "container_expiration_policy_attributes"): KIND_HASH,
    ("tenant-scale#update-a-project", "tag_list"): KIND_ARRAY,
    ("tenant-scale#update-a-project", "topics"): KIND_ARRAY,
    ("tenant-scale#upload-a-project-avatar", "avatar"): KIND_FILE,
    ("tenant-scale#upload-a-project-avatar", "container_expiration_policy_attributes"): KIND_HASH,
    ("tenant-scale#upload-a-project-avatar", "tag_list"): KIND_ARRAY,
    ("tenant-scale#upload-a-project-avatar", "topics"): KIND_ARRAY,
    ("tenant-scale#upload-a-project-avatar", "ci_id_token_sub_claim_components"): KIND_ARRAY,
    ("tenant-scale#create-a-project-topic", "avatar"): KIND_FILE,
    ("tenant-scale#update-a-project-topic", "avatar"): KIND_FILE,
}

# AC-4: the query, body and form rows of a declared record whose Required reads `yes`, by record, in table order; a
# record with none is not listed. A path row is no Param; `conditional` ("Schedule a group for deletion" `full_path`)
# is not `yes`; the four token records of issue #63 have no such row.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "tenant-scale#create-a-group-badge": ("link_url", "image_url"),
    "tenant-scale#retrieve-a-group-badge-preview": ("link_url", "image_url"),
    "tenant-scale#create-a-group": ("name", "path"),
    "tenant-scale#delete-a-group-permanently": ("full_path", "permanently_remove"),
    "tenant-scale#create-a-group-invitation": ("group_id", "group_access"),
    "tenant-scale#add-a-member-to-a-group-or-project": ("email", "user_id", "access_level"),
    "tenant-scale#create-an-organization": ("name", "path"),
    "tenant-scale#transfer-users-to-an-organization": ("user_ids",),
    "tenant-scale#create-a-badge-for-a-project": ("link_url", "image_url"),
    "tenant-scale#preview-a-badge-from-a-project": ("link_url", "image_url"),
    "tenant-scale#create-repository-storage-moves-for-all-projects-on-a-storage-shard": ("source_storage_name",),
    "tenant-scale#create-a-project": ("name", "path"),
    "tenant-scale#create-a-project-for-a-user": ("name",),
    "tenant-scale#transfer-a-project-to-a-new-namespace": ("namespace",),
    "tenant-scale#upload-a-project-avatar": ("avatar",),
    "tenant-scale#share-a-project-with-a-group": ("group_access", "group_id"),
    "tenant-scale#create-a-project-topic": ("name", "title"),
    "tenant-scale#merge-topics": ("source_topic_id", "target_topic_id"),
}

# AC-5: every declared `GET` section headed "List" (with or without a `page` row: the personal and the group and
# project access token lists, the SSH key list, the groups available to invite and both repository storage move lists
# have none) and the one not so headed whose table has a `page` row ("Search for a group"), in the page's order. Its
# path is RECORDS'.
LIST_RECORDS: Tuple[str, ...] = (
    "tenant-scale#list-all-group-badges",
    "tenant-scale#list-all-groups",
    "tenant-scale#search-for-a-group",
    "tenant-scale#list-projects",
    "tenant-scale#list-shared-projects",
    "tenant-scale#list-all-saml-users",
    "tenant-scale#list-provisioned-users",
    "tenant-scale#list-subgroups",
    "tenant-scale#list-descendant-groups",
    "tenant-scale#list-shared-groups",
    "tenant-scale#list-invited-groups",
    "tenant-scale#list-all-locations-available-for-group-transfer",
    "tenant-scale#list-all-personal-access-tokens-for-a-group",
    "tenant-scale#list-all-group-and-project-access-tokens-for-a-group",
    "tenant-scale#list-all-ssh-keys-for-a-group",
    "tenant-scale#list-all-pending-invitations-for-a-group-or-project",
    "tenant-scale#list-all-namespaces",
    "tenant-scale#list-all-badges-of-a-project",
    "tenant-scale#list-all-forks-of-a-project",
    "tenant-scale#list-all-project-repository-storage-moves",
    "tenant-scale#list-all-repository-storage-moves-for-a-project",
    "tenant-scale#list-projects-starred-by-a-user",
    "tenant-scale#list-users-who-starred-a-project",
    "tenant-scale#list-all-personal-projects-for-a-user",
    "tenant-scale#list-all-projects-contributions-for-a-user",
    "tenant-scale#list-all-members-of-a-project",
    "tenant-scale#list-all-ancestor-groups",
    "tenant-scale#list-all-groups-available-to-invite-to-a-project",
    "tenant-scale#list-all-invited-groups-in-a-project",
    "tenant-scale#list-groups-available-for-project-transfer",
    "tenant-scale#list-all-topics",
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
    """Import ``gitlab_api.<name>`` (``families.tenant_scale`` for the family) inside a test, after asserting its
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


def token_path_params() -> List[Any]:
    """One case per entry of ``TOKEN_PATH_CASES``, named by its anchor."""
    return [
        pytest.param(operation_id, method, path, id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id, method, path in TOKEN_PATH_CASES
    ]


def non_scalar_kinds(*, records: Sequence[Any], registry: ModuleType) -> Dict[Tuple[str, str], str]:
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
    """One case per entry of ``LIST_RECORDS``, with its path from ``RECORDS``, named by its anchor."""
    return [
        pytest.param(operation_id, RECORDS[operation_id][1], id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id in LIST_RECORDS
    ]


# --- AC-1, AC-2: what is declared and what stays pending ------------------------------------------------------------


def test_every_reference_has_its_record() -> None:
    """AC-1, UB-2, issue #63 AC-1.1 (design.md D9): ``OPERATIONS`` declares each key of an ID once; each ID's first
    record as ``{operation_id: (method, path)}`` is ``RECORDS``, every index Reference of the family but the three
    ``developer_experience`` holds (DL-003); the records after a base record are its section's other endpoints."""
    family = gitlab_module(name=FAMILY_MODULE)
    endpoints = endpoints_by_id(records=family.OPERATIONS)
    repeated = repeated_keys(endpoints=endpoints)
    assert not repeated, f"tenant_scale.OPERATIONS declares these keys of one ID more than once: {repeated}"
    declared = {operation_id: keys[0] for operation_id, keys in endpoints.items()}
    assert declared == RECORDS, (
        f"tenant_scale.OPERATIONS declares {len(declared)} ID(s), AC-1 expects {len(RECORDS)}:\n"
        + mapping_difference(declared=declared, expected=RECORDS)
    )
    others = {operation_id: keys[1:] for operation_id, keys in endpoints.items() if len(keys) > 1}
    assert others == OTHER_ENDPOINT_KEYS, "the records after a base record are not its section's other endpoints:\n" + (
        mapping_difference(declared=others, expected=OTHER_ENDPOINT_KEYS)
    )


def test_only_the_kept_keys_are_pending() -> None:
    """AC-2, issue #63 AC-1.1, AC-1.3 (design.md D9): ``PENDING`` is empty: the four token IDs and the
    ``/groups/:id/...`` endpoint of each Invitations section are records."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "tenant_scale.PENDING is not the keys AC-2 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )


# --- AC-4: kinds, required attributes, bodies -----------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-4: the ``Param``s that are not ``Kind.SCALAR`` carry their row's ``Kind``; the ``Param``s declared
    ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body and no ``fixed``
    pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = non_scalar_kinds(records=records, registry=registry)
    assert typed == NON_SCALAR_KINDS, "the Params that are not Kind.SCALAR are not the sections' (AC-4):\n" + (
        mapping_difference(declared=typed, expected=NON_SCALAR_KINDS)
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert required == expected_required, "required=True is not exactly where Required reads `yes` (AC-4):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    bodies = {record.operation_id: (record.body.name, tuple(record.fixed)) for record in records}
    expected_bodies = {operation_id: (BODY_JSON, NO_FIXED) for operation_id in RECORDS}
    assert bodies == expected_bodies, "every record has body BodyFormat.JSON and no fixed pairs (AC-4):\n" + (
        mapping_difference(declared=bodies, expected=expected_bodies)
    )


# --- AC-5, AC-7: the list records -----------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-5: the ``Paging.OFFSET`` records are exactly ``LIST_RECORDS``, and every other record is ``Paging.NONE`` (so
    none is ``Paging.KEYSET``)."""
    family = gitlab_module(name=FAMILY_MODULE)
    paging = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    listed = frozenset(LIST_RECORDS)
    expected = {operation_id: PAGING_OFFSET if operation_id in listed else PAGING_NONE for operation_id in RECORDS}
    assert paging == expected, "the records' Paging is not OFFSET for the sections' lists, NONE else (AC-5):\n" + (
        mapping_difference(declared=paging, expected=expected)
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


# --- AC-8: a download -------------------------------------------------------------------------------------------


def test_a_download_is_written_unchanged(
    project: Path, fake_gitlab: Any, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """AC-8: ``call tenant-scale#download-snapshot-of-a-git-repository``, answered with bytes that are not UTF-8 as
    ``application/octet-stream``, sends one ``GET`` to the configured project's snapshot, exits 0 and writes the bytes
    unchanged, no line end added."""
    argv = [OP_DOWNLOAD_SNAPSHOT]
    fake_gitlab.script(
        method=METHOD_GET,
        url=SNAPSHOT_URL,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
        body=NOT_UTF8_BYTES,
    )
    code = run_call(root=project, argv=argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, SNAPSHOT_URL)], "one GET to the project's snapshot, id the project"
    assert captured.out == NOT_UTF8_BYTES, (
        f"the body's bytes unchanged, no line end added (AC-8); standard output: {captured.out!r}"
    )


# --- Issue #63 AC-3.1, AC-3.2: one value per place ------------------------------------------------------------------


@pytest.mark.parametrize(argnames=("operation_id", "method", "path"), argvalues=token_path_params())
def test_each_id_of_a_token_path_takes_its_place(
    operation_id: str, method: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #63 AC-3.1, AC-3.2, AC-8.3: ``call <token record> --path id=7 --path id=self`` sends one request whose
    path holds ``7`` at the group's ``:id`` and ``self`` at the token's, the configured token in its header."""
    url = f"{REST_BASE}{path}"
    if method == METHOD_DELETE:
        fake_gitlab.script(method=method, url=url, status=STATUS_NO_CONTENT)
    else:
        fake_gitlab.script(method=method, url=url, body=ROTATED_TOKEN_ANSWER)
    argv = [operation_id, *(part for value in POSITIONAL_ID_VALUES for part in (OPTION_PATH, value))]
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(method, url)], "one request, each --path id in its own place (AC-3.2)"
    assert fake_gitlab.requests[0].header(name=HEADER_PRIVATE_TOKEN) == TOKEN, (
        "the configured token travels in its one header"
    )
