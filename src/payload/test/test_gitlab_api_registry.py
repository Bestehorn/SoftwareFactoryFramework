"""Tests for ``gitlab_api/registry.py`` — the operation records, path expansion, value encoding and id lookup.

What is pinned (issue #13, ``design.md`` D5): a value substituted into a path parameter is ONE percent-encoded segment
(``/`` as ``%2F``; an empty value, ``.`` and ``..`` refused — AC-2.2); an array of hashes in a query string or a form
body is sent in the bracket form ``name[0][key]=value`` (AC-2.3); ``lookup`` refuses an unknown and a twice-declared
operation id, each naming the id (AC-1.1).

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
