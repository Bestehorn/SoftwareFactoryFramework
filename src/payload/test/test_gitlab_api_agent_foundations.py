"""Tests for ``gitlab_api/families/agent_foundations.py``, the ``agent-foundations`` endpoint family of the GitLab
wrapper (issue #38, the remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-4, AC-5 and AC-8; issue
#15, the kept keys, ``change.md`` AC-1 to AC-3).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose key sorts to this module, ``key_families`` of
``test/test_gitlab_wrapper_coverage.py``) and ``docs/api-reference/gitlab/rest/agent-foundations.md`` (each section's
endpoints, its heading, and the ``In``, ``Type``, ``Required`` and ``Notes`` columns of its
``| Attribute | In | Type |`` table). What is pinned:

- #38 AC-1, #15 AC-1: ``OPERATIONS`` as ``{operation_id: (method, path)}`` is ``RECORD_ENDPOINTS``, each ID declared
  once: every Reference of those rows, "Trigger a flow" and "Restart a flow" among them, with its section's endpoint
  (of several, the first ``/projects/:id/...`` one, else the first);
- #15 AC-2: ``PENDING`` is empty;
- #15 AC-3: ``agent-foundations#trigger-a-flow`` and ``agent-foundations#restart-a-flow`` write code, merge requests
  and issues: ``registry.lookup`` returns each record, yet its ``call`` with a value for each path parameter exits 2
  with no request, an ERROR record naming the ID and that no subcommand sends it;
- #38 AC-4, #15 AC-1: the ``Kind`` of every ``Param`` that is not ``SCALAR`` ("Trigger a flow"'s ``integer array``
  rows ``ARRAY``, its ``array of objects`` row ``ARRAY_OF_HASHES``); the ``required`` names of every record, exactly
  its query and body rows whose Required reads ``yes`` (none); a JSON body and no ``fixed`` pairs on every record;
- #38 AC-5, #15 AC-1: the ``Paging`` of every record: ``OFFSET`` for a ``GET`` section headed "List" or with a
  ``page`` row, ``NONE`` for every other, none ``KEYSET``; "List all agent privileges" answers one object, so every
  record is ``NONE``;
- #38 AC-8: "Get workflow trace as JSONL", answered with bytes that are not UTF-8 as ``application/octet-stream``,
  exits 0 and writes those bytes unchanged (read with ``capsysbinary``).

#38's AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test, so the module collects whatever the family declares. The fake GitLab host
and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_agent_foundations.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, List, Mapping, Sequence, Tuple

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
EXIT_USAGE = 2  # argparse's usage error and a refused `call` (issue #13 design.md D4)
METHOD_GET = "GET"
OPTION_PATH = "--path"
ASSIGNED = "="
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
DECODE_ERRORS = "replace"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
CONTENT_TYPE_JSON = "application/json"
JSON_HEADERS = ((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON),)
EMPTY_JSON_OBJECT = b"{}"

# AC-8: "Get workflow trace as JSONL" (`GET /ai/duo_workflows/workflows/:workflow_id/trace.jsonl`); the body starts
# as a JSONL line does and holds bytes that are no UTF-8 sequence.
OP_WORKFLOW_TRACE = "agent-foundations#get-workflow-trace-as-jsonl"
PATH_WORKFLOW_ID = "workflow_id"
WORKFLOW_ID = "7"
TRACE_URL = f"{REST_BASE}/ai/duo_workflows/workflows/{WORKFLOW_ID}/trace.jsonl"
NOT_UTF8_BYTES = b'{"step": 1}\n\xff\xfe\xfd\x00\x80'

# Issue #15 AC-3: the writers (operations-index.md, rest/agent-foundations.md "Trigger a flow" and "Restart a flow"),
# each with the argv of its complete call: a value for each path parameter and required row; "Trigger a flow" has no
# path parameter and no required row, "Restart a flow" the one path parameter `workflow_id`.
OP_TRIGGER_A_FLOW = "agent-foundations#trigger-a-flow"
OP_RESTART_A_FLOW = "agent-foundations#restart-a-flow"
WRITING_CALLS: Dict[str, Tuple[str, ...]] = {
    OP_RESTART_A_FLOW: (OPTION_PATH, f"{PATH_WORKFLOW_ID}{ASSIGNED}{WORKFLOW_ID}"),
    OP_TRIGGER_A_FLOW: (),
}
WRITING_IDS: Tuple[str, ...] = tuple(sorted(WRITING_CALLS))
# The end of the refusal of an ID `GATED_OPERATIONS` maps to `None` (issue #44 design.md D6).
NO_SUBCOMMAND_SENDS_IT = ": no subcommand sends it"

# The `registry.Kind`, `registry.BodyFormat` and `registry.Paging` member names the tables hold, and the `fixed`
# pairs every record carries (none).
BODY_JSON = "JSON"
PAGING_NONE = "NONE"
NO_FIXED: Tuple[Tuple[str, str], ...] = ()

# --- The tables, transcribed from docs/api-reference/gitlab -----------------------------------------------------------

# operations-index.md and rest/agent-foundations.md: every record, by ID, sorted: each Reference of the rows whose key
# sorts to this module (`key_families`), with the method and path of its section's endpoint (#38 AC-1, #15 AC-1).
RECORD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "agent-foundations#get-workflow-trace-as-jsonl": ("GET", "/ai/duo_workflows/workflows/:workflow_id/trace.jsonl"),
    "agent-foundations#list-all-agent-privileges": ("GET", "/ai/duo_workflows/workflows/agent_privileges"),
    "agent-foundations#restart-a-flow": ("POST", "/ai/duo_workflows/workflows/:workflow_id/restart"),
    "agent-foundations#seed-gitlab-managed-external-agents": ("POST", "/admin/ai_catalog/seed_external_agents"),
    "agent-foundations#trigger-a-flow": ("POST", "/ai/duo_workflows/workflows"),
}

# rest/agent-foundations.md: the query and body rows of a record of a Kind other than SCALAR (#38 AC-4, #15 AC-1), all
# "Trigger a flow"'s: `additional_context` (`array of objects`) and the two `integer array` rows; every other row,
# `thread` and "Trigger a flow"'s `integer`, `boolean` and `string` rows, is SCALAR.
NON_SCALAR_PARAMS: Dict[Tuple[str, str], str] = {
    ("agent-foundations#trigger-a-flow", "additional_context"): "ARRAY_OF_HASHES",
    ("agent-foundations#trigger-a-flow", "agent_privileges"): "ARRAY",
    ("agent-foundations#trigger-a-flow", "pre_approved_agent_privileges"): "ARRAY",
}

# rest/agent-foundations.md: no query or body row of a record reads `yes` in Required (#38 AC-4, #15 AC-1); the rows
# that do, the `workflow_id` of "Restart a flow" and of "Get workflow trace as JSONL", are path rows, no `Param`.
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


def answer_anything(*, fake: Any) -> None:
    """Answer the next request, whatever it is, with ``{}``: a refusal that sends one is then judged by its oracle,
    not by the fake host's unscripted-request error."""
    fake.script_next(headers=JSON_HEADERS, body=EMPTY_JSON_OBJECT)


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


# --- #38 AC-1, #15 AC-1, AC-2: the records, and nothing pending ------------------------------------------------------


def test_every_reference_has_its_record() -> None:
    """#38 AC-1, #15 AC-1: ``OPERATIONS`` declares, once each, every Reference of the module's index rows, each with
    the method and path of its section's endpoint."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared_ids = [record.operation_id for record in family.OPERATIONS]
    repeated = sorted({operation_id for operation_id in declared_ids if declared_ids.count(operation_id) > 1})
    assert repeated == [], f"{FAMILY}.OPERATIONS declares these IDs more than once: {repeated}"
    declared = {record.operation_id: (record.method, record.path) for record in family.OPERATIONS}
    assert declared == RECORD_ENDPOINTS, f"{FAMILY}.OPERATIONS is not the family's References (AC-1):\n" + (
        mapping_difference(declared=declared, expected=RECORD_ENDPOINTS)
    )


def test_nothing_is_pending() -> None:
    """#15 AC-2: ``PENDING`` is empty; that every Reference of the family's index rows has its record is
    ``test_every_reference_has_its_record``'s."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"{FAMILY}.PENDING holds {len(pending)} key(s); each has its record (#15 AC-2): {pending}"


# --- #15 AC-3: a writing record is refused ---------------------------------------------------------------------------


@pytest.mark.parametrize(argnames="operation_id", argvalues=WRITING_IDS)
def test_a_writing_record_is_refused(
    operation_id: str,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#15 AC-3: the writer is declared and ``registry.lookup`` returns its record, yet its ``call`` with a value for
    each path parameter and required ``Param`` exits 2 with no request although one would be answered, nothing on
    standard output, and an ERROR record naming the ID and ending ": no subcommand sends it"."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = {record.operation_id: record for record in family.OPERATIONS}
    assert operation_id in records, (
        f"{operation_id} has no record in {FAMILY}.OPERATIONS, so its refusal proves nothing (#15 AC-1, AC-3): "
        f"{sorted(records)}"
    )
    assert registry.lookup(operation_id=operation_id) == records[operation_id], (
        f"registry.lookup returns another record for {operation_id} (#15 AC-3)"
    )
    argv = [operation_id, *WRITING_CALLS[operation_id]]
    answer_anything(fake=fake_gitlab)

    code = run_call(root=project, argv=argv)

    captured = capsys.readouterr()
    assert code == EXIT_USAGE, f"call {argv} exits {EXIT_USAGE}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [], f"a refused call sends no request (#15 AC-3): {sent(fake=fake_gitlab)}"
    assert captured.out == "", f"a refusal prints nothing on standard output:\n{captured.out}"
    messages = error_messages(caplog=caplog)
    assert any(operation_id in message and message.endswith(NO_SUBCOMMAND_SENDS_IT) for message in messages), (
        f"one log record names {operation_id!r} and ends {NO_SUBCOMMAND_SENDS_IT!r}: the gate refuses the writer, "
        f"which no subcommand sends (#15 AC-3); logged: {messages!r}"
    )


# --- #38 AC-4, #15 AC-1: kinds, required attributes, bodies ---------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """#38 AC-4, #15 AC-1: the ``Param``s that are not ``Kind.SCALAR`` carry the ``Kind`` of their row; the ``Param``s
    declared ``required`` are exactly the rows whose Required reads ``yes``; every record has a JSON body and no
    ``fixed`` pairs."""
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


# --- #38 AC-5, #15 AC-1: no record is paged -------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """#38 AC-5, #15 AC-1: "List all agent privileges" answers one object, so every record is ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {operation_id: PAGING_NONE for operation_id in RECORD_ENDPOINTS}
    assert paged == expected, "a record's Paging is not its section's (AC-5):\n" + mapping_difference(
        declared=paged, expected=expected
    )


# --- #38 AC-8: a download -----------------------------------------------------------------------------------------


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
