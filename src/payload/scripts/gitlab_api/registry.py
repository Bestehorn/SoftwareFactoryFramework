"""The operation records of the GitLab wrapper and the functions that read them (issue #13, design.md D5).

A ``RestOperation`` is one row of ``docs/api-reference/gitlab/operations-index.md``, transcribed from the attribute
table of its ``rest/<family>.md`` section: the method, the path verbatim (``/projects/:id/issues/:issue_iid``), and one
``Param`` per query or body attribute, the table's Type column as a ``Kind``. A ``GraphQLOperation`` is one query or
mutation of a GraphQL-only capability (``gitlab_api/graphql_only.py``), which it names by the first cell of the "Only in
GraphQL" row it serves (issue #41, design.md D2); several records may serve one capability (issue #44, design.md D1).
The REST records live in the endpoint family modules of
``gitlab_api.families``, each holding ``FAMILY`` (its file stem), ``OPERATIONS`` and ``PENDING`` (the
``(method, path)`` keys of the family's index rows that no record maps yet); ``discover_families`` finds them by
scanning the package, so no file lists them.

- ``lookup`` returns the record declared with an id (``plan#update-an-issue``), over every family and ``graphql_only``.
- ``expand`` writes the path values into a record's path, each as ONE percent-encoded segment (AC-2.2).
- ``encode`` turns the other values into the query pairs, form pairs, JSON body and files of a request, arrays and
  hashes in GitLab's bracket form (AC-2.3; ``conventions.md`` "Arrays, hashes and arrays of hashes").
- ``attribute_name`` names the ``Param`` of a reference table name (``iids[]`` is ``iids``); ``variables`` names the
  variables a GraphQL record's document defines (issue #41, design.md D2), and ``upload_variables`` those of them
  whose type is ``Upload`` or a list of ``Upload``, each mapped to whether it is a list (issue #44, design.md D4).
- ``split_uploads`` takes the files out of a GraphQL call's variables, leaving ``None`` where each one goes, and pairs
  each file with the operations path it fills, for ``Transport.graphql``'s multipart request (issue #44, design.md D4).
- ``send`` sends one call of a REST record through a ``gitlab_api.transport.Transport`` and returns its ``Response``;
  ``call`` sends one call of any record and returns its value; ``pages`` returns the items of every page of a REST list
  record. Each looks the record up and encodes its values before anything is sent, so a value the record does not
  declare is refused with nothing sent (AC-1.1).

Standard library only; Python 3.9.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple, Union
from urllib.parse import quote

import gitlab_api.families
from gitlab_api.errors import GitLabAPIError

if TYPE_CHECKING:
    # For the annotations only: gitlab_api.transport imports this module, so a run-time import would be a cycle.
    from gitlab_api.transport import Response, Transport

# A path parameter: `:` and an identifier, at a segment start (`/projects/:id`) or inside one (`binary-:architecture`).
PLACEHOLDER = re.compile(r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# A GraphQL variable definition: `$`, a Name, then `:` after any white space (`VariableDefinition : Variable : Type`).
# A use of the variable (`fullPath: $fullPath)`) has no `:` after it.
VARIABLE_DEFINITION = re.compile(r"\$(?P<name>[_A-Za-z][_0-9A-Za-z]*)\s*:")
# The Type of a variable definition, read where a VARIABLE_DEFINITION match ends (`Type : NamedType | ListType |
# NonNullType`): white space, then any `[` and white space, a Name, and any `]`, `!` and white space (`[Upload!]!`).
TYPE_REFERENCE = re.compile(pattern=r"\s*(?P<type>[\[\s]*[_A-Za-z][_0-9A-Za-z]*[\]!\s]*)")
GROUP_TYPE = "type"
# What `upload_variables` removes from a Type before comparing it with UPLOAD_TYPE.
TYPE_DECORATION = re.compile(pattern=r"[\[\]!\s]")
UPLOAD_TYPE = "Upload"
LIST_TYPE_START = "["
# Joins the parts of an operations path: `variables`, the variable name and, for a list item, its index.
OPERATIONS_PATH_SEPARATOR = "."
# None of these is one segment once a URL's dot segments are resolved (RFC 3986 section 5.2.4).
REFUSED_SEGMENTS = frozenset({"", ".", ".."})
ARRAY_SUFFIX = "[]"
BOOLEAN_TRUE = "true"
BOOLEAN_FALSE = "false"
GRAPHQL_ONLY_SOURCE = "graphql_only"
# The method of every page request `pages` sends (`Transport.pages`).
LIST_METHOD = "GET"

Pair = Tuple[str, str]


class Location(Enum):
    """Where a declared attribute is sent; a path attribute comes from the path template instead."""

    QUERY = "query"
    BODY = "body"


class Kind(Enum):
    """How a value is encoded — the Type column of the attribute's reference table."""

    SCALAR = "scalar"
    ARRAY = "array"
    HASH = "hash"
    ARRAY_OF_HASHES = "array_of_hashes"
    FILE = "file"


class BodyFormat(Enum):
    """How the BODY values of a request are sent; any FILE value makes the body multipart instead."""

    JSON = "json"
    FORM = "form"


class Paging(Enum):
    """How a list endpoint pages: not at all, by offset (``Link`` or ``x-next-page``), or by keyset (``Link`` only)."""

    NONE = "none"
    OFFSET = "offset"
    KEYSET = "keyset"


@dataclass(frozen=True)
class Param:
    """One query or body attribute of a record, as its reference table spells and types it."""

    name: str
    location: Location
    kind: Kind = Kind.SCALAR
    required: bool = False


@dataclass(frozen=True)
class RestOperation:
    """One REST endpoint: its id (the row's Reference target without ``rest/`` and ``.md``), method and path."""

    operation_id: str
    method: str
    path: str
    params: Tuple[Param, ...] = ()
    body: BodyFormat = BodyFormat.JSON
    paging: Paging = Paging.NONE
    fixed: Tuple[Pair, ...] = ()  # query values the endpoint requires on every call


@dataclass(frozen=True)
class GraphQLOperation:
    """One query or mutation of a GraphQL-only capability: the first cell of the "Only in GraphQL" row it serves,
    verbatim, its document and, for a paged connection, the key path to it under ``data``. Several records may serve
    one capability (issue #44, design.md D1)."""

    operation_id: str
    capability: str
    document: str
    connection: Tuple[str, ...] = ()


Operation = Union[RestOperation, GraphQLOperation]


@dataclass(frozen=True)
class EncodedRequest:
    """The values of one call, split into the keyword arguments of ``Transport.request`` (design.md D4).

    ``query``, ``form`` and ``files`` are name-value pairs in the order they are sent; ``json_body`` is ``None`` when
    the request carries no JSON body."""

    query: Tuple[Pair, ...] = ()
    form: Tuple[Pair, ...] = ()
    json_body: Optional[Dict[str, Any]] = None
    files: Tuple[Tuple[str, Path], ...] = ()


# --- Discovery and lookup ---------------------------------------------------------------------------------------

_DISCOVERED: Dict[str, Tuple[ModuleType, ...]] = {}


def discover_families(*, package: Optional[ModuleType] = None) -> Tuple[ModuleType, ...]:
    """Every module of a families package (``gitlab_api.families`` by default), sorted by module name.

    The modules are found with ``pkgutil.iter_modules`` over the package's ``__path__`` and imported by absolute
    name, so a family is added by writing its module and nothing else (the pattern of ``src/hooks/hooks.py``
    ``discover_gates``). The result is kept per package name: the first call for a package scans it."""
    scanned = gitlab_api.families if package is None else package
    cached = _DISCOVERED.get(scanned.__name__)
    if cached is not None:
        return cached
    # A module written after an earlier import in this process is invisible to the path finder's cached directory
    # listing until the caches are dropped.
    importlib.invalidate_caches()
    names = sorted(info.name for info in pkgutil.iter_modules(path=scanned.__path__))
    modules = tuple(importlib.import_module(name=f"{scanned.__name__}.{name}") for name in names)
    _DISCOVERED[scanned.__name__] = modules
    return modules


def _declarations(*, operation_id: str) -> Iterator[Tuple[str, Operation]]:
    """Every record declared with ``operation_id``, with the family (or ``graphql_only``) that declares it."""
    # Imported here, not at the top: graphql_only imports this module's record types.
    from gitlab_api import graphql_only

    for family in discover_families():
        yield from ((str(family.FAMILY), record) for record in family.OPERATIONS if record.operation_id == operation_id)
    yield from (
        (GRAPHQL_ONLY_SOURCE, record) for record in graphql_only.OPERATIONS if record.operation_id == operation_id
    )


def lookup(*, operation_id: str) -> Operation:
    """The one record declared with ``operation_id``, over every family module and ``graphql_only``.

    The families are discovered on every call; the registry keeps no index of its own. An id no record declares, and
    an id more than one record declares, raise ``ValueError`` naming it."""
    declarations = list(_declarations(operation_id=operation_id))
    if not declarations:
        raise ValueError(
            f"unknown operation id {operation_id!r}: no family module and no graphql_only record declares it"
        )
    if len(declarations) > 1:
        sources = ", ".join(source for source, _ in declarations)
        raise ValueError(f"operation id {operation_id!r} is declared {len(declarations)} times, by: {sources}")
    return declarations[0][1]


# --- Path expansion ---------------------------------------------------------------------------------------------


def placeholders(*, path: str) -> Tuple[str, ...]:
    """The ``:name`` path parameters of a path template, in order, without the colon."""
    return tuple(match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=path))


def _segment(*, name: str, values: Mapping[str, Any]) -> str:
    """The value of path parameter ``name`` as one percent-encoded segment."""
    value = values.get(name)
    if value is None:
        raise ValueError(f"no value for the path parameter :{name}")
    text = str(value)
    if text in REFUSED_SEGMENTS:
        raise GitLabAPIError(f"the path parameter :{name} is {text!r}, which is not one path segment")
    return quote(string=text, safe="")


def expand(*, operation: RestOperation, values: Mapping[str, Any]) -> str:
    """The record's path with every ``:name`` replaced by its value as ONE percent-encoded segment (AC-2.2).

    ``quote(str(value), safe="")`` encodes ``/`` as well, so ``group/project`` becomes ``group%2Fproject``
    (``conventions.md`` "URL-encoding path parameters": the default ``safe="/"`` is wrong). An empty value, ``.`` and
    ``..`` raise ``GitLabAPIError``; a path parameter without a value raises ``ValueError``."""

    def substitute(match: re.Match[str]) -> str:
        return _segment(name=match.group(GROUP_NAME), values=values)

    return PLACEHOLDER.sub(repl=substitute, string=operation.path)


# --- Attribute and variable names -------------------------------------------------------------------------------


def attribute_name(*, name: str) -> str:
    """The ``Param`` name a reference table name stands for: ``name`` without ONE trailing ``[]``, so ``iids[]`` is
    ``iids`` (``Kind.ARRAY`` writes the suffix itself, ``_pairs``); ``not[labels]`` is unchanged (issue #41, D2)."""
    return name.removesuffix(ARRAY_SUFFIX)


def variables(*, operation: GraphQLOperation) -> Tuple[str, ...]:
    """The name of every variable the record's document defines — each ``$name`` followed, after any white space, by
    ``:`` — in document order (issue #41, design.md D2).

    A record with a ``connection`` leaves out the cursor ``transport.FIELD_AFTER``: ``Transport.graphql_nodes`` sets it
    on every page (#13 AC-4.2)."""
    # Imported here, not at the top: gitlab_api.transport imports this module.
    from gitlab_api.transport import FIELD_AFTER

    defined = tuple(match.group(GROUP_NAME) for match in VARIABLE_DEFINITION.finditer(string=operation.document))
    if not operation.connection:
        return defined
    return tuple(name for name in defined if name != FIELD_AFTER)


def upload_variables(*, operation: GraphQLOperation) -> Dict[str, bool]:
    """Each variable the record's document defines whose type, with ``[``, ``]``, ``!`` and white space removed, is
    ``Upload``, mapped to whether that type is a list (it begins with ``[``): ``$files: [Upload!]!`` is ``True``,
    ``$file: Upload`` is ``False`` (issue #44, design.md D4).

    The types are read from the ``$name: Type`` definitions where ``variables`` reads the names; a variable of any
    other type is left out."""
    uploads: Dict[str, bool] = {}
    for definition in VARIABLE_DEFINITION.finditer(string=operation.document):
        reference = TYPE_REFERENCE.match(string=operation.document, pos=definition.end())
        if reference is None:
            continue
        type_text = reference.group(GROUP_TYPE)
        if TYPE_DECORATION.sub(repl="", string=type_text) == UPLOAD_TYPE:
            uploads[definition.group(GROUP_NAME)] = type_text.startswith(LIST_TYPE_START)
    return uploads


# --- Value encoding ---------------------------------------------------------------------------------------------


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float))


def _is_array(value: Any) -> bool:
    return isinstance(value, (list, tuple))


# The value shape each Kind accepts; anything else would be encoded into pairs that mean something else (a string
# given for an ARRAY would be sent one character per `name[]` pair).
KIND_ACCEPTS: Dict[Kind, Callable[[Any], bool]] = {
    Kind.SCALAR: _is_scalar,
    Kind.ARRAY: _is_array,
    Kind.HASH: lambda value: isinstance(value, Mapping),
    Kind.ARRAY_OF_HASHES: lambda value: _is_array(value) and all(isinstance(item, Mapping) for item in value),
    Kind.FILE: lambda value: isinstance(value, Path),
}


def _declared_values(*, operation: RestOperation, values: Mapping[str, Any]) -> List[Tuple[Param, Any]]:
    """The non-path values with their ``Param``, in the caller's order; a value of ``None`` is not sent.

    A name that is neither a path parameter nor a declared ``Param``, and a value whose shape its ``Kind`` does not
    accept, raise ``ValueError`` naming it."""
    path_names = frozenset(placeholders(path=operation.path))
    declared = {param.name: param for param in operation.params}
    given: List[Tuple[Param, Any]] = []
    for name, value in values.items():
        if name in path_names:
            continue
        param = declared.get(name)
        if param is None:
            raise ValueError(f"{operation.operation_id}: {name!r} is neither a path parameter nor a declared attribute")
        if value is None:
            continue
        if not KIND_ACCEPTS[param.kind](value):
            raise ValueError(
                f"{operation.operation_id}: {name!r} is declared {param.kind.value}, not a {type(value).__name__}"
            )
        given.append((param, value))
    return given


def _text(*, value: Any) -> str:
    """A scalar as GitLab reads it in a query string or a form body: booleans as ``true`` and ``false``."""
    if isinstance(value, bool):
        return BOOLEAN_TRUE if value else BOOLEAN_FALSE
    return str(value)


def _pairs(*, param: Param, value: Any) -> Iterator[Pair]:
    """The name-value pairs of one value by its ``Kind``: ``name=v``, ``name[]=v``, ``name[k]=v``, ``name[0][k]=v``."""
    name = param.name
    if param.kind is Kind.ARRAY:
        yield from ((name + ARRAY_SUFFIX, _text(value=item)) for item in value)
    elif param.kind is Kind.HASH:
        yield from ((f"{name}[{key}]", _text(value=entry)) for key, entry in value.items())
    elif param.kind is Kind.ARRAY_OF_HASHES:
        for index, item in enumerate(value):
            yield from ((f"{name}[{index}][{key}]", _text(value=entry)) for key, entry in item.items())
    else:
        yield (name, _text(value=value))


def _all_pairs(*, given: List[Tuple[Param, Any]], location: Location) -> List[Pair]:
    """The pairs of every value sent in ``location``, in the caller's order."""
    return [pair for param, value in given if param.location is location for pair in _pairs(param=param, value=value)]


def encode(*, operation: RestOperation, values: Mapping[str, Any]) -> EncodedRequest:
    """The query pairs, form pairs, JSON body and files of one call of ``operation`` (AC-2.3).

    ``values`` holds the path values (``expand`` reads them; they are skipped here) and the declared attributes.
    QUERY values become pairs by ``Kind``, followed by the record's ``fixed`` values. BODY values become form pairs the
    same way when the record's body is FORM or a FILE value is passed (the body is then multipart, design.md D4), and
    otherwise a JSON body holding each value natively. FILE values (``pathlib.Path``) are the ``files``."""
    given = _declared_values(operation=operation, values=values)
    files = tuple((param.name, value) for param, value in given if param.kind is Kind.FILE)
    sent = [(param, value) for param, value in given if param.kind is not Kind.FILE]
    query = tuple(_all_pairs(given=sent, location=Location.QUERY)) + operation.fixed
    if operation.body is BodyFormat.FORM or files:
        return EncodedRequest(query=query, form=tuple(_all_pairs(given=sent, location=Location.BODY)), files=files)
    body = {param.name: value for param, value in sent if param.location is Location.BODY}
    return EncodedRequest(query=query, json_body=body or None)


def split_uploads(*, values: Mapping[str, Any]) -> Tuple[Dict[str, Any], Tuple[Tuple[str, Path], ...]]:
    """The variables of a GraphQL call with its files taken out, and the files (issue #44, design.md D4).

    Each ``pathlib.Path`` value, and each ``Path`` item of a list, is replaced by ``None``, the ``null`` the
    ``operations`` part of a multipart request holds where a file goes; every other value is unchanged. The files follow
    in the order of the values and of each list, each with the operations path it fills: ``variables.<name>``, or
    ``variables.<name>.<index>`` for a list item. ``Transport.graphql`` sends them in one multipart request."""
    # Imported here, not at the top: gitlab_api.transport imports this module.
    from gitlab_api.transport import FIELD_VARIABLES

    sent: Dict[str, Any] = {}
    files: List[Tuple[str, Path]] = []
    for name, value in values.items():
        operations_path = f"{FIELD_VARIABLES}{OPERATIONS_PATH_SEPARATOR}{name}"
        if isinstance(value, Path):
            files.append((operations_path, value))
            sent[name] = None
        elif _is_array(value) and any(isinstance(item, Path) for item in value):
            files.extend(
                (f"{operations_path}{OPERATIONS_PATH_SEPARATOR}{index}", item)
                for index, item in enumerate(value)
                if isinstance(item, Path)
            )
            sent[name] = [None if isinstance(item, Path) else item for item in value]
        else:
            sent[name] = value
    return sent, tuple(files)


# --- Calls ------------------------------------------------------------------------------------------------------


def send(transport: Transport, operation_id: str, *, values: Optional[Mapping[str, Any]] = None) -> Response:
    """One call of the REST record declared with ``operation_id``, its ``Response`` returned (issue #41, design.md D2).

    The record is found with this module's ``lookup``, its values encoded and its path expanded first — a value it does
    not declare raises ``encode``'s ``ValueError`` before any request — and then sent with ``transport.request``. A
    GraphQL record raises ``ValueError`` with nothing sent."""
    operation = lookup(operation_id=operation_id)
    if not isinstance(operation, RestOperation):
        raise ValueError(f"{operation_id!r} is a GraphQL record; send sends REST records")
    given: Mapping[str, Any] = values or {}
    encoded = encode(operation=operation, values=given)
    path = expand(operation=operation, values=given)
    return transport.request(
        method=operation.method,
        path=path,
        query=encoded.query,
        form=encoded.form,
        json_body=encoded.json_body,
        files=encoded.files,
    )


def call(transport: Transport, operation_id: str, *, values: Optional[Mapping[str, Any]] = None) -> Any:
    """One call of the record declared with ``operation_id``, its result decoded (design.md D5).

    A ``RestOperation`` is sent with ``send`` and its ``Response.value`` returned. A ``GraphQLOperation`` sends its
    document with ``values`` as the variables, through ``transport.graphql_nodes`` when it names a connection and
    ``transport.graphql`` otherwise; without a connection the files are first taken out of the values with
    ``split_uploads`` and sent as ``transport.graphql``'s ``files`` (issue #44, design.md D4), so no ``Path`` is
    written into the JSON of the request. The record is found with this module's ``lookup``."""
    operation = lookup(operation_id=operation_id)
    if isinstance(operation, RestOperation):
        return send(transport=transport, operation_id=operation_id, values=values).value
    given: Mapping[str, Any] = values or {}
    if operation.connection:
        return transport.graphql_nodes(document=operation.document, variables=given, connection=operation.connection)
    sent, files = split_uploads(values=given)
    return transport.graphql(document=operation.document, variables=sent, files=files)


def pages(transport: Transport, operation_id: str, *, values: Optional[Mapping[str, Any]] = None) -> Iterator[Any]:
    """The items of every page of the REST list record declared with ``operation_id``: the generator
    ``transport.pages`` returns for the record's path, query and ``paging`` (design.md D5).

    The record is looked up and its values encoded and expanded before the generator is returned, so a refused value
    raises here. A GraphQL record, a record whose method is not ``GET``, and body values raise ``ValueError``: a page
    is fetched with a ``GET`` that carries a query only."""
    operation = lookup(operation_id=operation_id)
    if not isinstance(operation, RestOperation):
        raise ValueError(f"{operation_id!r} is a GraphQL record; pages reads REST list records")
    given: Mapping[str, Any] = values or {}
    encoded = encode(operation=operation, values=given)
    if operation.method != LIST_METHOD or encoded.form or encoded.files or encoded.json_body is not None:
        raise ValueError(f"{operation_id!r}: pages sends {LIST_METHOD} requests, which carry a query and no body")
    path = expand(operation=operation, values=given)
    return transport.pages(path=path, query=encoded.query, paging=operation.paging)
