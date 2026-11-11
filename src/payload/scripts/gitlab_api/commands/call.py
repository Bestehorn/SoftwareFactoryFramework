"""The GitLab wrapper's operation call, ``call <operation-id>`` (issue #41, design.md D1 to D4): any record that a
family module of ``gitlab_api/families/`` or ``gitlab_api/graphql_only.py`` declares, sent by its operation ID.

The grammar (D2, issue #40 design.md D5 for ``--input``, issue #43 design.md D3 for ``--route-prefix``, and issue #63
design.md D1 and D5 for ``--endpoint`` and ``--header``)::

    python scripts/gitlab_wrapper.py call <operation-id> [--path NAME=VALUE]... [--query NAME=VALUE]...
        [-f|--raw-field NAME=TEXT]... [-F|--field NAME=JSON]... [--file NAME=PATH]... [--input FILE]
        [--route-prefix PREFIX] [--endpoint 'METHOD path'] [--header NAME=VALUE]...

- ``<operation-id>``: a record's ID, ``<stem>#<anchor>`` for a REST record (``plan#retrieve-a-project-issue``) and
  ``graphql#<field>`` for a GraphQL record.
- ``--path NAME=VALUE``: a path parameter, as text: a ``:name`` written by ``registry.expand`` as ONE percent-encoded
  segment, a ``*name`` with each ``/`` kept and each part between them one such segment; the parameter of an optional
  ``(...)`` group may be left out, and the group is then not sent (issue #40, design.md D2). On a record whose path is
  ``/projects/:id`` or starts with ``/projects/:id/``, an ``id`` the call does not give is the configured project
  (``project_id`` of ``config/gitlab.json``); no other ``:id`` has a default. A name of the record's
  ``positional_names``, which its path holds at more than one place, takes one ``--path`` per place, its values filling
  the places in command-line order, and has no default (issue #63, design.md D2):
  ``--path id=7 --path id=12345`` sends ``/groups/7/ssh_certificates/12345``. A ``[.name]`` suffix is a path parameter
  that may be left out (D3): ``--path format=zip`` sends ``archive.zip``, its value one of the record's
  ``suffix_values``, and no ``--path format`` sends ``archive``. In a container-registry path each ``${NAME}`` is a
  path parameter whose ``/`` are kept (D4): ``--path CI_REGISTRY_IMAGE=group/project``.
- ``--query NAME=VALUE``: an attribute the record declares in the query, as text. The values of one name are collected
  in the order given: a list for an ``ARRAY`` attribute, even with one value, and the one string for any other
  ``Kind`` (a repeated name becomes a list, which the shape check refuses).
- ``-f/--raw-field NAME=TEXT``: a query or body attribute, the string TEXT as its value. A member of a form body below
  its first bracket level is named in full, as its table writes it (issue #63, design.md D6):
  ``-f 'override_params[container_expiration_policy_attributes][cadence]=7d'``.
- ``-F/--field NAME=JSON``: a query or body attribute, the value ``json.loads`` parses: a number, a boolean, an array,
  an object or a quoted string. Text that is not JSON is refused; ``NaN``, ``Infinity`` and ``-Infinity``, which plain
  ``json.loads`` takes outside the JSON grammar, are such text. ``null`` is accepted, but a REST attribute of ``None``
  is not sent (``registry.encode``); a GraphQL variable sends it.
- ``--file NAME=PATH``: a ``FILE`` attribute, ``pathlib.Path(PATH)`` as its value. The transport reads the file when it
  builds the request, and the body is then ``multipart/form-data``, every other body attribute a form field in it.
- ``--input FILE``: the request body is the bytes of FILE, or of standard input's binary buffer when FILE is ``-``,
  sent unchanged under the record's ``content_type`` (issue #40, design.md D5). Only a REST record that has a
  ``content_type`` takes it, its attributes given with ``--query``; such a record called without ``--input`` sends no
  body. The option's ``type``, ``read_input``, reads the bytes whole when the arguments are parsed; a file that cannot
  be read is an argparse usage error (exit 2) for ``--input``, before the config is read, whose message names only the
  path, rendered with ``json.dumps``.
- ``--route-prefix PREFIX``: the ``<route-prefix>`` of a protocol route (issue #43, design.md D3), for a REST record
  whose path starts with ``/<route-prefix>/``: one of the record's prefix values, its ``route_prefixes``, verbatim
  (``/groups/:id/-/packages/npm``). The option takes one value, stored as given; a repeated option keeps its last.
  ``registry.route`` writes the record's value in place of ``/<route-prefix>``, and every later step reads the routed
  record: each ``:name`` of the value is a path parameter of the call, given with ``--path`` (``--path id=7``), and a
  value starting ``/projects/:id`` takes the configured project as its ``id`` when the call gives none. The text goes
  to ``registry.send`` as its ``prefix``.
- ``--endpoint 'METHOD path'``: the endpoint of a Reference that several records of one family declare, its method,
  one space and its path as the index writes them, taken as one argument after the option (issue #63, design.md D1).
  The option takes one value; a repeated option keeps its last. The ID's record on that endpoint is sent, and every
  later step reads it: a path parameter of another endpoint is a name the record does not document. Without the
  option, an ID that several records declare sends its first declared endpoint, its base record. The option's
  ``type``, ``endpoint_key``, cuts the text at its first space; no space, an empty method and an empty path are an
  argparse usage error (exit 2) for ``--endpoint``, before the config is read, whose message names the text rendered
  with ``json.dumps``. The pair goes to ``registry.lookup``, ``registry.send`` and ``registry.pages`` as ``endpoint``.
- ``--header NAME=VALUE``: a request header the record declares, a ``Location.HEADER`` ``Param``, as text (issue #63,
  design.md D5): its name is compared with the declared names ignoring case (RFC 9110 section 5.1), and its value is
  sent under the declared spelling; a header not given is not sent. ``-f``, ``-F`` and ``--file`` give no header, and
  ``--header`` no other attribute; a record that declares no header, a GraphQL record included, takes none.
- A GraphQL record takes its variables with ``-f`` and ``-F``, and with ``--file`` a variable its document declares of
  type ``Upload`` or a list of them (``registry.upload_variables``; issue #44, design.md D4): each ``--file`` of a
  list's name is one item, in command-line order, a single one included, and one ``Upload`` keeps the last file given;
  the call is then one multipart request. Any other option, and a ``--file`` of any other name, is refused.

Issue #63's request forms (its design.md D1 to D6), one example each, the last a two-level member, by its full name::

    call plan#add-an-emoji-reaction-to-a-resource --path merge_request_iid=5 -f name=thumbsup
        --endpoint 'POST /projects/:id/merge_requests/:merge_request_iid/award_emoji'
    call create#delete-a-group-ssh-certificate --path id=7 --path id=12345
    call create#retrieve-file-archive-from-a-repository --path format=zip
    call software-supply-chain-security#set-status-of-an-external-control --path external_control_id=3 -f status=pass
        --header X-Gitlab-Timestamp=1700000000 --header X-Gitlab-Nonce=n1 --header X-Gitlab-Hmac-Sha256=ab12
    -f 'override_params[container_expiration_policy_attributes][cadence]=7d'   # a two-level member, by its full name

The first call without ``--endpoint`` sends the Reference's first declared endpoint, the issue's. The S3 import,
``gitlab-dedicated#import-a-project-from-an-aws-s3-bucket``, whose form body holds the last line's member, is refused
(``GATED_OPERATIONS``). A container-registry record (``package#delete-image-tags-by-reference``) obtains its registry
token from the configured instance before the registry is sent anything (D4, ``gitlab_api/container_registry.py``):
the login (``GET /user``, or ``gitlab-ci-token`` for a job token), the registry's origin (``GET /projects/<project>``),
and the registry token from ``/jwt/auth`` with the configured token as the password; the registry request then carries
that registry token alone, and the configured project goes to ``registry.send`` as its ``project``.

Each ``NAME=VALUE`` splits at its first ``=``; a REST attribute's name is read with ``registry.attribute_name``, so
``iids[]`` names the attribute ``iids``. No ``=``, an empty name, and ``-F`` text that is not JSON are argparse's usage
error (exit 2), raised by the option's ``type`` (``assignment``, ``json_member``, ``file_member``) before the config is
read: argparse names the option, and the message names the text before the first ``=`` (all of it when there is none)
rendered with ``json.dumps``, never a value. A path name, or an attribute given by ``-f`` or ``-F``, given twice keeps
its last value, but a name of the record's ``positional_names``, whose values fill its places in command-line order
(issue #63, design.md D2); so does a header given twice under names equal ignoring case. ``-f`` and ``-F`` share one
destination, so their values keep their command-line order. A ``-f`` or ``-F`` value replaces the ``--query`` values
of the same name, and ``--file`` replaces both. The raw body ``--input`` read goes to ``registry.send`` as its
``data``.

``call_operation`` refuses with exit 2 (``EXIT_REFUSED``), before any request (D4), in this order: a raw body given
together with one or more ``-f`` or ``-F`` values (``refuse_both_bodies``), in a message naming ``--input``,
``-f/--raw-field`` and ``-F/--field`` and saying that a raw-body record's attributes are given with ``--query``; an ID
in ``GATED_OPERATIONS``, naming the compatibility subcommand that sends it, or, for an ID mapped to ``None`` (a record
that writes a branch or a merge request's source branch, merges, writes into an existing project, or creates an issue
or another work item, and that no subcommand sends), saying that no subcommand sends it (issue #44, design.md D6; issue
#63, design.md D6; issue #15 AC-3); an ID no record declares, or one declared twice, and an ``--endpoint``
none of the ID's records is on, in a message naming the ID, the text given and each declared endpoint, or given for a
GraphQL record (``registry.lookup``; issue #63, design.md D1); a raw body for any record but a REST record with a
``content_type`` (``refuse_raw_body``), in a message naming the ID and ``--input`` and saying that its body is given
with ``-f``, ``-F`` or ``--file``; a route prefix that none of the record's values equals, none for a record whose path
starts with ``/<route-prefix>/``, or one for any other record (``registry.route``; issue #43, design.md D3), in a
message naming the ID and, for a record whose path starts with ``/<route-prefix>/``, each of its values; a name the
record does not document, a header the record does not declare included, a path parameter outside an optional group
left without a value, a positional name given more values than its places, and a suffix value none of the record's
``suffix_values`` equals, in one message naming each such name with its option, each missing path parameter (a
positional name once for each place left without a value), each such positional name and each such suffix value with
the listed values, then the record's documented parameters, a positional name once per place (``check_parameters``;
issue #63, design.md D2, D3, D5); a value of a shape its ``Kind`` does not take, or a header value holding CR, LF or
NUL (``registry.encode``); and a paged record given body values or a header (``registry.pages``). Each refusal is a
``ValueError``, logged; every name and path value the caller supplied is rendered with ``json.dumps``, and no byte of
a raw body is.

What prints (D3):

- a ``Paging.OFFSET`` or ``Paging.KEYSET`` record: every item of every page, in page order, as one JSON array
  (``print_json``), written once the last page has arrived;
- a ``Paging.NONE`` record, by its response: nothing for an empty body; ``print_json`` of the decoded body when its
  ``Content-Type`` is JSON (``Response.is_json``); any other body as its bytes unchanged (``print_bytes``), with no
  line end added;
- a GraphQL record: ``print_json`` of its ``data``, or of the one array of the nodes of every page of its connection.

A ``GitLabAPIError`` (an HTTP error, spent ``429`` retries, no response, GraphQL ``errors``, an empty, ``.`` or ``..``
path value or glob part, a ``--file`` that cannot be read, a container-registry call whose login, registry origin or
registry token the configured instance does not give, issue #63 design.md D4) reaches the entry script, which logs its
message and details and exits 1. Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from gitlab_api import graphql_only, registry
from gitlab_api.commands import issue, mr
from gitlab_api.commands._common import EXIT_REFUSED, PATH_PROJECT, add_command, print_bytes, print_json
from gitlab_api.families import agent_foundations, ai_coding, create, gitlab_dedicated, package, plan, verify
from gitlab_api.registry import Endpoint, GraphQLOperation, Kind, Location, Operation, Paging, RestOperation

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
OPTION_INPUT = "--input"
OPTION_ROUTE_PREFIX = "--route-prefix"
OPTION_ENDPOINT = "--endpoint"
OPTION_HEADER = "--header"
# How D4's message names the option of a name given with `-f` or `-F`, which share one destination.
OPTION_FIELDS = f"{OPTION_RAW_FIELD_SHORT}/{OPTION_FIELD_SHORT}"
# The `argparse.Namespace` attributes the options are stored under; `-f` and `-F` share one.
ARG_PATH = "path"
ARG_QUERY = "query"
ARG_FIELDS = "fields"
ARG_FILES = "files"
ARG_RAW_BODY = "raw_body"
ARG_ROUTE_PREFIX = "route_prefix"
ARG_ENDPOINT = "endpoint"
ARG_HEADERS = "headers"
ACTION_APPEND = "append"
ACTION_STORE = "store"
METAVAR_VALUE = "NAME=VALUE"
METAVAR_TEXT = "NAME=TEXT"
METAVAR_JSON = "NAME=JSON"
METAVAR_PATH = "NAME=PATH"
METAVAR_FILE = "FILE"
METAVAR_PREFIX = "PREFIX"
METAVAR_ENDPOINT = "ENDPOINT"
ASSIGNMENT_SEPARATOR = "="
# The `--input` text that reads the raw body from standard input rather than from a file, as `gh api` spells it.
STDIN_INPUT = "-"
# Each destination with the option D4's message names it by, in the message's order; `--header` last (issue #63, D5).
DESTINATION_OPTIONS: Tuple[Tuple[str, str], ...] = (
    (ARG_PATH, OPTION_PATH),
    (ARG_QUERY, OPTION_QUERY),
    (ARG_FIELDS, OPTION_FIELDS),
    (ARG_FILES, OPTION_FILE),
    (ARG_HEADERS, OPTION_HEADER),
)
# The locations of the attributes `-f`, `-F` and `--file` give; `--header` gives the HEADER ones (issue #63, D5).
FIELD_LOCATIONS = frozenset({Location.QUERY, Location.BODY})

# A path whose `:id` defaults to the configured project: `/projects/:id` itself, or a path under it (AC-1.8).
PROJECT_PATH = f"/projects/:{PATH_PROJECT}"
PATH_SEPARATOR = "/"

MESSAGE_SEPARATOR = "; "
LIST_SEPARATOR = ", "
NOTHING_DOCUMENTED = "none"

# The records `call` refuses: a record that writes a branch or a merge request's source branch, merges, writes into an
# existing project, or creates an issue or another work item (issue #41, design.md D8; issue #63, design.md D6; issue
# #15 AC-3). A record a gated compatibility subcommand sends maps to that subcommand: the `merge-steward` and
# `issue-filing-gate` hooks judge the subcommands by their words, so `call` refuses these IDs rather than reach them
# unjudged (design.md D1, "Security Considerations"). A record of that class no subcommand sends maps to `None`, and
# `call` refuses it with no alternative (issue #44, design.md D6).
GATED_OPERATIONS: Mapping[str, Optional[str]] = MappingProxyType(
    {
        mr.OP_MERGE_MR: f"{mr.GROUP} merge",
        issue.OP_CREATE_ISSUE: f"{issue.GROUP} create",
        graphql_only.OP_WORK_ITEM_CREATE: None,
        graphql_only.OP_WORK_ITEMS_CSV_IMPORT: None,
        gitlab_dedicated.OP_IMPORT_FROM_S3: None,
        agent_foundations.OP_TRIGGER_A_FLOW: None,
        agent_foundations.OP_RESTART_A_FLOW: None,
        ai_coding.OP_REBASE_A_MERGE_REQUEST: None,
        create.OP_CREATE_REPOSITORY_BRANCH: None,
        create.OP_CREATE_A_COMMIT: None,
        create.OP_CHERRY_PICK_A_COMMIT: None,
        create.OP_REVERT_A_COMMIT: None,
        create.OP_ADD_CHANGELOG_DATA_TO_FILE: None,
        create.OP_CREATE_A_FILE_IN_A_REPOSITORY: None,
        create.OP_UPDATE_A_FILE_IN_A_REPOSITORY: None,
        create.OP_DELETE_A_FILE_IN_A_REPOSITORY: None,
        create.OP_UPDATE_A_SUBMODULE_REFERENCE: None,
        create.OP_APPLY_A_SUGGESTION: None,
        create.OP_APPLY_MULTIPLE_SUGGESTIONS: None,
        create.OP_START_THE_PULL_MIRRORING_PROCESS_FOR_A_PROJECT: None,
        gitlab_dedicated.OP_IMPORT_A_PROJECT_FROM_A_LOCAL_ARCHIVE: None,
        gitlab_dedicated.OP_IMPORT_A_PROJECT_FROM_A_REMOTE_ARCHIVE: None,
        gitlab_dedicated.OP_IMPORT_PROJECT_RESOURCES: None,
        package.OP_CHANGE_THE_VISIBILITY_OF_THE_CONTAINER_REGISTRY: None,
        plan.OP_CLONE_AN_ISSUE: None,
        plan.OP_CREATE_A_MERGE_REQUEST_NOTE: None,
        verify.OP_ADD_A_MERGE_REQUEST_TO_A_MERGE_TRAIN: None,
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
    """A call that steps 1 to 5 accepted: its record, its values, for a paged record the generator of its items, which
    sends nothing until it is read, the raw body ``--input`` read, ``None`` when none was given, the
    ``--route-prefix`` text given, ``None`` when none was (issue #43, design.md D3), and the ``--endpoint`` given,
    ``(method, path)``, ``None`` when none was (issue #63, design.md D1)."""

    operation: Operation
    values: Dict[str, Any]
    items: Optional[Iterator[Any]] = None
    raw_body: Optional[bytes] = None
    prefix: Optional[str] = None
    endpoint: Optional[Endpoint] = None


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
    """The ``type`` of ``--path``, ``--query``, ``-f/--raw-field`` and ``--header``: ``NAME=VALUE`` with the value as
    text."""
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


def endpoint_key(text: str) -> Endpoint:
    """The ``type`` of ``--endpoint`` (issue #63, design.md D1): ``METHOD path`` cut at its first space into the method
    and the path, each verbatim. No space, an empty method and an empty path raise ``argparse.ArgumentTypeError``
    naming ``text`` rendered with ``json.dumps``."""
    method, separator, path = text.partition(registry.ENDPOINT_SEPARATOR)
    if not separator or not method or not path:
        raise argparse.ArgumentTypeError(
            f"{json.dumps(obj=text)} is not an endpoint: give its method, one space and its path as the index writes "
            "them, e.g. 'POST /projects/:id/issues/:issue_iid/award_emoji'"
        )
    return method, path


def read_input(text: str) -> bytes:
    """The ``type`` of ``--input`` (issue #40, design.md D5): the bytes of standard input's binary buffer when ``text``
    is ``-``, else the bytes of the file ``text`` names, read whole by ``Path.read_bytes``. An ``OSError`` raises
    ``argparse.ArgumentTypeError`` naming only the path, ``text`` as given rendered with ``json.dumps``; argparse
    handles no other exception type of a ``type``."""
    try:
        if text == STDIN_INPUT:
            return sys.stdin.buffer.read()
        return Path(text).read_bytes()
    except OSError:
        raise argparse.ArgumentTypeError(f"{json.dumps(obj=text)} cannot be read") from None


# --- The values of a call (D2 step 3) ---------------------------------------------------------------------------


def _given(*, args: argparse.Namespace, dest: str) -> List[Assignment]:
    """The assignments stored under ``dest``, in command-line order; none when the option was not given."""
    return list(getattr(args, dest, None) or ())


def takes_project(*, path: str) -> bool:
    """Whether ``path`` is ``/projects/:id`` or starts with ``/projects/:id/``, so its ``id`` defaults to the
    configured project."""
    return path == PROJECT_PATH or path.startswith(PROJECT_PATH + PATH_SEPARATOR)


def path_values(*, operation: RestOperation, project: str, args: argparse.Namespace) -> Dict[str, Any]:
    """The path values of the call: the given ones, a name given twice holding its last value but a name of the
    record's ``positional_names``, which holds the list of every value given for it, in command-line order (issue #63,
    design.md D2); and ``project`` as the ``id`` of a ``/projects/:id`` path the call gives no ``id`` for (AC-1.8),
    unless ``id`` is a positional name, which has no default."""
    values: Dict[str, Any] = {}
    for each in _given(args=args, dest=ARG_PATH):
        if each.name in operation.positional_names:
            values.setdefault(each.name, []).append(each.value)
        else:
            values[each.name] = each.value
    if (
        takes_project(path=operation.path)
        and PATH_PROJECT not in values
        and PATH_PROJECT not in operation.positional_names
    ):
        values[PATH_PROJECT] = project
    return values


def attribute_values(*, operation: RestOperation, args: argparse.Namespace) -> Dict[str, Any]:
    """The attributes of the call, each named by ``registry.attribute_name``: the ``--query`` values of a name (a list
    for an ``ARRAY`` query attribute or a repeated name, else the one string), replaced by a ``-f`` or ``-F`` value of
    the same name (the last one given), replaced in turn by a ``--file``; then each ``--header`` value under the
    spelling the record declares for its name, compared ignoring case, the last one given of a name (issue #63,
    design.md D5)."""
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
    values.update(
        (_compared_name(operation=operation, dest=ARG_HEADERS, name=each.name), each.value)
        for each in _given(args=args, dest=ARG_HEADERS)
    )
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
    record, the attributes, its request headers among them under their declared spelling (issue #63, design.md D5),
    and then the path values, which win over an attribute of the same name."""
    if isinstance(operation, GraphQLOperation):
        fields = {each.name: each.value for each in _given(args=args, dest=ARG_FIELDS)}
        return {**fields, **file_values(operation=operation, args=args)}
    attributes = attribute_values(operation=operation, args=args)
    return {**attributes, **path_values(operation=operation, project=project, args=args)}


# --- D4's parameter check (D2 step 4) ---------------------------------------------------------------------------


def documented_names(*, operation: Operation) -> Dict[str, FrozenSet[str]]:
    """The names each destination may give ``operation`` (D4): the path parameters for ``--path``, a ``[.name]`` suffix
    and a container registry's ``${NAME}`` included (``registry.placeholders``), the ``Location.QUERY`` ``Param`` names
    for ``--query``, the ``QUERY`` and ``BODY`` ``Param`` names for ``-f``, ``-F`` and ``--file``, and the ``HEADER``
    ones for ``--header`` (issue #63, design.md D5); for a GraphQL record, the variables its document defines for
    ``-f`` and ``-F``, those of ``registry.upload_variables`` for ``--file`` (issue #44, design.md D4), and nothing for
    any other option, ``--header`` included."""
    if isinstance(operation, GraphQLOperation):
        return {
            ARG_FIELDS: frozenset(registry.variables(operation=operation)),
            ARG_FILES: frozenset(registry.upload_variables(operation=operation)),
        }
    attributes = frozenset(param.name for param in operation.params if param.location in FIELD_LOCATIONS)
    return {
        ARG_PATH: frozenset(registry.placeholders(path=operation.path)),
        ARG_QUERY: frozenset(param.name for param in operation.params if param.location is Location.QUERY),
        ARG_FIELDS: attributes,
        ARG_FILES: attributes,
        ARG_HEADERS: frozenset(param.name for param in operation.params if param.location is Location.HEADER),
    }


def _compared_name(*, operation: Operation, dest: str, name: str) -> str:
    """The name a given name is checked and stored as: a REST record's request header by the spelling the record
    declares for a ``HEADER`` ``Param`` whose name equals it ignoring case (RFC 9110 section 5.1; issue #63, design.md
    D5), as given when none does; a REST attribute's by ``registry.attribute_name``; any other as given."""
    if not isinstance(operation, RestOperation) or dest == ARG_PATH:
        return name
    if dest == ARG_HEADERS:
        lowered = name.lower()
        declared = (param.name for param in operation.params if param.location is Location.HEADER)
        return next((header for header in declared if header.lower() == lowered), name)
    return registry.attribute_name(name=name)


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
    """The path parameters of a REST record outside an optional ``(...)`` group and a ``[.name]`` suffix
    (``registry.required_placeholders``) that the call leaves without a value once ``id`` has its default; the
    parameter of a group may be left out, and the group is then not sent (issue #40, design.md D2). A name of the
    record's ``positional_names`` is named once for each of its places left without a value (issue #63, design.md
    D2)."""
    if isinstance(operation, GraphQLOperation):
        return []
    given = path_values(operation=operation, project=project, args=args)
    required = registry.required_placeholders(path=operation.path)
    missing: List[str] = []
    for name in dict.fromkeys(required):
        if name in operation.positional_names:
            missing.extend([name] * max(0, required.count(name) - len(given.get(name, ()))))
        elif name not in given:
            missing.append(name)
    return missing


def _surplus_problems(*, operation: Operation, args: argparse.Namespace) -> List[str]:
    """For each name of a REST record's ``positional_names`` given more ``--path`` values than the places its path
    holds it at, the problem saying so (issue #63, design.md D2)."""
    if isinstance(operation, GraphQLOperation):
        return []
    places = registry.placeholders(path=operation.path)
    given = [each.name for each in _given(args=args, dest=ARG_PATH)]
    return [
        f"the path parameter {name} is given more values than its places: {given.count(name)} for {places.count(name)}"
        for name in operation.positional_names
        if given.count(name) > places.count(name)
    ]


def _suffix_problems(*, operation: Operation, project: str, args: argparse.Namespace) -> List[str]:
    """For each ``[.name]`` suffix of a REST record's path given a value none of the record's ``suffix_values``
    equals, the problem naming the value given, rendered with ``json.dumps``, and each listed value (issue #63,
    design.md D3)."""
    if isinstance(operation, GraphQLOperation):
        return []
    given = path_values(operation=operation, project=project, args=args)
    suffixes = dict.fromkeys(
        match.group(registry.GROUP_NAME) for match in registry.OPTIONAL_SUFFIX.finditer(string=operation.path)
    )
    listed = _listed(names=[json.dumps(obj=value) for value in operation.suffix_values])
    return [
        f"the path parameter {name} is {json.dumps(obj=given[name])}, which is none of its values, {listed}"
        for name in suffixes
        if name in given and given[name] not in operation.suffix_values
    ]


def _listed(*, names: Sequence[str]) -> str:
    return LIST_SEPARATOR.join(names) if names else NOTHING_DOCUMENTED


def documented_text(*, operation: Operation) -> str:
    """The record's documented parameters as D4's message ends with them: the path parameters, a name of the record's
    ``positional_names`` once per place (issue #63, design.md D2) and any other once, and every attribute with its
    location and ``Kind``, or a GraphQL record's variables."""
    if isinstance(operation, GraphQLOperation):
        return f"its variables: {_listed(names=registry.variables(operation=operation))}"
    attributes = [f"{param.name} ({param.location.value}, {param.kind.value})" for param in operation.params]
    path_parameters: List[str] = []
    for name in registry.placeholders(path=operation.path):
        if name in operation.positional_names or name not in path_parameters:
            path_parameters.append(name)
    return f"its path parameters: {_listed(names=path_parameters)}; its attributes: {_listed(names=attributes)}"


def check_parameters(*, operation: Operation, project: str, args: argparse.Namespace) -> None:
    """D4's check: refuse with ``ValueError``, in one message, each name ``operation`` does not document, with its
    option, a request header compared ignoring case (issue #63, design.md D5); each path parameter left without a
    value, a positional name once per place; each positional name given more values than its places (D2); and each
    suffix value none of the record's ``suffix_values`` equals, with those values (D3). The message then names the
    record's documented parameters. A name or path value the caller supplied is rendered with ``json.dumps``."""
    problems = [
        f"{json.dumps(obj=name)} given with {option} is not documented"
        for name, option in undocumented(operation=operation, args=args)
    ]
    problems.extend(
        f"the path parameter {name} has no value"
        for name in missing_path_parameters(operation=operation, project=project, args=args)
    )
    problems.extend(_surplus_problems(operation=operation, args=args))
    problems.extend(_suffix_problems(operation=operation, project=project, args=args))
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


def refuse_both_bodies(*, raw_body: Optional[bytes], args: argparse.Namespace) -> None:
    """Issue #40 design.md D5 step 1: refuse with ``ValueError`` a raw body given together with one or more ``-f`` or
    ``-F`` values, in a message naming ``--input``, ``-f/--raw-field`` and ``-F/--field`` and saying that a raw-body
    record's attributes are given with ``--query``."""
    if raw_body is None or not _given(args=args, dest=ARG_FIELDS):
        return
    raise ValueError(
        f"{COMMAND} refuses {OPTION_INPUT} together with {OPTION_RAW_FIELD_SHORT}/{OPTION_RAW_FIELD} or "
        f"{OPTION_FIELD_SHORT}/{OPTION_FIELD}: a raw body is the whole request body, and a raw-body record's "
        f"attributes are given with {OPTION_QUERY}"
    )


def refuse_raw_body(*, operation: Operation, raw_body: Optional[bytes]) -> None:
    """Issue #40 design.md D5 step 2: refuse with ``ValueError`` a raw body for any record but a ``RestOperation`` with
    a ``content_type``, in a message naming its ID and ``--input`` and saying that its body is given with ``-f``,
    ``-F`` or ``--file``."""
    if raw_body is None or (isinstance(operation, RestOperation) and operation.content_type is not None):
        return
    raise ValueError(
        f"{COMMAND} refuses {OPTION_INPUT} for the GitLab operation {json.dumps(obj=operation.operation_id)}: it takes "
        f"no raw body; its body is given with {OPTION_RAW_FIELD_SHORT}, {OPTION_FIELD_SHORT} or {OPTION_FILE}"
    )


def prepare_call(*, transport: Transport, project: str, operation_id: str, args: argparse.Namespace) -> PreparedCall:
    """Steps 1 to 5, each refusal a ``ValueError`` and nothing sent: a raw body beside ``-f`` or ``-F``
    (``refuse_both_bodies``), the gate, ``registry.lookup`` on the ``--endpoint`` given (issue #63, design.md D1), a
    raw body for a record that takes none (``refuse_raw_body``), the route prefix (``registry.route``; issue #43,
    design.md D3), whose routed record every later step reads, the values, D4's check, and the shape check —
    ``registry.encode`` for a ``Paging.NONE`` REST record, ``registry.pages`` (its own look-up on the endpoint,
    encoding, ``GET``-only check and ``expand``) for a paged one. The ``PreparedCall`` of a REST record carries the
    endpoint, and that of a ``Paging.NONE`` one the ``--route-prefix`` text, for ``registry.send``."""
    raw_body: Optional[bytes] = getattr(args, ARG_RAW_BODY, None)
    prefix: Optional[str] = getattr(args, ARG_ROUTE_PREFIX, None)
    endpoint: Optional[Endpoint] = getattr(args, ARG_ENDPOINT, None)
    refuse_both_bodies(raw_body=raw_body, args=args)
    refuse_gated(operation_id=operation_id)
    operation = registry.lookup(operation_id=operation_id, endpoint=endpoint)
    refuse_raw_body(operation=operation, raw_body=raw_body)
    operation = registry.route(operation=operation, prefix=prefix)
    values = call_values(operation=operation, project=project, args=args)
    check_parameters(operation=operation, project=project, args=args)
    if isinstance(operation, GraphQLOperation):
        return PreparedCall(operation=operation, values=values)
    if operation.paging is Paging.NONE:
        registry.encode(operation=operation, values=values)
        return PreparedCall(operation=operation, values=values, raw_body=raw_body, prefix=prefix, endpoint=endpoint)
    items = registry.pages(transport=transport, operation_id=operation_id, values=values, endpoint=endpoint)
    return PreparedCall(operation=operation, values=values, items=items, endpoint=endpoint)


def print_response(*, response: Response) -> None:
    """D3's ``Paging.NONE`` output: nothing for an empty body, ``print_json`` of the decoded body when its
    ``Content-Type`` is JSON, and any other body as its bytes unchanged."""
    if not response.body:
        return
    if response.is_json:
        print_json(value=response.value)
        return
    print_bytes(data=response.body)


def send_call(*, transport: Transport, project: str, prepared: PreparedCall) -> None:
    """Step 6 and D3: a paged record's items read and printed as one array once the last page has arrived; a GraphQL
    record through ``registry.call``; a ``Paging.NONE`` record through ``registry.send``, the raw body as its
    ``data``, the ``--route-prefix`` text as its ``prefix`` (issue #43, design.md D3), the ``--endpoint`` as its
    ``endpoint`` and the configured ``project`` as its ``project``, which a container-registry record's registry token
    is asked for with (issue #63, design.md D1, D4)."""
    operation_id = prepared.operation.operation_id
    if prepared.items is not None:
        print_json(value=list(prepared.items))
        return
    if isinstance(prepared.operation, GraphQLOperation):
        print_json(value=registry.call(transport=transport, operation_id=operation_id, values=prepared.values))
        return
    response = registry.send(
        transport=transport,
        operation_id=operation_id,
        values=prepared.values,
        data=prepared.raw_body,
        prefix=prepared.prefix,
        endpoint=prepared.endpoint,
        project=project,
    )
    print_response(response=response)


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
    send_call(transport=transport, project=project, prepared=prepared)
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
    parser.add_argument(
        OPTION_INPUT,
        dest=ARG_RAW_BODY,
        default=None,
        type=read_input,
        metavar=METAVAR_FILE,
        help="the request body, its bytes sent unchanged (- reads standard input); only for a raw-body record",
    )
    parser.add_argument(
        OPTION_ROUTE_PREFIX,
        dest=ARG_ROUTE_PREFIX,
        action=ACTION_STORE,
        default=None,
        metavar=METAVAR_PREFIX,
        help=(
            "the <route-prefix> of a protocol route: one of the values its page lists, e.g. /projects/:id/packages/npm"
        ),
    )
    parser.add_argument(
        OPTION_ENDPOINT,
        dest=ARG_ENDPOINT,
        action=ACTION_STORE,
        default=None,
        type=endpoint_key,
        metavar=METAVAR_ENDPOINT,
        help="'METHOD path', one endpoint of an ID several records declare; without it, its first declared endpoint",
    )
    parser.add_argument(
        OPTION_HEADER,
        dest=ARG_HEADERS,
        action=ACTION_APPEND,
        default=None,
        type=assignment,
        metavar=METAVAR_VALUE,
        help="a request header the record declares, its name compared ignoring case",
    )
