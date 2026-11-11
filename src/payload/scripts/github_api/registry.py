"""The GitHub wrapper's operation records, their discovery, and the calls that send them (design D4).

A ``RestOperation`` is one row of ``operations-index.md`` as data: its operation ID, method and path template, the
query and body parameter names its reference section documents, the path parameters that may span several segments,
its paging kind and item key, its API version and media type. A ``GraphQLOperation`` is one capability of the
"Only in GraphQL" table. Records live in ``github_api/families/<family>.py`` (``FAMILY``, ``OPERATIONS``, ``PENDING``);
``discover_families`` finds every such module by being there, as the hook runtime's gate discovery finds a gate, so no
file lists them.

``send``, ``call`` and ``pages`` send a record through the ``Transport`` with its method, API version and media type:
``send`` returns the ``Response``, ``call`` its parsed JSON, ``pages`` the items of every page. A query or body name
the record does not document is refused with ``ValueError`` before anything is sent; a query name may end in ``[]``,
``conventions.md`` "Query strings"'s spelling of an array, and is sent as written. ``expand`` percent-encodes every
path value, refusing a ``.`` or ``..`` segment with ``GitHubAPIError``. Every caller-supplied value a message names is
rendered with ``json.dumps``.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import re
from dataclasses import dataclass
from enum import Enum
from types import ModuleType
from typing import AbstractSet, Any, FrozenSet, Iterator, List, Mapping, Optional, Tuple
from urllib.parse import quote

from github_api.errors import GitHubAPIError
from github_api.transport import Response, Transport

FAMILIES_PACKAGE = "github_api.families"
MODULE_SEPARATOR = "."
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PARAMETER_PATTERN = re.compile(r"\{([^{}]+)\}")
SEGMENT_SEPARATOR = "/"
SAFE_SINGLE_SEGMENT = ""
SAFE_MULTI_SEGMENT = SEGMENT_SEPARATOR
DOT_SEGMENTS = frozenset({".", ".."})
KIND_QUERY = "query"
KIND_BODY = "body"
#: How ``conventions.md`` "Query strings" spells an array query name: ``repository_ids[]=1&repository_ids[]=2``.
QUERY_ARRAY_SUFFIX = "[]"


class Paging(Enum):
    """How a list operation pages: not at all, or by the ``link`` header's ``rel="next"`` target, which carries the
    page number or the cursor, whichever the endpoint uses."""

    NONE = "none"
    LINK = "link"


@dataclass(frozen=True)
class RestOperation:
    """One REST operation of the index: the row's ``operation_id``, ``method`` and ``path`` template; the documented
    ``query_params`` and ``body_params``; the path parameters in ``multi_segment``, whose value keeps its ``/``; its
    ``paging``; the ``item_key`` a wrapped list's items sit under (``None`` for a bare list); ``api_version`` and
    ``accept``."""

    operation_id: str
    method: str
    path: str
    query_params: FrozenSet[str]
    body_params: FrozenSet[str]
    multi_segment: FrozenSet[str]
    paging: Paging
    item_key: Optional[str]
    api_version: str
    accept: str


@dataclass(frozen=True)
class GraphQLOperation:
    """One "Only in GraphQL" capability: its ``capability`` (the table's first cell, verbatim), the GraphQL
    ``document`` that serves it, and the key path of its ``connection`` under ``data``."""

    capability: str
    document: str
    connection: Tuple[str, ...]


def discover_families() -> List[ModuleType]:
    """Every module of ``github_api.families``, imported by its absolute name, in sorted name order. The package's
    ``__path__`` is read on each call, so a family is found by being in the directory."""
    package = importlib.import_module(name=FAMILIES_PACKAGE)
    names = sorted(module.name for module in pkgutil.iter_modules(path=package.__path__))
    return [importlib.import_module(name=f"{FAMILIES_PACKAGE}{MODULE_SEPARATOR}{name}") for name in names]


def lookup(operation_id: str) -> RestOperation:
    """The one record of every family's ``OPERATIONS`` with ``operation_id``; ``ValueError`` when no family declares
    it or it is declared more than once."""
    matches = [
        record
        for module in discover_families()
        for record in module.OPERATIONS
        if isinstance(record, RestOperation) and record.operation_id == operation_id
    ]
    if not matches:
        raise ValueError(f"No GitHub operation record declares {json.dumps(operation_id)}")
    if len(matches) > 1:
        raise ValueError(f"The GitHub operation {json.dumps(operation_id)} is declared {len(matches)} times")
    return matches[0]


def _encode_path_value(*, operation: RestOperation, name: str, value: Any) -> str:
    """``value`` as the path segment(s) of ``name``: percent-encoded with nothing safe, or with ``/`` safe for a
    ``multi_segment`` name; a ``.`` or ``..`` segment raises ``GitHubAPIError``."""
    text = str(value)
    multi = name in operation.multi_segment
    segments = text.split(SEGMENT_SEPARATOR) if multi else [text]
    if any(segment in DOT_SEGMENTS for segment in segments):
        raise GitHubAPIError(
            message=(
                f"Refusing the path parameter {json.dumps(name)} of {json.dumps(operation.operation_id)}: "
                f"{json.dumps(text)} has a '.' or '..' segment"
            )
        )
    return quote(string=text, safe=SAFE_MULTI_SEGMENT if multi else SAFE_SINGLE_SEGMENT)


def expand(operation: RestOperation, path_params: Mapping[str, Any]) -> str:
    """``operation``'s path with each ``{name}`` replaced by its encoded ``path_params`` value; a parameter the path
    names that ``path_params`` lacks raises ``ValueError``."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in path_params:
            raise ValueError(
                f"The GitHub operation {json.dumps(operation.operation_id)} needs the path parameter {json.dumps(name)}"
            )
        return _encode_path_value(operation=operation, name=name, value=path_params[name])

    return PATH_PARAMETER_PATTERN.sub(repl=replace, string=operation.path)


def path_parameters(*, operation: RestOperation) -> Tuple[str, ...]:
    """The names of the ``{name}`` placeholders of ``operation``'s path, in the order the path names them."""
    return tuple(match.group(1) for match in PATH_PARAMETER_PATTERN.finditer(string=operation.path))


def query_name(*, name: str) -> str:
    """The documented query name a given ``name`` stands for: ``name`` with one trailing ``[]`` removed."""
    return name[: -len(QUERY_ARRAY_SUFFIX)] if name.endswith(QUERY_ARRAY_SUFFIX) else name


def _documented_name(*, kind: str, name: str) -> str:
    """The name ``_check_names`` looks up in a record's ``kind`` parameters: a query name through ``query_name``, a
    body name as given."""
    return query_name(name=name) if kind == KIND_QUERY else name


def _check_names(
    *, operation: RestOperation, kind: str, given: Optional[Mapping[str, Any]], documented: AbstractSet[str]
) -> None:
    """Refuse with ``ValueError`` every ``given`` name that ``documented`` lacks, before anything is sent; a query
    name is compared through ``query_name`` and named in the message as given."""
    undocumented = sorted(name for name in (given or {}) if _documented_name(kind=kind, name=name) not in documented)
    if undocumented:
        raise ValueError(
            f"The GitHub operation {json.dumps(operation.operation_id)} documents no {kind} parameter "
            f"{json.dumps(undocumented)}; its {kind} parameters are {json.dumps(sorted(documented))}"
        )


def send(
    transport: Transport,
    operation_id: str,
    *,
    path_params: Mapping[str, Any],
    query: Optional[Mapping[str, Any]] = None,
    body: Optional[Mapping[str, Any]] = None,
) -> Response:
    """Send the record ``operation_id`` once, with its method, its expanded path, ``query``, ``body`` and the record's
    API version and media type, and return the transport's ``Response``. Its names and path are checked first, so a
    refusal comes before anything is sent."""
    operation = lookup(operation_id=operation_id)
    _check_names(operation=operation, kind=KIND_QUERY, given=query, documented=operation.query_params)
    _check_names(operation=operation, kind=KIND_BODY, given=body, documented=operation.body_params)
    path = expand(operation=operation, path_params=path_params)
    return transport.request(
        method=operation.method,
        path=path,
        query=query,
        body=body,
        api_version=operation.api_version,
        accept=operation.accept,
    )


def call(
    transport: Transport,
    operation_id: str,
    *,
    path_params: Mapping[str, Any],
    query: Optional[Mapping[str, Any]] = None,
    body: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Send the record ``operation_id`` once through ``send`` and return the response's parsed JSON (``None`` for an
    empty body)."""
    response = send(transport=transport, operation_id=operation_id, path_params=path_params, query=query, body=body)
    return response.json()


def pages(
    transport: Transport,
    operation_id: str,
    *,
    path_params: Mapping[str, Any],
    query: Optional[Mapping[str, Any]] = None,
) -> Iterator[Any]:
    """The items of every page of the list record ``operation_id``, in page order, each page asked for with the
    record's API version and media type. The record, its query names and its path are checked here, so a refusal
    comes before anything is sent."""
    operation = lookup(operation_id=operation_id)
    _check_names(operation=operation, kind=KIND_QUERY, given=query, documented=operation.query_params)
    path = expand(operation=operation, path_params=path_params)
    return transport.pages(
        path=path,
        query=query,
        item_key=operation.item_key,
        api_version=operation.api_version,
        accept=operation.accept,
    )
