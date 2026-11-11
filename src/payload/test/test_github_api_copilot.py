"""Tests of the ``copilot`` records of the GitHub wrapper (``github_api/families/copilot.py``; issue #33 AC-2 to AC-4,
the slice test module of #28 design D8; issue #14 AC-1, AC-2, AC-4 and UB-3).

Installed from ``src/payload/test/test_github_api_copilot.py`` to ``test/test_github_api_copilot.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every operation ID, path template, item key and body name
below is transcribed from ``docs/api-reference/github/operations-index.md``, ``rest/copilot.md`` and ``conventions.md``
"Lists wrapped in an object", never read from the records:

- ``PAGED_SECTIONS``: the sections with a ``Paging:`` line, each with its path template, a value for each path
  parameter but ``owner`` and ``repo``, and its item key: "items in ``repositories``" and "items in ``seats``", as
  "Lists wrapped in an object" names them; both document ``per_page``;
- ``UNPAGED_IDS``: the other sections, without a ``Paging:`` line, the content-exclusion write among them (issue #14
  AC-1). No ``copilot`` record writes a branch or creates issues, so the module has no AC-6 test. ``PENDING`` is
  empty (issue #14 AC-2).

``test_a_paged_record_prints_every_page`` runs one golden case per paged section with
``github_wrapper_fixtures.run_product_case`` (loaded by path, as ``test_github_api_call.py`` loads it): ``call <id>``
with ``--path org=...`` and ``--query per_page=1``, against a fake host serving two items, one per page. The three
content-exclusion ``call`` tests run ``call copilot/set-copilot-content-exclusion-for-organization`` the same way: its
section's only body row is ``*`` ("any key"), so every ``-F`` member given is sent as given (issue #14 AC-4), while an
undocumented ``--query`` or ``--path`` name is still refused before any request, in a log record judged by
``fx.assert_log`` on ``caplog.records`` (issue #14 UB-3). ``registry.send`` refuses that record's undocumented query
name too, with ``ValueError``, before a ``Transport`` on the fake host of ``fx.FakeGitHub`` sends anything (issue #14
UB-3). The structural tests read the family module imported from the ``scripts`` directory beside this suite. No test
opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_copilot.py`` (no network).
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
FAMILY = "copilot"
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

FIELD_ID = fx.FIELD_ID
FIELD_NAME = fx.FIELD_NAME
#: The two items every paged case's host serves, cut to two fields.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {FIELD_ID: 1, FIELD_NAME: "wrapper"},
    {FIELD_ID: 2, FIELD_NAME: "transport"},
)

# The path parameter value the cases give (``owner`` and ``repo`` default to the fixture's ``origin``, ``o/r``).
PARAM_ORG = "org"
ORG = "acme"
ON_ORG = ((PARAM_ORG, ORG),)

# Issue #14 AC-4 and UB-3: ``rest/copilot.md`` "Set Copilot content exclusion rules for an organization", ``PUT
# /orgs/{org}/copilot/content_exclusion``, whose body rows are ``*`` ("any key", an array of string or object),
# ``*[]{variant 2}.ifAnyMatch`` and ``*[]{variant 3}.ifNoneMatch``; it documents no query row.
ISSUE_14_AC_4 = "issue-14-AC-4"
ISSUE_14_UB_3 = "issue-14-UB-3"
CONTENT_EXCLUSION_ID = "copilot/set-copilot-content-exclusion-for-organization"
CONTENT_EXCLUSION_PATH = "/orgs/acme/copilot/content_exclusion"
OPTION_FIELD_SHORT = "-F"
#: The two repositories of the map: the official page's example ``{"octo-repo": ["/src/some-dir/kernel.rs"]}``, a
#: string array, and a second one whose array holds an ``ifAnyMatch`` object (variant 2).
REPOSITORY_OF_PATHS = "octo-repo"
REPOSITORY_OF_PATTERNS = "octo-docs"
FIELD_IF_ANY_MATCH = "ifAnyMatch"
MEMBER_OF_PATHS = 'octo-repo=["/src/some-dir/kernel.rs"]'
MEMBER_OF_PATTERNS = 'octo-docs=[{"ifAnyMatch": ["/drafts/**", "*.secret"]}]'
#: The JSON body the two members make, exactly.
EXCLUSION_MAP: Dict[str, Any] = {
    REPOSITORY_OF_PATHS: ["/src/some-dir/kernel.rs"],
    REPOSITORY_OF_PATTERNS: [{FIELD_IF_ANY_MATCH: ["/drafts/**", "*.secret"]}],
}
#: The fake host's ``200`` answer: a JSON object, as the section's ``200: application/json object`` reads.
EXCLUSION_SET = {fx.FIELD_MESSAGE: "Content exclusion rules updated"}
#: A query name the section does not document, and the kind a refusal names it with (``commands/call.py``
#: ``check_call``: ``documents no query parameter ["sort"]``).
UNDOCUMENTED_QUERY_NAME = "sort"
KIND_QUERY = "query"
#: A path name the section does not document (its path names ``org`` alone), and the kind a refusal names it with
#: (``check_call``: ``documents no path parameter ["enterprise"]``).
UNDOCUMENTED_PATH_NAME = "enterprise"
KIND_PATH = "path"
#: The body ``registry.send`` is given beside the undocumented query name: the official page's example, one member.
EXAMPLE_MAP: Dict[str, Any] = {REPOSITORY_OF_PATHS: ["/src/some-dir/kernel.rs"]}
#: The token the ``registry.send`` case's ``Transport`` carries to the fake host.
TOKEN = "copilot-test-token"  # pragma: allowlist secret
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""


@dataclass(frozen=True)
class PagedSection:
    """A section of ``rest/copilot.md`` with a ``Paging:`` line: its operation ID, its path template, a value for each
    path parameter but ``owner`` and ``repo`` (name, value), and the item key ``conventions.md`` "Lists wrapped in an
    object" names for it (``None``: the response body is the array)."""

    operation_id: str
    path: str
    path_values: Tuple[Tuple[str, str], ...] = ()
    item_key: Optional[str] = None


PAGED_SECTIONS: Tuple[PagedSection, ...] = (
    PagedSection(
        operation_id="copilot/list-copilot-coding-agent-selected-repositories-for-organization",
        path="/orgs/{org}/copilot/coding-agent/permissions/repositories",
        path_values=ON_ORG,
        item_key="repositories",
    ),
    PagedSection(
        operation_id="copilot/list-copilot-seats",
        path="/orgs/{org}/copilot/billing/seats",
        path_values=ON_ORG,
        item_key="seats",
    ),
)

#: The sections of ``rest/copilot.md`` without a ``Paging:`` line.
UNPAGED_IDS: FrozenSet[str] = frozenset(
    {
        "copilot/add-copilot-seats-for-teams",
        "copilot/add-copilot-seats-for-users",
        "copilot/add-organizations-to-enterprise-coding-agent-policy",
        "copilot/cancel-copilot-seat-assignment-for-teams",
        "copilot/cancel-copilot-seat-assignment-for-users",
        "copilot/copilot-content-exclusion-for-organization",
        "copilot/copilot-enterprise-one-day-usage-metrics",
        "copilot/copilot-enterprise-repos-one-day-report",
        "copilot/copilot-enterprise-usage-metrics",
        "copilot/copilot-enterprise-user-teams-one-day-report",
        "copilot/copilot-organization-one-day-usage-metrics",
        "copilot/copilot-organization-repos-one-day-report",
        "copilot/copilot-organization-usage-metrics",
        "copilot/copilot-organization-user-teams-one-day-report",
        "copilot/copilot-organization-users-one-day-usage-metrics",
        "copilot/copilot-organization-users-usage-metrics",
        "copilot/copilot-users-one-day-usage-metrics",
        "copilot/copilot-users-usage-metrics",
        "copilot/delete-copilot-team-customizations",
        "copilot/disable-copilot-coding-agent-for-repository-in-organization",
        "copilot/enable-copilot-coding-agent-for-repository-in-organization",
        "copilot/get-copilot-cloud-agent-configuration",
        "copilot/get-copilot-coding-agent-permissions-organization",
        "copilot/get-copilot-organization-details",
        "copilot/get-copilot-seat-details-for-user",
        "copilot/get-copilot-team-customizations",
        "copilot/get-enterprise-code-review-policy",
        "copilot/get-organization-code-review-policy",
        "copilot/get-organization-code-review-runner",
        "copilot/get-organization-code-review-settings",
        "copilot/get-repository-code-review-settings",
        "copilot/remove-organizations-from-enterprise-coding-agent-policy",
        "copilot/set-copilot-coding-agent-permissions-organization",
        "copilot/set-copilot-coding-agent-selected-repositories-for-organization",
        "copilot/set-copilot-content-exclusion-for-organization",
        "copilot/set-copilot-team-customizations",
        "copilot/set-enterprise-code-review-policy",
        "copilot/set-enterprise-coding-agent-policy",
        "copilot/set-organization-code-review-policy",
        "copilot/set-organization-code-review-runner",
        "copilot/update-organization-code-review-settings",
        "copilot/update-repository-code-review-settings",
    }
)

PAGED_IDS: FrozenSet[str] = frozenset(section.operation_id for section in PAGED_SECTIONS)
#: AC-1, AC-2: the IDs ``OPERATIONS`` holds a record of, each once: every section of the family (issue #14 AC-1).
RECORDED_IDS: FrozenSet[str] = PAGED_IDS | UNPAGED_IDS
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
    """``github_api.families.copilot``, imported from the ``scripts`` directory beside this suite."""
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


def named(*, name: str) -> str:
    """A pattern for ``name`` as a refusal renders a name: with ``json.dumps`` (#28 design D4)."""
    return re.escape(json.dumps(obj=name))


def named_with_kind(*, kind: str, name: str) -> str:
    """A pattern for the undocumented ``name`` in the list that follows ``<kind> parameter`` (or ``parameters``), as
    ``commands/call.py`` ``check_call`` writes one (``documents no query parameter ["sort"]``); a name in another
    kind's list, or in a list of documented names, does not match."""
    return rf'\b{kind} parameters?[^"\[\]\n;]*\[?(?:"[^"]*",\s*)*{named(name=name)}'


def test_nothing_is_pending() -> None:
    """Issue #14 AC-2: ``copilot.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == frozenset(), f"{FAMILY_MODULE}.PENDING holds {sorted(pending)}; nothing is to stay pending"


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections, one each; the ``Paging.LINK`` ones are exactly the sections with a
    ``Paging:`` line (the paged cases' IDs); and every record has no ``multi_segment`` name, its section's item key
    (none for an operation that does not page), ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(RECORDED_IDS), (
        f"{FAMILY_MODULE} declares {declared}, its sections are {sorted(RECORDED_IDS)}"
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
    host serves, one per page, as ``printed_json`` of the two; every request was routed, one per page."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    urls = [request.url for request in requests]
    assert len(requests) == len(LISTED_ITEMS), f"{case.name}: one request per page expected, sent {urls}"


def test_the_content_exclusion_map_is_sent_as_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #14 AC-4: ``call copilot/set-copilot-content-exclusion-for-organization --path org=acme`` with one ``-F``
    member per repository, a string array and an array holding an ``ifAnyMatch`` object, exits 0, prints the answer,
    and sends one ``PUT /orgs/acme/copilot/content_exclusion`` whose JSON body is exactly those two members."""
    case = fx.GoldenCase(
        name=f"{ISSUE_14_AC_4}/exit-0/{CONTENT_EXCLUSION_ID}",
        argv=(
            CALL,
            CONTENT_EXCLUSION_ID,
            OPTION_PATH,
            f"{PARAM_ORG}={ORG}",
            OPTION_FIELD_SHORT,
            MEMBER_OF_PATHS,
            OPTION_FIELD_SHORT,
            MEMBER_OF_PATTERNS,
        ),
        stdout=fx.printed_json(value=EXCLUSION_SET),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.StaticRouteSpec(
                method=fx.METHOD_PUT, url=CONTENT_EXCLUSION_PATH, replies=(fx.Reply(body=EXCLUSION_SET),)
            ),
        ),
        writes=(fx.NonGetRequest(method=fx.METHOD_PUT, path=CONTENT_EXCLUSION_PATH, body=EXCLUSION_MAP),),
    )

    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    sent = [f"{request.method} {request.url}" for request in requests]
    assert len(requests) == 1, f"{case.name}: one request expected, sent {sent}"


def test_the_content_exclusion_call_checks_its_query(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #14 UB-3: the record takes any body name, yet ``call`` still refuses an undocumented ``--query`` name: with
    ``--path org=acme``, one ``-F`` member and ``--query sort=name`` it exits 2 with nothing on standard output and no
    request, and a log record names the record's ID and ``sort`` as a query parameter."""
    case = fx.GoldenCase(
        name=f"{ISSUE_14_UB_3}/exit-2/{CONTENT_EXCLUSION_ID}",
        argv=(
            CALL,
            CONTENT_EXCLUSION_ID,
            OPTION_PATH,
            f"{PARAM_ORG}={ORG}",
            OPTION_FIELD_SHORT,
            MEMBER_OF_PATHS,
            OPTION_QUERY,
            f"{UNDOCUMENTED_QUERY_NAME}=name",
        ),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(
                named(name=CONTENT_EXCLUSION_ID),
                named_with_kind(kind=KIND_QUERY, name=UNDOCUMENTED_QUERY_NAME),
            ),
            withheld=(),
        ),
    )
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)


def test_the_content_exclusion_call_checks_its_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #14 UB-3: the record takes any body name, yet ``call`` still refuses an undocumented ``--path`` name: with
    ``--path org=acme``, ``--path enterprise=acme-corp`` and one ``-F`` member it exits 2 with nothing on standard
    output and no request, and a log record names the record's ID and ``enterprise`` as a path parameter."""
    case = fx.GoldenCase(
        name=f"{ISSUE_14_UB_3}/exit-2/undocumented-path/{CONTENT_EXCLUSION_ID}",
        argv=(
            CALL,
            CONTENT_EXCLUSION_ID,
            OPTION_PATH,
            f"{PARAM_ORG}={ORG}",
            OPTION_PATH,
            f"{UNDOCUMENTED_PATH_NAME}=acme-corp",
            OPTION_FIELD_SHORT,
            MEMBER_OF_PATHS,
        ),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(
                named(name=CONTENT_EXCLUSION_ID),
                named_with_kind(kind=KIND_PATH, name=UNDOCUMENTED_PATH_NAME),
            ),
            withheld=(),
        ),
    )
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)


def test_the_registry_refuses_the_content_exclusion_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #14 UB-3: ``registry.send`` of ``copilot/set-copilot-content-exclusion-for-organization``, whose body
    takes any key, with ``org=acme``, one documented body member and the undocumented query name ``sort`` raises
    ``ValueError`` naming ``sort`` as a query parameter, and its ``Transport`` sends the fake host nothing."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    host = fx.FakeGitHub()
    host.install(monkeypatch=monkeypatch)
    sender = transport.Transport(token=TOKEN)

    with pytest.raises(ValueError) as raised:
        registry.send(
            transport=sender,
            operation_id=CONTENT_EXCLUSION_ID,
            path_params={PARAM_ORG: ORG},
            query={UNDOCUMENTED_QUERY_NAME: "name"},
            body=EXAMPLE_MAP,
        )

    message = str(raised.value)
    assert re.search(pattern=named_with_kind(kind=KIND_QUERY, name=UNDOCUMENTED_QUERY_NAME), string=message), (
        f"the refusal does not name {UNDOCUMENTED_QUERY_NAME!r} as a query parameter: {message}"
    )
    sent = [f"{request.method} {request.url}" for request in host.requests]
    assert sent == [], f"an undocumented query name is refused before any request; sent {sent}"
