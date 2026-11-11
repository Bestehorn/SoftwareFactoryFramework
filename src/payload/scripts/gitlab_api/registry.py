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
  Several REST records of one family may declare one id, each on its own endpoint, the base record first: given an
  ``endpoint``, ``(method, path)``, ``lookup`` returns the record on it and refuses any other, and given none it returns
  the first declared (issue #63, design.md D1).
- ``base_of`` reads where a path is sent: under ``/api/v4`` (``Base.REST``), at the configured host's root for a path
  starting ``https://HOST/`` (``Base.HOST``), or to the container registry for one starting
  ``/http(s)://${CI_REGISTRY}/`` (``Base.CONTAINER_REGISTRY``), whose ``${NAME}`` parts are path parameters; the path
  functions read the rest after that root (issue #63, design.md D4).
- ``route`` writes the route prefix a call names into a record whose path starts with ``/<route-prefix>/``: the one of
  the record's ``route_prefixes`` equal to it, the text the record holds, in place of ``/<route-prefix>``. Any other
  text, or none, is refused for such a record, and any prefix for another record, which ``route`` returns itself when
  given none (issue #43, design.md D2).
- ``expand`` writes the path values into a record's path: a ``:name`` as ONE percent-encoded segment (AC-2.2), a
  ``*name`` glob with each ``/`` kept and each part between them such a segment; an optional ``(...)`` group is written
  only when its parameters have values, and a parenthesis the path escapes with a backslash is sent without it (issue
  #40, design.md D1). A name continues past a ``-`` that a name character follows (``:module-name``). A path that
  starts with ``/<route-prefix>/`` is refused before anything is written: it is expanded only once ``route`` has
  written its prefix (issue #43, design.md D1, D2). A ``[.name]`` suffix is written as ``.`` and one of the record's
  ``suffix_values`` when given and as nothing otherwise (issue #63, design.md D3); each place of a name in the record's
  ``positional_names`` takes its own item of the list given for it (D2); a ``${NAME}`` of a container-registry path is
  written as a glob (D4).
- ``encode`` turns the other values into the query pairs, form pairs, JSON body, files and request headers of a
  request, arrays and hashes in GitLab's bracket form (AC-2.3; ``conventions.md`` "Arrays, hashes and arrays of
  hashes"); a header value holding CR, LF or NUL is refused by ``check_header_value`` (issue #63, design.md D5).
- ``attribute_name`` names the ``Param`` of a reference table name (``iids[]`` is ``iids``); ``variables`` names the
  variables a GraphQL record's document defines (issue #41, design.md D2), and ``upload_variables`` those of them
  whose type is ``Upload`` or a list of ``Upload``, each mapped to whether it is a list (issue #44, design.md D4).
- ``split_uploads`` takes the files out of a GraphQL call's variables, leaving ``None`` where each one goes, and pairs
  each file with the operations path it fills, for ``Transport.graphql``'s multipart request (issue #44, design.md D4).
- ``send`` sends one call of a REST record through a ``gitlab_api.transport.Transport`` and returns its ``Response``,
  the record first routed by ``route`` with the ``prefix`` it is given (issue #43, design.md D2): a record with a
  ``content_type`` through ``Transport.request_raw``, the bytes it is given as the body, any other through
  ``Transport.request`` (issue #40, design.md D5), each under the record's base, and a container-registry record
  through ``gitlab_api.container_registry.send`` (issue #63, design.md D4); ``call`` sends one call of any record and
  returns its value; ``pages`` returns the items of every page of a REST list record under ``/api/v4``. Each looks the
  record up, by its endpoint when one is given, and encodes its values before anything is sent, so a value the record
  does not declare is refused with nothing sent (AC-1.1).

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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)
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
# An optional suffix, `[.name]` (`archive[.format]`): the path parameter `name`, written as `.` and one of the record's
# `suffix_values`, or as nothing (issue #63, design.md D3).
OPTIONAL_SUFFIX = re.compile(pattern=r"\[\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)\]")
SUFFIX_SEPARATOR = "."
# The roots of the paths the index does not write under `/api/v4` (operations-index.md: "paths are relative to
# `https://HOST/api/v4` unless they start with `https://HOST`"; rest/package.md "Container registry API"), each
# followed by SEGMENT_SEPARATOR; `base_of` reads them (issue #63, design.md D4).
HOST_ROOT = "https://HOST"
CONTAINER_REGISTRY_ROOT = "/http(s)://${CI_REGISTRY}"
# A path parameter of a container-registry path, and a part of its `token_scope`: `${NAME}` (design.md D4).
CONTAINER_REGISTRY_NAME = re.compile(pattern=r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}")
# How an endpoint `(method, path)` is written: `METHOD path`, as `call --endpoint` takes it (issue #63, design.md D1).
ENDPOINT_SEPARATOR = " "
# RFC 9110 section 5.5: "Field values containing CR, LF, or NUL characters are invalid and dangerous".
REFUSED_HEADER_CHARACTERS = ("\r", "\n", "\0")
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
# An endpoint of a record: its method and its path, verbatim as the index writes them (issue #63, design.md D1).
Endpoint = Tuple[str, str]


class Location(Enum):
    """Where a declared attribute is sent; a path attribute comes from the path template instead. A HEADER attribute
    is a request header its section documents, sent under the name the section spells (issue #63, design.md D5)."""

    QUERY = "query"
    BODY = "body"
    HEADER = "header"


class Base(Enum):
    """Where a record's path is sent (issue #63, design.md D4): under ``https://<hostname>/api/v4``, under
    ``https://<hostname>`` outside the API, or to the container registry with a registry token."""

    REST = "rest"
    HOST = "host"
    CONTAINER_REGISTRY = "container_registry"


# Each base but REST with the root its paths start with; `base_of` reads them in this order.
BASE_ROOTS: Tuple[Tuple[Base, str], ...] = ((Base.HOST, HOST_ROOT), (Base.CONTAINER_REGISTRY, CONTAINER_REGISTRY_ROOT))


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
    # Each `:name` the path holds more than once that takes one value per place, in path order (issue #63, D2).
    positional_names: Tuple[str, ...] = ()
    # The values of the path's `[.name]` suffix, verbatim from its docs page (issue #63, design.md D3).
    suffix_values: Tuple[str, ...] = ()
    # On a container-registry path, the scope its registry token is asked for, `${NAME}` the call's value (D4).
    token_scope: Optional[str] = None


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

    ``query``, ``form``, ``files`` and ``headers`` are name-value pairs in the order they are sent; ``json_body`` is
    ``None`` when the request carries no JSON body. ``headers`` are the request headers of the record's ``HEADER``
    attributes (issue #63, design.md D5)."""

    query: Tuple[Pair, ...] = ()
    form: Tuple[Pair, ...] = ()
    json_body: Optional[Dict[str, Any]] = None
    files: Tuple[Tuple[str, Path], ...] = ()
    headers: Tuple[Pair, ...] = ()


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


def _endpoint_text(*, endpoint: Endpoint) -> str:
    """An endpoint written ``METHOD path``, as ``call --endpoint`` takes it (issue #63, design.md D1)."""
    method, path = endpoint
    return f"{method}{ENDPOINT_SEPARATOR}{path}"


def _endpoint_records(*, declarations: Sequence[Tuple[str, Operation]]) -> bool:
    """Whether the declarations of one id are D1's records of one Reference: REST records, all of one family, each on
    its own ``(method, path)`` (issue #63, design.md D1)."""
    sources = {source for source, _ in declarations}
    keys = [(record.method, record.path) for _, record in declarations if isinstance(record, RestOperation)]
    return len(sources) == 1 and len(keys) == len(declarations) and len(set(keys)) == len(keys)


def lookup(*, operation_id: str, endpoint: Optional[Endpoint] = None) -> Operation:
    """The record declared with ``operation_id`` on ``endpoint``, over every family module and ``graphql_only`` (issue
    #63, design.md D1).

    The families are discovered on every call; the registry keeps no index of its own. An id no record declares raises
    ``ValueError`` naming it, and so does an id that more than one source declares (two families, or a family and
    ``graphql_only``) or that two records of one family declare on one ``(method, path)``: "declared … times". The REST
    records of one family that declare an id are its endpoints, the first declared its base endpoint: ``endpoint``
    ``None`` gives the first, an ``endpoint`` equal to a record's ``(method, path)`` that record, and any other raises
    ``ValueError`` naming the id, the text given (``json.dumps``) and each declared endpoint, ``METHOD path``, in
    declaration order. A GraphQL record is returned for ``None``, and an ``endpoint`` for it raises ``ValueError``
    saying it takes none."""
    declarations = list(_declarations(operation_id=operation_id))
    if not declarations:
        raise ValueError(
            f"unknown operation id {operation_id!r}: no family module and no graphql_only record declares it"
        )
    if len(declarations) > 1 and not _endpoint_records(declarations=declarations):
        sources = ", ".join(source for source, _ in declarations)
        raise ValueError(f"operation id {operation_id!r} is declared {len(declarations)} times, by: {sources}")
    records = [record for _, record in declarations]
    if endpoint is None:
        return records[0]
    given = json.dumps(obj=_endpoint_text(endpoint=endpoint))
    rest_records = [record for record in records if isinstance(record, RestOperation)]
    if not rest_records:
        raise ValueError(f"{operation_id!r} is a GraphQL record, which takes no endpoint; {given} was given")
    for record in rest_records:
        if (record.method, record.path) == endpoint:
            return record
    listed = LIST_SEPARATOR.join(_endpoint_text(endpoint=(record.method, record.path)) for record in rest_records)
    raise ValueError(f"{operation_id!r}: the endpoint {given} is none of its endpoints, {listed}")


def _record_of(*, operation_id: str, endpoint: Optional[Endpoint]) -> Operation:
    """``lookup`` of ``operation_id``, its ``endpoint`` passed only when one is given: ``lookup(operation_id=...)``
    alone for ``None``, so every call without an endpoint looks a record up as on #43's base (design.md D1)."""
    if endpoint is None:
        return lookup(operation_id=operation_id)
    return lookup(operation_id=operation_id, endpoint=endpoint)


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


def base_of(*, path: str) -> Tuple[Base, str]:
    """Where ``path`` is sent and the rest of it (issue #63, design.md D4): ``(Base.HOST, rest)`` for a path starting
    ``HOST_ROOT`` and ``/``, ``(Base.CONTAINER_REGISTRY, rest)`` for one starting ``CONTAINER_REGISTRY_ROOT`` and ``/``,
    the rest being the path after the root, and ``(Base.REST, path)`` for any other."""
    for base, root in BASE_ROOTS:
        if path.startswith(root + SEGMENT_SEPARATOR):
            return base, path[len(root) :]
    return Base.REST, path


def _parameter_names(*, base: Base, rest: str) -> Tuple[str, ...]:
    """The path parameters of ``rest``, the part of a path ``base_of`` gives for ``base``, in path order: each
    ``:name`` and ``*name``, each ``[.name]`` suffix and, in a container-registry rest, each ``${NAME}``."""
    patterns = [PLACEHOLDER, OPTIONAL_SUFFIX]
    if base is Base.CONTAINER_REGISTRY:
        patterns.append(CONTAINER_REGISTRY_NAME)
    matches = sorted(
        (match for pattern in patterns for match in pattern.finditer(string=rest)), key=lambda match: match.start()
    )
    return tuple(match.group(GROUP_NAME) for match in matches)


def placeholders(*, path: str) -> Tuple[str, ...]:
    """The path parameters of a path template, in order, without the sigil: every ``:name`` and every ``*name`` glob,
    inside an optional ``(...)`` group or not (issue #40, design.md D1). A name continues past a ``-`` that a name
    character follows, so ``:module-name`` is the one parameter ``module-name``, and ``:name-/`` is ``name`` (issue
    #43, design.md D1). Only the rest of the path after its ``base_of`` root is read; each ``[.name]`` suffix is a
    parameter too, and so is each ``${NAME}`` of a container-registry path (issue #63, design.md D3, D4)."""
    base, rest = base_of(path=path)
    return _parameter_names(base=base, rest=rest)


def required_placeholders(*, path: str) -> Tuple[str, ...]:
    """The path parameters a call must give: ``placeholders`` of the path with every optional ``(...)`` group and every
    ``[.name]`` suffix removed (issue #40, design.md D1; issue #63, design.md D3)."""
    base, rest = base_of(path=path)
    required = OPTIONAL_SUFFIX.sub(repl="", string=OPTIONAL_GROUP.sub(repl="", string=rest))
    return _parameter_names(base=base, rest=required)


def check_header_value(*, name: str, value: str) -> None:
    """Refuse a request header value holding CR, LF or NUL with ``ValueError`` naming the header and never quoting the
    value (RFC 9110 section 5.5; issue #63, design.md D5). ``encode`` and the transport's request builder call it."""
    if any(character in value for character in REFUSED_HEADER_CHARACTERS):
        raise ValueError(
            f"the request header {name!r} has a value holding CR, LF or NUL, which no header value may hold "
            "(RFC 9110 section 5.5)"
        )


def _segment(*, name: str, values: Mapping[str, Any]) -> str:
    """The value of path parameter ``name`` as one percent-encoded segment."""
    value = values.get(name)
    if value is None:
        raise ValueError(f"no value for the path parameter :{name}")
    text = str(value)
    if text in REFUSED_SEGMENTS:
        raise GitLabAPIError(f"the path parameter :{name} is {text!r}, which is not one path segment")
    return quote(string=text, safe="")


def _glob(*, name: str, values: Mapping[str, Any], written: str) -> str:
    """The value of the glob ``name`` with each ``/`` kept, each part between them written as ``_segment`` writes one
    segment (issue #40, design.md D1); ``written`` is the parameter as the path writes it, ``*name`` or a container
    registry's ``${NAME}`` (issue #63, design.md D4), for the refusals."""
    value = values.get(name)
    if value is None:
        raise ValueError(f"no value for the path parameter {written}")
    text = str(value)
    parts = text.split(sep=GLOB_SEPARATOR)
    for part in parts:
        if part in REFUSED_SEGMENTS:
            raise GitLabAPIError(
                f"the path parameter {written} is {text!r}, whose part {part!r} is not one path segment"
            )
    return GLOB_SEPARATOR.join(quote(string=part, safe="") for part in parts)


def _described(*, value: Any) -> str:
    """What a positional refusal says it was given: no value, the number of items, or the value's type."""
    if value is None:
        return "no value"
    if _is_array(value=value):
        return f"{len(value)} values"
    return f"a {type(value).__name__}"


def _place_values(*, operation: RestOperation, template: str, values: Mapping[str, Any]) -> Dict[str, Iterator[Any]]:
    """For each name of the record's ``positional_names`` that ``template`` holds, an iterator over the list or tuple
    given for it, its k-th item the value of the k-th place in path order (issue #63, design.md D2). Any other shape,
    and a number of items other than the number of places, raise ``ValueError`` naming the name and its places."""
    held = [match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=template)]
    items: Dict[str, Iterator[Any]] = {}
    for name in operation.positional_names:
        places = held.count(name)
        if not places:
            continue
        value = values.get(name)
        if not isinstance(value, (list, tuple)) or len(value) != places:
            raise ValueError(
                f"{operation.operation_id!r}: the path parameter :{name} is written at {places} places, so it takes a "
                f"list of {places} values, one per place in path order; it was given {_described(value=value)}"
            )
        items[name] = iter(value)
    return items


def _suffix(*, operation: RestOperation, name: str, values: Mapping[str, Any]) -> str:
    """Step 0 of ``expand`` for the suffix ``[.name]``: ``.`` and its value, verbatim, for one of the record's
    ``suffix_values``, nothing when it has no value, and ``ValueError`` naming the values for any other (issue #63,
    design.md D3)."""
    value = values.get(name)
    if value is None:
        return ""
    if value not in operation.suffix_values:
        listed = LIST_SEPARATOR.join(json.dumps(obj=listed_value) for listed_value in operation.suffix_values)
        raise ValueError(
            f"{operation.operation_id!r}: the path parameter {name} is {json.dumps(obj=str(value))}, which is none of "
            f"its values, {listed or NOTHING_LISTED}"
        )
    return SUFFIX_SEPARATOR + str(value)


def expand(*, operation: RestOperation, values: Mapping[str, Any]) -> str:
    """The rest of the record's path after its ``base_of`` root (issue #63, design.md D4) with its values written in,
    in four steps (issue #40, design.md D1; issue #63, design.md D2, D3):

    0. each ``[.name]`` suffix is written as ``.`` and its value, verbatim, when the value is one of the record's
       ``suffix_values``, and as nothing when it has none (absent or ``None``); any other value raises ``ValueError``
       naming the values;
    1. each optional ``(...)`` group is written as the text between its parentheses when every path parameter in it has
       a value other than ``None``, and is left out whole otherwise;
    2. each parenthesis the path escapes with a backslash is written without the backslash;
    3. each ``:name`` is replaced by its value as ONE percent-encoded segment (AC-2.2), and each ``*name`` glob by its
       value with each ``/`` kept and each part between them such a segment. A name of the record's
       ``positional_names`` takes a list or tuple of one value per place, the k-th place written from the k-th item;
       any other shape or length raises ``ValueError`` naming the name and its places. In a container-registry rest,
       each ``${NAME}`` is then written as a glob.

    Steps 1 and 2 read the template alone, and of a value step 1 reads only whether it is given, so no value is read as
    a group, an escape or a parameter; step 0 writes only a listed value, which is letters, digits and ``.``, and step
    3 writes only percent-encoded parts and ``/``, so neither is read as a parameter by a later step.
    ``quote(str(value), safe="")`` encodes ``/`` as well, so ``group/project`` becomes ``group%2Fproject``
    (``conventions.md`` "URL-encoding path parameters": the default ``safe="/"`` is wrong). An empty value, ``.`` and
    ``..``, and a glob part that is one of them, raise ``GitLabAPIError``; a path parameter without a value outside an
    optional group and the suffix raises ``ValueError``.

    A path that ``takes_route_prefix`` raises ``ValueError`` before anything is written: a prefix record is expanded
    only once ``route`` has written its prefix, so ``pages``, which takes no prefix, sends no prefix path unrouted
    (issue #43, design.md D2)."""
    if takes_route_prefix(path=operation.path):
        raise ValueError(
            f"{operation.operation_id!r}: its path starts with {ROUTE_PREFIX}{SEGMENT_SEPARATOR}, so it is expanded "
            "only once route has written one of its route prefixes"
        )
    base, rest = base_of(path=operation.path)

    def suffix(match: re.Match[str]) -> str:
        return _suffix(operation=operation, name=match.group(GROUP_NAME), values=values)

    def group(match: re.Match[str]) -> str:
        inner = match.group(GROUP_INNER)
        given = all(values.get(name) is not None for name in _parameter_names(base=base, rest=inner))
        return inner if given else ""

    def parenthesis(match: re.Match[str]) -> str:
        return match.group(GROUP_PARENTHESIS)

    template = OPTIONAL_SUFFIX.sub(repl=suffix, string=rest)
    template = OPTIONAL_GROUP.sub(repl=group, string=template)
    template = ESCAPED_PARENTHESIS.sub(repl=parenthesis, string=template)
    places = _place_values(operation=operation, template=template, values=values)

    def substitute(match: re.Match[str]) -> str:
        name = match.group(GROUP_NAME)
        place = places.get(name)
        written: Mapping[str, Any] = values if place is None else {name: next(place)}
        if match.group(GROUP_SIGIL) == GLOB_SIGIL:
            return _glob(name=name, values=written, written=match.group(0))
        return _segment(name=name, values=written)

    def registry_name(match: re.Match[str]) -> str:
        return _glob(name=match.group(GROUP_NAME), values=values, written=match.group(0))

    expanded = PLACEHOLDER.sub(repl=substitute, string=template)
    if base is Base.CONTAINER_REGISTRY:
        expanded = CONTAINER_REGISTRY_NAME.sub(repl=registry_name, string=expanded)
    return expanded


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


def _header(*, param: Param, value: Any) -> Pair:
    """One request header: the declared name and the value as ``_text`` writes it, refused by ``check_header_value``
    when it holds CR, LF or NUL (issue #63, design.md D5)."""
    text = _text(value=value)
    check_header_value(name=param.name, value=text)
    return param.name, text


def encode(*, operation: RestOperation, values: Mapping[str, Any]) -> EncodedRequest:
    """The query pairs, form pairs, JSON body, files and request headers of one call of ``operation`` (AC-2.3).

    ``values`` holds the path values (``expand`` reads them; they are skipped here) and the declared attributes.
    QUERY values become pairs by ``Kind``, followed by the record's ``fixed`` values. BODY values become form pairs the
    same way when the record's body is FORM or a FILE value is passed (the body is then multipart, design.md D4), and
    otherwise a JSON body holding each value natively. FILE values (``pathlib.Path``) are the ``files``. HEADER values
    are the ``headers``, each under its declared name, in the caller's order, and in no query, form or JSON body; a
    value holding CR, LF or NUL raises ``ValueError`` (issue #63, design.md D5)."""
    given = _declared_values(operation=operation, values=values)
    files = tuple((param.name, value) for param, value in given if param.kind is Kind.FILE)
    sent = [(param, value) for param, value in given if param.kind is not Kind.FILE]
    query = tuple(_all_pairs(given=sent, location=Location.QUERY)) + operation.fixed
    headers = tuple(_header(param=param, value=value) for param, value in sent if param.location is Location.HEADER)
    if operation.body is BodyFormat.FORM or files:
        form = tuple(_all_pairs(given=sent, location=Location.BODY))
        return EncodedRequest(query=query, form=form, files=files, headers=headers)
    body = {param.name: value for param, value in sent if param.location is Location.BODY}
    return EncodedRequest(query=query, json_body=body or None, headers=headers)


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


def _scope(*, operation: RestOperation, values: Mapping[str, Any]) -> str:
    """The scope a container-registry record's registry token is asked for: its ``token_scope`` with each ``${NAME}``
    written as the call's value of ``NAME``, as given (issue #63, design.md D4). A record that declares no
    ``token_scope``, and a ``${NAME}`` given no value, raise ``ValueError``."""
    scope = operation.token_scope
    if scope is None:
        raise ValueError(f"{operation.operation_id!r} is sent to the container registry but declares no token_scope")

    def substitute(match: re.Match[str]) -> str:
        value = values.get(match.group(GROUP_NAME))
        if value is None:
            raise ValueError(f"{operation.operation_id!r}: its token_scope names {match.group(0)}, given no value")
        return str(value)

    return CONTAINER_REGISTRY_NAME.sub(repl=substitute, string=scope)


def _send_to_container_registry(
    *,
    transport: Transport,
    operation: RestOperation,
    encoded: EncodedRequest,
    path: str,
    values: Mapping[str, Any],
    data: Optional[bytes],
    project: Optional[str],
) -> Response:
    """One call of a container-registry record through ``container_registry.send``: its method, its expanded path
    after ``CONTAINER_REGISTRY_ROOT``, its query, its ``_scope`` and the configured ``project`` (issue #63, design.md
    D4). No ``project``, and a body, a file, a request header or raw bytes, which a registry request does not carry,
    raise ``ValueError`` before any request."""
    if project is None:
        raise ValueError(
            f"{operation.operation_id!r} is sent to the container registry, whose registry token is asked for with "
            "the configured project; send was given no project"
        )
    if data is not None or encoded.form or encoded.files or encoded.json_body is not None or encoded.headers:
        raise ValueError(
            f"{operation.operation_id!r} is sent to the container registry, which send gives a query and no body, file "
            "or request header"
        )
    scope = _scope(operation=operation, values=values)
    # Imported here, not at the top: gitlab_api.container_registry imports this module.
    from gitlab_api import container_registry

    return container_registry.send(
        transport=transport,
        method=operation.method,
        path=path,
        query=encoded.query,
        scope=scope,
        project=project,
    )


def send(
    transport: Transport,
    operation_id: str,
    *,
    values: Optional[Mapping[str, Any]] = None,
    data: Optional[bytes] = None,
    prefix: Optional[str] = None,
    endpoint: Optional[Endpoint] = None,
    project: Optional[str] = None,
) -> Response:
    """One call of the REST record declared with ``operation_id``, its ``Response`` returned (issue #41, design.md D2).

    The record is found with this module's ``lookup``, on ``endpoint`` when one is given (issue #63, design.md D1),
    and, a GraphQL record refused, routed with ``route`` under ``prefix`` (issue #43, design.md D2): a record whose
    path starts with ``/<route-prefix>/`` is sent under the one of its ``route_prefixes`` that ``prefix`` equals, and a
    ``prefix`` for any other record, or a missing or unlisted one for such a record, raises ``route``'s ``ValueError``
    before any request. The ``data`` check, ``encode``, ``expand`` and the transport read the routed record. Its values
    are encoded and its path expanded first — a value it does not declare raises ``encode``'s ``ValueError`` before any
    request. A record whose path ``base_of`` reads as ``Base.CONTAINER_REGISTRY`` is then sent through
    ``container_registry.send`` with the configured ``project``, which it needs (issue #63, design.md D4). Any other
    record whose ``content_type`` is ``None`` is sent with ``transport.request``; any other with
    ``transport.request_raw``, ``data`` unchanged as its body under the record's ``content_type`` and its query pairs as
    its query (issue #40, design.md D5); each under the record's base and with its request headers (issue #63,
    design.md D4, D5). A GraphQL record, and a ``data`` value for a record whose ``content_type`` is ``None``, raise
    ``ValueError`` with nothing sent."""
    operation = _record_of(operation_id=operation_id, endpoint=endpoint)
    if not isinstance(operation, RestOperation):
        raise ValueError(f"{operation_id!r} is a GraphQL record; send sends REST records")
    operation = route(operation=operation, prefix=prefix)
    if operation.content_type is None and data is not None:
        raise ValueError(f"{operation_id!r} declares no content_type, so send sends no raw body for it")
    given: Mapping[str, Any] = values or {}
    encoded = encode(operation=operation, values=given)
    path = expand(operation=operation, values=given)
    base, _ = base_of(path=operation.path)
    if base is Base.CONTAINER_REGISTRY:
        return _send_to_container_registry(
            transport=transport,
            operation=operation,
            encoded=encoded,
            path=path,
            values=given,
            data=data,
            project=project,
        )
    if operation.content_type is not None:
        return transport.request_raw(
            method=operation.method,
            path=path,
            query=encoded.query,
            data=data,
            content_type=operation.content_type,
            base=base,
            headers=encoded.headers,
        )
    return transport.request(
        method=operation.method,
        path=path,
        query=encoded.query,
        form=encoded.form,
        json_body=encoded.json_body,
        files=encoded.files,
        base=base,
        headers=encoded.headers,
    )


def call(
    transport: Transport,
    operation_id: str,
    *,
    values: Optional[Mapping[str, Any]] = None,
    endpoint: Optional[Endpoint] = None,
) -> Any:
    """One call of the record declared with ``operation_id``, its result decoded (design.md D5).

    A ``RestOperation`` is sent with ``send`` and its ``Response.value`` returned. A ``GraphQLOperation`` sends its
    document with ``values`` as the variables, through ``transport.graphql_nodes`` when it names a connection and
    ``transport.graphql`` otherwise; without a connection the files are first taken out of the values with
    ``split_uploads`` and sent as ``transport.graphql``'s ``files`` (issue #44, design.md D4), so no ``Path`` is
    written into the JSON of the request. The record is found with this module's ``lookup``, on ``endpoint`` when one
    is given (issue #63, design.md D1)."""
    operation = _record_of(operation_id=operation_id, endpoint=endpoint)
    if isinstance(operation, RestOperation):
        return send(transport=transport, operation_id=operation_id, values=values, endpoint=endpoint).value
    given: Mapping[str, Any] = values or {}
    if operation.connection:
        return transport.graphql_nodes(document=operation.document, variables=given, connection=operation.connection)
    sent, files = split_uploads(values=given)
    return transport.graphql(document=operation.document, variables=sent, files=files)


def pages(
    transport: Transport,
    operation_id: str,
    *,
    values: Optional[Mapping[str, Any]] = None,
    endpoint: Optional[Endpoint] = None,
) -> Iterator[Any]:
    """The items of every page of the REST list record declared with ``operation_id``: the generator
    ``transport.pages`` returns for the record's path, query and ``paging`` (design.md D5).

    The record is looked up, on ``endpoint`` when one is given (issue #63, design.md D1), and its values encoded and
    expanded before the generator is returned, so a refused value raises here. A GraphQL record, a record whose path
    ``base_of`` does not read as ``Base.REST`` (issue #63, design.md D4), a record whose method is not ``GET``, and
    body values and request headers raise ``ValueError``: a page is fetched with a ``GET`` under ``/api/v4`` that
    carries a query only."""
    operation = _record_of(operation_id=operation_id, endpoint=endpoint)
    if not isinstance(operation, RestOperation):
        raise ValueError(f"{operation_id!r} is a GraphQL record; pages reads REST list records")
    base, _ = base_of(path=operation.path)
    if base is not Base.REST:
        raise ValueError(f"{operation_id!r}: pages reads list records under /api/v4, and its base is {base.value}")
    given: Mapping[str, Any] = values or {}
    encoded = encode(operation=operation, values=given)
    if (
        operation.method != LIST_METHOD
        or encoded.form
        or encoded.files
        or encoded.json_body is not None
        or encoded.headers
    ):
        raise ValueError(
            f"{operation_id!r}: pages sends {LIST_METHOD} requests, which carry a query and no body or request header"
        )
    path = expand(operation=operation, values=given)
    return transport.pages(path=path, query=encoded.query, paging=operation.paging)
