"""Tests of the GitHub wrapper's ``secret-scanning`` family, ``github_api/families/secret_scanning.py`` (issue #31
``change.md``; AC-1, AC-3, AC-4, AC-6).

Every expected value here is transcribed from ``docs/api-reference/github/rest/secret-scanning.md`` and
``conventions.md``, never read from the records or from ``commands/call.py``:

- ``SECRET_SCANNING_OPERATION_IDS``: the operations of ``rest/secret-scanning.md`` ("GitHub REST API —
  ``secret-scanning`` (17 operations)"), each of which has one record and none of which is pending (AC-1);
- ``MULTI_SEGMENT_PARAMETERS``: for each section with one, the path parameters whose ``Parameter`` row reads "may
  contain `/` (multi-segment path)" (AC-3). No row of ``rest/secret-scanning.md`` reads so, so the table is empty and
  every record's ``multi_segment`` is empty;
- ``LIST_RECORDS``: each section with a ``Paging:`` line (AC-4): its path, the key that line names after "items in"
  (``None`` where it reads "the response body is the array", as every ``Paging:`` line of this family does;
  ``conventions.md`` "Lists wrapped in an object" names no ``secret-scanning/`` operation), and whether its
  ``Parameter`` table documents ``per_page`` (the custom-pattern lists are cursor-based alone and do not).

``test_a_list_record_prints_every_item`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page (both on one page where no ``per_page`` is sent); standard output is both as one JSON array. Each
case runs with ``fx.run_product_case`` through the product entry script's ``main(argv=...)`` in the fixture project
(``origin`` ``o/r``), which judges its exit code, its standard output exactly, its requests other than ``GET`` and
that every request was routed, so a wrong ``item_key`` exits 1 and a wrong path reaches no route.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_secret_scanning.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
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

REGISTRY = "registry"
TRANSPORT = "transport"
FAMILY_MODULE_NAME = "secret_scanning"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY_MODULE_NAME}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY_MODULE_NAME}.py"

AC_6 = "AC-6"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
PATH_OWNER = "owner"
PATH_REPO = "repo"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"

#: Every operation of ``rest/secret-scanning.md``, listed in its order: custom-patterns, push-protection,
#: secret-scanning.
SECRET_SCANNING_OPERATION_IDS = frozenset(
    {
        "secret-scanning/list-org-custom-patterns",
        "secret-scanning/bulk-create-org-custom-patterns",
        "secret-scanning/bulk-delete-org-custom-patterns",
        "secret-scanning/update-org-custom-pattern",
        "secret-scanning/list-repo-custom-patterns",
        "secret-scanning/bulk-create-repo-custom-patterns",
        "secret-scanning/bulk-delete-repo-custom-patterns",
        "secret-scanning/update-repo-custom-pattern",
        "secret-scanning/list-org-pattern-configs",
        "secret-scanning/update-org-pattern-configs",
        "secret-scanning/list-alerts-for-org",
        "secret-scanning/list-alerts-for-repo",
        "secret-scanning/get-alert",
        "secret-scanning/update-alert",
        "secret-scanning/list-locations-for-alert",
        "secret-scanning/create-push-protection-bypass",
        "secret-scanning/get-scan-history",
    }
)

#: AC-3: for each ``secret-scanning/`` section with one, its path parameters whose row reads "may contain `/`
#: (multi-segment path)": none in ``rest/secret-scanning.md``.
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {}


@dataclass(frozen=True)
class ListRecord:
    """A ``Paging.LINK`` record as its section documents it: the operation ID, the path template, the key its items
    sit under (``None``: the body is the array), and whether it documents ``per_page``."""

    operation_id: str
    path: str
    item_key: Optional[str]
    per_page: bool


#: AC-4, AC-6: every ``secret-scanning/`` section with a ``Paging:`` line.
LIST_RECORDS: Tuple[ListRecord, ...] = (
    # ``Paging: cursor-based (`after`, `before`)`` and no ``per_page`` row: both items arrive on one page.
    ListRecord(
        operation_id="secret-scanning/list-org-custom-patterns",
        path="/orgs/{org}/secret-scanning/custom-patterns",
        item_key=None,
        per_page=False,
    ),
    ListRecord(
        operation_id="secret-scanning/list-repo-custom-patterns",
        path="/repos/{owner}/{repo}/secret-scanning/custom-patterns",
        item_key=None,
        per_page=False,
    ),
    ListRecord(
        operation_id="secret-scanning/list-alerts-for-org",
        path="/orgs/{org}/secret-scanning/alerts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="secret-scanning/list-alerts-for-repo",
        path="/repos/{owner}/{repo}/secret-scanning/alerts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="secret-scanning/list-locations-for-alert",
        path="/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations",
        item_key=None,
        per_page=True,
    ),
)

#: The two items every list case serves, one per page where the record documents ``per_page``.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def path_value(*, name: str) -> str:
    """A path parameter's test value: alphanumeric, so nothing needs encoding, and made from its name, so a value
    given under another name changes the path."""
    return f"{TEST_VALUE_PREFIX}{NON_ALPHANUMERIC.sub(repl='', string=name)}"


def path_values(*, listed: ListRecord) -> Dict[str, str]:
    """The value of each placeholder of ``listed.path``, in path order: the fixture's ``origin`` for ``owner`` and
    ``repo``, else ``path_value``'s."""
    origin = {PATH_OWNER: fx.OWNER, PATH_REPO: fx.REPOSITORY}
    return {name: origin.get(name, path_value(name=name)) for name in PATH_PLACEHOLDER.findall(string=listed.path)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written."""
    return PATH_PLACEHOLDER.sub(repl=lambda match: values[match.group(1)], string=path)


def list_argv(*, listed: ListRecord, values: Mapping[str, str]) -> Tuple[str, ...]:
    """``call <id>``, ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, and ``--query
    per_page=1`` when the record documents ``per_page`` (#28 design D8)."""
    argv = [CALL, listed.operation_id]
    for name, value in values.items():
        if name not in ORIGIN_PARAMETERS:
            argv.extend((OPTION_PATH, f"{name}={value}"))
    if listed.per_page:
        argv.extend((OPTION_QUERY, QUERY_ONE_PER_PAGE))
    return tuple(argv)


def list_case(*, listed: ListRecord) -> Any:
    """#28 design D8's golden case of ``listed``: exit 0, standard output both items as one JSON array, against a list
    route serving them under the record's item key on its expanded path."""
    values = path_values(listed=listed)
    return fx.GoldenCase(
        name=f"{AC_6}/exit-0/{listed.operation_id}",
        argv=list_argv(listed=listed, values=values),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.ListRouteSpec(
                url=expanded(path=listed.path, values=values), items=LISTED_ITEMS, item_key=listed.item_key
            ),
        ),
    )


def list_record_name(listed: ListRecord) -> str:
    """The test id of a ``LIST_RECORDS`` row."""
    return listed.operation_id


def secret_scanning_family() -> ModuleType:
    """``github_api.families.secret_scanning``, imported from the ``scripts`` directory beside this suite
    (``fx.import_api_module`` puts it on ``sys.path``); a copy imported from anywhere else fails here."""
    fx.import_api_module(name=REGISTRY)
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def records_by_id(*, family: ModuleType) -> Dict[str, Any]:
    """Each ``RestOperation`` of ``family.OPERATIONS``, keyed by its operation ID."""
    registry = fx.import_api_module(name=REGISTRY)
    return {record.operation_id: record for record in family.OPERATIONS if isinstance(record, registry.RestOperation)}


def differences(*, declared: Mapping[str, Any], expected: Mapping[str, Any]) -> List[str]:
    """One line per ID whose value in ``declared`` is not its value in ``expected``, absent counted as a value."""
    return [
        f"{json.dumps(obj=operation_id)}: declared {declared.get(operation_id)!r}, "
        f"the section documents {expected.get(operation_id)!r}"
        for operation_id in sorted(set(declared) | set(expected))
        if declared.get(operation_id) != expected.get(operation_id)
    ]


def test_nothing_is_pending() -> None:
    """AC-1: ``PENDING`` is empty, and ``OPERATIONS`` holds one record of every operation of
    ``rest/secret-scanning.md``, none twice and none of another ID."""
    family = secret_scanning_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    problems = []
    pending = frozenset(family.PENDING)
    if pending:
        problems.append(f"PENDING still holds {len(pending)} IDs: {sorted(pending)}")
    missing = sorted(SECRET_SCANNING_OPERATION_IDS - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - SECRET_SCANNING_OPERATION_IDS)
    if extra:
        problems.append(f"records of IDs rest/secret-scanning.md does not document: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-3: every operation of ``rest/secret-scanning.md`` has a record, and each declares ``API_VERSION_DEFAULT`` and
    ``ACCEPT_JSON``, so ``call`` sends them."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=secret_scanning_family())
    problems = []
    for operation_id in sorted(SECRET_SCANNING_OPERATION_IDS):
        record = records.get(operation_id)
        if record is None:
            problems.append(f"{json.dumps(obj=operation_id)}: no record")
            continue
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{json.dumps(obj=operation_id)}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{json.dumps(obj=operation_id)}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-3: each record's ``multi_segment`` is its section's "may contain `/` (multi-segment path)" rows, which
    ``MULTI_SEGMENT_PARAMETERS`` holds: so ``{operation_id: multi_segment}`` over the records with one equals it (it is
    empty), and every operation of ``rest/secret-scanning.md`` has a record, so none is left unjudged."""
    records = records_by_id(family=secret_scanning_family())
    declared = {operation_id: frozenset(record.multi_segment) for operation_id, record in records.items()}
    expected = {
        operation_id: MULTI_SEGMENT_PARAMETERS.get(operation_id, frozenset())
        for operation_id in SECRET_SCANNING_OPERATION_IDS
    }

    problems = differences(declared=declared, expected=expected)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-4: the family's ``Paging.LINK`` records are exactly the sections of ``LIST_RECORDS``, the ones with a
    ``Paging:`` line, so every other record of the family is ``Paging.NONE``."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=secret_scanning_family())
    paged = {operation_id for operation_id, record in records.items() if record.paging == registry.Paging.LINK}
    cased = {listed.operation_id for listed in LIST_RECORDS}

    assert paged == cased, (
        f"Paging.LINK records without a case: {sorted(paged - cased)}; "
        f"cases without a Paging.LINK record: {sorted(cased - paged)}"
    )


@pytest.mark.parametrize(argnames="listed", argvalues=LIST_RECORDS, ids=list_record_name)
def test_a_list_record_prints_every_item(
    listed: ListRecord, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record against a fake host serving two items under its
    item key prints both as one JSON array and exits 0, having asked for one page per item where the record documents
    ``per_page`` and one page where it does not; every request was routed."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"
