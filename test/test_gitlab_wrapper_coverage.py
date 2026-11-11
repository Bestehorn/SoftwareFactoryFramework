"""The coverage test of the GitLab wrapper: every row of the GitLab operations index is mapped or pending.

`docs/api-reference/gitlab/operations-index.md` lists every REST endpoint as a `| Method | Path | Reference |` row.
A row is MAPPED when a `RestOperation` record of an endpoint family declares its `(method, path)` key, and PENDING
when the `PENDING` set of the key's family module names the key. A row's family module is the file stem of its
Reference link with `-` replaced by `_` (`rest/ai-coding.md#...` is `ai_coding`); a key whose rows link to several
families belongs to the family whose module name sorts first. The family modules are found by
`gitlab_api.registry.discover_families` scanning the families package, never by a list (issue #13 design, D2 and D8).

The helpers are pure: `index_rows` parses the index table, `coverage_gaps` returns every row neither mapped nor
pending, and `gap_report` groups the gaps by family module as `PENDING` tuple literals. Discovery and the checker are
tested on a synthetic families package written into `tmp_path` and a synthetic index. The index exists only in this
repository, which is why the module lives in `test/`. It puts `src/payload/scripts` on `sys.path` and imports
`gitlab_api` inside each test, so it collects while the package is absent. No test of the module may open a network
connection: a `socket.socket.connect` guard is installed for every one.

Issue #41 (design D6) adds the checks of a regenerated reference and of the GraphQL-only capabilities:
`family_problems` names each `PENDING` key and each record that the index no longer bears out, `only_in_graphql`
reads the first cells of the table under `### Only in GraphQL` in `graphql/conventions.md`, and `capability_problems`
names each capability neither served by a `graphql_only` record nor in `graphql_only.PENDING_CAPABILITIES`, and each
entry or record capability the table lacks.

Run: ``python scripts/run_tests.py test/test_gitlab_wrapper_coverage.py``
"""

from __future__ import annotations

import importlib
import re
import socket
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import AbstractSet, Any, FrozenSet, Iterable, Iterator, Mapping, NamedTuple, Sequence, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "src" / "payload" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

PACKAGE = "gitlab_api"
REGISTRY = PACKAGE + ".registry"
INDEX = ROOT / "docs" / "api-reference" / "gitlab" / "operations-index.md"
GRAPHQL_ONLY = PACKAGE + ".graphql_only"
CONVENTIONS = ROOT / "docs" / "api-reference" / "gitlab" / "graphql" / "conventions.md"

# The two tables of `graphql/conventions.md` "Only in GraphQL / only in REST", each read under its heading (D6).
ONLY_IN_GRAPHQL_HEADING = "### Only in GraphQL"
ONLY_IN_REST_HEADING = "### Only in REST"
HEADING_PREFIX = "#"
CELL_SEPARATOR = "|"
SEPARATOR_ROW = re.compile(r"\|(?:\s*:?-+:?\s*\|)+")
SEPARATOR_CHARACTERS = "-:"
CAPABILITY_HEADER = "Capability"
FIRST_CAPABILITY = "Work items"
LAST_CAPABILITY = "Query cost introspection"
# The names of the GraphQL capability module (D6).
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING_CAPABILITIES = "PENDING_CAPABILITIES"
# A package-manager protocol path (AC-6.1).
ROUTE_PREFIX = "/<route-prefix>/"

METHODS = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")
TABLE_HEADER = "| Method | Path | Reference |"
TABLE_SEPARATOR = "|---|---|---|"
TABLE_ROW = re.compile(
    r"\| (?P<method>" + "|".join(METHODS) + r") \| `(?P<path>[^`]+)` \| "
    r"\[.*\]\((?P<reference>rest/[a-z0-9-]+\.md#[^)]+)\) \|"
)
GROUP_METHOD = "method"
GROUP_PATH = "path"
GROUP_REFERENCE = "reference"

Key = Tuple[str, str]


class IndexRow(NamedTuple):
    """One method-and-path row of the operations index."""

    method: str
    path: str
    reference: str

    @property
    def key(self) -> Key:
        return (self.method, self.path)


def family_stem(reference: str) -> str:
    """The file stem of a Reference link: `rest/ai-coding.md#create-a-merge-request` is `ai-coding`."""
    return PurePosixPath(reference.partition("#")[0]).stem


def family_module(reference: str) -> str:
    """The family module a Reference link names: its file stem with `-` replaced by `_`."""
    return family_stem(reference=reference).replace("-", "_")


def operation_id(reference: str) -> str:
    """A record's id: the Reference target without `rest/` and `.md` (`plan#update-an-issue`)."""
    return f"{family_stem(reference=reference)}#{reference.partition('#')[2]}"


def index_rows(path: Path) -> list[IndexRow]:
    """Every method-and-path row of an operations index's table, in file order.

    A table line that is neither the header, the separator nor such a row fails the test, naming the line."""
    rows: list[IndexRow] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        if not line.startswith("|") or line in (TABLE_HEADER, TABLE_SEPARATOR):
            continue
        match = TABLE_ROW.fullmatch(line)
        assert match is not None, f"{path.name}:{number}: a table line that is no method-and-path row: {line}"
        rows.append(
            IndexRow(
                method=match.group(GROUP_METHOD), path=match.group(GROUP_PATH), reference=match.group(GROUP_REFERENCE)
            )
        )
    assert rows, f"{path} holds no method-and-path row"
    return rows


def key_families(rows: Iterable[IndexRow]) -> dict[Key, str]:
    """Each key's family module: the one whose name sorts first among the families of the rows carrying the key."""
    families: dict[Key, str] = {}
    for row in rows:
        module = family_module(reference=row.reference)
        families[row.key] = min(families.get(row.key, module), module)
    return families


def coverage_gaps(
    rows: Sequence[IndexRow], mapped: AbstractSet[Key], pending: Mapping[str, AbstractSet[Key]]
) -> list[IndexRow]:
    """Every row, sorted, whose key is neither a record's `(method, path)` nor in the `PENDING` of the key's family."""
    families = key_families(rows=rows)
    return sorted(
        row for row in rows if row.key not in mapped and row.key not in pending.get(families[row.key], frozenset())
    )


def gaps_by_family(gaps: Sequence[IndexRow]) -> dict[str, dict[Key, list[str]]]:
    """The gaps grouped by the family module that must list them: module -> key -> the references of its rows."""
    families = key_families(rows=gaps)
    grouped: dict[str, dict[Key, list[str]]] = {}
    for row in sorted(gaps):
        grouped.setdefault(families[row.key], {}).setdefault(row.key, []).append(row.reference)
    return {module: grouped[module] for module in sorted(grouped)}


def gap_report(gaps: Sequence[IndexRow]) -> str:
    """The failure message: per family module, each unlisted key as a `PENDING` tuple literal with its rows."""
    lines = [
        f"{len(gaps)} row(s) of operations-index.md are neither mapped nor pending; "
        "add each key to the PENDING of its family module:"
    ]
    for module, keys in gaps_by_family(gaps=gaps).items():
        lines.append(f"families/{module}.py:")
        lines.extend(f"    {key!r},  # {', '.join(references)}" for key, references in keys.items())
    return "\n".join(lines)


def declared_keys(families: Iterable[ModuleType]) -> tuple[set[Key], dict[str, frozenset[Key]]]:
    """What the discovered family modules declare: every record's `(method, path)`, and each module's `PENDING` by
    module name. A module's `FAMILY` is its module name with `_` written as `-`."""
    mapped: set[Key] = set()
    pending: dict[str, frozenset[Key]] = {}
    for module in families:
        name = module.__name__.rpartition(".")[2]
        assert module.FAMILY.replace("-", "_") == name, f"{module.__name__}: FAMILY {module.FAMILY!r} is not its stem"
        mapped.update((record.method, record.path) for record in module.OPERATIONS)
        pending[name] = frozenset(module.PENDING)
    return mapped, pending


def registry_module() -> ModuleType:
    """`gitlab_api.registry`, imported inside a test; while it is absent the test fails on this assertion."""
    try:
        return importlib.import_module(name=REGISTRY)
    except ModuleNotFoundError as missing:
        if missing.name not in (PACKAGE, REGISTRY):
            raise
        raise AssertionError(f"{REGISTRY} is not importable from {SCRIPTS}: {missing}") from missing


def graphql_only_module() -> ModuleType:
    """`gitlab_api.graphql_only`, imported inside a test as `registry_module` imports the registry; while it is absent
    the test fails on this assertion."""
    try:
        return importlib.import_module(name=GRAPHQL_ONLY)
    except ModuleNotFoundError as missing:
        if missing.name not in (PACKAGE, GRAPHQL_ONLY):
            raise
        raise AssertionError(f"{GRAPHQL_ONLY} is not importable from {SCRIPTS}: {missing}") from missing


# --- Issue #41, D6: what a regenerated reference no longer bears out ---------------------------------------------


def reference_keys(rows: Iterable[IndexRow]) -> dict[str, set[Key]]:
    """Each Reference's operation ID, mapped to the keys of the rows carrying it; a Reference can carry several."""
    keys: dict[str, set[Key]] = {}
    for row in rows:
        keys.setdefault(operation_id(reference=row.reference), set()).add(row.key)
    return keys


def pending_key_problems(*, name: str, pending: AbstractSet[Key], owners: Mapping[Key, str]) -> list[str]:
    """Each `PENDING` key of the family module `name` that no row carries, or whose family is another module."""
    problems: list[str] = []
    for key in sorted(pending):
        owner = owners.get(key)
        if owner is None:
            problems.append(f"families/{name}.py: PENDING holds {key!r}, which no row of the index carries")
        elif owner != name:
            problems.append(f"families/{name}.py: PENDING holds {key!r}, a key of families/{owner}.py")
    return problems


def record_key_problems(*, name: str, records: Iterable[Any], references: Mapping[str, AbstractSet[Key]]) -> list[str]:
    """Each record of the family module `name` whose operation ID is the Reference of no row, or whose
    `(method, path)` is on none of the rows carrying its Reference."""
    problems: list[str] = []
    for record in records:
        declared = (record.method, record.path)
        keys = references.get(record.operation_id)
        if keys is None:
            problems.append(
                f"families/{name}.py: the record {record.operation_id!r} is the Reference of no row of the index"
            )
        elif declared not in keys:
            problems.append(
                f"families/{name}.py: the record {record.operation_id!r} declares {declared!r}; "
                f"the rows of its Reference carry {sorted(keys)!r}"
            )
    return problems


def family_problems(*, rows: Sequence[IndexRow], families: Iterable[ModuleType]) -> list[str]:
    """Per family module, every declaration the index does not bear out (design D6): a `PENDING` key that no row
    carries or whose family (`key_families`) is another module, a record whose operation ID is the Reference of no
    row, and a record whose `(method, path)` is on none of the rows carrying its Reference. Each problem names the
    module and the key or the ID."""
    owners = key_families(rows=rows)
    references = reference_keys(rows=rows)
    problems: list[str] = []
    for module in families:
        name = module.__name__.rpartition(".")[2]
        problems.extend(pending_key_problems(name=name, pending=module.PENDING, owners=owners))
        problems.extend(record_key_problems(name=name, records=module.OPERATIONS, references=references))
    return problems


def first_cell(line: str) -> str:
    """The stripped first cell of one Markdown table row."""
    return line.strip().strip(CELL_SEPARATOR).split(CELL_SEPARATOR)[0].strip()


def table_first_cells(*, path: Path, heading: str) -> list[str]:
    """The first cell of every data row of the table under the one line `heading` of a Markdown file, up to the
    table's end. The header row and the separator row are no data rows; a heading met before any table ends the
    search, so the table of a later section is never read."""
    lines = [raw.rstrip() for raw in path.read_text(encoding="utf-8").splitlines()]
    starts = [number for number, line in enumerate(lines) if line == heading]
    assert len(starts) == 1, f"{path.name}: {len(starts)} lines are {heading!r}, expected one"
    table: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if line.startswith(CELL_SEPARATOR):
            table.append(line)
        elif table or line.startswith(HEADING_PREFIX):
            break
    assert len(table) >= 2 and SEPARATOR_ROW.fullmatch(table[1]), (
        f"{path.name}: the table under {heading!r} has no header and separator row: {table}"
    )
    return [first_cell(line=line) for line in table[2:]]


def only_in_graphql(*, path: Path) -> list[str]:
    """The first cells of the table under the `### Only in GraphQL` heading, up to the table's end (design D6)."""
    return table_first_cells(path=path, heading=ONLY_IN_GRAPHQL_HEADING)


def capability_problems(*, capabilities: Sequence[str], module: ModuleType) -> list[str]:
    """What a GraphQL capability module leaves unaccounted (design D6): each capability neither served by a record's
    `capability` nor in `PENDING_CAPABILITIES`, then each `PENDING_CAPABILITIES` entry and each record `capability`
    that `capabilities` (the table's first cells) lacks. Each problem names the capability."""
    name = module.__name__
    records = tuple(module.OPERATIONS)
    pending = frozenset(module.PENDING_CAPABILITIES)
    accounted = {record.capability for record in records} | pending
    listed = frozenset(capabilities)
    problems = [
        f"{name}: the capability {capability!r} is neither served by a record nor in {ATTRIBUTE_PENDING_CAPABILITIES}"
        for capability in capabilities
        if capability not in accounted
    ]
    problems.extend(
        f"{name}: {ATTRIBUTE_PENDING_CAPABILITIES} holds {entry!r}, which the Only in GraphQL table lacks"
        for entry in sorted(pending - listed)
    )
    problems.extend(
        f"{name}: the record {record.operation_id!r} serves {record.capability!r}, which the Only in GraphQL table "
        "lacks"
        for record in records
        if record.capability not in listed
    )
    return problems


# --- Synthetic families packages and indexes --------------------------------------------------------------------


@dataclass(frozen=True)
class SyntheticFamily:
    """A family module to write into a synthetic families package: its stem, the rows its records map, and the keys
    its `PENDING` lists."""

    family: str
    records: Tuple[IndexRow, ...] = ()
    pending: FrozenSet[Key] = frozenset()

    @property
    def module_name(self) -> str:
        return self.family.replace("-", "_")

    def source(self) -> str:
        """The module text, written as a family module of the real package is: `FAMILY`, `OPERATIONS`, `PENDING`."""
        lines = [
            f'"""Synthetic endpoint family {self.family}, found by discovery."""',
            "",
            f"from {REGISTRY} import RestOperation",
            "",
            f"FAMILY = {self.family!r}",
            "OPERATIONS = (",
            *(
                f"    RestOperation(operation_id={operation_id(reference=row.reference)!r},"
                f" method={row.method!r}, path={row.path!r}),"
                for row in self.records
            ),
            ")",
            f"PENDING = frozenset({sorted(self.pending)!r})",
            "",
        ]
        return "\n".join(lines)


def write_package(*, root: Path, name: str, families: Iterable[SyntheticFamily]) -> ModuleType:
    """Write a families package under `root` — an empty `__init__.py`, one module per family — and import it."""
    directory = root / name
    directory.mkdir()
    (directory / "__init__.py").write_text(data="", encoding="utf-8")
    for family in families:
        (directory / f"{family.module_name}.py").write_text(data=family.source(), encoding="utf-8")
    importlib.invalidate_caches()
    return importlib.import_module(name=name)


def present_modules(directory: Path, package: str) -> list[str]:
    """The dotted names of the module files present in a package directory, sorted by module name."""
    return [f"{package}.{path.stem}" for path in sorted(directory.glob("*.py")) if path.stem != "__init__"]


def index_line(row: IndexRow) -> str:
    return f"| {row.method} | `{row.path}` | [Synthetic API: `{row.path}`]({row.reference}) |"


def index_text(rows: Iterable[IndexRow]) -> str:
    """A synthetic index shaped like the generated one: a preamble with a link, then the table."""
    return "\n".join(
        [
            "<!-- A synthetic operations index, written by a test. -->",
            "",
            "# GitLab REST API — every endpoint",
            "",
            "Sorted by path. Back to the [README](README.md).",
            "",
            TABLE_HEADER,
            TABLE_SEPARATOR,
            *(index_line(row=row) for row in rows),
            "",
        ]
    )


ALPHA_BETA = "alpha-beta"
GAMMA = "gamma"
DELTA = "delta"  # a stem the synthetic index links and no module declares

LIST_WIDGETS = IndexRow(method="GET", path="/widgets", reference="rest/alpha-beta.md#list-widgets")
CREATE_WIDGET = IndexRow(method="POST", path="/widgets", reference="rest/alpha-beta.md#create-a-widget")
DELETE_WIDGET = IndexRow(method="DELETE", path="/widgets/:id", reference="rest/alpha-beta.md#delete-a-widget")
LIST_GADGETS = IndexRow(method="GET", path="/gadgets", reference="rest/gamma.md#list-gadgets")
UPDATE_GADGET = IndexRow(method="PUT", path="/gadgets/:id", reference="rest/gamma.md#update-a-gadget")
RELEASE_FILE = IndexRow(
    method="GET",
    path="/<route-prefix>/dists/*distribution/Release",
    reference="rest/gamma.md#download-a-distribution-release-file",
)
TOKEN_INFO = IndexRow(
    method="GET", path="https://HOST/oauth/token/info", reference="rest/gamma.md#retrieve-the-token-information"
)
SHARED_IN_ALPHA_BETA = IndexRow(method="GET", path="/shared", reference="rest/alpha-beta.md#list-shared")
SHARED_IN_GAMMA = IndexRow(method="GET", path="/shared", reference="rest/gamma.md#list-shared")
CONTESTED_IN_ALPHA_BETA = IndexRow(method="GET", path="/contested", reference="rest/alpha-beta.md#list-contested")
CONTESTED_IN_GAMMA = IndexRow(method="GET", path="/contested", reference="rest/gamma.md#list-contested")
LIST_DELTAS = IndexRow(method="GET", path="/deltas", reference="rest/delta.md#list-deltas")

SYNTHETIC_ROWS = (
    RELEASE_FILE,
    CONTESTED_IN_ALPHA_BETA,
    CONTESTED_IN_GAMMA,
    LIST_DELTAS,
    LIST_GADGETS,
    UPDATE_GADGET,
    SHARED_IN_GAMMA,
    SHARED_IN_ALPHA_BETA,
    LIST_WIDGETS,
    CREATE_WIDGET,
    DELETE_WIDGET,
    TOKEN_INFO,
)
CHECKER_FAMILIES = (
    # `/gadgets/:id` is gamma's key, so alpha-beta's listing does not cover it; `/shared` is alpha-beta's key (the
    # module name that sorts first), so alpha-beta's listing covers both of its rows.
    SyntheticFamily(
        family=ALPHA_BETA,
        records=(LIST_WIDGETS,),
        pending=frozenset({CREATE_WIDGET.key, UPDATE_GADGET.key, SHARED_IN_ALPHA_BETA.key}),
    ),
    # `/contested` is alpha-beta's key, so gamma's listing covers neither of its rows.
    SyntheticFamily(family=GAMMA, pending=frozenset({LIST_GADGETS.key, RELEASE_FILE.key, CONTESTED_IN_GAMMA.key})),
)
# The rows neither mapped nor listed by their key's family.
UNLISTED_ROWS = (DELETE_WIDGET, UPDATE_GADGET, TOKEN_INFO, CONTESTED_IN_ALPHA_BETA, CONTESTED_IN_GAMMA, LIST_DELTAS)

# AC-5.3's regeneration: alpha-beta maps `LIST_WIDGETS` and lists `CREATE_WIDGET`, which matches the index before it;
# a regenerated index adds a row, drops one, or gives the record's Reference another path or another method.
REGENERATION_FAMILY = SyntheticFamily(
    family=ALPHA_BETA, records=(LIST_WIDGETS,), pending=frozenset({CREATE_WIDGET.key})
)
REGENERATION_MODULE = f"families/{REGENERATION_FAMILY.module_name}.py"
REGENERATION_RECORD_ID = operation_id(reference=LIST_WIDGETS.reference)
BEFORE_REGENERATION = (LIST_WIDGETS, CREATE_WIDGET)
LIST_WIDGETS_OTHER_PATH = IndexRow(method=LIST_WIDGETS.method, path="/widgets/all", reference=LIST_WIDGETS.reference)
LIST_WIDGETS_OTHER_METHOD = IndexRow(method="HEAD", path=LIST_WIDGETS.path, reference=LIST_WIDGETS.reference)

# AC-6.2's synthetic capability module: a table of three capabilities, one served, one pending, one neither, and a
# pending entry and a record capability that the table lacks.
SERVED_CAPABILITY = "Served capability"
PENDING_CAPABILITY = "Pending capability"
UNLISTED_CAPABILITY = "Unlisted capability"
RETIRED_PENDING_CAPABILITY = "Retired pending capability"
RETIRED_SERVED_CAPABILITY = "Retired served capability"
SYNTHETIC_CAPABILITIES = (SERVED_CAPABILITY, PENDING_CAPABILITY, UNLISTED_CAPABILITY)
EVERY_CAPABILITY = (*SYNTHETIC_CAPABILITIES, RETIRED_PENDING_CAPABILITY, RETIRED_SERVED_CAPABILITY)
SYNTHETIC_GRAPHQL_ONLY = "synthetic_graphql_only"
SYNTHETIC_DOCUMENT = "query Q { currentUser { id } }"


def capability_module(*, registry: ModuleType, served: Iterable[str], pending: Iterable[str]) -> ModuleType:
    """A synthetic GraphQL capability module: one `GraphQLOperation` (`graphql#<field>`) per served capability, and
    `PENDING_CAPABILITIES`."""
    module = ModuleType(name=SYNTHETIC_GRAPHQL_ONLY)
    records = tuple(
        registry.GraphQLOperation(
            operation_id=f"graphql#syntheticField{number}", capability=capability, document=SYNTHETIC_DOCUMENT
        )
        for number, capability in enumerate(served)
    )
    setattr(module, ATTRIBUTE_OPERATIONS, records)
    setattr(module, ATTRIBUTE_PENDING_CAPABILITIES, frozenset(pending))
    return module


@pytest.fixture(autouse=True)
def refuse_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test of this module runs without network access: a connection attempt fails the test."""

    def refuse(self: socket.socket, address: object) -> None:
        raise AssertionError(f"a coverage test tried to open a network connection to {address!r}")

    monkeypatch.setattr(target=socket.socket, name="connect", value=refuse)


@pytest.fixture
def package_prefix() -> Iterator[str]:
    """A package-name prefix unique to the test, so a per-package discovery cache never holds another test's package;
    the synthetic modules leave `sys.modules` afterwards."""
    prefix = f"synthetic_gitlab_families_{uuid.uuid4().hex}"
    yield prefix
    for loaded in [name for name in sys.modules if name.startswith(prefix)]:
        sys.modules.pop(loaded)


# --- AC-1.2, AC-5.2: a family is one module, found by being there -----------------------------------------------


def test_a_family_module_is_discovered_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, package_prefix: str
) -> None:
    """A module added to a families package is discovered with no other file changed: the package's `__init__.py`
    is empty and nothing lists the families. Its `PENDING` is read from the module itself. One discovery per
    package, after its files are written."""
    registry = registry_module()
    monkeypatch.syspath_prepend(path=str(tmp_path))
    alpha_beta = SyntheticFamily(family=ALPHA_BETA, records=(LIST_WIDGETS,), pending=frozenset({CREATE_WIDGET.key}))
    gamma = SyntheticFamily(family=GAMMA, pending=frozenset({LIST_GADGETS.key}))

    before = write_package(root=tmp_path, name=f"{package_prefix}_before", families=(alpha_beta,))
    discovered = list(registry.discover_families(package=before))
    names = [module.__name__ for module in discovered]
    assert names == present_modules(directory=tmp_path / before.__name__, package=before.__name__)
    assert names == [f"{before.__name__}.alpha_beta"]
    assert declared_keys(families=discovered) == ({LIST_WIDGETS.key}, {"alpha_beta": frozenset({CREATE_WIDGET.key})})

    after = write_package(root=tmp_path, name=f"{package_prefix}_after", families=(alpha_beta, gamma))
    discovered = list(registry.discover_families(package=after))
    names = [module.__name__ for module in discovered]
    assert names == present_modules(directory=tmp_path / after.__name__, package=after.__name__)
    assert names == [f"{after.__name__}.alpha_beta", f"{after.__name__}.gamma"], "the added module is discovered"
    assert declared_keys(families=discovered) == (
        {LIST_WIDGETS.key},
        {"alpha_beta": frozenset({CREATE_WIDGET.key}), "gamma": frozenset({LIST_GADGETS.key})},
    )


# --- AC-5.1: the checker names every row neither mapped nor pending -----------------------------------------------


def test_checker_names_each_unlisted_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, package_prefix: str) -> None:
    """On a synthetic index against a synthetic families package, the checker names exactly the rows no record maps
    and the key's family does not list: a row of a stem with no module, a key listed only by another family, and a
    key shared by two families that only the later-sorting one lists. A table line that is no row fails the parse."""
    registry = registry_module()
    monkeypatch.syspath_prepend(path=str(tmp_path))
    index = tmp_path / "operations-index.md"
    index.write_text(data=index_text(rows=SYNTHETIC_ROWS), encoding="utf-8")
    rows = index_rows(path=index)
    assert rows == list(SYNTHETIC_ROWS)

    package = write_package(root=tmp_path, name=f"{package_prefix}_checker", families=CHECKER_FAMILIES)
    mapped, pending = declared_keys(families=registry.discover_families(package=package))
    gaps = coverage_gaps(rows=rows, mapped=mapped, pending=pending)
    assert gaps == sorted(UNLISTED_ROWS)

    grouped = gaps_by_family(gaps=gaps)
    assert list(grouped) == ["alpha_beta", "delta", "gamma"]
    assert grouped == {
        "alpha_beta": {
            DELETE_WIDGET.key: [DELETE_WIDGET.reference],
            CONTESTED_IN_ALPHA_BETA.key: [CONTESTED_IN_ALPHA_BETA.reference, CONTESTED_IN_GAMMA.reference],
        },
        "delta": {LIST_DELTAS.key: [LIST_DELTAS.reference]},
        "gamma": {UPDATE_GADGET.key: [UPDATE_GADGET.reference], TOKEN_INFO.key: [TOKEN_INFO.reference]},
    }
    report = gap_report(gaps=gaps)
    for module in grouped:
        assert f"families/{module}.py:" in report, report
    for row in UNLISTED_ROWS:
        assert repr(row.key) in report and row.reference in report, report

    malformed = f"| {LIST_WIDGETS.method} | {LIST_WIDGETS.path} | [List widgets]({LIST_WIDGETS.reference}) |"
    broken = tmp_path / "broken-index.md"
    broken.write_text(
        data=f"{TABLE_HEADER}\n{TABLE_SEPARATOR}\n{index_line(row=CREATE_WIDGET)}\n{malformed}\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError, match=re.escape(malformed)):
        index_rows(path=broken)


# --- AC-5.3, AC-5.4: every row of the real index is mapped or pending, offline ------------------------------------


def test_every_index_row_is_mapped_or_pending() -> None:
    """Every row of the real `operations-index.md` is mapped by a record of a family module or listed in the `PENDING`
    of its key's family module (a key two families link is the family's whose module name sorts first). The modules
    are what `discover_families()` finds in the real `gitlab_api.families` package. The failure message is the gap
    report: every unlisted key as a `PENDING` tuple literal under the family module that must list it. The module's
    socket guard is installed, so the check runs with no network access."""
    registry = registry_module()
    rows = index_rows(path=INDEX)
    mapped, pending = declared_keys(families=registry.discover_families())
    gaps = coverage_gaps(rows=rows, mapped=mapped, pending=pending)
    assert not gaps, gap_report(gaps=gaps)


# --- Issue #41 AC-5.3: a regenerated index names each changed key or ID ------------------------------------------


@pytest.mark.parametrize(
    argnames=("regenerated", "expected_gaps", "expected_problems"),
    argvalues=[
        pytest.param((*BEFORE_REGENERATION, DELETE_WIDGET), [DELETE_WIDGET], [], id="key_added"),
        pytest.param(
            (LIST_WIDGETS,),
            [],
            [(REGENERATION_MODULE, repr(CREATE_WIDGET.key))],
            id="pending_key_removed",
        ),
        pytest.param(
            (CREATE_WIDGET,),
            [],
            [(REGENERATION_MODULE, repr(REGENERATION_RECORD_ID))],
            id="record_row_removed",
        ),
        pytest.param(
            (LIST_WIDGETS_OTHER_PATH, CREATE_WIDGET),
            [LIST_WIDGETS_OTHER_PATH],
            [
                (
                    REGENERATION_MODULE,
                    repr(REGENERATION_RECORD_ID),
                    repr(LIST_WIDGETS.key),
                    repr(LIST_WIDGETS_OTHER_PATH.key),
                )
            ],
            id="record_path_changed",
        ),
        pytest.param(
            (LIST_WIDGETS_OTHER_METHOD, CREATE_WIDGET),
            [LIST_WIDGETS_OTHER_METHOD],
            [
                (
                    REGENERATION_MODULE,
                    repr(REGENERATION_RECORD_ID),
                    repr(LIST_WIDGETS.key),
                    repr(LIST_WIDGETS_OTHER_METHOD.key),
                )
            ],
            id="record_method_changed_same_path",
        ),
    ],
)
def test_a_regenerated_index_names_each_changed_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    package_prefix: str,
    regenerated: Tuple[IndexRow, ...],
    expected_gaps: list[IndexRow],
    expected_problems: Sequence[Tuple[str, ...]],
) -> None:
    """AC-5.3: on a synthetic families package that matches the index before the regeneration, a regenerated index
    that adds a key no record maps and no `PENDING` lists makes `coverage_gaps` return its row; one that lacks a
    pending key, lacks the row of a record's Reference, or gives that row another path, or another method with the
    same path, makes `family_problems` name the module and the key or the ID (a changed row's key shown beside the
    record's). A changed method or path is also a removal plus an addition, so its new row is a gap as well."""
    registry = registry_module()
    monkeypatch.syspath_prepend(path=str(tmp_path))
    package = write_package(root=tmp_path, name=f"{package_prefix}_regeneration", families=(REGENERATION_FAMILY,))
    families = registry.discover_families(package=package)
    mapped, pending = declared_keys(families=families)

    before_index = tmp_path / "before-operations-index.md"
    before_index.write_text(data=index_text(rows=BEFORE_REGENERATION), encoding="utf-8")
    before_rows = index_rows(path=before_index)
    before = (
        coverage_gaps(rows=before_rows, mapped=mapped, pending=pending),
        family_problems(rows=before_rows, families=families),
    )
    assert before == ([], []), f"the synthetic package must match the index before the regeneration: {before}"

    regenerated_index = tmp_path / "operations-index.md"
    regenerated_index.write_text(data=index_text(rows=regenerated), encoding="utf-8")
    rows = index_rows(path=regenerated_index)
    gaps = coverage_gaps(rows=rows, mapped=mapped, pending=pending)
    problems = family_problems(rows=rows, families=families)

    assert gaps == sorted(expected_gaps), f"coverage_gaps returned {gaps} for the regenerated index {rows}"
    assert len(problems) == len(expected_problems), (
        f"family_problems returned {problems} for the regenerated index {rows}; expected one problem per "
        f"{expected_problems}"
    )
    unshown = [
        f"{problem!r} does not show {fragment}"
        for problem, fragments in zip(problems, expected_problems)
        for fragment in fragments
        if fragment not in problem
    ]
    assert not unshown, "\n".join(unshown)


def test_every_declared_key_is_in_its_family() -> None:
    """AC-5.3, AC-6.3: every `PENDING` key of every family module of the real `gitlab_api.families` package is the
    key of a row of the real `operations-index.md` whose family is that module, and every record's operation ID is
    the Reference of a row whose key is the record's `(method, path)`. The failure message names each module and key
    or ID; the module's socket guard is installed, so the check runs with no network access."""
    registry = registry_module()
    problems = family_problems(rows=index_rows(path=INDEX), families=registry.discover_families())
    assert not problems, "declarations the operations index does not bear out:\n" + "\n".join(problems)


# --- Issue #41 AC-6.1: a `/<route-prefix>/` key is held to the rule as any other key ------------------------------


def test_a_route_prefix_key_is_held_to_the_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, package_prefix: str
) -> None:
    """AC-6.1: the synthetic `gamma` without `RELEASE_FILE`, a `/<route-prefix>/` key, on its `PENDING` makes
    `coverage_gaps` return that row beside the other unlisted rows, and the gap report lists the key under
    `families/gamma.py`; no route prefix is excluded from the rule."""
    registry = registry_module()
    monkeypatch.syspath_prepend(path=str(tmp_path))
    assert RELEASE_FILE.path.startswith(ROUTE_PREFIX), f"{RELEASE_FILE} is no {ROUTE_PREFIX} key"
    index = tmp_path / "operations-index.md"
    index.write_text(data=index_text(rows=SYNTHETIC_ROWS), encoding="utf-8")
    rows = index_rows(path=index)
    alpha_beta, gamma = CHECKER_FAMILIES
    unlisted = SyntheticFamily(family=gamma.family, records=gamma.records, pending=gamma.pending - {RELEASE_FILE.key})
    package = write_package(root=tmp_path, name=f"{package_prefix}_route_prefix", families=(alpha_beta, unlisted))
    mapped, pending = declared_keys(families=registry.discover_families(package=package))

    gaps = coverage_gaps(rows=rows, mapped=mapped, pending=pending)

    assert gaps == sorted((*UNLISTED_ROWS, RELEASE_FILE)), f"coverage_gaps returned {gaps}"
    listed = gaps_by_family(gaps=gaps).get(unlisted.module_name, {})
    assert listed.get(RELEASE_FILE.key) == [RELEASE_FILE.reference], f"families/gamma.py is told to list {listed}"
    report = gap_report(gaps=gaps)
    assert repr(RELEASE_FILE.key) in report, report


# --- Issue #41 AC-6.2, AC-6.3: every GraphQL-only capability is served or pending ---------------------------------


def test_a_capability_neither_served_nor_pending_is_named() -> None:
    """AC-6.2: on a synthetic table and capability module, `capability_problems` names the capability that is neither
    served nor pending, the `PENDING_CAPABILITIES` entry the table lacks and the record capability the table lacks,
    and not the served or the pending capability; a module that accounts for every capability has no problem."""
    registry = registry_module()
    module = capability_module(
        registry=registry,
        served=(SERVED_CAPABILITY, RETIRED_SERVED_CAPABILITY),
        pending=(PENDING_CAPABILITY, RETIRED_PENDING_CAPABILITY),
    )

    problems = capability_problems(capabilities=SYNTHETIC_CAPABILITIES, module=module)

    named = [capability for capability in EVERY_CAPABILITY if any(repr(capability) in line for line in problems)]
    assert named == [UNLISTED_CAPABILITY, RETIRED_PENDING_CAPABILITY, RETIRED_SERVED_CAPABILITY], problems
    assert len(problems) == len(named), f"one problem per named capability: {problems}"
    accounted = capability_module(
        registry=registry, served=(SERVED_CAPABILITY,), pending=(PENDING_CAPABILITY, UNLISTED_CAPABILITY)
    )
    assert capability_problems(capabilities=SYNTHETIC_CAPABILITIES, module=accounted) == []


def test_the_only_in_graphql_table_is_read_whole() -> None:
    """AC-6.2: `only_in_graphql` reads the real `graphql/conventions.md` table under `### Only in GraphQL` from its
    first data row, `Work items`, to its last, `Query cost introspection`, each capability once, and nothing of its
    header and separator rows or of the `### Only in REST` table that follows it."""
    capabilities = only_in_graphql(path=CONVENTIONS)

    assert capabilities[:1] == [FIRST_CAPABILITY], (
        f"the first capability read is not {FIRST_CAPABILITY!r}: {capabilities}"
    )
    assert capabilities[-1:] == [LAST_CAPABILITY], (
        f"the last capability read is not {LAST_CAPABILITY!r}: {capabilities}"
    )
    assert len(set(capabilities)) == len(capabilities), f"a capability is read twice: {capabilities}"
    only_in_rest = table_first_cells(path=CONVENTIONS, heading=ONLY_IN_REST_HEADING)
    assert only_in_rest, f"{CONVENTIONS.name}: the {ONLY_IN_REST_HEADING!r} table has no rows to tell apart"
    leaked = [
        cell
        for cell in capabilities
        if cell in (CAPABILITY_HEADER, *only_in_rest) or not cell.strip(SEPARATOR_CHARACTERS)
    ]
    assert not leaked, f"only_in_graphql read {leaked}, which are no Only in GraphQL row"


def test_every_graphql_only_capability_is_served_or_pending() -> None:
    """AC-6.2, AC-6.3: every first cell of the real "Only in GraphQL" table, experimental or not, is served by a
    `graphql_only` record's `capability` or held in `graphql_only.PENDING_CAPABILITIES`, and neither names a
    capability the table lacks. `gitlab_api.graphql_only` is imported inside the test; the failure message names
    each capability."""
    graphql_only = graphql_only_module()
    assert hasattr(graphql_only, ATTRIBUTE_PENDING_CAPABILITIES), (
        f"{GRAPHQL_ONLY} declares no {ATTRIBUTE_PENDING_CAPABILITIES}; design D6 holds there every capability of the "
        "Only in GraphQL table that no record serves"
    )

    problems = capability_problems(capabilities=only_in_graphql(path=CONVENTIONS), module=graphql_only)

    assert not problems, "GraphQL-only capabilities neither served nor pending, or unknown:\n" + "\n".join(problems)
