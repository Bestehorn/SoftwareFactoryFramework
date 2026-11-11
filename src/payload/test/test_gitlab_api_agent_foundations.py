"""Tests for ``gitlab_api/families/agent_foundations.py``, the ``agent-foundations`` endpoint family of the GitLab
wrapper (issue #38, the remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5 and AC-8).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose key sorts to this module, ``key_families`` of
``test/test_gitlab_wrapper_coverage.py``) and ``docs/api-reference/gitlab/rest/agent-foundations.md`` (each section's
endpoints, its heading, and the ``In``, ``Type``, ``Required`` and ``Notes`` columns of its
``| Attribute | In | Type |`` table). What is pinned:

- AC-1, UB-2: ``OPERATIONS`` as ``{operation_id: (method, path)}`` is ``RECORD_ENDPOINTS``, each ID declared once: every
  Reference of those rows but the IDs AC-2 keeps, with its section's endpoint (of several, the first
  ``/projects/:id/...`` one, else the first);
- AC-2: ``PENDING`` is exactly the keys of ``agent-foundations#trigger-a-flow`` and
  ``agent-foundations#restart-a-flow``, which have no record;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (no row of a record is of a Type that is not a scalar);
  the ``required`` names of every record, exactly its query and body rows whose Required reads ``yes``; a JSON body and
  no ``fixed`` pairs on every record;
- AC-5: the ``Paging`` of every record: ``OFFSET`` for a ``GET`` section headed "List" or with a ``page`` row, ``NONE``
  for every other, none ``KEYSET``; "List all agent privileges" answers one object, so every record is ``NONE``;
- AC-8: "Get workflow trace as JSONL", answered with bytes that are not UTF-8 as ``application/octet-stream``, exits 0
  and writes those bytes unchanged (read with ``capsysbinary``).

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test, so the module collects whatever the family declares. The fake GitLab host
and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_agent_foundations.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
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
WRAPPER_MODULE = "gitlab_wrapper_agent_foundations_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY = "agent_foundations"
FAMILY_MODULE = f"families{MODULE_SEPARATOR}{FAMILY}"
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
TOKEN = "glpat-gitlab-api-agent-foundations-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
METHOD_GET = "GET"
OPTION_PATH = "--path"
ASSIGNED = "="
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
DECODE_ERRORS = "replace"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"

# AC-8: "Get workflow trace as JSONL" (`GET /ai/duo_workflows/workflows/:workflow_id/trace.jsonl`); the body starts
# as a JSONL line does and holds bytes that are no UTF-8 sequence.
OP_WORKFLOW_TRACE = "agent-foundations#get-workflow-trace-as-jsonl"
PATH_WORKFLOW_ID = "workflow_id"
WORKFLOW_ID = "7"
TRACE_URL = f"{REST_BASE}/ai/duo_workflows/workflows/{WORKFLOW_ID}/trace.jsonl"
NOT_UTF8_BYTES = b'{"step": 1}\n\xff\xfe\xfd\x00\x80'

# The `registry.Kind`, `registry.BodyFormat` and `registry.Paging` member names the tables hold, and the `fixed`
# pairs every record carries (none).
BODY_JSON = "JSON"
PAGING_NONE = "NONE"
NO_FIXED: Tuple[Tuple[str, str], ...] = ()

# --- The tables, transcribed from docs/api-reference/gitlab -----------------------------------------------------------

# operations-index.md and rest/agent-foundations.md: every record, by ID, sorted: each Reference of the rows whose key
# sorts to this module (`key_families`), but AC-2's, with the method and path of its section's endpoint (AC-1).
RECORD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "agent-foundations#get-workflow-trace-as-jsonl": ("GET", "/ai/duo_workflows/workflows/:workflow_id/trace.jsonl"),
    "agent-foundations#list-all-agent-privileges": ("GET", "/ai/duo_workflows/workflows/agent_privileges"),
    "agent-foundations#seed-gitlab-managed-external-agents": ("POST", "/admin/ai_catalog/seed_external_agents"),
}

# AC-2: the IDs kept pending, "Trigger a flow" and "Restart a flow" (they write code, merge requests and issues;
# change.md Residuals), each with the key of its one row.
KEPT_PENDING: Dict[str, Tuple[str, str]] = {
    "agent-foundations#restart-a-flow": ("POST", "/ai/duo_workflows/workflows/:workflow_id/restart"),
    "agent-foundations#trigger-a-flow": ("POST", "/ai/duo_workflows/workflows"),
}
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(KEPT_PENDING.values())

# rest/agent-foundations.md: no query or body row of a record is of a Kind other than SCALAR (AC-4); the one such row,
# `thread`, is a `string`.
NON_SCALAR_PARAMS: Dict[Tuple[str, str], str] = {}

# rest/agent-foundations.md: no query or body row of a record reads `yes` in Required (AC-4).
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {}


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
    """Import ``gitlab_api.<name>`` (``FAMILY_MODULE`` for the family) inside a test, after asserting its file."""
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


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


# --- AC-1, AC-2: the records and what stays pending ------------------------------------------------------------------


def test_every_reference_has_its_record() -> None:
    """AC-1, UB-2: ``OPERATIONS`` declares, once each, every Reference of the module's index rows but AC-2's, each with
    the method and path of its section's endpoint."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared_ids = [record.operation_id for record in family.OPERATIONS]
    repeated = sorted({operation_id for operation_id in declared_ids if declared_ids.count(operation_id) > 1})
    assert repeated == [], f"{FAMILY}.OPERATIONS declares these IDs more than once: {repeated}"
    declared = {record.operation_id: (record.method, record.path) for record in family.OPERATIONS}
    assert declared == RECORD_ENDPOINTS, f"{FAMILY}.OPERATIONS is not the family's References (AC-1):\n" + (
        mapping_difference(declared=declared, expected=RECORD_ENDPOINTS)
    )


def test_only_the_kept_keys_are_pending() -> None:
    """AC-2, UB-2: ``PENDING`` is exactly the keys of "Trigger a flow" and "Restart a flow", and no record declares
    either ID."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, f"{FAMILY}.PENDING is not the keys AC-2 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )
    declared = sorted(frozenset(record.operation_id for record in family.OPERATIONS) & frozenset(KEPT_PENDING))
    assert declared == [], f"{FAMILY}.OPERATIONS declares IDs AC-2 keeps pending (UB-2): {declared}"


# --- AC-4: kinds, required attributes, bodies --------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-4: the ``Param``s that are not ``Kind.SCALAR`` carry the ``Kind`` of their row; the ``Param``s declared
    ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body and no ``fixed``
    pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = {
        (record.operation_id, param.name): param.kind.name
        for record in records
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }
    assert typed == NON_SCALAR_PARAMS, "the Params that are not Kind.SCALAR are not the sections' (AC-4):\n" + (
        mapping_difference(declared=typed, expected=NON_SCALAR_PARAMS)
    )
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required) for record in records
    }
    expected_required = {
        operation_id: frozenset(REQUIRED_PARAMS.get(operation_id, ())) for operation_id in RECORD_ENDPOINTS
    }
    assert required == expected_required, "required=True is not exactly where Required reads `yes` (AC-4):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    bodies = {record.operation_id: (record.body.name, tuple(record.fixed)) for record in records}
    expected_bodies = {operation_id: (BODY_JSON, NO_FIXED) for operation_id in RECORD_ENDPOINTS}
    assert bodies == expected_bodies, "the bodies and fixed pairs are not the sections' (AC-4):\n" + (
        mapping_difference(declared=bodies, expected=expected_bodies)
    )


# --- AC-5: no record is paged ---------------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-5: "List all agent privileges" answers one object, so every record is ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {operation_id: PAGING_NONE for operation_id in RECORD_ENDPOINTS}
    assert paged == expected, "a record's Paging is not its section's (AC-5):\n" + mapping_difference(
        declared=paged, expected=expected
    )


# --- AC-8: a download ---------------------------------------------------------------------------------------------


def test_a_download_is_written_unchanged(
    project: Path, fake_gitlab: Any, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """AC-8: ``call agent-foundations#get-workflow-trace-as-jsonl --path workflow_id=...``, answered with bytes that are
    not UTF-8 as ``application/octet-stream``, sends one ``GET`` to the workflow's trace, exits 0 and writes the bytes
    unchanged, no line end added."""
    argv = [OP_WORKFLOW_TRACE, OPTION_PATH, f"{PATH_WORKFLOW_ID}{ASSIGNED}{WORKFLOW_ID}"]
    fake_gitlab.script(
        method=METHOD_GET,
        url=TRACE_URL,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
        body=NOT_UTF8_BYTES,
    )
    code = run_call(root=project, argv=argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, TRACE_URL)], "one GET to the workflow's trace.jsonl path"
    assert captured.out == NOT_UTF8_BYTES, (
        f"the body's bytes unchanged, no line end added (AC-8); standard output: {captured.out!r}"
    )
