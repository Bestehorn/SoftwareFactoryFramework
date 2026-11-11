"""Tests of the GitHub wrapper's ``teams`` family, ``github_api/families/teams.py`` (issue #29 ``change.md``; AC-1 to
AC-3, the slice test module of #28 design D8).

Every expected value here is transcribed from ``docs/api-reference/github/rest/teams.md`` and ``conventions.md``, never
read from the records or from ``commands/call.py``:

- ``TEAMS_OPERATION_IDS``: the operation ID of every section of ``teams.md``, in section order (each is a ``teams/``
  row of ``operations-index.md``);
- ``MULTI_SEGMENT_PARAMETERS``: empty, since no ``Parameter`` row of ``teams.md`` reads "may contain `/`
  (multi-segment path)" (AC-2);
- ``LIST_RECORDS``: each section with a ``Paging:`` line or a ``Link`` response header (AC-2): its path, the one key
  after "items in" (``None``: every one reads "items: the response body is the array", and "Lists wrapped in an
  object" names no ``teams/`` operation), and whether its ``Parameter`` table documents ``per_page``.

``teams/check-permissions-for-repo-in-org`` names ``application/vnd.github.v3.repository+json``; its record sends
``ACCEPT_JSON`` all the same (``change.md`` Residuals), so every record is judged against the default media type.

``test_a_list_record_prints_every_item`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page; standard output is both as one JSON array (AC-3). Each case runs with ``fx.run_product_case``
through the product entry script's ``main(argv=...)`` in the fixture project (``origin`` ``o/r``), which judges its
exit code, its standard output exactly, its requests other than ``GET`` and that every request was routed.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_teams.py`` (no network).
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
FAMILY = "teams"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_3 = "AC-3"
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

#: AC-1: the operation ID of every section of ``rest/teams.md``, in section order.
TEAMS_OPERATION_IDS: Tuple[str, ...] = (
    # members
    "teams/list-pending-invitations-in-org",
    "teams/list-members-in-org",
    "teams/get-membership-for-user-in-org",
    "teams/add-or-update-membership-for-user-in-org",
    "teams/remove-membership-for-user-in-org",
    "teams/list-pending-invitations-legacy",
    "teams/list-members-legacy",
    "teams/get-member-legacy",
    "teams/add-member-legacy",
    "teams/remove-member-legacy",
    "teams/get-membership-for-user-legacy",
    "teams/add-or-update-membership-for-user-legacy",
    "teams/remove-membership-for-user-legacy",
    # teams
    "teams/list",
    "teams/create",
    "teams/get-by-name",
    "teams/update-in-org",
    "teams/delete-in-org",
    "teams/list-repos-in-org",
    "teams/check-permissions-for-repo-in-org",
    "teams/add-or-update-repo-permissions-in-org",
    "teams/remove-repo-in-org",
    "teams/list-child-in-org",
    "teams/get-legacy",
    "teams/update-legacy",
    "teams/delete-legacy",
    "teams/list-repos-legacy",
    "teams/check-permissions-for-repo-legacy",
    "teams/add-or-update-repo-permissions-legacy",
    "teams/remove-repo-legacy",
    "teams/list-child-legacy",
    "teams/list-for-authenticated-user",
)

#: AC-2: for each ``teams/`` section with one, its path parameters whose row reads "may contain `/` (multi-segment
#: path)": no section of ``teams.md`` has such a row.
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {}


@dataclass(frozen=True)
class ListRecord:
    """A ``Paging.LINK`` record as its section documents it: the operation ID, the path template, the key its items
    sit under (``None``: the body is the array), whether it documents ``per_page``, and each path value the case gives
    in place of ``path_value``'s, as ``(name, value)`` pairs."""

    operation_id: str
    path: str
    item_key: Optional[str]
    per_page: bool
    values: Tuple[Tuple[str, str], ...] = ()


#: AC-2, AC-3: every ``teams/`` section with a ``Paging:`` line or a ``Link`` response header, in section order.
LIST_RECORDS: Tuple[ListRecord, ...] = (
    ListRecord(
        operation_id="teams/list-pending-invitations-in-org",
        path="/orgs/{org}/teams/{team_slug}/invitations",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-members-in-org",
        path="/orgs/{org}/teams/{team_slug}/members",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-pending-invitations-legacy",
        path="/teams/{team_id}/invitations",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-members-legacy",
        path="/teams/{team_id}/members",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list",
        path="/orgs/{org}/teams",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-repos-in-org",
        path="/orgs/{org}/teams/{team_slug}/repos",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-child-in-org",
        path="/orgs/{org}/teams/{team_slug}/teams",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-repos-legacy",
        path="/teams/{team_id}/repos",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-child-legacy",
        path="/teams/{team_id}/teams",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="teams/list-for-authenticated-user",
        path="/user/teams",
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
    ``repo``, else the record's own value or ``path_value``'s."""
    origin = {PATH_OWNER: fx.OWNER, PATH_REPO: fx.REPOSITORY}
    given = dict(listed.values)
    return {
        name: origin.get(name, given.get(name, path_value(name=name)))
        for name in PATH_PLACEHOLDER.findall(string=listed.path)
    }


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written, a ``/`` kept literal."""
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
        name=f"{AC_3}/exit-0/{listed.operation_id}",
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


def teams_family() -> ModuleType:
    """``github_api.families.teams``, imported from the ``scripts`` directory beside this suite
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
    """AC-1: ``PENDING`` is empty, and ``OPERATIONS`` holds one record of every ID of ``TEAMS_OPERATION_IDS``, none
    twice and none of another ID."""
    family = teams_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    expected = frozenset(TEAMS_OPERATION_IDS)
    problems = []
    pending = frozenset(family.PENDING)
    if pending:
        problems.append(f"PENDING still holds {len(pending)} IDs: {sorted(pending)}")
    missing = sorted(expected - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - expected)
    if extra:
        problems.append(f"records of IDs that are not the family's sections: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-2: every ``teams/`` ID has a record, and each declares ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, so
    ``call`` sends them."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=teams_family())
    problems = []
    for operation_id in TEAMS_OPERATION_IDS:
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
    """AC-2: ``{operation_id: multi_segment}`` over the records with a multi-segment parameter is
    ``MULTI_SEGMENT_PARAMETERS``, the parameters whose row reads "may contain `/` (multi-segment path)": none here."""
    records = records_by_id(family=teams_family())
    declared = {
        operation_id: frozenset(record.multi_segment)
        for operation_id, record in records.items()
        if record.multi_segment
    }

    problems = differences(declared=declared, expected=MULTI_SEGMENT_PARAMETERS)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-2: the family's ``Paging.LINK`` records are exactly the sections of ``LIST_RECORDS``, and every
    ``Paging.NONE`` record has no item key."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=teams_family())
    paged = {operation_id for operation_id, record in records.items() if record.paging == registry.Paging.LINK}
    cased = {listed.operation_id for listed in LIST_RECORDS}
    keyed = sorted(
        operation_id
        for operation_id, record in records.items()
        if record.paging == registry.Paging.NONE and record.item_key is not None
    )
    problems = []
    if paged != cased:
        problems.append(
            f"Paging.LINK records without a case: {sorted(paged - cased)}; "
            f"cases without a Paging.LINK record: {sorted(cased - paged)}"
        )
    if keyed:
        problems.append(f"Paging.NONE records with an item key: {keyed}")

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(argnames="listed", argvalues=LIST_RECORDS, ids=list_record_name)
def test_a_list_record_prints_every_item(
    listed: ListRecord, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record against a fake host serving two items under its
    item key prints both as one JSON array and exits 0, having asked for one page per item where the record documents
    ``per_page``; every request was routed."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"
