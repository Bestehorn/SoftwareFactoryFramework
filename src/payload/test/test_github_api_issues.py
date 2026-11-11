"""Tests of the ``issues`` family's records (``github_api/families/issues.py``; issue #32 AC-2, AC-3, AC-4).

Installed from ``src/payload/test/test_github_api_issues.py`` to ``test/test_github_api_issues.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every expected value here is transcribed from
``docs/api-reference/github/rest/issues.md`` and ``conventions.md``, never read from the records:

- ``RESIDUAL_IDS``: the IDs of the family left on ``PENDING`` once every record is declared: none (AC-2);
- ``PAGED_OPERATIONS``: each operation whose section has a ``Paging:`` line, but ``issues/get-issue-artifact``, with
  its path as the section's index row writes it and a value for each of its path parameters but ``owner`` and
  ``repo``. Each of these sections reads "items: the response body is the array", and ``conventions.md`` "Lists
  wrapped in an object" names none of them, so none has an item key; every one documents ``per_page`` (AC-3, AC-4);
- ``OP_GET_ISSUE_ARTIFACT``: the one section with a ``Paging:`` line that pages the ``versions`` inside one artifact
  (``conventions.md`` "Lists wrapped in an object"), declared ``Paging.NONE`` with no item key (AC-3, #32 DL-004).

``github_wrapper_fixtures.run_product_case`` (loaded by path) runs a case through the product entry script's
``main(argv=...)`` in the fixture project (``origin`` ``o/r``) against the fake GitHub host, and judges its exit code,
its standard output exactly, its requests other than ``GET`` and that every request was routed. These rows are not in
``CASES``, so the fork never runs them. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_issues.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

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
FAMILY_NAME = "issues"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY_NAME}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY_NAME}.py"

AC_4 = "AC-4"

CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPERATION_ID_INDEX = 1  # argv is ``call <operation-id> …``
#: AC-4's page size: one item per page, so the two items of a list arrive over two pages.
PER_PAGE = "1"
#: The pages AC-4's two items arrive on, as each request asks for them (the first names no ``page``).
PAGES_ASKED = [str(fx.FIRST_PAGE), "2"]

#: AC-2: the IDs of the family that stay on ``PENDING``.
RESIDUAL_IDS: FrozenSet[str] = frozenset()

#: ``rest/issues.md`` "Get an issue artifact": a ``Paging:`` line, but its ``200`` is one artifact whose ``versions``
#: are the paged list (``conventions.md`` "Lists wrapped in an object", item key ``versions``).
OP_GET_ISSUE_ARTIFACT = "issues/get-issue-artifact"

# The path parameter values the cases give (``owner`` and ``repo`` default to the fixture's ``origin``, ``o/r``).
PARAM_ISSUE_NUMBER = "issue_number"
PARAM_MILESTONE_NUMBER = "milestone_number"
PARAM_ORG = "org"
ISSUE_NUMBER = "5"
MILESTONE_NUMBER = "3"
ORG = "acme"
PLACEHOLDER_OWNER = "{owner}"
PLACEHOLDER_REPO = "{repo}"
PLACEHOLDER_START = "{"


@dataclass(frozen=True)
class PagedOperation:
    """A ``Paging.LINK`` operation as its section of ``rest/issues.md`` documents it: its ID, its path as the index row
    writes it, the value the case gives each path parameter but ``owner`` and ``repo``, and the item key
    ``conventions.md`` "Lists wrapped in an object" names for it (``None``: the response body is the array)."""

    operation_id: str
    path: str
    path_values: Tuple[Tuple[str, str], ...] = ()
    item_key: Optional[str] = None


ON_ISSUE_5 = ((PARAM_ISSUE_NUMBER, ISSUE_NUMBER),)

#: Every section of ``rest/issues.md`` with a ``Paging:`` line but ``OP_GET_ISSUE_ARTIFACT``, in the file's order.
PAGED_OPERATIONS: Tuple[PagedOperation, ...] = (
    PagedOperation(
        operation_id="issues/list-issue-artifacts",
        path="/repos/{owner}/{repo}/issues/{issue_number}/artifacts",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(operation_id="issues/list-assignees", path="/repos/{owner}/{repo}/assignees"),
    PagedOperation(operation_id="issues/list-comments-for-repo", path="/repos/{owner}/{repo}/issues/comments"),
    PagedOperation(
        operation_id="issues/list-comments",
        path="/repos/{owner}/{repo}/issues/{issue_number}/comments",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(operation_id="issues/list-events-for-repo", path="/repos/{owner}/{repo}/issues/events"),
    PagedOperation(
        operation_id="issues/list-events",
        path="/repos/{owner}/{repo}/issues/{issue_number}/events",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(
        operation_id="issues/list-dependencies-blocked-by",
        path="/repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(
        operation_id="issues/list-dependencies-blocking",
        path="/repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocking",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(
        operation_id="issues/list-issue-field-values-for-issue",
        path="/repos/{owner}/{repo}/issues/{issue_number}/issue-field-values",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(operation_id="issues/list", path="/issues"),
    PagedOperation(operation_id="issues/list-for-org", path="/orgs/{org}/issues", path_values=((PARAM_ORG, ORG),)),
    PagedOperation(operation_id="issues/list-for-repo", path="/repos/{owner}/{repo}/issues"),
    PagedOperation(
        operation_id="issues/list-relates-to",
        path="/repos/{owner}/{repo}/issues/{issue_number}/relates_to",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(
        operation_id="issues/list-suggestions",
        path="/repos/{owner}/{repo}/issues/{issue_number}/suggestions",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(operation_id="issues/list-for-authenticated-user", path="/user/issues"),
    PagedOperation(
        operation_id="issues/list-labels-on-issue",
        path="/repos/{owner}/{repo}/issues/{issue_number}/labels",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(operation_id="issues/list-labels-for-repo", path="/repos/{owner}/{repo}/labels"),
    PagedOperation(
        operation_id="issues/list-labels-for-milestone",
        path="/repos/{owner}/{repo}/milestones/{milestone_number}/labels",
        path_values=((PARAM_MILESTONE_NUMBER, MILESTONE_NUMBER),),
    ),
    PagedOperation(operation_id="issues/list-milestones", path="/repos/{owner}/{repo}/milestones"),
    PagedOperation(
        operation_id="issues/list-sub-issues",
        path="/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
        path_values=ON_ISSUE_5,
    ),
    PagedOperation(
        operation_id="issues/list-events-for-timeline",
        path="/repos/{owner}/{repo}/issues/{issue_number}/timeline",
        path_values=ON_ISSUE_5,
    ),
)


def expanded(*, operation: PagedOperation) -> str:
    """``operation.path`` with ``{owner}`` and ``{repo}`` the fixture's ``origin`` and every other placeholder its
    value in ``operation.path_values``; none of these values needs encoding."""
    path = operation.path.replace(PLACEHOLDER_OWNER, fx.OWNER).replace(PLACEHOLDER_REPO, fx.REPOSITORY)
    for name, value in operation.path_values:
        path = path.replace(f"{{{name}}}", value)
    assert PLACEHOLDER_START not in path, f"{operation.operation_id}: {path} keeps a placeholder with no value"
    return path


def listed_item(*, path: str, number: int) -> Dict[str, Any]:
    """One item of the list on ``path``, cut to an ID and a URL."""
    return {fx.FIELD_ID: number, fx.FIELD_URL: f"{fx.API_ORIGIN}{path}/{number}"}


def _paged_case(*, operation: PagedOperation) -> Any:
    """#28 design D8's case for a ``Paging.LINK`` record: ``call <id>`` with ``--path`` for each path parameter but
    ``owner`` and ``repo`` and ``--query per_page=1``, against a list route of two items under the operation's item key;
    standard output is both items as one indented JSON array."""
    path = expanded(operation=operation)
    items = (listed_item(path=path, number=1), listed_item(path=path, number=2))
    path_options = tuple(word for name, value in operation.path_values for word in (OPTION_PATH, f"{name}={value}"))
    return fx.GoldenCase(
        name=f"{AC_4}/exit-0/{operation.operation_id}",
        argv=(CALL, operation.operation_id, *path_options, OPTION_QUERY, f"{fx.QUERY_PER_PAGE}={PER_PAGE}"),
        stdout=fx.printed_json(value=list(items)),
        exit_code=fx.EXIT_OK,
        routes=(fx.ListRouteSpec(url=path, items=items, item_key=operation.item_key),),
    )


PAGED_CASES: Tuple[Any, ...] = tuple(_paged_case(operation=operation) for operation in PAGED_OPERATIONS)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def _family() -> ModuleType:
    """``github_api.families.issues`` from the product scripts directory beside this suite; one imported from any other
    directory fails the calling test."""
    fx.import_api_module(name=REGISTRY)  # puts the product scripts directory on ``sys.path``
    module = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}, not {FAMILY_FILE}"
    return module


def _records_of(*, records: Sequence[Any], operation_id: str) -> List[Any]:
    """Every record of ``records`` with ``operation_id``."""
    return [record for record in records if record.operation_id == operation_id]


def _artifact_problems(*, records: Sequence[Any], paging_none: Any) -> List[str]:
    """What keeps ``OP_GET_ISSUE_ARTIFACT`` from being one ``Paging.NONE`` record with no item key."""
    named = json.dumps(obj=OP_GET_ISSUE_ARTIFACT)
    matches = _records_of(records=records, operation_id=OP_GET_ISSUE_ARTIFACT)
    if len(matches) != 1:
        return [f"{named}: families/{FAMILY_NAME}.py declares {len(matches)} records with this ID, one expected"]
    record = matches[0]
    problems = []
    if record.paging != paging_none:
        problems.append(f"{named}: paging {record.paging}, Paging.NONE expected (#32 DL-004)")
    if record.item_key is not None:
        problems.append(f"{named}: item_key {record.item_key!r}, None expected (#32 DL-004)")
    return problems


def _record_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """What keeps ``record`` from AC-3's fixed fields: no multi-segment parameter (no ``Parameter`` row of
    ``rest/issues.md`` reads "may contain ``/``"), no item key (``conventions.md`` names none for this family but
    ``OP_GET_ISSUE_ARTIFACT``'s, which DL-004 declares ``None``), and the default version and media type."""
    named = json.dumps(obj=record.operation_id)
    problems = []
    if record.multi_segment:
        problems.append(f"{named}: multi_segment {sorted(record.multi_segment)}, none expected")
    if record.item_key is not None:
        problems.append(f"{named}: item_key {record.item_key!r}, None expected")
    if record.api_version != transport.API_VERSION_DEFAULT:
        problems.append(f"{named}: api_version {record.api_version!r}, {transport.API_VERSION_DEFAULT!r} expected")
    if record.accept != transport.ACCEPT_JSON:
        problems.append(f"{named}: accept {record.accept!r}, {transport.ACCEPT_JSON!r} expected")
    return problems


def test_only_the_residual_ids_are_pending() -> None:
    """AC-2: ``issues.PENDING`` is empty: every operation ID of ``rest/issues.md`` has its record."""
    family = _family()

    assert family.PENDING == RESIDUAL_IDS, (
        f"families/{FAMILY_NAME}.py still has pending IDs: {sorted(family.PENDING - RESIDUAL_IDS)}"
    )


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the family's ``Paging.LINK`` records are exactly the operations of ``PAGED_CASES`` (the sections with a
    ``Paging:`` line but ``issues/get-issue-artifact``); ``issues/get-issue-artifact`` is one ``Paging.NONE`` record
    with no item key; and every record has no multi-segment parameter, no item key, ``API_VERSION_DEFAULT`` and
    ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(_family().OPERATIONS)

    linked = {record.operation_id for record in records if record.paging == registry.Paging.LINK}
    cased = {case.argv[OPERATION_ID_INDEX] for case in PAGED_CASES}
    problems = []
    if linked != cased:
        problems.append(
            f"Paging.LINK records missing {sorted(cased - linked)} and unexpected {sorted(linked - cased)}; "
            f"rest/{FAMILY_NAME}.md pages {sorted(cased)}"
        )
    problems.extend(_artifact_problems(records=records, paging_none=registry.Paging.NONE))
    for record in records:
        problems.extend(_record_problems(record=record, transport=transport))

    assert problems == [], f"families/{FAMILY_NAME}.py breaks AC-3: {problems}"


@pytest.mark.parametrize(argnames="case", argvalues=PAGED_CASES, ids=fx.case_name)
def test_a_paged_record_prints_every_page(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4: ``call <id>`` with ``--query per_page=1`` exits 0 and prints both items the host serves as one indented
    JSON array, read over two pages: the first, then the one its ``rel="next"`` names; every request was routed."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    asked = [request.query.get(fx.QUERY_PAGE, [str(fx.FIRST_PAGE)])[-1] for request in requests]
    assert asked == PAGES_ASKED, f"{case.name}: the pages asked for are {asked}, {PAGES_ASKED} expected"
    sizes = [request.query.get(fx.QUERY_PER_PAGE) for request in requests]
    assert all(size == [PER_PAGE] for size in sizes), f"{case.name}: per_page sent as {sizes}"
