"""Tests for ``gitlab_api/families/orbit.py``, the ``orbit`` endpoint family of the GitLab wrapper (issue #38, the
remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4 and AC-5; issue #15, the kept keys;
``change.md`` AC-1, AC-2 and AC-4).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose key sorts to this module, ``key_families`` of
``test/test_gitlab_wrapper_coverage.py``) and ``docs/api-reference/gitlab/rest/orbit.md`` (each section's endpoints, its
heading, and the ``In``, ``Type``, ``Required`` and ``Notes`` columns of its ``| Attribute | In | Type |`` table). What
is pinned:

- AC-1 (#15 AC-1): ``OPERATIONS`` as ``{operation_id: (method, path)}`` is ``RECORD_ENDPOINTS``, each ID declared once:
  every Reference of those rows with its section's endpoint (of several, the first ``/projects/:id/...`` one, else the
  first), the glob ``GET /orbit/skills/:name/*path`` of ``orbit#retrieve-a-deployed-skill-file`` included, whose two
  rows are path rows, so it has no ``Param``;
- #15 AC-2: ``PENDING`` is empty;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``ARRAY`` for a ``string array`` row, ``HASH`` for
  ``hash``); the ``required`` names of every record, exactly its query and body rows whose Required reads ``yes`` (a
  ``conditional`` is not ``yes``); a JSON body and no ``fixed`` pairs on every record;
- AC-5: the ``Paging`` of every record: ``OFFSET`` for a ``GET`` section headed "List" or with a ``page`` row, ``NONE``
  for every other, none ``KEYSET``; every ``orbit#`` list answers one object, so every record is ``NONE``;
- #15 AC-4: ``call orbit#retrieve-a-deployed-skill-file --path name=code-review --path path=references/usage.md``
  exits 0 and sends one ``GET`` whose path keeps each ``/`` of the glob value, each part one encoded segment (#40
  design.md D1); a value with an empty or ``..`` part is refused as ``registry.expand`` refuses it: exit 1, no request,
  and an ERROR record naming ``*path``.

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test, so the module collects whatever the family declares. The fake GitLab host
and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test; ``call`` runs
through the product's entry script ``main`` in a scratch project whose ``config/gitlab.json`` names the fake host.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_orbit.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_orbit_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY = "orbit"
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
TOKEN = "glpat-gitlab-api-orbit-test"  # pragma: allowlist secret
PROJECT_ID = 4242

# The exit codes of `call` (commands/call.py): sent, and a GitLabAPIError (an empty, `.` or `..` glob part included).
EXIT_OK = 0
EXIT_API_ERROR = 1
METHOD_GET = "GET"
FIELD_ID = "id"
ANSWER: Dict[str, Any] = {FIELD_ID: 1}

# The `registry.Kind`, `registry.BodyFormat` and `registry.Paging` member names the tables hold, and the `fixed`
# pairs every record carries (none).
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
BODY_JSON = "JSON"
PAGING_NONE = "NONE"
NO_FIXED: Tuple[Tuple[str, str], ...] = ()

# --- The tables, transcribed from docs/api-reference/gitlab -----------------------------------------------------------

# operations-index.md and rest/orbit.md: every record, by ID, sorted: each Reference of the rows whose key sorts to this
# module (`key_families`), with the method and path of its section's endpoint (AC-1; #15 AC-1).
RECORD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "orbit#check-deployed-skill-metadata": ("HEAD", "/orbit/skills/:name"),
    "orbit#list-all-deployed-skills": ("GET", "/orbit/skills"),
    "orbit#list-all-graph-entities-that-match-a-search": ("GET", "/orbit/grep"),
    "orbit#retrieve-a-deployed-skill": ("GET", "/orbit/skills/:name"),
    "orbit#retrieve-a-deployed-skill-file": ("GET", "/orbit/skills/:name/*path"),
    "orbit#retrieve-entity-context": ("POST", "/orbit/context"),
    "orbit#run-a-named-query": ("POST", "/orbit/query/:name"),
    "orbit#run-a-query": ("POST", "/orbit/query"),
}

# rest/orbit.md: every query and body row of a record whose Kind is not SCALAR (AC-4). Every other row's Type is
# `string`, `integer` or `boolean`; "Retrieve a deployed skill file" has only its `name` and `path` path rows.
NON_SCALAR_PARAMS: Dict[Tuple[str, str], str] = {
    ("orbit#list-all-graph-entities-that-match-a-search", "scopes"): KIND_ARRAY,
    ("orbit#retrieve-entity-context", "tokens"): KIND_ARRAY,
    ("orbit#run-a-named-query", "parameters"): KIND_HASH,
}

# rest/orbit.md: the query and body rows whose Required reads `yes`, by record, in table order (AC-4); a record with
# none is not listed. `full_path`, `namespace_id` and `project_id` of the grep read `conditional`; the `name` and
# `path` rows of "Retrieve a deployed skill file" are path rows, no `Param`.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    "orbit#list-all-graph-entities-that-match-a-search": ("search",),
    "orbit#retrieve-entity-context": ("tokens",),
    "orbit#run-a-query": ("query",),
}

# #15 AC-4: "Retrieve a deployed skill file" (`GET /orbit/skills/:name/*path`), the `*path` value written with each `/`
# kept and each part one percent-encoded segment (#40 design.md D1), and a part that is no segment refused by
# `registry.expand` with an ERROR record naming the glob.
OP_RETRIEVE_SKILL_FILE = "orbit#retrieve-a-deployed-skill-file"
GLOB_NAMED = "*path"


class GlobCase(NamedTuple):
    """A call of "Retrieve a deployed skill file", a glob record: the arguments after its ID, the exit code, the
    requests it sends, and a text one ERROR record holds (``None`` for a call that is sent)."""

    arguments: Tuple[str, ...]
    code: int
    sent: Tuple[Tuple[str, str], ...]
    logged: Optional[str]


GLOB_CASES = (
    pytest.param(
        GlobCase(
            arguments=("--path", "name=code-review", "--path", "path=references/usage.md"),
            code=EXIT_OK,
            sent=((METHOD_GET, f"{REST_BASE}/orbit/skills/code-review/references/usage.md"),),
            logged=None,
        ),
        id="glob-holding-a-slash",
    ),
    pytest.param(
        GlobCase(
            arguments=("--path", "name=code-review", "--path", "path=references/usage notes.md"),
            code=EXIT_OK,
            sent=((METHOD_GET, f"{REST_BASE}/orbit/skills/code-review/references/usage%20notes.md"),),
            logged=None,
        ),
        id="glob-part-encoded",
    ),
    pytest.param(
        GlobCase(
            arguments=("--path", "name=code-review", "--path", "path=references//usage.md"),
            code=EXIT_API_ERROR,
            sent=(),
            logged=GLOB_NAMED,
        ),
        id="glob-part-empty-refused",
    ),
    pytest.param(
        GlobCase(
            arguments=("--path", "name=code-review", "--path", "path=references/../usage.md"),
            code=EXIT_API_ERROR,
            sent=(),
            logged=GLOB_NAMED,
        ),
        id="glob-part-dot-dot-refused",
    ),
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
    """Import ``gitlab_api.<name>`` (``FAMILY_MODULE`` for the family) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


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


# --- AC-1, #15 AC-2: the records, and nothing pending ----------------------------------------------------------------


def test_every_reference_has_its_record() -> None:
    """AC-1 (#15 AC-1): ``OPERATIONS`` declares, once each, every Reference of the module's index rows, each with the
    method and path of its section's endpoint."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared_ids = [record.operation_id for record in family.OPERATIONS]
    repeated = sorted({operation_id for operation_id in declared_ids if declared_ids.count(operation_id) > 1})
    assert repeated == [], f"{FAMILY}.OPERATIONS declares these IDs more than once: {repeated}"
    declared = {record.operation_id: (record.method, record.path) for record in family.OPERATIONS}
    assert declared == RECORD_ENDPOINTS, f"{FAMILY}.OPERATIONS is not the family's References (AC-1):\n" + (
        mapping_difference(declared=declared, expected=RECORD_ENDPOINTS)
    )


def test_nothing_is_pending() -> None:
    """#15 AC-2: ``PENDING`` is empty; the glob key issue #38 kept for #40, ``GET /orbit/skills/:name/*path``, has its
    record."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"{FAMILY}.PENDING holds {len(pending)} key(s); each has its record (#15 AC-2): {pending}"


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
    """AC-5: every ``orbit#`` list answers one object, so every record is ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {operation_id: PAGING_NONE for operation_id in RECORD_ENDPOINTS}
    assert paged == expected, "a record's Paging is not its section's (AC-5):\n" + mapping_difference(
        declared=paged, expected=expected
    )


# --- #15 AC-4: the glob record is sent with its slashes -------------------------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=GLOB_CASES)
def test_a_glob_record_is_sent_with_its_slashes(
    case: GlobCase,
    project: Path,
    fake_gitlab: Any,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """#15 AC-4: "Retrieve a deployed skill file" given ``name`` and its ``*path`` exits 0 and sends one ``GET`` whose
    path keeps each ``/`` of the value, each part one encoded segment; a part that is empty or ``..`` is refused by
    ``registry.expand`` (exit 1) with no request and an ERROR record naming ``*path``."""
    fake_gitlab.script_next(body=ANSWER)
    argv = (OP_RETRIEVE_SKILL_FILE, *case.arguments)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == case.code, f"call {list(argv)} exits {case.code}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == list(case.sent), "the requests the call sends (#15 AC-4)"
    if case.logged is None:
        return
    messages = error_messages(caplog=caplog)
    assert any(case.logged in message for message in messages), (
        f"an ERROR record holds {case.logged!r} (#40 AC-2.2): {messages}"
    )
