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
- ``route`` writes the route prefix a call names into a record whose path starts with ``/<route-prefix>/``: the one of
  the record's ``route_prefixes`` equal to it, the text the record holds, in place of ``/<route-prefix>``. Any other
  text, or none, is refused for such a record, and any prefix for another record, which ``route`` returns itself when
  given none (issue #43, design.md D2).
- ``expand`` writes the path values into a record's path: a ``:name`` as ONE percent-encoded segment (AC-2.2), a
  ``*name`` glob with each ``/`` kept and each part between them such a segment; an optional ``(...)`` group is written
  only when its parameters have values, and a parenthesis the path escapes with a backslash is sent without it (issue
  #40, design.md D1). A name continues past a ``-`` that a name character follows (``:module-name``). A path that
  starts with ``/<route-prefix>/`` is refused before anything is written: it is expanded only once ``route`` has
  written its prefix (issue #43, design.md D1, D2).
- ``encode`` turns the other values into the query pairs, form pairs, JSON body and files of a request, arrays and
  hashes in GitLab's bracket form (AC-2.3; ``conventions.md`` "Arrays, hashes and arrays of hashes").
- ``attribute_name`` names the ``Param`` of a reference table name (``iids[]`` is ``iids``); ``variables`` names the
  variables a GraphQL record's document defines (issue #41, design.md D2), and ``upload_variables`` those of them
  whose type is ``Upload`` or a list of ``Upload``, each mapped to whether it is a list (issue #44, design.md D4).
- ``split_uploads`` takes the files out of a GraphQL call's variables, leaving ``None`` where each one goes, and pairs
  each file with the operations path it fills, for ``Transport.graphql``'s multipart request (issue #44, design.md D4).
- ``send`` sends one call of a REST record through a ``gitlab_api.transport.Transport`` and returns its ``Response``,
  the record first routed by ``route`` with the ``prefix`` it is given (issue #43, design.md D2): a record with a
  ``content_type`` through ``Transport.request_raw``, the bytes it is given as the body, any other through
  ``Transport.request`` (issue #40, design.md D5); ``call`` sends one call of any record and returns its
  value; ``pages`` returns the items of every page of a REST list record. Each looks the record up and encodes its
  values before anything is sent, so a value the record does not declare is refused with nothing sent (AC-1.1).

Standard library only; Python 3.9.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import re
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple, Union, overload
from urllib.parse import quote

import gitlab_api.families
from gitlab_api.errors import GitLabAPIError

if TYPE_CHECKING:
    # For the annotations only: gitlab_api.transport imports this module, so a run-time import would be a cycle.
    from gitlab_api.transport import Response, Transport

# A path parameter: `:name`, sent as ONE segment, at a segment start (`/projects/:id`) or inside one
# (`binary-:architecture`); or `*name`, a glob whose value keeps its `/` (#40 D1). A name continues past a `-` that a
# name character follows (`:module-name`); `:name-/` still ends before its `-`.
PLACEHOLDER = re.compile(pattern=r"(?P<sigil>[:*])(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*)")
GROUP_SIGIL = "sigil"
GROUP_NAME = "name"
GLOB_SIGIL = "*"
GLOB_SEPARATOR = "/"
# The template text a protocol route's path starts with, followed by SEGMENT_SEPARATOR, where its page lists the
# values it stands for (`rest/package.md`: "`<route-prefix>` on this page is one of: ..."); `route` writes one of the
# record's `route_prefixes` in its place (issue #43, design.md D2).
ROUTE_PREFIX = "/<route-prefix>"
SEGMENT_SEPARATOR = "/"
# How `route`'s refusal lists the record's route prefixes, and what it lists when the record holds none.
LIST_SEPARATOR = ", "
NOTHING_LISTED = "none"
# An optional group: an unescaped `(`, text with no parenthesis, an unescaped `)` — `(*path/)`.
OPTIONAL_GROUP = re.compile(pattern=r"(?<!\\)\((?P<inner>[^()]*)(?<!\\)\)")
GROUP_INNER = "inner"
# A parenthesis the path writes escaped, `\(` or `\)` (`Packages\(\)`), sent without its backslash.
ESCAPED_PARENTHESIS = re.compile(pattern=r"\\(?P<parenthesis>[()])")
GROUP_PARENTHESIS = "parenthesis"
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
    content_type: Optional[str] = None  # the media type of a body that is the bytes `call --input` gives
    route_prefixes: Tuple[str, ...] = ()  # on a path starting `/<route-prefix>/`, its page's values, in line order


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


# --- Route prefixes ---------------------------------------------------------------------------------------------


def takes_route_prefix(*, path: str) -> bool:
    """Whether ``path`` starts with ``ROUTE_PREFIX`` followed by ``/`` (issue #43, design.md D2)."""
    return path.startswith(ROUTE_PREFIX + SEGMENT_SEPARATOR)


@overload
def route(*, operation: RestOperation, prefix: Optional[str]) -> RestOperation: ...


@overload
def route(*, operation: GraphQLOperation, prefix: Optional[str]) -> GraphQLOperation: ...


def route(*, operation: Operation, prefix: Optional[str]) -> Operation:
    """The record a call of ``operation`` under the route prefix ``prefix`` sends (issue #43, design.md D2).

    A REST record whose path ``takes_route_prefix`` gives, for a ``prefix`` equal as text to one of its
    ``route_prefixes``, a ``dataclasses.replace`` copy whose path is that value followed by the path after
    ``ROUTE_PREFIX``: the text written is the value the record holds, and the caller's text only selects it. ``None``
    or any other text raises ``ValueError`` naming the ID, the text given rendered with ``json.dumps``, and each of
    the record's ``route_prefixes``. Any other record, a GraphQL record included, is returned itself for ``None``, and
    any text raises ``ValueError`` naming the ID and saying it takes no route prefix. The routed record is a value of
    the call; no family declares it."""
    if isinstance(operation, RestOperation) and takes_route_prefix(path=operation.path):
        for value in operation.route_prefixes:
            if value == prefix:
                # positional: replace takes its object positional-only
                return replace(operation, path=value + operation.path[len(ROUTE_PREFIX) :])
        listed = LIST_SEPARATOR.join(json.dumps(obj=value) for value in operation.route_prefixes) or NOTHING_LISTED
        if prefix is None:
            raise ValueError(
                f"{operation.operation_id!r} is sent under one of its route prefixes, {listed}, in place of "
                f"{ROUTE_PREFIX}; none was given"
            )
        raise ValueError(
            f"{operation.operation_id!r}: the route prefix {json.dumps(obj=prefix)} is none of its route prefixes, "
            f"{listed}"
        )
    if prefix is None:
        return operation
    raise ValueError(
        f"{operation.operation_id!r} takes no route prefix: its path does not start with "
        f"{ROUTE_PREFIX}{SEGMENT_SEPARATOR}"
    )


# --- Path expansion ---------------------------------------------------------------------------------------------


def placeholders(*, path: str) -> Tuple[str, ...]:
    """The path parameters of a path template, in order, without the sigil: every ``:name`` and every ``*name`` glob,
    inside an optional ``(...)`` group or not (issue #40, design.md D1). A name continues past a ``-`` that a name
    character follows, so ``:module-name`` is the one parameter ``module-name``, and ``:name-/`` is ``name`` (issue
    #43, design.md D1)."""
    return tuple(match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=path))


def required_placeholders(*, path: str) -> Tuple[str, ...]:
    """The path parameters a call must give: ``placeholders`` of the path with every optional ``(...)`` group removed
    (issue #40, design.md D1)."""
    return placeholders(path=OPTIONAL_GROUP.sub(repl="", string=path))


def _segment(*, name: str, values: Mapping[str, Any]) -> str:
    """The value of path parameter ``name`` as one percent-encoded segment."""
    value = values.get(name)
    if value is None:
        raise ValueError(f"no value for the path parameter :{name}")
    text = str(value)
    if text in REFUSED_SEGMENTS:
        raise GitLabAPIError(f"the path parameter :{name} is {text!r}, which is not one path segment")
    return quote(string=text, safe="")


def _glob(*, name: str, values: Mapping[str, Any]) -> str:
    """The value of the glob ``*name`` with each ``/`` kept, each part between them written as ``_segment`` writes one
    segment (issue #40, design.md D1)."""
    value = values.get(name)
    if value is None:
        raise ValueError(f"no value for the path parameter {GLOB_SIGIL}{name}")
    text = str(value)
    parts = text.split(sep=GLOB_SEPARATOR)
    for part in parts:
        if part in REFUSED_SEGMENTS:
            raise GitLabAPIError(
                f"the path parameter {GLOB_SIGIL}{name} is {text!r}, whose part {part!r} is not one path segment"
            )
    return GLOB_SEPARATOR.join(quote(string=part, safe="") for part in parts)


def expand(*, operation: RestOperation, values: Mapping[str, Any]) -> str:
    """The record's path with its values written in, in three steps (issue #40, design.md D1):

    1. each optional ``(...)`` group is written as the text between its parentheses when every path parameter in it has
       a value other than ``None``, and is left out whole otherwise;
    2. each parenthesis the path escapes with a backslash is written without the backslash;
    3. each ``:name`` is replaced by its value as ONE percent-encoded segment (AC-2.2), and each ``*name`` glob by its
       value with each ``/`` kept and each part between them such a segment.

    Steps 1 and 2 read the template alone, and of a value step 1 reads only whether it is given, so no value is read as
    a group, an escape or a parameter. ``quote(str(value), safe="")`` encodes ``/`` as well, so ``group/project``
    becomes ``group%2Fproject`` (``conventions.md`` "URL-encoding path parameters": the default ``safe="/"`` is
    wrong). An empty value, ``.`` and ``..``, and a glob part that is one of them, raise ``GitLabAPIError``; a path
    parameter without a value outside an optional group raises ``ValueError``.

    A path that ``takes_route_prefix`` raises ``ValueError`` before anything is written: a prefix record is expanded
    only once ``route`` has written its prefix, so ``pages``, which takes no prefix, sends no prefix path unrouted
    (issue #43, design.md D2)."""
    if takes_route_prefix(path=operation.path):
        raise ValueError(
            f"{operation.operation_id!r}: its path starts with {ROUTE_PREFIX}{SEGMENT_SEPARATOR}, so it is expanded "
            "only once route has written one of its route prefixes"
        )

    def group(match: re.Match[str]) -> str:
        inner = match.group(GROUP_INNER)
        given = all(values.get(name) is not None for name in placeholders(path=inner))
        return inner if given else ""

    def parenthesis(match: re.Match[str]) -> str:
        return match.group(GROUP_PARENTHESIS)

    def substitute(match: re.Match[str]) -> str:
        name = match.group(GROUP_NAME)
        if match.group(GROUP_SIGIL) == GLOB_SIGIL:
            return _glob(name=name, values=values)
        return _segment(name=name, values=values)

    template = OPTIONAL_GROUP.sub(repl=group, string=operation.path)
    template = ESCAPED_PARENTHESIS.sub(repl=parenthesis, string=template)
    return PLACEHOLDER.sub(repl=substitute, string=template)


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


def send(
    transport: Transport,
    operation_id: str,
    *,
    values: Optional[Mapping[str, Any]] = None,
    data: Optional[bytes] = None,
    prefix: Optional[str] = None,
) -> Response:
    """One call of the REST record declared with ``operation_id``, its ``Response`` returned (issue #41, design.md D2).

    The record is found with this module's ``lookup`` and, a GraphQL record refused, routed with ``route`` under
    ``prefix`` (issue #43, design.md D2): a record whose path starts with ``/<route-prefix>/`` is sent under the one of
    its ``route_prefixes`` that ``prefix`` equals, and a ``prefix`` for any other record, or a missing or unlisted one
    for such a record, raises ``route``'s ``ValueError`` before any request. The ``data`` check, ``encode``, ``expand``
    and the transport read the routed record. Its values are encoded and its path expanded first — a value it does not
    declare raises ``encode``'s ``ValueError`` before any request. A record whose ``content_type`` is ``None`` is then
    sent with ``transport.request``; any other with ``transport.request_raw``, ``data`` unchanged as its body under the
    record's ``content_type`` and its query pairs as its query (issue #40, design.md D5). A GraphQL record, and a
    ``data`` value for a record whose ``content_type`` is ``None``, raise ``ValueError`` with nothing sent."""
    operation = lookup(operation_id=operation_id)
    if not isinstance(operation, RestOperation):
        raise ValueError(f"{operation_id!r} is a GraphQL record; send sends REST records")
    operation = route(operation=operation, prefix=prefix)
    if operation.content_type is None and data is not None:
        raise ValueError(f"{operation_id!r} declares no content_type, so send sends no raw body for it")
    given: Mapping[str, Any] = values or {}
    encoded = encode(operation=operation, values=given)
    path = expand(operation=operation, values=given)
    if operation.content_type is not None:
        return transport.request_raw(
            method=operation.method,
            path=path,
            query=encoded.query,
            data=data,
            content_type=operation.content_type,
        )
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
