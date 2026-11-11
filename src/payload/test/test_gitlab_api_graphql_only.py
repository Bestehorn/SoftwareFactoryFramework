"""Tests of the GitLab wrapper's GraphQL-only records, each called as ``call graphql#<member>`` (issue #44,
``design.md`` D1 to D7): ``gitlab_api/graphql_only.py`` through ``commands/call.py``, ``registry.call`` and
``Transport.graphql``.

What is pinned, every call through the product's ``main(argv=["call", ...])`` against the fake GitLab host, each answer
queued with ``FakeGitLab.script_next``:

- ``test_every_record_is_called_through_main`` (AC-2.1 to AC-2.3, AC-2.5, design D7): every record of
  ``graphql_only.OPERATIONS`` whose ID is not in ``REFUSED_IDS``, found by iterating the module, called with D7's argv —
  ``--file NAME=<a file>`` for an ``Upload`` variable (twice for a list), ``-f NAME=v-NAME`` for every other name of
  ``registry.variables`` — exits 0, posts its own document with those variables (``after`` ``null`` and then
  ``FIRST_CURSOR`` over two pages for a record with a ``connection``), or AC-3.1's parts for an ``Upload`` record, and
  prints ``data``, or both pages' nodes as one array. It fails when it calls no record. Which variables are ``Upload``
  is read with this file's ``UPLOAD_DEFINITION``, never with the product's ``registry.upload_variables``.
- ``test_every_record_id_is_looked_up_once`` (AC-1.4): ``registry.lookup`` returns each record itself.
- ``test_a_variable_holds_the_given_json_value`` (AC-2.1), ``test_a_work_item_list_prints_every_node`` (AC-2.2),
  ``test_a_graphql_failure_exits_1_with_its_details`` (AC-2.4) and ``test_a_design_upload_sends_each_file_as_a_part``
  (AC-3.1, AC-3.2): design.md § Correctness Properties, each with its cases.
- ``test_a_refused_mutation_sends_nothing`` (AC-4.1 to AC-4.3), over ``REFUSED_IDS``, and
  ``test_a_file_for_a_variable_that_is_no_upload_is_refused`` (UB-1.2): exit 2 and no request although one would be
  answered, judged with the log record of the refusal.

``test_the_usage_names_every_graphql_record`` (AC-5.1, design.md D8) reads the entry script's ``__doc__``, loaded with
``gitlab_wrapper_fixtures.load_wrapper``, within its GraphQL entry only: every capability of ``OPERATIONS`` followed by
the IDs of its records, how a variable, a file and a result are given and printed, ``exit 2`` and each ID of
``REFUSED_IDS``.

Each by this file's own constants, never the product's: ``test_every_paging_record_names_its_designed_connection``
(AC-2.2, design.md D1) holds each record's ``connection`` to ``DESIGNED_CONNECTIONS``, D1's query table;
``test_every_mutation_document_has_the_designed_shape`` (AC-1.1, D1) holds every mutation but the three of
``INLINE_INPUT_MUTATIONS`` to ``MUTATION_DOCUMENT_SHAPE``, and those three to an input object written into the
document; ``test_a_file_replaces_a_field_of_the_same_name`` (AC-3.1, D4) gives ``files`` with ``-F``/``-f`` and with
``--file`` and expects the multipart body; ``test_the_usage_says_which_mutations_are_refused`` (AC-5.1, D8) expects
D8's ``REFUSAL_SENTENCE`` in the GraphQL entry.

A JSON body is compared as parsed JSON. A ``multipart/form-data`` body is read with ``email.parser.BytesParser``, its
``Content-Type`` header prefixed, as ``test/test_gitlab_wrapper_contract.py`` ``sent_call`` reads one: each part's
``Content-Disposition`` ``name`` and ``filename``, a form field's content as JSON and a file's bytes unchanged. A
refusal and an API error are judged by their ``logging`` records (``caplog``).

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; each
package module is imported inside the test that reads it, after its file is asserted, so nothing of the product is
read when this module is collected. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded
by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_graphql_only.py`` (no network).
"""

from __future__ import annotations

import email.parser
import importlib
import importlib.util
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, NoReturn, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_graphql_only_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CALL = "call"
REGISTRY = "registry"
TRANSPORT = "transport"
GRAPHQL_ONLY = "graphql_only"

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_TOKEN_TYPE = "token_type"
TOKEN = "glpat-gitlab-graphql-only-test"  # pragma: allowlist secret
TOKEN_TYPE_JOB = "job"  # a token_type value, not a secret
PROJECT_ID = 4242

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_REFUSED = 2  # a refused `call` (#41 design.md D4)

GRAPHQL_URL = fixtures.GRAPHQL_URL
METHOD_POST = "POST"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "Content-Disposition"
HEADER_AUTHORIZATION = "Authorization"
HEADER_RETRY_AFTER = "Retry-After"
HEADER_BLOCK_END = "\r\n\r\n"
BEARER_PREFIX = "Bearer "
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
JSON_HEADERS: Tuple[Tuple[str, str], ...] = ((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON),)
PARAM_BOUNDARY = "boundary"
PARAM_NAME = "name"
PARAM_FILENAME = "filename"
TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"
STATUS_OK = 200
STATUS_BAD_GATEWAY = 502
STATUS_TOO_MANY_REQUESTS = 429
# `urllib.request.HTTPSHandler`'s method the fake host replaces, replaced again for the no-response case.
HTTPS_OPEN = "https_open"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

# The options of `call` (#41 design.md D2; design.md D3, D4).
OPTION_RAW_FIELD = "-f"
OPTION_FIELD = "-F"
OPTION_FILE = "--file"
ASSIGNMENT_SEPARATOR = "="

# The IDs the cases call (design.md D1, D2) and D6's two refused mutations.
GRAPHQL_ID_PREFIX = "graphql#"
OP_WORK_ITEM = "graphql#workItem"
OP_WORK_ITEM_UPDATE = "graphql#workItemUpdate"
OP_PROJECT_WORK_ITEMS = "graphql#Project.workItems"
OP_DESIGN_UPLOAD = "graphql#designManagementUpload"
OP_WORK_ITEM_CREATE = "graphql#workItemCreate"
OP_WORK_ITEMS_CSV_IMPORT = "graphql#workItemsCsvImport"
#: AC-4.1's mutations: each creates a work item, so ``call`` refuses it before any request (design.md D6).
REFUSED_IDS: Tuple[str, ...] = (OP_WORK_ITEM_CREATE, OP_WORK_ITEMS_CSV_IMPORT)
#: AC-4.2: the end of each refusal of ``REFUSED_IDS``; the text a refusal naming a subcommand ends with instead.
NO_SUBCOMMAND_SENDS_IT = "no subcommand sends it"
SENDS_IT = "which sends it"

# The GraphQL request body (#13 design.md D4) and the response members the transport reads (graphql/conventions.md).
FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_ERRORS = "errors"
FIELD_MESSAGE = "message"
FIELD_PATH = "path"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"
FIELD_ID = "id"
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_STATE = "state"
FIELD_WEB_URL = "webUrl"
FIELD_WORK_ITEM_TYPE = "workItemType"
FIELD_NAME = "name"
FIELD_FILENAME = "filename"
FIELD_PROJECT = "project"
FIELD_WORK_ITEM = "workItem"
FIELD_WORK_ITEMS = "workItems"
FIELD_WORK_ITEM_UPDATE = "workItemUpdate"
FIELD_DESIGN_UPLOAD = "designManagementUpload"
FIELD_DESIGNS = "designs"
FIELD_SKIPPED_DESIGNS = "skippedDesigns"
#: The member every ``data`` answer of D7's calls holds; the wrapper prints ``data`` whatever its members.
FIELD_ANSWER = "answer"
# graphql/conventions.md "File uploads": the form parts before the files; an operations path names where a file goes.
PART_OPERATIONS = "operations"
PART_MAP = "map"
OPERATIONS_PATH_SEPARATOR = "."

# D7's argv: an `Upload` variable takes files, two for a list; any other variable is `v-<name>` as text.
TEXT_VALUE_PREFIX = "v-"
LIST_UPLOAD_FILES = 2
UPLOAD_FILE_SUFFIX = ".png"
#: The bytes of a file D7's call uploads, before its own name: a PNG signature, so a byte that is not UTF-8 and a CRLF.
UPLOAD_HEAD = b"\x89PNG\r\n\x1a\n\x00\xff "
FIRST_CURSOR = "c1"
LAST_CURSOR = "c2"
FIRST_NODE = 1
SECOND_NODE = 2
#: An ``Upload`` variable of a document: ``$name``, ``:`` and the type ``Upload`` or a list of it (``[Upload!]!``), read
#: by this file and not by the product; the group ``type`` starts with ``[`` for a list.
UPLOAD_DEFINITION = re.compile(
    pattern=r"\$(?P<name>[_A-Za-z][_0-9A-Za-z]*)\s*:\s*(?P<type>\[\s*Upload\s*!?\s*\]|Upload)(?![_0-9A-Za-z])"
)
GROUP_NAME = "name"
GROUP_TYPE = "type"
LIST_TYPE_START = "["
# A word inside a message: not part of a longer name.
NAME_EDGE_BEFORE = r"(?<![A-Za-z0-9_])"
NAME_EDGE_AFTER = r"(?![A-Za-z0-9_])"

# The variables of the cases (design.md D1, D4, D5): a global ID another record prints, and a full path.
VARIABLE_ID = "id"
VARIABLE_INPUT = "input"
VARIABLE_FULL_PATH = "fullPath"
VARIABLE_PROJECT_PATH = "projectPath"
VARIABLE_IID = "iid"
VARIABLE_FILES = "files"
VARIABLE_FILE = "file"
WORK_ITEM_ID = "gid://gitlab/WorkItem/1"
FULL_PATH = "g/p"
DESIGN_ISSUE_IID = "5"
WORK_ITEMS_CONNECTION: Tuple[str, ...] = (FIELD_PROJECT, FIELD_WORK_ITEMS)
#: How a transport error names the connection of ``graphql#Project.workItems``.
WORK_ITEMS_CONNECTION_TEXT = OPERATIONS_PATH_SEPARATOR.join(WORK_ITEMS_CONNECTION)


# --- Fixtures and helpers -------------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory; the entry script reads ``config/gitlab.json`` under it."""
    monkeypatch.chdir(path=tmp_path)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` inside a test, after asserting its file, so a module not written yet fails it on an
    assertion."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str], token_type: Optional[str] = None) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's, ``token_type`` when given) under ``root``, the working
    directory, and return the exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    if token_type is not None:
        config[FIELD_TOKEN_TYPE] = token_type
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def placed(*, arguments: Sequence[str], marks: Mapping[str, Path]) -> Tuple[str, ...]:
    """``arguments`` with each mark of ``marks`` replaced by its file's path."""
    placed_arguments: List[str] = []
    for argument in arguments:
        text = argument
        for mark, path in marks.items():
            text = text.replace(mark, str(path))
        placed_arguments.append(text)
    return tuple(placed_arguments)


def assigned(*, option: str, name: str, value: Any) -> Tuple[str, str]:
    """An option and its ``NAME=VALUE``."""
    return (option, f"{name}{ASSIGNMENT_SEPARATOR}{value}")


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


def names(*, text: str, name: str) -> bool:
    """Whether ``text`` holds ``name`` as a word of its own, not inside a longer name."""
    return re.search(pattern=f"{NAME_EDGE_BEFORE}{re.escape(pattern=name)}{NAME_EDGE_AFTER}", string=text) is not None


def json_text(*, value: Any) -> str:
    """``value`` as the fake host sends a JSON answer, and so as the transport keeps it in ``details``."""
    return json.dumps(obj=value)


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def declared_document(*, operation_id: str) -> Optional[str]:
    """The document of the one record of ``graphql_only.OPERATIONS`` whose ID is ``operation_id``; ``None`` while no
    single record declares it, when ``call`` refuses the ID with exit 2, which each test checks first."""
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    documents = [str(record.document) for record in graphql_only.OPERATIONS if record.operation_id == operation_id]
    return documents[0] if len(documents) == 1 else None


def refused_messages(
    *, code: Any, fake: Any, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> List[str]:
    """Assert a refusal before any request: exit 2, nothing sent, nothing printed, an ERROR record logged; return the
    messages of the ERROR records."""
    captured = capsys.readouterr()
    messages = error_messages(caplog=caplog)
    assert code == EXIT_REFUSED, f"a refused call exits {EXIT_REFUSED}, got {code}; logged: {messages!r}"
    assert sent(fake=fake) == [], f"a refused call sends no request: {sent(fake=fake)}"
    assert captured.out == "", f"a refusal prints nothing on standard output:\n{captured.out}"
    assert messages, "call_operation logs its refusal with logger.error before returning 2; no ERROR record was logged"
    return messages


class Answer(NamedTuple):
    """One response the fake host serves to the next request: its status, headers and body (a JSON value)."""

    status: int = STATUS_OK
    headers: Tuple[Tuple[str, str], ...] = JSON_HEADERS
    body: Any = None


def queue_answers(*, fake: Any, answers: Sequence[Answer], times: int = 1) -> None:
    """Queue each answer ``times`` times, in order, for whatever request comes next."""
    for answer in answers:
        for _ in range(times):
            fake.script_next(status=answer.status, headers=answer.headers, body=answer.body)


def answer_anything(*, fake: Any) -> None:
    """Answer the next request, whatever it is, with ``data``: a refusal that sends one is then judged by its oracle,
    not by the fake host's unscripted-request error."""
    queue_answers(fake=fake, answers=(Answer(body={FIELD_DATA: {FIELD_ANSWER: None}}),))


def connection_page(*, connection: Sequence[str], nodes: Sequence[Any], page_info: Mapping[str, Any]) -> Dict[str, Any]:
    """A GraphQL response holding one page of ``nodes`` and its ``pageInfo`` at the key path ``connection`` under
    ``data``."""
    page: Any = {FIELD_NODES: list(nodes), FIELD_PAGE_INFO: dict(page_info)}
    for key in reversed(connection):
        page = {key: page}
    return {FIELD_DATA: page}


def two_pages(*, connection: Sequence[str], first: Any, second: Any) -> Tuple[Answer, Answer]:
    """The pages of a connection holding ``first`` and then ``second``: the first names ``FIRST_CURSOR`` as its
    ``endCursor`` with ``hasNextPage`` ``true``; the second is the last."""
    return (
        Answer(
            body=connection_page(
                connection=connection,
                nodes=(first,),
                page_info={FIELD_HAS_NEXT_PAGE: True, FIELD_END_CURSOR: FIRST_CURSOR},
            )
        ),
        Answer(
            body=connection_page(
                connection=connection,
                nodes=(second,),
                page_info={FIELD_HAS_NEXT_PAGE: False, FIELD_END_CURSOR: LAST_CURSOR},
            )
        ),
    )


# --- The posted body, read by this file's own oracle ---------------------------------------------------------------


@dataclass(frozen=True)
class Part:
    """One part of a multipart body: its ``Content-Disposition`` ``name`` and ``filename`` (``None`` for a form field),
    and its content — a form field's JSON value (its text when it is not JSON), a file's bytes unchanged."""

    name: Optional[str]
    filename: Optional[str]
    content: Any


@dataclass(frozen=True)
class GivenFile:
    """A file a call names with ``--file``: the operations path it fills, its path and the bytes written to it."""

    operations_path: str
    path: Path
    content: bytes


def media_type(*, value: Optional[str]) -> Optional[str]:
    """The media type of a ``Content-Type`` value, lower-cased and without its parameters; ``None`` without one."""
    if value is None:
        return None
    message = Message()
    message[HEADER_CONTENT_TYPE] = value
    return message.get_content_type()


def field_content(*, content: bytes) -> Any:
    """A form field's content: its JSON value, or its text when it is not JSON."""
    text = content.decode(encoding=TEXT_ENCODING)
    try:
        return json.loads(s=text)
    except ValueError:
        return text


def body_part(*, part: Message) -> Part:
    """One part of a parsed multipart body, as ``Part``."""
    name = part.get_param(param=PARAM_NAME, header=HEADER_CONTENT_DISPOSITION)
    filename = part.get_param(param=PARAM_FILENAME, header=HEADER_CONTENT_DISPOSITION)
    content = part.get_payload(decode=True)
    assert isinstance(content, bytes), f"a multipart part without content: {part!r}"
    if filename is None:
        return Part(name=None if name is None else str(name), filename=None, content=field_content(content=content))
    return Part(name=None if name is None else str(name), filename=str(filename), content=content)


def multipart_parts(*, body: bytes, content_type: str) -> Tuple[Part, ...]:
    """The parts of a ``multipart/form-data`` body in body order, read with ``email.parser.BytesParser`` with its
    ``Content-Type`` header prefixed (``test_gitlab_wrapper_contract.py`` ``multipart_names``)."""
    head = f"{HEADER_CONTENT_TYPE}: {content_type}{HEADER_BLOCK_END}".encode(encoding=ASCII_ENCODING)
    message = email.parser.BytesParser().parsebytes(text=head + body)
    boundary = message.get_param(param=PARAM_BOUNDARY)
    assert isinstance(boundary, str) and boundary, f"a multipart Content-Type names its boundary: {content_type!r}"
    assert message.is_multipart(), f"a {CONTENT_TYPE_MULTIPART} body that is not multipart: {body!r}"
    parts: List[Part] = []
    for part in message.get_payload():
        assert isinstance(part, Message), f"a multipart body whose part is not a message: {part!r}"
        parts.append(body_part(part=part))
    return tuple(parts)


def posted(*, request: Any) -> Tuple[Optional[str], Any]:
    """A recorded request's body by its media type: a JSON value, the parts of a multipart body, else the raw bytes."""
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    media = media_type(value=content_type)
    if media == CONTENT_TYPE_MULTIPART:
        return media, multipart_parts(body=request.body or b"", content_type=str(content_type))
    if media == CONTENT_TYPE_JSON:
        return media, request.json()
    return media, request.body


def json_post(*, document: Optional[str], variables: Mapping[str, Any]) -> Tuple[str, Any]:
    """The JSON body ``Transport.graphql`` posts: ``query`` the document, ``variables`` the variables."""
    return CONTENT_TYPE_JSON, {FIELD_QUERY: document, FIELD_VARIABLES: dict(variables)}


def multipart_post(
    *, document: Optional[str], variables: Mapping[str, Any], files: Sequence[GivenFile]
) -> Tuple[str, Tuple[Part, ...]]:
    """AC-3.1's multipart body (graphql/conventions.md "File uploads", design.md D4): ``operations``, the JSON of the
    document and the variables, each file's place ``null``; ``map``, each part name ``str(i)`` mapped to a list holding
    the i-th file's operations path; then the i-th file as the part ``str(i)``, its name and bytes unchanged."""
    operations = {FIELD_QUERY: document, FIELD_VARIABLES: dict(variables)}
    file_map = {str(index): [given.operations_path] for index, given in enumerate(files)}
    file_parts = tuple(
        Part(name=str(index), filename=given.path.name, content=given.content) for index, given in enumerate(files)
    )
    return CONTENT_TYPE_MULTIPART, (
        Part(name=PART_OPERATIONS, filename=None, content=operations),
        Part(name=PART_MAP, filename=None, content=file_map),
        *file_parts,
    )


def operations_path(*, name: str, index: Optional[int] = None) -> str:
    """The operations path a file fills: ``variables.<name>``, or ``variables.<name>.<index>`` for a list item."""
    path = f"{FIELD_VARIABLES}{OPERATIONS_PATH_SEPARATOR}{name}"
    return path if index is None else f"{path}{OPERATIONS_PATH_SEPARATOR}{index}"


# --- AC-2.1 to AC-2.3, AC-2.5: every record called through main -----------------------------------------------------


@dataclass(frozen=True)
class PlannedCall:
    """D7's call of one record: the argv after its ID, the answers queued, the body of each request it posts, in
    order, and its standard output."""

    arguments: Tuple[str, ...]
    answers: Tuple[Answer, ...]
    posts: Tuple[Tuple[str, Any], ...]
    printed: str


def upload_definitions(*, document: str) -> Dict[str, bool]:
    """Each ``Upload`` variable ``document`` defines, by ``UPLOAD_DEFINITION``, mapped to whether it is a list."""
    return {
        match.group(GROUP_NAME): match.group(GROUP_TYPE).startswith(LIST_TYPE_START)
        for match in UPLOAD_DEFINITION.finditer(string=document)
    }


def given_values(
    *, names: Sequence[str], uploads: Mapping[str, bool], directory: Path, slug: str
) -> Tuple[Tuple[str, ...], Dict[str, Any], Tuple[GivenFile, ...]]:
    """D7's argv for the declared variables ``names``: ``--file NAME=<a new file>`` for an ``Upload`` variable, twice
    for a list, and ``-f NAME=v-NAME`` for any other; the variables the request holds (each file's place ``None``);
    and the files in command-line order, each with the operations path it fills."""
    arguments: List[str] = []
    variables: Dict[str, Any] = {}
    files: List[GivenFile] = []
    for name in names:
        if name not in uploads:
            text = f"{TEXT_VALUE_PREFIX}{name}"
            arguments.extend(assigned(option=OPTION_RAW_FIELD, name=name, value=text))
            variables[name] = text
            continue
        indexes: Sequence[Optional[int]] = range(LIST_UPLOAD_FILES) if uploads[name] else (None,)
        for index in indexes:
            path = directory / f"{slug}-{name}-{index}{UPLOAD_FILE_SUFFIX}"
            content = UPLOAD_HEAD + path.name.encode(encoding=ASCII_ENCODING) + b"\r\n"
            path.write_bytes(data=content)
            arguments.extend(assigned(option=OPTION_FILE, name=name, value=path))
            files.append(GivenFile(operations_path=operations_path(name=name, index=index), path=path, content=content))
        variables[name] = [None] * LIST_UPLOAD_FILES if uploads[name] else None
    return tuple(arguments), variables, tuple(files)


def node_of(*, operation_id: str, number: int) -> Dict[str, Any]:
    """The ``number``-th node a connection of the record ``operation_id`` is answered with."""
    return {FIELD_ID: f"{operation_id}/{number}"}


def plan_record_call(*, registry: ModuleType, record: Any, directory: Path, slug: str) -> PlannedCall:
    """D7's call of ``record``: its argv, answers and oracle — two pages and their nodes for a record with a
    ``connection``, else one ``data`` answer, posted as JSON or, with a file, as AC-3.1's parts."""
    operation_id = str(record.operation_id)
    document = str(record.document)
    arguments, variables, files = given_values(
        names=registry.variables(operation=record),
        uploads=upload_definitions(document=document),
        directory=directory,
        slug=slug,
    )
    if record.connection:
        first = node_of(operation_id=operation_id, number=FIRST_NODE)
        second = node_of(operation_id=operation_id, number=SECOND_NODE)
        return PlannedCall(
            arguments=arguments,
            answers=two_pages(connection=tuple(record.connection), first=first, second=second),
            posts=tuple(
                json_post(document=document, variables={**variables, FIELD_AFTER: after})
                for after in (None, FIRST_CURSOR)
            ),
            printed=printed_json(value=[first, second]),
        )
    data = {FIELD_ANSWER: {FIELD_ID: operation_id}}
    if files:
        post = multipart_post(document=document, variables=variables, files=files)
    else:
        post = json_post(document=document, variables=variables)
    return PlannedCall(
        arguments=arguments,
        answers=(Answer(body={FIELD_DATA: data}),),
        posts=(post,),
        printed=printed_json(value=data),
    )


def judge_call(*, operation_id: str, planned: PlannedCall, code: Any, fake: Any, out: str, logged: List[str]) -> None:
    """D7's oracle for one call: exit 0; one ``POST`` to ``/api/graphql`` per page, each carrying ``Authorization:
    Bearer`` and the planned body; standard output the planned text."""
    pages = len(planned.posts)
    assert code == EXIT_OK, f"call {operation_id} exits {code}, not {EXIT_OK}; logged: {logged!r}"
    assert sent(fake=fake) == [(METHOD_POST, GRAPHQL_URL)] * pages, (
        f"call {operation_id} sends {pages} POST to {GRAPHQL_URL}, one per page: {sent(fake=fake)}"
    )
    bodies = [posted(request=request) for request in fake.requests]
    assert bodies == list(planned.posts), (
        f"call {operation_id} posts its document with the given variables (after null then {FIRST_CURSOR!r} on a "
        f"connection), or AC-3.1's parts for an Upload variable:\nposted   {bodies!r}\nexpected {list(planned.posts)!r}"
    )
    assert [request.header(name=HEADER_AUTHORIZATION) for request in fake.requests] == [
        BEARER_PREFIX + TOKEN
    ] * pages, f"call {operation_id}: GraphQL carries the token as Authorization: Bearer (#13 AC-4.1)"
    assert out == planned.printed, f"call {operation_id} prints data, or both pages' nodes as one array:\n{out}"


def test_every_record_is_called_through_main(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.1 to AC-2.3, AC-2.5 (design.md D7): every record of ``graphql_only.OPERATIONS`` whose ID is not in
    ``REFUSED_IDS``, called through ``main`` with D7's argv against a fake host of its own, exits 0, posts what
    ``judge_call`` expects and prints its ``data`` or its nodes; the test fails when it calls no record."""
    registry = gitlab_module(name=REGISTRY)
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    called: List[str] = []
    for index, record in enumerate(graphql_only.OPERATIONS):
        operation_id = str(record.operation_id)
        if operation_id in REFUSED_IDS:
            continue
        planned = plan_record_call(registry=registry, record=record, directory=project, slug=f"record-{index}")
        fake = fixtures.FakeGitLab().install(monkeypatch=monkeypatch)
        queue_answers(fake=fake, answers=planned.answers)
        caplog.clear()
        code = run_call(root=project, argv=(operation_id, *planned.arguments))
        out = capsys.readouterr().out
        judge_call(
            operation_id=operation_id,
            planned=planned,
            code=code,
            fake=fake,
            out=out,
            logged=error_messages(caplog=caplog),
        )
        called.append(operation_id)

    assert called, (
        "graphql_only.OPERATIONS holds no record outside REFUSED_IDS, so no GraphQL call was proven (AC-2.5): "
        f"{[record.operation_id for record in graphql_only.OPERATIONS]}"
    )


# --- AC-1.4: every record ID is looked up once ---------------------------------------------------------------------


def lookup_problems(*, registry: ModuleType, record: Any) -> List[str]:
    """Why ``registry.lookup`` does not return ``record`` itself for its ID: its refusal, or another record."""
    try:
        found = registry.lookup(operation_id=record.operation_id)
    except ValueError as refusal:
        return [f"{record.operation_id}: lookup refuses it: {refusal}"]
    if found is not record:
        return [f"{record.operation_id}: lookup returns {found!r}, not the graphql_only record"]
    return []


def test_every_record_id_is_looked_up_once() -> None:
    """AC-1.4: for every record of ``graphql_only.OPERATIONS``, ``registry.lookup(operation_id=...)`` over every family
    module and ``graphql_only`` returns that record; it fails on an empty ``OPERATIONS``."""
    registry = gitlab_module(name=REGISTRY)
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    records = tuple(graphql_only.OPERATIONS)
    assert records, "graphql_only.OPERATIONS holds no record, so no GraphQL record's ID is proven (AC-1.4)"

    problems = [problem for record in records for problem in lookup_problems(registry=registry, record=record)]

    assert not problems, "records registry.lookup does not return once:\n" + "\n".join(problems)


# --- AC-2.2: every record that pages names design D1's connection --------------------------------------------------

FIELD_GROUP = "group"
FIELD_NAMESPACE = "namespace"
FIELD_WORK_ITEMS_BY_REFERENCE = "workItemsByReference"
FIELD_BRANCH_RULES = "branchRules"
FIELD_VULNERABILITIES = "vulnerabilities"
OP_WORK_ITEMS_BY_REFERENCE = "graphql#workItemsByReference"
OP_GROUP_WORK_ITEMS = "graphql#Group.workItems"
OP_NAMESPACE_WORK_ITEMS = "graphql#Namespace.workItems"
OP_PROJECT_BRANCH_RULES = "graphql#Project.branchRules"
OP_GROUP_VULNERABILITIES = "graphql#Group.vulnerabilities"
OP_QUERY_VULNERABILITIES = "graphql#Query.vulnerabilities"
#: Design D1's query table, its ``connection`` column written out: the key path under ``data`` of every record that
#: pages, by its ID. A record whose ID is not here pages nothing, ``NO_CONNECTION``.
DESIGNED_CONNECTIONS: Mapping[str, Tuple[str, ...]] = {
    OP_WORK_ITEMS_BY_REFERENCE: (FIELD_WORK_ITEMS_BY_REFERENCE,),
    OP_PROJECT_WORK_ITEMS: (FIELD_PROJECT, FIELD_WORK_ITEMS),
    OP_GROUP_WORK_ITEMS: (FIELD_GROUP, FIELD_WORK_ITEMS),
    OP_NAMESPACE_WORK_ITEMS: (FIELD_NAMESPACE, FIELD_WORK_ITEMS),
    OP_PROJECT_BRANCH_RULES: (FIELD_PROJECT, FIELD_BRANCH_RULES),
    OP_GROUP_VULNERABILITIES: (FIELD_GROUP, FIELD_VULNERABILITIES),
    OP_QUERY_VULNERABILITIES: (FIELD_VULNERABILITIES,),
}
NO_CONNECTION: Tuple[str, ...] = ()


def designed_connection_problems(*, records: Sequence[Any]) -> List[str]:
    """Each record whose ``connection`` is not design D1's — ``DESIGNED_CONNECTIONS``' for its ID, ``NO_CONNECTION``
    for any other ID — and each ID of ``DESIGNED_CONNECTIONS`` that no record declares."""
    problems: List[str] = []
    for record in records:
        operation_id = str(record.operation_id)
        designed = DESIGNED_CONNECTIONS.get(operation_id, NO_CONNECTION)
        if tuple(record.connection) != designed:
            problems.append(f"{operation_id}: its connection is {tuple(record.connection)!r}, design D1's {designed!r}")
    declared = {str(record.operation_id) for record in records}
    problems.extend(
        f"{operation_id}: design D1 pages it at {connection!r}, but no record declares it"
        for operation_id, connection in DESIGNED_CONNECTIONS.items()
        if operation_id not in declared
    )
    return problems


def test_every_paging_record_names_its_designed_connection() -> None:
    """AC-2.2 (design.md D1): every record of ``graphql_only.OPERATIONS`` whose ID is in ``DESIGNED_CONNECTIONS``, D1's
    query table written out here, has that ``connection``, so ``call`` prints the nodes of every page; every other
    record has none; every ID of the table is a record. It fails when ``OPERATIONS`` holds no record."""
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    records = tuple(graphql_only.OPERATIONS)
    assert records, "graphql_only.OPERATIONS holds no record, so no connection is proven (AC-2.2)"

    problems = designed_connection_problems(records=records)

    assert not problems, "records whose connection is not design D1's:\n" + "\n".join(problems)


# --- AC-1.1: every mutation document has design D1's shape ---------------------------------------------------------

#: How the document of a mutation record starts.
MUTATION_KEYWORD = "mutation"
OP_PIPELINE_CREATE = "graphql#pipelineCreate"
#: Design D1's three mutations that write their input object into the document, each of its fields a variable of its
#: own: two take an ``Upload`` (D4), and ``pipelineCreate``'s input holds ``async: true``. Every other mutation takes
#: ``$input``.
INLINE_INPUT_MUTATIONS: Tuple[str, ...] = (OP_DESIGN_UPLOAD, OP_PIPELINE_CREATE, OP_WORK_ITEMS_CSV_IMPORT)
#: Design D1's ``$input`` mutation, ``mutation($input: <I>!) { <m>(input: $input) { <selection> errors } }``, with any
#: white space between its tokens: the one variable ``$input``, of a non-null named type; a root field called with
#: ``(input: $input)``; a selection of at least one field, then ``errors`` last. The group ``selection`` is what comes
#: before ``errors``.
MUTATION_DOCUMENT_SHAPE = re.compile(
    pattern=(
        r"\Amutation\s*\(\s*\$input\s*:\s*[_A-Za-z][_0-9A-Za-z]*\s*!\s*\)\s*\{"
        r"\s*[_A-Za-z][_0-9A-Za-z]*\s*\(\s*input\s*:\s*\$input\s*\)\s*\{"
        r"\s*(?P<selection>[_A-Za-z].*?)\s+errors\s*\}\s*\}\s*\Z"
    ),
    flags=re.DOTALL,
)
GROUP_SELECTION = "selection"
#: A definition of the variable ``$input``: ``$input``, then ``:`` after any white space.
INPUT_DEFINITION = re.compile(pattern=r"\$input\s*:")
#: An ``input`` argument whose value is an object written into the document: ``(input: {``.
INLINE_INPUT_ARGUMENT = re.compile(pattern=r"\(\s*input\s*:\s*\{")
OPENING_BRACE = "{"
CLOSING_BRACE = "}"
#: D1's ``$input`` shape, as a failure names it.
MUTATION_SHAPE_TEXT = "mutation($input: <I>!) { <m>(input: $input) { <selection> errors } }"


def selection_is_unbalanced(*, selection: str) -> bool:
    """Whether ``selection`` closes a brace it did not open, or leaves one open: what a second root field after the
    first one's selection leaves in the text ``MUTATION_DOCUMENT_SHAPE`` reads as the selection."""
    depth = 0
    for character in selection:
        if character == OPENING_BRACE:
            depth += 1
        elif character == CLOSING_BRACE:
            depth -= 1
            if depth < 0:
                return True
    return depth != 0


def mutation_shape_problems(*, operation_id: str, document: str) -> List[str]:
    """Why the mutation ``document`` of the record ``operation_id`` does not have design D1's shape: for an ID of
    ``INLINE_INPUT_MUTATIONS``, a ``$input`` definition or no ``input`` object written into it; for any other, no match
    of ``MUTATION_DOCUMENT_SHAPE`` or a second root field. None when it has."""
    if operation_id in INLINE_INPUT_MUTATIONS:
        problems: List[str] = []
        if INPUT_DEFINITION.search(string=document) is not None:
            problems.append(
                f"{operation_id}: design D1 writes its input object into the document, not $input: {document}"
            )
        if INLINE_INPUT_ARGUMENT.search(string=document) is None:
            problems.append(
                f"{operation_id}: no input object is written into the document as (input: {{...}}): {document}"
            )
        return problems
    shape = MUTATION_DOCUMENT_SHAPE.match(string=document)
    if shape is None:
        return [f"{operation_id}: the document is not {MUTATION_SHAPE_TEXT}: {document}"]
    if selection_is_unbalanced(selection=shape.group(GROUP_SELECTION)):
        return [f"{operation_id}: the document selects more than one root field, or leaves a brace open: {document}"]
    return []


def test_every_mutation_document_has_the_designed_shape() -> None:
    """AC-1.1 (design.md D1): the document of every record of ``graphql_only.OPERATIONS`` that starts with
    ``mutation`` and whose ID is not in ``INLINE_INPUT_MUTATIONS`` is ``mutation($input: <I>!) { <m>(input: $input) {
    <selection> errors } }`` — one ``$input`` of a non-null type, one root field called with ``(input: $input)``,
    ``errors`` last — judged by ``MUTATION_DOCUMENT_SHAPE`` and ``selection_is_unbalanced``, not by the product's
    builder; each ID of ``INLINE_INPUT_MUTATIONS`` is a mutation record that defines no ``$input`` and writes its input
    object into the document. It fails when no record is a mutation, or none takes ``$input``."""
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    mutations = [
        (str(record.operation_id), str(record.document))
        for record in graphql_only.OPERATIONS
        if str(record.document).startswith(MUTATION_KEYWORD)
    ]
    assert mutations, (
        f"graphql_only.OPERATIONS holds no record whose document starts with {MUTATION_KEYWORD!r}: "
        f"{[record.operation_id for record in graphql_only.OPERATIONS]}"
    )
    assert [operation_id for operation_id, _ in mutations if operation_id not in INLINE_INPUT_MUTATIONS], (
        f"every mutation record is one of INLINE_INPUT_MUTATIONS, so no $input document was judged: {mutations!r}"
    )
    declared = {operation_id for operation_id, _ in mutations}

    problems = [
        f"{operation_id}: design D1 writes its input object into its document, but no mutation record declares it"
        for operation_id in INLINE_INPUT_MUTATIONS
        if operation_id not in declared
    ]
    problems.extend(
        problem
        for operation_id, document in mutations
        for problem in mutation_shape_problems(operation_id=operation_id, document=document)
    )

    assert not problems, "mutation documents without design D1's shape:\n" + "\n".join(problems)


# --- AC-2.1: a variable holds the JSON value the caller gave -------------------------------------------------------

UPDATE_DATA: Dict[str, Any] = {
    FIELD_WORK_ITEM_UPDATE: {
        FIELD_WORK_ITEM: {FIELD_ID: WORK_ITEM_ID, FIELD_IID: "1", FIELD_TITLE: "Renamed", FIELD_STATE: "OPEN"},
        FIELD_ERRORS: [],
    }
}


class VariableValue(NamedTuple):
    """``input`` given as ``text`` with ``option``, and the JSON value the posted ``variables`` must hold for it."""

    slug: str
    option: str
    text: str
    value: Any


VARIABLE_VALUES: Tuple[VariableValue, ...] = (
    VariableValue(slug="text", option=OPTION_RAW_FIELD, text="text", value="text"),
    VariableValue(slug="number", option=OPTION_FIELD, text="5", value=5),
    VariableValue(slug="boolean", option=OPTION_FIELD, text="true", value=True),
    VariableValue(slug="array", option=OPTION_FIELD, text='["a"]', value=["a"]),
    VariableValue(
        slug="object",
        option=OPTION_FIELD,
        text=json.dumps(obj={FIELD_ID: WORK_ITEM_ID}),
        value={FIELD_ID: WORK_ITEM_ID},
    ),
    VariableValue(slug="null", option=OPTION_FIELD, text="null", value=None),
)


def variable_value_name(given: VariableValue) -> str:
    """The test id of a ``VARIABLE_VALUES`` row."""
    return given.slug


@pytest.mark.parametrize(argnames="given", argvalues=VARIABLE_VALUES, ids=variable_value_name)
def test_a_variable_holds_the_given_json_value(
    given: VariableValue,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.1: ``call graphql#workItemUpdate`` with ``-f input=text``, or ``-F input=<JSON>``, sends one ``POST`` to
    ``/api/graphql`` with ``Authorization: Bearer <token>``, whose ``query`` is the record's document and whose
    ``variables`` are ``{"input": <the value>}`` of the same JSON kind (compared by ``json.dumps(sort_keys=True)``:
    ``true`` is not ``1``), and prints ``data``."""
    document = declared_document(operation_id=OP_WORK_ITEM_UPDATE)
    queue_answers(fake=fake_gitlab, answers=(Answer(body={FIELD_DATA: UPDATE_DATA}),))

    code = run_call(
        root=project, argv=(OP_WORK_ITEM_UPDATE, *assigned(option=given.option, name=VARIABLE_INPUT, value=given.text))
    )

    out = capsys.readouterr().out
    assert code == EXIT_OK, (
        f"call {OP_WORK_ITEM_UPDATE} exits {code}, not {EXIT_OK}; logged: {error_messages(caplog=caplog)!r}"
    )
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)], (
        f"one POST to {GRAPHQL_URL}: {sent(fake=fake_gitlab)}"
    )
    request = fake_gitlab.requests[0]
    assert request.header(name=HEADER_AUTHORIZATION) == BEARER_PREFIX + TOKEN, "GraphQL sends Authorization: Bearer"
    media, body = posted(request=request)
    assert media == CONTENT_TYPE_JSON, f"a call with no file posts a JSON body, not {media}"
    assert body[FIELD_QUERY] == document, f"the posted query is the record's document: {body[FIELD_QUERY]!r}"
    sent_variables = json.dumps(obj=body[FIELD_VARIABLES], sort_keys=True)
    expected = json.dumps(obj={VARIABLE_INPUT: given.value}, sort_keys=True)
    assert sent_variables == expected, f"the posted variables are {sent_variables}, not {expected} (AC-2.1)"
    assert out == printed_json(value=UPDATE_DATA), f"the call prints data as print_json writes it (AC-2.3):\n{out}"


# --- AC-2.2: a connection prints every node of every page ----------------------------------------------------------

LIST_ARGUMENTS: Tuple[str, ...] = assigned(option=OPTION_RAW_FIELD, name=VARIABLE_FULL_PATH, value=FULL_PATH)
WORK_ITEM_NODES: Tuple[Dict[str, Any], ...] = (
    {
        FIELD_ID: WORK_ITEM_ID,
        FIELD_IID: "1",
        FIELD_TITLE: "First",
        FIELD_STATE: "OPEN",
        FIELD_WEB_URL: f"https://{fixtures.HOST}/g/p/-/work_items/1",
        FIELD_WORK_ITEM_TYPE: {FIELD_ID: "gid://gitlab/WorkItems::Type/1", FIELD_NAME: "Issue"},
    },
    {
        FIELD_ID: "gid://gitlab/WorkItem/2",
        FIELD_IID: "2",
        FIELD_TITLE: "Second",
        FIELD_STATE: "CLOSED",
        FIELD_WEB_URL: f"https://{fixtures.HOST}/g/p/-/work_items/2",
        FIELD_WORK_ITEM_TYPE: {FIELD_ID: "gid://gitlab/WorkItems::Type/5", FIELD_NAME: "Task"},
    },
)


def test_a_work_item_list_prints_every_node(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """AC-2.2: ``call graphql#Project.workItems -f fullPath=g/p`` over two pages posts twice, ``after`` ``null`` and
    then the first page's ``endCursor``, prints both pages' nodes as one JSON array once the last page has arrived,
    and exits 0."""
    document = declared_document(operation_id=OP_PROJECT_WORK_ITEMS)
    first, second = WORK_ITEM_NODES
    queue_answers(fake=fake_gitlab, answers=two_pages(connection=WORK_ITEMS_CONNECTION, first=first, second=second))

    code = run_call(root=project, argv=(OP_PROJECT_WORK_ITEMS, *LIST_ARGUMENTS))

    out = capsys.readouterr().out
    assert code == EXIT_OK, (
        f"call {OP_PROJECT_WORK_ITEMS} exits {code}, not {EXIT_OK}; logged: {error_messages(caplog=caplog)!r}"
    )
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)] * 2, f"one POST per page: {sent(fake=fake_gitlab)}"
    assert [posted(request=request) for request in fake_gitlab.requests] == [
        json_post(document=document, variables={VARIABLE_FULL_PATH: FULL_PATH, FIELD_AFTER: after})
        for after in (None, FIRST_CURSOR)
    ], f"each page posts the record's document, after null and then the first page's endCursor {FIRST_CURSOR!r}"
    assert out == printed_json(value=list(WORK_ITEM_NODES)), (
        f"one JSON array of both pages' nodes, in page order, as print_json writes it (AC-2.2):\n{out}"
    )


# --- AC-2.4: a GraphQL failure exits 1 with its message and details ------------------------------------------------

WORK_ITEM_ARGUMENTS: Tuple[str, ...] = assigned(option=OPTION_RAW_FIELD, name=VARIABLE_ID, value=WORK_ITEM_ID)
UPDATE_ARGUMENTS: Tuple[str, ...] = assigned(
    option=OPTION_FIELD, name=VARIABLE_INPUT, value=json.dumps(obj={FIELD_ID: WORK_ITEM_ID, FIELD_TITLE: ""})
)
#: The mark ``test_a_graphql_failure_exits_1_with_its_details`` replaces with the path of a file it never writes.
MISSING_MARK = "<missing-file>"
MISSING_FILE_NAME = "never-written-design.png"
DESIGN_ARGUMENTS: Tuple[str, ...] = (
    *assigned(option=OPTION_RAW_FIELD, name=VARIABLE_PROJECT_PATH, value=FULL_PATH),
    *assigned(option=OPTION_RAW_FIELD, name=VARIABLE_IID, value=DESIGN_ISSUE_IID),
)
WORK_ITEM_DATA: Dict[str, Any] = {FIELD_WORK_ITEM: WORK_ITEM_NODES[0]}
GRAPHQL_ERROR_TEXT = "The resource that you are attempting to access does not exist"
GRAPHQL_ERRORS: Tuple[Dict[str, Any], ...] = ({FIELD_MESSAGE: GRAPHQL_ERROR_TEXT, FIELD_PATH: [FIELD_WORK_ITEM]},)
PAYLOAD_ERROR_TEXT = "Title can't be blank"
BAD_GATEWAY_TEXT = "502 Bad Gateway"
RATE_LIMITED_TEXT = "Retry later"
NO_RESPONSE_REASON = "the fake host closed the connection without a response"
# What the transport's errors name (transport.py `Transport.graphql`, `graphql_nodes`, `_connection`): a body that is
# no JSON object, an absent connection, a next page without a cursor, and a job token.
NOT_A_JSON_OBJECT = "not a JSON object"
ABSENT_CONNECTION = "absent or forbidden"
JOB_TOKEN_TEXT = "job token"


@dataclass(frozen=True)
class FailureCase:
    """An AC-2.4 case: ``call <operation_id>`` with ``arguments``, answered with ``answers`` in turn (each once per
    attempt when ``rate_limited``; recorded and never answered when ``no_response``).

    ``message`` holds the texts one log record holds; ``details`` says that another record holds the last answer's body
    as the fake host sent it. ``posts`` is the number of requests sent, unless ``rate_limited``: one per attempt."""

    slug: str
    operation_id: str
    arguments: Tuple[str, ...]
    answers: Tuple[Answer, ...]
    message: Tuple[str, ...]
    details: bool = False
    posts: int = 1
    rate_limited: bool = False
    no_response: bool = False
    token_type: Optional[str] = None


FAILURE_CASES: Tuple[FailureCase, ...] = (
    FailureCase(
        slug="errors-without-data",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(body={FIELD_ERRORS: list(GRAPHQL_ERRORS)}),),
        message=(GRAPHQL_URL, GRAPHQL_ERROR_TEXT),
        details=True,
    ),
    FailureCase(
        slug="errors-with-data",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(body={FIELD_DATA: {FIELD_WORK_ITEM: None}, FIELD_ERRORS: list(GRAPHQL_ERRORS)}),),
        message=(GRAPHQL_URL, GRAPHQL_ERROR_TEXT),
        details=True,
    ),
    FailureCase(
        slug="mutation-payload-errors",
        operation_id=OP_WORK_ITEM_UPDATE,
        arguments=UPDATE_ARGUMENTS,
        answers=(
            Answer(
                body={FIELD_DATA: {FIELD_WORK_ITEM_UPDATE: {FIELD_WORK_ITEM: None, FIELD_ERRORS: [PAYLOAD_ERROR_TEXT]}}}
            ),
        ),
        message=(GRAPHQL_URL, PAYLOAD_ERROR_TEXT),
        details=True,
    ),
    FailureCase(
        slug="http-502",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(status=STATUS_BAD_GATEWAY, body={FIELD_MESSAGE: BAD_GATEWAY_TEXT}),),
        message=(GRAPHQL_URL, BAD_GATEWAY_TEXT),
        details=True,
    ),
    FailureCase(
        slug="spent-429-retries",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(
            Answer(
                status=STATUS_TOO_MANY_REQUESTS,
                headers=(*JSON_HEADERS, (HEADER_RETRY_AFTER, "0")),  # no wait between the retries
                body={FIELD_MESSAGE: RATE_LIMITED_TEXT},
            ),
        ),
        message=(GRAPHQL_URL, RATE_LIMITED_TEXT),
        details=True,
        rate_limited=True,
    ),
    FailureCase(
        slug="no-response",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(body={FIELD_DATA: WORK_ITEM_DATA}),),
        message=(GRAPHQL_URL, NO_RESPONSE_REASON),
        no_response=True,
    ),
    FailureCase(
        slug="body-that-is-no-json-object",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(body=[]),),
        message=(GRAPHQL_URL, NOT_A_JSON_OBJECT),
        details=True,
    ),
    FailureCase(
        slug="absent-connection",
        operation_id=OP_PROJECT_WORK_ITEMS,
        arguments=LIST_ARGUMENTS,
        answers=(Answer(body={FIELD_DATA: {FIELD_PROJECT: None}}),),
        message=(WORK_ITEMS_CONNECTION_TEXT, ABSENT_CONNECTION),
    ),
    FailureCase(
        slug="next-page-without-end-cursor",
        operation_id=OP_PROJECT_WORK_ITEMS,
        arguments=LIST_ARGUMENTS,
        answers=(
            Answer(
                body=connection_page(
                    connection=WORK_ITEMS_CONNECTION, nodes=WORK_ITEM_NODES[:1], page_info={FIELD_HAS_NEXT_PAGE: True}
                )
            ),
        ),
        message=(WORK_ITEMS_CONNECTION_TEXT, FIELD_END_CURSOR),
    ),
    FailureCase(
        slug="job-token",
        operation_id=OP_WORK_ITEM,
        arguments=WORK_ITEM_ARGUMENTS,
        answers=(Answer(body={FIELD_DATA: WORK_ITEM_DATA}),),
        message=(JOB_TOKEN_TEXT,),
        posts=0,
        token_type=TOKEN_TYPE_JOB,
    ),
    FailureCase(
        slug="file-that-cannot-be-read",
        operation_id=OP_DESIGN_UPLOAD,
        arguments=(*DESIGN_ARGUMENTS, *assigned(option=OPTION_FILE, name=VARIABLE_FILES, value=MISSING_MARK)),
        answers=(Answer(body={FIELD_DATA: {FIELD_DESIGN_UPLOAD: {FIELD_ERRORS: []}}}),),
        message=(MISSING_FILE_NAME,),
        posts=0,
    ),
)


def failure_case_name(case: FailureCase) -> str:
    """The test id of a ``FAILURE_CASES`` row."""
    return case.slug


def answer_with_no_response(*, fake: Any) -> Callable[..., NoReturn]:
    """An ``HTTPSHandler.https_open`` for a host that never answers: the fake host records the request, then
    ``urllib.error.URLError`` is raised, as a refused or reset connection raises it inside urllib's handler."""

    def https_open(handler: urllib.request.BaseHandler, req: urllib.request.Request) -> NoReturn:
        fake.serve(request=req)
        raise urllib.error.URLError(reason=NO_RESPONSE_REASON)

    return https_open


@pytest.mark.parametrize(argnames="failure", argvalues=FAILURE_CASES, ids=failure_case_name)
def test_a_graphql_failure_exits_1_with_its_details(
    failure: FailureCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.4: top-level ``errors`` with and without ``data``, a mutation payload's ``errors``, HTTP ``502``, ``429``
    on every attempt, no response, a body ``[]``, a ``null`` project on a connection, a next page without
    ``endCursor``, a job token and a file that cannot be read each exit 1 with nothing on standard output; one log
    record holds the error's message and, where the error has details, another holds them; a job token and the file
    send no request."""
    attempts = gitlab_module(name=TRANSPORT).RATE_LIMIT_MAX_RETRIES + 1 if failure.rate_limited else 1
    queue_answers(fake=fake_gitlab, answers=failure.answers, times=attempts)
    if failure.no_response:
        monkeypatch.setattr(
            target=urllib.request.HTTPSHandler, name=HTTPS_OPEN, value=answer_with_no_response(fake=fake_gitlab)
        )
    argv = placed(
        arguments=(failure.operation_id, *failure.arguments), marks={MISSING_MARK: project / MISSING_FILE_NAME}
    )

    code = run_call(root=project, argv=argv, token_type=failure.token_type)

    out = capsys.readouterr().out
    messages = error_messages(caplog=caplog)
    assert code == EXIT_API_ERROR, (
        f"call {failure.operation_id} exits {code}, not {EXIT_API_ERROR}; logged: {messages!r}"
    )
    assert out == "", f"an API error prints nothing on standard output:\n{out}"
    posts = attempts if failure.rate_limited else failure.posts
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)] * posts, (
        f"{posts} POST to {GRAPHQL_URL}, one per attempt or page: {sent(fake=fake_gitlab)}"
    )
    assert any(all(text in message for text in failure.message) for message in messages), (
        f"one log record holds the error's message, {list(failure.message)} (AC-2.4); logged: {messages!r}"
    )
    if failure.details:
        details = json_text(value=failure.answers[-1].body)
        assert details in messages, (
            f"one log record holds the error's details, {details} (AC-2.4); logged: {messages!r}"
        )


# --- AC-3.1, AC-3.2: a design upload sends each file as a part -----------------------------------------------------

DESIGN_DATA: Dict[str, Any] = {
    FIELD_DESIGN_UPLOAD: {
        FIELD_DESIGNS: [{FIELD_ID: "gid://gitlab/DesignManagement::Design/1", FIELD_FILENAME: "first-design.png"}],
        FIELD_SKIPPED_DESIGNS: [],
        FIELD_ERRORS: [],
    }
}
#: The designs uploaded, each a name and its bytes: distinct, and each holding bytes that are not UTF-8 and a CRLF.
FIRST_DESIGN: Tuple[str, bytes] = ("first-design.png", b"\x89PNG\r\n\x1a\n\x00\xff first design\r\n")
SECOND_DESIGN: Tuple[str, bytes] = ("second-design.png", b"\x89PNG\r\n\x1a\n\x00\xfe second design\r\nend")


class UploadCase(NamedTuple):
    """``call graphql#designManagementUpload`` with one ``--file files=…`` per design of ``designs``, in order."""

    slug: str
    designs: Tuple[Tuple[str, bytes], ...]


UPLOAD_CASES: Tuple[UploadCase, ...] = (
    UploadCase(slug="one-file", designs=(FIRST_DESIGN,)),
    UploadCase(slug="two-files", designs=(FIRST_DESIGN, SECOND_DESIGN)),
)


def upload_case_name(case: UploadCase) -> str:
    """The test id of an ``UPLOAD_CASES`` row."""
    return case.slug


@pytest.mark.parametrize(argnames="case", argvalues=UPLOAD_CASES, ids=upload_case_name)
def test_a_design_upload_sends_each_file_as_a_part(
    case: UploadCase,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-3.1, AC-3.2: ``call graphql#designManagementUpload -f projectPath=g/p -f iid=5 --file files=…`` sends one
    ``POST`` to ``/api/graphql`` with ``Authorization: Bearer``, ``multipart/form-data`` with a boundary, whose parts
    are ``operations``, ``map`` and ``0``, … in that order: ``operations`` the document and the variables with each
    file ``null``, ``map`` each part name mapped to ``variables.files.<i>``, each file part the file's name and its
    bytes unchanged; it prints ``data``."""
    document = declared_document(operation_id=OP_DESIGN_UPLOAD)
    arguments: List[str] = list(DESIGN_ARGUMENTS)
    files: List[GivenFile] = []
    for index, (file_name, content) in enumerate(case.designs):
        path = project / file_name
        path.write_bytes(data=content)
        arguments.extend(assigned(option=OPTION_FILE, name=VARIABLE_FILES, value=path))
        files.append(
            GivenFile(operations_path=operations_path(name=VARIABLE_FILES, index=index), path=path, content=content)
        )
    queue_answers(fake=fake_gitlab, answers=(Answer(body={FIELD_DATA: DESIGN_DATA}),))

    code = run_call(root=project, argv=(OP_DESIGN_UPLOAD, *arguments))

    out = capsys.readouterr().out
    assert code == EXIT_OK, (
        f"call {OP_DESIGN_UPLOAD} exits {code}, not {EXIT_OK}; logged: {error_messages(caplog=caplog)!r}"
    )
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)], (
        f"the files and the operation travel in one POST to {GRAPHQL_URL} (AC-3.1): {sent(fake=fake_gitlab)}"
    )
    request = fake_gitlab.requests[0]
    assert request.header(name=HEADER_AUTHORIZATION) == BEARER_PREFIX + TOKEN, "GraphQL sends Authorization: Bearer"
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == CONTENT_TYPE_MULTIPART, f"the body is multipart, not {content_type!r}"
    parts = multipart_parts(body=request.body or b"", content_type=str(content_type))
    expected = multipart_post(
        document=document,
        variables={
            VARIABLE_PROJECT_PATH: FULL_PATH,
            VARIABLE_IID: DESIGN_ISSUE_IID,
            VARIABLE_FILES: [None] * len(files),
        },
        files=files,
    )[1]
    assert [part.name for part in parts] == [part.name for part in expected], (
        "the parts are operations, map, then one per file named after its map key, in that order (AC-3.1)"
    )
    assert parts[0] == expected[0], f"operations is the document and the variables, each file null: {parts[0]!r}"
    assert parts[1] == expected[1], f"map names variables.files.<i> for each item of files (AC-3.2): {parts[1]!r}"
    assert parts[2:] == expected[2:], "each file part holds the file's name and its bytes unchanged (AC-3.1)"
    assert out == printed_json(value=DESIGN_DATA), f"the call prints data as print_json writes it (AC-3.1):\n{out}"


# --- AC-3.1, design D4: a --file replaces a -f or -F value of the same name ----------------------------------------


class ReplacedField(NamedTuple):
    """``files`` given as ``text`` with ``option`` besides its ``--file``, before it or after it on the command line."""

    slug: str
    option: str
    text: str
    before_file: bool


REPLACED_FIELDS: Tuple[ReplacedField, ...] = (
    ReplacedField(
        slug="json-field-before-the-file",
        option=OPTION_FIELD,
        text=json.dumps(obj=["given-with-field.png"]),
        before_file=True,
    ),
    ReplacedField(
        slug="raw-field-after-the-file", option=OPTION_RAW_FIELD, text="given-as-text.png", before_file=False
    ),
)


def replaced_field_name(case: ReplacedField) -> str:
    """The test id of a ``REPLACED_FIELDS`` row."""
    return case.slug


@pytest.mark.parametrize(argnames="case", argvalues=REPLACED_FIELDS, ids=replaced_field_name)
def test_a_file_replaces_a_field_of_the_same_name(
    case: ReplacedField,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-3.1, design.md D4: ``call graphql#designManagementUpload -f projectPath=g/p -f iid=5`` given ``files`` both
    with ``-F``/``-f`` and with ``--file files=<a file>``, in either order: the ``--file`` replaces the other value, so
    one ``POST`` sends AC-3.1's ``multipart/form-data`` body — ``operations`` with ``files`` ``[null]``, ``map``, and
    the file as part ``0`` — and not a JSON body holding the ``-F``/``-f`` value; it prints ``data``."""
    document = declared_document(operation_id=OP_DESIGN_UPLOAD)
    file_name, content = FIRST_DESIGN
    path = project / file_name
    path.write_bytes(data=content)
    field = assigned(option=case.option, name=VARIABLE_FILES, value=case.text)
    upload = assigned(option=OPTION_FILE, name=VARIABLE_FILES, value=path)
    ordered = (*field, *upload) if case.before_file else (*upload, *field)
    queue_answers(fake=fake_gitlab, answers=(Answer(body={FIELD_DATA: DESIGN_DATA}),))

    code = run_call(root=project, argv=(OP_DESIGN_UPLOAD, *DESIGN_ARGUMENTS, *ordered))

    out = capsys.readouterr().out
    assert code == EXIT_OK, (
        f"call {OP_DESIGN_UPLOAD} exits {code}, not {EXIT_OK}; logged: {error_messages(caplog=caplog)!r}"
    )
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)], (
        f"the file and the operation travel in one POST to {GRAPHQL_URL} (AC-3.1): {sent(fake=fake_gitlab)}"
    )
    media, body = posted(request=fake_gitlab.requests[0])
    expected_media, expected_parts = multipart_post(
        document=document,
        variables={VARIABLE_PROJECT_PATH: FULL_PATH, VARIABLE_IID: DESIGN_ISSUE_IID, VARIABLE_FILES: [None]},
        files=(GivenFile(operations_path=operations_path(name=VARIABLE_FILES, index=0), path=path, content=content),),
    )
    assert media == expected_media, (
        f"the --file replaces the {case.option} value of {VARIABLE_FILES}, so the body is {expected_media}, "
        f"not {media} (design.md D4): {body!r}"
    )
    assert body == expected_parts, (
        f"operations holds files [null], map names variables.files.0, and part 0 is the file (AC-3.1): {body!r}"
    )
    assert out == printed_json(value=DESIGN_DATA), f"the call prints data as print_json writes it (AC-3.1):\n{out}"


# --- AC-4.1 to AC-4.3: a refused mutation sends nothing ------------------------------------------------------------

#: The mark ``test_a_refused_mutation_sends_nothing`` replaces with the path of the CSV file it writes.
IMPORT_MARK = "<import-file>"
IMPORT_FILE_NAME = "work-items.csv"
IMPORT_BYTES = b"title,description\r\nImported,From a CSV file\r\n"
#: D7's argv of each refused record (design.md § Correctness Properties AC-4.1).
REFUSED_ARGUMENTS: Mapping[str, Tuple[str, ...]] = {
    OP_WORK_ITEM_CREATE: assigned(option=OPTION_FIELD, name=VARIABLE_INPUT, value="{}"),
    OP_WORK_ITEMS_CSV_IMPORT: (
        *assigned(option=OPTION_RAW_FIELD, name=VARIABLE_PROJECT_PATH, value=FULL_PATH),
        *assigned(option=OPTION_FILE, name=VARIABLE_FILE, value=IMPORT_MARK),
    ),
}


@pytest.mark.parametrize(argnames="operation_id", argvalues=REFUSED_IDS)
def test_a_refused_mutation_sends_nothing(
    operation_id: str,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-4.1 to AC-4.3: each ID of ``REFUSED_IDS`` names a record of ``graphql_only.OPERATIONS``; its call exits 2
    with no request although one would be answered, and a log record names the ID and the mutation and states that no
    subcommand sends it, never that a subcommand does."""
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    declared = [record for record in graphql_only.OPERATIONS if record.operation_id == operation_id]
    assert declared, (
        f"{operation_id} of REFUSED_IDS names no record of graphql_only.OPERATIONS, so its refusal proves nothing "
        f"(AC-4.3): {[record.operation_id for record in graphql_only.OPERATIONS]}"
    )
    import_file = project / IMPORT_FILE_NAME
    import_file.write_bytes(data=IMPORT_BYTES)
    argv = placed(arguments=(operation_id, *REFUSED_ARGUMENTS[operation_id]), marks={IMPORT_MARK: import_file})
    answer_anything(fake=fake_gitlab)

    code = run_call(root=project, argv=argv)

    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    mutation = operation_id[len(GRAPHQL_ID_PREFIX) :]
    naming = [
        message
        for message in messages
        if operation_id in message and names(text=message, name=mutation) and NO_SUBCOMMAND_SENDS_IT in message
    ]
    assert naming, (
        f"a log record names {operation_id}, the mutation {mutation} and that {NO_SUBCOMMAND_SENDS_IT!r} "
        f"(AC-4.1, AC-4.2); logged: {messages!r}"
    )
    assert not [message for message in messages if SENDS_IT in message], (
        f"no log record names a subcommand {SENDS_IT!r} for {operation_id} (AC-4.2); logged: {messages!r}"
    )


# --- UB-1.2: a file for a variable that is no Upload is refused ----------------------------------------------------

#: The mark ``test_a_file_for_a_variable_that_is_no_upload_is_refused`` replaces with the path of the file it writes.
NOT_AN_UPLOAD_MARK = "<not-an-upload>"
NOT_AN_UPLOAD_FILE_NAME = "project-path.txt"
NOT_AN_UPLOAD_ARGUMENTS: Tuple[str, ...] = (
    *assigned(option=OPTION_RAW_FIELD, name=VARIABLE_IID, value=DESIGN_ISSUE_IID),
    *assigned(option=OPTION_FILE, name=VARIABLE_PROJECT_PATH, value=NOT_AN_UPLOAD_MARK),
)
#: How the refusal names the name: rendered with ``json.dumps``, beside the option it was given with (#41 D4).
NOT_AN_UPLOAD_REFUSAL = f"{json.dumps(obj=VARIABLE_PROJECT_PATH)} given with {OPTION_FILE}"


def test_a_file_for_a_variable_that_is_no_upload_is_refused(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """UB-1.2: ``call graphql#designManagementUpload -f iid=5 --file projectPath=<file>`` gives a file to a variable
    whose type is not ``Upload``: exit 2 with no request, its log record naming ``"projectPath" given with --file``."""
    given_file = project / NOT_AN_UPLOAD_FILE_NAME
    given_file.write_bytes(data=FULL_PATH.encode(encoding=ASCII_ENCODING))
    argv = placed(arguments=(OP_DESIGN_UPLOAD, *NOT_AN_UPLOAD_ARGUMENTS), marks={NOT_AN_UPLOAD_MARK: given_file})
    answer_anything(fake=fake_gitlab)

    code = run_call(root=project, argv=argv)

    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    assert any(NOT_AN_UPLOAD_REFUSAL in message for message in messages), (
        f"a log record names {NOT_AN_UPLOAD_REFUSAL} (UB-1.2, design.md D3 step 4); logged: {messages!r}"
    )


# --- AC-5.1: the usage names every GraphQL record ------------------------------------------------------------------

#: A usage line of the entry script's docstring starts with this, after its indentation; the GraphQL entry's with the
#: second (design.md D8).
USAGE_LINE_PREFIX = "python scripts/gitlab_wrapper.py "
GRAPHQL_USAGE_PREFIX = f"{USAGE_LINE_PREFIX}{CALL} {GRAPHQL_ID_PREFIX}"
#: Each line under a usage line starts with it, after its indentation.
COMMENT_MARKER = "#"
#: What joins the lines of the entry, each stripped of its indentation and its ``#``: a phrase wrapped onto the next
#: line reads as one.
ENTRY_LINE_JOIN = " "
#: What ends a capability where the entry names it, before the IDs of its records (design.md D8).
CAPABILITY_END = ":"
#: The end of an operation ID named whole: no letter, digit or ``_`` follows it, nor ``.`` and a letter, so
#: ``graphql#Query.vulnerability`` is not named by ``graphql#Query.vulnerabilities``, nor an ID by a longer
#: ``<Type>.<field>`` ID it begins.
ID_EDGE_AFTER = r"(?![A-Za-z0-9_]|\.[A-Za-z])"
#: What the GraphQL entry names besides its records (AC-5.1, design.md D8): how a variable is given as text and as
#: JSON and a file with ``--file`` (AC-2.1, AC-3.1), how a connection and any other result print (AC-2.2, AC-2.3),
#: and the exit code of a refusal (AC-4.1).
USAGE_TERMS: Tuple[str, ...] = (
    "-f NAME=TEXT",
    "-F NAME=JSON",
    "--file NAME=PATH",
    "JSON array",
    FIELD_DATA,
    f"exit {EXIT_REFUSED}",
)


def graphql_usage_entry(*, doc: str) -> str:
    """The GraphQL entry of the usage ``doc`` (design.md D8): its one ``call graphql#`` usage line and the ``#`` lines
    under it, up to the first line that is no ``#`` line (the next usage line or the blank line after the list), each
    stripped of its indentation and its ``#``, joined with one space, so a phrase wrapped onto the next line reads as
    one."""
    lines = doc.splitlines()
    starts = [number for number, line in enumerate(lines) if line.strip().startswith(GRAPHQL_USAGE_PREFIX)]
    assert len(starts) == 1, (
        f"the docstring of {fixtures.WRAPPER_FILE.name} holds {len(starts)} usage lines starting "
        f"{GRAPHQL_USAGE_PREFIX!r}, expected one (AC-5.1, design.md D8)"
    )
    entry = [lines[starts[0]].strip()]
    for line in lines[starts[0] + 1 :]:
        text = line.strip()
        if not text.startswith(COMMENT_MARKER):
            break
        entry.append(text[len(COMMENT_MARKER) :].strip())
    return ENTRY_LINE_JOIN.join(entry)


def names_id(*, text: str, operation_id: str) -> bool:
    """Whether ``text`` names ``operation_id`` whole: not inside a longer name, and not followed by a letter, a digit,
    ``_``, or ``.`` and a letter."""
    whole = f"{NAME_EDGE_BEFORE}{re.escape(pattern=operation_id)}{ID_EDGE_AFTER}"
    return re.search(pattern=whole, string=text) is not None


def capability_problems(*, entry: str, ids_by_capability: Mapping[str, Sequence[str]]) -> List[str]:
    """Each capability the GraphQL ``entry`` does not name as ``<capability>:``, and each ID of a capability's records
    the entry does not name whole after it and before the next capability it names."""
    labels = {
        capability: re.compile(
            pattern=f"{NAME_EDGE_BEFORE}{re.escape(pattern=capability)}{re.escape(pattern=CAPABILITY_END)}"
        )
        for capability in ids_by_capability
    }
    starts = sorted(match.start() for label in labels.values() for match in label.finditer(string=entry))
    problems: List[str] = []
    for capability, operation_ids in ids_by_capability.items():
        found = labels[capability].search(string=entry)
        if found is None:
            problems.append(f"{json.dumps(obj=capability)} is not named as {capability}{CAPABILITY_END}")
            continue
        following = [start for start in starts if start > found.start()]
        segment = entry[found.end() : following[0] if following else len(entry)]
        problems.extend(
            f"{json.dumps(obj=capability)}: {operation_id} is not named before the next capability"
            for operation_id in operation_ids
            if not names_id(text=segment, operation_id=operation_id)
        )
    return problems


def test_the_usage_names_every_graphql_record() -> None:
    """AC-5.1 (design.md D8): the GraphQL entry of the entry script's ``__doc__``, loaded with ``load_wrapper`` (its
    ``call graphql#`` usage line and the ``#`` lines under it, joined by ``graphql_usage_entry``), names every
    capability of ``graphql_only.OPERATIONS`` followed by the IDs of its records before the next capability, each ID
    whole; ``-f NAME=TEXT``, ``-F NAME=JSON``, ``--file NAME=PATH``, ``JSON array``, ``data`` and ``exit 2``; and each
    ID of ``REFUSED_IDS``. Only the entry is read, so what the docstring says of a REST ``call`` satisfies none of it;
    the test fails when ``OPERATIONS`` holds no record."""
    graphql_only = gitlab_module(name=GRAPHQL_ONLY)
    ids_by_capability: Dict[str, List[str]] = {}
    for record in graphql_only.OPERATIONS:
        ids_by_capability.setdefault(str(record.capability), []).append(str(record.operation_id))
    assert ids_by_capability, "graphql_only.OPERATIONS holds no record for the usage to name (AC-5.1)"
    doc = fixtures.load_wrapper(module_name=WRAPPER_MODULE).__doc__
    assert doc, f"{fixtures.WRAPPER_FILE} has no module docstring"

    entry = graphql_usage_entry(doc=doc)

    problems = capability_problems(entry=entry, ids_by_capability=ids_by_capability)
    problems.extend(f"{term!r} is not in the entry" for term in USAGE_TERMS if not names(text=entry, name=term))
    problems.extend(
        f"the refused {operation_id} is not named"
        for operation_id in REFUSED_IDS
        if not names_id(text=entry, operation_id=operation_id)
    )
    assert not problems, (
        f"the GraphQL usage entry of {fixtures.WRAPPER_FILE.name}:\n"
        + "\n".join(problems)
        + f"\nThe entry reads: {entry}"
    )


#: What joins the IDs of ``REFUSED_IDS`` in design D8's refusal sentence.
REFUSED_IDS_JOIN = " and "
#: Design D8's refusal sentence of the GraphQL entry, verbatim: it names each ID of ``REFUSED_IDS`` and says that it is
#: refused before any request, with exit 2 (AC-4.1). The capability lines name the same IDs, so only this sentence
#: tells the reader they are refused.
REFUSAL_SENTENCE = f"{REFUSED_IDS_JOIN.join(REFUSED_IDS)} are refused before any request: exit {EXIT_REFUSED}."


def test_the_usage_says_which_mutations_are_refused() -> None:
    """AC-5.1, AC-4.1 (design.md D8): the GraphQL entry of the entry script's ``__doc__``, read by
    ``graphql_usage_entry``, holds ``REFUSAL_SENTENCE``, D8's sentence naming each ID of ``REFUSED_IDS`` as refused
    before any request with exit 2; a sentence that says some other operation is refused does not satisfy it."""
    doc = fixtures.load_wrapper(module_name=WRAPPER_MODULE).__doc__
    assert doc, f"{fixtures.WRAPPER_FILE} has no module docstring"

    entry = graphql_usage_entry(doc=doc)

    assert REFUSAL_SENTENCE in entry, (
        f"the GraphQL usage entry of {fixtures.WRAPPER_FILE.name} does not hold design D8's refusal sentence "
        f"{REFUSAL_SENTENCE!r} (AC-5.1); the entry reads: {entry}"
    )
