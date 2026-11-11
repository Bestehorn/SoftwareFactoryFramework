"""Tests for ``gitlab_api/registry.py`` — the operation records, path expansion, value encoding and id lookup.

What is pinned (issue #13, ``design.md`` D5): a value substituted into a path parameter is ONE percent-encoded segment
(``/`` as ``%2F``; an empty value, ``.`` and ``..`` refused — AC-2.2); an array of hashes in a query string or a form
body is sent in the bracket form ``name[0][key]=value`` (AC-2.3); ``lookup`` refuses an unknown and a twice-declared
operation id, each naming the id, and ``call`` refuses a value its record does not declare, naming it, before anything
is sent (AC-1.1).

Issue #41 (``design.md`` D2) adds: ``send`` returns the ``Response`` of a REST record's request and refuses a GraphQL
record with nothing sent (AC-1.2); ``attribute_name`` drops one trailing ``[]`` (AC-1.3); ``variables`` names each
``$name`` that a ``:`` follows in a record's document, in order, a connection record's cursor ``after`` left out
(AC-2.2). Their ``GraphQLOperation`` records carry D2's ``capability``.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; each
test imports the production module inside its body, so a module not written yet fails the test on an assertion. The
fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_registry.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "gitlab_api"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# The keywords of ``Transport.request`` that ``registry.encode``'s result feeds (design.md D4, D5).
PART_QUERY = "query"
PART_FORM = "form"

# conventions.md "Arrays, hashes and arrays of hashes": `variables[0][key]=VAR1&variables[0][value]=hello&...`.
VARIABLES = [{"key": "VAR1", "value": "hello"}, {"key": "VAR2", "value": "world"}]
VARIABLES_PAIRS = [
    ("variables[0][key]", "VAR1"),
    ("variables[0][value]", "hello"),
    ("variables[1][key]", "VAR2"),
    ("variables[1][value]", "world"),
]

# The record `registry.call` reaches through a monkeypatched `lookup`, and a value it does not declare: a misspelling
# of its declared `confidential`, which `call` must refuse rather than send or drop.
CALL_OPERATION_ID = "synthetic#update-an-issue"
UNDECLARED_NAME = "confidental"
# The `Transport` of design.md D4 built for a test: a fixed clock, a recording sleep, the default opener.
FIXED_CLOCK_SECONDS = 0.0
TOKEN_TYPE_PRIVATE = "private"

# The records of the registry additions (issue #41, design.md D2). `send` is tested on a REST record answered `204` (an
# empty body, whose decoded value is `None`, so only the `Response` itself tells `send` from `call`) and on a GraphQL
# record, which `send` refuses.
SEND_OPERATION_ID = "synthetic#delete-a-repository-branch"
SEND_PATH = "/projects/:id/repository/branches/:branch"
SEND_VALUES = {"id": "diaspora/diaspora", "branch": "feature/x"}
SEND_SENT_PATH = "/projects/diaspora%2Fdiaspora/repository/branches/feature%2Fx"
STATUS_NO_CONTENT = 204
GRAPHQL_OPERATION_ID = "graphql#syntheticProject"
SYNTHETIC_CAPABILITY = "Synthetic project lookup"
# design.md § Correctness Properties AC-2.2: `$fullPath` and `$first` are defined (`$first` with white space before its
# `:`); `$fullPath` in the selection set is a use, not a definition.
PROJECT_DOCUMENT = "query Q($fullPath: ID!, $first : Int = 2) { project(fullPath: $fullPath) { id } }"
# A connection document over several lines: `$after` is the cursor `Transport.graphql_nodes` sets on every page.
ISSUES_DOCUMENT = (
    "query Issues($fullPath: ID!,\n"
    "    $after: String) {\n"
    "  project(fullPath: $fullPath) { issues(after: $after) { nodes { iid } pageInfo { hasNextPage endCursor } } }\n"
    "}\n"
)
ISSUES_CONNECTION = ("project", "issues")


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` inside a test, so a module not written yet fails it on an assertion."""
    source = PACKAGE_DIR / f"{name}.py"
    assert source.is_file(), f"gitlab_api/{name}.py does not exist under {SCRIPTS_DIR}"
    return importlib.import_module(name=f"gitlab_api.{name}")


def encoded_part(*, encoded: Any, name: str) -> List[Tuple[str, str]]:
    """The name-value pairs of one part of ``registry.encode``'s result, by the ``Transport.request`` keyword the
    part feeds; read as an attribute or as a mapping key, the two shapes D5 leaves open."""
    part = encoded[name] if isinstance(encoded, Mapping) else getattr(encoded, name)
    return [(str(pair_name), str(pair_value)) for pair_name, pair_value in part]


def synthetic_family(*, name: str, operations: Sequence[Any]) -> ModuleType:
    """A stand-in for one ``gitlab_api/families/<family>.py`` module (D2's family module contract)."""
    module = ModuleType(name=f"synthetic_families.{name.replace('-', '_')}")
    module.__dict__.update(FAMILY=name, OPERATIONS=tuple(operations), PENDING=frozenset())
    return module


def serve_families(*, monkeypatch: pytest.MonkeyPatch, registry: ModuleType, families: Sequence[ModuleType]) -> None:
    """Make ``registry.discover_families`` return exactly ``families``, so ``lookup`` reads their records."""

    def discover_families(*, package: Any = None) -> Tuple[ModuleType, ...]:
        return tuple(families)

    monkeypatch.setattr(registry, "discover_families", discover_families)


@pytest.mark.parametrize(
    ("path", "values", "expected"),
    [
        ("/projects/:id", {"id": "diaspora/diaspora"}, "/projects/diaspora%2Fdiaspora"),
        (
            "/projects/:id",
            {"id": "my-group/my-subgroup/my-project"},
            "/projects/my-group%2Fmy-subgroup%2Fmy-project",
        ),
        ("/projects/:id", {"id": 42}, "/projects/42"),
        (
            "/projects/:id/repository/branches/:branch",
            {"id": "diaspora/diaspora", "branch": "my/branch"},
            "/projects/diaspora%2Fdiaspora/repository/branches/my%2Fbranch",
        ),
        (
            "/projects/:id/repository/files/:file_path",
            {"id": 1, "file_path": "src/README.md"},
            "/projects/1/repository/files/src%2FREADME.md",
        ),
        (
            "/projects/:id/repository/tags/:tag_name",
            {"id": 1, "tag_name": "my/tag"},
            "/projects/1/repository/tags/my%2Ftag",
        ),
    ],
    ids=["full-path", "subgroup-path", "numeric-id", "branch", "file-path", "tag"],
)
def test_project_path_is_encoded(path: str, values: Dict[str, Any], expected: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(operation_id="synthetic#expand", method="GET", path=path)
    assert registry.expand(operation=operation, values=values) == expected, (
        "each path value is one segment, `/` sent as %2F (conventions.md 'URL-encoding path parameters')"
    )


@pytest.mark.parametrize("value", ["", ".", ".."], ids=["empty", "dot", "dot-dot"])
def test_empty_and_dot_segments_are_refused(value: str) -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(
        operation_id="synthetic#retrieve-a-branch",
        method="GET",
        path="/projects/:id/repository/branches/:branch",
    )
    with pytest.raises(errors.GitLabAPIError):
        registry.expand(operation=operation, values={"id": "diaspora/diaspora", "branch": value})


@pytest.mark.parametrize(
    ("location", "body", "part"),
    [("QUERY", "JSON", PART_QUERY), ("BODY", "FORM", PART_FORM)],
    ids=["query-string", "form-body"],
)
def test_array_of_hashes_pairs(location: str, body: str, part: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(
        operation_id="synthetic#create-a-pipeline",
        method="POST",
        path="/projects/:id/pipeline",
        params=(
            registry.Param(
                name="variables",
                location=getattr(registry.Location, location),
                kind=registry.Kind.ARRAY_OF_HASHES,
            ),
        ),
        body=getattr(registry.BodyFormat, body),
    )
    encoded = registry.encode(operation=operation, values={"id": 7, "variables": VARIABLES})
    assert encoded_part(encoded=encoded, name=part) == VARIABLES_PAIRS, (
        "an array of hashes is sent as name[index][key]=value pairs, in list and key order (AC-2.3)"
    )


def test_lookup_refuses_unknown_and_duplicate_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = gitlab_module(name="registry")

    def record(*, operation_id: str, path: str) -> Any:
        return registry.RestOperation(operation_id=operation_id, method="GET", path=path)

    declared_once = record(operation_id="synthetic-alpha#declared-once", path="/alpha")
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[
            synthetic_family(name="synthetic-alpha", operations=[declared_once]),
            synthetic_family(
                name="synthetic-beta",
                operations=[record(operation_id="synthetic-beta#declared-once", path="/beta")],
            ),
        ],
    )
    assert registry.lookup(operation_id="synthetic-alpha#declared-once") == declared_once, (
        "lookup reads the records of the families discover_families returns"
    )
    unknown = "synthetic-alpha#no-such-operation"
    with pytest.raises(ValueError, match=re.escape(unknown)) as unknown_refusal:
        registry.lookup(operation_id=unknown)

    twice = "synthetic-beta#declared-twice"
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[
            synthetic_family(name="synthetic-alpha", operations=[record(operation_id=twice, path="/alpha/twice")]),
            synthetic_family(name="synthetic-beta", operations=[record(operation_id=twice, path="/beta/twice")]),
        ],
    )
    with pytest.raises(ValueError, match=re.escape(twice)) as duplicate_refusal:
        registry.lookup(operation_id=twice)
    duplicate_message = str(duplicate_refusal.value).replace(twice, "<id>")
    unknown_message = str(unknown_refusal.value).replace(unknown, "<id>")
    assert duplicate_message != unknown_message, "a twice-declared id is refused as declared twice, not as unknown"


def test_call_refuses_an_undeclared_value(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    operation = registry.RestOperation(
        operation_id=CALL_OPERATION_ID,
        method="PUT",
        path="/projects/:id/issues/:issue_iid",
        params=(
            registry.Param(name="title", location=registry.Location.BODY),
            registry.Param(name="confidential", location=registry.Location.BODY),
        ),
    )

    def lookup(*, operation_id: str) -> Any:
        assert operation_id == CALL_OPERATION_ID, f"call looked up {operation_id!r}, not the id it was given"
        return operation

    monkeypatch.setattr(registry, "lookup", lookup)
    # The request `call` would send if it dropped the undeclared value is scripted, so sending it fails this test on its
    # oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="PUT", url=f"{fixtures.REST_BASE}/projects/diaspora%2Fdiaspora/issues/7", body={"iid": 7})
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )
    with pytest.raises(ValueError, match=re.escape(UNDECLARED_NAME)):
        registry.call(
            transport=transport,
            operation_id=CALL_OPERATION_ID,
            values={"id": "diaspora/diaspora", "issue_iid": 7, "title": "Renamed", UNDECLARED_NAME: True},
        )
    assert fake_gitlab.requests == [], "a value the record does not declare is refused before any request (AC-1.1)"


def test_send_returns_the_response_of_the_record(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    graphql_only = gitlab_module(name="graphql_only")
    operation = registry.RestOperation(operation_id=SEND_OPERATION_ID, method="DELETE", path=SEND_PATH)
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[operation])],
    )
    sent_url = f"{fixtures.REST_BASE}{SEND_SENT_PATH}"
    fake_gitlab.script(method="DELETE", url=sent_url, status=STATUS_NO_CONTENT)
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    response = registry.send(transport=transport, operation_id=SEND_OPERATION_ID, values=SEND_VALUES)
    assert isinstance(response, transport_module.Response), (
        f"send returns the Response of the record's request, not its decoded value; got {response!r} (design.md D2)"
    )
    assert (response.status, response.body) == (STATUS_NO_CONTENT, b""), "the Response is the 204 the host answered"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("DELETE", sent_url)], (
        "send sends the record's one request: its method, its path expanded (AC-1.2)"
    )

    graphql_record = registry.GraphQLOperation(
        operation_id=GRAPHQL_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=PROJECT_DOCUMENT,
    )
    monkeypatch.setattr(graphql_only, "OPERATIONS", (graphql_record,))
    assert registry.lookup(operation_id=GRAPHQL_OPERATION_ID) == graphql_record, (
        "the GraphQL record is declared, so a refusal below is send's and not lookup's unknown id"
    )
    # The request `send` would send if it ran the GraphQL record is scripted, so sending it fails this test on its
    # oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="POST", url=fixtures.GRAPHQL_URL, body={"data": {"project": {"id": "gid://gitlab/1"}}})
    sent_before = list(fake_gitlab.requests)
    with pytest.raises(ValueError):
        registry.send(transport=transport, operation_id=GRAPHQL_OPERATION_ID, values={"fullPath": "g/p"})
    assert fake_gitlab.requests == sent_before, "send refuses a GraphQL record with no request (design.md D2)"


@pytest.mark.parametrize(
    ("name", "expected"),
    [("iids[]", "iids"), ("a[][]", "a[]"), ("not[labels]", "not[labels]")],
    ids=["array-suffix", "one-pair-only", "hash-key-unchanged"],
)
def test_attribute_name_drops_one_trailing_bracket_pair(name: str, expected: str) -> None:
    registry = gitlab_module(name="registry")
    assert registry.attribute_name(name=name) == expected, (
        f"{name!r} names the Param {expected!r}: one trailing [] is dropped, nothing else (design.md D2, AC-1.3)"
    )


@pytest.mark.parametrize(
    ("document", "connection", "expected"),
    [
        (PROJECT_DOCUMENT, (), ("fullPath", "first")),
        (ISSUES_DOCUMENT, ISSUES_CONNECTION, ("fullPath",)),
        (ISSUES_DOCUMENT, (), ("fullPath", "after")),
    ],
    ids=["definitions-in-order", "connection-drops-after", "no-connection-keeps-after"],
)
def test_variables_are_the_documents_definitions(
    document: str, connection: Tuple[str, ...], expected: Tuple[str, ...]
) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=GRAPHQL_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=document,
        connection=connection,
    )
    assert registry.variables(operation=operation) == expected, (
        "each $name followed, after any white space, by `:` is a definition, in order; a connection record leaves "
        "out its cursor `after` (design.md D2, AC-2.2)"
    )
