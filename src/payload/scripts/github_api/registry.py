"""The GitHub wrapper's operation records, their discovery, and the calls that send them (design D4).

A ``RestOperation`` is one row of ``operations-index.md`` as data: its operation ID, method and path template, the
query and body parameter names its reference section documents, the path parameters that may span several segments,
its paging kind and item key, its API version and media type, the ``root`` its path is sent under (``API_ROOT`` unless
its section names another host) and, for a body that is not JSON, that body's ``content_type`` (``None`` for every
record whose body is JSON). A ``GraphQLOperation`` is one GraphQL operation serving a capability of the "Only in
GraphQL" table: its ``graphql/<member>`` operation ID, the capability, the document, and the key path of the
connection it pages (``()`` when it pages none); a capability may have several. REST records live in
``github_api/families/<family>.py`` (``FAMILY``, ``OPERATIONS``, ``PENDING``); ``discover_families`` finds every such
module by being there, as the hook runtime's gate discovery finds a gate, so no file lists them. GraphQL records live
in ``github_api/graphql_only.py``; ``graphql_lookup`` finds one by its ID, and ``declared_variables`` names the
variables its document defines that a caller gives.

``send``, ``call`` and ``pages`` send a record through the ``Transport`` with its method, API version and media type:
``send`` returns the ``Response``, ``call`` its parsed JSON, ``pages`` the items of every page. ``send`` takes one of
two paths: a record whose ``content_type`` is ``None`` goes through ``Transport.request``, its body as JSON, to
``API_ROOT``, and raw ``data`` for it is refused with ``ValueError`` before anything is sent; any other record goes
through ``Transport.request_raw``, ``data`` unchanged under the record's ``content_type``, to the record's ``root``. A
query or body name the record does not document is refused with ``ValueError`` before anything is sent; a query name
may end in ``[]``, ``conventions.md`` "Query strings"'s spelling of an array, and is sent as written. A record whose
``body_params`` holds ``ANY_BODY_NAME`` (``*``, a section's "any key" body) documents every body name, so each body
member given is sent; its query names and path parameters are checked as every record's are. ``expand``
percent-encodes every path value, refusing a ``.`` or ``..`` segment with ``GitHubAPIError``. Every caller-supplied
value a message names is rendered with ``json.dumps``.
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
from github_api.transport import API_ROOT, FIELD_AFTER, Response, Transport

FAMILIES_PACKAGE = "github_api.families"
#: The operation ID prefix of every GraphQL record: ``graphql/`` and the member it runs (design D2).
GRAPHQL_ID_PREFIX = "graphql/"
#: A GraphQL variable definition: ``$``, a Name, then ``:`` after any white space (``VariableDefinition : Variable :
#: Type``). A use of the variable as an argument value (``owner: $owner)``) has no ``:`` after it.
VARIABLE_DEFINITION_PATTERN = re.compile(r"\$([_A-Za-z][_0-9A-Za-z]*)\s*:")
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
#: The body name of a section whose body takes any key (``*``, "any key"): a record's ``body_params`` holding it
#: documents every body name. It stands for body names only; query and path names stay checked.
ANY_BODY_NAME = "*"


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
    ``accept``; the ``root`` the path is sent under; and ``content_type``, the media type of a body that is not JSON
    (``None`` when the body is JSON)."""

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
    root: str = API_ROOT
    content_type: Optional[str] = None


@dataclass(frozen=True)
class GraphQLOperation:
    """One GraphQL operation serving an "Only in GraphQL" capability: its ``operation_id`` (``graphql/<member>``), the
    ``capability`` it serves (the table's first cell, verbatim), its GraphQL ``document``, and the key path of the
    ``connection`` it pages under ``data`` (``()`` when it pages none)."""

    operation_id: str
    capability: str
    document: str
    connection: Tuple[str, ...] = ()


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


def graphql_lookup(*, operation_id: str) -> GraphQLOperation:
    """The one record of ``graphql_only.OPERATIONS`` with ``operation_id``; ``ValueError`` naming the ID when no
    record declares it or it is declared more than once."""
    # Imported here, not at the top: graphql_only imports this module's GraphQLOperation.
    from github_api import graphql_only

    declared: Tuple[object, ...] = graphql_only.OPERATIONS
    matches = [
        record for record in declared if isinstance(record, GraphQLOperation) and record.operation_id == operation_id
    ]
    if not matches:
        raise ValueError(f"No GitHub GraphQL record declares {json.dumps(operation_id)}")
    if len(matches) > 1:
        raise ValueError(f"The GitHub GraphQL record {json.dumps(operation_id)} is declared {len(matches)} times")
    return matches[0]


def declared_variables(*, operation: GraphQLOperation) -> Tuple[str, ...]:
    """The names of the variables ``operation``'s document defines, in document order: each ``$name`` followed,
    after any white space, by ``:``. A record with a ``connection`` leaves out ``after``, which
    ``Transport.graphql_nodes`` sets on every page."""
    defined = tuple(match.group(1) for match in VARIABLE_DEFINITION_PATTERN.finditer(string=operation.document))
    if not operation.connection:
        return defined
    return tuple(name for name in defined if name != FIELD_AFTER)


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
    name is compared through ``query_name`` and named in the message as given. A body whose ``documented`` names hold
    ``ANY_BODY_NAME`` accepts every name; a query's ``documented`` names never do."""
    if kind == KIND_BODY and ANY_BODY_NAME in documented:
        return
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
    data: Optional[bytes] = None,
) -> Response:
    """Send the record ``operation_id`` once, with its method, its expanded path, ``query`` and the record's API
    version and media type, and return the transport's ``Response``. A record whose ``content_type`` is ``None`` sends
    ``body`` as JSON to ``API_ROOT``, and ``data`` for it raises ``ValueError``; any other record sends ``data``, its
    bytes unchanged under the record's ``content_type`` (no body when ``data`` is ``None``), to the record's ``root``.
    Its ``data``, names and path are checked first, so a refusal comes before anything is sent."""
    operation = lookup(operation_id=operation_id)
    if operation.content_type is None and data is not None:
        raise ValueError(
            f"The GitHub operation {json.dumps(operation.operation_id)} takes a JSON body: it sends no raw bytes"
        )
    _check_names(operation=operation, kind=KIND_QUERY, given=query, documented=operation.query_params)
    _check_names(operation=operation, kind=KIND_BODY, given=body, documented=operation.body_params)
    path = expand(operation=operation, path_params=path_params)
    if operation.content_type is None:
        return transport.request(
            method=operation.method,
            path=path,
            query=query,
            body=body,
            api_version=operation.api_version,
            accept=operation.accept,
        )
    return transport.request_raw(
        method=operation.method,
        root=operation.root,
        path=path,
        query=query,
        data=data,
        content_type=operation.content_type,
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


def graphql_call(transport: Transport, operation_id: str, *, variables: Mapping[str, Any]) -> Any:
    """Send the GraphQL record ``operation_id`` with ``variables``: for a record with a ``connection``, the nodes of
    every page in page order, collected before they are returned; for any other record, the response's ``data``. A
    variable the record does not declare (``declared_variables``) is refused with ``ValueError`` before anything is
    sent, as ``_check_names`` refuses an undocumented name."""
    operation = graphql_lookup(operation_id=operation_id)
    declared = declared_variables(operation=operation)
    undeclared = sorted(name for name in variables if name not in declared)
    if undeclared:
        raise ValueError(
            f"The GitHub GraphQL record {json.dumps(obj=operation.operation_id)} declares no variable "
            f"{json.dumps(obj=undeclared)}; its variables are {json.dumps(obj=list(declared))}"
        )
    if operation.connection:
        return list(
            transport.graphql_nodes(document=operation.document, variables=variables, connection=operation.connection)
        )
    return transport.graphql(document=operation.document, variables=variables)
