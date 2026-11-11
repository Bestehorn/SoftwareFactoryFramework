"""Tests of the GitHub wrapper's GraphQL call, ``call graphql/<member>`` (``github_api/graphql_only.py``,
``github_api/commands/call.py``, ``registry.graphql_call``; issue #30 design D3, D5, D6; AC-2.1 to AC-2.6, AC-3.1 to
AC-3.3).

Installed from ``src/payload/test/test_github_api_graphql_only.py`` to ``test/test_github_api_graphql_only.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every call here is a golden case whose argv is
``call graphql/…``. ``github_wrapper_fixtures.run_product_case`` (loaded by path) runs it through the product entry
script's ``main(argv=...)`` in the fixture project (``origin`` ``o/r``) against the fake GitHub host, where a
``StaticRouteSpec`` answers ``POST /graphql`` with its replies in turn, and judges its exit code, its standard output
exactly, every ``POST`` as ``GoldenCase.writes`` holds it (method, path, and the JSON body's ``query`` and
``variables``), no request at all for a refusal, and that every request was routed. A log record is judged by
``fx.assert_log`` on ``caplog.records``; a name the caller gave is matched as ``json.dumps`` renders it.

- ``test_every_record_is_called_through_main`` (AC-2.1 to AC-2.3, AC-2.6) iterates ``graphql_only.OPERATIONS``, so a
  later record is proven without editing this file, and calls every record whose ID is not in ``REFUSED_MUTATIONS``
  with D6's argv: ``-F input=<MUTATION_INPUT>`` for ``input`` and ``-f <name>=v-<name>`` for any other declared
  variable. A record without a ``connection`` is answered with a ``data`` object, which prints; a record with one with
  two pages nested at its ``connection``, the first naming ``FIRST_CURSOR``, whose nodes print as one array.
- ``test_a_variable_holds_the_given_json_value`` (AC-2.1) also compares the posted ``variables`` with
  ``json.dumps(sort_keys=True)``, so ``true`` is not ``1``.
- ``test_a_graphql_failure_exits_1_with_its_details`` (AC-2.4) patches ``FakeGitHub.answer`` for its no-response
  case, which records the request and raises ``urllib.error.URLError``.
- ``test_an_undeclared_variable_is_refused`` (AC-2.5) and ``test_a_refused_mutation_sends_nothing`` (AC-3.1 to AC-3.3)
  are answered by the same route, so only the refusal keeps a request from being sent and answered.

The expected request of a call is built from the document of the record that declares its ID (``declared_document``);
while no single record declares it, ``call`` refuses the ID with exit 2, which is ``run_product_case``'s first check.
The fork has no ``call``, so ``CASES`` holds none of these rows and the fork parity test never runs them. No test opens
a connection.

Run: ``python scripts/run_tests.py test/test_github_api_graphql_only.py`` (no network).
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, NoReturn, Optional, Sequence, Tuple

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
GRAPHQL_ONLY = "graphql_only"

# The criteria; every case's name starts with its criterion, then ``/``.
AC_2_1 = "AC-2.1"
AC_2_2 = "AC-2.2"
AC_2_4 = "AC-2.4"
AC_2_5 = "AC-2.5"
AC_2_6 = "AC-2.6"
AC_3_1 = "AC-3.1"

CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD_SHORT = "-f"
OPTION_FIELD_SHORT = "-F"
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value from it, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

#: The operation ID prefix of a GraphQL record (design D2).
GRAPHQL_ID_PREFIX = "graphql/"
GRAPHQL_PATH = "/graphql"
OP_PIN_ISSUE = "graphql/pinIssue"
OP_DISCUSSIONS = "graphql/Repository.discussions"
OP_MERGE_QUEUE = "graphql/Repository.mergeQueue"
OP_ENABLE_AUTO_MERGE = "graphql/enablePullRequestAutoMerge"
OP_CREATE_COMMIT_ON_BRANCH = "graphql/createCommitOnBranch"
OP_REVERT_PULL_REQUEST = "graphql/revertPullRequest"
OP_TRANSFER_ISSUE = "graphql/transferIssue"
#: AC-3.1's mutations: each commits to or creates a branch, sets a pull request to merge, or moves an issue into
#: another repository, so ``call`` refuses it before any request (design D5).
REFUSED_MUTATIONS: Tuple[str, ...] = (
    OP_ENABLE_AUTO_MERGE,
    OP_CREATE_COMMIT_ON_BRANCH,
    OP_REVERT_PULL_REQUEST,
    OP_TRANSFER_ISSUE,
)
#: AC-3.2: the refused mutation whose refusal names the subcommand to use, which never sends it; the refusal of every
#: other one states that no subcommand sends it.
SUBCOMMAND_OF_REFUSED: Mapping[str, str] = {OP_ENABLE_AUTO_MERGE: "merge-pr"}
#: The end of a refusal whose subcommand sends the refused record itself (issue #32 DL-007); ``merge-pr`` never sends
#: ``graphql/enablePullRequestAutoMerge``, so its refusal must not hold it.
SENDS_IT = "which sends it"
NO_SUBCOMMAND_SENDS_IT = "no subcommand sends it"

# The JSON body ``Transport.graphql`` posts and the response members it reads (``graphql/conventions.md``).
FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"
FIELD_TYPE = "type"
FIELD_PATH = "path"
FIELD_CLIENT_MUTATION_ID = "clientMutationId"
FIELD_PIN_ISSUE = "pinIssue"
FIELD_ISSUE = "issue"
FIELD_ISSUE_ID = "issueId"
FIELD_POSITION = "position"
FIELD_STATE = "state"
FIELD_PULL_REQUEST = "pullRequest"
FIELD_REPOSITORY = "repository"
FIELD_MERGE_QUEUE = "mergeQueue"
FIELD_ENTRIES = "entries"
#: The member every ``data`` answer of D6's calls holds; the wrapper prints ``data`` whatever its members.
FIELD_ANSWER = "answer"

# D6's argv: a mutation's one variable, ``input``, is a JSON object; any other variable is ``v-<name>`` as text.
VARIABLE_INPUT = "input"
VARIABLE_OWNER = "owner"
VARIABLE_NAME = "name"
VARIABLE_BRANCH = "branch"
MUTATION_INPUT: Mapping[str, Any] = {FIELD_CLIENT_MUTATION_ID: "k"}
TEXT_VALUE_PREFIX = "v-"
FIRST_CURSOR = "c1"
LAST_CURSOR = "c2"
FIRST_NODE = 1
SECOND_NODE = 2

ISSUE_NODE_ID = "I_1"
PIN_INPUT: Mapping[str, Any] = {FIELD_ISSUE_ID: ISSUE_NODE_ID}
PIN_DATA: Mapping[str, Any] = {
    FIELD_PIN_ISSUE: {FIELD_CLIENT_MUTATION_ID: None, FIELD_ISSUE: {fx.FIELD_ID: ISSUE_NODE_ID}},
}
#: AC-2.5's names no record documents: a variable ``pinIssue``'s document does not define, a path and a query name.
UNDECLARED_VARIABLE = "issue"
UNDECLARED_PATH_NAME = "issue_number"
UNDECLARED_QUERY_NAME = "state"

#: ``Repository.mergeQueue``'s connection (design D1) and two entries, one to a page.
MERGE_QUEUE_CONNECTION = (FIELD_REPOSITORY, FIELD_MERGE_QUEUE, FIELD_ENTRIES)
MERGE_QUEUE_VARIABLES: Mapping[str, Any] = {
    VARIABLE_OWNER: fx.OWNER,
    VARIABLE_NAME: fx.REPOSITORY,
    VARIABLE_BRANCH: fx.BRANCH_MAIN,
}
MERGE_QUEUE_ARGUMENTS: Tuple[str, ...] = tuple(
    argument for name, text in MERGE_QUEUE_VARIABLES.items() for argument in (OPTION_RAW_FIELD_SHORT, f"{name}={text}")
)
MERGE_QUEUE_ENTRIES: Tuple[Mapping[str, Any], ...] = (
    {
        fx.FIELD_ID: "MQE_1",
        FIELD_POSITION: 1,
        FIELD_STATE: "QUEUED",
        FIELD_PULL_REQUEST: {fx.FIELD_ID: "PR_77", fx.FIELD_NUMBER: 77},
    },
    {
        fx.FIELD_ID: "MQE_2",
        FIELD_POSITION: 2,
        FIELD_STATE: "AWAITING_CHECKS",
        FIELD_PULL_REQUEST: {fx.FIELD_ID: "PR_78", fx.FIELD_NUMBER: 78},
    },
)

# AC-2.4: GitHub's answers that the transport raises ``GitHubAPIError`` for.
GRAPHQL_ERROR_TEXT = "Could not resolve to a node with the global id of I_404"
GRAPHQL_ERRORS: Tuple[Mapping[str, Any], ...] = (
    {FIELD_TYPE: "NOT_FOUND", FIELD_PATH: [FIELD_PIN_ISSUE], fx.FIELD_MESSAGE: GRAPHQL_ERROR_TEXT},
)
BAD_GATEWAY = fx.error_reply(status=502, message="Server Error")
RATE_LIMITED_MESSAGE = "You have exceeded a secondary rate limit"
HEADER_RETRY_AFTER = "retry-after"
RATE_LIMITED = fx.Reply(
    status=403,
    body={fx.FIELD_MESSAGE: RATE_LIMITED_MESSAGE, fx.FIELD_DOCUMENTATION_URL: fx.DOCUMENTATION_URL},
    headers={HEADER_RETRY_AFTER: "0"},  # no wait between the retries, and every answer is the same limit
)
NO_RESPONSE_REASON = "the fake host closed the connection without a response"
DETAILS_PREFIX = "Details: "


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def named(*, name: str) -> str:
    """A pattern for ``name`` as a refusal renders a name: with ``json.dumps``."""
    return re.escape(pattern=json.dumps(obj=name))


def lacking(*, text: str) -> str:
    """A pattern that matches only a message holding no ``text`` anywhere in it."""
    return rf"\A(?![\s\S]*{re.escape(pattern=text)})"


def raw_field(*, name: str, text: str) -> Tuple[str, str]:
    """``-f NAME=TEXT``: the variable ``name`` as the string ``text``."""
    return (OPTION_RAW_FIELD_SHORT, f"{name}={text}")


def json_field(*, name: str, value: Any) -> Tuple[str, str]:
    """``-F NAME=JSON``: the variable ``name`` as the JSON value ``value``."""
    return (OPTION_FIELD_SHORT, f"{name}={json.dumps(obj=value)}")


def graphql_route(*, replies: Sequence[Any]) -> Any:
    """The fake host's ``POST /graphql``, answered with ``replies`` in turn, the last repeated."""
    return fx.StaticRouteSpec(method=fx.METHOD_POST, url=GRAPHQL_PATH, replies=tuple(replies))


def data_reply(*, data: Any) -> Any:
    """A GraphQL response whose ``data`` is ``data``."""
    return fx.Reply(body={FIELD_DATA: data})


def connection_reply(*, connection: Sequence[str], nodes: Sequence[Any], end_cursor: str, has_next: bool) -> Any:
    """A GraphQL response holding one page of ``nodes`` at the key path ``connection`` under ``data``."""
    page: Any = {
        FIELD_NODES: list(nodes),
        FIELD_PAGE_INFO: {FIELD_HAS_NEXT_PAGE: has_next, FIELD_END_CURSOR: end_cursor},
    }
    for key in reversed(connection):
        page = {key: page}
    return data_reply(data=page)


def two_pages(*, connection: Sequence[str], first: Any, second: Any) -> Tuple[Any, Any]:
    """The pages of a connection holding ``first`` and then ``second``: the first names ``FIRST_CURSOR`` as its
    ``endCursor`` with ``hasNextPage`` ``true``, the second is the last."""
    return (
        connection_reply(connection=connection, nodes=(first,), end_cursor=FIRST_CURSOR, has_next=True),
        connection_reply(connection=connection, nodes=(second,), end_cursor=LAST_CURSOR, has_next=False),
    )


def posted(*, document: Optional[str], variables: Mapping[str, Any]) -> Any:
    """The ``POST`` to ``/graphql`` whose JSON body's ``query`` is ``document`` and whose ``variables`` are
    ``variables``, as ``Transport.graphql`` sends it."""
    return fx.NonGetRequest(
        method=fx.METHOD_POST,
        path=GRAPHQL_PATH,
        body={FIELD_QUERY: document, FIELD_VARIABLES: dict(variables)},
    )


def paged_posts(*, document: Optional[str], variables: Mapping[str, Any], afters: Sequence[Optional[str]]) -> Any:
    """The ``POST`` of each page of a connection, ``after`` set to each of ``afters`` in turn."""
    return tuple(posted(document=document, variables={**variables, FIELD_AFTER: after}) for after in afters)


def declared_document(*, operation_id: str) -> Optional[str]:
    """The document of the one record of ``graphql_only.OPERATIONS`` whose ID is ``operation_id``; ``None`` while no
    single record declares it, when ``call`` refuses the ID with exit 2, which ``run_product_case`` checks first."""
    graphql_only = fx.import_api_module(name=GRAPHQL_ONLY)
    documents = [record.document for record in graphql_only.OPERATIONS if record.operation_id == operation_id]
    return str(documents[0]) if len(documents) == 1 else None


def _refusal(*, criterion: str, slug: str, argv: Tuple[str, ...], patterns: Tuple[str, ...]) -> Any:
    """A refusal: exit 2, nothing on standard output, no request although ``POST /graphql`` would be answered, and
    one log record matching every pattern."""
    return fx.GoldenCase(
        name=f"{criterion}/exit-2/{slug}",
        argv=argv,
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        routes=(graphql_route(replies=(data_reply(data=PIN_DATA),)),),
        log=fx.LogExpectation(refusal=patterns, withheld=()),
    )


def _judge_logged(
    *,
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Run ``case`` with ``fx.run_product_case`` and judge its log records by its ``log`` (``fx.assert_log``)."""
    caplog.set_level(level=logging.DEBUG)
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)
    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.1 to AC-2.3, AC-2.6 — every record called through main
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class GivenVariable:
    """One variable of D6's argv: its ``name``, the option that gives it, the text after ``NAME=``, and the JSON value
    the posted ``variables`` hold for it."""

    name: str
    option: str
    text: str
    value: Any

    def arguments(self) -> Tuple[str, str]:
        """The option and its ``NAME=VALUE``."""
        return (self.option, f"{self.name}={self.text}")


def given_variables(*, names: Sequence[str]) -> Tuple[GivenVariable, ...]:
    """D6's value for each of ``names``: ``input`` as ``MUTATION_INPUT`` with ``-F``, any other name as the text
    ``v-<name>`` with ``-f``."""
    given: List[GivenVariable] = []
    for name in names:
        if name == VARIABLE_INPUT:
            given.append(
                GivenVariable(
                    name=name,
                    option=OPTION_FIELD_SHORT,
                    text=json.dumps(obj=MUTATION_INPUT),
                    value=dict(MUTATION_INPUT),
                )
            )
        else:
            text = f"{TEXT_VALUE_PREFIX}{name}"
            given.append(GivenVariable(name=name, option=OPTION_RAW_FIELD_SHORT, text=text, value=text))
    return tuple(given)


def node_of(*, operation_id: str, number: int) -> Dict[str, Any]:
    """The ``number``-th node a connection of the record ``operation_id`` is answered with."""
    return {fx.FIELD_ID: f"{operation_id}#{number}"}


def record_case(*, record: Any, given: Sequence[GivenVariable]) -> Any:
    """D6's call of ``record`` with ``given``: exit 0, its document posted with the given variables (``after``
    ``null`` and then ``FIRST_CURSOR`` across two pages for a record with a ``connection``), and standard output
    ``print_json``'s form of the answer's ``data``, or of both pages' nodes in order."""
    operation_id = str(record.operation_id)
    variables = {each.name: each.value for each in given}
    argv = (CALL, operation_id, *(argument for each in given for argument in each.arguments()))
    if record.connection:
        first = node_of(operation_id=operation_id, number=FIRST_NODE)
        second = node_of(operation_id=operation_id, number=SECOND_NODE)
        replies: Tuple[Any, ...] = two_pages(connection=record.connection, first=first, second=second)
        writes = paged_posts(document=record.document, variables=variables, afters=(None, FIRST_CURSOR))
        stdout = fx.printed_json(value=[first, second])
    else:
        data = {FIELD_ANSWER: {fx.FIELD_ID: operation_id}}
        replies = (data_reply(data=data),)
        writes = (posted(document=record.document, variables=variables),)
        stdout = fx.printed_json(value=data)
    return fx.GoldenCase(
        name=f"{AC_2_6}/exit-0/{operation_id}",
        argv=argv,
        stdout=stdout,
        exit_code=fx.EXIT_OK,
        routes=(graphql_route(replies=replies),),
        writes=writes,
    )


def test_every_record_is_called_through_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.1 to AC-2.3, AC-2.6: every record of ``graphql_only.OPERATIONS`` whose ID is not in ``REFUSED_MUTATIONS``,
    called through ``main`` with a value for each declared variable, exits 0, posts its document with those variables
    (on each of two pages for a connection, ``after`` ``null`` then ``FIRST_CURSOR``), and prints ``data``, or every
    node of both pages as one array; it fails when it calls no record."""
    registry = fx.import_api_module(name=REGISTRY)
    graphql_only = fx.import_api_module(name=GRAPHQL_ONLY)
    called: List[str] = []
    for index, record in enumerate(graphql_only.OPERATIONS):
        if record.operation_id in REFUSED_MUTATIONS:
            continue
        given = given_variables(names=registry.declared_variables(operation=record))
        case = record_case(record=record, given=given)
        fx.run_product_case(case=case, root=tmp_path / f"record-{index}", monkeypatch=monkeypatch, capsys=capsys)
        called.append(str(record.operation_id))

    assert called, (
        "graphql_only.OPERATIONS holds no record outside REFUSED_MUTATIONS, so no GraphQL call was proven: "
        f"{[record.operation_id for record in graphql_only.OPERATIONS]}"
    )


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.1 — a variable holds the JSON value the caller gave
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class VariableValue:
    """``input`` given as ``text`` with ``option``, and the JSON value the posted ``variables`` must hold for it."""

    slug: str
    option: str
    text: str
    value: Any


VARIABLE_VALUES: Tuple[VariableValue, ...] = (
    VariableValue(slug="text", option=OPTION_RAW_FIELD_SHORT, text="text", value="text"),
    VariableValue(slug="number", option=OPTION_FIELD_SHORT, text="5", value=5),
    VariableValue(slug="boolean", option=OPTION_FIELD_SHORT, text="true", value=True),
    VariableValue(slug="array", option=OPTION_FIELD_SHORT, text='["a"]', value=["a"]),
    VariableValue(slug="object", option=OPTION_FIELD_SHORT, text='{"issueId": "I_1"}', value={FIELD_ISSUE_ID: "I_1"}),
    VariableValue(slug="null", option=OPTION_FIELD_SHORT, text="null", value=None),
)


def variable_value_name(given: VariableValue) -> str:
    """The test id of a ``VARIABLE_VALUES`` row."""
    return given.slug


@pytest.mark.parametrize(argnames="given", argvalues=VARIABLE_VALUES, ids=variable_value_name)
def test_a_variable_holds_the_given_json_value(
    given: VariableValue, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.1: ``call graphql/pinIssue`` with ``-f input=text`` or ``-F input=<JSON>`` sends one ``POST`` to
    ``/graphql`` whose ``query`` is the record's document and whose ``variables`` are ``{"input": <the value>}``, of
    the same JSON kind (compared by ``json.dumps(sort_keys=True)``: ``true`` is not ``1``), and prints ``data``."""
    document = declared_document(operation_id=OP_PIN_ISSUE)
    variables = {VARIABLE_INPUT: given.value}
    case = fx.GoldenCase(
        name=f"{AC_2_1}/exit-0/{given.slug}",
        argv=(CALL, OP_PIN_ISSUE, given.option, f"{VARIABLE_INPUT}={given.text}"),
        stdout=fx.printed_json(value=PIN_DATA),
        exit_code=fx.EXIT_OK,
        routes=(graphql_route(replies=(data_reply(data=PIN_DATA),)),),
        writes=(posted(document=document, variables=variables),),
    )

    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    written = [request for request in requests if request.method == fx.METHOD_POST]
    assert len(written) == 1, f"{case.name}: {len(written)} POST requests"
    body = written[0].json()
    assert body[FIELD_QUERY] == document, f"{case.name}: the posted query is not the record's document"
    sent = json.dumps(obj=body[FIELD_VARIABLES], sort_keys=True)
    assert sent == json.dumps(obj=variables, sort_keys=True), f"{case.name}: the posted variables are {sent}"


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.2 — a connection prints every node of every page
# ---------------------------------------------------------------------------------------------------------------------


def test_a_merge_queue_prints_every_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.2: ``call graphql/Repository.mergeQueue -f owner=o -f name=r -f branch=main`` posts twice, ``after``
    ``null`` then the first page's ``endCursor``, and prints both pages' entries as one JSON array, once the last page
    has arrived; it exits 0."""
    document = declared_document(operation_id=OP_MERGE_QUEUE)
    first, second = MERGE_QUEUE_ENTRIES
    case = fx.GoldenCase(
        name=f"{AC_2_2}/exit-0/merge-queue-entries",
        argv=(CALL, OP_MERGE_QUEUE, *MERGE_QUEUE_ARGUMENTS),
        stdout=fx.printed_json(value=list(MERGE_QUEUE_ENTRIES)),
        exit_code=fx.EXIT_OK,
        routes=(graphql_route(replies=two_pages(connection=MERGE_QUEUE_CONNECTION, first=first, second=second)),),
        writes=paged_posts(document=document, variables=MERGE_QUEUE_VARIABLES, afters=(None, FIRST_CURSOR)),
    )

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.4 — a GraphQL failure exits 1 with its message and details
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FailureCase:
    """An AC-2.4 case: ``call <operation_id>`` with ``arguments``, which give ``variables``, against ``POST /graphql``
    answered with ``replies`` in turn (or, with ``no_response``, never answered).

    ``afters`` is the ``after`` of each page posted, for a record that pages a connection; a record that pages none is
    posted once, or once and then once per retry when ``rate_limited``. ``message`` holds the patterns one log record
    matches; ``details`` is the JSON value a ``Details:`` record holds, ``None`` when the error carries none."""

    slug: str
    operation_id: str
    arguments: Tuple[str, ...]
    variables: Mapping[str, Any]
    replies: Tuple[Any, ...]
    message: Tuple[str, ...]
    details: Any = None
    afters: Tuple[Optional[str], ...] = ()
    rate_limited: bool = False
    no_response: bool = False


PIN_ARGUMENTS = json_field(name=VARIABLE_INPUT, value=PIN_INPUT)
PIN_VARIABLES: Mapping[str, Any] = {VARIABLE_INPUT: dict(PIN_INPUT)}
ON_GRAPHQL = re.escape(pattern=GRAPHQL_PATH)

FAILURE_CASES: Tuple[FailureCase, ...] = (
    FailureCase(
        slug="errors-without-data",
        operation_id=OP_PIN_ISSUE,
        arguments=PIN_ARGUMENTS,
        variables=PIN_VARIABLES,
        replies=(fx.Reply(body={fx.FIELD_ERRORS: list(GRAPHQL_ERRORS)}),),
        message=(ON_GRAPHQL, re.escape(pattern=GRAPHQL_ERROR_TEXT)),
        details=list(GRAPHQL_ERRORS),
    ),
    FailureCase(
        slug="errors-with-data",
        operation_id=OP_PIN_ISSUE,
        arguments=PIN_ARGUMENTS,
        variables=PIN_VARIABLES,
        replies=(fx.Reply(body={FIELD_DATA: {FIELD_PIN_ISSUE: None}, fx.FIELD_ERRORS: list(GRAPHQL_ERRORS)}),),
        message=(ON_GRAPHQL, re.escape(pattern=GRAPHQL_ERROR_TEXT)),
        details=list(GRAPHQL_ERRORS),
    ),
    FailureCase(
        slug="http-502",
        operation_id=OP_PIN_ISSUE,
        arguments=PIN_ARGUMENTS,
        variables=PIN_VARIABLES,
        replies=(BAD_GATEWAY,),
        message=(ON_GRAPHQL, re.escape(pattern="HTTP 502")),
        details=BAD_GATEWAY.body,
    ),
    FailureCase(
        slug="spent-rate-limit",
        operation_id=OP_PIN_ISSUE,
        arguments=PIN_ARGUMENTS,
        variables=PIN_VARIABLES,
        replies=(RATE_LIMITED,),
        message=(ON_GRAPHQL, re.escape(pattern="HTTP 403")),
        details=RATE_LIMITED.body,
        rate_limited=True,
    ),
    FailureCase(
        slug="no-response",
        operation_id=OP_PIN_ISSUE,
        arguments=PIN_ARGUMENTS,
        variables=PIN_VARIABLES,
        replies=(data_reply(data=PIN_DATA),),
        message=(ON_GRAPHQL, re.escape(pattern=NO_RESPONSE_REASON)),
        no_response=True,
    ),
    FailureCase(
        slug="page-without-its-connection",
        operation_id=OP_MERGE_QUEUE,
        arguments=MERGE_QUEUE_ARGUMENTS,
        variables=MERGE_QUEUE_VARIABLES,
        replies=(data_reply(data={FIELD_REPOSITORY: {FIELD_MERGE_QUEUE: None}}),),
        message=(re.escape(pattern=json.dumps(obj=list(MERGE_QUEUE_CONNECTION))),),
        afters=(None,),
    ),
    FailureCase(
        slug="second-page-fails",
        operation_id=OP_MERGE_QUEUE,
        arguments=MERGE_QUEUE_ARGUMENTS,
        variables=MERGE_QUEUE_VARIABLES,
        replies=(
            connection_reply(
                connection=MERGE_QUEUE_CONNECTION, nodes=MERGE_QUEUE_ENTRIES[:1], end_cursor=FIRST_CURSOR, has_next=True
            ),
            BAD_GATEWAY,
        ),
        message=(ON_GRAPHQL, re.escape(pattern="HTTP 502")),
        details=BAD_GATEWAY.body,
        afters=(None, FIRST_CURSOR),
    ),
)


def failure_case_name(case: FailureCase) -> str:
    """The test id of a ``FAILURE_CASES`` row."""
    return case.slug


def failure_writes(*, case: FailureCase, document: Optional[str], retries: int) -> Tuple[Any, ...]:
    """Every ``POST`` ``case`` sends, in order: one per page of a connection, else one, and one more per retry of a
    spent rate limit."""
    if case.afters:
        return tuple(paged_posts(document=document, variables=case.variables, afters=case.afters))
    attempts = 1 + retries if case.rate_limited else 1
    return (posted(document=document, variables=case.variables),) * attempts


def _answer_with_no_response(self: Any, *, request: urllib.request.Request) -> NoReturn:
    """``FakeGitHub.answer`` for a host that never answers: the request is recorded, then ``urllib.error.URLError`` is
    raised, as a refused or reset connection raises it inside urllib's handler."""
    self.requests.append(fx.RecordedRequest.of(request=request))
    raise urllib.error.URLError(reason=NO_RESPONSE_REASON)


def logged_details(*, records: Sequence[logging.LogRecord]) -> List[Any]:
    """The JSON value of every ``Details:`` log record, parsed."""
    messages = [record.getMessage() for record in records]
    return [json.loads(s=message[len(DETAILS_PREFIX) :]) for message in messages if message.startswith(DETAILS_PREFIX)]


@pytest.mark.parametrize(argnames="failure", argvalues=FAILURE_CASES, ids=failure_case_name)
def test_a_graphql_failure_exits_1_with_its_details(
    failure: FailureCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.4: a response with ``errors`` (with or without ``data``), an HTTP ``502``, a rate limit still applying
    after every retry, no response, a page without its connection (a ``null`` ``mergeQueue``), and a ``502`` on the
    second page each exit 1 with nothing on standard output; a log record holds the error's message, and a
    ``Details:`` record holds its details: for ``errors``, the ``errors`` array."""
    transport = fx.import_api_module(name=TRANSPORT)
    document = declared_document(operation_id=failure.operation_id)
    if failure.no_response:
        monkeypatch.setattr(target=fx.FakeGitHub, name="answer", value=_answer_with_no_response)
    case = fx.GoldenCase(
        name=f"{AC_2_4}/exit-1/{failure.slug}",
        argv=(CALL, failure.operation_id, *failure.arguments),
        stdout="",
        exit_code=fx.EXIT_API_ERROR,
        routes=(graphql_route(replies=failure.replies),),
        writes=failure_writes(case=failure, document=document, retries=transport.RATE_LIMIT_MAX_RETRIES),
        log=fx.LogExpectation(refusal=failure.message, withheld=()),
    )

    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)

    if failure.details is not None:
        details = logged_details(records=caplog.records)
        assert failure.details in details, f"{case.name}: no Details: record holds {failure.details}: {details}"


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.5 — a variable the document does not declare is refused before any request
# ---------------------------------------------------------------------------------------------------------------------


def _undeclared(*, slug: str, argv: Tuple[str, ...], refused: Tuple[str, ...], declared: Tuple[str, ...]) -> Any:
    """A refusal naming each of ``refused`` and the record's declared variables, ``declared``, in document order."""
    patterns = (*(named(name=name) for name in refused), re.escape(pattern=json.dumps(obj=list(declared))))
    return _refusal(criterion=AC_2_5, slug=slug, argv=argv, patterns=patterns)


UNDECLARED_CASES: Tuple[Any, ...] = (
    _undeclared(
        slug="variable-the-document-does-not-define",
        argv=(CALL, OP_PIN_ISSUE, *raw_field(name=UNDECLARED_VARIABLE, text="1")),
        refused=(UNDECLARED_VARIABLE,),
        declared=(VARIABLE_INPUT,),
    ),
    _undeclared(
        slug="path-and-query-names",
        argv=(
            CALL,
            OP_PIN_ISSUE,
            *json_field(name=VARIABLE_INPUT, value={}),
            OPTION_PATH,
            f"{UNDECLARED_PATH_NAME}=1",
            OPTION_QUERY,
            f"{UNDECLARED_QUERY_NAME}={fx.STATE_OPEN}",
        ),
        refused=(UNDECLARED_PATH_NAME, UNDECLARED_QUERY_NAME),
        declared=(VARIABLE_INPUT,),
    ),
    _undeclared(
        slug="after-of-a-paging-record",
        argv=(
            CALL,
            OP_DISCUSSIONS,
            *raw_field(name=VARIABLE_OWNER, text=fx.OWNER),
            *raw_field(name=VARIABLE_NAME, text=fx.REPOSITORY),
            *raw_field(name=FIELD_AFTER, text="c"),
        ),
        refused=(FIELD_AFTER,),
        declared=(VARIABLE_OWNER, VARIABLE_NAME),
    ),
)


@pytest.mark.parametrize(argnames="case", argvalues=UNDECLARED_CASES, ids=fx.case_name)
def test_an_undeclared_variable_is_refused(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.5: a variable the document does not declare (``after`` on a record that pages a connection included), and
    any ``--path`` or ``--query`` name, exits 2 with no request, and one log record names each such name and the
    record's declared variables."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


# ---------------------------------------------------------------------------------------------------------------------
# AC-3.1 to AC-3.3 — a refused mutation sends nothing
# ---------------------------------------------------------------------------------------------------------------------


def refusal_patterns(*, operation_id: str) -> Tuple[str, ...]:
    """AC-3.1's and AC-3.2's log of the refusal of ``operation_id``: the ID and the mutation's name, then the
    subcommand to use without saying that it sends the mutation, or that no subcommand sends it."""
    mutation = operation_id[len(GRAPHQL_ID_PREFIX) :]
    identified = (named(name=operation_id), re.escape(pattern=mutation))
    subcommand = SUBCOMMAND_OF_REFUSED.get(operation_id)
    if subcommand is None:
        return (*identified, re.escape(pattern=NO_SUBCOMMAND_SENDS_IT))
    return (*identified, re.escape(pattern=subcommand), lacking(text=SENDS_IT))


@pytest.mark.parametrize(argnames="operation_id", argvalues=REFUSED_MUTATIONS)
def test_a_refused_mutation_sends_nothing(
    operation_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-3.1 to AC-3.3: ``call <id> -F input={}`` of each refused mutation exits 2 with no request, although
    ``POST /graphql`` would be answered; the log record names the ID and the mutation, and for
    ``graphql/enablePullRequestAutoMerge`` the ``merge-pr`` subcommand without saying that it sends it, for each other
    that no subcommand sends it."""
    case = _refusal(
        criterion=AC_3_1,
        slug=operation_id,
        argv=(CALL, operation_id, *json_field(name=VARIABLE_INPUT, value={})),
        patterns=refusal_patterns(operation_id=operation_id),
    )

    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)
