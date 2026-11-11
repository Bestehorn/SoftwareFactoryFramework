"""Tests of the ``pulls`` family's records (``github_api/families/pulls.py``; issue #32 AC-2, AC-3, AC-4).

Installed from ``src/payload/test/test_github_api_pulls.py`` to ``test/test_github_api_pulls.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every expected value here is transcribed from
``docs/api-reference/github/rest/pulls.md`` and ``conventions.md``, never read from the records. The family is the
operation IDs of ``rest/pulls.md`` that start with ``pulls/``; its ``agent-merge/`` and ``pull-request-stacks/``
sections belong to other families.

- ``RESIDUAL_IDS``: the IDs of the family left on ``PENDING`` once every other record is declared:
  ``pulls/update-branch``, which writes the pull request's head branch (AC-2, #32 DL-002);
- ``PAGED_OPERATIONS``: each operation of the family whose section has a ``Paging:`` line, with its path as the
  section's index row writes it and a value for each of its path parameters but ``owner`` and ``repo``. Each of these
  sections reads "items: the response body is the array", and ``conventions.md`` "Lists wrapped in an object" names
  none of them, so none has an item key; every one documents ``per_page`` (AC-3, AC-4).

``github_wrapper_fixtures.run_product_case`` (loaded by path) runs a case through the product entry script's
``main(argv=...)`` in the fixture project (``origin`` ``o/r``) against the fake GitHub host, and judges its exit code,
its standard output exactly, its requests other than ``GET`` and that every request was routed. These rows are not in
``CASES``, so the fork never runs them. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_pulls.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

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
FAMILY_NAME = "pulls"
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

#: AC-2: the IDs of the family that stay on ``PENDING`` (#32 DL-002).
RESIDUAL_IDS: FrozenSet[str] = frozenset({"pulls/update-branch"})

# The path parameter values the cases give (``owner`` and ``repo`` default to the fixture's ``origin``, ``o/r``).
PARAM_PULL_NUMBER = "pull_number"
PARAM_REVIEW_ID = "review_id"
PULL_NUMBER = "77"
REVIEW_ID = "80"
PLACEHOLDER_OWNER = "{owner}"
PLACEHOLDER_REPO = "{repo}"
PLACEHOLDER_START = "{"


@dataclass(frozen=True)
class PagedOperation:
    """A ``Paging.LINK`` operation as its section of ``rest/pulls.md`` documents it: its ID, its path as the index row
    writes it, the value the case gives each path parameter but ``owner`` and ``repo``, and the item key
    ``conventions.md`` "Lists wrapped in an object" names for it (``None``: the response body is the array)."""

    operation_id: str
    path: str
    path_values: Tuple[Tuple[str, str], ...] = ()
    item_key: Optional[str] = None


ON_PULL_77 = ((PARAM_PULL_NUMBER, PULL_NUMBER),)

#: Every section of ``rest/pulls.md`` with a ``Paging:`` line whose ID starts with ``pulls/``, in the file's order.
PAGED_OPERATIONS: Tuple[PagedOperation, ...] = (
    PagedOperation(operation_id="pulls/list-review-comments-for-repo", path="/repos/{owner}/{repo}/pulls/comments"),
    PagedOperation(
        operation_id="pulls/list-review-comments",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/comments",
        path_values=ON_PULL_77,
    ),
    PagedOperation(operation_id="pulls/list", path="/repos/{owner}/{repo}/pulls"),
    PagedOperation(
        operation_id="pulls/list-commits",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/commits",
        path_values=ON_PULL_77,
    ),
    PagedOperation(
        operation_id="pulls/list-files",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/files",
        path_values=ON_PULL_77,
    ),
    PagedOperation(
        operation_id="pulls/list-reviews",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        path_values=ON_PULL_77,
    ),
    PagedOperation(
        operation_id="pulls/list-comments-for-review",
        path="/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments",
        path_values=(*ON_PULL_77, (PARAM_REVIEW_ID, REVIEW_ID)),
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
    """``github_api.families.pulls`` from the product scripts directory beside this suite; one imported from any other
    directory fails the calling test."""
    fx.import_api_module(name=REGISTRY)  # puts the product scripts directory on ``sys.path``
    module = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}, not {FAMILY_FILE}"
    return module


def _record_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """What keeps ``record`` from AC-3's fixed fields: no multi-segment parameter (no ``Parameter`` row of
    ``rest/pulls.md`` reads "may contain ``/``"), no item key (``conventions.md`` names none for this family), and the
    default version and media type."""
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
    """AC-2: ``pulls.PENDING`` is exactly ``{"pulls/update-branch"}``: every other operation ID of the family has its
    record."""
    family = _family()

    assert family.PENDING == RESIDUAL_IDS, (
        f"families/{FAMILY_NAME}.py has pending IDs {sorted(family.PENDING)}; only {sorted(RESIDUAL_IDS)} expected"
    )


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the family's ``Paging.LINK`` records are exactly the operations of ``PAGED_CASES`` (the family's sections
    with a ``Paging:`` line), and every record has no multi-segment parameter, no item key, ``API_VERSION_DEFAULT``
    and ``ACCEPT_JSON``."""
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
