"""Contract tests of the product GitHub wrapper's records and its ``call`` command against the REST reference (issue
#28 design D5; AC-1.1, AC-3.1, AC-3.2).

The method has two halves. The reference half: ``reference_sections`` reads every
``docs/api-reference/github/rest/<category>.md`` once and keys its sections by operation ID. A section starts at its
line `` `<METHOD> <path>` · operationId `<id>` `` and ends at the next heading. Its host is the one its ``- Host: `…` ``
line names, ``https://api.github.com`` when it has none (issue #46 D5). Its path and query parameters are the rows of
its ``Parameter`` table, told apart by the ``In`` cell. Its body parameters are the first-level names of the
``Field`` table after a ``Request body (`application/json`…)`` line, read as ``docs/api-reference/README.md`` "Body
field paths" writes them: a row whose Type cell is ``constraint`` names no field, a leading variant label
(``{variant 1}``, ``{single_select}``) is removed with the ``.`` after it, and the name is the text before the first
``.``, ``[`` or ``{``. ``record_problems`` names every way a record differs from its section. The call half:
``expected_call`` is the ``CallShape`` the section documents for some path values, ``sent_call`` the shape of a request
the fake host recorded, and ``call_problems`` names every difference. ``is_unreachable`` states D5's rule for an
operation no ``sff-test-*`` repository can exercise; for such an operation the two halves are the whole proof.

The reference exists only in this repository, so this module lives in ``test/`` and is never installed into a project
(cross-wrapper decision X1). It loads ``github_api`` from ``src/payload/scripts/``, put on ``sys.path`` by
``scripts_on_path`` as ``test_github_wrapper_coverage.py`` does, and the fake host from
``src/payload/test/github_wrapper_fixtures.py`` by path, as ``test_github_wrapper_fork_parity.py`` does; a test builds
its project with ``fx.enter_project`` and loads the entry script with ``fx.load_script``. A test that needs
``commands/call.py`` imports it itself after asserting the file exists, so while it is not written the test fails on
that assertion. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_wrapper_contract.py`` (no network).
"""

from __future__ import annotations

import functools
import importlib
import importlib.util
import inspect
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Callable, Dict, FrozenSet, List, Mapping, Optional, Sequence, Set, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = ROOT / "src" / "payload" / "test" / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

SCRIPTS_DIR = ROOT / "src" / "payload" / "scripts"
ENTRY_SCRIPT = SCRIPTS_DIR / "github_wrapper.py"
WRAPPER_MODULE = "github_wrapper_contract_under_test"
PACKAGE = "github_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
MODULE_SEPARATOR = "."
PYTHON_SUFFIX = ".py"
REGISTRY = "registry"
TRANSPORT = "transport"
CALL_COMMAND = "commands.call"
BILLING_FAMILY = "families.billing"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
FAMILY_SEPARATOR = "/"

REFERENCE_DIR = ROOT / "docs" / "api-reference" / "github"
REST_DIR = REFERENCE_DIR / "rest"
OPERATIONS_INDEX = REFERENCE_DIR / "operations-index.md"
MARKDOWN_GLOB = "*.md"
INDEX_COUNT = "count"
INDEX_HEADING = re.compile(rf"^# .*\bevery operation \((?P<{INDEX_COUNT}>\d+)\)[ \t]*$", re.MULTILINE)

# A section's operation line: `` `<METHOD> <path>` · operationId `<id>` · [docs](...) `` (the middle dot is U+00B7).
MIDDLE_DOT = "\N{MIDDLE DOT}"
GROUP_METHOD = "method"
GROUP_PATH = "path"
GROUP_OPERATION_ID = "operation_id"
OPERATION_LINE = re.compile(
    rf"^`(?P<{GROUP_METHOD}>[A-Z]+) (?P<{GROUP_PATH}>/[^`\s]*)` {MIDDLE_DOT} "
    rf"operationId `(?P<{GROUP_OPERATION_ID}>[^`]+)`"
)
HEADING_PREFIX = "#"
# A section's host line, `` - Host: `https://uploads.github.com` (not `https://api.github.com`) ``; a section without
# one is on the REST API host (`conventions.md` "Hosts and base URLs").
GROUP_HOST = "host"
HOST_LINE = re.compile(rf"^- Host: `(?P<{GROUP_HOST}>[^`]+)`")
REST_API_HOST = "https://api.github.com"
TABLE_ROW_PREFIX = "|"
ESCAPED_CELL_SEPARATOR = "\\|"
#: A cell boundary: a ``|`` the generator did not escape (a Type cell such as ``string \| null`` holds escaped ones).
CELL_SEPARATOR = re.compile(r"(?<!\\)\|")
SEPARATOR_CELL = re.compile(r"^:?-+:?$")
CODE_QUOTE = "`"
PARAMETER_TABLE = "Parameter"
FIELD_TABLE = "Field"
JSON_REQUEST_BODY = "Request body (`application/json`"
IN_PATH = "path"
IN_QUERY = "query"
TYPE_CONSTRAINT = "constraint"
#: A field path's leading variant label, numbered (``{variant 1}``) or named (``{single_select}``), with its ``.``.
LEADING_VARIANT = re.compile(r"^\{[^{}]*\}\.")
#: Where a field path's first-level name ends: its first ``.``, ``[`` or ``{``.
NAME_END = re.compile(r"[.\[{]")
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
TABLE_PARAMETERS = "parameters"
TABLE_BODY = "body"
TABLE_OTHER = "other"

# D5's rule: no `sff-test-*` repository has an enterprise or an organisation, and these families need either one or a
# GitHub App's credentials.
UNREACHABLE_PLACEHOLDERS = ("{enterprise}", "{org}")
UNREACHABLE_FAMILIES = frozenset({"apps", "billing", "teams"})

# How a problem names what differs.
KIND_METHOD = "method"
KIND_PATH = "path"
KIND_PATH_PARAMETER = "path parameter"
KIND_QUERY = "query"
KIND_BODY = "body"
RECORD_DECLARES = "the record declares"
CALL_SENDS = "the call sends"
DECLARED = "declared"
SENT = "sent"

# The `call` command line (design D2).
CALL_SUBCOMMAND = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "--raw-field"
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"

# AC-3.2's unreachable operation, `rest/billing.md` "Update a budget for an organization" (D5's five steps).
BUDGET_UPDATE = "billing/update-budget-org"
METHOD_PATCH = "PATCH"
METHOD_PUT = "PUT"
BUDGET_PATH_TEMPLATE = "/organizations/{org}/settings/billing/budgets/{budget_id}"
PATH_ORG = "org"
PATH_BUDGET_ID = "budget_id"
BUDGET_PATH_VALUES = {PATH_ORG: "acme", PATH_BUDGET_ID: "b1"}
BUDGET_PATH = "/organizations/acme/settings/billing/budgets/b1"
BUDGET_SINGULAR_PATH = "/organizations/acme/settings/billing/budget/b1"
FIELD_BUDGET_AMOUNT = "budget_amount"
FIELD_PREVENT_FURTHER_USAGE = "prevent_further_usage"
FIELD_BUDGET_ALERTING = "budget_alerting"
FIELD_WILL_ALERT = "will_alert"
FIELD_EXPIRES_AT = "expires_at"
FIELD_AMOUNT = "amount"
QUERY_YEAR = "year"
BUDGET_BODY_NAMES = frozenset(
    {FIELD_BUDGET_AMOUNT, FIELD_PREVENT_FURTHER_USAGE, FIELD_BUDGET_ALERTING, FIELD_EXPIRES_AT}
)
BUDGET_CALL_ARGV = (
    "call",
    "billing/update-budget-org",
    "--path",
    "org=acme",
    "--path",
    "budget_id=b1",
    "--field",
    "budget_amount=100",
    "--field",
    "prevent_further_usage=true",
    "--field",
    'budget_alerting={"will_alert": false}',
    "--field",
    "expires_at=null",
)
#: The body the typed `--field` values make: a number, a boolean, an object and `null`.
BUDGET_BODY = {
    FIELD_BUDGET_AMOUNT: 100,
    FIELD_PREVENT_FURTHER_USAGE: True,
    FIELD_BUDGET_ALERTING: {FIELD_WILL_ALERT: False},
    FIELD_EXPIRES_AT: None,
}
#: AC-3.1's examples: both arms, the path arm only (`/orgs/{org}`), the family arm only (`/app`), and neither.
UNREACHABLE_EXAMPLES = {
    BUDGET_UPDATE: True,
    "orgs/get": True,
    "apps/get-authenticated": True,
    "issues/get": False,
}


# ---------------------------------------------------------------------------------------------------------------------
# The reference half (D5)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ReferenceSection:
    """One operation's section of ``rest/<category>.md``: its operation ID, method and path template, the names of its
    ``path`` and ``query`` rows, the first-level names of its JSON request body, and the host its ``- Host:`` line
    names, ``https://api.github.com`` when it has none."""

    operation_id: str
    method: str
    path: str
    path_names: FrozenSet[str]
    query_names: FrozenSet[str]
    body_names: FrozenSet[str]
    host: str = REST_API_HOST


def _cells(*, line: str) -> List[str]:
    """The stripped cells of one Markdown table row, split at the ``|`` the generator did not escape."""
    inner = line.strip()
    if inner.startswith(TABLE_ROW_PREFIX):
        inner = inner[len(TABLE_ROW_PREFIX) :]
    if inner.endswith(TABLE_ROW_PREFIX) and not inner.endswith(ESCAPED_CELL_SEPARATOR):
        inner = inner[: -len(TABLE_ROW_PREFIX)]
    return [cell.strip() for cell in CELL_SEPARATOR.split(string=inner)]


def _unquoted(*, cell: str) -> str:
    """A cell's text without the backticks of its code span."""
    return cell.strip(CODE_QUOTE)


def first_level_name(*, field_path: str) -> str:
    """The first-level body field a ``Field`` row's path names: its leading variant label and the ``.`` after it
    removed, then the text before the first ``.``, ``[`` or ``{``; ``ValueError`` when that leaves no name."""
    unlabelled = LEADING_VARIANT.sub(repl="", string=field_path, count=1)
    end = NAME_END.search(string=unlabelled)
    name = unlabelled if end is None else unlabelled[: end.start()]
    if not name:
        raise ValueError(f"the body field path {json.dumps(obj=field_path)} names no first-level field")
    return name


class _SectionReader:
    """Reads the lines of one section after its operation line: its ``- Host:`` line, the ``Parameter`` table's rows by
    their ``In`` cell, and the ``Field`` table that follows a JSON request-body line."""

    def __init__(self, *, operation_id: str, method: str, path: str, source: str) -> None:
        self._operation_id = operation_id
        self._method = method
        self._path = path
        self._source = source
        self._host = REST_API_HOST
        self._parameters: Dict[str, Set[str]] = {IN_PATH: set(), IN_QUERY: set()}
        self._body: Set[str] = set()
        self._table: Optional[str] = None
        self._body_follows = False

    def read(self, *, line: str) -> None:
        """Take one line of the section: a table's header starts it, a non-table line ends it, and a ``- Host:`` line
        names the section's host."""
        if not line.startswith(TABLE_ROW_PREFIX):
            self._table = None
            if line.startswith(JSON_REQUEST_BODY):
                self._body_follows = True
            host = HOST_LINE.match(string=line)
            if host is not None:
                self._host = host.group(GROUP_HOST)
            return
        cells = _cells(line=line)
        if self._table is None:
            self._table = self._kind_of(header=cells[0])
        elif not all(SEPARATOR_CELL.match(string=cell) for cell in cells):
            self._read_row(cells=cells)

    def _kind_of(self, *, header: str) -> str:
        if header == PARAMETER_TABLE:
            return TABLE_PARAMETERS
        if header == FIELD_TABLE and self._body_follows:
            self._body_follows = False
            return TABLE_BODY
        return TABLE_OTHER

    def _read_row(self, *, cells: Sequence[str]) -> None:
        name = _unquoted(cell=cells[0])
        if self._table == TABLE_PARAMETERS:
            location = cells[1]
            if location not in self._parameters:
                raise ValueError(
                    f"{self._source}: {json.dumps(obj=self._operation_id)} has the parameter "
                    f"{json.dumps(obj=name)} in {json.dumps(obj=location)}, neither {IN_PATH} nor {IN_QUERY}"
                )
            self._parameters[location].add(name)
        elif self._table == TABLE_BODY and cells[1] != TYPE_CONSTRAINT:
            self._body.add(first_level_name(field_path=name))

    def section(self) -> ReferenceSection:
        """What the lines read so far document."""
        return ReferenceSection(
            operation_id=self._operation_id,
            method=self._method,
            path=self._path,
            path_names=frozenset(self._parameters[IN_PATH]),
            query_names=frozenset(self._parameters[IN_QUERY]),
            body_names=frozenset(self._body),
            host=self._host,
        )


def _file_sections(*, path: Path) -> List[ReferenceSection]:
    """Every section of one ``rest/<category>.md``: each from its operation line to the next heading or operation
    line."""
    sections: List[ReferenceSection] = []
    reader: Optional[_SectionReader] = None
    for line in path.read_text(encoding="utf-8").splitlines():
        opened = OPERATION_LINE.match(string=line)
        if opened is not None or line.startswith(HEADING_PREFIX):
            if reader is not None:
                sections.append(reader.section())
            reader = None
            if opened is not None:
                reader = _SectionReader(
                    operation_id=opened.group(GROUP_OPERATION_ID),
                    method=opened.group(GROUP_METHOD),
                    path=opened.group(GROUP_PATH),
                    source=path.name,
                )
        elif reader is not None:
            reader.read(line=line)
    if reader is not None:
        sections.append(reader.section())
    return sections


def reference_sections(*, rest_dir: Path) -> Dict[str, ReferenceSection]:
    """Every section of every ``rest_dir/<category>.md``, each file read once, keyed by operation ID; an operation ID
    with two sections, or a directory with none, raises ``ValueError``."""
    sections: Dict[str, ReferenceSection] = {}
    for path in sorted(rest_dir.glob(pattern=MARKDOWN_GLOB)):
        for section in _file_sections(path=path):
            if section.operation_id in sections:
                raise ValueError(
                    f"{path.name}: the operation ID {json.dumps(obj=section.operation_id)} has two sections"
                )
            sections[section.operation_id] = section
    if not sections:
        raise ValueError(f"{rest_dir} holds no operation section")
    return sections


def _value_problem(*, kind: str, documented: str, actual: str, actor: str) -> List[str]:
    """A problem naming both values when ``actual`` is not what the section documents; none when it is."""
    if actual == documented:
        return []
    return [f"{kind}: the section documents {json.dumps(obj=documented)}, {actor} {json.dumps(obj=actual)}"]


def _names_problem(*, kind: str, documented: AbstractSet[str], actual: AbstractSet[str], actual_by: str) -> List[str]:
    """A problem naming every documented name ``actual`` lacks and every name it holds the section does not document;
    none when the two sets are equal."""
    missing = sorted(set(documented) - set(actual))
    extra = sorted(set(actual) - set(documented))
    if not missing and not extra:
        return []
    return [
        f"{kind} names: documented and not {actual_by} {json.dumps(obj=missing)}; "
        f"{actual_by} and not documented {json.dumps(obj=extra)}"
    ]


def record_problems(*, record: Any, section: Optional[ReferenceSection]) -> List[str]:
    """Every way ``record`` (a ``RestOperation``) differs from ``section`` in its method, its path, and its path, query
    and body parameter names, each problem naming the record; a record with no section is itself a problem."""
    prefix = json.dumps(obj=record.operation_id)
    if section is None:
        return [f"{prefix}: no section of rest/*.md has this operation ID"]
    problems = [
        *_value_problem(kind=KIND_METHOD, documented=section.method, actual=record.method, actor=RECORD_DECLARES),
        *_value_problem(kind=KIND_PATH, documented=section.path, actual=record.path, actor=RECORD_DECLARES),
        *_names_problem(
            kind=KIND_PATH_PARAMETER,
            documented=section.path_names,
            actual=frozenset(PATH_PLACEHOLDER.findall(string=record.path)),
            actual_by=DECLARED,
        ),
        *_names_problem(
            kind=KIND_QUERY, documented=section.query_names, actual=record.query_params, actual_by=DECLARED
        ),
        *_names_problem(kind=KIND_BODY, documented=section.body_names, actual=record.body_params, actual_by=DECLARED),
    ]
    return [f"{prefix}: {problem}" for problem in problems]


# ---------------------------------------------------------------------------------------------------------------------
# The call half (D5)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CallShape:
    """A call as the method compares it: its method, its path as sent, its query names and its body member names."""

    method: str
    path: str
    query_names: FrozenSet[str]
    body_names: FrozenSet[str]


def expected_call(*, section: ReferenceSection, values: Mapping[str, str]) -> CallShape:
    """The call ``section`` documents: its method, its path with each ``{name}`` replaced by ``values[name]`` (the test
    values are alphanumeric, so nothing needs encoding), and its query and body names. A placeholder ``values`` lacks
    raises ``ValueError``."""

    def value_of(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(
                f"no test value for the path parameter {json.dumps(obj=name)} of {json.dumps(obj=section.path)}"
            )
        return values[name]

    return CallShape(
        method=section.method,
        path=PATH_PLACEHOLDER.sub(repl=value_of, string=section.path),
        query_names=section.query_names,
        body_names=section.body_names,
    )


def sent_call(*, request: Any) -> CallShape:
    """The shape of a request the fake host recorded: its method, its path as sent, the names of its decoded query and
    the member names of its JSON body; a body that is not a JSON object raises ``ValueError``."""
    body = request.json()
    if body is not None and not isinstance(body, dict):
        raise ValueError(f"the body of {request.method} {request.url} is not a JSON object: {json.dumps(obj=body)}")
    return CallShape(
        method=request.method,
        path=request.path,
        query_names=frozenset(request.query),
        body_names=frozenset(body or {}),
    )


def call_problems(*, expected: CallShape, sent: CallShape) -> List[str]:
    """Every way ``sent`` differs from ``expected``: its method, its path, its query names and its body names."""
    return [
        *_value_problem(kind=KIND_METHOD, documented=expected.method, actual=sent.method, actor=CALL_SENDS),
        *_value_problem(kind=KIND_PATH, documented=expected.path, actual=sent.path, actor=CALL_SENDS),
        *_names_problem(kind=KIND_QUERY, documented=expected.query_names, actual=sent.query_names, actual_by=SENT),
        *_names_problem(kind=KIND_BODY, documented=expected.body_names, actual=sent.body_names, actual_by=SENT),
    ]


def is_unreachable(*, operation_id: str, path: str) -> bool:
    """D5's rule: the operation's path names ``{enterprise}`` or ``{org}``, or its family is ``apps``, ``billing`` or
    ``teams``."""
    family = operation_id.partition(FAMILY_SEPARATOR)[0]
    return family in UNREACHABLE_FAMILIES or any(placeholder in path for placeholder in UNREACHABLE_PLACEHOLDERS)


# ---------------------------------------------------------------------------------------------------------------------
# Loading the package and running the entry script
# ---------------------------------------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The product scripts directory first on ``sys.path``, so ``github_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_product_module(*, name: str) -> ModuleType:
    """``github_api.<name>`` (``commands.call``, ``registry``) from the product scripts directory; while its file is
    not written, the calling test fails on this assertion, and a ``github_api`` imported from any other directory fails
    it too."""
    *packages, stem = name.split(MODULE_SEPARATOR)
    path = PACKAGE_DIR.joinpath(*packages, f"{stem}{PYTHON_SUFFIX}")
    assert path.is_file(), f"{path.relative_to(SCRIPTS_DIR).as_posix()} is not written: {path} does not exist"
    module = importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == path.resolve(), f"{module.__name__} was imported from {loaded_from}, not from {path}"
    return module


def _declared_records(*, registry: ModuleType) -> List[Any]:
    """Every ``RestOperation`` of every family module ``registry.discover_families()`` yields."""
    return [
        record
        for module in registry.discover_families()
        for record in module.OPERATIONS
        if isinstance(record, registry.RestOperation)
    ]


def _load_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The product entry script, freshly loaded by path as ``test_github_wrapper_compat.load_wrapper`` loads it."""
    return fx.load_script(path=ENTRY_SCRIPT, name=WRAPPER_MODULE, monkeypatch=monkeypatch)


def _exit_code_of(*, wrapper: ModuleType, argv: Sequence[str]) -> int:
    """The exit code of ``wrapper.main(argv=argv)``: its return value, or the code of the ``SystemExit`` it raises."""
    main = getattr(wrapper, "main", None)
    assert callable(main), f"{ENTRY_SCRIPT} defines no main"
    assert "argv" in inspect.signature(main).parameters, f"{ENTRY_SCRIPT}: main takes no argv"
    try:
        result = main(argv=list(argv))
    except SystemExit as exc:
        return fx.exit_code_of(exc=exc)
    assert isinstance(result, int), f"main(argv={list(argv)}) returned {result!r}, not an exit code"
    return result


def _budget_record(*, registry: ModuleType, transport: ModuleType, body_params: FrozenSet[str]) -> Any:
    """``billing/update-budget-org`` as a slice would declare it (D5 step 1): path parameters ``org`` and
    ``budget_id``, no query, the body ``body_params``, no paging, the default API version and media type."""
    return registry.RestOperation(
        operation_id=BUDGET_UPDATE,
        method=METHOD_PATCH,
        path=BUDGET_PATH_TEMPLATE,
        query_params=frozenset(),
        body_params=body_params,
        multi_segment=frozenset(),
        paging=registry.Paging.NONE,
        item_key=None,
        api_version=transport.API_VERSION_DEFAULT,
        accept=transport.ACCEPT_JSON,
    )


@dataclass(frozen=True)
class PlannedCall:
    """One record's ``call`` in the every-record test: the argv, the shape its section documents, and the route that
    answers exactly that method, path and query on the section's host."""

    operation_id: str
    argv: Tuple[str, ...]
    expected: CallShape
    route: Any


def _value_of(*, name: str) -> str:
    """A parameter's test value: alphanumeric, so expanding a path needs no encoding (D5), and made from the name, so a
    value given under another name changes the path."""
    return f"{TEST_VALUE_PREFIX}{NON_ALPHANUMERIC.sub(repl='', string=name)}"


def _answer_of(*, record: Any, link: Any) -> Any:
    """What the host answers the record's call with (D5): ``[]`` for a ``Paging.LINK`` record, under its ``item_key``
    when it has one, and ``{}`` for any other."""
    if record.paging != link:
        return {}
    return [] if record.item_key is None else {record.item_key: []}


def _plan_call(*, record: Any, section: ReferenceSection, link: Any) -> PlannedCall:
    """The ``call`` of ``record`` giving a value for every path, query and body parameter ``section`` documents, with
    ``--path``, ``--query`` and ``--raw-field``, and the route of the call the section documents, on its host."""
    names = section.path_names | section.query_names | section.body_names
    names |= frozenset(PATH_PLACEHOLDER.findall(string=section.path))
    values = {name: _value_of(name=name) for name in names}
    expected = expected_call(section=section, values=values)
    argv = [CALL_SUBCOMMAND, record.operation_id]
    for option, documented in (
        (OPTION_PATH, section.path_names),
        (OPTION_QUERY, section.query_names),
        (OPTION_RAW_FIELD, section.body_names),
    ):
        argv.extend(token for name in sorted(documented) for token in (option, f"{name}={values[name]}"))
    route = fx.StaticRouteSpec(
        method=section.method,
        url=f"{section.host}{expected.path}",
        replies=(fx.Reply(body=_answer_of(record=record, link=link)),),
        query={name: values[name] for name in section.query_names},
    )
    return PlannedCall(operation_id=record.operation_id, argv=tuple(argv), expected=expected, route=route)


def _problems_of_run(
    *,
    wrapper: ModuleType,
    host: Any,
    planned: PlannedCall,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> List[str]:
    """Run ``planned`` through the entry script's ``main``: a refusal or any exit but 0 is a problem, so is any count
    of requests but one, and the call half names how the request differs from its section."""
    caplog.clear()
    first = len(host.requests)
    try:
        exit_code: Optional[int] = _exit_code_of(wrapper=wrapper, argv=planned.argv)
    except pytest.fail.Exception:
        # The fake host fails the test on a request no route answers, after recording it: the call half below names
        # how that request differs from the section, and every other record is still called.
        exit_code = None
    stderr = capsys.readouterr().err
    sent = host.requests[first:]
    problems = []
    if exit_code != fx.EXIT_OK:
        outcome = "the fake host has no route for its request" if exit_code is None else f"exit {exit_code}, not 0"
        problems.append(f"{outcome}; log {caplog.messages}; stderr {stderr!r}")
    if len(sent) != 1:
        problems.append(f"{len(sent)} requests sent, one expected")
    problems.extend(
        problem
        for request in sent[:1]
        for problem in call_problems(expected=planned.expected, sent=sent_call(request=request))
    )
    return [f"{json.dumps(obj=planned.operation_id)}: {problem}" for problem in problems]


# ---------------------------------------------------------------------------------------------------------------------
# AC-3.2's rejection cases (D5)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RejectionCase(ABC):
    """One of D5's five ways a call or a record differs from the ``billing/update-budget-org`` section, and the words
    the one problem the method returns for it must hold."""

    name: str
    named: Tuple[str, ...]

    @abstractmethod
    def problems(self, *, section: ReferenceSection, expected: CallShape, record_of: Callable[..., Any]) -> List[str]:
        """What the method returns for this difference."""


@dataclass(frozen=True)
class SentCallDiffers(RejectionCase):
    """A sent shape that is the expected one but for its method, its path, an added query name or a renamed body
    member."""

    method: Optional[str] = None
    path: Optional[str] = None
    query_added: FrozenSet[str] = frozenset()
    body_renamed: Tuple[Tuple[str, str], ...] = ()

    def problems(self, *, section: ReferenceSection, expected: CallShape, record_of: Callable[..., Any]) -> List[str]:
        """``call_problems`` of the expected shape and this sent one."""
        del section, record_of  # the call half compares the two shapes only
        renamed = dict(self.body_renamed)
        sent = CallShape(
            method=expected.method if self.method is None else self.method,
            path=expected.path if self.path is None else self.path,
            query_names=expected.query_names | self.query_added,
            body_names=frozenset(renamed.get(name, name) for name in expected.body_names),
        )
        return call_problems(expected=expected, sent=sent)


@dataclass(frozen=True)
class RecordDiffers(RejectionCase):
    """The record as a slice would declare it but for the body names in ``body_removed``."""

    body_removed: FrozenSet[str] = frozenset()

    def problems(self, *, section: ReferenceSection, expected: CallShape, record_of: Callable[..., Any]) -> List[str]:
        """``record_problems`` of that record and the section."""
        del expected  # the reference half compares the record with its section only
        return record_problems(record=record_of(body_params=BUDGET_BODY_NAMES - self.body_removed), section=section)


def _case_name(case: RejectionCase) -> str:
    """The test id of ``case``."""
    return case.name


REJECTION_CASES: Tuple[RejectionCase, ...] = (
    SentCallDiffers(
        name="method-put",
        named=(KIND_METHOD, json.dumps(obj=METHOD_PUT), json.dumps(obj=METHOD_PATCH)),
        method=METHOD_PUT,
    ),
    SentCallDiffers(
        name="path-budget-not-budgets",
        named=(KIND_PATH, json.dumps(obj=BUDGET_SINGULAR_PATH), json.dumps(obj=BUDGET_PATH)),
        path=BUDGET_SINGULAR_PATH,
    ),
    SentCallDiffers(
        name="body-amount-for-budget-amount",
        named=(KIND_BODY, json.dumps(obj=FIELD_AMOUNT), json.dumps(obj=FIELD_BUDGET_AMOUNT)),
        body_renamed=((FIELD_BUDGET_AMOUNT, FIELD_AMOUNT),),
    ),
    SentCallDiffers(
        name="query-year",
        named=(KIND_QUERY, json.dumps(obj=QUERY_YEAR)),
        query_added=frozenset({QUERY_YEAR}),
    ),
    RecordDiffers(
        name="record-without-expires-at",
        named=(KIND_BODY, json.dumps(obj=FIELD_EXPIRES_AT)),
        body_removed=frozenset({FIELD_EXPIRES_AT}),
    ),
)


# ---------------------------------------------------------------------------------------------------------------------
# D5's reader sections
# ---------------------------------------------------------------------------------------------------------------------


def _section_id(section: ReferenceSection) -> str:
    """The test id of an expected section."""
    return section.operation_id


READ_SECTIONS: Tuple[ReferenceSection, ...] = (
    # Every first-level field, and no `labels[]{variant 2}.…` row leaking in as a name of its own.
    ReferenceSection(
        operation_id="issues/create",
        method="POST",
        path="/repos/{owner}/{repo}/issues",
        path_names=frozenset({"owner", "repo"}),
        query_names=frozenset(),
        body_names=frozenset(
            {
                "title",
                "body",
                "assignee",
                "milestone",
                "labels",
                "assignees",
                "issue_field_values",
                "type",
                "parent_issue_id",
            }
        ),
    ),
    # A numbered variant label: `{variant 1}.labels`.
    ReferenceSection(
        operation_id="issues/add-labels",
        method="POST",
        path="/repos/{owner}/{repo}/issues/{issue_number}/labels",
        path_names=frozenset({"owner", "repo", "issue_number"}),
        query_names=frozenset(),
        body_names=frozenset({"labels"}),
    ),
    # Numbered and named variant labels: `{variant 2}.name`, `{single_select}.single_select_options`, `{iteration}.…`.
    ReferenceSection(
        operation_id="projects/add-field-for-org",
        method="POST",
        path="/orgs/{org}/projectsV2/{project_number}/fields",
        path_names=frozenset({"org", "project_number"}),
        query_names=frozenset(),
        body_names=frozenset(
            {"issue_field_id", "name", "data_type", "single_select_options", "iteration_configuration"}
        ),
    ),
    # A `(body)` row of Type `constraint`, which names no field.
    ReferenceSection(
        operation_id="pulls/request-reviewers",
        method="POST",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers",
        path_names=frozenset({"owner", "repo", "pull_number"}),
        query_names=frozenset(),
        body_names=frozenset({"reviewers", "team_reviewers"}),
    ),
    # Path and query rows told apart by the `In` cell.
    ReferenceSection(
        operation_id="actions/get-workflow-run",
        method="GET",
        path="/repos/{owner}/{repo}/actions/runs/{run_id}",
        path_names=frozenset({"owner", "repo", "run_id"}),
        query_names=frozenset({"exclude_pull_requests"}),
        body_names=frozenset(),
    ),
    # A `- Host:` line naming another host, and a request body that is not JSON, which names no field.
    ReferenceSection(
        operation_id="repos/upload-release-asset",
        method="POST",
        path="/repos/{owner}/{repo}/releases/{release_id}/assets",
        path_names=frozenset({"owner", "repo", "release_id"}),
        query_names=frozenset({"name", "label"}),
        body_names=frozenset(),
        host="https://uploads.github.com",
    ),
)


# ---------------------------------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(argnames="expected", argvalues=READ_SECTIONS, ids=_section_id)
def test_a_section_is_read_as_the_reference_writes_it(expected: ReferenceSection) -> None:
    """AC-3.2 (the reader the method uses): ``reference_sections`` reads one section per operation the index heading
    counts, and D5's sections as the reference writes them: their method, path, host, path and query rows, and the
    first-level body names under D5's rules for variant labels and ``constraint`` rows."""
    sections = reference_sections(rest_dir=REST_DIR)

    heading = INDEX_HEADING.search(string=OPERATIONS_INDEX.read_text(encoding="utf-8"))
    assert heading is not None, f"{OPERATIONS_INDEX.name} has no `every operation (N)` heading"
    assert len(sections) == int(heading.group(INDEX_COUNT)), (
        f"{len(sections)} sections read from {REST_DIR}, the index heading counts {heading.group(INDEX_COUNT)}"
    )
    assert sections.get(expected.operation_id) == expected


@pytest.mark.usefixtures("scripts_on_path")
def test_every_record_matches_its_reference_section() -> None:
    """AC-1.1, AC-3.2: every record ``discover_families`` yields documents its section's method, path, and path, query
    and body parameter names; the failure names each record and each difference."""
    sections = reference_sections(rest_dir=REST_DIR)
    records = _declared_records(registry=_import_product_module(name=REGISTRY))
    assert records, "discover_families() yields no record, so there is nothing to check against the reference"

    problems = [
        problem
        for record in records
        for problem in record_problems(record=record, section=sections.get(record.operation_id))
    ]

    assert not problems, f"{len(problems)} differences between records and their sections:\n" + "\n".join(problems)


@pytest.mark.usefixtures("scripts_on_path")
def test_every_record_is_sent_as_its_section_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-1.1: every record outside ``GATED_OPERATIONS``, called through the product's ``main`` in one project against
    one fake host with a value for every parameter its section documents, exits 0 and sends one request whose method,
    path, query names and body names are the section's."""
    gated = _import_product_module(name=CALL_COMMAND).GATED_OPERATIONS
    registry = _import_product_module(name=REGISTRY)
    sections = reference_sections(rest_dir=REST_DIR)
    records = [record for record in _declared_records(registry=registry) if record.operation_id not in gated]
    assert records, f"every record is in GATED_OPERATIONS {sorted(gated)}, so no record is called"
    problems: List[str] = []
    planned: List[PlannedCall] = []
    for record in records:
        section = sections.get(record.operation_id)
        if section is None:
            problems.append(f"{json.dumps(obj=record.operation_id)}: no section of rest/*.md has this operation ID")
            continue
        planned.append(_plan_call(record=record, section=section, link=registry.Paging.LINK))
    host = fx.enter_project(
        project=fx.PROJECT, root=tmp_path, monkeypatch=monkeypatch, routes=[each.route for each in planned]
    )
    wrapper = _load_wrapper(monkeypatch=monkeypatch)
    caplog.set_level(level=logging.INFO)

    for each in planned:
        problems.extend(_problems_of_run(wrapper=wrapper, host=host, planned=each, capsys=capsys, caplog=caplog))

    assert not problems, f"{len(problems)} problems calling {len(planned)} records:\n" + "\n".join(problems)
    host.assert_every_request_routed()


@pytest.mark.usefixtures("scripts_on_path")
def test_an_unreachable_call_matches_its_reference_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-3.1, AC-3.2: ``is_unreachable`` holds for ``billing/update-budget-org`` (both arms), ``orgs/get`` (the path
    arm) and ``apps/get-authenticated`` (the family arm), not for ``issues/get``; that operation's record, built as a
    slice would write it, matches its section, and its ``call`` with typed ``--field`` values exits 0 and sends the
    call its section documents with the typed body."""
    sections = reference_sections(rest_dir=REST_DIR)
    judged = {
        operation_id: is_unreachable(operation_id=operation_id, path=sections[operation_id].path)
        for operation_id in UNREACHABLE_EXAMPLES
    }
    assert judged == UNREACHABLE_EXAMPLES
    section = sections[BUDGET_UPDATE]
    registry = _import_product_module(name=REGISTRY)
    # Step 1 and 2: the record a slice would write, and the reference half on it.
    record = _budget_record(
        registry=registry,
        transport=_import_product_module(name=TRANSPORT),
        body_params=BUDGET_BODY_NAMES,
    )
    assert record_problems(record=record, section=section) == []
    # Step 3: the record declared, for this test only, in place of any record the family already declares of its ID
    # (issue #33 DL-005), so the ID is declared once and `registry.lookup` returns this record.
    billing = _import_product_module(name=BILLING_FAMILY)
    others = tuple(
        each
        for each in billing.OPERATIONS
        if not (isinstance(each, registry.RestOperation) and each.operation_id == record.operation_id)
    )
    monkeypatch.setattr(target=billing, name=ATTRIBUTE_OPERATIONS, value=(*others, record))
    expected = expected_call(section=section, values=BUDGET_PATH_VALUES)
    assert expected.path == BUDGET_PATH
    # Step 4: the call through the product's `main`, against a host that answers the `PATCH`.
    host = fx.enter_project(
        project=fx.PROJECT,
        root=tmp_path,
        monkeypatch=monkeypatch,
        routes=(fx.StaticRouteSpec(method=METHOD_PATCH, url=BUDGET_PATH, replies=(fx.Reply(body={}),)),),
    )
    caplog.set_level(level=logging.INFO)

    exit_code = _exit_code_of(wrapper=_load_wrapper(monkeypatch=monkeypatch), argv=BUDGET_CALL_ARGV)

    # Step 5: exit 0, the call half finds nothing, and the body holds the typed values.
    stderr = capsys.readouterr().err
    assert exit_code == fx.EXIT_OK, f"exit {exit_code}; log {caplog.messages}; stderr {stderr!r}"
    assert len(host.requests) == 1, f"{len(host.requests)} requests sent, one expected: {host.urls()}"
    request = host.requests[0]
    assert call_problems(expected=expected, sent=sent_call(request=request)) == []
    assert request.json() == BUDGET_BODY
    # `==` holds `1` and `true` equal; the JSON text tells a number from a boolean.
    assert json.dumps(obj=request.json(), sort_keys=True) == json.dumps(obj=BUDGET_BODY, sort_keys=True)
    host.assert_every_request_routed()


@pytest.mark.usefixtures("scripts_on_path")
@pytest.mark.parametrize(argnames="case", argvalues=REJECTION_CASES, ids=_case_name)
def test_the_method_rejects_a_call_that_differs(case: RejectionCase) -> None:
    """AC-3.2: against the ``billing/update-budget-org`` section, which the unchanged call and record match, a sent
    method ``PUT``, a path ``…/budget/b1``, a body member ``amount`` in place of ``budget_amount``, a query name
    ``year``, and a record whose ``body_params`` lack ``expires_at`` each give one problem naming that difference."""
    section = reference_sections(rest_dir=REST_DIR)[BUDGET_UPDATE]
    record_of = functools.partial(
        _budget_record,
        registry=_import_product_module(name=REGISTRY),
        transport=_import_product_module(name=TRANSPORT),
    )
    expected = expected_call(section=section, values=BUDGET_PATH_VALUES)
    assert call_problems(expected=expected, sent=expected) == [], "the unchanged call already differs"
    assert record_problems(record=record_of(body_params=BUDGET_BODY_NAMES), section=section) == [], (
        "the unchanged record already differs"
    )

    problems = case.problems(section=section, expected=expected, record_of=record_of)

    assert len(problems) == 1, f"{case.name}: the method returned {problems}, one problem expected"
    unnamed = [word for word in case.named if word not in problems[0]]
    assert not unnamed, f"{case.name}: the problem {problems[0]!r} does not name {unnamed}"
