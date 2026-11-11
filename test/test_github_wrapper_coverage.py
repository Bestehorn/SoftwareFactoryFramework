"""Coverage, structure and standard-library tests of the product GitHub wrapper (design D7).

Every REST operation of the GitHub operations index and every capability of the "Only in GraphQL" table of the
GraphQL conventions is either covered (a record of the package declares it) or on a pending list (a family module's
``PENDING``, ``graphql_only.PENDING_CAPABILITIES``); the test names each one that is neither (AC-5). The family
modules follow the directory and each holds only its own family's IDs (AC-1.2, AC-1.3), and the entry script and the
package import only the standard library (UB-2.2).

The reference under ``docs/api-reference/github/`` exists only in this repository, so this module lives in ``test/``
and is never installed into a project (cross-wrapper decision X1). It reads the reference whole with ``index_rows`` and
``graphql_only`` and compares with the pure ``coverage_gaps``. It loads the product package ``github_api`` from
``src/payload/scripts/``, put on ``sys.path`` for each test that needs it; each test imports the package itself, so
while a module is not written the test fails on the assertion that names it. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_wrapper_coverage.py`` (CI runs it on Python 3.10, which has
``sys.stdlib_module_names``).
"""

from __future__ import annotations

import ast
import importlib
import re
import socket
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Mapping, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "src" / "payload" / "scripts"
ENTRY_SCRIPT = SCRIPTS_DIR / "github_wrapper.py"
PACKAGE = "github_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FAMILIES = "families"
FAMILIES_PACKAGE = f"{PACKAGE}.{FAMILIES}"
FAMILIES_DIR = PACKAGE_DIR / FAMILIES
REGISTRY = "registry"
GRAPHQL_ONLY = "graphql_only"
INIT_FILE = "__init__.py"
PYTHON_GLOB = "*.py"
PYTHON_SUFFIX = ".py"
MODULE_SEPARATOR = "."

REFERENCE_DIR = ROOT / "docs" / "api-reference" / "github"
OPERATIONS_INDEX = REFERENCE_DIR / "operations-index.md"
GRAPHQL_CONVENTIONS = REFERENCE_DIR / "graphql" / "conventions.md"

# The family module contract (D2) and the GraphQL capability module's names (D5).
ATTRIBUTE_FAMILY = "FAMILY"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING = "PENDING"
ATTRIBUTE_PENDING_CAPABILITIES = "PENDING_CAPABILITIES"
FAMILY_CONTRACT = (ATTRIBUTE_FAMILY, ATTRIBUTE_OPERATIONS, ATTRIBUTE_PENDING)
GRAPHQL_ONLY_CONTRACT = (ATTRIBUTE_OPERATIONS, ATTRIBUTE_PENDING_CAPABILITIES)
# The registry's record types and their fields (D4).
REST_OPERATION = "RestOperation"
GRAPHQL_OPERATION = "GraphQLOperation"
FAMILY_SEPARATOR = "/"
FAMILY_FILE_HYPHEN = "-"
FAMILY_FILE_UNDERSCORE = "_"

# The index: a table row is ``| <method> | `<path>` | `<operation id>` | <reference> |``, the heading carries the count.
HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"})
TABLE_ROW_PREFIX = "|"
CELL_SEPARATOR = "|"
CODE_QUOTE = "`"
INDEX_ROW_CELLS = 4
INDEX_COUNT = "count"
INDEX_HEADING = re.compile(r"^# .*\bevery operation \((?P<count>\d+)\)[ \t]*$", re.MULTILINE)
SEPARATOR_CELL = re.compile(r"^:?-+:?$")
ONLY_IN_GRAPHQL_MARKER = "**Only in GraphQL**"
IN_BOTH_MARKER = "**In both**"
CAPABILITY_HEADER = "Capability"

# AC-5.1's named rows: an index row, and the first and the last row of the "Only in GraphQL" table.
ISSUES_GET = "issues/get"
ISSUES_GET_ROW = ("GET", "/repos/{owner}/{repo}/issues/{issue_number}")
REPOSITORY_DISCUSSIONS = "Repository discussions"
WILDCARD_BRANCH_PROTECTION = "Branch protection with wildcard patterns"

# AC-5.2's synthetic reference: one covered, one pending and one uncovered item of each kind.
SYNTHETIC_COVERED_ID = "alpha/get-thing"
SYNTHETIC_PENDING_ID = "alpha/list-things"
SYNTHETIC_GAP_ID = "beta/delete-thing"
SYNTHETIC_INDEX = {
    SYNTHETIC_COVERED_ID: ("GET", "/things/{thing_id}"),
    SYNTHETIC_PENDING_ID: ("GET", "/things"),
    SYNTHETIC_GAP_ID: ("DELETE", "/things/{thing_id}"),
}
SYNTHETIC_COVERED_CAPABILITY = "Covered capability"
SYNTHETIC_PENDING_CAPABILITY = "Pending capability"
SYNTHETIC_GAP_CAPABILITY = "Uncovered capability"
SYNTHETIC_CAPABILITIES = (SYNTHETIC_COVERED_CAPABILITY, SYNTHETIC_PENDING_CAPABILITY, SYNTHETIC_GAP_CAPABILITY)

# AC-5.3's synthetic regeneration: a family module with one record and one pending ID, the index it matches before the
# regeneration, and the rows a regenerated index adds or changes.
REGENERATION_FAMILY = "gamma"
REGENERATION_MODULE = f"{FAMILIES_PACKAGE}{MODULE_SEPARATOR}{REGENERATION_FAMILY}"
REGENERATION_RECORD_ID = "gamma/get-widget"
REGENERATION_RECORD_ROW = ("GET", "/widgets/{widget_id}")
REGENERATION_PENDING_ID = "gamma/list-widgets"
REGENERATION_PENDING_ROW = ("GET", "/widgets")
REGENERATION_ADDED_ID = "gamma/delete-widget"
REGENERATION_ADDED_ROW = ("DELETE", "/widgets/{widget_id}")
REGENERATION_OTHER_PATH_ROW = (REGENERATION_RECORD_ROW[0], "/widgets/{widget_number}")
REGENERATION_OTHER_METHOD_ROW = ("PUT", REGENERATION_RECORD_ROW[1])
BEFORE_REGENERATION = {
    REGENERATION_RECORD_ID: REGENERATION_RECORD_ROW,
    REGENERATION_PENDING_ID: REGENERATION_PENDING_ROW,
}
NO_CAPABILITIES: tuple[str, ...] = ()

# AC-1.4's synthetic capability module: GraphQL records whose operation IDs are compared with each other and with the
# operation IDs of an index that holds one row, ``issues/get``'s.
SYNTHETIC_GRAPHQL_MODULE = "synthetic_graphql_only"
SYNTHETIC_FIRST_CAPABILITY = "First capability"
SYNTHETIC_SECOND_CAPABILITY = "Second capability"
SYNTHETIC_GRAPHQL_CAPABILITIES = (SYNTHETIC_FIRST_CAPABILITY, SYNTHETIC_SECOND_CAPABILITY)
SYNTHETIC_FIRST_GRAPHQL_ID = "graphql/firstMutation"
SYNTHETIC_SECOND_GRAPHQL_ID = "graphql/secondMutation"
SYNTHETIC_GRAPHQL_INDEX = {ISSUES_GET: ISSUES_GET_ROW}
SYNTHETIC_DOCUMENT = "mutation($input: SyntheticInput!) { synthetic(input: $input) { clientMutationId } }"
NO_CONNECTION: tuple[str, ...] = ()


# ---------------------------------------------------------------------------------------------------------------------
# Reading the reference (D7)
# ---------------------------------------------------------------------------------------------------------------------


def _cells(*, line: str) -> list[str]:
    """The stripped cells of one Markdown table row."""
    return [cell.strip() for cell in line.strip().strip(CELL_SEPARATOR).split(CELL_SEPARATOR)]


def _unquoted(*, cell: str) -> str:
    """A cell's text without the backticks of its code span."""
    return cell.strip(CODE_QUOTE)


def index_rows(*, path: Path) -> dict[str, tuple[str, str]]:
    """Every table row of the operations index whose first cell is an HTTP method, as ``{id: (method, path)}``.

    An operation ID on two rows raises ``ValueError``, so the mapping holds as many IDs as the index has rows.
    """
    rows: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith(TABLE_ROW_PREFIX):
            continue
        cells = _cells(line=line)
        if cells[0] not in HTTP_METHODS:
            continue
        if len(cells) != INDEX_ROW_CELLS:
            raise ValueError(f"{path.name}: the row {line!r} has {len(cells)} cells, not {INDEX_ROW_CELLS}")
        method, route, operation_id = cells[0], _unquoted(cell=cells[1]), _unquoted(cell=cells[2])
        if operation_id in rows:
            raise ValueError(f"{path.name}: the operation ID {operation_id!r} is on two rows")
        rows[operation_id] = (method, route)
    return rows


def _table_after(*, lines: list[str], start: int) -> list[list[str]]:
    """The rows of the first table after line ``start``, up to that table's end, as cell lists."""
    table: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith(TABLE_ROW_PREFIX):
            table.append(_cells(line=line))
        elif table:
            break
    return table


def _first_cells_of_table_after(*, path: Path, marker: str) -> list[str]:
    """The first cell of every data row of the table after the one line that starts with ``marker``."""
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [number for number, line in enumerate(lines) if line.startswith(marker)]
    if len(starts) != 1:
        raise ValueError(f"{path.name}: {len(starts)} lines start with {marker!r}, expected one")
    table = _table_after(lines=lines, start=starts[0])
    if len(table) < 2 or not all(SEPARATOR_CELL.match(cell) for cell in table[1]):
        raise ValueError(f"{path.name}: the table after {marker!r} has no header and separator row")
    return [row[0] for row in table[2:]]


def graphql_only(*, path: Path) -> list[str]:
    """The first cell of every row of the table after the ``**Only in GraphQL**`` line, up to that table's end."""
    return _first_cells_of_table_after(path=path, marker=ONLY_IN_GRAPHQL_MARKER)


def coverage_gaps(
    *,
    index: Mapping[str, tuple[str, str]],
    capabilities: Sequence[str],
    covered: AbstractSet[str],
    pending: AbstractSet[str],
) -> list[str]:
    """Every operation ID of ``index`` and every capability, sorted, that is neither covered nor pending."""
    accounted = set(covered) | set(pending)
    return sorted(item for item in (*index, *capabilities) if item not in accounted)


def gap_message(*, gaps: Sequence[str]) -> str:
    """The coverage test's failure message: every gap, one per line."""
    listed = "\n".join(f"  {gap}" for gap in gaps)
    return (
        f"{len(gaps)} operations and capabilities are neither covered by a record nor pending; declare a record, or "
        f"put each on its family module's {ATTRIBUTE_PENDING} (a capability on "
        f"{GRAPHQL_ONLY}.{ATTRIBUTE_PENDING_CAPABILITIES}):\n{listed}"
    )


# ---------------------------------------------------------------------------------------------------------------------
# Loading the package
# ---------------------------------------------------------------------------------------------------------------------


def _refuse_connection(self: socket.socket, address: object) -> None:
    pytest.fail(reason=f"a coverage test opened a connection to {address!r}; it reads files only")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs opens a socket connection."""
    monkeypatch.setattr(target=socket.socket, name="connect", value=_refuse_connection)
    monkeypatch.setattr(target=socket.socket, name="connect_ex", value=_refuse_connection)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The product scripts directory first on ``sys.path``, so ``github_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_package_module(*, name: str) -> ModuleType:
    """``github_api.<name>`` from the product scripts directory; while its file is not written, the calling test fails
    on this assertion, and a ``github_api`` imported from any other directory fails it too."""
    path = PACKAGE_DIR / f"{name}{PYTHON_SUFFIX}"
    assert path.is_file(), f"{PACKAGE}/{name}{PYTHON_SUFFIX} is not written: {path} does not exist"
    module = importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == path.resolve(), f"{module.__name__} was imported from {loaded_from}, not from {path}"
    return module


def _family_modules(*, registry: ModuleType) -> list[ModuleType]:
    """What ``registry.discover_families()`` returns, which D2 makes the imported family modules."""
    families = list(registry.discover_families())
    not_modules = [repr(item) for item in families if not isinstance(item, ModuleType)]
    assert not not_modules, f"registry.discover_families() must yield the imported family modules, not {not_modules}"
    return families


def _assert_contract(*, modules: Sequence[ModuleType], names: Sequence[str]) -> None:
    lacking = [f"{module.__name__} lacks {name}" for module in modules for name in names if not hasattr(module, name)]
    assert not lacking, "modules without the names their contract declares:\n" + "\n".join(lacking)


def _module_stem(*, module: ModuleType) -> str:
    return module.__name__.rpartition(MODULE_SEPARATOR)[2]


def _family_of(*, operation_id: str) -> str:
    return operation_id.partition(FAMILY_SEPARATOR)[0]


def _module_name_of(*, family: str) -> str:
    return family.replace(FAMILY_FILE_HYPHEN, FAMILY_FILE_UNDERSCORE)


def _covered_and_pending(*, families: Sequence[ModuleType], registry: ModuleType) -> tuple[set[str], set[str]]:
    """The union of the records' IDs and capabilities, and the union of every pending list."""
    graphql = _import_package_module(name=GRAPHQL_ONLY)
    _assert_contract(modules=families, names=FAMILY_CONTRACT)
    _assert_contract(modules=[graphql], names=GRAPHQL_ONLY_CONTRACT)
    rest_type = getattr(registry, REST_OPERATION)
    graphql_type = getattr(registry, GRAPHQL_OPERATION)
    covered = {
        record.operation_id for module in families for record in module.OPERATIONS if isinstance(record, rest_type)
    }
    covered |= {record.capability for record in graphql.OPERATIONS if isinstance(record, graphql_type)}
    pending = {operation_id for module in families for operation_id in module.PENDING}
    pending |= set(graphql.PENDING_CAPABILITIES)
    return covered, pending


# ---------------------------------------------------------------------------------------------------------------------
# Structure checks (AC-1.3)
# ---------------------------------------------------------------------------------------------------------------------


def _record_problems(
    *, name: str, family: str, record: Any, index: Mapping[str, tuple[str, str]], record_type: type
) -> list[str]:
    if not isinstance(record, record_type):
        return [f"{name}: {record!r} in {ATTRIBUTE_OPERATIONS} is not a {REST_OPERATION}"]
    operation_id = record.operation_id
    if _family_of(operation_id=operation_id) != family:
        return [f"{name}: the record {operation_id!r} is not of family {family!r}"]
    row = index.get(operation_id)
    if row is None:
        return [f"{name}: the record {operation_id!r} is not an operation ID of the index"]
    declared = (record.method, record.path)
    if declared != row:
        return [f"{name}: the record {operation_id!r} declares {declared}, its index row is {row}"]
    return []


def _pending_problems(
    *,
    name: str,
    family: str,
    pending: AbstractSet[str],
    index: Mapping[str, tuple[str, str]],
    capabilities: Sequence[str],
) -> list[str]:
    problems = []
    for operation_id in sorted(pending):
        if operation_id in capabilities:
            problems.append(
                f"{name}: {ATTRIBUTE_PENDING} holds the capability {operation_id!r}; capabilities are pending only in "
                f"{GRAPHQL_ONLY}.{ATTRIBUTE_PENDING_CAPABILITIES}"
            )
        elif operation_id not in index or _family_of(operation_id=operation_id) != family:
            problems.append(f"{name}: {ATTRIBUTE_PENDING} holds {operation_id!r}, not an index ID of family {family!r}")
    return problems


def _family_problems(
    *, module: ModuleType, index: Mapping[str, tuple[str, str]], capabilities: Sequence[str], record_type: type
) -> list[str]:
    """Every way one family module breaks D2's contract."""
    name = module.__name__
    family = module.FAMILY
    problems = []
    if _module_name_of(family=family) != _module_stem(module=module):
        problems.append(f"{name}: {ATTRIBUTE_FAMILY} {family!r} does not name its file")
    if not isinstance(module.PENDING, frozenset):
        problems.append(f"{name}: {ATTRIBUTE_PENDING} is a {type(module.PENDING).__name__}, not a frozenset")
    problems.extend(
        _pending_problems(name=name, family=family, pending=module.PENDING, index=index, capabilities=capabilities)
    )
    for record in module.OPERATIONS:
        problems.extend(_record_problems(name=name, family=family, record=record, index=index, record_type=record_type))
    declared = [record.operation_id for record in module.OPERATIONS if isinstance(record, record_type)]
    problems.extend(
        f"{name}: {operation_id!r} is declared {count} times"
        for operation_id, count in sorted(Counter(declared).items())
        if count > 1
    )
    problems.extend(
        f"{name}: {operation_id!r} is both covered and pending"
        for operation_id in sorted(set(declared) & module.PENDING)
    )
    return problems


def _capability_problems(
    *, module: ModuleType, index: Mapping[str, tuple[str, str]], capabilities: Sequence[str], record_type: type[Any]
) -> list[str]:
    """Every way the GraphQL capability module breaks D2: a record or pending entry that is no "Only in GraphQL"
    capability, a record's operation ID declared twice or that is an operation ID of ``index``, or a capability both
    covered and pending."""
    name = module.__name__
    problems = []
    declared: list[str] = []
    covered: set[str] = set()
    for record in module.OPERATIONS:
        if not isinstance(record, record_type):
            problems.append(f"{name}: {record!r} in {ATTRIBUTE_OPERATIONS} is not a {GRAPHQL_OPERATION}")
            continue
        declared.append(record.operation_id)
        covered.add(record.capability)
        if record.capability not in capabilities:
            problems.append(f'{name}: the record {record.capability!r} is not an "Only in GraphQL" capability')
        if record.operation_id in index:
            problems.append(f"{name}: the record {record.operation_id!r} is an operation ID of the index")
    pending = set(module.PENDING_CAPABILITIES)
    problems.extend(
        f'{name}: {ATTRIBUTE_PENDING_CAPABILITIES} holds {capability!r}, not an "Only in GraphQL" capability'
        for capability in sorted(pending)
        if capability not in capabilities
    )
    problems.extend(
        f"{name}: {operation_id!r} is declared {count} times"
        for operation_id, count in sorted(Counter(declared).items())
        if count > 1
    )
    problems.extend(f"{name}: {capability!r} is both covered and pending" for capability in sorted(covered & pending))
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# The standard-library check (UB-2.2)
# ---------------------------------------------------------------------------------------------------------------------


def _top_level_imports(*, path: Path) -> list[tuple[int, str]]:
    """``(line, top-level name)`` of every import statement in the file, nested ones included; a relative import is
    the package's own."""
    tree = ast.parse(source=path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name.partition(MODULE_SEPARATOR)[0]) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            top_level = PACKAGE if node.level else str(node.module).partition(MODULE_SEPARATOR)[0]
            imports.append((node.lineno, top_level))
    return imports


def _loaded_package_files() -> set[Path]:
    """The file of every ``github_api`` module this process has imported."""
    prefix = f"{PACKAGE}{MODULE_SEPARATOR}"
    return {
        Path(str(module.__file__)).resolve()
        for name, module in list(sys.modules.items())
        if (name == PACKAGE or name.startswith(prefix)) and getattr(module, "__file__", None)
    }


# ---------------------------------------------------------------------------------------------------------------------
# A synthetic regeneration (AC-5.3)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SyntheticRecord:
    """The fields of a REST record that ``_family_problems`` reads: its ``operation_id``, ``method`` and ``path``."""

    operation_id: str
    method: str
    path: str


def _regeneration_family() -> ModuleType:
    """A family module of D2's contract with one record, whose row is ``REGENERATION_RECORD_ROW``, and one pending
    ID; it matches ``BEFORE_REGENERATION``."""
    method, path = REGENERATION_RECORD_ROW
    module = ModuleType(name=REGENERATION_MODULE)
    setattr(module, ATTRIBUTE_FAMILY, REGENERATION_FAMILY)
    setattr(
        module,
        ATTRIBUTE_OPERATIONS,
        (SyntheticRecord(operation_id=REGENERATION_RECORD_ID, method=method, path=path),),
    )
    setattr(module, ATTRIBUTE_PENDING, frozenset({REGENERATION_PENDING_ID}))
    return module


def _regenerated(
    *, changes: Mapping[str, tuple[str, str]], removed: AbstractSet[str] = frozenset()
) -> dict[str, tuple[str, str]]:
    """``BEFORE_REGENERATION`` with the rows of ``changes`` added or replaced and the IDs of ``removed`` gone."""
    rows = {**BEFORE_REGENERATION, **changes}
    return {operation_id: row for operation_id, row in rows.items() if operation_id not in removed}


# ---------------------------------------------------------------------------------------------------------------------
# A synthetic capability module (AC-1.4)
# ---------------------------------------------------------------------------------------------------------------------


def _capability_module(*, records: Sequence[Any]) -> ModuleType:
    """A GraphQL capability module of D2's contract whose ``OPERATIONS`` are ``records`` and whose
    ``PENDING_CAPABILITIES`` is empty."""
    module = ModuleType(name=SYNTHETIC_GRAPHQL_MODULE)
    setattr(module, ATTRIBUTE_OPERATIONS, tuple(records))
    setattr(module, ATTRIBUTE_PENDING_CAPABILITIES, frozenset())
    return module


# ---------------------------------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------------------------------


def test_the_reference_is_read_whole() -> None:
    """AC-5.1: ``index_rows`` returns distinct IDs, as many as the index heading counts, ``issues/get`` among them;
    ``graphql_only`` returns the "Only in GraphQL" table's first and last capability and nothing of its header or of
    the **In both** table."""
    text = OPERATIONS_INDEX.read_text(encoding="utf-8")
    heading = INDEX_HEADING.search(string=text)
    assert heading is not None, f"{OPERATIONS_INDEX.name} has no `every operation (N)` heading"
    index = index_rows(path=OPERATIONS_INDEX)
    assert len(index) == int(heading.group(INDEX_COUNT)), (
        f"{OPERATIONS_INDEX.name}: {len(index)} operation rows read, the heading counts {heading.group(INDEX_COUNT)}"
    )
    assert index.get(ISSUES_GET) == ISSUES_GET_ROW, f"{ISSUES_GET} is read as {index.get(ISSUES_GET)}"

    capabilities = graphql_only(path=GRAPHQL_CONVENTIONS)
    assert len(set(capabilities)) == len(capabilities), f"a capability is read twice: {capabilities}"
    missing = [name for name in (REPOSITORY_DISCUSSIONS, WILDCARD_BRANCH_PROTECTION) if name not in capabilities]
    assert not missing, f"graphql_only misses {missing}; it read {capabilities}"
    in_both = _first_cells_of_table_after(path=GRAPHQL_CONVENTIONS, marker=IN_BOTH_MARKER)
    assert in_both, f"{GRAPHQL_CONVENTIONS.name}: the {IN_BOTH_MARKER} table has no rows to tell apart"
    leaked = [name for name in (CAPABILITY_HEADER, *in_both) if name in capabilities]
    assert not leaked, f'graphql_only read {leaked}, which are no "Only in GraphQL" row'


def test_a_gap_is_named() -> None:
    """AC-5.2: an ID and a capability neither covered nor pending are returned by name, the covered and the pending
    item of each kind are not, and the failure message names every gap."""
    covered = frozenset({SYNTHETIC_COVERED_ID, SYNTHETIC_COVERED_CAPABILITY})
    pending = frozenset({SYNTHETIC_PENDING_ID, SYNTHETIC_PENDING_CAPABILITY})

    gaps = coverage_gaps(index=SYNTHETIC_INDEX, capabilities=SYNTHETIC_CAPABILITIES, covered=covered, pending=pending)

    assert gaps == sorted([SYNTHETIC_GAP_ID, SYNTHETIC_GAP_CAPABILITY])
    message = gap_message(gaps=gaps)
    assert [gap for gap in gaps if gap not in message] == [], f"the failure message omits a gap: {message}"
    accounted = pending | {SYNTHETIC_GAP_ID, SYNTHETIC_GAP_CAPABILITY}
    assert (
        coverage_gaps(index=SYNTHETIC_INDEX, capabilities=SYNTHETIC_CAPABILITIES, covered=covered, pending=accounted)
        == []
    )


@pytest.mark.parametrize(
    argnames=("regenerated", "expected_gaps", "expected_problems"),
    argvalues=[
        pytest.param(
            _regenerated(changes={REGENERATION_ADDED_ID: REGENERATION_ADDED_ROW}),
            [REGENERATION_ADDED_ID],
            [],
            id="added_id",
        ),
        pytest.param(
            _regenerated(changes={}, removed=frozenset({REGENERATION_PENDING_ID})),
            [],
            [(repr(REGENERATION_PENDING_ID),)],
            id="pending_id_removed",
        ),
        pytest.param(
            _regenerated(changes={}, removed=frozenset({REGENERATION_RECORD_ID})),
            [],
            [(repr(REGENERATION_RECORD_ID),)],
            id="record_id_removed",
        ),
        pytest.param(
            _regenerated(changes={REGENERATION_RECORD_ID: REGENERATION_OTHER_PATH_ROW}),
            [],
            [(repr(REGENERATION_RECORD_ID), str(REGENERATION_RECORD_ROW), str(REGENERATION_OTHER_PATH_ROW))],
            id="record_path_changed",
        ),
        pytest.param(
            _regenerated(changes={REGENERATION_RECORD_ID: REGENERATION_OTHER_METHOD_ROW}),
            [],
            [(repr(REGENERATION_RECORD_ID), str(REGENERATION_RECORD_ROW), str(REGENERATION_OTHER_METHOD_ROW))],
            id="record_method_changed_same_path",
        ),
    ],
)
def test_a_regenerated_index_names_each_changed_id(
    regenerated: Mapping[str, tuple[str, str]],
    expected_gaps: list[str],
    expected_problems: Sequence[tuple[str, ...]],
) -> None:
    """AC-5.3: a regenerated index that adds an ID no record or pending list holds makes ``coverage_gaps`` return
    it; one that lacks a pending ID or a record ID, or gives a record's ID another path, or another method with the
    same path, makes ``_family_problems`` name that ID (a changed row shown beside the record's). The synthetic family
    module matches the index before the regeneration, so each gap and each problem is the regeneration's."""
    module = _regeneration_family()
    covered = {record.operation_id for record in module.OPERATIONS}
    before = (
        coverage_gaps(index=BEFORE_REGENERATION, capabilities=NO_CAPABILITIES, covered=covered, pending=module.PENDING),
        _family_problems(
            module=module, index=BEFORE_REGENERATION, capabilities=NO_CAPABILITIES, record_type=SyntheticRecord
        ),
    )
    assert before == ([], []), f"the synthetic family module must match the index before the regeneration: {before}"

    gaps = coverage_gaps(index=regenerated, capabilities=NO_CAPABILITIES, covered=covered, pending=module.PENDING)
    problems = _family_problems(
        module=module, index=regenerated, capabilities=NO_CAPABILITIES, record_type=SyntheticRecord
    )

    assert gaps == expected_gaps, f"coverage_gaps returned {gaps} for the regenerated index {regenerated}"
    assert len(problems) == len(expected_problems), (
        f"_family_problems returned {problems} for the regenerated index {regenerated}; expected one problem per "
        f"{expected_problems}"
    )
    unshown = [
        f"{problem!r} does not show {fragment}"
        for problem, fragments in zip(problems, expected_problems)
        for fragment in fragments
        if fragment not in problem
    ]
    assert not unshown, "\n".join(unshown)


@pytest.mark.usefixtures("scripts_on_path")
def test_every_operation_is_covered_or_pending() -> None:
    """AC-5.3: every index operation and "Only in GraphQL" capability is covered by a record or pending; the failure
    message lists every gap."""
    registry = _import_package_module(name=REGISTRY)
    families = _family_modules(registry=registry)
    covered, pending = _covered_and_pending(families=families, registry=registry)

    gaps = coverage_gaps(
        index=index_rows(path=OPERATIONS_INDEX),
        capabilities=graphql_only(path=GRAPHQL_CONVENTIONS),
        covered=covered,
        pending=pending,
    )

    assert not gaps, gap_message(gaps=gaps)


@pytest.mark.usefixtures("scripts_on_path")
def test_discovery_follows_the_directory() -> None:
    """AC-1.2: the family modules ``discover_families()`` returns are the module files of ``github_api/families/``,
    in sorted name order and imported from there, so no list of families exists to edit."""
    registry = _import_package_module(name=REGISTRY)
    present = sorted(path.stem for path in FAMILIES_DIR.glob(PYTHON_GLOB) if path.name != INIT_FILE)
    assert present, (
        f"{PACKAGE}/{FAMILIES}/ holds no family module, so discovery has nothing to follow; D2 gives every index "
        "family a module"
    )

    discovered = [
        (module.__name__, Path(str(module.__file__)).resolve()) for module in _family_modules(registry=registry)
    ]

    expected = [
        (f"{FAMILIES_PACKAGE}{MODULE_SEPARATOR}{stem}", (FAMILIES_DIR / f"{stem}{PYTHON_SUFFIX}").resolve())
        for stem in present
    ]
    assert discovered == expected


@pytest.mark.usefixtures("scripts_on_path")
def test_one_module_per_family_holding_only_its_own_ids() -> None:
    """AC-1.3: one family module per index family, named for it; each ``FAMILY`` names its file; each ``PENDING`` ID
    and record ID is an index ID of that family, a record's method and path its index row; nothing declared twice or
    both covered and pending; capabilities pending only in ``graphql_only.PENDING_CAPABILITIES``."""
    index = index_rows(path=OPERATIONS_INDEX)
    capabilities = graphql_only(path=GRAPHQL_CONVENTIONS)
    registry = _import_package_module(name=REGISTRY)
    families = _family_modules(registry=registry)

    expected = {_module_name_of(family=_family_of(operation_id=operation_id)) for operation_id in index}
    present = {_module_stem(module=module) for module in families}
    missing, extra = sorted(expected - present), sorted(present - expected)
    assert not missing and not extra, (
        f"{PACKAGE}/{FAMILIES}/ must hold one module per index family: no module for {missing}; no index family "
        f"for {extra}"
    )
    _assert_contract(modules=families, names=FAMILY_CONTRACT)
    rest_type = getattr(registry, REST_OPERATION)
    problems = [
        problem
        for module in families
        for problem in _family_problems(module=module, index=index, capabilities=capabilities, record_type=rest_type)
    ]
    graphql = _import_package_module(name=GRAPHQL_ONLY)
    _assert_contract(modules=[graphql], names=GRAPHQL_ONLY_CONTRACT)
    problems.extend(
        _capability_problems(
            module=graphql, index=index, capabilities=capabilities, record_type=getattr(registry, GRAPHQL_OPERATION)
        )
    )

    assert not problems, "the family and capability modules break D2's contract:\n" + "\n".join(problems)


@pytest.mark.usefixtures("scripts_on_path")
@pytest.mark.parametrize(
    argnames=("declared", "expected_named_ids"),
    argvalues=[
        pytest.param(
            (
                (SYNTHETIC_FIRST_GRAPHQL_ID, SYNTHETIC_FIRST_CAPABILITY),
                (SYNTHETIC_SECOND_GRAPHQL_ID, SYNTHETIC_FIRST_CAPABILITY),
            ),
            (),
            id="shared_capability",
        ),
        pytest.param(
            (
                (SYNTHETIC_FIRST_GRAPHQL_ID, SYNTHETIC_FIRST_CAPABILITY),
                (SYNTHETIC_FIRST_GRAPHQL_ID, SYNTHETIC_SECOND_CAPABILITY),
            ),
            (SYNTHETIC_FIRST_GRAPHQL_ID,),
            id="shared_id",
        ),
        pytest.param(
            ((ISSUES_GET, SYNTHETIC_FIRST_CAPABILITY),),
            (ISSUES_GET,),
            id="index_id",
        ),
    ],
)
def test_a_graphql_record_id_is_its_own(declared: Sequence[tuple[str, str]], expected_named_ids: Sequence[str]) -> None:
    """AC-1.4: on a synthetic capability module of the registry's ``GraphQLOperation`` records, each built from one
    ``(operation_id, capability)`` pair of ``declared``, two records that share a capability give no problem; two that
    share an operation ID give one problem naming the ID, and so does a record whose ID is an operation ID of the
    index. Every capability is one the table lists and nothing is pending, so each problem is the ID's."""
    registry = _import_package_module(name=REGISTRY)
    record_type = getattr(registry, GRAPHQL_OPERATION)
    records = [
        record_type(
            operation_id=operation_id, capability=capability, document=SYNTHETIC_DOCUMENT, connection=NO_CONNECTION
        )
        for operation_id, capability in declared
    ]

    problems = _capability_problems(
        module=_capability_module(records=records),
        index=SYNTHETIC_GRAPHQL_INDEX,
        capabilities=SYNTHETIC_GRAPHQL_CAPABILITIES,
        record_type=record_type,
    )

    assert len(problems) == len(expected_named_ids), (
        f"_capability_problems returned {problems} for the records {declared}; expected one problem naming each of "
        f"{list(expected_named_ids)}"
    )
    unnamed = [
        f"{problem!r} does not name {operation_id!r}"
        for problem, operation_id in zip(problems, expected_named_ids)
        if repr(operation_id) not in problem
    ]
    assert not unnamed, "\n".join(unnamed)


@pytest.mark.usefixtures("scripts_on_path")
def test_the_wrapper_imports_only_the_standard_library() -> None:
    """UB-2.2: every top-level import name of the entry script and of every module under ``github_api/`` is
    ``github_api`` or in ``sys.stdlib_module_names`` (X1: CI's Python 3.10 has it).

    The scan must cover the package the wrapper runs: every ``github_api`` module imported here — the registry, the
    families it discovers, the GraphQL capability module — is one of the scanned files, so an absent, partial or
    foreign copy of the package cannot pass.
    """
    stdlib_names = getattr(sys, "stdlib_module_names", None)
    assert stdlib_names is not None, (
        f"UB-2.2's oracle is sys.stdlib_module_names (Python 3.10+, cross-wrapper decision X1); this interpreter is "
        f"Python {sys.version.split()[0]}"
    )
    scanned = [ENTRY_SCRIPT, *sorted(PACKAGE_DIR.rglob(PYTHON_GLOB))]
    registry = _import_package_module(name=REGISTRY)
    _family_modules(registry=registry)
    _import_package_module(name=GRAPHQL_ONLY)
    unscanned = sorted(str(path) for path in _loaded_package_files() - {path.resolve() for path in scanned})
    assert not unscanned, f"imported {PACKAGE} modules outside the scanned tree {PACKAGE_DIR}: {unscanned}"

    foreign = [
        f"{path.relative_to(SCRIPTS_DIR).as_posix()}:{line}: {name}"
        for path in scanned
        for line, name in _top_level_imports(path=path)
        if name != PACKAGE and name not in stdlib_names
    ]

    assert not foreign, "imports outside the standard library and the package:\n" + "\n".join(foreign)
