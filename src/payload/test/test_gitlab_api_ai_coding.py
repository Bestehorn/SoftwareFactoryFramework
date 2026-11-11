"""Tests for ``gitlab_api/families/ai_coding.py``: the records of the ai-coding endpoint family, the Code Suggestions,
draft notes, merge request approvals, context commits and merge requests APIs (issue #35, ``change.md`` AC-1, AC-2,
AC-3, AC-4, AC-6).

What is pinned:

- ``PENDING`` is exactly the key of ``ai-coding#rebase-a-merge-request``, and ``OPERATIONS`` declares, once each and at
  its index row's method and path, every Reference of the family's rows of
  ``docs/api-reference/gitlab/operations-index.md`` but that one (AC-1);
- every ``Param`` that is not ``Kind.SCALAR``, or that is a query member row (``not[author_id]``), is typed as its row
  of ``rest/ai-coding.md`` — ``ARRAY`` for a Type holding ``array`` or ``Array``, ``HASH`` for ``hash``, every member
  row its own ``QUERY`` ``Param`` and no body member row (``position[base_sha]``) a ``Param``; ``required`` exactly
  where Required reads ``yes``; every record has a JSON body and no ``fixed`` pairs (AC-2, AC-3);
- the ``Paging.OFFSET`` records are exactly the ``GET`` sections headed "List" or carrying a ``page`` row, and the four
  "Retrieve" lists of DL-005; every other record is ``Paging.NONE`` and none ``Paging.KEYSET`` (AC-4);
- each ``Paging.OFFSET`` record this change adds, called through the product's ``main(argv=["call", ...])`` with
  ``--path`` for every placeholder of its path against a fake host serving one item on each of two pages chained by
  ``x-next-page``, exits 0, requests both pages at their exact URLs and prints both items as one JSON array (AC-6).

Every expected Reference, key, Kind, required name and paged ID is a literal table transcribed from
``operations-index.md`` and ``rest/ai-coding.md``, never read from the records. The names and ``In`` of every ``Param``,
and one call of every record, are proven by ``test/test_gitlab_wrapper_contract.py`` (AC-2, AC-5).

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_ai_coding.py`` (no network).
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
WRAPPER_MODULE = "gitlab_wrapper_ai_coding_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.ai_coding"
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
TOKEN = "glpat-gitlab-api-ai-coding-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
HEADER_NEXT_PAGE = "x-next-page"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

METHOD_GET = "GET"
# The `--path` option of `call` (#41 design.md D2).
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
# Transport.pages: OFFSET adds `per_page=MAX_PER_PAGE` to the first request, and the next page's request sets `page` to
# the `x-next-page` value (conventions.md "Offset-based", #13 AC-2.5).
FIRST_PAGE_QUERY = "?per_page=100"
NEXT_PAGE = "2"
SECOND_PAGE_QUERY = f"?per_page=100&page={NEXT_PAGE}"
LAST_PAGE = ""  # an empty `x-next-page`: no next page

# A path parameter as operations-index.md writes it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds: `id` is a key of the merge requests, rules, notes, commits, users and issues these lists
# answer with (rest/ai-coding.md "Response attributes").
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` and `registry.Paging` member names the tables hold (AC-3, AC-4).
KIND_SCALAR = "SCALAR"
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"
PAGING_KEYSET = "KEYSET"
# A Param name holding one of these is a member row's `parent[key]` name (AC-2).
MEMBER_MARKS = ("[", ":")

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: the method and path of every row whose Reference links rest/ai-coding.md, by the Reference
# written `ai-coding#<anchor>`, sorted. Each Reference carries one row.
INDEX_ROWS: Dict[str, Tuple[str, str]] = {
    "ai-coding#add-spent-time-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/add_spent_time",
    ),
    "ai-coding#approve-merge-request": ("POST", "/projects/:id/merge_requests/:merge_request_iid/approve"),
    "ai-coding#cancel-auto-merge": ("POST", "/projects/:id/merge_requests/:merge_request_iid/cancel_auto_merge"),
    "ai-coding#cancel-merge-when-pipeline-succeeds-deprecated": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/cancel_merge_when_pipeline_succeeds",
    ),
    "ai-coding#create-a-draft-note": ("POST", "/projects/:id/merge_requests/:merge_request_iid/draft_notes"),
    "ai-coding#create-a-merge-request": ("POST", "/projects/:id/merge_requests"),
    "ai-coding#create-a-merge-request-dependency": ("POST", "/projects/:id/merge_requests/:merge_request_iid/blocks"),
    "ai-coding#create-a-to-do-item": ("POST", "/projects/:id/merge_requests/:merge_request_iid/todo"),
    "ai-coding#create-an-approval-rule-for-a-group": ("POST", "/groups/:id/approval_rules"),
    "ai-coding#create-an-approval-rule-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/approval_rules",
    ),
    "ai-coding#create-an-approval-rule-for-a-project": ("POST", "/projects/:id/approval_rules"),
    "ai-coding#create-context-commits-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/context_commits",
    ),
    "ai-coding#create-merge-request-pipeline": ("POST", "/projects/:id/merge_requests/:merge_request_iid/pipelines"),
    "ai-coding#delete-a-draft-note": (
        "DELETE",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
    ),
    "ai-coding#delete-a-merge-request": ("DELETE", "/projects/:id/merge_requests/:merge_request_iid"),
    "ai-coding#delete-a-merge-request-dependency": (
        "DELETE",
        "/projects/:id/merge_requests/:merge_request_iid/blocks/:block_id",
    ),
    "ai-coding#delete-an-approval-rule-for-a-merge-request": (
        "DELETE",
        "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
    ),
    "ai-coding#delete-an-approval-rule-for-a-project": ("DELETE", "/projects/:id/approval_rules/:approval_rule_id"),
    "ai-coding#delete-context-commits-from-a-merge-request": (
        "DELETE",
        "/projects/:id/merge_requests/:merge_request_iid/context_commits",
    ),
    "ai-coding#fetch-connection-details": ("POST", "/code_suggestions/connection_details"),
    "ai-coding#fetch-direct-connection-details-for-the-ai-gateway": ("POST", "/code_suggestions/direct_access"),
    "ai-coding#generate-code-completions": ("POST", "/code_suggestions/completions"),
    "ai-coding#list-all-approval-rules-for-a-group": ("GET", "/groups/:id/approval_rules"),
    "ai-coding#list-all-approval-rules-for-a-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/approval_rules",
    ),
    "ai-coding#list-all-approval-rules-for-a-project": ("GET", "/projects/:id/approval_rules"),
    "ai-coding#list-all-merge-request-draft-notes": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes",
    ),
    "ai-coding#list-context-commits-for-a-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/context_commits",
    ),
    "ai-coding#list-group-merge-requests": ("GET", "/groups/:id/merge_requests"),
    "ai-coding#list-issues-related-to-the-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/related_issues",
    ),
    "ai-coding#list-issues-that-close-on-merge": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/closes_issues",
    ),
    "ai-coding#list-merge-request-diffs": ("GET", "/projects/:id/merge_requests/:merge_request_iid/diffs"),
    "ai-coding#list-merge-request-pipelines": ("GET", "/projects/:id/merge_requests/:merge_request_iid/pipelines"),
    "ai-coding#list-merge-requests": ("GET", "/merge_requests"),
    "ai-coding#list-project-merge-requests": ("GET", "/projects/:id/merge_requests"),
    "ai-coding#merge-a-merge-request": ("PUT", "/projects/:id/merge_requests/:merge_request_iid/merge"),
    "ai-coding#merge-to-default-merge-ref-path": ("GET", "/projects/:id/merge_requests/:merge_request_iid/merge_ref"),
    "ai-coding#publish-a-draft-note": (
        "PUT",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id/publish",
    ),
    "ai-coding#publish-all-pending-draft-notes": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes/bulk_publish",
    ),
    "ai-coding#rebase-a-merge-request": ("PUT", "/projects/:id/merge_requests/:merge_request_iid/rebase"),
    "ai-coding#reset-approvals-for-a-merge-request": (
        "PUT",
        "/projects/:id/merge_requests/:merge_request_iid/reset_approvals",
    ),
    "ai-coding#reset-spent-time-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/reset_spent_time",
    ),
    "ai-coding#reset-the-time-estimate-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/reset_time_estimate",
    ),
    "ai-coding#retrieve-a-draft-note": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
    ),
    "ai-coding#retrieve-a-merge-request": ("GET", "/projects/:id/merge_requests/:merge_request_iid"),
    "ai-coding#retrieve-a-merge-request-diff-version": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/versions/:version_id",
    ),
    "ai-coding#retrieve-an-approval-rule-for-a-project": ("GET", "/projects/:id/approval_rules/:approval_rule_id"),
    "ai-coding#retrieve-an-approval-rule-for-a-specific-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
    ),
    "ai-coding#retrieve-approval-configuration-for-a-project": ("GET", "/projects/:id/approvals"),
    "ai-coding#retrieve-approval-details-for-a-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/approval_state",
    ),
    "ai-coding#retrieve-approval-state-for-a-merge-request": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/approvals",
    ),
    "ai-coding#retrieve-blocked-merge-requests": ("GET", "/projects/:id/merge_requests/:merge_request_iid/blockees"),
    "ai-coding#retrieve-merge-request-changes": ("GET", "/projects/:id/merge_requests/:merge_request_iid/changes"),
    "ai-coding#retrieve-merge-request-commits": ("GET", "/projects/:id/merge_requests/:merge_request_iid/commits"),
    "ai-coding#retrieve-merge-request-dependencies": ("GET", "/projects/:id/merge_requests/:merge_request_iid/blocks"),
    "ai-coding#retrieve-merge-request-diff-versions": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/versions",
    ),
    "ai-coding#retrieve-merge-request-participants": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/participants",
    ),
    "ai-coding#retrieve-merge-request-reviewers": ("GET", "/projects/:id/merge_requests/:merge_request_iid/reviewers"),
    "ai-coding#retrieve-time-tracking-statistics": (
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/time_stats",
    ),
    "ai-coding#set-a-time-estimate-for-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/time_estimate",
    ),
    "ai-coding#show-merge-request-raw-diffs": ("GET", "/projects/:id/merge_requests/:merge_request_iid/raw_diffs"),
    "ai-coding#subscribe-to-a-merge-request": ("POST", "/projects/:id/merge_requests/:merge_request_iid/subscribe"),
    "ai-coding#unapprove-a-merge-request": ("POST", "/projects/:id/merge_requests/:merge_request_iid/unapprove"),
    "ai-coding#unsubscribe-from-a-merge-request": (
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/unsubscribe",
    ),
    "ai-coding#update-a-draft-note": (
        "PUT",
        "/projects/:id/merge_requests/:merge_request_iid/draft_notes/:draft_note_id",
    ),
    "ai-coding#update-a-merge-request": ("PUT", "/projects/:id/merge_requests/:merge_request_iid"),
    "ai-coding#update-an-approval-rule-for-a-merge-request": (
        "PUT",
        "/projects/:id/merge_requests/:merge_request_iid/approval_rules/:approval_rule_id",
    ),
    "ai-coding#update-an-approval-rule-for-a-project": ("PUT", "/projects/:id/approval_rules/:approval_rule_id"),
    "ai-coding#update-approval-configuration-for-a-project": ("POST", "/projects/:id/approvals"),
    "ai-coding#validate-that-code-suggestions-is-enabled": ("POST", "/code_suggestions/enabled"),
}

# AC-1: the one ID kept pending (it rewrites the source branch and no subcommand gates it; change.md Residuals), and
# its key (rest/ai-coding.md "Rebase a merge request").
KEPT_PENDING_IDS: FrozenSet[str] = frozenset({"ai-coding#rebase-a-merge-request"})
KEPT_PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {("PUT", "/projects/:id/merge_requests/:merge_request_iid/rebase")}
)

# rest/ai-coding.md: every query and body row whose Kind is not SCALAR, and every query member row, by record — ARRAY
# for a Type holding `array` or `Array` (`Array`, `array`, `string array`, `integer array`, `array of string`), HASH for
# `hash` (AC-3). A name is the table's, `[]` dropped (`iids[]` is `iids`) and an annotation dropped. A query member row
# (`not[author_id]`) is its own attribute, typed as its own row; a body member row (`position[base_sha]`) is no
# attribute (AC-2). The page has no `array of hashes`, `Hash` or `object` row; `add_labels` and `remove_labels` of
# "Update a merge request" are `string`, so SCALAR.
NON_SCALAR_OR_MEMBER_PARAMS: Dict[str, Dict[str, str]] = {
    "ai-coding#create-a-draft-note": {"position": KIND_HASH},
    "ai-coding#create-a-merge-request": {
        "assignee_ids": KIND_ARRAY,
        "reviewer_ids": KIND_ARRAY,
        "add_labels": KIND_ARRAY,
        "remove_labels": KIND_ARRAY,
    },
    "ai-coding#create-an-approval-rule-for-a-group": {"group_ids": KIND_ARRAY, "user_ids": KIND_ARRAY},
    "ai-coding#create-an-approval-rule-for-a-merge-request": {
        "group_ids": KIND_ARRAY,
        "user_ids": KIND_ARRAY,
        "usernames": KIND_ARRAY,
    },
    "ai-coding#create-an-approval-rule-for-a-project": {
        "group_ids": KIND_ARRAY,
        "protected_branch_ids": KIND_ARRAY,
        "user_ids": KIND_ARRAY,
        "usernames": KIND_ARRAY,
    },
    "ai-coding#create-context-commits-for-a-merge-request": {"commits": KIND_ARRAY},
    "ai-coding#delete-context-commits-from-a-merge-request": {"commits": KIND_ARRAY},
    "ai-coding#generate-code-completions": {"current_file": KIND_HASH, "context": KIND_ARRAY},
    "ai-coding#list-group-merge-requests": {
        "approved_by_ids": KIND_ARRAY,
        "approved_by_usernames": KIND_ARRAY,
        "approver_ids": KIND_ARRAY,
        "assignee_username": KIND_ARRAY,
        "not": KIND_HASH,
        "not[author_id]": KIND_SCALAR,
        "not[author_username]": KIND_SCALAR,
        "not[assignee_id]": KIND_SCALAR,
        "not[assignee_username]": KIND_ARRAY,
        "not[reviewer_username]": KIND_SCALAR,
        "not[labels]": KIND_ARRAY,
        "not[milestone]": KIND_SCALAR,
        "not[my_reaction_emoji]": KIND_SCALAR,
        "not[reviewer_id]": KIND_SCALAR,
    },
    "ai-coding#list-merge-requests": {
        "approved_by_ids": KIND_ARRAY,
        "approved_by_usernames": KIND_ARRAY,
        "approver_ids": KIND_ARRAY,
        "assignee_username": KIND_ARRAY,
        "not": KIND_HASH,
        "not[author_id]": KIND_SCALAR,
        "not[author_username]": KIND_SCALAR,
        "not[assignee_id]": KIND_SCALAR,
        "not[assignee_username]": KIND_ARRAY,
        "not[reviewer_username]": KIND_SCALAR,
        "not[labels]": KIND_ARRAY,
        "not[milestone]": KIND_SCALAR,
        "not[my_reaction_emoji]": KIND_SCALAR,
        "not[reviewer_id]": KIND_SCALAR,
    },
    "ai-coding#list-project-merge-requests": {
        "iids": KIND_ARRAY,
        "approved_by_ids": KIND_ARRAY,
        "approved_by_usernames": KIND_ARRAY,
        "approver_ids": KIND_ARRAY,
        "assignee_username": KIND_ARRAY,
        "not": KIND_HASH,
        "not[author_id]": KIND_SCALAR,
        "not[author_username]": KIND_SCALAR,
        "not[assignee_id]": KIND_SCALAR,
        "not[assignee_username]": KIND_ARRAY,
        "not[reviewer_username]": KIND_SCALAR,
        "not[labels]": KIND_ARRAY,
        "not[milestone]": KIND_SCALAR,
        "not[my_reaction_emoji]": KIND_SCALAR,
        "not[reviewer_id]": KIND_SCALAR,
    },
    "ai-coding#update-a-draft-note": {"position": KIND_HASH},
    "ai-coding#update-a-merge-request": {"assignee_ids": KIND_ARRAY, "reviewer_ids": KIND_ARRAY},
    "ai-coding#update-an-approval-rule-for-a-merge-request": {
        "group_ids": KIND_ARRAY,
        "user_ids": KIND_ARRAY,
        "usernames": KIND_ARRAY,
    },
    "ai-coding#update-an-approval-rule-for-a-project": {
        "group_ids": KIND_ARRAY,
        "protected_branch_ids": KIND_ARRAY,
        "user_ids": KIND_ARRAY,
        "usernames": KIND_ARRAY,
    },
}

# rest/ai-coding.md: the query and body rows whose Required reads `yes`, by record; a record with none is not listed. A
# path row is no Param, and neither is a body member row (the required `position[...]` rows of "Create a draft note"
# and "Update a draft note"); a `conditional` Required (`sha` of "Merge a merge request", the `blocking_merge_request_*`
# rows of "Create a merge request dependency") is not `yes` (AC-3).
REQUIRED_PARAMS: Dict[str, FrozenSet[str]] = {
    "ai-coding#add-spent-time-for-a-merge-request": frozenset({"duration"}),
    "ai-coding#create-a-draft-note": frozenset({"note"}),
    "ai-coding#create-a-merge-request": frozenset({"source_branch", "target_branch", "title"}),
    "ai-coding#create-an-approval-rule-for-a-group": frozenset({"approvals_required", "name"}),
    "ai-coding#create-an-approval-rule-for-a-merge-request": frozenset({"approvals_required", "name"}),
    "ai-coding#create-an-approval-rule-for-a-project": frozenset({"approvals_required", "name"}),
    "ai-coding#create-context-commits-for-a-merge-request": frozenset({"commits"}),
    "ai-coding#delete-context-commits-from-a-merge-request": frozenset({"commits"}),
    "ai-coding#generate-code-completions": frozenset({"current_file"}),
    "ai-coding#set-a-time-estimate-for-a-merge-request": frozenset({"duration"}),
    "ai-coding#validate-that-code-suggestions-is-enabled": frozenset({"project_path"}),
}

# AC-4: every `GET` section headed "List" (the first twelve), every other `GET` section with a `page` row ("Retrieve
# merge request commits", "Retrieve merge request diff versions"), and the four "Retrieve" lists DL-005 pages
# (GitLab's handlers call `paginate`; conventions.md "Pagination").
OFFSET_IDS: FrozenSet[str] = frozenset(
    {
        "ai-coding#list-all-approval-rules-for-a-group",
        "ai-coding#list-all-approval-rules-for-a-merge-request",
        "ai-coding#list-all-approval-rules-for-a-project",
        "ai-coding#list-all-merge-request-draft-notes",
        "ai-coding#list-context-commits-for-a-merge-request",
        "ai-coding#list-group-merge-requests",
        "ai-coding#list-issues-related-to-the-merge-request",
        "ai-coding#list-issues-that-close-on-merge",
        "ai-coding#list-merge-request-diffs",
        "ai-coding#list-merge-request-pipelines",
        "ai-coding#list-merge-requests",
        "ai-coding#list-project-merge-requests",
        "ai-coding#retrieve-merge-request-commits",
        "ai-coding#retrieve-merge-request-diff-versions",
        "ai-coding#retrieve-blocked-merge-requests",
        "ai-coding#retrieve-merge-request-dependencies",
        "ai-coding#retrieve-merge-request-participants",
        "ai-coding#retrieve-merge-request-reviewers",
    }
)
# The part-1 list record (issue #13); AC-6 calls only the lists this change adds.
PART_ONE_LIST_ID = "ai-coding#list-merge-request-pipelines"


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
    """Import ``gitlab_api.<name>`` (``families.ai_coding`` for the family) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
    return "\n".join(lines)


def mapping_difference(*, declared: Mapping[str, Any], expected: Mapping[str, Any]) -> str:
    """The keys ``declared`` lacks or has beyond ``expected``, and each key whose value differs."""
    lines = [set_difference(declared=set(declared), expected=set(expected))]
    lines.extend(
        f"{key}: declared {declared[key]!r}, expected {expected[key]!r}"
        for key in sorted(set(declared) & set(expected))
        if declared[key] != expected[key]
    )
    return "\n".join(line for line in lines if line)


def is_member(*, name: str) -> bool:
    """A ``Param`` name holding ``[`` or ``:`` names a member row (``not[author_id]``)."""
    return any(mark in name for mark in MEMBER_MARKS)


def typed_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[str, Dict[str, str]]:
    """``{operation_id: {name: Kind name}}`` of every ``Param`` that is not SCALAR or is a member, over the records with
    any."""
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


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def new_list_params() -> List[Any]:
    """One case per ``Paging.OFFSET`` ID but the part-1 one, with its index row's path, named by its anchor."""
    return [
        pytest.param(operation_id, INDEX_ROWS[operation_id][1], id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id in sorted(OFFSET_IDS - {PART_ONE_LIST_ID})
    ]


# --- AC-1: only the kept key is pending -------------------------------------------------------------------------------


def test_only_the_kept_keys_are_pending() -> None:
    """AC-1, UB-2: ``PENDING`` is exactly the kept ID's key, and ``OPERATIONS`` declares, once each and at its index
    row's method and path, every index Reference of the family but the kept ID."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == KEPT_PENDING_KEYS, "PENDING is not the key AC-1 keeps pending:\n" + set_difference(
        declared=pending, expected=KEPT_PENDING_KEYS
    )
    declared = [record.operation_id for record in family.OPERATIONS]
    repeated = sorted({operation_id for operation_id in declared if declared.count(operation_id) > 1})
    assert repeated == [], f"OPERATIONS declares these IDs more than once: {repeated}"
    expected = frozenset(INDEX_ROWS) - KEPT_PENDING_IDS
    assert frozenset(declared) == expected, "OPERATIONS does not declare the family's References (AC-1):\n" + (
        set_difference(declared=frozenset(declared), expected=expected)
    )
    keys = {record.operation_id: (record.method, record.path) for record in family.OPERATIONS}
    expected_keys = {operation_id: INDEX_ROWS[operation_id] for operation_id in expected}
    assert keys == expected_keys, "a record's method and path is not its index row's (AC-1):\n" + mapping_difference(
        declared=keys, expected=expected_keys
    )


# --- AC-2, AC-3: every Param typed as its row ---------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-2, AC-3: the ``Param``s that are not ``Kind.SCALAR`` or are query member rows carry their row's Kind; the
    ``Param``s declared ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body and
    no ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = typed_params(records=records, registry=registry)
    assert typed == NON_SCALAR_OR_MEMBER_PARAMS, (
        "the Params not Kind.SCALAR or naming a member are not the rows' (AC-2, AC-3):\n"
        + mapping_difference(declared=typed, expected=NON_SCALAR_OR_MEMBER_PARAMS)
    )
    required = required_params(records=records)
    assert required == REQUIRED_PARAMS, "required=True is not exactly the Required `yes` rows (AC-3):\n" + (
        mapping_difference(declared=required, expected=REQUIRED_PARAMS)
    )
    misbodied = sorted(
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    )
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-3): {misbodied}"


# --- AC-4: only the list records are paged --------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-4: the ``Paging.OFFSET`` records are exactly ``OFFSET_IDS``; every other record is ``Paging.NONE``, so none
    is ``Paging.KEYSET``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {
        record.operation_id: record.paging.name for record in family.OPERATIONS if record.paging.name != PAGING_NONE
    }
    keyset = sorted(operation_id for operation_id, paging in paged.items() if paging == PAGING_KEYSET)
    assert keyset == [], f"no ai-coding list is keyset-only (conventions.md 'Keyset-based'), yet KEYSET: {keyset}"
    expected = {operation_id: PAGING_OFFSET for operation_id in OFFSET_IDS}
    assert paged == expected, "the records not Paging.NONE are not the lists AC-4 pages:\n" + mapping_difference(
        declared=paged, expected=expected
    )


# --- AC-6: a list record prints every page --------------------------------------------------------------------------


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=new_list_params())
def test_a_list_record_prints_every_page(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6: ``call <id> --path NAME=VALUE ...`` against two pages scripted at their exact URLs, the second named by
    the first's ``x-next-page``, exits 0, requests both pages in order and prints both items as one JSON array."""
    values = path_values(path=path)
    argv = [
        operation_id,
        *(part for name, value in values.items() for part in (OPTION_PATH, f"{name}{ASSIGNED}{value}")),
    ]
    url = f"{REST_BASE}{expanded(path=path, values=values)}"
    first_page = f"{url}{FIRST_PAGE_QUERY}"
    second_page = f"{url}{SECOND_PAGE_QUERY}"
    fake_gitlab.script(
        method=METHOD_GET, url=first_page, headers=((HEADER_NEXT_PAGE, NEXT_PAGE),), body=[PAGE_ITEMS[0]]
    )
    fake_gitlab.script(
        method=METHOD_GET, url=second_page, headers=((HEADER_NEXT_PAGE, LAST_PAGE),), body=[PAGE_ITEMS[1]]
    )
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_page), (METHOD_GET, second_page)], (
        "each page requested as Transport.pages does (#13 AC-2.5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-6):\n{captured.out}"
    )
