"""Tests of the ``projects`` records of the GitHub wrapper (``github_api/families/projects.py``; issue #33 AC-2 to
AC-4, the slice test module of #28 design D8).

Installed from ``src/payload/test/test_github_api_projects.py`` to ``test/test_github_api_projects.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every operation ID, path template and item key below is
transcribed from the ``projects/`` rows of ``docs/api-reference/github/operations-index.md``, the sections of
``rest/projects.md`` they link and ``conventions.md`` "Lists wrapped in an object", never read from the records:

- ``PAGED_SECTIONS``: the sections with a ``Paging:`` line, each with its path template, a value for each path
  parameter but ``owner`` and ``repo``, and its item key. Every one reads "items: the response body is the array", and
  "Lists wrapped in an object" names no ``projects`` operation, so no item key is set. Every one documents
  ``per_page``, beside its ``after``/``before`` cursor;
- ``UNPAGED_IDS``: the sections without a ``Paging:`` line. The ``get-`` sections answer one object with a ``Link``
  header, which does not page (DL-006).

``test_a_paged_record_prints_every_page`` runs one golden case per paged section with
``github_wrapper_fixtures.run_product_case`` (loaded by path, as ``test_github_api_call.py`` loads it): ``call <id>``
with ``--path`` for each path parameter but ``owner`` and ``repo`` (the fixture project's ``origin`` is ``o/r``) and
``--query per_page=1``, against a fake host serving two items, one per page, each page's ``Link`` naming the next. The
structural tests read the family module imported from the ``scripts`` directory beside this suite. No test opens a
connection.

Run: ``python scripts/run_tests.py test/test_github_api_projects.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
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
FAMILY = "projects"
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

ORG = "octo-org"
USERNAME = "octocat"
PROJECT_NUMBER = "3"
VIEW_NUMBER = "4"

FIELD_ID = fx.FIELD_ID
FIELD_NAME = fx.FIELD_NAME
#: The two items every paged case's host serves, cut to two fields.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {FIELD_ID: 1, FIELD_NAME: "first"},
    {FIELD_ID: 2, FIELD_NAME: "second"},
)

#: AC-2: what ``PENDING`` keeps. The two residuals of the slice, ``markdown/render-raw`` and
#: ``copilot/set-copilot-content-exclusion-for-organization``, are not this family's.
RESIDUAL_PENDING: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class PagedSection:
    """A section of ``rest/projects.md`` with a ``Paging:`` line: its operation ID, its path template, a value for
    each path parameter but ``owner`` and ``repo`` (name, value), and the item key its ``Paging:`` line names after
    "items in" (``None``: the response body is the array)."""

    operation_id: str
    path: str
    path_values: Tuple[Tuple[str, str], ...]
    item_key: Optional[str] = None


PAGED_SECTIONS: Tuple[PagedSection, ...] = (
    PagedSection(
        operation_id="projects/list-fields-for-org",
        path="/orgs/{org}/projectsV2/{project_number}/fields",
        path_values=(("org", ORG), ("project_number", PROJECT_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-fields-for-user",
        path="/users/{username}/projectsV2/{project_number}/fields",
        path_values=(("username", USERNAME), ("project_number", PROJECT_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-items-for-org",
        path="/orgs/{org}/projectsV2/{project_number}/items",
        path_values=(("org", ORG), ("project_number", PROJECT_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-view-items-for-org",
        path="/orgs/{org}/projectsV2/{project_number}/views/{view_number}/items",
        path_values=(("org", ORG), ("project_number", PROJECT_NUMBER), ("view_number", VIEW_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-items-for-user",
        path="/users/{username}/projectsV2/{project_number}/items",
        path_values=(("username", USERNAME), ("project_number", PROJECT_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-view-items-for-user",
        path="/users/{username}/projectsV2/{project_number}/views/{view_number}/items",
        path_values=(("username", USERNAME), ("project_number", PROJECT_NUMBER), ("view_number", VIEW_NUMBER)),
    ),
    PagedSection(
        operation_id="projects/list-for-org",
        path="/orgs/{org}/projectsV2",
        path_values=(("org", ORG),),
    ),
    PagedSection(
        operation_id="projects/list-for-user",
        path="/users/{username}/projectsV2",
        path_values=(("username", USERNAME),),
    ),
)

#: The sections of ``rest/projects.md`` without a ``Paging:`` line.
UNPAGED_IDS: FrozenSet[str] = frozenset(
    {
        "projects/create-draft-item-for-org",
        "projects/create-draft-item-for-authenticated-user",
        "projects/add-field-for-org",
        "projects/get-field-for-org",
        "projects/add-field-for-user",
        "projects/get-field-for-user",
        "projects/add-item-for-org",
        "projects/get-org-item",
        "projects/update-item-for-org",
        "projects/delete-item-for-org",
        "projects/add-item-for-user",
        "projects/get-user-item",
        "projects/update-item-for-user",
        "projects/delete-item-for-user",
        "projects/get-for-org",
        "projects/get-for-user",
        "projects/create-view-for-org",
        "projects/create-view-for-user",
    }
)

PAGED_IDS: FrozenSet[str] = frozenset(section.operation_id for section in PAGED_SECTIONS)
FAMILY_IDS: FrozenSet[str] = PAGED_IDS | UNPAGED_IDS
#: The item key each record must carry: its paged section's, and ``None`` for every other record (AC-3).
ITEM_KEYS: Mapping[str, Optional[str]] = {section.operation_id: section.item_key for section in PAGED_SECTIONS}


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


def _family() -> ModuleType:
    """``github_api.families.projects``, imported from the ``scripts`` directory beside this suite."""
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
    """AC-2: ``projects.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == RESIDUAL_PENDING, f"{FAMILY_MODULE}.PENDING still holds {sorted(pending - RESIDUAL_PENDING)}"


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections, one each; the ``Paging.LINK`` ones are exactly the sections with a
    ``Paging:`` line (the paged cases' IDs); and every record has no ``multi_segment`` name, its section's item key
    (none for a bare array or an operation that does not page), ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(FAMILY_IDS), f"{FAMILY_MODULE} declares {declared}, its sections are {sorted(FAMILY_IDS)}"
    paged = frozenset(record.operation_id for record in records if record.paging == registry.Paging.LINK)
    assert paged == PAGED_IDS, f"Paging.LINK records {sorted(paged)}, sections with a Paging line {sorted(PAGED_IDS)}"
    problems = [problem for record in records for problem in _rule_problems(record=record, transport=transport)]
    assert problems == [], f"{FAMILY_MODULE}: {problems}"


@pytest.mark.parametrize(argnames="case", argvalues=PAGED_CASES, ids=fx.case_name)
def test_a_paged_record_prints_every_page(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4: ``call <id>`` of a ``Paging.LINK`` record with ``--query per_page=1`` exits 0 and prints both items the
    host serves, one per page, as ``printed_json`` of the two; every request was routed, one per page."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    urls = [request.url for request in requests]
    assert len(requests) == len(LISTED_ITEMS), f"{case.name}: one request per page expected, sent {urls}"
