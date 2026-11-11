"""Tests of the GitHub wrapper's ``activity`` family, ``github_api/families/activity.py`` (issue #32 ``change.md``;
AC-2, AC-3, AC-4).

Installed from ``src/payload/test/test_github_api_activity.py`` to ``test/test_github_api_activity.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every expected value here is transcribed from
``docs/api-reference/github/rest/activity.md`` and ``conventions.md``, never read from the records:

- ``ACTIVITY_OPERATION_IDS``: the operation ID of every section of ``rest/activity.md`` ("GitHub REST API —
  ``activity`` (34 operations)"); ``RESIDUAL_IDS``, the ones left pending, is empty (AC-2);
- ``ITEM_KEYS``: the item key ``conventions.md`` "Lists wrapped in an object" names for an ID of this family; its
  table has no ``activity/`` row, so every record's ``item_key`` is ``None`` (AC-3);
- ``PAGED_RECORDS``: each section with a ``Paging:`` line, with the path of its operation line. Every such line is
  page-based and every such section documents ``per_page`` (AC-3, AC-4).

``test_a_paged_record_prints_every_page`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1``, against a fake host serving two items on the expanded path with no item key, one per page; standard
output is both as one JSON array (AC-4). The ``{org}`` rows, which no test repository reaches (#28 D5), are called
here on the fake host like the others. ``github_wrapper_fixtures.run_product_case`` (loaded by path, as
``test_github_api_call.py`` loads it) runs each case through the product entry script's ``main(argv=...)`` in the
fixture project (``origin`` ``o/r``), and judges its exit code, its standard output exactly, its requests other than
``GET`` and that every request was routed. These rows are not in ``CASES``, so the fork never runs them. No test
opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_activity.py`` (no network).
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
from typing import Any, Dict, FrozenSet, List, Mapping, Tuple

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
FAMILY = "activity"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_4 = "AC-4"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPERATION_ID_INDEX = 1  # argv is ``call <operation-id> …``
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")

PATH_OWNER = "owner"
PATH_REPO = "repo"
PATH_USERNAME = "username"
PATH_ORG = "org"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
ORG_LOGIN = "acme"
#: The value of each path parameter of ``PAGED_RECORDS`` in a case: ``owner`` and ``repo`` are the fixture's
#: ``origin``; the others are alphanumeric, so nothing needs encoding, and differ, so a value sent under another name
#: reaches another path.
PATH_VALUES: Mapping[str, str] = {
    PATH_OWNER: fx.OWNER,
    PATH_REPO: fx.REPOSITORY,
    PATH_USERNAME: fx.USER_LOGIN,
    PATH_ORG: ORG_LOGIN,
}

#: Every operation ID of ``rest/activity.md``, one per section, in its order: events, feeds, notifications, starring,
#: watching.
ACTIVITY_OPERATION_IDS: FrozenSet[str] = frozenset(
    {
        "activity/list-public-events",
        "activity/list-public-events-for-repo-network",
        "activity/list-public-org-events",
        "activity/list-repo-events",
        "activity/list-events-for-authenticated-user",
        "activity/list-org-events-for-authenticated-user",
        "activity/list-public-events-for-user",
        "activity/list-received-events-for-user",
        "activity/list-received-public-events-for-user",
        "activity/get-feeds",
        "activity/list-notifications-for-authenticated-user",
        "activity/mark-notifications-as-read",
        "activity/get-thread",
        "activity/mark-thread-as-read",
        "activity/mark-thread-as-done",
        "activity/get-thread-subscription-for-authenticated-user",
        "activity/set-thread-subscription",
        "activity/delete-thread-subscription",
        "activity/list-repo-notifications-for-authenticated-user",
        "activity/mark-repo-notifications-as-read",
        "activity/list-stargazers-for-repo",
        "activity/get-stargazer-count-for-repo",
        "activity/get-stargazer-history-for-repo",
        "activity/list-repos-starred-by-authenticated-user",
        "activity/check-repo-is-starred-by-authenticated-user",
        "activity/star-repo-for-authenticated-user",
        "activity/unstar-repo-for-authenticated-user",
        "activity/list-repos-starred-by-user",
        "activity/list-watchers-for-repo",
        "activity/get-repo-subscription",
        "activity/set-repo-subscription",
        "activity/delete-repo-subscription",
        "activity/list-watched-repos-for-authenticated-user",
        "activity/list-repos-watched-by-user",
    }
)
#: AC-2: the IDs of this family left on ``PENDING``: none.
RESIDUAL_IDS: FrozenSet[str] = frozenset()
#: AC-1, AC-2: the IDs ``OPERATIONS`` holds a record of, each once.
RECORDED_IDS = ACTIVITY_OPERATION_IDS - RESIDUAL_IDS
#: AC-3: the item key ``conventions.md`` "Lists wrapped in an object" names for an ID of this family; its table has no
#: ``activity/`` row, so each record's ``item_key`` is ``None``.
ITEM_KEYS: Mapping[str, str] = {}


@dataclass(frozen=True)
class PagedRecord:
    """A section of ``rest/activity.md`` with a ``Paging:`` line: its operation ID and the path of its operation
    line."""

    operation_id: str
    path: str


#: AC-3, AC-4: every section of ``rest/activity.md`` with a ``Paging:`` line. ``activity/list-stargazers-for-repo`` and
#: ``activity/list-repos-starred-by-user`` name no items on that line; their ``200`` is an array all the same.
PAGED_RECORDS: Tuple[PagedRecord, ...] = (
    PagedRecord(operation_id="activity/list-public-events", path="/events"),
    PagedRecord(operation_id="activity/list-public-events-for-repo-network", path="/networks/{owner}/{repo}/events"),
    PagedRecord(operation_id="activity/list-public-org-events", path="/orgs/{org}/events"),
    PagedRecord(operation_id="activity/list-repo-events", path="/repos/{owner}/{repo}/events"),
    PagedRecord(operation_id="activity/list-events-for-authenticated-user", path="/users/{username}/events"),
    PagedRecord(
        operation_id="activity/list-org-events-for-authenticated-user", path="/users/{username}/events/orgs/{org}"
    ),
    PagedRecord(operation_id="activity/list-public-events-for-user", path="/users/{username}/events/public"),
    PagedRecord(operation_id="activity/list-received-events-for-user", path="/users/{username}/received_events"),
    PagedRecord(
        operation_id="activity/list-received-public-events-for-user", path="/users/{username}/received_events/public"
    ),
    PagedRecord(operation_id="activity/list-notifications-for-authenticated-user", path="/notifications"),
    PagedRecord(
        operation_id="activity/list-repo-notifications-for-authenticated-user",
        path="/repos/{owner}/{repo}/notifications",
    ),
    PagedRecord(operation_id="activity/list-stargazers-for-repo", path="/repos/{owner}/{repo}/stargazers"),
    PagedRecord(
        operation_id="activity/get-stargazer-history-for-repo", path="/repos/{owner}/{repo}/stargazers/history"
    ),
    PagedRecord(operation_id="activity/list-repos-starred-by-authenticated-user", path="/user/starred"),
    PagedRecord(operation_id="activity/list-repos-starred-by-user", path="/users/{username}/starred"),
    PagedRecord(operation_id="activity/list-watchers-for-repo", path="/repos/{owner}/{repo}/subscribers"),
    PagedRecord(operation_id="activity/list-watched-repos-for-authenticated-user", path="/user/subscriptions"),
    PagedRecord(operation_id="activity/list-repos-watched-by-user", path="/users/{username}/subscriptions"),
)

#: The two items every paged case serves; with ``per_page=1`` each is a page of its own.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)
PAGES = len(LISTED_ITEMS)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def path_values(*, paged: PagedRecord) -> Dict[str, str]:
    """The ``PATH_VALUES`` value of each placeholder of ``paged.path``, in path order."""
    return {name: PATH_VALUES[name] for name in PATH_PLACEHOLDER.findall(string=paged.path)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written."""
    return PATH_PLACEHOLDER.sub(repl=lambda match: values[match.group(1)], string=path)


def paged_argv(*, operation_id: str, values: Mapping[str, str]) -> Tuple[str, ...]:
    """``call <id>``, ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, and ``--query
    per_page=1`` (#28 design D8)."""
    argv = [CALL, operation_id]
    for name, value in values.items():
        if name not in ORIGIN_PARAMETERS:
            argv.extend((OPTION_PATH, f"{name}={value}"))
    argv.extend((OPTION_QUERY, QUERY_ONE_PER_PAGE))
    return tuple(argv)


def paged_case(*, paged: PagedRecord) -> Any:
    """#28 design D8's golden case of ``paged``: exit 0, standard output both items as one JSON array, against a list
    route serving them with no item key on the expanded path."""
    values = path_values(paged=paged)
    return fx.GoldenCase(
        name=f"{AC_4}/exit-0/{paged.operation_id}",
        argv=paged_argv(operation_id=paged.operation_id, values=values),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.ListRouteSpec(
                url=expanded(path=paged.path, values=values),
                items=LISTED_ITEMS,
                item_key=ITEM_KEYS.get(paged.operation_id),
            ),
        ),
    )


#: AC-4: one golden case per section of ``PAGED_RECORDS``.
PAGED_CASES: Tuple[Any, ...] = tuple(paged_case(paged=paged) for paged in PAGED_RECORDS)


def family_module() -> ModuleType:
    """``github_api.families.activity``, imported from the ``scripts`` directory beside this suite
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


def test_only_the_residual_ids_are_pending() -> None:
    """AC-2: ``PENDING`` is exactly ``RESIDUAL_IDS`` (empty), and ``OPERATIONS`` holds one record of every other
    operation of ``rest/activity.md``, none twice and none of another ID."""
    family = family_module()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    problems: List[str] = []
    pending = frozenset(family.PENDING)
    if pending != RESIDUAL_IDS:
        problems.append(f"PENDING holds {len(pending)} IDs, {sorted(RESIDUAL_IDS)} expected: {sorted(pending)}")
    missing = sorted(RECORDED_IDS - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - RECORDED_IDS)
    if extra:
        problems.append(f"records of IDs that are not to be recorded: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the family's ``Paging.LINK`` records are exactly the operations of ``PAGED_CASES``, the sections with a
    ``Paging:`` line, so every other record is ``Paging.NONE``; and the record of each ID of ``rest/activity.md`` has
    no multi-segment parameter, the item key of ``ITEM_KEYS`` (``None`` for every ID here), ``API_VERSION_DEFAULT``
    and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=family_module())
    problems: List[str] = []
    paged = {operation_id for operation_id, record in records.items() if record.paging == registry.Paging.LINK}
    cased = {case.argv[OPERATION_ID_INDEX] for case in PAGED_CASES}
    if paged != cased:
        problems.append(
            f"Paging.LINK records without a paged case: {sorted(paged - cased)}; "
            f"paged cases without a Paging.LINK record: {sorted(cased - paged)}"
        )
    for operation_id in sorted(RECORDED_IDS):
        record = records.get(operation_id)
        named = json.dumps(obj=operation_id)
        if record is None:
            problems.append(f"{named}: no record")
            continue
        if record.multi_segment:
            problems.append(f"{named}: multi_segment {sorted(record.multi_segment)}, none documented")
        if record.item_key != ITEM_KEYS.get(operation_id):
            problems.append(f"{named}: item_key {record.item_key!r}, {ITEM_KEYS.get(operation_id)!r} documented")
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{named}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{named}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


@pytest.mark.parametrize(argnames="case", argvalues=PAGED_CASES, ids=fx.case_name)
def test_a_paged_record_prints_every_page(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record, with ``--path`` for each path parameter but
    ``owner`` and ``repo`` and ``--query per_page=1``, against a fake host serving two items on its expanded path,
    exits 0 and prints both as one JSON array, having asked for one page per item; every request was routed."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert len(requests) == PAGES, f"{case.name}: {len(requests)} requests, {PAGES} pages expected"
