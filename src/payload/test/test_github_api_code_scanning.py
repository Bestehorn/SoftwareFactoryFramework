"""Tests of the GitHub wrapper's ``code-scanning`` family, ``github_api/families/code_scanning.py`` (issue #31
``change.md``; AC-1, AC-3, AC-4, AC-6, UB-2; issue #14 ``change.md``: AC-1, AC-2, AC-3).

Every expected value here is transcribed from ``docs/api-reference/github/rest/code-scanning.md`` and
``conventions.md``, never read from the records or from ``commands/call.py``:

- ``CODE_SCANNING_OPERATION_IDS``: the operation ID of every section of ``code-scanning.md`` (25), each with its
  record and none pending (#14 AC-1, AC-2);
- ``MULTI_SEGMENT_PARAMETERS``: empty, as no ``Parameter`` row of ``code-scanning.md`` reads "may contain `/`
  (multi-segment path)" (AC-3);
- ``LIST_RECORDS``: each section with a ``Paging:`` line (AC-4): its path, the key after "items in" (``None``: every
  one of these lines reads "the response body is the array", and no ``code-scanning/`` ID is in ``conventions.md``
  "Lists wrapped in an object"), and whether its ``Parameter`` table documents ``per_page``;
  ``code-scanning/list-codeql-databases`` has no ``Paging:`` line, so it is not one of them;
- ``BRANCH_WRITING_CALLS``: #14 AC-3's record of this family, ``code-scanning/commit-autofix``, which commits to
  ``target_ref``, called with every path parameter but ``owner`` and ``repo`` and every body member its section
  documents, so only a refusal keeps the request from being sent.

``test_a_list_record_prints_every_item`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page; standard output is both as one JSON array. ``test_a_branch_writing_record_is_refused`` runs #14
AC-3's call the same way and expects exit 2, no request and a log record naming the ID and that no subcommand sends
it. Each case runs with ``fx.run_product_case`` through the product entry script's ``main(argv=...)`` in the fixture
project (``origin`` ``o/r``), which judges its exit code, its standard output exactly, its requests other than ``GET``
(none at all for a refusal) and that every request was routed.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_code_scanning.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
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
FAMILY = "code_scanning"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_6 = "AC-6"
ISSUE_14_AC_3 = "#14 AC-3"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "--raw-field"
PATH_OWNER = "owner"
PATH_REPO = "repo"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

#: #14 AC-3: "Commit an autofix for a code scanning alert" commits to ``target_ref``, so ``call`` refuses it.
COMMIT_AUTOFIX = "code-scanning/commit-autofix"

#: Every operation ID of ``rest/code-scanning.md``, one per section.
CODE_SCANNING_OPERATION_IDS = frozenset(
    {
        "code-scanning/commit-autofix",
        "code-scanning/create-autofix",
        "code-scanning/create-variant-analysis",
        "code-scanning/delete-analysis",
        "code-scanning/delete-codeql-database",
        "code-scanning/get-ai-scan-enablement",
        "code-scanning/get-ai-scan-enablement-for-org",
        "code-scanning/get-alert",
        "code-scanning/get-analysis",
        "code-scanning/get-autofix",
        "code-scanning/get-codeql-database",
        "code-scanning/get-default-setup",
        "code-scanning/get-sarif",
        "code-scanning/get-variant-analysis",
        "code-scanning/get-variant-analysis-repo-task",
        "code-scanning/list-alert-instances",
        "code-scanning/list-alerts-for-org",
        "code-scanning/list-alerts-for-repo",
        "code-scanning/list-codeql-databases",
        "code-scanning/list-recent-analyses",
        "code-scanning/update-ai-scan-enablement",
        "code-scanning/update-ai-scan-enablement-for-org",
        "code-scanning/update-alert",
        "code-scanning/update-default-setup",
        "code-scanning/upload-sarif",
    }
)
#: AC-1, #14 AC-1: the IDs ``OPERATIONS`` holds a record of, each once: every ``code-scanning/`` ID of the reference,
#: ``code-scanning/commit-autofix`` included.
RECORDED_IDS = CODE_SCANNING_OPERATION_IDS

#: AC-3: no ``code-scanning/`` section has a path parameter whose row reads "may contain `/` (multi-segment path)".
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


#: AC-4, AC-6: every ``code-scanning/`` section with a ``Paging:`` line.
LIST_RECORDS: Tuple[ListRecord, ...] = (
    ListRecord(
        operation_id="code-scanning/list-alerts-for-org",
        path="/orgs/{org}/code-scanning/alerts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="code-scanning/list-alerts-for-repo",
        path="/repos/{owner}/{repo}/code-scanning/alerts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="code-scanning/list-alert-instances",
        path="/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="code-scanning/list-recent-analyses",
        path="/repos/{owner}/{repo}/code-scanning/analyses",
        item_key=None,
        per_page=True,
    ),
)

#: The two items every list case serves, one per page where the record documents ``per_page``.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)


@dataclass(frozen=True)
class BranchWritingCall:
    """A #14 AC-3 record of this family and the arguments after ``call <id>``: every path parameter but ``owner`` and
    ``repo``, and every body member its section documents."""

    operation_id: str
    arguments: Tuple[str, ...]


#: #14 AC-3: the record of this family whose call commits to a branch, ``target_ref``; its section documents the path
#: parameter ``alert_number`` and the body members ``target_ref`` and ``message``.
BRANCH_WRITING_CALLS: Tuple[BranchWritingCall, ...] = (
    BranchWritingCall(
        operation_id=COMMIT_AUTOFIX,
        arguments=(
            OPTION_PATH,
            "alert_number=42",
            OPTION_RAW_FIELD,
            "target_ref=refs/heads/main",
            OPTION_RAW_FIELD,
            "message=Fix the code scanning alert",
        ),
    ),
)
#: #14 AC-3's refusal: the log record says that no subcommand sends the operation (``commands/call.py`` maps it to
#: none).
NO_SUBCOMMAND_SENDS_IT = r"(?i)\bno\b[\w\s-]*\bsubcommand\b[\w\s-]*\bsends\b"


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


def refusal_case(*, branch_writing: BranchWritingCall) -> Any:
    """#14 AC-3's golden case of ``branch_writing``: exit 2, nothing on standard output, no request, and one log record
    naming the ID as ``json.dumps`` renders it (#28 D4) and that no subcommand sends it."""
    return fx.GoldenCase(
        name=f"{ISSUE_14_AC_3}/exit-2/{branch_writing.operation_id}",
        argv=(CALL, branch_writing.operation_id, *branch_writing.arguments),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(re.escape(json.dumps(obj=branch_writing.operation_id)), NO_SUBCOMMAND_SENDS_IT), withheld=()
        ),
    )


def list_record_name(listed: ListRecord) -> str:
    """The test id of a ``LIST_RECORDS`` row."""
    return listed.operation_id


def branch_writing_name(branch_writing: BranchWritingCall) -> str:
    """The test id of a ``BRANCH_WRITING_CALLS`` row."""
    return branch_writing.operation_id


def code_scanning_family() -> ModuleType:
    """``github_api.families.code_scanning``, imported from the ``scripts`` directory beside this suite
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
    """#14 AC-1, AC-2: ``PENDING`` is empty, and ``OPERATIONS`` holds one record of every ``code-scanning/`` ID of the
    reference, ``code-scanning/commit-autofix`` included, none twice and none of another ID."""
    family = code_scanning_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    problems = []
    pending = sorted(family.PENDING)
    if pending:
        problems.append(f"PENDING still holds {len(pending)} IDs: {pending}")
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


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-3, #14 AC-1: every ``code-scanning/`` ID has a record, ``code-scanning/commit-autofix`` included, and each
    declares ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, so ``call`` sends them (``get-analysis`` and
    ``get-codeql-database`` included, DL-005)."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=code_scanning_family())
    problems = []
    for operation_id in sorted(RECORDED_IDS):
        record = records.get(operation_id)
        if record is None:
            problems.append(f"{json.dumps(obj=operation_id)}: no record")
            continue
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{json.dumps(obj=operation_id)}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{json.dumps(obj=operation_id)}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


def test_the_branch_writing_record_has_no_item_key_and_no_content_type() -> None:
    """#14 AC-1: the one record of ``code-scanning/commit-autofix`` in ``OPERATIONS``, found by its ID as a literal, has
    ``item_key`` ``None`` (its section has no ``Paging:`` line) and ``content_type`` ``None`` (its section reads
    "Request body (`application/json`, optional)": a JSON body)."""
    operation_id = "code-scanning/commit-autofix"
    matches = [record for record in code_scanning_family().OPERATIONS if record.operation_id == operation_id]
    assert len(matches) == 1, f"{operation_id}: {FAMILY_FILE.name} declares {len(matches)} records, one expected"
    record = matches[0]
    problems = []
    if record.item_key is not None:
        problems.append(f"item_key {record.item_key!r}, None expected")
    if record.content_type is not None:
        problems.append(f"content_type {record.content_type!r}, None expected")

    assert not problems, f"{json.dumps(obj=operation_id)}: " + "; ".join(problems)


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-3: each record's ``multi_segment`` is its section's parameters whose row reads "may contain `/`
    (multi-segment path)", which is none for every ``code-scanning/`` ID; an ID without a record counts as a
    difference, so the comparison covers the whole family rather than holding of an empty ``OPERATIONS``."""
    records = records_by_id(family=code_scanning_family())
    declared = {operation_id: frozenset(record.multi_segment) for operation_id, record in records.items()}
    expected = {operation_id: MULTI_SEGMENT_PARAMETERS.get(operation_id, frozenset()) for operation_id in RECORDED_IDS}

    problems = differences(declared=declared, expected=expected)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-4: the family's ``Paging.LINK`` records are exactly the sections of ``LIST_RECORDS``, so every other record,
    ``code-scanning/list-codeql-databases`` included, is ``Paging.NONE``."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=code_scanning_family())
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
    ``per_page``; every request was routed."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"


@pytest.mark.parametrize(argnames="branch_writing", argvalues=BRANCH_WRITING_CALLS, ids=branch_writing_name)
def test_a_branch_writing_record_is_refused(
    branch_writing: BranchWritingCall,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#14 AC-3: the record is declared and ``registry.lookup`` returns it, yet its complete ``call`` exits 2 with no
    request, and a log record names the ID and that no subcommand sends it."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=code_scanning_family())
    assert branch_writing.operation_id in records, f"{branch_writing.operation_id} has no record in {FAMILY_FILE.name}"
    assert registry.lookup(operation_id=branch_writing.operation_id) == records[branch_writing.operation_id]
    case = refusal_case(branch_writing=branch_writing)
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)
