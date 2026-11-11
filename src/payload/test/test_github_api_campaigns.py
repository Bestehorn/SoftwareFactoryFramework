"""Tests of the ``campaigns`` records of the GitHub wrapper (``github_api/families/campaigns.py``; issue #33 AC-1 to
AC-4 and AC-6, the slice test module of #28 design D8).

Installed from ``src/payload/test/test_github_api_campaigns.py`` to ``test/test_github_api_campaigns.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every operation ID, path template and item key below is
transcribed from the ``campaigns/`` rows of ``docs/api-reference/github/operations-index.md``, the sections they link in
``rest/campaigns.md`` and ``conventions.md`` "Lists wrapped in an object", never read from the records:

- ``PAGED_SECTIONS``: the one section with a ``Paging:`` line, ``campaigns/list-org-campaigns``, with its path template
  and a value for ``org``. It reads "items: the response body is the array", and "Lists wrapped in an object" names no
  ``campaigns`` operation, so it has no item key; it documents ``per_page``;
- ``UNPAGED_IDS``: the sections without a ``Paging:`` line (the create, read, update and delete of one campaign);
- ``RESIDUAL_PENDING``: none: every ID of the family has its record (AC-2);
- ``REFUSED_CALLS``: AC-6's record of this family, ``campaigns/create-campaign``, whose call creates issues, with the
  arguments of a complete call.

``test_a_paged_record_prints_every_page`` runs one golden case per paged section with
``github_wrapper_fixtures.run_product_case`` (loaded by path, as ``test_github_api_call.py`` loads it): ``call <id>``
with ``--path`` for each path parameter but ``owner`` and ``repo`` (the fixture project's ``origin`` is ``o/r``) and
``--query per_page=1``, against a fake host serving two items (under the section's item key, where it has one), one per
page. ``test_a_branch_writing_record_is_refused`` runs AC-6's call the same way and expects exit 2, no request, and a
log record naming the ID and that no subcommand sends it. The structural tests read the family module imported from the
``scripts`` directory beside this suite. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_campaigns.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import re
import sys
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
FAMILY = "campaigns"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING = "PENDING"

AC_4 = "AC-4"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
PARAM_OWNER = "owner"
PARAM_REPO = "repo"
PAGE_SIZE = 1  # one item per page, so the two items arrive over two pages
AC_6 = "AC-6"
OPTION_RAW_FIELD = "--raw-field"
OPTION_FIELD = "--field"
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

#: The two items every paged case's host serves, one per page.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)

#: AC-2: what ``PENDING`` keeps: nothing.
RESIDUAL_PENDING: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class PagedSection:
    """A section of the family with a ``Paging:`` line: its operation ID, its path template, a value for each path
    parameter but ``owner`` and ``repo`` (name, value), and the item key ``conventions.md`` "Lists wrapped in an
    object" names for it (``None``: the response body is the array)."""

    operation_id: str
    path: str
    path_values: Tuple[Tuple[str, str], ...] = ()
    item_key: Optional[str] = None


#: The sections of the family with a ``Paging:`` line.
PAGED_SECTIONS: Tuple[PagedSection, ...] = (
    PagedSection(
        operation_id="campaigns/list-org-campaigns",
        path="/orgs/{org}/campaigns",
        path_values=(("org", "acme"),),
    ),
)

#: The sections of the family without a ``Paging:`` line.
UNPAGED_IDS: FrozenSet[str] = frozenset(
    {
        "campaigns/create-campaign",
        "campaigns/get-campaign-summary",
        "campaigns/update-campaign",
        "campaigns/delete-campaign",
    }
)

PAGED_IDS: FrozenSet[str] = frozenset(section.operation_id for section in PAGED_SECTIONS)
FAMILY_IDS: FrozenSet[str] = PAGED_IDS | UNPAGED_IDS
#: AC-1: the IDs ``OPERATIONS`` holds a record of, each once: every ID of the family but ``RESIDUAL_PENDING``'s.
RECORDED_IDS: FrozenSet[str] = FAMILY_IDS - RESIDUAL_PENDING
#: The item key each record must carry: its paged section's, and ``None`` for every other record (AC-3).
ITEM_KEYS: Mapping[str, Optional[str]] = {section.operation_id: section.item_key for section in PAGED_SECTIONS}


@dataclass(frozen=True)
class RefusedCall:
    """An AC-6 record of this family and the arguments after ``call <id>``: every path parameter but ``owner`` and
    ``repo``, and the body members that make the call complete, so only a refusal keeps the request from being
    sent."""

    operation_id: str
    arguments: Tuple[str, ...]


CAMPAIGN_ORG = "acme"
FIELD_REPOSITORY_ID = "repository_id"
FIELD_ALERT_NUMBERS = "alert_numbers"
#: The ``code_scanning_alerts`` of the refused call: one repository ID with one alert number of it.
CODE_SCANNING_ALERTS = json.dumps(obj=[{FIELD_REPOSITORY_ID: 1, FIELD_ALERT_NUMBERS: [2]}])

#: AC-6: the records of this family whose call writes a branch or creates issues. ``campaigns/create-campaign`` is
#: called with ``org``, its required body members ``name``, ``description`` and ``ends_at``, the
#: ``code_scanning_alerts`` its ``(body)`` constraint requires one of, and ``generate_issues`` true, the member that
#: makes the call create issues.
REFUSED_CALLS: Tuple[RefusedCall, ...] = (
    RefusedCall(
        operation_id="campaigns/create-campaign",
        arguments=(
            OPTION_PATH,
            f"org={CAMPAIGN_ORG}",
            OPTION_RAW_FIELD,
            "name=Close the alerts",
            OPTION_RAW_FIELD,
            "description=Fix the open code scanning alerts",
            OPTION_RAW_FIELD,
            "ends_at=2026-12-31T00:00:00Z",
            OPTION_FIELD,
            f"code_scanning_alerts={CODE_SCANNING_ALERTS}",
            OPTION_FIELD,
            "generate_issues=true",
        ),
    ),
)
#: AC-6's refusal: the log record says that no subcommand sends the operation (``commands/call.py`` maps it to none).
NO_SUBCOMMAND_SENDS_IT = r"(?i)\bno\b[\w\s-]*\bsubcommand\b[\w\s-]*\bsends\b"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def expanded_path(*, section: PagedSection) -> str:
    """``section``'s path template with ``owner`` and ``repo`` the fixture project's ``origin`` and each other path
    parameter its value; a placeholder without a value raises ``KeyError``."""
    values = {PARAM_OWNER: fx.OWNER, PARAM_REPO: fx.REPOSITORY, **dict(section.path_values)}
    return section.path.format(**values)


def paged_case(*, section: PagedSection) -> Any:
    """AC-4's golden case of ``section``: ``call <id>`` with ``--path`` for each path parameter but ``owner`` and
    ``repo`` and ``--query per_page=1``, against a host serving ``LISTED_ITEMS`` one per page under the section's item
    key; it exits 0 and prints both items as one JSON array."""
    path_options = tuple(word for name, value in section.path_values for word in (OPTION_PATH, f"{name}={value}"))
    return fx.GoldenCase(
        name=f"{AC_4}/exit-0/{section.operation_id}",
        argv=(CALL, section.operation_id, *path_options, OPTION_QUERY, f"{fx.QUERY_PER_PAGE}={PAGE_SIZE}"),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(fx.ListRouteSpec(url=expanded_path(section=section), items=LISTED_ITEMS, item_key=section.item_key),),
    )


PAGED_CASES: Tuple[Any, ...] = tuple(paged_case(section=section) for section in PAGED_SECTIONS)


def refusal_case(*, refused: RefusedCall) -> Any:
    """AC-6's golden case of ``refused``: exit 2, nothing on standard output, no request, and one log record naming
    the ID as ``json.dumps`` renders it (#28 D4) and that no subcommand sends it."""
    return fx.GoldenCase(
        name=f"{AC_6}/exit-2/{refused.operation_id}",
        argv=(CALL, refused.operation_id, *refused.arguments),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(re.escape(json.dumps(obj=refused.operation_id)), NO_SUBCOMMAND_SENDS_IT), withheld=()
        ),
    )


def refused_call_name(refused: RefusedCall) -> str:
    """The test id of a ``REFUSED_CALLS`` row."""
    return refused.operation_id


def records_by_id(*, family: ModuleType) -> Dict[str, Any]:
    """Each ``RestOperation`` of ``family.OPERATIONS``, keyed by its operation ID."""
    registry = fx.import_api_module(name=REGISTRY)
    return {record.operation_id: record for record in family.OPERATIONS if isinstance(record, registry.RestOperation)}


def _family() -> ModuleType:
    """``github_api.families.campaigns``, imported from the ``scripts`` directory beside this suite."""
    fx.import_api_module(name=REGISTRY)  # puts that ``scripts`` directory on ``sys.path``
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def _rule_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """AC-3's problems with ``record``: a ``multi_segment`` name, an item key other than ``ITEM_KEYS`` gives it, an API
    version other than ``API_VERSION_DEFAULT`` or a media type other than ``ACCEPT_JSON``."""
    name = record.operation_id
    expected_key = ITEM_KEYS.get(name)
    problems = []
    if record.multi_segment:
        problems.append(f"{name}: multi_segment {sorted(record.multi_segment)}, expected none")
    if record.item_key != expected_key:
        problems.append(f"{name}: item_key {record.item_key!r}, expected {expected_key!r}")
    if record.api_version != transport.API_VERSION_DEFAULT:
        problems.append(f"{name}: api_version {record.api_version!r}, expected {transport.API_VERSION_DEFAULT!r}")
    if record.accept != transport.ACCEPT_JSON:
        problems.append(f"{name}: accept {record.accept!r}, expected {transport.ACCEPT_JSON!r}")
    return problems


def test_only_the_residual_ids_are_pending() -> None:
    """AC-2: ``campaigns.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == RESIDUAL_PENDING, (
        f"{FAMILY_MODULE}.PENDING holds {sorted(pending)}, expected {sorted(RESIDUAL_PENDING)}"
    )


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections to record, one each; the ``Paging.LINK`` ones are exactly
    the sections with a ``Paging:`` line (the paged cases' IDs); and every record has no ``multi_segment`` name,
    its section's item key (none for a bare array or an operation that does not page), ``API_VERSION_DEFAULT``
    and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(RECORDED_IDS), (
        f"{FAMILY_MODULE} declares {declared}, its sections to record are {sorted(RECORDED_IDS)}"
    )
    paged = frozenset(record.operation_id for record in records if record.paging == registry.Paging.LINK)
    assert paged == PAGED_IDS, f"Paging.LINK records {sorted(paged)}, sections with a Paging line {sorted(PAGED_IDS)}"
    problems = [problem for record in records for problem in _rule_problems(record=record, transport=transport)]
    assert problems == [], f"{FAMILY_MODULE}: {problems}"


@pytest.mark.parametrize(argnames="case", argvalues=PAGED_CASES, ids=fx.case_name)
def test_a_paged_record_prints_every_page(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4: ``call <id>`` of a ``Paging.LINK`` record with ``--query per_page=1`` exits 0 and prints both items the
    host serves, one per page, as ``printed_json`` of the two; every request was routed, one per page (every paged
    section documents ``per_page``)."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    urls = [request.url for request in requests]
    assert len(requests) == len(LISTED_ITEMS), f"{case.name}: one request per page expected, sent {urls}"


@pytest.mark.parametrize(argnames="refused", argvalues=REFUSED_CALLS, ids=refused_call_name)
def test_a_branch_writing_record_is_refused(
    refused: RefusedCall,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-6: the record is declared and ``registry.lookup`` returns it, yet its complete ``call`` exits 2 with no
    request, and a log record names the ID and that no subcommand sends it."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=_family())
    assert refused.operation_id in records, f"{refused.operation_id} has no record in {FAMILY_FILE.name}"
    assert registry.lookup(operation_id=refused.operation_id) == records[refused.operation_id]
    case = refusal_case(refused=refused)
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)
