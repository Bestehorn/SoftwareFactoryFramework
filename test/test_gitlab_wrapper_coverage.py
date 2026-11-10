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
from typing import AbstractSet, FrozenSet, Iterable, Iterator, Mapping, NamedTuple, Sequence, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "src" / "payload" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

PACKAGE = "gitlab_api"
REGISTRY = PACKAGE + ".registry"
INDEX = ROOT / "docs" / "api-reference" / "gitlab" / "operations-index.md"

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
