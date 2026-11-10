"""Tests for the GitHub wrapper's operation registry, ``github_api/registry.py`` (design D4; AC-1.1).

Installed from ``src/payload/test/test_github_api_registry.py`` to ``test/test_github_api_registry.py``, beside
``scripts/github_api/``. The records under test belong to a synthetic family: its module is written to the test's own
directory and ``github_api.families.__path__`` points there for the test, so ``discover_families`` finds it the way it
finds a real family (by being there) and no real family takes part. Every request reaches the fake GitHub host of
``github_wrapper_fixtures.py`` (loaded by path) through the transport's own opener; no socket is opened. Each test
imports the package itself, so while a module is not written the test fails on the assertion that names it.

Run: ``python scripts/run_tests.py test/test_github_api_registry.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pytest

FIXTURES_PATH = Path(__file__).resolve().parent / "github_wrapper_fixtures.py"
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
    spec.loader.exec_module(module)
    return module


fx = _load_fixtures()

TOKEN = "registry-test-token"  # pragma: allowlist secret

FAMILIES = "families"
FAMILIES_PACKAGE = f"{fx.PACKAGE}.{FAMILIES}"
FAMILIES_INIT = fx.SCRIPTS_DIR / fx.PACKAGE / FAMILIES / "__init__.py"
SYNTHETIC_FAMILY = "synthetic"
SYNTHETIC_MODULE = f"{FAMILIES_PACKAGE}.{SYNTHETIC_FAMILY}"
SYNTHETIC_PENDING = "synthetic/delete-label"

METHOD_GET = "GET"
METHOD_PATCH = "PATCH"
PAGING_NONE = "NONE"
PAGING_LINK = "LINK"

PARAM_OWNER = "owner"
PARAM_REPO = "repo"
PARAM_ISSUE_NUMBER = "issue_number"
PARAM_NAME = "name"
PARAM_REF = "ref"
PARAM_PATH = "path"
PARAM_TITLE = "title"
PARAM_BODY = "body"
PARAM_STATE = "state"
PARAM_LABELS = "labels"
PARAM_STATUS = "status"
PARAM_PER_PAGE = "per_page"
PARAM_PAGE = "page"
UNDOCUMENTED_BODY_NAME = "milestone_title"
UNDOCUMENTED_QUERY_NAME = "media"
UNDOCUMENTED_LIST_QUERY_NAME = "direction"

FIELD_NUMBER = "number"
FIELD_TITLE = "title"
FIELD_STATE = "state"
FIELD_NAME = "name"
FIELD_PATH = "path"
FIELD_ID = "id"
FIELD_WORKFLOW_RUNS = "workflow_runs"


@dataclass(frozen=True)
class Api:
    """The three modules under test."""

    registry: ModuleType
    transport: ModuleType
    errors: ModuleType


def load_api() -> Api:
    """The registry, transport and errors modules; while one is not written, the calling test fails on its assertion
    (the registry's first, the module this suite tests)."""
    return Api(
        registry=fx.import_api_module(name="registry"),
        transport=fx.import_api_module(name="transport"),
        errors=fx.import_api_module(name="errors"),
    )


@dataclass(frozen=True)
class RecordSpec:
    """A synthetic ``RestOperation``: built in the test for ``expand``, written as source into the synthetic family
    module for ``call`` and ``pages``. Its paths are index rows' paths under the synthetic family's IDs."""

    operation_id: str
    method: str
    path: str
    query_params: Tuple[str, ...] = ()
    body_params: Tuple[str, ...] = ()
    multi_segment: Tuple[str, ...] = ()
    paging: str = PAGING_NONE
    item_key: Optional[str] = None

    def build(self, *, api: Api) -> Any:
        """The record as ``registry.RestOperation``, every field named."""
        return api.registry.RestOperation(
            operation_id=self.operation_id,
            method=self.method,
            path=self.path,
            query_params=frozenset(self.query_params),
            body_params=frozenset(self.body_params),
            multi_segment=frozenset(self.multi_segment),
            paging=api.registry.Paging[self.paging],
            item_key=self.item_key,
            api_version=api.transport.API_VERSION_DEFAULT,
            accept=api.transport.ACCEPT_JSON,
        )

    def source(self) -> str:
        """The record as a family module declares it: one ``RestOperation(...)`` element of ``OPERATIONS``."""
        arguments = (
            f"operation_id={self.operation_id!r}",
            f"method={self.method!r}",
            f"path={self.path!r}",
            f"query_params=frozenset({list(self.query_params)!r})",
            f"body_params=frozenset({list(self.body_params)!r})",
            f"multi_segment=frozenset({list(self.multi_segment)!r})",
            f"paging=Paging.{self.paging}",
            f"item_key={self.item_key!r}",
            "api_version=API_VERSION_DEFAULT",  # pragma: allowlist secret
            "accept=ACCEPT_JSON",
        )
        return "    RestOperation(\n" + "".join(f"        {argument},\n" for argument in arguments) + "    ),\n"


UPDATE_ISSUE = RecordSpec(
    operation_id="synthetic/update-issue",
    method=METHOD_PATCH,
    path="/repos/{owner}/{repo}/issues/{issue_number}",
    body_params=(PARAM_TITLE, PARAM_BODY, PARAM_STATE, PARAM_LABELS),
)
GET_CONTENT = RecordSpec(
    operation_id="synthetic/get-content",
    method=METHOD_GET,
    path="/repos/{owner}/{repo}/contents/{path}",
    query_params=(PARAM_REF,),
    multi_segment=(PARAM_PATH,),
)
GET_REF = RecordSpec(
    operation_id="synthetic/get-ref",
    method=METHOD_GET,
    path="/repos/{owner}/{repo}/git/ref/{ref}",
    multi_segment=(PARAM_REF,),
)
GET_LABEL = RecordSpec(
    operation_id="synthetic/get-label",
    method=METHOD_GET,
    path="/repos/{owner}/{repo}/labels/{name}",
)
LIST_WORKFLOW_RUNS = RecordSpec(
    operation_id="synthetic/list-workflow-runs",
    method=METHOD_GET,
    path="/repos/{owner}/{repo}/actions/runs",
    query_params=(PARAM_STATUS, PARAM_PER_PAGE, PARAM_PAGE),
    paging=PAGING_LINK,
    item_key=FIELD_WORKFLOW_RUNS,
)
SYNTHETIC_RECORDS = (UPDATE_ISSUE, GET_CONTENT, GET_REF, GET_LABEL, LIST_WORKFLOW_RUNS)


def synthetic_family_source() -> str:
    """The synthetic family module: ``FAMILY``, ``OPERATIONS`` and ``PENDING``, as D2's family contract has them."""
    records = "".join(record.source() for record in SYNTHETIC_RECORDS)
    return (
        '"""A synthetic operation family: the only module github_api.families holds during a registry test."""\n'
        "\n"
        "from github_api.registry import Paging, RestOperation\n"
        "from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT\n"
        "\n"
        f"FAMILY = {SYNTHETIC_FAMILY!r}\n"
        f"OPERATIONS = (\n{records})\n"
        f"PENDING = frozenset({[SYNTHETIC_PENDING]!r})\n"
    )


def load_families_package() -> ModuleType:
    """``github_api.families`` from the ``scripts`` directory beside this suite; while its ``__init__.py`` is not
    written, the calling test fails on this assertion."""
    assert FAMILIES_INIT.is_file(), f"{FAMILIES_PACKAGE} is not written: {FAMILIES_INIT} does not exist"
    package = importlib.import_module(name=FAMILIES_PACKAGE)
    loaded_from = Path(str(package.__file__)).resolve()
    assert loaded_from == FAMILIES_INIT.resolve(), f"{FAMILIES_PACKAGE} was imported from {loaded_from}"
    return package


def install_synthetic_family(*, directory: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the synthetic family the one module under ``github_api.families`` for this test: its source written to
    ``directory`` and the package's ``__path__``, which discovery walks and imports from, pointed there."""
    families = load_families_package()
    (directory / f"{SYNTHETIC_FAMILY}.py").write_text(data=synthetic_family_source(), encoding="utf-8")
    sys.modules.pop(SYNTHETIC_MODULE, None)
    importlib.invalidate_caches()
    monkeypatch.setattr(target=families, name="__path__", value=[str(directory)])


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    host = fx.FakeGitHub()
    host.install(monkeypatch=monkeypatch)
    yield host
    host.assert_every_request_routed()


@pytest.fixture
def family_directory(tmp_path: Path) -> Iterator[Path]:
    """A directory for the synthetic family module; the module is forgotten afterwards, so no later test (and no
    later case of a parametrized one) reuses the copy imported from another test's directory."""
    yield tmp_path
    sys.modules.pop(SYNTHETIC_MODULE, None)
    package = sys.modules.get(FAMILIES_PACKAGE)
    if package is not None and hasattr(package, SYNTHETIC_FAMILY):
        delattr(package, SYNTHETIC_FAMILY)


# ---------------------------------------------------------------------------------------------------------------------
# AC-1.1 — call and pages refuse a query or body name the record does not document, before any request
# ---------------------------------------------------------------------------------------------------------------------

ENTRY_CALL = "call"
ENTRY_PAGES = "pages"
OWNER_REPO = {PARAM_OWNER: "o", PARAM_REPO: "r"}
WORKFLOW_RUNS = [{FIELD_ID: run_id} for run_id in (101, 102, 103)]


@dataclass(frozen=True)
class Documented:
    """A documented use of a synthetic record: the entry point (``call`` or ``pages``), its arguments, the path it is
    sent to, and the host's answer (for ``pages``, the list's items, served two to a page)."""

    entry: str
    record: RecordSpec
    path_params: Dict[str, Any]
    sent_path: str
    answer: Any
    query: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None


UPDATE_ISSUE_CALL = Documented(
    entry=ENTRY_CALL,
    record=UPDATE_ISSUE,
    path_params={**OWNER_REPO, PARAM_ISSUE_NUMBER: 7},
    sent_path="/repos/o/r/issues/7",
    body={PARAM_TITLE: "Renamed", PARAM_STATE: "closed"},
    answer={FIELD_NUMBER: 7, FIELD_TITLE: "Renamed", FIELD_STATE: "closed"},
)
GET_CONTENT_CALL = Documented(
    entry=ENTRY_CALL,
    record=GET_CONTENT,
    path_params={**OWNER_REPO, PARAM_PATH: "docs/guide.md"},
    sent_path="/repos/o/r/contents/docs/guide.md",
    query={PARAM_REF: "main"},
    answer={FIELD_NAME: "guide.md", FIELD_PATH: "docs/guide.md"},
)
LIST_WORKFLOW_RUNS_PAGES = Documented(
    entry=ENTRY_PAGES,
    record=LIST_WORKFLOW_RUNS,
    path_params=dict(OWNER_REPO),
    sent_path="/repos/o/r/actions/runs",
    query={PARAM_STATUS: "completed", PARAM_PER_PAGE: 2},
    answer=WORKFLOW_RUNS,
)


@dataclass(frozen=True)
class Refusal:
    """A use of ``documented``'s record with a query or body name the record does not document."""

    name: str
    documented: Documented
    query: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None


REFUSALS = (
    Refusal(
        name="undocumented-body-name",
        documented=UPDATE_ISSUE_CALL,
        body={PARAM_TITLE: "Renamed", UNDOCUMENTED_BODY_NAME: "v2"},
    ),
    Refusal(name="body-name-sent-as-query", documented=UPDATE_ISSUE_CALL, query={PARAM_STATE: "closed"}),
    Refusal(name="path-name-sent-as-query", documented=UPDATE_ISSUE_CALL, query={PARAM_ISSUE_NUMBER: 7}),
    Refusal(
        name="undocumented-query-name",
        documented=GET_CONTENT_CALL,
        query={PARAM_REF: "main", UNDOCUMENTED_QUERY_NAME: "raw"},
    ),
    Refusal(name="query-name-sent-as-body", documented=GET_CONTENT_CALL, body={PARAM_REF: "main"}),
    Refusal(
        name="undocumented-query-name-of-a-list",
        documented=LIST_WORKFLOW_RUNS_PAGES,
        query={PARAM_STATUS: "completed", UNDOCUMENTED_LIST_QUERY_NAME: "asc"},
    ),
)


def _invoke(
    *,
    api: Api,
    transport: Any,
    documented: Documented,
    query: Optional[Dict[str, Any]],
    body: Optional[Dict[str, Any]],
) -> Any:
    """``documented``'s entry point on its record and path parameters with ``query`` and ``body`` (``pages`` takes
    no body); a list is read to its end, so a refusal raised lazily is raised here too."""
    operation_id = documented.record.operation_id
    if documented.entry == ENTRY_PAGES:
        listed = api.registry.pages(
            transport=transport, operation_id=operation_id, path_params=documented.path_params, query=query
        )
        return list(listed)
    return api.registry.call(
        transport=transport, operation_id=operation_id, path_params=documented.path_params, query=query, body=body
    )


def _route(*, fake: Any, documented: Documented) -> None:
    """Answer ``documented``'s request: a list route of its items, or a static route of its answer."""
    if documented.entry == ENTRY_PAGES:
        fixed = {name: value for name, value in (documented.query or {}).items() if name not in fx.PAGING_PARAMETERS}
        fake.list_route(
            url=documented.sent_path, items=documented.answer, query=fixed, item_key=documented.record.item_key
        )
        return
    fake.route(
        method=documented.record.method,
        url=documented.sent_path,
        query=documented.query,
        replies=[fx.Reply(body=documented.answer)],
    )


def _assert_sent(*, requests: List[Any], documented: Documented) -> None:
    """The documented use reached the host as declared: its method, its expanded path, its query and its body."""
    if documented.entry == ENTRY_PAGES:
        assert len(requests) == 2, "three items two to a page: the first URL and one rel=next target"
        assert [(request.method, request.path) for request in requests] == [(METHOD_GET, documented.sent_path)] * 2
        return
    (request,) = requests
    assert request.method == documented.record.method
    assert request.path == documented.sent_path
    assert request.query == fx.query_of(values=documented.query)
    assert request.json() == documented.body


@pytest.mark.parametrize("case", REFUSALS, ids=lambda case: case.name)
def test_call_refuses_an_undocumented_parameter(
    case: Refusal, fake: Any, family_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = load_api()
    install_synthetic_family(directory=family_directory, monkeypatch=monkeypatch)
    transport = api.transport.Transport(token=TOKEN)
    documented = case.documented

    with pytest.raises(ValueError):
        _invoke(api=api, transport=transport, documented=documented, query=case.query, body=case.body)
    assert fake.requests == [], "a name the record does not document is refused before any request"

    # The same record, with only documented names, is found and sent: the refusal above was the undocumented name's.
    _route(fake=fake, documented=documented)
    answer = _invoke(api=api, transport=transport, documented=documented, query=documented.query, body=documented.body)
    assert answer == documented.answer
    _assert_sent(requests=fake.requests, documented=documented)


# ---------------------------------------------------------------------------------------------------------------------
# AC-1.1 — expand percent-encodes path values and refuses dot segments
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ExpandCase:
    """``record``'s path expanded with ``path_params``: ``expanded`` is the path, or ``None`` when ``expand`` must
    refuse the values with ``GitHubAPIError``."""

    name: str
    record: RecordSpec
    path_params: Dict[str, Any]
    expanded: Optional[str]


EXPAND_CASES = (
    ExpandCase(
        name="single-segment-encodes-slash-and-space",
        record=GET_LABEL,
        path_params={**OWNER_REPO, PARAM_NAME: "needs review/ui"},
        expanded="/repos/o/r/labels/needs%20review%2Fui",
    ),
    ExpandCase(
        name="single-segment-keeps-dots-inside-a-segment",
        record=GET_LABEL,
        path_params={**OWNER_REPO, PARAM_NAME: "v1..v2"},
        expanded="/repos/o/r/labels/v1..v2",
    ),
    ExpandCase(
        name="multi-segment-keeps-slash-and-encodes-space",
        record=GET_REF,
        path_params={**OWNER_REPO, PARAM_REF: "heads/feature/new parser"},
        expanded="/repos/o/r/git/ref/heads/feature/new%20parser",
    ),
    ExpandCase(
        name="multi-segment-keeps-a-dot-prefixed-segment",
        record=GET_CONTENT,
        path_params={**OWNER_REPO, PARAM_PATH: ".github/workflows/ci.yml"},
        expanded="/repos/o/r/contents/.github/workflows/ci.yml",
    ),
    ExpandCase(
        name="single-segment-dot",
        record=GET_LABEL,
        path_params={**OWNER_REPO, PARAM_NAME: "."},
        expanded=None,
    ),
    ExpandCase(
        name="single-segment-dot-dot",
        record=GET_LABEL,
        path_params={**OWNER_REPO, PARAM_NAME: ".."},
        expanded=None,
    ),
    ExpandCase(
        name="owner-dot-dot",
        record=GET_LABEL,
        path_params={PARAM_OWNER: "..", PARAM_REPO: "r", PARAM_NAME: "bug"},
        expanded=None,
    ),
    ExpandCase(
        name="multi-segment-dot-dot",
        record=GET_REF,
        path_params={**OWNER_REPO, PARAM_REF: ".."},
        expanded=None,
    ),
    ExpandCase(
        name="multi-segment-with-a-dot-dot-segment",
        record=GET_REF,
        path_params={**OWNER_REPO, PARAM_REF: "heads/../../pulls"},
        expanded=None,
    ),
    ExpandCase(
        name="multi-segment-with-a-dot-segment",
        record=GET_CONTENT,
        path_params={**OWNER_REPO, PARAM_PATH: "docs/./guide.md"},
        expanded=None,
    ),
    ExpandCase(
        name="multi-segment-ending-in-dot-dot",
        record=GET_CONTENT,
        path_params={**OWNER_REPO, PARAM_PATH: "docs/guide/.."},
        expanded=None,
    ),
)


@pytest.mark.parametrize("case", EXPAND_CASES, ids=lambda case: case.name)
def test_expand_encodes_and_refuses_dot_segments(case: ExpandCase) -> None:
    api = load_api()
    operation = case.record.build(api=api)

    if case.expanded is None:
        with pytest.raises(api.errors.GitHubAPIError):
            api.registry.expand(operation=operation, path_params=case.path_params)
    else:
        assert api.registry.expand(operation=operation, path_params=case.path_params) == case.expanded
