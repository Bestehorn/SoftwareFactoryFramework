"""Hypothesis properties of the GitLab wrapper package's request encoding (P of issue #13's design).

`registry.expand` puts a path value into a path template as ONE percent-encoded segment, `/` written `%2F` (AC-2.2;
`docs/api-reference/gitlab/conventions.md` "URL-encoding path parameters"). `registry.encode` turns an array into
`k[]=a&k[]=b` and a hash into `k[key]=v` (AC-2.3; `conventions.md` "Arrays, hashes and arrays of hashes"). The pairs
`encode` builds are joined here with `urllib.parse.urlencode(pairs, safe="[]", quote_via=urllib.parse.quote)`, the
join `Transport.request` applies (design.md D4), and read back with
`urllib.parse.parse_qsl(..., keep_blank_values=True)`, which keeps the empty values the strategies generate.

A `*name` glob keeps each `/` of its value (issue #40, AC-2.1 and AC-2.2): `test_glob_value_keeps_each_slash` has
`expand` write each `/`-separated part as one such segment, and `test_a_glob_value_with_a_refused_part_is_refused` has
it refuse a value with an empty, `.` or `..` part, a leading, trailing or doubled `/` among them.

A record whose path starts with `/<route-prefix>/` is routed only under a value of its page (issue #43, AC-2.4 and
UB-2): `test_route_accepts_only_the_records_prefixes` has `route` write each declared npm value in place of
`/<route-prefix>` and refuse any other text with `ValueError`.

The request forms of issue #63 (AC-2.4, AC-3.1, AC-3.2 and AC-4.2): `test_only_a_declared_endpoint_is_chosen` has
`lookup` return, of a synthetic ID's records, the one whose method and path equal the endpoint given and refuse any
other with `ValueError`, `test_each_place_takes_its_own_value` has `expand` write each place of a `positional_names`
name from its own value, and `test_only_a_listed_format_reaches_the_path` has it write a `[.format]` suffix only for one
of the record's `suffix_values`, refusing any other text with `ValueError`.

The properties live in this repository's own `test/`, where Hypothesis is a dev extra; the shipped `src/payload/test/`
stays pytest-only. `src/payload/scripts` is put on `sys.path`, and `gitlab_api` is imported inside each test, so the
module collects whether or not the package exists yet.

The UB-2 import scan lives here too (design.md "Correctness Properties", cross-wrapper decision X1): it reads the entry
script and every module of the package as text, so it imports nothing it scans, and it compares their imports with
`sys.stdlib_module_names` (Python 3.10+, https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names), which
this framework-only suite may use and the shipped Python 3.9 suites may not. Besides the text search for `os.environ`
and `getenv`, it walks each module's AST for the environment names and dynamic imports a text search misses.

Run: ``python scripts/run_tests.py test/test_gitlab_api_properties.py``
"""

from __future__ import annotations

import ast
import importlib
import sys
from collections.abc import Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qsl, quote, unquote, urlencode

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

SCRIPTS = Path(__file__).resolve().parents[1] / "src" / "payload" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

REGISTRY_MODULE = "gitlab_api.registry"

# Every text UTF-8 can encode: all Unicode categories but the surrogates (design.md "Correctness Properties").
TEXT_ALPHABET = st.characters(exclude_categories=("Cs",))
TEXTS = st.text(alphabet=TEXT_ALPHABET)
PATH_VALUES = st.text(alphabet=TEXT_ALPHABET, min_size=1)
HASH_KEYS = st.from_regex(regex=r"[A-Za-z_][A-Za-z0-9_]*", fullmatch=True)

# `.` and `..` are dot segments a URL parser removes; `expand` refuses them (R's example test), so they are outside
# this property's domain.
DOT_SEGMENTS = frozenset({".", ".."})
# A path segment ends at `/`, and the path itself ends at `?` or `#` (RFC 3986 section 3.3).
SEGMENT_DELIMITERS = ("/", "?", "#")

OPERATION_ID_PREFIX = "properties#"
METHOD_GET = "GET"
PATH_PREFIX = "/projects/"
PATH_SUFFIX = "/issues"
PATH_PARAMETER = "id"
PATH_TEMPLATE = PATH_PREFIX + ":" + PATH_PARAMETER + PATH_SUFFIX
PLACEHOLDER_FREE_PATH = "/issues"
QUERY_PARAMETER = "k"
ARRAY_PAIR_NAME = QUERY_PARAMETER + "[]"

# The glob properties (issue #40, design.md "Correctness Properties" AC-2.1 and AC-2.2): one `*glob` between the same
# prefix and suffix, its value the parts joined by `/`.
ERRORS_MODULE = "gitlab_api.errors"
GLOB_PARAMETER = "glob"
GLOB_PATH_TEMPLATE = PATH_PREFIX + "*" + GLOB_PARAMETER + PATH_SUFFIX
PART_SEPARATOR = "/"
# A part is any text UTF-8 can encode but `/`, other than the empty part, `.` and `..`, which are no segment.
PART_ALPHABET = TEXT_ALPHABET.filter(lambda character: character != PART_SEPARATOR)
GLOB_PARTS = st.lists(
    elements=st.text(alphabet=PART_ALPHABET, min_size=1).filter(lambda part: part not in DOT_SEGMENTS),
    min_size=1,
)
REFUSED_PARTS = ("", ".", "..")

# The route-prefix property (issue #43, design.md "Correctness Properties" AC-2.4 and UB-2): the synthetic npm record
# of R's `test_route_writes_the_chosen_prefix`, its path `/<route-prefix>` followed by the dist-tags suffix, and its
# route prefixes the values of the npm page's `<route-prefix>` line (`docs/api-reference/gitlab/rest/package.md`), in
# the line's order.
ROUTE_PREFIX_TEMPLATE = "/<route-prefix>"
DIST_TAGS_SUFFIX = "/-/package/:package_name/dist-tags"
DIST_TAGS_TEMPLATE = ROUTE_PREFIX_TEMPLATE + DIST_TAGS_SUFFIX
NPM_ROUTE_PREFIXES = ("/packages/npm", "/projects/:id/packages/npm", "/groups/:id/-/packages/npm")

# The endpoint property (issue #63, design.md D1 and "Correctness Properties" AC-2.4): one synthetic ID declared on the
# three endpoints of the emoji-reaction "Add" section (`docs/api-reference/gitlab/operations-index.md`), in one
# synthetic family that `discover_families` is made to return.
METHOD_POST = "POST"
ENDPOINT_OPERATION_ID = OPERATION_ID_PREFIX + "add-an-emoji-reaction-to-a-resource"
ISSUE_EMOJI_PATH = "/projects/:id/issues/:issue_iid/award_emoji"
MERGE_REQUEST_EMOJI_PATH = "/projects/:id/merge_requests/:merge_request_iid/award_emoji"
SNIPPET_EMOJI_PATH = "/projects/:id/snippets/:snippet_id/award_emoji"
EMOJI_PATHS = (ISSUE_EMOJI_PATH, MERGE_REQUEST_EMOJI_PATH, SNIPPET_EMOJI_PATH)
ENDPOINT_METHODS = (METHOD_POST, METHOD_GET)
SYNTHETIC_FAMILY = "properties"
SYNTHETIC_FAMILY_MODULE = "synthetic_families." + SYNTHETIC_FAMILY
DISCOVER_FAMILIES = "discover_families"

# The positional property (issue #63, design.md D2 and "Correctness Properties" AC-3.1, AC-3.2): the group SSH
# certificate delete, whose path holds `:id` twice, the group's and the certificate's.
METHOD_DELETE = "DELETE"
POSITIONAL_PARAMETER = "id"
GROUPS_PREFIX = "/groups/"
CERTIFICATES_INFIX = "/ssh_certificates/"
POSITIONAL_PATH_TEMPLATE = GROUPS_PREFIX + ":" + POSITIONAL_PARAMETER + CERTIFICATES_INFIX + ":" + POSITIONAL_PARAMETER
PLACES = 2
# A value of one place: any text UTF-8 can encode but the empty text, `.` and `..`, which are no segment.
PLACE_VALUES = PATH_VALUES.filter(lambda value: value not in DOT_SEGMENTS)

# The suffix property (issue #63, design.md D3 and "Correctness Properties" AC-4.2): the archive path of the index row
# and the page's "Available options" (docs.gitlab.com `repositories`), verbatim and in their order.
ARCHIVE_PATH_TEMPLATE = "/projects/:id/repository/archive[.format]"
ARCHIVE_FORMATS = ("bz2", "tar", "tar.bz2", "tar.gz", "tb2", "tbz", "tbz2", "zip")
SUFFIX_PARAMETER = "format"
SUFFIX_SEPARATOR = "."
ARCHIVE_PROJECT = "7"
ARCHIVED_PATH = "/projects/7/repository/archive"

# The UB-2 scan: the entry script and every module under the package, named by their paths below `SCRIPTS`.
PACKAGE_NAME = "gitlab_api"
ENTRY_SCRIPT = "gitlab_wrapper.py"
PACKAGE_DIRECTORY = SCRIPTS / PACKAGE_NAME
MODULE_PATTERN = "*.py"
REQUIRED_SCANNED = (ENTRY_SCRIPT, PACKAGE_NAME + "/transport.py", PACKAGE_NAME + "/registry.py")
ENVIRONMENT_READS = ("os.environ", "getenv")
# The AST half of the scan: the names `os` (and `posix`, `nt`) read and write the process environment by, and the two
# functions that import a module no `import` statement names. Only AST names are compared, never text, so prose and an
# endpoint path such as `/projects/:id/environments` cannot match.
ENVIRONMENT_NAMES = frozenset({"environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"})
DUNDER_IMPORT = "__import__"
IMPORT_MODULE = "import_module"
DYNAMIC_IMPORT_NAMES = frozenset({DUNDER_IMPORT, IMPORT_MODULE})
REFUSED_IMPORT_NAMES = ENVIRONMENT_NAMES | DYNAMIC_IMPORT_NAMES
MODULE_NAME_ATTRIBUTE = "__name__"
MODULE_SEPARATOR = "."


def load_registry() -> ModuleType:
    """Import `gitlab_api.registry` at test time, so collecting this module never needs the package."""
    return importlib.import_module(name=REGISTRY_MODULE)


def joined_query(*, pairs: Sequence[tuple[str, str]]) -> str:
    """Join name-value pairs the way `Transport.request` does (design.md D4): brackets literal, `+` as `%2B`."""
    return urlencode(query=pairs, safe="[]", quote_via=quote)


def one_query_parameter_operation(*, registry: ModuleType, name: str, kind: Any) -> Any:
    """A GET record with one QUERY parameter of `kind` on a path without placeholders."""
    return registry.RestOperation(
        operation_id=OPERATION_ID_PREFIX + name,
        method=METHOD_GET,
        path=PLACEHOLDER_FREE_PATH,
        params=(registry.Param(name=QUERY_PARAMETER, location=registry.Location.QUERY, kind=kind),),
    )


def encoded_query(*, registry: ModuleType, operation: Any, value: Any) -> str:
    """The joined query of `encode` for the one value; `encode`'s pairs are the `query` that `request` takes (D4)."""
    encoded = registry.encode(operation=operation, values={QUERY_PARAMETER: value})
    return joined_query(pairs=encoded.query)


def hash_pair_name(*, key: str) -> str:
    """The bracket name of one hash entry: `k[key]`."""
    return QUERY_PARAMETER + "[" + key + "]"


@settings(deadline=None)  # the first example also pays for importing the package
@given(value=PATH_VALUES)
@example(value="group/project")
def test_path_value_is_one_segment(value: str) -> None:
    """AC-2.2: any value but a dot segment becomes one segment, free of delimiters, that decodes to the value."""
    assume(value not in DOT_SEGMENTS)
    registry = load_registry()
    operation = registry.RestOperation(
        operation_id=OPERATION_ID_PREFIX + "one-segment", method=METHOD_GET, path=PATH_TEMPLATE
    )

    path = registry.expand(operation=operation, values={PATH_PARAMETER: value})

    assert path.startswith(PATH_PREFIX), path
    assert path.endswith(PATH_SUFFIX), path
    segment = path[len(PATH_PREFIX) : -len(PATH_SUFFIX)]
    assert [delimiter for delimiter in SEGMENT_DELIMITERS if delimiter in segment] == [], segment
    assert unquote(string=segment) == value, segment


@settings(deadline=None)  # the first example also pays for importing the package
@given(items=st.lists(elements=TEXTS), mapping=st.dictionaries(keys=HASH_KEYS, values=TEXTS))
def test_array_and_hash_pairs(items: list[str], mapping: dict[str, str]) -> None:
    """AC-2.3: an array is its `k[]` pairs in order, a hash exactly its `k[key]` pairs, empty values included."""
    registry = load_registry()
    array_operation = one_query_parameter_operation(registry=registry, name="array", kind=registry.Kind.ARRAY)
    hash_operation = one_query_parameter_operation(registry=registry, name="hash", kind=registry.Kind.HASH)

    array_query = encoded_query(registry=registry, operation=array_operation, value=items)
    hash_query = encoded_query(registry=registry, operation=hash_operation, value=mapping)

    assert parse_qsl(qs=array_query, keep_blank_values=True) == [(ARRAY_PAIR_NAME, item) for item in items], array_query
    assert sorted(parse_qsl(qs=hash_query, keep_blank_values=True)) == sorted(
        (hash_pair_name(key=key), entry) for key, entry in mapping.items()
    ), hash_query


def load_errors() -> ModuleType:
    """Import `gitlab_api.errors` at test time, as `load_registry` imports the registry."""
    return importlib.import_module(name=ERRORS_MODULE)


def glob_operation(*, registry: ModuleType, name: str) -> Any:
    """A GET record whose path is `/projects/*glob/issues`."""
    return registry.RestOperation(operation_id=OPERATION_ID_PREFIX + name, method=METHOD_GET, path=GLOB_PATH_TEMPLATE)


@st.composite
def parts_with_a_refused_part(draw: st.DrawFn) -> list[str]:
    """`GLOB_PARTS` with `""`, `.` or `..` inserted at any position, both ends included, so the joined value has an
    empty part (a leading, trailing or doubled `/`), a `.` part or a `..` part."""
    parts = draw(strategy=GLOB_PARTS)
    refused = draw(strategy=st.sampled_from(elements=REFUSED_PARTS))
    position = draw(strategy=st.integers(min_value=0, max_value=len(parts)))
    return [*parts[:position], refused, *parts[position:]]


@settings(deadline=None)  # the first example also pays for importing the package
@given(parts=GLOB_PARTS)
@example(parts=["1.0", "rc 1"])
def test_glob_value_keeps_each_slash(parts: list[str]) -> None:
    """AC-2.1: a glob value, its parts joined by `/`, is written with each `/` kept and one piece per part, each piece
    a segment free of delimiters that decodes to its part."""
    registry = load_registry()
    operation = glob_operation(registry=registry, name="glob-keeps-each-slash")

    path = registry.expand(operation=operation, values={GLOB_PARAMETER: PART_SEPARATOR.join(parts)})

    assert path.startswith(PATH_PREFIX), path
    assert path.endswith(PATH_SUFFIX), path
    pieces = path[len(PATH_PREFIX) : -len(PATH_SUFFIX)].split(sep=PART_SEPARATOR)
    assert len(pieces) == len(parts), path
    assert [delimiter for piece in pieces for delimiter in SEGMENT_DELIMITERS if delimiter in piece] == [], path
    assert [unquote(string=piece) for piece in pieces] == parts, path


@settings(deadline=None)  # the first example also pays for importing the package
@given(parts=parts_with_a_refused_part())
@example(parts=["", "1.0"])
@example(parts=["1.0", ""])
@example(parts=["1.0", "", "rc 1"])
@example(parts=["1.0", ".", "rc 1"])
@example(parts=["1.0", "..", "rc 1"])
def test_a_glob_value_with_a_refused_part_is_refused(parts: list[str]) -> None:
    """AC-2.2: a glob value with an empty, `.` or `..` part anywhere — `/1.0`, `1.0/`, `1.0//rc 1`, `1.0/../rc 1` — is
    refused with `GitLabAPIError`."""
    registry = load_registry()
    errors = load_errors()
    operation = glob_operation(registry=registry, name="glob-refused-part")

    with pytest.raises(expected_exception=errors.GitLabAPIError):
        registry.expand(operation=operation, values={GLOB_PARAMETER: PART_SEPARATOR.join(parts)})


@settings(deadline=None)  # the first example also pays for importing the package
@given(prefix=st.text() | st.sampled_from(elements=NPM_ROUTE_PREFIXES))
@example(prefix="/packages/npm/")
@example(prefix="//packages/npm")
@example(prefix="https://other.example/packages/npm")
@example(prefix="")
def test_route_accepts_only_the_records_prefixes(prefix: str) -> None:
    """AC-2.4 and UB-2: `route` gives a declared npm value the path of that value followed by the dist-tags suffix,
    and refuses any other text — a trailing or doubled `/`, another origin, the empty text — with `ValueError`, so no
    text but a declared value reaches the path."""
    registry = load_registry()
    operation = registry.RestOperation(
        operation_id=OPERATION_ID_PREFIX + "route-prefix",
        method=METHOD_GET,
        path=DIST_TAGS_TEMPLATE,
        route_prefixes=NPM_ROUTE_PREFIXES,
    )

    if prefix in NPM_ROUTE_PREFIXES:
        routed = registry.route(operation=operation, prefix=prefix)
        assert routed.path == prefix + DIST_TAGS_SUFFIX, routed.path
    else:
        with pytest.raises(expected_exception=ValueError):
            registry.route(operation=operation, prefix=prefix)


def serving_one_family(*, registry: ModuleType, operations: Sequence[Any]) -> AbstractContextManager[Any]:
    """A patch making `registry.discover_families` return one synthetic family that declares `operations`, so `lookup`
    reads their records alone (R's `serve_families`). It is a context manager entered inside the test body, so each
    example Hypothesis runs restores the registry; a function-scoped `monkeypatch` would be shared by them all."""
    family = ModuleType(name=SYNTHETIC_FAMILY_MODULE)
    family.__dict__.update(FAMILY=SYNTHETIC_FAMILY, OPERATIONS=tuple(operations), PENDING=frozenset())

    def discover_families(*, package: ModuleType | None = None) -> tuple[ModuleType, ...]:
        return (family,)

    return patch.object(target=registry, attribute=DISCOVER_FAMILIES, new=discover_families)


@settings(deadline=None)  # the first example also pays for importing the package
@given(
    method=st.one_of(st.sampled_from(elements=ENDPOINT_METHODS), st.text()),
    path=st.one_of(st.sampled_from(elements=EMOJI_PATHS), st.text()),
)
@example(method="post", path=ISSUE_EMOJI_PATH)
@example(method=METHOD_POST, path="/Projects/:id/issues/:issue_iid/award_emoji")
@example(method=METHOD_POST, path=ISSUE_EMOJI_PATH + "/")
@example(method=METHOD_POST, path="/projects/:id/issues/:merge_request_iid/award_emoji")
@example(method=METHOD_POST, path=MERGE_REQUEST_EMOJI_PATH)
def test_only_a_declared_endpoint_is_chosen(method: str, path: str) -> None:
    """AC-2.4: of the records one ID declares, `lookup` given an endpoint returns the record whose method and path
    equal it as text, and refuses any other pair with `ValueError` — one differing only in case, by a trailing `/` or
    by a `:name` among them — so no endpoint but a declared one is chosen."""
    registry = load_registry()
    records = [
        registry.RestOperation(operation_id=ENDPOINT_OPERATION_ID, method=METHOD_POST, path=emoji_path)
        for emoji_path in EMOJI_PATHS
    ]
    declared = {(record.method, record.path): record for record in records}

    with serving_one_family(registry=registry, operations=records):
        if (method, path) in declared:
            chosen = registry.lookup(operation_id=ENDPOINT_OPERATION_ID, endpoint=(method, path))
            assert chosen == declared[(method, path)], chosen
        else:
            with pytest.raises(expected_exception=ValueError):
                registry.lookup(operation_id=ENDPOINT_OPERATION_ID, endpoint=(method, path))


@settings(deadline=None)  # the first example also pays for importing the package
@given(first=PLACE_VALUES, second=PLACE_VALUES)
@example(first="7", second="12345")
def test_each_place_takes_its_own_value(first: str, second: str) -> None:
    """AC-3.1 and AC-3.2: on a path that holds `:id` twice, `id` a name of the record's `positional_names`, `expand`
    writes the first value at the first place and the second at the second, each one segment, free of delimiters,
    that decodes to its value."""
    registry = load_registry()
    operation = registry.RestOperation(
        operation_id=OPERATION_ID_PREFIX + "delete-a-group-ssh-certificate",
        method=METHOD_DELETE,
        path=POSITIONAL_PATH_TEMPLATE,
        positional_names=(POSITIONAL_PARAMETER,),
    )

    path = registry.expand(operation=operation, values={POSITIONAL_PARAMETER: [first, second]})

    assert path.startswith(GROUPS_PREFIX), path
    segments = path[len(GROUPS_PREFIX) :].split(sep=CERTIFICATES_INFIX)
    assert len(segments) == PLACES, path
    assert [delimiter for segment in segments for delimiter in SEGMENT_DELIMITERS if delimiter in segment] == [], path
    assert [unquote(string=segment) for segment in segments] == [first, second], path


@settings(deadline=None)  # the first example also pays for importing the package
@given(value=st.one_of(st.sampled_from(elements=ARCHIVE_FORMATS), st.text()))
@example(value="ZIP")
@example(value="rar")
@example(value="")
def test_only_a_listed_format_reaches_the_path(value: str) -> None:
    """AC-4.2: `expand` writes the `[.format]` suffix as `.` and the value for each of the record's `suffix_values`,
    and refuses any other text — another case, an unlisted format, the empty text — with `ValueError`, so no text but a
    listed format reaches the path."""
    registry = load_registry()
    operation = registry.RestOperation(
        operation_id=OPERATION_ID_PREFIX + "retrieve-file-archive-from-a-repository",
        method=METHOD_GET,
        path=ARCHIVE_PATH_TEMPLATE,
        suffix_values=ARCHIVE_FORMATS,
    )
    values = {PATH_PARAMETER: ARCHIVE_PROJECT, SUFFIX_PARAMETER: value}

    if value in ARCHIVE_FORMATS:
        path = registry.expand(operation=operation, values=values)
        assert path == ARCHIVED_PATH + SUFFIX_SEPARATOR + value, path
    else:
        with pytest.raises(expected_exception=ValueError):
            registry.expand(operation=operation, values=values)


def scanned_sources() -> dict[str, str]:
    """The text of the entry script and of every module under the package, keyed by its POSIX path below `SCRIPTS`."""
    paths = [SCRIPTS / ENTRY_SCRIPT, *sorted(PACKAGE_DIRECTORY.rglob(pattern=MODULE_PATTERN))]
    return {path.relative_to(SCRIPTS).as_posix(): path.read_text(encoding="utf-8") for path in paths if path.is_file()}


def imported_names(*, source: str) -> list[str]:
    """The module every `import` and `from … import` of `source` names, top-level and nested; a relative import keeps
    its leading dots, so it is neither `gitlab_api…` nor a standard-library name."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source=source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append("." * node.level + (node.module or ""))
    return names


def is_allowed_import(*, name: str, standard_library: frozenset[str]) -> bool:
    """`gitlab_api` or one of its modules, or a module of a standard-library top-level package."""
    top_level = name.split(sep=".")[0]
    return top_level == PACKAGE_NAME or top_level in standard_library


def is_submodule_import(*, call: ast.Call) -> bool:
    """`<x>.import_module(name=f"{package.__name__}.{name}")`: a submodule of a package the module already holds, the
    discovery of `registry.discover_families` and of the entry script's `command_modules` (AC-1.2, design.md D6). It
    is the one dynamic import the scan admits: the package was imported by a statement the import scan checked."""
    arguments = [*call.args, *(keyword.value for keyword in call.keywords)]
    if not (isinstance(call.func, ast.Attribute) and call.func.attr == IMPORT_MODULE and len(arguments) == 1):
        return False
    name = arguments[0]
    if not (isinstance(name, ast.JoinedStr) and len(name.values) > 1):
        return False
    head, separator = name.values[0], name.values[1]
    return (
        isinstance(head, ast.FormattedValue)
        and isinstance(head.value, ast.Attribute)
        and head.value.attr == MODULE_NAME_ATTRIBUTE
        and isinstance(separator, ast.Constant)
        and separator.value == MODULE_SEPARATOR
    )


def refused_import(*, node: ast.Import | ast.ImportFrom) -> bool:
    """An `import` or `from … import` of an environment name or of a dynamic-import function: `from os import environ`,
    `from posix import getenv`, `from nt import putenv`, `from importlib import import_module` (an alias would hide
    every later call)."""
    named = {part for alias in node.names for part in alias.name.split(sep=MODULE_SEPARATOR)}
    return not named.isdisjoint(REFUSED_IMPORT_NAMES)


def refused_reference(*, node: ast.Name | ast.Attribute, call: ast.Call | None) -> bool:
    """A bare name or an attribute access (`environ`, `os.environ`, `__import__("os").environ`, `x.getenv`) naming an
    environment name, or naming `__import__` or `import_module` anywhere but as the function of a submodule import."""
    name = node.id if isinstance(node, ast.Name) else node.attr
    if name in ENVIRONMENT_NAMES:
        return True
    admitted = call is not None and is_submodule_import(call=call)
    return name in DYNAMIC_IMPORT_NAMES and not admitted


def environment_constructs(*, source: str) -> list[tuple[int, str]]:
    """The line and the construct of every refused import, name and attribute access of `source`, in walk order; a
    refused function is reported as the whole call it is the function of."""
    tree = ast.parse(source=source)
    calls: dict[ast.AST, ast.Call] = {node.func: node for node in ast.walk(tree) if isinstance(node, ast.Call)}
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and refused_import(node=node):
            found.append((node.lineno, ast.unparse(ast_obj=node)))
        elif isinstance(node, (ast.Name, ast.Attribute)) and refused_reference(node=node, call=calls.get(node)):
            found.append((node.lineno, ast.unparse(ast_obj=calls.get(node, node))))
    return found


def test_standard_library_only() -> None:
    """UB-2: the entry script and the package import only `gitlab_api…` and the standard library, and neither contains
    `os.environ` or `getenv`; the scanned set includes the entry script, the transport and the registry. The AST scan
    adds what the text search misses (refutation O1: `from os import environ`, `__import__("os").environ`): no import,
    bare name or attribute access of an environment name, and no `__import__` or `import_module` but the package's
    submodule discovery."""
    assert hasattr(sys, "stdlib_module_names"), f"sys.stdlib_module_names needs Python 3.10+; this is {sys.version}"
    standard_library = frozenset(sys.stdlib_module_names)
    sources = scanned_sources()

    foreign = [
        relative + ": " + name
        for relative, source in sources.items()
        for name in imported_names(source=source)
        if not is_allowed_import(name=name, standard_library=standard_library)
    ]
    environment_reads = [
        relative + ": " + marker
        for relative, source in sources.items()
        for marker in ENVIRONMENT_READS
        if marker in source
    ]
    constructs = [
        f"{relative}:{line}: {construct}"
        for relative, source in sources.items()
        for line, construct in environment_constructs(source=source)
    ]
    missing = [relative for relative in REQUIRED_SCANNED if relative not in sources]

    assert foreign == [], f"imports outside gitlab_api and the standard library: {foreign}"
    assert environment_reads == [], f"environment reads: {environment_reads}"
    assert constructs == [], f"environment names or dynamic imports: {constructs}"
    assert missing == [], f"missing from the scanned set {sorted(sources)}: {missing}"
