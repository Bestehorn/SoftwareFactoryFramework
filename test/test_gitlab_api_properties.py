"""Hypothesis properties of the GitLab wrapper package's request encoding (P of issue #13's design).

`registry.expand` puts a path value into a path template as ONE percent-encoded segment, `/` written `%2F` (AC-2.2;
`docs/api-reference/gitlab/conventions.md` "URL-encoding path parameters"). `registry.encode` turns an array into
`k[]=a&k[]=b` and a hash into `k[key]=v` (AC-2.3; `conventions.md` "Arrays, hashes and arrays of hashes"). The pairs
`encode` builds are joined here with `urllib.parse.urlencode(pairs, safe="[]", quote_via=urllib.parse.quote)`, the
join `Transport.request` applies (design.md D4), and read back with
`urllib.parse.parse_qsl(..., keep_blank_values=True)`, which keeps the empty values the strategies generate.

The properties live in this repository's own `test/`, where Hypothesis is a dev extra; the shipped `src/payload/test/`
stays pytest-only. `src/payload/scripts` is put on `sys.path`, and `gitlab_api` is imported inside each test, so the
module collects whether or not the package exists yet.

Run: ``python scripts/run_tests.py test/test_gitlab_api_properties.py``
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qsl, quote, unquote, urlencode

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
