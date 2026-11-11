"""Tests for ``gitlab_api/families/security_factory.py``, the ``security-factory`` endpoint family of the GitLab wrapper
(issue #42, the security slice of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5 and AC-7).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is ``rest/security-factory.md``) and
``docs/api-reference/gitlab/rest/security-factory.md`` (each section's endpoint, its heading, and the ``In``, ``Type``
and ``Required`` columns of its ``| Attribute | In | Type |`` table). The family had no record at 3beba95, so every
record is a new one. What is pinned:

- AC-1: ``{(method, path): operation_id}`` over the records is the five index keys of the family, each with the
  Reference of its one row (every section has one endpoint);
- AC-2: ``PENDING`` is empty;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``package_manager``, a ``string array`` row, is
  ``ARRAY``), and the ``required`` ``Param`` names of each record, exactly its Required ``yes`` query and body rows;
- AC-5: the ``Paging.OFFSET`` records are the ``GET`` sections headed "List" or "Get all" but
  ``security-factory#list-all-project-security-settings``, which answers one object; no record is ``Paging.KEYSET``;
- AC-7: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by
  ``x-next-page: 2``, exits 0, requests both pages at their exact URLs and prints both items as one JSON array
  (``print_json``).

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, as ``test/test_gitlab_wrapper_coverage.py`` imports it, so the module collects whatever the package lacks. The
fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path as
``test_gitlab_api_call.py`` loads it) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_security_factory.py`` (no network).
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
WRAPPER_MODULE = "gitlab_wrapper_security_factory_under_test"
PACKAGE = "gitlab_api"
REGISTRY = f"{PACKAGE}.registry"
FAMILY_MODULE = f"{PACKAGE}.families.security_factory"
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
TOKEN = "glpat-gitlab-api-security-factory-test"  # pragma: allowlist secret
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

# A path parameter as operations-index.md and rest/security-factory.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` member names a non-SCALAR attribute takes (AC-4).
KIND_ARRAY = "ARRAY"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: every row linking rest/security-factory.md, `(method, path)` to its Reference written
# `security-factory#<anchor>` (AC-1). Each key has one row and each section one endpoint.
KEY_IDS: Dict[Tuple[str, str], str] = {
    ("GET", "/projects/:id/dependencies"): "security-factory#list-project-dependencies",
    ("GET", "/projects/:id/security_settings"): "security-factory#list-all-project-security-settings",
    ("PUT", "/projects/:id/security_settings"): "security-factory#update-the-secret_push_protection_enabled-setting",
    ("GET", "/templates/licenses/:key"): "security-factory#retrieve-a-single-license-template",
    ("GET", "/templates/licenses"): "security-factory#list-all-license-templates",
}

# AC-2: no section of the page has a second endpoint, so nothing stays pending.
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset()

# rest/security-factory.md: every query or body row whose Kind is not SCALAR, by (record ID, attribute name) (AC-4):
# "List project dependencies" `package_manager`, Type `string array`.
TYPED_ATTRIBUTES: Dict[Tuple[str, str], str] = {
    ("security-factory#list-project-dependencies", "package_manager"): KIND_ARRAY,
}

# rest/security-factory.md: the query and body rows whose Required reads `yes`, by record (AC-4). No other record has
# one: "List all license templates" has no `yes` row, and the only `yes` row of the other three sections is `In` `path`.
REQUIRED_ATTRIBUTES: Dict[str, FrozenSet[str]] = {
    "security-factory#update-the-secret_push_protection_enabled-setting": frozenset({"secret_push_protection_enabled"}),
}

# rest/security-factory.md: every `GET` section headed "List" or "Get all" but
# `#list-all-project-security-settings` (AC-5), with its record's path.
LIST_ENDPOINTS: Tuple[Tuple[str, str], ...] = (
    ("security-factory#list-all-license-templates", "/templates/licenses"),
    ("security-factory#list-project-dependencies", "/projects/:id/dependencies"),
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
    """``name`` (``gitlab_api.registry``, ``gitlab_api.families.security_factory``) imported inside a test, as
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


def repeated(*, items: Sequence[Any]) -> List[Any]:
    """Every item ``items`` holds more than once, sorted."""
    return sorted({item for item in items if items.count(item) > 1})


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


# --- AC-1, AC-2: the records and what stays pending -------------------------------------------------------------


def test_every_key_has_its_record() -> None:
    """AC-1: each index key of the family is the method and path of one record, whose ID is its row's Reference; no
    key and no ID is declared twice."""
    family = gitlab_module(name=FAMILY_MODULE)
    records = tuple(family.OPERATIONS)
    keys = [(record.method, record.path) for record in records]
    assert repeated(items=keys) == [], f"keys declared by more than one record: {repeated(items=keys)}"
    operation_ids = [record.operation_id for record in records]
    assert repeated(items=operation_ids) == [], f"IDs declared more than once: {repeated(items=operation_ids)}"
    declared = {(record.method, record.path): record.operation_id for record in records}
    assert declared == KEY_IDS, "the records are not the family's index keys and References (AC-1):\n" + (
        mapping_difference(declared=declared, expected=KEY_IDS)
    )


def test_only_the_unmapped_keys_are_pending() -> None:
    """AC-2: ``PENDING`` is empty once every key has its record."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "security_factory.PENDING is not the keys AC-2 keeps pending:\n" + (
        set_difference(declared=pending, expected=PENDING_KEYS)
    )


# --- AC-4: kinds and required attributes ------------------------------------------------------------------------


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
    assert declared == TYPED_ATTRIBUTES, "the non-SCALAR Params are not the sections' (AC-4):\n" + (
        mapping_difference(declared=declared, expected=TYPED_ATTRIBUTES)
    )


def test_the_required_attributes_are_the_sections() -> None:
    """AC-4: ``{operation_id: names}`` of the ``required`` ``Param``s, over the records with any, is the table of the
    Required ``yes`` query and body rows."""
    family = gitlab_module(name=FAMILY_MODULE)
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required)
        for record in family.OPERATIONS
    }
    declared = {operation_id: names for operation_id, names in required.items() if names}
    assert declared == REQUIRED_ATTRIBUTES, "the required Params are not the sections' `yes` rows (AC-4):\n" + (
        mapping_difference(declared=declared, expected=REQUIRED_ATTRIBUTES)
    )


# --- AC-5, AC-7: the list records -----------------------------------------------------------------------------------


def test_every_list_record_has_a_case() -> None:
    """AC-5: the ``Paging.OFFSET`` records are exactly ``LIST_ENDPOINTS``' IDs, and no record is ``Paging.KEYSET``."""
    registry = gitlab_module(name=REGISTRY)
    family = gitlab_module(name=FAMILY_MODULE)
    offset = {record.operation_id for record in family.OPERATIONS if record.paging is registry.Paging.OFFSET}
    expected = {operation_id for operation_id, _ in LIST_ENDPOINTS}
    assert offset == expected, "the Paging.OFFSET records are not the sections' lists (AC-5):\n" + set_difference(
        declared=offset, expected=expected
    )
    keyset = sorted(record.operation_id for record in family.OPERATIONS if record.paging is registry.Paging.KEYSET)
    assert keyset == [], f"no security-factory list is keyset-paged (AC-5), yet KEYSET: {keyset}"


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_item(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-7: ``call <id> --path NAME=VALUE ...`` against two pages chained by ``x-next-page`` exits 0, requests both
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
        f"one JSON array of both items, in page order, as print_json writes it (AC-7):\n{captured.out}"
    )
