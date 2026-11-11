"""The GitLab wrapper's operation call, ``call <operation-id>`` (issue #41, design.md D1 to D4): any record that a
family module of ``gitlab_api/families/`` or ``gitlab_api/graphql_only.py`` declares, sent by its operation ID.

The grammar (D2)::

    python scripts/gitlab_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
        [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]... [--file NAME=PATH]...

- ``<operation-id>``: a record's ID, ``<stem>#<anchor>`` for a REST record (``plan#retrieve-a-project-issue``) and
  ``graphql#<field>`` for a GraphQL record.
- ``--path NAME=VALUE``: a path parameter, as text, written by ``registry.expand`` as ONE percent-encoded segment. On a
  record whose path is ``/projects/:id`` or starts with ``/projects/:id/``, an ``id`` the call does not give is the
  configured project (``project_id`` of ``config/gitlab.json``); no other ``:id`` has a default.
- ``--query NAME=VALUE``: an attribute the record declares in the query, as text. The values of one name are collected
  in the order given: a list for an ``ARRAY`` attribute, even with one value, and the one string for any other
  ``Kind`` (a repeated name becomes a list, which the shape check refuses).
- ``-f/--raw-field NAME=TEXT``: an attribute of either location, the string TEXT as its value.
- ``-F/--field NAME=JSON``: an attribute of either location, the value ``json.loads`` parses: a number, a boolean, an
  array, an object or a quoted string. Text that is not JSON is refused; ``NaN``, ``Infinity`` and ``-Infinity``,
  which plain ``json.loads`` takes outside the JSON grammar, are such text. ``null`` is accepted, but a REST attribute
  of ``None`` is not sent (``registry.encode``); a GraphQL variable sends it.
- ``--file NAME=PATH``: a ``FILE`` attribute, ``pathlib.Path(PATH)`` as its value. The transport reads the file when it
  builds the request, and the body is then ``multipart/form-data``, every other body attribute a form field in it.
- A GraphQL record takes its variables with ``-f`` and ``-F``, and with ``--file`` a variable its document declares of
  type ``Upload`` or a list of them (``registry.upload_variables``; issue #44, design.md D4): each ``--file`` of a
  list's name is one item, in command-line order, a single one included, and one ``Upload`` keeps the last file given;
  the call is then one multipart request. Any other option, and a ``--file`` of any other name, is refused.

Each ``NAME=VALUE`` splits at its first ``=``; a REST attribute's name is read with ``registry.attribute_name``, so
``iids[]`` names the attribute ``iids``. No ``=``, an empty name, and ``-F`` text that is not JSON are argparse's usage
error (exit 2), raised by the option's ``type`` (``assignment``, ``json_member``, ``file_member``) before the config is
read: argparse names the option, and the message names the text before the first ``=`` (all of it when there is none)
rendered with ``json.dumps``, never a value. A path name, or an attribute given by ``-f`` or ``-F``, given twice keeps
its last value; ``-f`` and ``-F`` share one destination, so their values keep their command-line order. A ``-f`` or
``-F`` value replaces the ``--query`` values of the same name, and ``--file`` replaces both.

``call_operation`` refuses with exit 2 (``EXIT_REFUSED``), before any request (D4): an ID in ``GATED_OPERATIONS``,
naming the compatibility subcommand that sends it, or, for an ID mapped to ``None`` (``graphql#workItemCreate``,
``graphql#workItemsCsvImport``), saying that no subcommand sends it (issue #44, design.md D6); an ID no record
declares, or one declared twice (``registry.lookup``); a name the record does not document or a path parameter left
without a value, in one message naming each such name with its option, each missing path parameter, then the record's
documented parameters (``check_parameters``); a value of a shape its ``Kind`` does not take (``registry.encode``); and a
paged record given body values (``registry.pages``). Each refusal is a ``ValueError``, logged; every name the caller
supplied is rendered with ``json.dumps``.

What prints (D3):

- a ``Paging.OFFSET`` or ``Paging.KEYSET`` record: every item of every page, in page order, as one JSON array
  (``print_json``), written once the last page has arrived;
- a ``Paging.NONE`` record, by its response: nothing for an empty body; ``print_json`` of the decoded body when its
  ``Content-Type`` is JSON (``Response.is_json``); any other body as its bytes unchanged (``print_bytes``), with no
  line end added;
- a GraphQL record: ``print_json`` of its ``data``, or of the one array of the nodes of every page of its connection.

A ``GitLabAPIError`` (an HTTP error, spent ``429`` retries, no response, GraphQL ``errors``, an empty, ``.`` or ``..``
path value, a ``--file`` that cannot be read) reaches the entry script, which logs its message and details and exits
1. Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from gitlab_api import graphql_only, registry
from gitlab_api.commands import issue, mr
from gitlab_api.commands._common import EXIT_REFUSED, PATH_PROJECT, add_command, print_bytes, print_json
from gitlab_api.registry import GraphQLOperation, Kind, Location, Operation, Paging, RestOperation

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Response, Transport

COMMAND = "call"
ARG_OPERATION_ID = "operation_id"
METAVAR_OPERATION_ID = "operation-id"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD_SHORT = "-f"
OPTION_RAW_FIELD = "--raw-field"
OPTION_FIELD_SHORT = "-F"
OPTION_FIELD = "--field"
OPTION_FILE = "--file"
# How D4's message names the option of a name given with `-f` or `-F`, which share one destination.
OPTION_FIELDS = f"{OPTION_RAW_FIELD_SHORT}/{OPTION_FIELD_SHORT}"
# The `argparse.Namespace` attributes the options are stored under; `-f` and `-F` share one.
ARG_PATH = "path"
ARG_QUERY = "query"
ARG_FIELDS = "fields"
ARG_FILES = "files"
ACTION_APPEND = "append"
METAVAR_VALUE = "NAME=VALUE"
METAVAR_TEXT = "NAME=TEXT"
METAVAR_JSON = "NAME=JSON"
METAVAR_PATH = "NAME=PATH"
ASSIGNMENT_SEPARATOR = "="
# Each destination with the option D4's message names it by, in the message's order.
DESTINATION_OPTIONS: Tuple[Tuple[str, str], ...] = (
    (ARG_PATH, OPTION_PATH),
    (ARG_QUERY, OPTION_QUERY),
    (ARG_FIELDS, OPTION_FIELDS),
    (ARG_FILES, OPTION_FILE),
)

# A path whose `:id` defaults to the configured project: `/projects/:id` itself, or a path under it (AC-1.8).
PROJECT_PATH = f"/projects/:{PATH_PROJECT}"
PATH_SEPARATOR = "/"

MESSAGE_SEPARATOR = "; "
LIST_SEPARATOR = ", "
NOTHING_DOCUMENTED = "none"

# The records `call` refuses: a record that commits to or merges into a branch, or that creates an issue or another
# work item (issue #41, design.md D8). A record a gated compatibility subcommand sends maps to that subcommand: the
# `merge-steward` and `issue-filing-gate` hooks judge the subcommands by their words, so `call` refuses these IDs rather
# than reach them unjudged (design.md D1, "Security Considerations"). A record no subcommand sends maps to `None`, and
# `call` refuses it with no alternative: `issue create` never sends `graphql#workItemCreate`, which creates a work item
# of any type, and no subcommand imports a CSV (issue #44, design.md D6).
GATED_OPERATIONS: Mapping[str, Optional[str]] = MappingProxyType(
    {
        mr.OP_MERGE_MR: f"{mr.GROUP} merge",
        issue.OP_CREATE_ISSUE: f"{issue.GROUP} create",
        graphql_only.OP_WORK_ITEM_CREATE: None,
        graphql_only.OP_WORK_ITEMS_CSV_IMPORT: None,
    }
)
# The end of the refusal of an ID `GATED_OPERATIONS` maps to `None`.
NO_SUBCOMMAND_SENDS_IT = ": no subcommand sends it"

logger = logging.getLogger(__name__)


class Assignment(NamedTuple):
    """One ``NAME=VALUE`` of the command line: the ``name`` before its first ``=``, and the ``value`` after it — text,
    the JSON value the text parses to (``-F/--field``), or a path (``--file``)."""

    name: str
    value: Any


@dataclass(frozen=True)
class PreparedCall:
    """A call that steps 1 to 5 accepted: its record, its values and, for a paged record, the generator of its items,
    which sends nothing until it is read."""

    operation: Operation
    values: Dict[str, Any]
    items: Optional[Iterator[Any]] = None


# --- The argparse types (D2) ----------------------------------------------------------------------------------------


def _split(*, text: str) -> Tuple[str, str]:
    """``text`` cut at its first ``=`` into a name and a value; no ``=`` or an empty name raises
    ``argparse.ArgumentTypeError`` naming the name (all of ``text`` when there is no ``=``), never the value."""
    name, separator, value = text.partition(ASSIGNMENT_SEPARATOR)
    if not separator:
        raise argparse.ArgumentTypeError(f'{json.dumps(obj=name)} has no "=" between a name and its value')
    if not name:
        raise argparse.ArgumentTypeError(f'{json.dumps(obj=name)}: the name before the first "=" is empty')
    return name, value


def assignment(text: str) -> Assignment:
    """The ``type`` of ``--path``, ``--query`` and ``-f/--raw-field``: ``NAME=VALUE`` with the value as text."""
    name, value = _split(text=text)
    return Assignment(name=name, value=value)


def _refuse_constant(text: str) -> Any:
    """``json.loads``'s ``parse_constant``: ``NaN``, ``Infinity`` and ``-Infinity`` are not JSON, so each is refused."""
    raise ValueError(f"{json.dumps(obj=text)} is not a JSON value")


def json_member(text: str) -> Assignment:
    """The ``type`` of ``-F/--field``: ``NAME=JSON`` with the value parsed by ``json.loads``. Every ``ValueError`` of
    ``json.loads``, the one ``parse_constant`` raises included, becomes ``argparse.ArgumentTypeError`` naming the name,
    never the value."""
    name, value = _split(text=text)
    try:
        parsed = json.loads(s=value, parse_constant=_refuse_constant)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'{json.dumps(obj=name)}: the text after the first "=" is not JSON (a number, boolean, array, object, '
            f"null or quoted string); give a string quoted or with {OPTION_RAW_FIELD_SHORT}/{OPTION_RAW_FIELD}"
        ) from None
    return Assignment(name=name, value=parsed)


def file_member(text: str) -> Assignment:
    """The ``type`` of ``--file``: ``NAME=PATH`` with ``pathlib.Path(PATH)`` as the value; the transport reads it."""
    name, value = _split(text=text)
    return Assignment(name=name, value=Path(value))


# --- The values of a call (D2 step 3) ---------------------------------------------------------------------------


def _given(*, args: argparse.Namespace, dest: str) -> List[Assignment]:
    """The assignments stored under ``dest``, in command-line order; none when the option was not given."""
    return list(getattr(args, dest, None) or ())


def takes_project(*, path: str) -> bool:
    """Whether ``path`` is ``/projects/:id`` or starts with ``/projects/:id/``, so its ``id`` defaults to the
    configured project."""
    return path == PROJECT_PATH or path.startswith(PROJECT_PATH + PATH_SEPARATOR)


def path_values(*, operation: RestOperation, project: str, args: argparse.Namespace) -> Dict[str, Any]:
    """The path values of the call: the given ones, a name given twice holding its last value, and ``project`` as the
    ``id`` of a ``/projects/:id`` path the call gives no ``id`` for (AC-1.8)."""
    values: Dict[str, Any] = {each.name: each.value for each in _given(args=args, dest=ARG_PATH)}
    if takes_project(path=operation.path) and PATH_PROJECT not in values:
        values[PATH_PROJECT] = project
    return values


def attribute_values(*, operation: RestOperation, args: argparse.Namespace) -> Dict[str, Any]:
    """The attributes of the call, each named by ``registry.attribute_name``: the ``--query`` values of a name (a list
    for an ``ARRAY`` query attribute or a repeated name, else the one string), replaced by a ``-f`` or ``-F`` value of
    the same name (the last one given), replaced in turn by a ``--file``."""
    query_kinds = {param.name: param.kind for param in operation.params if param.location is Location.QUERY}
    collected: Dict[str, List[str]] = {}
    for each in _given(args=args, dest=ARG_QUERY):
        collected.setdefault(registry.attribute_name(name=each.name), []).append(each.value)
    values: Dict[str, Any] = {
        name: texts if query_kinds.get(name) is Kind.ARRAY or len(texts) > 1 else texts[0]
        for name, texts in collected.items()
    }
    for dest in (ARG_FIELDS, ARG_FILES):
        values.update((registry.attribute_name(name=each.name), each.value) for each in _given(args=args, dest=dest))
    return values


def file_values(*, operation: GraphQLOperation, args: argparse.Namespace) -> Dict[str, Any]:
    """The ``--file`` values of a GraphQL record's call (issue #44, design.md D4): every ``Path`` of a name
    ``registry.upload_variables`` maps to ``True``, as a list in command-line order, a single one included; for any
    other name the last ``Path`` given, a name outside ``upload_variables`` included, which ``check_parameters`` then
    refuses."""
    lists = registry.upload_variables(operation=operation)
    values: Dict[str, Any] = {}
    for each in _given(args=args, dest=ARG_FILES):
        if lists.get(each.name, False):
            values.setdefault(each.name, []).append(each.value)
        else:
            values[each.name] = each.value
    return values


def call_values(*, operation: Operation, project: str, args: argparse.Namespace) -> Dict[str, Any]:
    """The values ``registry`` is given: a GraphQL record's variables from ``-f`` and ``-F``, a name given twice keeping
    its last value, then its ``--file`` values (``file_values``), which replace a variable of the same name; for a REST
    record, the attributes and then the path values, which win over an attribute of the same name."""
    if isinstance(operation, GraphQLOperation):
        fields = {each.name: each.value for each in _given(args=args, dest=ARG_FIELDS)}
        return {**fields, **file_values(operation=operation, args=args)}
    attributes = attribute_values(operation=operation, args=args)
    return {**attributes, **path_values(operation=operation, project=project, args=args)}


# --- D4's parameter check (D2 step 4) ---------------------------------------------------------------------------


def documented_names(*, operation: Operation) -> Dict[str, FrozenSet[str]]:
    """The names each destination may give ``operation`` (D4): the path parameters for ``--path``, the
    ``Location.QUERY`` ``Param`` names for ``--query``, every ``Param`` name for ``-f``, ``-F`` and ``--file``; for a
    GraphQL record, the variables its document defines for ``-f`` and ``-F``, those of ``registry.upload_variables``
    for ``--file`` (issue #44, design.md D4), and nothing for any other option."""
    if isinstance(operation, GraphQLOperation):
        return {
            ARG_FIELDS: frozenset(registry.variables(operation=operation)),
            ARG_FILES: frozenset(registry.upload_variables(operation=operation)),
        }
    attributes = frozenset(param.name for param in operation.params)
    return {
        ARG_PATH: frozenset(registry.placeholders(path=operation.path)),
        ARG_QUERY: frozenset(param.name for param in operation.params if param.location is Location.QUERY),
        ARG_FIELDS: attributes,
        ARG_FILES: attributes,
    }


def _compared_name(*, operation: Operation, dest: str, name: str) -> str:
    """The name a given name is checked as: a REST attribute's by ``registry.attribute_name``, any other as given."""
    if isinstance(operation, RestOperation) and dest != ARG_PATH:
        return registry.attribute_name(name=name)
    return name


def undocumented(*, operation: Operation, args: argparse.Namespace) -> List[Tuple[str, str]]:
    """Each name the call gives that ``operation`` does not document, as given, with its option; in the order of
    ``DESTINATION_OPTIONS``, then of the command line, each pair once."""
    documented = documented_names(operation=operation)
    found: Dict[Tuple[str, str], None] = {}
    for dest, option in DESTINATION_OPTIONS:
        accepted = documented.get(dest, frozenset())
        for each in _given(args=args, dest=dest):
            if _compared_name(operation=operation, dest=dest, name=each.name) not in accepted:
                found[(each.name, option)] = None
    return list(found)


def missing_path_parameters(*, operation: Operation, project: str, args: argparse.Namespace) -> List[str]:
    """The path parameters of a REST record that the call leaves without a value once ``id`` has its default."""
    if isinstance(operation, GraphQLOperation):
        return []
    given = path_values(operation=operation, project=project, args=args)
    return [name for name in dict.fromkeys(registry.placeholders(path=operation.path)) if name not in given]


def _listed(*, names: Sequence[str]) -> str:
    return LIST_SEPARATOR.join(names) if names else NOTHING_DOCUMENTED


def documented_text(*, operation: Operation) -> str:
    """The record's documented parameters as D4's message ends with them: the path parameters and every attribute with
    its location and ``Kind``, or a GraphQL record's variables."""
    if isinstance(operation, GraphQLOperation):
        return f"its variables: {_listed(names=registry.variables(operation=operation))}"
    attributes = [f"{param.name} ({param.location.value}, {param.kind.value})" for param in operation.params]
    path_parameters = list(dict.fromkeys(registry.placeholders(path=operation.path)))
    return f"its path parameters: {_listed(names=path_parameters)}; its attributes: {_listed(names=attributes)}"


def check_parameters(*, operation: Operation, project: str, args: argparse.Namespace) -> None:
    """D4's check: refuse with ``ValueError``, in one message, each name ``operation`` does not document, with its
    option, and each path parameter left without a value; the message then names the record's documented
    parameters. A name the caller supplied is rendered with ``json.dumps``."""
    problems = [
        f"{json.dumps(obj=name)} given with {option} is not documented"
        for name, option in undocumented(operation=operation, args=args)
    ]
    problems.extend(
        f"the path parameter {name} has no value"
        for name in missing_path_parameters(operation=operation, project=project, args=args)
    )
    if problems:
        raise ValueError(
            f"{operation.operation_id}: {MESSAGE_SEPARATOR.join(problems)}{MESSAGE_SEPARATOR}"
            f"{documented_text(operation=operation)}"
        )


# --- The call (D2 steps 1 to 6, D3) -----------------------------------------------------------------------------


def refuse_gated(*, operation_id: str) -> None:
    """Refuse with ``ValueError`` every ID in ``GATED_OPERATIONS``: naming the subcommand that sends it, or, for an ID
    mapped to ``None``, saying that no subcommand sends it (issue #44, design.md D6)."""
    if operation_id not in GATED_OPERATIONS:
        return
    subcommand = GATED_OPERATIONS[operation_id]
    refused = f"{COMMAND} refuses the GitLab operation {json.dumps(obj=operation_id)}"
    if subcommand is None:
        raise ValueError(f"{refused}{NO_SUBCOMMAND_SENDS_IT}")
    raise ValueError(f"{refused}: use the {subcommand} subcommand, which sends it")


def prepare_call(*, transport: Transport, project: str, operation_id: str, args: argparse.Namespace) -> PreparedCall:
    """Steps 1 to 5, each refusal a ``ValueError`` and nothing sent: the gate, ``registry.lookup``, the values, D4's
    check, and the shape check — ``registry.encode`` for a ``Paging.NONE`` REST record, ``registry.pages`` (its own
    look-up, encoding, ``GET``-only check and ``expand``) for a paged one."""
    refuse_gated(operation_id=operation_id)
    operation = registry.lookup(operation_id=operation_id)
    values = call_values(operation=operation, project=project, args=args)
    check_parameters(operation=operation, project=project, args=args)
    if isinstance(operation, GraphQLOperation):
        return PreparedCall(operation=operation, values=values)
    if operation.paging is Paging.NONE:
        registry.encode(operation=operation, values=values)
        return PreparedCall(operation=operation, values=values)
    items = registry.pages(transport=transport, operation_id=operation_id, values=values)
    return PreparedCall(operation=operation, values=values, items=items)


def print_response(*, response: Response) -> None:
    """D3's ``Paging.NONE`` output: nothing for an empty body, ``print_json`` of the decoded body when its
    ``Content-Type`` is JSON, and any other body as its bytes unchanged."""
    if not response.body:
        return
    if response.is_json:
        print_json(value=response.value)
        return
    print_bytes(data=response.body)


def send_call(*, transport: Transport, prepared: PreparedCall) -> None:
    """Step 6 and D3: a paged record's items read and printed as one array once the last page has arrived; a GraphQL
    record through ``registry.call``; a ``Paging.NONE`` record through ``registry.send``."""
    operation_id = prepared.operation.operation_id
    if prepared.items is not None:
        print_json(value=list(prepared.items))
        return
    if isinstance(prepared.operation, GraphQLOperation):
        print_json(value=registry.call(transport=transport, operation_id=operation_id, values=prepared.values))
        return
    print_response(response=registry.send(transport=transport, operation_id=operation_id, values=prepared.values))


def call_operation(
    *, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace
) -> Optional[int]:
    """``call <operation-id>``: steps 1 to 5 decide every refusal before anything is sent; a refusal is logged with
    ``logger.error`` and returns ``EXIT_REFUSED``. Then the call is sent and its response printed (step 6, D3)."""
    operation_id = str(getattr(args, ARG_OPERATION_ID))
    try:
        prepared = prepare_call(transport=transport, project=project, operation_id=operation_id, args=args)
    except ValueError as refusal:
        logger.error("%s", refusal)
        return EXIT_REFUSED
    send_call(transport=transport, prepared=prepared)
    return None


# --- The subcommand ---------------------------------------------------------------------------------------------


def register(*, subparsers: SubParsers) -> None:
    """Add ``call`` to the entry script's top-level ``subparsers``, carrying ``call_operation`` as its handler."""
    parser = add_command(
        subparsers=subparsers,
        name=COMMAND,
        handler=call_operation,
        help_text="send any declared operation record, named by its operation ID",
    )
    parser.add_argument(
        ARG_OPERATION_ID, metavar=METAVAR_OPERATION_ID, help="the operation ID, e.g. plan#retrieve-a-project-issue"
    )
    parser.add_argument(
        OPTION_PATH,
        dest=ARG_PATH,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_VALUE,
        help="a path parameter; id defaults to the configured project_id on a /projects/:id path",
    )
    parser.add_argument(
        OPTION_QUERY,
        dest=ARG_QUERY,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_VALUE,
        help="a query attribute as text; repeat it for each item of an array",
    )
    parser.add_argument(
        OPTION_RAW_FIELD_SHORT,
        OPTION_RAW_FIELD,
        dest=ARG_FIELDS,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_TEXT,
        help="an attribute or GraphQL variable whose value is the string TEXT",
    )
    parser.add_argument(
        OPTION_FIELD_SHORT,
        OPTION_FIELD,
        dest=ARG_FIELDS,
        action=ACTION_APPEND,
        default=None,
        type=json_member,
        metavar=METAVAR_JSON,
        help="an attribute or GraphQL variable whose value is JSON: a number, boolean, array, object or quoted string",
    )
    parser.add_argument(
        OPTION_FILE,
        dest=ARG_FILES,
        action=ACTION_APPEND,
        default=None,
        type=file_member,
        metavar=METAVAR_PATH,
        help="a file attribute; the body is sent as multipart/form-data",
    )
