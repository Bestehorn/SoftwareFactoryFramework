"""Tests for ``gitlab_api/families/plan.py``, the ``plan`` endpoint family of the GitLab wrapper (issue #39, the plan
slice of the wrapper rewrite; ``change.md`` AC-1, AC-3, AC-4 and AC-6).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/plan.md``) and
``docs/api-reference/gitlab/rest/plan.md`` (each section's endpoints, its heading, and the ``In``, ``Type`` and
``Required`` columns of its ``| Attribute | In | Type | Required |`` table). What is pinned:

- AC-1: ``PENDING`` is exactly the keys of the two IDs kept pending (DL-003) and, of each section with several
  endpoints, every endpoint but its record's (the first under ``/projects/:id/``); ``OPERATIONS`` declares every
  Reference of the family but those two IDs and ``plan#promote-an-issue-to-an-epic``, whose key is the one
  ``plan#create-an-issue-note`` declares;
- AC-3: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``FILE`` for an ``In`` ``form`` row, ``ARRAY`` for a
  Type holding ``array``, ``HASH`` for ``Hash`` or ``object``); the ``required`` ``Param``s, exactly the Required
  ``yes`` rows that are not path rows; a JSON body and no ``fixed`` pairs on every record;
- AC-4: the ``Paging.OFFSET`` records are exactly the ``GET`` sections whose heading begins with "List" or "Get all",
  and no record is ``Paging.KEYSET``;
- AC-6: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``).

AC-2 and AC-5 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, so the module collects whatever the package lacks. The fake GitLab host and the socket guard
(``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_plan.py`` (no network).
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
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_plan_under_test"
PACKAGE = "gitlab_api"
REGISTRY = f"{PACKAGE}.registry"
PLAN = f"{PACKAGE}.families.plan"
MODULE_SEPARATOR = "."

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

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-plan-test"  # pragma: allowlist secret
PROJECT_ID = 4242

CALL = "call"
EXIT_OK = 0
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
METHOD_GET = "GET"
REST_BASE = fixtures.REST_BASE
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_NEXT_PAGE = "x-next-page"
CONTENT_TYPE_JSON = "application/json"
# The query of a list's first page: the transport adds `per_page=100` (conventions.md "Offset-based", #13 AC-2.5), and
# the next page repeats it with `page` set to the `x-next-page` value.
FIRST_PAGE_QUERY = "per_page=100"
NEXT_PAGE = "2"
NEXT_PAGE_QUERY = f"page={NEXT_PAGE}"
LAST_PAGE = ""  # an empty `x-next-page`: no next page
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

# A path parameter as operations-index.md and rest/plan.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds: `id` is a key of every plan list response (rest/plan.md).
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` values a non-SCALAR attribute takes (AC-3).
KIND_ARRAY = "array"
KIND_HASH = "hash"
KIND_FILE = "file"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: the Reference of every row linking rest/plan.md, written `plan#<anchor>`, sorted.
INDEX_REFERENCES: Tuple[str, ...] = (
    "plan#add-an-emoji-reaction-to-a-comment",
    "plan#add-an-emoji-reaction-to-a-resource",
    "plan#add-spent-time-for-an-issue",
    "plan#assign-a-child-epic",
    "plan#assign-an-issue-to-an-epic",
    "plan#clone-an-issue",
    "plan#create-a-board-list",
    "plan#create-a-group-issue-board",
    "plan#create-a-group-issue-board-list",
    "plan#create-a-merge-request-note",
    "plan#create-a-milestone",
    "plan#create-a-new-group-label",
    "plan#create-a-project-label",
    "plan#create-a-related-epic-link",
    "plan#create-a-snippet-note",
    "plan#create-a-to-do-item-for-an-epic",
    "plan#create-a-to-do-item-for-an-issue",
    "plan#create-a-wiki-page",
    "plan#create-a-wiki-page-1",
    "plan#create-a-wiki-page-note",
    "plan#create-a-wiki-page-note-1",
    "plan#create-an-epic",
    "plan#create-an-epic-note",
    "plan#create-an-issue",
    "plan#create-an-issue-board",
    "plan#create-an-issue-link",
    "plan#create-an-issue-note",
    "plan#create-an-upload",
    "plan#create-and-assign-a-child-epic",
    "plan#create-new-milestone",
    "plan#create-new-pages-domain",
    "plan#delete-a-board-list-from-a-board",
    "plan#delete-a-group-issue-board",
    "plan#delete-a-group-issue-board-list",
    "plan#delete-a-group-label",
    "plan#delete-a-merge-request-note",
    "plan#delete-a-metric-image-from-an-incident",
    "plan#delete-a-milestone",
    "plan#delete-a-project-label",
    "plan#delete-a-related-epic-link",
    "plan#delete-a-snippet-note",
    "plan#delete-a-wiki-page",
    "plan#delete-a-wiki-page-1",
    "plan#delete-a-wiki-page-note",
    "plan#delete-a-wiki-page-note-1",
    "plan#delete-an-emoji-reaction-from-a-comment",
    "plan#delete-an-emoji-reaction-from-a-resource",
    "plan#delete-an-epic",
    "plan#delete-an-epic-note",
    "plan#delete-an-issue",
    "plan#delete-an-issue-board",
    "plan#delete-an-issue-link",
    "plan#delete-an-issue-note",
    "plan#delete-an-uploaded-file-by-id",
    "plan#delete-an-uploaded-file-by-id-1",
    "plan#delete-an-uploaded-file-by-secret-and-filename",
    "plan#delete-an-uploaded-file-by-secret-and-filename-1",
    "plan#delete-group-milestone",
    "plan#delete-pages-domain",
    "plan#download-an-uploaded-file-by-id",
    "plan#download-an-uploaded-file-by-id-1",
    "plan#download-an-uploaded-file-by-secret-and-filename",
    "plan#download-an-uploaded-file-by-secret-and-filename-1",
    "plan#edit-milestone",
    "plan#execute-a-glql-query",
    "plan#get-a-single-group-label",
    "plan#get-all-burndown-chart-events-for-a-single-milestone",
    "plan#get-all-issues-assigned-to-a-single-milestone",
    "plan#get-all-merge-requests-assigned-to-a-single-milestone",
    "plan#get-single-milestone",
    "plan#list-all-board-lists-in-an-issue-board",
    "plan#list-all-burndown-chart-events-for-a-milestone",
    "plan#list-all-child-epics-of-an-epic",
    "plan#list-all-emoji-reactions-for-a-comment",
    "plan#list-all-emoji-reactions-for-a-resource",
    "plan#list-all-epic-boards-in-a-group",
    "plan#list-all-epic-notes",
    "plan#list-all-group-epics",
    "plan#list-all-group-issue-boards-in-a-group",
    "plan#list-all-group-issues",
    "plan#list-all-group-iterations",
    "plan#list-all-issue-links",
    "plan#list-all-issue-notes",
    "plan#list-all-issues",
    "plan#list-all-issues-for-a-milestone",
    "plan#list-all-issues-for-an-epic",
    "plan#list-all-linked-epics-for-an-epic",
    "plan#list-all-merge-request-notes",
    "plan#list-all-merge-requests-for-a-milestone",
    "plan#list-all-merge-requests-related-to-an-issue",
    "plan#list-all-merge-requests-that-close-an-issue-on-merge",
    "plan#list-all-metric-images-for-an-incident",
    "plan#list-all-pages-domains",
    "plan#list-all-pages-domains-in-a-project",
    "plan#list-all-participants-in-an-issue",
    "plan#list-all-project-issue-boards",
    "plan#list-all-project-issue-weight-events",
    "plan#list-all-project-issues",
    "plan#list-all-project-iterations",
    "plan#list-all-project-labels",
    "plan#list-all-project-milestones",
    "plan#list-all-project-wiki-notes",
    "plan#list-all-related-epic-links-for-a-group",
    "plan#list-all-snippet-notes",
    "plan#list-all-to-do-items",
    "plan#list-all-uploads-for-a-group",
    "plan#list-all-wiki-pages",
    "plan#list-group-epic-board-lists",
    "plan#list-group-epic-label-events",
    "plan#list-group-epic-state-events",
    "plan#list-group-issue-board-lists",
    "plan#list-group-labels",
    "plan#list-group-milestones",
    "plan#list-group-wiki-notes",
    "plan#list-project-issue-iteration-events",
    "plan#list-project-issue-label-events",
    "plan#list-project-issue-milestone-events",
    "plan#list-project-issue-state-events",
    "plan#list-project-merge-request-label-events",
    "plan#list-project-merge-request-milestone-events",
    "plan#list-project-merge-request-state-events",
    "plan#list-uploads",
    "plan#list-wiki-pages",
    "plan#mark-a-to-do-item-as-done",
    "plan#mark-all-to-do-items-as-done",
    "plan#move-an-issue",
    "plan#promote-a-milestone-to-group-milestone",
    "plan#promote-a-project-label-to-a-group-label",
    "plan#promote-an-issue-to-an-epic",
    "plan#re-order-a-child-epic",
    "plan#register-a-device",
    "plan#remove-an-issue-from-an-epic",
    "plan#render-markdown-content",
    "plan#reorder-an-issue",
    "plan#reset-spent-time-for-an-issue",
    "plan#reset-the-time-estimate-for-an-issue",
    "plan#retrieve-a-board-list",
    "plan#retrieve-a-group-epic-board",
    "plan#retrieve-a-group-epic-board-list",
    "plan#retrieve-a-group-issue-board",
    "plan#retrieve-a-group-issue-board-list",
    "plan#retrieve-a-merge-request-note",
    "plan#retrieve-a-milestone",
    "plan#retrieve-a-pages-domain",
    "plan#retrieve-a-project-issue",
    "plan#retrieve-a-project-label",
    "plan#retrieve-a-single-epic-label-event",
    "plan#retrieve-a-single-epic-state-event",
    "plan#retrieve-a-single-issue-label-event",
    "plan#retrieve-a-single-issue-milestone-event",
    "plan#retrieve-a-single-issue-state-event",
    "plan#retrieve-a-single-merge-request-label-event",
    "plan#retrieve-a-single-merge-request-milestone-event",
    "plan#retrieve-a-single-merge-request-state-event",
    "plan#retrieve-a-snippet-note",
    "plan#retrieve-a-wiki-page",
    "plan#retrieve-a-wiki-page-1",
    "plan#retrieve-a-wiki-page-note",
    "plan#retrieve-a-wiki-page-note-1",
    "plan#retrieve-an-emoji-reaction-from-a-comment",
    "plan#retrieve-an-emoji-reaction-from-a-resource",
    "plan#retrieve-an-epic",
    "plan#retrieve-an-epic-note",
    "plan#retrieve-an-issue",
    "plan#retrieve-an-issue-board",
    "plan#retrieve-an-issue-iteration-event",
    "plan#retrieve-an-issue-link",
    "plan#retrieve-an-issue-note",
    "plan#retrieve-global-notification-settings",
    "plan#retrieve-issues-statistics-for-a-group",
    "plan#retrieve-issues-statistics-for-a-project",
    "plan#retrieve-issues-statistics-for-a-user",
    "plan#retrieve-notification-settings",
    "plan#retrieve-pages-settings-for-a-project",
    "plan#retrieve-single-issue-weight-event",
    "plan#retrieve-the-glql-schema",
    "plan#retrieve-time-tracking-stats-for-an-issue",
    "plan#retrieve-user-agent-details-for-an-issue",
    "plan#set-a-time-estimate-for-an-issue",
    "plan#subscribe-to-a-group-label",
    "plan#subscribe-to-a-project-label",
    "plan#subscribe-to-an-issue",
    "plan#unassign-a-child-epic",
    "plan#unpublish-pages",
    "plan#unregister-a-device",
    "plan#unsubscribe-from-a-group-label",
    "plan#unsubscribe-from-a-project-label",
    "plan#unsubscribe-from-an-issue",
    "plan#update-a-board-list",
    "plan#update-a-group-issue-board",
    "plan#update-a-group-issue-board-list",
    "plan#update-a-group-label",
    "plan#update-a-merge-request-note",
    "plan#update-a-metric-image-for-an-incident",
    "plan#update-a-milestone",
    "plan#update-a-project-label",
    "plan#update-a-snippet-note",
    "plan#update-a-wiki-page",
    "plan#update-a-wiki-page-1",
    "plan#update-a-wiki-page-note",
    "plan#update-a-wiki-page-note-1",
    "plan#update-an-epic",
    "plan#update-an-epic-issue-association",
    "plan#update-an-epic-note",
    "plan#update-an-issue",
    "plan#update-an-issue-board",
    "plan#update-an-issue-note",
    "plan#update-global-notification-settings",
    "plan#update-group-or-project-notification-settings",
    "plan#update-pages-domain",
    "plan#update-pages-settings-for-a-project",
    "plan#upload-a-file-to-a-group",
    "plan#upload-a-metric-image-for-an-incident",
    "plan#upload-an-attachment-to-the-wiki-repository",
    "plan#upload-an-attachment-to-the-wiki-repository-1",
    "plan#verify-pages-domain",
)

# DL-003: the two IDs kept pending, and the keys of their rows (rest/plan.md "Clone an issue", "Create a merge request
# note"; one endpoint each).
KEPT_PENDING_IDS: FrozenSet[str] = frozenset({"plan#clone-an-issue", "plan#create-a-merge-request-note"})
KEPT_PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/projects/:id/issues/:issue_iid/clone"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/notes"),
    }
)
# The index's other Reference on the key `plan#create-an-issue-note` declares (`POST .../issues/:issue_iid/notes`):
# no record of its own.
SHARED_KEY_ID = "plan#promote-an-issue-to-an-epic"
# The endpoints of the sections with several endpoints that are not their record's: the merge-request and snippet
# endpoints of the four resource sections of "Emoji reactions API", and the group endpoints of "Retrieve notification
# settings" and "Update group or project notification settings".
SECOND_ENDPOINT_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
        ("GET", "/projects/:id/snippets/:snippet_id/award_emoji"),
        ("GET", "/projects/:id/merge_requests/:merge_request_iid/award_emoji/:award_id"),
        ("GET", "/projects/:id/snippets/:snippet_id/award_emoji/:award_id"),
        ("POST", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
        ("POST", "/projects/:id/snippets/:snippet_id/award_emoji"),
        ("DELETE", "/projects/:id/merge_requests/:merge_request_iid/award_emoji/:award_id"),
        ("DELETE", "/projects/:id/snippets/:snippet_id/award_emoji/:award_id"),
        ("GET", "/groups/:id/notification_settings"),
        ("PUT", "/groups/:id/notification_settings"),
    }
)
PENDING_KEYS: FrozenSet[Tuple[str, str]] = KEPT_PENDING_KEYS | SECOND_ENDPOINT_KEYS

# rest/plan.md: every query, body and form row whose Kind is not SCALAR, by (record ID, attribute name) — FILE for an
# `In` `form` row, ARRAY for a Type holding `array`, HASH for `Hash` or `object` (AC-3). A name is the table's, `[]`
# dropped (`iids[]` is `iids`); a member row (`not[labels]`) is its own attribute (AC-2).
TYPED_ATTRIBUTES: Dict[Tuple[str, str], str] = {
    ("plan#create-a-wiki-page", "front_matter"): KIND_HASH,
    ("plan#create-a-wiki-page-1", "front_matter"): KIND_HASH,
    ("plan#create-an-issue", "add_labels"): KIND_ARRAY,
    ("plan#create-an-issue", "assignee_ids"): KIND_ARRAY,
    ("plan#create-an-issue", "remove_labels"): KIND_ARRAY,
    ("plan#create-an-upload", "file"): KIND_FILE,
    ("plan#create-new-pages-domain", "certificate"): KIND_FILE,
    ("plan#create-new-pages-domain", "key"): KIND_FILE,
    ("plan#list-all-group-epics", "not"): KIND_HASH,
    ("plan#list-all-group-issues", "assignee_username"): KIND_ARRAY,
    ("plan#list-all-group-issues", "iids"): KIND_ARRAY,
    ("plan#list-all-group-issues", "not"): KIND_HASH,
    ("plan#list-all-group-issues", "not[assignee_username]"): KIND_ARRAY,
    ("plan#list-all-group-issues", "not[iids]"): KIND_ARRAY,
    ("plan#list-all-group-issues", "not[labels]"): KIND_ARRAY,
    ("plan#list-all-group-iterations", "in"): KIND_ARRAY,
    ("plan#list-all-issues", "assignee_username"): KIND_ARRAY,
    ("plan#list-all-issues", "iids"): KIND_ARRAY,
    ("plan#list-all-issues", "not"): KIND_HASH,
    ("plan#list-all-issues", "not[assignee_username]"): KIND_ARRAY,
    ("plan#list-all-issues", "not[iids]"): KIND_ARRAY,
    ("plan#list-all-issues", "not[labels]"): KIND_ARRAY,
    ("plan#list-all-project-issues", "assignee_username"): KIND_ARRAY,
    ("plan#list-all-project-issues", "iids"): KIND_ARRAY,
    ("plan#list-all-project-issues", "not"): KIND_HASH,
    ("plan#list-all-project-issues", "not[assignee_username]"): KIND_ARRAY,
    ("plan#list-all-project-issues", "not[iids]"): KIND_ARRAY,
    ("plan#list-all-project-issues", "not[labels]"): KIND_ARRAY,
    ("plan#list-all-project-iterations", "in"): KIND_ARRAY,
    ("plan#list-all-project-milestones", "iids"): KIND_ARRAY,
    ("plan#list-group-milestones", "iids"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-group", "assignee_username"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-group", "iids"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-group", "not[assignee_username]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-group", "not[iids]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-group", "not[labels]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-project", "assignee_username"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-project", "iids"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-project", "not[assignee_username]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-project", "not[iids]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-project", "not[labels]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-user", "assignee_username"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-user", "iids"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-user", "not[assignee_username]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-user", "not[iids]"): KIND_ARRAY,
    ("plan#retrieve-issues-statistics-for-a-user", "not[labels]"): KIND_ARRAY,
    ("plan#update-a-wiki-page", "front_matter"): KIND_HASH,
    ("plan#update-a-wiki-page-1", "front_matter"): KIND_HASH,
    ("plan#update-an-issue", "assignee_ids"): KIND_ARRAY,
    ("plan#update-pages-domain", "certificate"): KIND_FILE,
    ("plan#update-pages-domain", "key"): KIND_FILE,
    ("plan#upload-a-file-to-a-group", "file"): KIND_FILE,
    ("plan#upload-a-metric-image-for-an-incident", "file"): KIND_FILE,
    ("plan#upload-an-attachment-to-the-wiki-repository", "file"): KIND_FILE,
    ("plan#upload-an-attachment-to-the-wiki-repository-1", "file"): KIND_FILE,
}

# rest/plan.md: every row whose Required reads `yes` and whose `In` is not `path`, by (record ID, attribute name); the
# emoji sections' combined row is named as written (AC-2).
REQUIRED_ATTRIBUTES: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("plan#add-an-emoji-reaction-to-a-comment", "name"),
        ("plan#add-an-emoji-reaction-to-a-resource", "issue_iid/merge_request_iid/snippet_id"),
        ("plan#add-an-emoji-reaction-to-a-resource", "name"),
        ("plan#add-spent-time-for-an-issue", "duration"),
        ("plan#create-a-group-issue-board", "name"),
        ("plan#create-a-milestone", "title"),
        ("plan#create-a-new-group-label", "color"),
        ("plan#create-a-new-group-label", "name"),
        ("plan#create-a-project-label", "color"),
        ("plan#create-a-project-label", "name"),
        ("plan#create-a-related-epic-link", "target_epic_iid"),
        ("plan#create-a-related-epic-link", "target_group_id"),
        ("plan#create-a-snippet-note", "body"),
        ("plan#create-a-wiki-page", "content"),
        ("plan#create-a-wiki-page", "title"),
        ("plan#create-a-wiki-page-1", "content"),
        ("plan#create-a-wiki-page-1", "title"),
        ("plan#create-a-wiki-page-note", "body"),
        ("plan#create-a-wiki-page-note-1", "body"),
        ("plan#create-an-epic", "title"),
        ("plan#create-an-epic-note", "body"),
        ("plan#create-an-issue", "title"),
        ("plan#create-an-issue-board", "name"),
        ("plan#create-an-issue-link", "target_issue_iid"),
        ("plan#create-an-issue-link", "target_project_id"),
        ("plan#create-an-issue-note", "body"),
        ("plan#create-an-upload", "file"),
        ("plan#create-and-assign-a-child-epic", "title"),
        ("plan#create-new-milestone", "title"),
        ("plan#create-new-pages-domain", "domain"),
        ("plan#delete-an-emoji-reaction-from-a-resource", "issue_iid/merge_request_iid/snippet_id"),
        ("plan#execute-a-glql-query", "glql_yaml"),
        ("plan#list-all-emoji-reactions-for-a-resource", "issue_iid/merge_request_iid/snippet_id"),
        ("plan#move-an-issue", "to_project_id"),
        ("plan#register-a-device", "device_token"),
        ("plan#render-markdown-content", "text"),
        ("plan#retrieve-an-emoji-reaction-from-a-resource", "issue_iid/merge_request_iid/snippet_id"),
        ("plan#set-a-time-estimate-for-an-issue", "duration"),
        ("plan#unregister-a-device", "device_token"),
        ("plan#update-a-board-list", "position"),
        ("plan#update-a-group-issue-board-list", "position"),
        ("plan#update-a-merge-request-note", "body"),
        ("plan#update-a-project-label", "color"),
        ("plan#update-a-project-label", "new_name"),
        ("plan#update-a-snippet-note", "body"),
        ("plan#update-a-wiki-page", "content"),
        ("plan#update-a-wiki-page", "title"),
        ("plan#update-a-wiki-page-1", "content"),
        ("plan#update-a-wiki-page-1", "title"),
        ("plan#update-a-wiki-page-note", "body"),
        ("plan#update-a-wiki-page-note-1", "body"),
        ("plan#update-an-epic-note", "body"),
        ("plan#upload-a-file-to-a-group", "file"),
        ("plan#upload-a-metric-image-for-an-incident", "file"),
        ("plan#upload-an-attachment-to-the-wiki-repository", "file"),
        ("plan#upload-an-attachment-to-the-wiki-repository-1", "file"),
    }
)

# rest/plan.md: every section that is a `GET` headed "List" or "Get all" (AC-4), with its record's path — the section's
# endpoint, or of several the first under `/projects/:id/` (AC-1). The two part-1 lists are among them.
LIST_ENDPOINTS: Tuple[Tuple[str, str], ...] = (
    (
        "plan#get-all-burndown-chart-events-for-a-single-milestone",
        "/groups/:id/milestones/:milestone_id/burndown_events",
    ),
    ("plan#get-all-issues-assigned-to-a-single-milestone", "/groups/:id/milestones/:milestone_id/issues"),
    (
        "plan#get-all-merge-requests-assigned-to-a-single-milestone",
        "/groups/:id/milestones/:milestone_id/merge_requests",
    ),
    ("plan#list-all-board-lists-in-an-issue-board", "/projects/:id/boards/:board_id/lists"),
    ("plan#list-all-burndown-chart-events-for-a-milestone", "/projects/:id/milestones/:milestone_id/burndown_events"),
    ("plan#list-all-child-epics-of-an-epic", "/groups/:id/epics/:epic_iid/epics"),
    ("plan#list-all-emoji-reactions-for-a-comment", "/projects/:id/issues/:issue_iid/notes/:note_id/award_emoji"),
    ("plan#list-all-emoji-reactions-for-a-resource", "/projects/:id/issues/:issue_iid/award_emoji"),
    ("plan#list-all-epic-boards-in-a-group", "/groups/:id/epic_boards"),
    ("plan#list-all-epic-notes", "/groups/:id/epics/:epic_id/notes"),
    ("plan#list-all-group-epics", "/groups/:id/epics"),
    ("plan#list-all-group-issue-boards-in-a-group", "/groups/:id/boards"),
    ("plan#list-all-group-issues", "/groups/:id/issues"),
    ("plan#list-all-group-iterations", "/groups/:id/iterations"),
    ("plan#list-all-issue-links", "/projects/:id/issues/:issue_iid/links"),
    ("plan#list-all-issue-notes", "/projects/:id/issues/:issue_iid/notes"),
    ("plan#list-all-issues", "/issues"),
    ("plan#list-all-issues-for-a-milestone", "/projects/:id/milestones/:milestone_id/issues"),
    ("plan#list-all-issues-for-an-epic", "/groups/:id/epics/:epic_iid/issues"),
    ("plan#list-all-linked-epics-for-an-epic", "/groups/:id/epics/:epic_iid/related_epics"),
    ("plan#list-all-merge-request-notes", "/projects/:id/merge_requests/:merge_request_iid/notes"),
    ("plan#list-all-merge-requests-for-a-milestone", "/projects/:id/milestones/:milestone_id/merge_requests"),
    ("plan#list-all-merge-requests-related-to-an-issue", "/projects/:id/issues/:issue_iid/related_merge_requests"),
    ("plan#list-all-merge-requests-that-close-an-issue-on-merge", "/projects/:id/issues/:issue_iid/closed_by"),
    ("plan#list-all-metric-images-for-an-incident", "/projects/:id/issues/:issue_iid/metric_images"),
    ("plan#list-all-pages-domains", "/pages/domains"),
    ("plan#list-all-pages-domains-in-a-project", "/projects/:id/pages/domains"),
    ("plan#list-all-participants-in-an-issue", "/projects/:id/issues/:issue_iid/participants"),
    ("plan#list-all-project-issue-boards", "/projects/:id/boards"),
    ("plan#list-all-project-issue-weight-events", "/projects/:id/issues/:issue_iid/resource_weight_events"),
    ("plan#list-all-project-issues", "/projects/:id/issues"),
    ("plan#list-all-project-iterations", "/projects/:id/iterations"),
    ("plan#list-all-project-labels", "/projects/:id/labels"),
    ("plan#list-all-project-milestones", "/projects/:id/milestones"),
    ("plan#list-all-project-wiki-notes", "/projects/:id/wiki_pages/:wiki_page_meta_id/notes"),
    ("plan#list-all-related-epic-links-for-a-group", "/groups/:id/related_epic_links"),
    ("plan#list-all-snippet-notes", "/projects/:id/snippets/:snippet_id/notes"),
    ("plan#list-all-to-do-items", "/todos"),
    ("plan#list-all-uploads-for-a-group", "/groups/:id/uploads"),
    ("plan#list-all-wiki-pages", "/projects/:id/wikis"),
    ("plan#list-group-epic-board-lists", "/groups/:id/epic_boards/:board_id/lists"),
    ("plan#list-group-epic-label-events", "/groups/:id/epics/:epic_id/resource_label_events"),
    ("plan#list-group-epic-state-events", "/groups/:id/epics/:epic_id/resource_state_events"),
    ("plan#list-group-issue-board-lists", "/groups/:id/boards/:board_id/lists"),
    ("plan#list-group-labels", "/groups/:id/labels"),
    ("plan#list-group-milestones", "/groups/:id/milestones"),
    ("plan#list-group-wiki-notes", "/groups/:id/wiki_pages/:wiki_page_meta_id/notes"),
    ("plan#list-project-issue-iteration-events", "/projects/:id/issues/:issue_iid/resource_iteration_events"),
    ("plan#list-project-issue-label-events", "/projects/:id/issues/:issue_iid/resource_label_events"),
    ("plan#list-project-issue-milestone-events", "/projects/:id/issues/:issue_iid/resource_milestone_events"),
    ("plan#list-project-issue-state-events", "/projects/:id/issues/:issue_iid/resource_state_events"),
    (
        "plan#list-project-merge-request-label-events",
        "/projects/:id/merge_requests/:merge_request_iid/resource_label_events",
    ),
    (
        "plan#list-project-merge-request-milestone-events",
        "/projects/:id/merge_requests/:merge_request_iid/resource_milestone_events",
    ),
    (
        "plan#list-project-merge-request-state-events",
        "/projects/:id/merge_requests/:merge_request_iid/resource_state_events",
    ),
    ("plan#list-uploads", "/projects/:id/uploads"),
    ("plan#list-wiki-pages", "/groups/:id/wikis"),
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
    """``name`` (``gitlab_api.registry``, ``gitlab_api.families.plan``) imported inside a test, as
    ``test/test_gitlab_wrapper_coverage.py`` imports the registry: while it is absent the test fails on this
    assertion."""
    parts = name.split(MODULE_SEPARATOR)
    owners = {MODULE_SEPARATOR.join(parts[:count]) for count in range(1, len(parts) + 1)}
    try:
        return importlib.import_module(name=name)
    except ModuleNotFoundError as missing:
        if missing.name not in owners:
            raise
        raise AssertionError(f"{name} is not importable from {SCRIPTS_DIR}: {missing}") from missing


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
    """AC-1, UB-2: ``PENDING`` is the kept IDs' keys and the second endpoints, and ``OPERATIONS`` declares, once each,
    every index Reference of the family but the kept IDs and the one whose key another record declares."""
    plan = gitlab_module(name=PLAN)
    pending = frozenset(plan.PENDING)
    assert pending == PENDING_KEYS, "plan.PENDING is not the keys AC-1 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )
    declared = [record.operation_id for record in plan.OPERATIONS]
    expected = set(INDEX_REFERENCES) - KEPT_PENDING_IDS - {SHARED_KEY_ID}
    repeated = sorted({operation_id for operation_id in declared if declared.count(operation_id) > 1})
    assert not repeated, f"plan.OPERATIONS declares these IDs more than once: {repeated}"
    assert set(declared) == expected, "plan.OPERATIONS does not declare the family's References (AC-1):\n" + (
        set_difference(declared=set(declared), expected=expected)
    )


# --- AC-3: kinds, required attributes, bodies -----------------------------------------------------------------------


def test_the_typed_attributes_are_the_sections() -> None:
    """AC-3: every ``Param`` that is not ``SCALAR``, with its ``Kind``, is the table's non-SCALAR row."""
    registry = gitlab_module(name=REGISTRY)
    plan = gitlab_module(name=PLAN)
    declared = {
        (record.operation_id, param.name): param.kind.value
        for record in plan.OPERATIONS
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }
    assert declared == TYPED_ATTRIBUTES, "the non-SCALAR Params are not the sections' (AC-3):\n" + mapping_difference(
        declared=declared, expected=TYPED_ATTRIBUTES
    )


def test_the_required_attributes_are_the_sections() -> None:
    """AC-3: the ``required`` ``Param``s are exactly the Required ``yes`` rows that are not path rows."""
    plan = gitlab_module(name=PLAN)
    declared = {
        (record.operation_id, param.name) for record in plan.OPERATIONS for param in record.params if param.required
    }
    assert declared == REQUIRED_ATTRIBUTES, "the required Params are not the sections' (AC-3):\n" + set_difference(
        declared=declared, expected=REQUIRED_ATTRIBUTES
    )


def test_every_body_is_json_with_no_fixed_pairs() -> None:
    """AC-3: every record's ``body`` is ``BodyFormat.JSON`` and its ``fixed`` is empty."""
    registry = gitlab_module(name=REGISTRY)
    plan = gitlab_module(name=PLAN)
    problems = [
        f"{record.operation_id}: body {record.body.value}"
        for record in plan.OPERATIONS
        if record.body is not registry.BodyFormat.JSON
    ]
    problems.extend(f"{record.operation_id}: fixed {record.fixed!r}" for record in plan.OPERATIONS if record.fixed)
    assert not problems, "records with another body or fixed pairs (AC-3):\n" + "\n".join(problems)


# --- AC-4, AC-6: the list records -----------------------------------------------------------------------------------


def test_every_list_record_has_a_case() -> None:
    """AC-4: the ``Paging.OFFSET`` records are exactly ``LIST_ENDPOINTS``' IDs, and no record is ``Paging.KEYSET``."""
    registry = gitlab_module(name=REGISTRY)
    plan = gitlab_module(name=PLAN)
    offset = {record.operation_id for record in plan.OPERATIONS if record.paging is registry.Paging.OFFSET}
    expected = {operation_id for operation_id, _ in LIST_ENDPOINTS}
    assert offset == expected, "the Paging.OFFSET records are not the sections' lists (AC-4):\n" + set_difference(
        declared=offset, expected=expected
    )
    keyset = sorted(record.operation_id for record in plan.OPERATIONS if record.paging is registry.Paging.KEYSET)
    assert keyset == [], f"no plan list is keyset-only (conventions.md 'Keyset-based'), yet KEYSET: {keyset}"


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_item(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6: ``call <id> --path NAME=VALUE ...`` against two pages chained by ``x-next-page`` exits 0, requests both
    pages at their exact URLs and prints both items as one JSON array."""
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
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [
        (METHOD_GET, first_url),
        (METHOD_GET, next_url),
    ], "each page requested as Transport.pages does (#13 AC-2.5)"
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-6):\n{captured.out}"
    )
