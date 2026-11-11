"""The GitHub wrapper's operation call, ``call <operation-id>`` (issue #28 design D2 to D4): any record a family module
of ``github_api/families/`` declares, sent by its operation ID.

The grammar (D2)::

    python scripts/github_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
                                          [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]...

- ``<operation-id>``: the operation ID of the index (``issues/get``).
- ``--path NAME=VALUE``: a path parameter, as text, encoded by ``registry.expand``. When the record's path names
  ``{owner}`` or ``{repo}`` and the call gives no value for it, the value is the ``origin`` repository in
  ``.git/config``, which the entry script passes to every handler.
- ``--query NAME=VALUE``: a query parameter, as text. A name given more than once is sent once per value, in the order
  given. A name may end in ``[]``, the array spelling of ``conventions.md`` "Query strings", and is sent as written.
- ``-f/--raw-field NAME=TEXT``: a body member whose value is the string TEXT.
- ``-F/--field NAME=JSON``: a body member whose value is JSON parsed by ``json.loads``: a number, boolean, array,
  object, ``null`` or quoted string. Text that is not JSON, ``NaN`` and the infinities included, is refused, so a
  string is given quoted or with ``-f``.

Each ``NAME=VALUE`` splits at its first ``=``. No ``=``, an empty name, and ``--field`` text that is not JSON are each
an argparse usage error (exit 2), raised by the option's ``type`` (``assignment``, ``json_member``) before the
credential is read; argparse names the option, and the message names the text before the first ``=`` (all of it when
there is none) rendered with ``json.dumps``, never a value. A path or body name given twice keeps its last value. The
two body options share one destination, so the members keep their command-line order; ``body_of`` joins them into
one JSON object, or ``None`` when none was given, which sends no body.

``cmd_call`` refuses, with exit 2 (``EXIT_REFUSED``) and before any request: an ID in ``GATED_OPERATIONS``, naming
the compatibility subcommand that sends it; an ID no record declares (``registry.lookup``); and a call that gives a
path, query or body name the record does not document or leaves a path parameter without a value, in one message
naming each such name with its kind, each missing path parameter, then the record's documented path, query and body
parameters (``check_call``). A refusal is logged; every name the caller gave is rendered with ``json.dumps``.

What prints (D3):

- a ``Paging.LINK`` record: every item of every page, in page order, as one JSON array (``print_json``), written once
  the last page has arrived;
- any other record, by its response body: nothing for an empty body; the parsed body as indented JSON
  (``print_json``) for a body that decodes as UTF-8 and parses with ``json.loads``; any other body as its bytes
  unchanged (``print_bytes``), with no line end added.

A ``GitHubAPIError`` (an HTTP error, a spent rate limit, no response, a ``.`` or ``..`` path segment) reaches the entry
script, which logs its message and details and exits 1.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Collection, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from github_api import registry
from github_api.commands._common import EXIT_REFUSED, print_bytes, print_json
from github_api.registry import Paging, RestOperation
from github_api.transport import Transport

CMD_CALL = "call"
ARG_OPERATION_ID = "operation_id"
METAVAR_OPERATION_ID = "operation-id"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD_SHORT = "-f"
OPTION_RAW_FIELD = "--raw-field"
OPTION_FIELD_SHORT = "-F"
OPTION_FIELD = "--field"
#: The ``argparse.Namespace`` attributes the options are stored under; ``-f`` and ``-F`` share one.
ARG_PATH = "path"
ARG_QUERY = "query"
ARG_MEMBERS = "members"
ACTION_APPEND = "append"
METAVAR_VALUE = "NAME=VALUE"
METAVAR_TEXT = "NAME=TEXT"
METAVAR_JSON = "NAME=JSON"
ASSIGNMENT_SEPARATOR = "="

#: The path parameters that default to the ``origin`` repository when the call gives no value for them.
PATH_OWNER = "owner"
PATH_REPO = "repo"

KIND_PATH = "path"
KIND_QUERY = "query"
KIND_BODY = "body"
BODY_ENCODING = "utf-8"

#: The records a gated compatibility subcommand sends, each with that subcommand: ``gate_merge_steward`` and
#: ``gate_filing`` match the subcommand words, so ``call`` refuses these IDs rather than reach them unjudged.
GATED_OPERATIONS: Mapping[str, str] = MappingProxyType({"pulls/merge": "merge-pr", "issues/create": "create-issue"})

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Assignment:
    """One ``NAME=VALUE`` of the command line: the ``name`` before its first ``=``, and the ``value`` after it, as text
    or, for ``-F/--field``, as the JSON value the text parses to."""

    name: str
    value: Any


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
    """The ``type`` of ``-F/--field``: ``NAME=JSON`` with the value parsed by ``json.loads``; text that is not JSON,
    ``NaN`` and the infinities included, raises ``argparse.ArgumentTypeError`` naming the name, never the value."""
    name, value = _split(text=text)
    try:
        parsed = json.loads(s=value, parse_constant=_refuse_constant)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'{json.dumps(obj=name)}: the value after the first "=" is not JSON; give a string quoted or with '
            f"{OPTION_RAW_FIELD_SHORT}/{OPTION_RAW_FIELD}"
        ) from None
    return Assignment(name=name, value=parsed)


def body_of(*, members: Sequence[Assignment]) -> Optional[Dict[str, Any]]:
    """The request body ``members`` make: one JSON object of every member in command-line order, a name given twice
    holding its last value; ``None`` when no member was given, so no body is sent."""
    if not members:
        return None
    return {member.name: member.value for member in members}


def query_of(*, given: Sequence[Assignment]) -> Dict[str, Any]:
    """The query ``given`` makes: ``{name: value}``, or ``{name: [values in order]}`` for a name given more than once,
    which ``Transport.request`` encodes as one pair per value."""
    values: Dict[str, List[str]] = {}
    for each in given:
        values.setdefault(each.name, []).append(each.value)
    return {name: texts[0] if len(texts) == 1 else texts for name, texts in values.items()}


def refuse_gated(*, operation_id: str) -> None:
    """Refuse with ``ValueError`` an ID in ``GATED_OPERATIONS``, naming the subcommand that sends it."""
    subcommand = GATED_OPERATIONS.get(operation_id)
    if subcommand is not None:
        raise ValueError(
            f"{CMD_CALL} refuses the GitHub operation {json.dumps(obj=operation_id)}: use the {subcommand} "
            f"subcommand, which sends it"
        )


def path_values(*, operation: RestOperation, given: Sequence[Assignment], owner: str, repo: str) -> Dict[str, Any]:
    """The path values of the call: the given ones, a name given twice holding its last value, and ``owner`` and
    ``repo`` for a ``{owner}`` or ``{repo}`` of the record's path that the call gives no value for."""
    values: Dict[str, Any] = {each.name: each.value for each in given}
    placeholders = registry.path_parameters(operation=operation)
    for name, default in ((PATH_OWNER, owner), (PATH_REPO, repo)):
        if name in placeholders and name not in values:
            values[name] = default
    return values


def _undocumented(
    *, operation: RestOperation, path_names: Collection[str], query_names: Iterable[str], body_names: Iterable[str]
) -> List[Tuple[str, List[str]]]:
    """Each kind with the given names of that kind the record does not document, sorted; a query name is compared as
    ``registry.query_name`` gives it and named as given."""
    documented_path = registry.path_parameters(operation=operation)
    path = {name for name in path_names if name not in documented_path}
    query = {name for name in query_names if registry.query_name(name=name) not in operation.query_params}
    body = {name for name in body_names if name not in operation.body_params}
    return [(KIND_PATH, sorted(path)), (KIND_QUERY, sorted(query)), (KIND_BODY, sorted(body))]


def check_call(
    *, operation: RestOperation, path_names: Collection[str], query_names: Iterable[str], body_names: Iterable[str]
) -> None:
    """D4's check: refuse with ``ValueError``, in one message, every path, query or body name the record does not
    document, each with its kind, and every path parameter of the record ``path_names`` lacks; the message then names
    the record's documented path parameters (in path order), query and body parameters."""
    documented_path = list(registry.path_parameters(operation=operation))
    named = [
        f"no {kind} parameter {json.dumps(obj=names)}"
        for kind, names in _undocumented(
            operation=operation, path_names=path_names, query_names=query_names, body_names=body_names
        )
        if names
    ]
    missing = [name for name in documented_path if name not in path_names]
    problems = []
    if named:
        problems.append(f"documents {', '.join(named)}")
    if missing:
        problems.append(f"has no value for the path parameter {json.dumps(obj=missing)}")
    if not problems:
        return
    raise ValueError(
        f"The GitHub operation {json.dumps(obj=operation.operation_id)} {'; it '.join(problems)}; "
        f"its path parameters are {json.dumps(obj=documented_path)}, "
        f"its query parameters are {json.dumps(obj=sorted(operation.query_params))}, "
        f"its body parameters are {json.dumps(obj=sorted(operation.body_params))}"
    )


def _given(*, args: argparse.Namespace, dest: str) -> List[Assignment]:
    """The assignments stored under ``dest``, in command-line order; none when the option was not given."""
    return list(getattr(args, dest, None) or ())


def print_body(*, body: bytes) -> None:
    """D3's ``Paging.NONE`` output: nothing for an empty body, ``print_json`` of a body that decodes as UTF-8 and
    parses as JSON, and any other body as its bytes unchanged."""
    if not body:
        return
    try:
        parsed = json.loads(s=body.decode(encoding=BODY_ENCODING))
    except ValueError:
        print_bytes(data=body)
        return
    print_json(value=parsed)


def cmd_call(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> Optional[int]:
    """Send the record ``args.operation_id`` names and print its response (D2 steps 1 to 7, D3).

    Steps 1 to 4 decide every refusal before anything is sent: a gated ID, an ID no record declares, then the path
    values (``owner`` and ``repo`` defaulted) and D4's check. Each refusal is a ``ValueError``, logged, and the call
    returns ``EXIT_REFUSED``. Then the query and the body are built, and a ``Paging.LINK`` record goes through
    ``registry.pages``, any other through ``registry.send``.
    """
    operation_id = str(getattr(args, ARG_OPERATION_ID))
    query_given = _given(args=args, dest=ARG_QUERY)
    members = _given(args=args, dest=ARG_MEMBERS)
    try:
        refuse_gated(operation_id=operation_id)
        operation = registry.lookup(operation_id=operation_id)
        path_params = path_values(operation=operation, given=_given(args=args, dest=ARG_PATH), owner=owner, repo=repo)
        check_call(
            operation=operation,
            path_names=path_params,
            query_names=[each.name for each in query_given],
            body_names=[each.name for each in members],
        )
    except ValueError as refusal:
        logger.error("%s", refusal)
        return EXIT_REFUSED
    query = query_of(given=query_given)
    if operation.paging == Paging.LINK:
        items = list(
            registry.pages(transport=transport, operation_id=operation_id, path_params=path_params, query=query)
        )
        print_json(value=items)
        return None
    response = registry.send(
        transport=transport,
        operation_id=operation_id,
        path_params=path_params,
        query=query,
        body=body_of(members=members),
    )
    print_body(body=response.body)
    return None


def register(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add ``call`` to the entry script's ``subparsers``, carrying ``cmd_call`` as its ``handler``."""
    parser = subparsers.add_parser(name=CMD_CALL, help="Send any declared operation record, named by its operation ID")
    parser.set_defaults(handler=cmd_call)
    parser.add_argument(ARG_OPERATION_ID, metavar=METAVAR_OPERATION_ID, help="The operation ID, e.g. issues/get")
    parser.add_argument(
        OPTION_PATH,
        dest=ARG_PATH,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_VALUE,
        help="A path parameter; owner and repo default to the origin in .git/config",
    )
    parser.add_argument(
        OPTION_QUERY,
        dest=ARG_QUERY,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_VALUE,
        help="A query parameter; a name repeated sends each value, an array parameter is NAME[]",
    )
    parser.add_argument(
        OPTION_RAW_FIELD_SHORT,
        OPTION_RAW_FIELD,
        dest=ARG_MEMBERS,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_TEXT,
        help="A body member whose value is the string TEXT",
    )
    parser.add_argument(
        OPTION_FIELD_SHORT,
        OPTION_FIELD,
        dest=ARG_MEMBERS,
        action=ACTION_APPEND,
        default=None,
        type=json_member,
        metavar=METAVAR_JSON,
        help="A body member whose value is JSON: a number, boolean, array, object, null or quoted string",
    )
