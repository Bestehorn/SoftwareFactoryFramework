"""Tests for ``gitlab_api/families/security_risk_management.py``, the ``security-risk-management`` endpoint family of
the GitLab wrapper (issue #42, the security slice of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5 and
AC-7).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/security-risk-management.md``)
and ``docs/api-reference/gitlab/rest/security-risk-management.md`` (each section's endpoints, its heading, and the
``In``, ``Type`` and ``Required`` columns of its ``| Attribute | In | Type | Required |`` table). What is pinned:

- AC-1: the ``(method, path)`` of every record, each key once, mapped to its record's ID, the Reference of its row;
  "Create a dependency list export", the one section with several endpoints, maps its ``/projects/:id/`` endpoint;
- AC-2: ``PENDING`` is exactly that section's other two endpoints (one record per ID, DL-003);
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``HASH`` for an ``object`` row, ``ARRAY`` for an
  ``array`` or ``string array`` row; no row is noted "file upload" and no ``array`` row has ``name[].…`` rows), and
  the ``required`` ``Param``s of each record, exactly its Required ``yes`` rows that are not path rows;
- AC-5: the ``Paging`` of every record — ``Paging.OFFSET`` for the ``GET`` sections whose heading begins with "List"
  and for ``#retrieve-project-external-status-check-services``, ``Paging.NONE`` for every other, so no record is
  ``Paging.KEYSET``;
- AC-7: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages, the first answering
  ``x-next-page: 2``, exits 0, requests both pages at their exact URLs and prints both items as one JSON array
  (``print_json``).

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, as ``test/test_gitlab_wrapper_coverage.py`` imports the registry. The fake GitLab host and the socket guard
(``gitlab_wrapper_fixtures.py``, loaded by path as ``test_gitlab_api_call.py`` loads it) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_security_risk_management.py`` (no network).
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
WRAPPER_MODULE = "gitlab_wrapper_security_risk_management_under_test"
PACKAGE = "gitlab_api"
REGISTRY = f"{PACKAGE}.registry"
FAMILY_MODULE = f"{PACKAGE}.families.security_risk_management"
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
TOKEN = "glpat-gitlab-api-security-risk-management-test"  # pragma: allowlist secret
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

# A path parameter as operations-index.md and rest/security-risk-management.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` and `registry.Paging` member names the tables hold (AC-4, AC-5).
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# rest/security-risk-management.md: every section, as (record ID, method, path), in page order — the section's
# endpoint, or of several its `/projects/:id/` one (AC-1). Each is the key of an operations-index.md row whose
# Reference is the ID.
RECORDS: Tuple[Tuple[str, str, str], ...] = (
    (
        "security-risk-management#retrieve-security-policy-settings",
        "GET",
        "/admin/security/compliance_policy_settings",
    ),
    (
        "security-risk-management#update-security-policy-settings",
        "PUT",
        "/admin/security/compliance_policy_settings",
    ),
    ("security-risk-management#create-a-dependency-list-export", "POST", "/projects/:id/dependency_list_exports"),
    ("security-risk-management#retrieve-a-single-dependency-list-export", "GET", "/dependency_list_exports/:id"),
    ("security-risk-management#download-dependency-list-export", "GET", "/dependency_list_exports/:id/download"),
    (
        "security-risk-management#retrieve-project-external-status-check-services",
        "GET",
        "/projects/:id/external_status_checks",
    ),
    ("security-risk-management#create-external-status-check-service", "POST", "/projects/:id/external_status_checks"),
    (
        "security-risk-management#update-external-status-check-service",
        "PUT",
        "/projects/:id/external_status_checks/:check_id",
    ),
    (
        "security-risk-management#delete-external-status-check-service",
        "DELETE",
        "/projects/:id/external_status_checks/:check_id",
    ),
    (
        "security-risk-management#list-all-status-checks-for-a-merge-request",
        "GET",
        "/projects/:id/merge_requests/:merge_request_iid/status_checks",
    ),
    (
        "security-risk-management#set-status-of-an-external-status-check",
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/status_check_responses",
    ),
    (
        "security-risk-management#retry-failed-status-check-for-a-merge-request",
        "POST",
        "/projects/:id/merge_requests/:merge_request_iid/status_checks/:external_status_check_id/retry",
    ),
    ("security-risk-management#list-all-triggers", "GET", "/security/policy_store/triggers"),
    ("security-risk-management#list-all-actions", "GET", "/security/policy_store/actions"),
    ("security-risk-management#list-all-rule-kinds", "GET", "/security/policy_store/rules"),
    (
        "security-risk-management#list-all-organization-policies",
        "GET",
        "/organizations/:id/security/policy_store",
    ),
    (
        "security-risk-management#retrieve-an-organization-policy",
        "GET",
        "/organizations/:id/security/policy_store/:policy_id",
    ),
    (
        "security-risk-management#create-an-organization-policy",
        "POST",
        "/organizations/:id/security/policy_store",
    ),
    (
        "security-risk-management#update-an-organization-policy",
        "PATCH",
        "/organizations/:id/security/policy_store/:policy_id",
    ),
    (
        "security-risk-management#delete-an-organization-policy",
        "DELETE",
        "/organizations/:id/security/policy_store/:policy_id",
    ),
    ("security-risk-management#list-all-group-policies", "GET", "/groups/:id/security/policy_store"),
    ("security-risk-management#retrieve-a-group-policy", "GET", "/groups/:id/security/policy_store/:policy_id"),
    ("security-risk-management#create-a-group-policy", "POST", "/groups/:id/security/policy_store"),
    ("security-risk-management#update-a-group-policy", "PATCH", "/groups/:id/security/policy_store/:policy_id"),
    ("security-risk-management#delete-a-group-policy", "DELETE", "/groups/:id/security/policy_store/:policy_id"),
    ("security-risk-management#list-project-vulnerabilities", "GET", "/projects/:id/vulnerabilities"),
    ("security-risk-management#create-a-vulnerability", "POST", "/projects/:id/vulnerabilities"),
    ("security-risk-management#retrieve-a-vulnerability", "GET", "/vulnerabilities/:id"),
    ("security-risk-management#confirm-a-vulnerability", "POST", "/vulnerabilities/:id/confirm"),
    ("security-risk-management#resolve-a-vulnerability", "POST", "/vulnerabilities/:id/resolve"),
    ("security-risk-management#dismiss-a-vulnerability", "POST", "/vulnerabilities/:id/dismiss"),
    ("security-risk-management#revert-a-vulnerability-to-the-detected-state", "POST", "/vulnerabilities/:id/revert"),
    (
        "security-risk-management#create-an-export-for-archived-vulnerabilities",
        "POST",
        "/security/projects/:id/vulnerability_archive_exports",
    ),
    (
        "security-risk-management#retrieve-a-vulnerability-archive-export",
        "GET",
        "/security/vulnerability_archive_exports/:id",
    ),
    (
        "security-risk-management#download-a-vulnerability-archive-export",
        "GET",
        "/security/vulnerability_archive_exports/:id/download",
    ),
    (
        "security-risk-management#create-a-project-level-vulnerability-export",
        "POST",
        "/security/projects/:id/vulnerability_exports",
    ),
    (
        "security-risk-management#create-a-group-level-vulnerability-export",
        "POST",
        "/security/groups/:id/vulnerability_exports",
    ),
    (
        "security-risk-management#create-an-instance-level-vulnerability-export",
        "POST",
        "/security/vulnerability_exports",
    ),
    ("security-risk-management#retrieve-a-vulnerability-export", "GET", "/security/vulnerability_exports/:id"),
    (
        "security-risk-management#download-a-vulnerability-export",
        "GET",
        "/security/vulnerability_exports/:id/download",
    ),
    (
        "security-risk-management#list-all-project-vulnerability-findings",
        "GET",
        "/projects/:id/vulnerability_findings",
    ),
)
RECORD_KEYS: Dict[Tuple[str, str], str] = {(method, path): operation_id for operation_id, method, path in RECORDS}
RECORD_PATHS: Dict[str, str] = {operation_id: path for operation_id, _, path in RECORDS}

# AC-2: the endpoints of "Create a dependency list export" that are not its record's (one record per ID, DL-003).
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/groups/:id/dependency_list_exports"),
        ("POST", "/pipelines/:id/dependency_list_exports"),
    }
)

# rest/security-risk-management.md: every query and body row whose Kind is not SCALAR, by (record ID, attribute name)
# — HASH for Type `object`, ARRAY for Type `array` or `string array`. Every other row's Type is `integer`,
# `integer or string`, `boolean` or `string`, a SCALAR.
TYPED_PARAMS: Dict[Tuple[str, str], str] = {
    ("security-risk-management#create-external-status-check-service", "protected_branch_ids"): KIND_ARRAY,
    ("security-risk-management#update-external-status-check-service", "protected_branch_ids"): KIND_ARRAY,
    ("security-risk-management#list-all-organization-policies", "namespace_ids"): KIND_ARRAY,
    ("security-risk-management#create-an-organization-policy", "rules"): KIND_ARRAY,
    ("security-risk-management#create-an-organization-policy", "actions"): KIND_ARRAY,
    ("security-risk-management#create-an-organization-policy", "policy_scope"): KIND_HASH,
    ("security-risk-management#update-an-organization-policy", "actions"): KIND_ARRAY,
    ("security-risk-management#update-an-organization-policy", "policy_scope"): KIND_HASH,
    ("security-risk-management#update-an-organization-policy", "rules"): KIND_ARRAY,
    ("security-risk-management#create-a-group-policy", "rules"): KIND_ARRAY,
    ("security-risk-management#create-a-group-policy", "actions"): KIND_ARRAY,
    ("security-risk-management#create-a-group-policy", "policy_scope"): KIND_HASH,
    ("security-risk-management#update-a-group-policy", "actions"): KIND_ARRAY,
    ("security-risk-management#update-a-group-policy", "policy_scope"): KIND_HASH,
    ("security-risk-management#update-a-group-policy", "rules"): KIND_ARRAY,
    ("security-risk-management#create-a-project-level-vulnerability-export", "report_data"): KIND_HASH,
    ("security-risk-management#create-a-group-level-vulnerability-export", "report_data"): KIND_HASH,
    ("security-risk-management#list-all-project-vulnerability-findings", "report_type"): KIND_ARRAY,
    ("security-risk-management#list-all-project-vulnerability-findings", "severity"): KIND_ARRAY,
}

# rest/security-risk-management.md: the rows whose Required reads `yes` and whose `In` is not `path`, by record, in
# table order. A record with no such row is not listed.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "security-risk-management#update-security-policy-settings": ("csp_namespace_id",),
    "security-risk-management#create-a-dependency-list-export": ("export_type",),
    "security-risk-management#create-external-status-check-service": ("name", "external_url"),
    "security-risk-management#set-status-of-an-external-status-check": ("sha", "external_status_check_id"),
    "security-risk-management#create-an-organization-policy": ("name", "rules", "trigger_type"),
    "security-risk-management#create-a-group-policy": ("name", "rules", "trigger_type"),
    "security-risk-management#create-a-vulnerability": ("finding_id",),
    "security-risk-management#create-an-export-for-archived-vulnerabilities": ("start_date", "end_date"),
}

# AC-5: the sections that are a `GET` headed "List" or "Get all", and `#retrieve-project-external-status-check-services`
# (AC-5's paged exception, DL-006), in page order.
LIST_IDS: Tuple[str, ...] = (
    "security-risk-management#retrieve-project-external-status-check-services",
    "security-risk-management#list-all-status-checks-for-a-merge-request",
    "security-risk-management#list-all-triggers",
    "security-risk-management#list-all-actions",
    "security-risk-management#list-all-rule-kinds",
    "security-risk-management#list-all-organization-policies",
    "security-risk-management#list-all-group-policies",
    "security-risk-management#list-project-vulnerabilities",
    "security-risk-management#list-all-project-vulnerability-findings",
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
    """``name`` (``gitlab_api.registry``, ``gitlab_api.families.security_risk_management``) imported inside a test, as
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
    """One case per entry of ``LIST_IDS``, with its record's path from ``RECORDS``, named by its anchor."""
    return [
        pytest.param(operation_id, RECORD_PATHS[operation_id], id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id in LIST_IDS
    ]


# --- AC-1, AC-2: every key has its record, the second endpoints stay pending ----------------------------------------


def test_every_key_has_its_record() -> None:
    """AC-1: ``{(method, path): operation_id}`` over the family's records is ``RECORD_KEYS``, each key declared once."""
    family = gitlab_module(name=FAMILY_MODULE)
    keys = [(record.method, record.path) for record in family.OPERATIONS]
    repeated = sorted({key for key in keys if keys.count(key) > 1})
    assert not repeated, f"security_risk_management.OPERATIONS declares these keys more than once: {repeated}"
    declared = {(record.method, record.path): record.operation_id for record in family.OPERATIONS}
    assert declared == RECORD_KEYS, "the records are not the family's sections (AC-1):\n" + mapping_difference(
        declared=declared, expected=RECORD_KEYS
    )


def test_only_the_unmapped_keys_are_pending() -> None:
    """AC-2: ``PENDING`` is exactly the two endpoints of "Create a dependency list export" that its record does not
    map."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "security_risk_management.PENDING is not AC-2's set:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )


# --- AC-4: kinds and required attributes ----------------------------------------------------------------------------


def test_every_kind_is_its_rows_type() -> None:
    """AC-4: every ``Param`` that is not ``SCALAR``, with its ``Kind``, is the table's non-SCALAR row."""
    registry = gitlab_module(name=REGISTRY)
    family = gitlab_module(name=FAMILY_MODULE)
    declared = {
        (record.operation_id, param.name): param.kind.name
        for record in family.OPERATIONS
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }
    assert declared == TYPED_PARAMS, "the non-SCALAR Params are not the sections' (AC-4):\n" + mapping_difference(
        declared=declared, expected=TYPED_PARAMS
    )


def test_the_required_attributes_are_the_sections() -> None:
    """AC-4: ``{operation_id: names}`` over the records with a ``required`` ``Param`` is the table's Required ``yes``
    rows that are not path rows."""
    family = gitlab_module(name=FAMILY_MODULE)
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required)
        for record in family.OPERATIONS
    }
    declared = {operation_id: names for operation_id, names in required.items() if names}
    expected = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert declared == expected, "the required Params are not the sections' (AC-4):\n" + mapping_difference(
        declared=declared, expected=expected
    )


# --- AC-5, AC-7: the list records -----------------------------------------------------------------------------------


def test_every_list_record_has_a_case() -> None:
    """AC-5: every record's ``Paging`` is ``OFFSET`` for exactly ``LIST_IDS`` and ``NONE`` for every other record of
    ``RECORDS``, so the ``Paging.OFFSET`` IDs are the list cases' and none is ``Paging.KEYSET``."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {
        operation_id: PAGING_OFFSET if operation_id in LIST_IDS else PAGING_NONE for operation_id, _, _ in RECORDS
    }
    assert declared == expected, "the records' Paging is not AC-5's:\n" + mapping_difference(
        declared=declared, expected=expected
    )


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_item(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-7: ``call <id> --path NAME=VALUE ...`` against two pages, the first answering ``x-next-page: 2``, exits 0,
    requests both pages at their exact URLs and prints both items as one JSON array."""
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
        f"one JSON array of both items, in page order, as print_json writes it (AC-7):\n{captured.out}"
    )
