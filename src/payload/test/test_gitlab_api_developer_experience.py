"""Tests for ``gitlab_api/families/developer_experience.py``, the ``developer-experience`` endpoint family of the GitLab
wrapper (issue #38, the remaining stage groups of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4, AC-5 and AC-7).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose key sorts to this module, ``key_families`` of
``test/test_gitlab_wrapper_coverage.py``) and ``docs/api-reference/gitlab/rest/developer-experience.md`` and
``rest/tenant-scale.md`` (each section's endpoints, its heading, and the ``In``, ``Type``, ``Required`` and ``Notes``
columns of its ``| Attribute | In | Type |`` table). What is pinned:

- AC-1, UB-2: ``OPERATIONS`` as ``{operation_id: (method, path)}`` is ``RECORD_ENDPOINTS``, each ID declared once: every
  Reference of those rows but the IDs AC-2 keeps, the three ``tenant-scale#`` References whose keys (``GET /projects``,
  ``DELETE /projects/:id/share/:group_id``) sort to this module (DL-003) among them, with its section's endpoint (of
  several, the first ``/projects/:id/...`` one, else the first);
- AC-2: ``PENDING`` is exactly the second and third endpoints of "File path, branches, and tags name", whose record
  takes the first;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``ARRAY`` for an ``array of string`` row, ``HASH`` for
  ``hash``); the ``required`` names of every record, exactly its query and body rows whose Required reads ``yes``; a
  JSON body and no ``fixed`` pairs on every record;
- AC-5: the ``Paging`` of every record: ``OFFSET`` for a ``GET`` section headed "List" or with a ``page`` row, ``NONE``
  for every other, none ``KEYSET``; "Sudo" by its ``page`` row;
- AC-7: each ``Paging.OFFSET`` record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for
  every placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``).

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test, so the module collects whatever the family declares. The fake GitLab host
and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_developer_experience.py`` (no network).
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
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_developer_experience_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY = "developer_experience"
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
TOKEN = "glpat-gitlab-api-developer-experience-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
METHOD_GET = "GET"
OPTION_PATH = "--path"
ASSIGNED = "="
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
ID_SEPARATOR = "#"
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

# A path parameter as operations-index.md and rest/developer-experience.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The synthetic item each page holds; the wrapper prints every item as the host serves it.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind`, `registry.BodyFormat` and `registry.Paging` member names the tables hold, and the `fixed`
# pairs every record carries (none).
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
BODY_JSON = "JSON"
PAGING_NONE = "NONE"
PAGING_OFFSET = "OFFSET"
NO_FIXED: Tuple[Tuple[str, str], ...] = ()

# --- The tables, transcribed from docs/api-reference/gitlab -----------------------------------------------------------

# operations-index.md and rest/developer-experience.md: every record, by ID, sorted: each Reference of the rows whose
# key sorts to this module (`key_families`), but AC-2's, with the method and path of its section's endpoint (AC-1). The
# three `tenant-scale#` IDs are References of the rows of `GET /projects` and `DELETE /projects/:id/share/:group_id`,
# keys that sort to `developer_experience` (DL-003). The first two sections are examples with literal paths.
RECORD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "developer-experience#file-path-branches-and-tags-name": ("GET", "/projects/1/repository/files/src%2FREADME.md"),
    "developer-experience#namespaced-paths": ("GET", "/projects/diaspora%2Fdiaspora"),
    "developer-experience#path-parameters": ("DELETE", "/projects/:id/share/:group_id"),
    "developer-experience#sudo": ("GET", "/projects"),
    "tenant-scale#delete-a-shared-project-link-in-a-group": ("DELETE", "/projects/:id/share/:group_id"),
    "tenant-scale#list-all-projects": ("GET", "/projects"),
    "tenant-scale#list-all-projects-assigned-to-a-topic": ("GET", "/projects"),
}

# AC-2: "File path, branches, and tags name" lists `GET /projects/1/repository/files/src%2FREADME.md` first, then the
# two below; no endpoint is a `/projects/:id/...` one, so its record takes the first and the others stay pending.
OTHER_ENDPOINT_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("GET", "/projects/1/branches/my%2Fbranch/commits"),
        ("GET", "/projects/1/repository/tags/my%2Ftag"),
    }
)
PENDING_KEYS: FrozenSet[Tuple[str, str]] = OTHER_ENDPOINT_KEYS

# rest/developer-experience.md and rest/tenant-scale.md: every query and body row of a record whose Kind is not SCALAR
# (AC-4). Every other row's Type is `string`, `boolean`, `integer`, `integer (int32)`, `string (date-time)`,
# `string (date)`, `datetime` or `date`.
NON_SCALAR_PARAMS: Dict[Tuple[str, str], str] = {
    ("developer-experience#sudo", "topic"): KIND_ARRAY,
    ("tenant-scale#list-all-projects", "custom_attributes"): KIND_HASH,
    ("tenant-scale#list-all-projects-assigned-to-a-topic", "topic"): KIND_ARRAY,
}

# rest/developer-experience.md and rest/tenant-scale.md: no query or body row of a record reads `yes` in Required
# (AC-4).
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {}

# rest/developer-experience.md and rest/tenant-scale.md: every record that is a `GET` section headed "List" or with a
# `page` row (AC-5), sorted; each is `Paging.OFFSET` and has a case of `test_a_list_record_prints_every_page`.
LIST_RECORDS: Tuple[str, ...] = (
    "developer-experience#sudo",
    "tenant-scale#list-all-projects",
    "tenant-scale#list-all-projects-assigned-to-a-topic",
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


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


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
    """One case per entry of ``LIST_RECORDS``, with the path of its record, named by its anchor."""
    return [
        pytest.param(operation_id, RECORD_ENDPOINTS[operation_id][1], id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id in LIST_RECORDS
    ]


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
    """AC-2: ``PENDING`` is exactly the second and third endpoints of "File path, branches, and tags name", whose
    record takes the first."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, f"{FAMILY}.PENDING is not the keys AC-2 keeps pending:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )


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


# --- AC-5, AC-7: the list records ---------------------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-5: the ``Paging.OFFSET`` records are exactly ``LIST_RECORDS``; every other record is ``Paging.NONE``, and
    none is ``Paging.KEYSET``."""
    family = gitlab_module(name=FAMILY_MODULE)
    paged = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    listed = frozenset(LIST_RECORDS)
    expected = {
        operation_id: PAGING_OFFSET if operation_id in listed else PAGING_NONE for operation_id in RECORD_ENDPOINTS
    }
    assert paged == expected, "the paged records are not the sections' lists (AC-5):\n" + mapping_difference(
        declared=paged, expected=expected
    )


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_page(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-7: ``call <id> --path NAME=VALUE ...`` against two pages, the second named by the first's ``x-next-page``,
    exits 0, requests both pages at their exact URLs and prints both items as one JSON array."""
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
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_url), (METHOD_GET, next_url)], (
        "each page requested as Transport.pages does (#13 AC-2.5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-7):\n{captured.out}"
    )
