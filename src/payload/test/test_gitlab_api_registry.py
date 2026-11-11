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

Issue #44 (``design.md`` D4) adds: ``upload_variables`` maps each variable a record's document defines with the type
``Upload``, or a list of it, to whether it is a list; ``split_uploads`` replaces each ``pathlib.Path`` value, and each
one in a list, with ``None`` and returns the files with the operations path each fills, in order (AC-3.1).
``upload_variables`` also leaves out a definition that has no type, and still reads the ones around it.

Issue #40 (``design.md`` D1, D5) adds the path forms of the reference: ``placeholders`` names every ``:name`` and
``*name`` in path order (AC-2.4); ``expand`` writes a ``*name`` glob with each ``/`` kept and each part one segment,
refusing an empty, ``.`` or ``..`` part (AC-2.1, AC-2.2), an optional ``(...)`` group only when its parameter has a
value (AC-2.3), and an escaped ``\\(`` or ``\\)`` as its parenthesis (AC-2.5); ``send`` sends a raw-body record the
bytes it is given as its body, and refuses bytes for any other record with nothing sent (AC-3.2).

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

# The upload records of issue #44 (design.md D4, § Correctness Properties AC-3.1): `$files` is a list of `Upload`, with
# white space before its `:`; `$file` is one `Upload`; `$n` is a list of another type, so no upload variable.
UPLOAD_OPERATION_ID = "graphql#syntheticUpload"
FILES_DOCUMENT = "mutation M($files : [Upload!]!) { syntheticUpload(input: {files: $files}) { errors } }"
FILE_DOCUMENT = "mutation M($file: Upload) { syntheticUpload(input: {file: $file}) { errors } }"
INT_LIST_DOCUMENT = "query Q($n: [Int!]) { syntheticList(n: $n) { id } }"
ALL_UPLOADS_DOCUMENT = (
    "mutation M($files : [Upload!]!, $file: Upload,\n"
    "    $n: [Int!]) {\n"
    "  syntheticUpload(input: {files: $files, file: $file, n: $n}) { errors }\n"
    "}\n"
)
FILES_UPLOADS: Dict[str, bool] = {"files": True}
FILE_UPLOADS: Dict[str, bool] = {"file": False}
NO_UPLOADS: Dict[str, bool] = {}
ALL_UPLOADS: Dict[str, bool] = {"files": True, "file": False}
# `split_uploads`' values as `commands/call.py` `call_values` gives them (design.md D4): a list of files, one file, and
# text. The files are never read here, so they need not exist.
FIRST_FILE = Path("first.png")
SECOND_FILE = Path("second.png")
THIRD_FILE = Path("import.csv")
SPLIT_VALUES: Dict[str, Any] = {"projectPath": "g/p", "files": [FIRST_FILE, SECOND_FILE], "file": THIRD_FILE}
SPLIT_VARIABLES: Dict[str, Any] = {"projectPath": "g/p", "files": [None, None], "file": None}
SPLIT_FILES: Tuple[Tuple[str, Path], ...] = (
    ("variables.files.0", FIRST_FILE),
    ("variables.files.1", SECOND_FILE),
    ("variables.file", THIRD_FILE),
)
# The path forms of issue #40 (design.md D1), each on a reference path of operations-index.md as its row writes it (a
# `\` is `\\` here, as `families/openapi_only.py` spells it): a `*name` glob, an optional `(...)` group, an escaped
# parenthesis, and a `:name` inside a segment.
MAVEN_OPERATION_ID = "synthetic#workhorse-authorize-the-maven-package-file-upload"
MAVEN_AUTHORIZE_PATH = "/projects/:id/packages/maven/*path/:file_name/authorize"
MAVEN_VALUES = {"id": 1, "file_name": "x.jar"}
# The glob of MAVEN_AUTHORIZE_PATH as a refusal names it (design.md § Correctness Properties AC-2.2).
MAVEN_GLOB = "*path"
GENERIC_OPERATION_ID = "synthetic#download-package-file"
GENERIC_PACKAGE_PATH = "/projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name"
GENERIC_VALUES = {"id": 1, "package_name": "pkg", "package_version": "1.0", "file_name": "file.txt"}
GENERIC_WITH_GROUP = "/projects/1/packages/generic/pkg/1.0/a/b/file.txt"
GENERIC_WITHOUT_GROUP = "/projects/1/packages/generic/pkg/1.0/file.txt"
NUGET_SINGLE_PACKAGE_PATH = (
    "/projects/:project_id/packages/nuget/v2/Packages\\(Id='*package_name',Version='*package_version'\\)"
)
NUGET_FIND_BY_ID_PATH = "/projects/:project_id/packages/nuget/v2/FindPackagesById\\(\\)"
NUGET_ENUMERATE_PATH = "/projects/:project_id/packages/nuget/v2/Packages\\(\\)"
NUGET_METADATA_PATH = "/projects/:id/packages/nuget/v2/$metadata"
DEBIAN_INDEX_PATH = "/projects/:id/packages/debian/dists/*distribution/:component/binary-:architecture/Packages"
# design.md § Correctness Properties AC-2.5: each case's path and values, and the path `expand` writes for it.
ESCAPED_CASES = {
    "single-package": (NUGET_SINGLE_PACKAGE_PATH, {"project_id": 7, "package_name": "N", "package_version": "1.0"}),
    "find-by-id": (NUGET_FIND_BY_ID_PATH, {"project_id": 7}),
    "enumerate-with-no-value": (NUGET_ENUMERATE_PATH, {"project_id": 7}),
    "metadata": (NUGET_METADATA_PATH, {"id": 7}),
    "glob-value-with-parentheses": (
        NUGET_SINGLE_PACKAGE_PATH,
        {"project_id": 7, "package_name": "a(b)'", "package_version": "1.0"},
    ),
}
ESCAPED_WRITTEN = {
    "single-package": "/projects/7/packages/nuget/v2/Packages(Id='N',Version='1.0')",
    "find-by-id": "/projects/7/packages/nuget/v2/FindPackagesById()",
    "enumerate-with-no-value": "/projects/7/packages/nuget/v2/Packages()",
    "metadata": "/projects/7/packages/nuget/v2/$metadata",
    "glob-value-with-parentheses": "/projects/7/packages/nuget/v2/Packages(Id='a%28b%29%27',Version='1.0')",
}
# The raw-body record of design.md D5 on the reference path of `openapi-only#create-or-update-a-terraform-state`, a
# record on the same path that is not one, and bytes a text-layer read would translate (`\r\n`) or fail to decode
# (`\xff`) (design.md § Correctness Properties AC-3.2).
RAW_OPERATION_ID = "synthetic#create-or-update-a-terraform-state"
PLAIN_OPERATION_ID = "synthetic#create-or-update-a-terraform-state-without-a-raw-body"
TERRAFORM_STATE_PATH = "/projects/:id/terraform/state/:name"
TERRAFORM_STATE_VALUES = {"id": 1, "name": "production"}
TERRAFORM_STATE_SENT_PATH = "/projects/1/terraform/state/production"
RAW_MEDIA_TYPE = "application/octet-stream"
RAW_BYTES = b"terraform state\r\nserial \xff\x00"


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


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        (FILES_DOCUMENT, FILES_UPLOADS),
        (FILE_DOCUMENT, FILE_UPLOADS),
        (INT_LIST_DOCUMENT, NO_UPLOADS),
        (ALL_UPLOADS_DOCUMENT, ALL_UPLOADS),
    ],
    ids=["list-of-uploads", "one-upload", "list-of-another-type", "all-three-in-one-document"],
)
def test_upload_variables_are_the_documents_upload_definitions(document: str, expected: Dict[str, bool]) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=UPLOAD_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=document,
    )
    assert registry.upload_variables(operation=operation) == expected, (
        "each defined variable whose type, with `[`, `]`, `!` and white space removed, is `Upload` is mapped to "
        "whether its type begins with `[`; a variable of another type is left out (design.md D4, AC-3.1)"
    )


# A document one of whose definitions has no type `TYPE_REFERENCE` reads: `$broken:` is followed by `,`, which starts
# no Name. The upload variables before and after it are read all the same (design.md D4).
UNTYPED_DEFINITION_NAME = "broken"
UNTYPED_DEFINITION_DOCUMENT = (
    "mutation M($files: [Upload!]!, $broken: , $file: Upload) "
    "{ syntheticUpload(input: {files: $files, file: $file}) { errors } }"
)


def test_upload_variables_leave_out_a_definition_without_a_type() -> None:
    """design.md D4, AC-3.1: a ``$name:`` definition followed by no type is a declared variable (``variables`` names
    it) that ``upload_variables`` leaves out, while it still maps the ``Upload`` variables before and after it."""
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=UPLOAD_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=UNTYPED_DEFINITION_DOCUMENT,
    )
    assert UNTYPED_DEFINITION_NAME in registry.variables(operation=operation), (
        f"${UNTYPED_DEFINITION_NAME} is a definition of the document, so upload_variables reads a type for it"
    )
    assert registry.upload_variables(operation=operation) == ALL_UPLOADS, (
        f"a definition without a type, ${UNTYPED_DEFINITION_NAME}, is left out, and the Upload variables around it are "
        "still mapped to whether each is a list (design.md D4, AC-3.1)"
    )


def test_split_uploads_puts_null_where_each_file_goes() -> None:
    registry = gitlab_module(name="registry")
    sent_variables, files = registry.split_uploads(values=SPLIT_VALUES)
    assert sent_variables == SPLIT_VARIABLES, (
        "each Path value, and each Path item of a list, is replaced by None, the null of the operations part; every "
        "other value is unchanged (design.md D4, AC-3.1)"
    )
    assert files == SPLIT_FILES, (
        "each file with the operations path it fills, variables.<name> or variables.<name>.<index>, in the order of "
        "the values and of each list (design.md D4, AC-3.1)"
    )


@pytest.mark.parametrize(
    ("path", "named", "required"),
    [
        (
            GENERIC_PACKAGE_PATH,
            ("id", "package_name", "package_version", "path", "file_name"),
            ("id", "package_name", "package_version", "file_name"),
        ),
        (
            NUGET_SINGLE_PACKAGE_PATH,
            ("project_id", "package_name", "package_version"),
            ("project_id", "package_name", "package_version"),
        ),
        (
            DEBIAN_INDEX_PATH,
            ("id", "distribution", "component", "architecture"),
            ("id", "distribution", "component", "architecture"),
        ),
        ("/projects/:id/repository/branches/:branch", ("id", "branch"), ("id", "branch")),
    ],
    ids=["optional-group", "escaped-parentheses", "glob-and-placeholder-inside-a-segment", "colon-only"],
)
def test_placeholders_name_every_path_form(path: str, named: Tuple[str, ...], required: Tuple[str, ...]) -> None:
    registry = gitlab_module(name="registry")
    assert registry.placeholders(path=path) == named, (
        f"{path!r} names {named!r}: every :name and *name, without its sigil, in path order, inside an optional group "
        "or not (design.md D1, AC-2.4)"
    )
    assert registry.required_placeholders(path=path) == required, (
        f"{path!r} must be given {required!r}: its placeholders with every optional group's left out (design.md D1, "
        "AC-2.3, AC-2.4)"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.0/rc 1", "/projects/1/packages/maven/1.0/rc%201/x.jar/authorize"),
        ("@scope/pkg", "/projects/1/packages/maven/%40scope/pkg/x.jar/authorize"),
        ("a?b#c", "/projects/1/packages/maven/a%3Fb%23c/x.jar/authorize"),
        ("%2e%2e/x", "/projects/1/packages/maven/%252e%252e/x/x.jar/authorize"),
    ],
    ids=["space", "npm-scope", "query-and-fragment", "encoded-dots"],
)
def test_a_glob_value_keeps_its_slashes(value: str, expected: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(operation_id=MAVEN_OPERATION_ID, method="PUT", path=MAVEN_AUTHORIZE_PATH)
    assert registry.expand(operation=operation, values={**MAVEN_VALUES, "path": value}) == expected, (
        f"the glob {MAVEN_GLOB} given {value!r} keeps each `/`, each part between them one percent-encoded segment "
        "(design.md D1, AC-2.1)"
    )


@pytest.mark.parametrize(
    "value",
    ["a//b", "/a", "a/", "a/./b", "a/../b", "", ".", ".."],
    ids=["empty-inner-part", "leading-slash", "trailing-slash", "dot-part", "dot-dot-part", "empty", "dot", "dot-dot"],
)
def test_a_glob_part_that_is_no_segment_is_refused(value: str) -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(operation_id=MAVEN_OPERATION_ID, method="PUT", path=MAVEN_AUTHORIZE_PATH)
    with pytest.raises(errors.GitLabAPIError, match=re.escape(MAVEN_GLOB)):
        registry.expand(operation=operation, values={**MAVEN_VALUES, "path": value})
    with pytest.raises(ValueError):
        registry.expand(operation=operation, values=MAVEN_VALUES)


def test_an_optional_group_is_written_only_when_given() -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(operation_id=GENERIC_OPERATION_ID, method="GET", path=GENERIC_PACKAGE_PATH)
    written = {
        "given": registry.expand(operation=operation, values={**GENERIC_VALUES, "path": "a/b"}),
        "absent": registry.expand(operation=operation, values=GENERIC_VALUES),
        "none": registry.expand(operation=operation, values={**GENERIC_VALUES, "path": None}),
    }
    assert written == {"given": GENERIC_WITH_GROUP, "absent": GENERIC_WITHOUT_GROUP, "none": GENERIC_WITHOUT_GROUP}, (
        "the group `(*path/)` is written without its parentheses when `path` has a value, and left out whole when "
        "`path` is absent or None (design.md D1, AC-2.3)"
    )
    with pytest.raises(errors.GitLabAPIError):
        registry.expand(operation=operation, values={**GENERIC_VALUES, "path": ""})


def test_an_escaped_parenthesis_is_sent_without_its_backslash() -> None:
    registry = gitlab_module(name="registry")
    written = {
        case: registry.expand(
            operation=registry.RestOperation(operation_id=f"synthetic#{case}", method="GET", path=path),
            values=values,
        )
        for case, (path, values) in ESCAPED_CASES.items()
    }
    assert written == ESCAPED_WRITTEN, (
        "each `\\(` and `\\)` is sent as its parenthesis and never read as an optional group; `$`, `'`, `,` and `=` "
        "are sent as the path writes them, and a value's parentheses are percent-encoded (design.md D1, AC-2.5)"
    )


def test_send_sends_a_raw_record_its_bytes(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    raw_record = registry.RestOperation(
        operation_id=RAW_OPERATION_ID, method="POST", path=TERRAFORM_STATE_PATH, content_type=RAW_MEDIA_TYPE
    )
    plain_record = registry.RestOperation(operation_id=PLAIN_OPERATION_ID, method="POST", path=TERRAFORM_STATE_PATH)
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[raw_record, plain_record])],
    )
    sent_url = f"{fixtures.REST_BASE}{TERRAFORM_STATE_SENT_PATH}"
    fake_gitlab.script(method="POST", url=sent_url)
    # The request `send` would send if it sent the plain record's bytes is scripted too, so sending it fails this test
    # on its oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="POST", url=sent_url)
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    registry.send(transport=transport, operation_id=RAW_OPERATION_ID, values=TERRAFORM_STATE_VALUES, data=RAW_BYTES)
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("POST", sent_url)], (
        "send sends the raw-body record's one request: its method, its path expanded (design.md D5)"
    )
    sent = fake_gitlab.requests[0]
    assert sent.body == RAW_BYTES, "the bytes go out as the body, unchanged (design.md D5, AC-3.2)"
    assert sent.header(name=fixtures.HEADER_CONTENT_TYPE) == RAW_MEDIA_TYPE, (
        "the body's Content-Type is the record's media type (design.md D5, AC-3.2)"
    )

    sent_before = list(fake_gitlab.requests)
    with pytest.raises(ValueError):
        registry.send(
            transport=transport, operation_id=PLAIN_OPERATION_ID, values=TERRAFORM_STATE_VALUES, data=RAW_BYTES
        )
    assert fake_gitlab.requests == sent_before, (
        "bytes given for a record with no media type are refused with no request (design.md D5)"
    )
