"""Tests for ``gitlab_api/commands/call.py``: the ``call`` subcommand, which sends any declared record by its operation
ID (issue #41, ``design.md`` D1 to D4).

What is pinned, each case through the product's ``main(argv=["call", ...])`` against the fake GitLab host:

- the request a call sends (AC-1.2, AC-1.3, AC-1.8): the record's method; its path with every ``:name`` one encoded
  segment and ``id`` defaulting to the configured ``project_id`` on a ``/projects/:id`` path; the ``--query`` values in
  the order given, then the record's ``fixed`` pairs, as the query; the attributes as a JSON, form or multipart body,
  each in the shape its ``Kind`` declares; and the configured token type's one credential header;
- what prints (AC-1.4 to AC-1.6, AC-1.9): every page of a list as one JSON array, a JSON response as ``print_json``
  writes it, an empty body as nothing, any other body as its bytes unchanged, a GraphQL record's ``data`` or the nodes
  of every page of its connection;
- a ``GitLabAPIError`` exits 1, its message and then its details logged (AC-1.7);
- the refusals, exit 2 with no request (AC-1.1, AC-2.1 to AC-2.4): a gated ID names the subcommand to use; an unknown
  ID, an undocumented parameter, a missing path parameter and a value of the wrong shape are named in a log record;
  a ``NAME=VALUE`` with no ``=`` or an empty name, and ``-F`` text that is not JSON, are argparse's usage error, which
  names no value (design.md D2, D4); ``call`` has no token option (UB-2.1).

A refusal is judged by its ``logging`` record (``caplog``) and argparse's by standard error (``capsys``), each with no
request recorded; output that is not JSON is read as bytes (``capsysbinary``). A synthetic record (design.md "Testing
Strategy") is set into a family module's ``OPERATIONS`` or ``graphql_only.OPERATIONS`` for its test only.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; no test
imports ``gitlab_api.commands.call``, and a package module a test reads is imported inside the test. The fake GitLab
host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_call.py`` (no network).
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import logging
import re
import sys
import urllib.parse
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_call_under_test"
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
FAMILIES = "families"
OPERATIONS = "OPERATIONS"
PLAN = "plan"

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_TOKEN_TYPE = "token_type"
TOKEN = "glpat-gitlab-api-call-test"  # pragma: allowlist secret
TOKEN_TYPE_BEARER = "bearer"  # a token_type value, not a secret
TOKEN_TEXT = "token"  # the text no option string of `call` holds (UB-2.1)
PROJECT_ID = 4242

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_USAGE = 2  # argparse's usage error and a refused `call` (design.md D4)
USAGE_PREFIX = "usage:"

TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"
DECODE_ERRORS = "replace"
REST_BASE = fixtures.REST_BASE
GRAPHQL_URL = fixtures.GRAPHQL_URL

HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "Content-Disposition"
HEADER_LOCATION = "Location"
HEADER_LINK = "Link"
HEADER_NEXT_PAGE = "x-next-page"
HEADER_RETRY_AFTER = "Retry-After"
# The three credential headers (#13 design.md D4 "Credentials"); a request carries exactly one of them.
HEADER_PRIVATE_TOKEN = "PRIVATE-TOKEN"
HEADER_AUTHORIZATION = "Authorization"
HEADER_JOB_TOKEN = "JOB-TOKEN"
BEARER_PREFIX = "Bearer "

CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_JSON_UTF8 = "application/json; charset=utf-8"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
CONTENT_TYPE_ZIP = "application/zip"
JSON_HEADERS = ((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON),)
PARAM_BOUNDARY = "boundary"
PARAM_NAME = "name"
PARAM_FILENAME = "filename"
CRLF = b"\r\n"
DASHES = b"--"
QUERY_SEPARATOR = "?"
HEADER_SEPARATOR = ":"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

METHOD_GET = "GET"
METHOD_POST = "POST"
METHOD_PUT = "PUT"
METHOD_DELETE = "DELETE"
STATUS_OK = 200
STATUS_NO_CONTENT = 204
STATUS_FOUND = 302
STATUS_NOT_FOUND = 404
STATUS_TOO_MANY_REQUESTS = 429

# The options of `call` (design.md D2), and how D4's one message names the option a refused name was given with.
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "-f"
OPTION_FIELD = "-F"
OPTION_FILE = "--file"
OPTION_FIELDS = "-f/-F"
FIELD_OPTION_NAME = "-F/--field"  # argparse's name of the `-F` option in its usage error
RAW_FIELD_OPTION_NAME = "-f/--raw-field"  # and of the `-f` option
# The `:id` path parameter, which defaults to the configured project on a `/projects/:id` path (AC-1.8).
PATH_ID = "id"
# A word inside a message: not part of a longer name (`id` is not found in `issue_iid`).
NAME_EDGE_BEFORE = r"(?<![A-Za-z0-9_])"
NAME_EDGE_AFTER = r"(?![A-Za-z0-9_])"

# The part-1 records the cases call (families/plan.py, create.py, verify.py, ai_coding.py; commands/mr.py and issue.py).
OP_RETRIEVE_ISSUE = "plan#retrieve-a-project-issue"
OP_UPDATE_ISSUE = "plan#update-an-issue"
OP_LIST_ISSUES = "plan#list-all-project-issues"
OP_LIST_LABELS = "plan#list-all-project-labels"
OP_CREATE_ISSUE = "plan#create-an-issue"
OP_MERGE_MR = "ai-coding#merge-a-merge-request"
OP_DELETE_BRANCH = "create#delete-repository-branch"
OP_JOB_TRACE = "verify#retrieve-a-log-file-for-a-job"
# The verify record of issue #37 (families/verify.py; rest/verify.md "Download job artifacts by job ID").
OP_DOWNLOAD_ARTIFACTS = "verify#download-job-artifacts-by-job-id"
# `plan#clone-an-issue`, the Reference of the index row `POST /projects/:id/issues/:issue_iid/clone`, a key only on
# plan's PENDING (issue #39 keeps it pending); and an ID the reference does not hold (AC-2.1).
OP_PENDING_ONLY = "plan#clone-an-issue"
OP_UNDECLARED = "plan#no-such-operation"
# The synthetic records (design.md "Testing Strategy"), each set into a module's OPERATIONS for one test.
OP_FORM_RECORD = "plan#synthetic-create-a-form-record"
OP_FIXED_RECORD = "plan#synthetic-list-with-fixed-pairs"
OP_ATTRIBUTE_RECORD = "plan#synthetic-set-an-attribute"
OP_UPLOAD_RECORD = "plan#synthetic-upload-a-file"
OP_PROJECT_RECORD = "plan#synthetic-retrieve-a-project"
OP_GROUP_LABELS_RECORD = "plan#synthetic-list-group-labels"
OP_KEYSET_ISSUES = "plan#synthetic-keyset-issues"
OP_GRAPHQL_PROJECT = "graphql#syntheticProject"
OP_GRAPHQL_ISSUES = "graphql#syntheticProjectIssues"
SYNTHETIC_CAPABILITY = "Synthetic project lookup"

# Request and response keys: rest/plan.md "Issues API" and "Project labels API"; graphql/conventions.md "Connections
# and cursor pagination"; the GraphQL request body (#13 design.md D4).
FIELD_ID = "id"
FIELD_IID = "iid"
FIELD_NAME = "name"
FIELD_TITLE = "title"
FIELD_LABELS = "labels"
FIELD_ASSIGNEE_IDS = "assignee_ids"
FIELD_MESSAGE = "message"
FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_ERRORS = "errors"
FIELD_PROJECT = "project"
FIELD_ISSUES = "issues"
FIELD_MERGE_REQUESTS = "mergeRequests"
FIELD_COUNT = "count"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"
VARIABLE_FULL_PATH = "fullPath"
VARIABLE_FIRST = "first"

ISSUE_IID = 5
JOB_ID = 3001
BRANCH = "feature/x"
FULL_PATH = "g/p"
END_CURSOR = "eyJpZCI6IjEifQ"


def project_url(*, path: str) -> str:
    """``path`` under the configured project's ``/projects/:id``, as the transport sends it."""
    return f"{REST_BASE}/projects/{PROJECT_ID}{path}"


ISSUE_URL = project_url(path=f"/issues/{ISSUE_IID}")
# BRANCH as ONE path segment, `/` written %2F (conventions.md "URL-encoding path parameters").
BRANCH_URL = project_url(path="/repository/branches/feature%2Fx")
LABELS_URL = project_url(path="/labels")
ISSUES_URL = project_url(path="/issues")
# A keyset page's `Link` rel="next" URL, requested as given (#13 AC-2.6).
KEYSET_NEXT_URL = project_url(path="/issues?cursor=eyJpZCI6IjEwIn0%3D&pagination=keyset&per_page=20")
TRACE_URL = project_url(path=f"/jobs/{JOB_ID}/trace")
ARTIFACTS_URL = project_url(path=f"/jobs/{JOB_ID}/artifacts")
# The object-storage host an artifacts download redirects to (conventions.md "Downloads and redirects").
STORAGE_URL = "https://storage.example.com/a.zip"

# The file a `--file` names (written into the project by the `project` fixture) and its bytes, which are not UTF-8.
UPLOAD_NAME = "upload.bin"
UPLOAD_MARK = "<upload>"  # replaced in an argv by the file's absolute path
UPLOAD_BYTES = b"\x89PNG\r\n\x1a\n\x00\xff\xfe synthetic upload\r\n"
# Bodies printed unchanged (AC-1.6): a job trace with mixed line ends, bytes that are not UTF-8 and end without a line
# end, JSON text with no Content-Type (its spacing kept), and the archive the storage host serves.
TRACE_BYTES = b"Running with gitlab-runner 17.5.0\r\n$ python scripts/run_tests.py\nFAILED test/test_parser.py\n"
NOT_UTF8_BYTES = b"\x89PNG\r\n\x1a\n\x00\xff\xfe\xfd"
JSON_TEXT_BYTES = b'{"iid": 5,   "title":"spacing kept"}'
ZIP_BYTES = b"PK\x03\x04\x14\x00\x00\x00\x08\x00\xff\xfe synthetic artifacts"

# GraphQL documents (design.md "Correctness Properties" AC-1.9): one without a connection, defining `$fullPath` and
# `$first`; one paging the connection `project.issues` by `$after`.
PROJECT_DOCUMENT = (
    "query Q($fullPath: ID!, $first: Int) {\n"
    "  project(fullPath: $fullPath) { mergeRequests(first: $first) { count } }\n"
    "}\n"
)
ISSUES_DOCUMENT = (
    "query Issues($fullPath: ID!, $after: String) {\n"
    "  project(fullPath: $fullPath) { issues(after: $after) { nodes { iid } pageInfo { hasNextPage endCursor } } }\n"
    "}\n"
)
ISSUES_CONNECTION = (FIELD_PROJECT, FIELD_ISSUES)
PROJECT_DATA: Dict[str, Any] = {FIELD_PROJECT: {FIELD_MERGE_REQUESTS: {FIELD_COUNT: 3}}}
ISSUE_NODES: Tuple[Dict[str, Any], ...] = ({FIELD_IID: "1"}, {FIELD_IID: "2"})
GRAPHQL_ERROR = "Field 'nope' doesn't exist on type 'Project'"


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory, holding the file a ``--file`` names; the entry script reads
    ``config/gitlab.json`` under it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / UPLOAD_NAME).write_bytes(data=UPLOAD_BYTES)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` (``families.plan`` for a family module) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


class Synthetic(NamedTuple):
    """A record set into one module's ``OPERATIONS`` for one test: the family module's stem, or ``GRAPHQL_ONLY``, and
    the function that builds the record from the registry module (``build(registry=...)``)."""

    module: str
    build: Callable[..., Any]


def install(*, monkeypatch: pytest.MonkeyPatch, records: Sequence[Synthetic]) -> None:
    """Append each synthetic record to its module's ``OPERATIONS`` for this test only; ``registry.lookup`` reads the
    attribute on every call, so the wrapper's ``call`` finds the record."""
    registry = gitlab_module(name=REGISTRY)
    for synthetic in records:
        stem = GRAPHQL_ONLY if synthetic.module == GRAPHQL_ONLY else f"{FAMILIES}{MODULE_SEPARATOR}{synthetic.module}"
        module = gitlab_module(name=stem)
        record = synthetic.build(registry=registry)
        monkeypatch.setattr(target=module, name=OPERATIONS, value=(*module.OPERATIONS, record))


def run_call(*, root: Path, argv: Sequence[str], config_changes: Optional[Mapping[str, Any]] = None) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``, a file mark in ``argv`` replaced by the file's path."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    config.update(config_changes or {})
    fixtures.write_config(root=root, config=config)
    upload = str(root / UPLOAD_NAME)
    arguments = [CALL, *(argument.replace(UPLOAD_MARK, upload) for argument in argv)]
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=arguments)


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


def names(*, text: str, name: str, ignore_case: bool = False) -> bool:
    """Whether ``text`` holds ``name`` as a word of its own, not inside a longer name."""
    pattern = f"{NAME_EDGE_BEFORE}{re.escape(pattern=name)}{NAME_EDGE_AFTER}"
    return re.search(pattern=pattern, string=text, flags=re.IGNORECASE if ignore_case else 0) is not None


def refused_messages(
    *, code: Any, fake: Any, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> List[str]:
    """Assert a refusal before any request (design.md D4): exit 2, nothing sent, nothing printed, an ERROR record
    logged; return the messages of the ERROR records."""
    captured = capsys.readouterr()
    assert code == EXIT_USAGE, f"a refused call exits {EXIT_USAGE}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake) == [], "a refused call sends no request (design.md D4)"
    assert captured.out == "", f"a refusal prints nothing on standard output:\n{captured.out}"
    messages = error_messages(caplog=caplog)
    assert messages, (
        "call_operation logs its refusal with logger.error before returning 2 (design.md D4); no ERROR record was "
        f"logged. stderr:\n{captured.err}"
    )
    return messages


def media_type(*, value: Optional[str]) -> Optional[str]:
    """The media type of a ``Content-Type`` value, lower-cased and without its parameters; ``None`` without one."""
    if value is None:
        return None
    message = Message()
    message[HEADER_CONTENT_TYPE] = value
    return message.get_content_type()


def part_disposition(*, head: bytes) -> Message:
    """The ``Content-Disposition`` header of one multipart part's header block, parsed."""
    message = Message()
    for line in head.split(sep=CRLF):
        name, _, value = line.decode(encoding=TEXT_ENCODING).partition(HEADER_SEPARATOR)
        if name.strip().lower() == HEADER_CONTENT_DISPOSITION.lower():
            message[HEADER_CONTENT_DISPOSITION] = value.strip()
    return message


def multipart_parts(
    *, body: bytes, content_type: str
) -> Tuple[Tuple[Tuple[str, str], ...], Tuple[Tuple[str, bytes], ...]]:
    """The form fields and the files of a ``multipart/form-data`` body (RFC 7578, RFC 2046 section 5.1.1), each in
    body order: a part whose ``Content-Disposition`` has a ``filename`` is a file, its bytes unchanged; any other part
    is a field, its content as text."""
    header = Message()
    header[HEADER_CONTENT_TYPE] = content_type
    boundary = header.get_param(param=PARAM_BOUNDARY)
    assert isinstance(boundary, str) and boundary, f"a multipart Content-Type names its boundary: {content_type!r}"
    delimiter = CRLF + DASHES + boundary.encode(encoding=ASCII_ENCODING)
    fields: List[Tuple[str, str]] = []
    files: List[Tuple[str, bytes]] = []
    # Every delimiter but the first follows a CRLF, which belongs to it; the close delimiter ends in `--`.
    for section in (CRLF + body).split(sep=delimiter)[1:]:
        if section.startswith(DASHES):
            break
        head, _, content = section[len(CRLF) :].partition(CRLF + CRLF)
        disposition = part_disposition(head=head)
        name = str(disposition.get_param(param=PARAM_NAME, header=HEADER_CONTENT_DISPOSITION))
        if disposition.get_param(param=PARAM_FILENAME, header=HEADER_CONTENT_DISPOSITION) is None:
            fields.append((name, content.decode(encoding=TEXT_ENCODING)))
        else:
            files.append((name, content))
    return tuple(fields), tuple(files)


def decoded_body(*, request: Any) -> Any:
    """A recorded request's body by its ``Content-Type``: a JSON value; the pairs of a form body; the fields and files
    of a multipart body; else the raw bytes. ``None`` when the request carried no body."""
    if request.body is None:
        return None
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    media = media_type(value=content_type)
    if media == CONTENT_TYPE_JSON:
        return json.loads(s=request.body.decode(encoding=TEXT_ENCODING))
    if media == CONTENT_TYPE_FORM:
        return tuple(urllib.parse.parse_qsl(qs=request.body.decode(encoding=ASCII_ENCODING), keep_blank_values=True))
    if media == CONTENT_TYPE_MULTIPART:
        return multipart_parts(body=request.body, content_type=str(content_type))
    return request.body


def credentials(*, request: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """The values of the three credential headers a request may carry: PRIVATE-TOKEN, Authorization, JOB-TOKEN."""
    return (
        request.header(name=HEADER_PRIVATE_TOKEN),
        request.header(name=HEADER_AUTHORIZATION),
        request.header(name=HEADER_JOB_TOKEN),
    )


def json_text(*, value: Any) -> str:
    """``value`` as the fake host sends a JSON answer, and so as the transport keeps it in ``details``."""
    return json.dumps(obj=value)


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


class Answer(NamedTuple):
    """One response the fake host serves for an exact method and URL: the request it answers must be sent so."""

    method: str
    url: str
    status: int = STATUS_OK
    headers: Tuple[Tuple[str, str], ...] = ()
    body: bytes = b""


def json_answer(
    *, method: str, url: str, value: Any, status: int = STATUS_OK, headers: Tuple[Tuple[str, str], ...] = ()
) -> Answer:
    """An ``Answer`` whose body is ``value`` as JSON, under ``Content-Type: application/json``."""
    return Answer(
        method=method,
        url=url,
        status=status,
        headers=(*JSON_HEADERS, *headers),
        body=json_text(value=value).encode(encoding=TEXT_ENCODING),
    )


def script_answers(*, fake: Any, answers: Sequence[Answer], times: int = 1) -> None:
    """Script each answer ``times`` times for its exact method and URL."""
    for answer in answers:
        for _ in range(times):
            fake.script(
                method=answer.method, url=answer.url, status=answer.status, headers=answer.headers, body=answer.body
            )


def answer_anything(*, fake: Any) -> None:
    """Answer the next request, whatever it is, with ``{}``: a refusal that sends one is then judged by its oracle,
    not by the fake host's unscripted-request error."""
    fake.script_next(headers=JSON_HEADERS, body=json_text(value={}).encode(encoding=TEXT_ENCODING))


def documented_parameters(*, registry: ModuleType, record: Any) -> Tuple[str, ...]:
    """A record's documented parameters (requirements Glossary): its path parameters and its ``Param`` names, or the
    variables a GraphQL record's document defines (``registry.variables``)."""
    if isinstance(record, registry.GraphQLOperation):
        return tuple(registry.variables(operation=record))
    return (*registry.placeholders(path=record.path), *(param.name for param in record.params))


# --- The synthetic records ----------------------------------------------------------------------------------------


def form_record(*, registry: ModuleType) -> Any:
    """A FORM-body record: its BODY attributes go as ``application/x-www-form-urlencoded`` pairs."""
    return registry.RestOperation(
        operation_id=OP_FORM_RECORD,
        method=METHOD_POST,
        path="/projects/:id/synthetic_forms",
        params=(
            registry.Param(name=FIELD_TITLE, location=registry.Location.BODY),
            registry.Param(name=FIELD_LABELS, location=registry.Location.BODY, kind=registry.Kind.ARRAY),
        ),
        body=registry.BodyFormat.FORM,
    )


def fixed_record(*, registry: ModuleType) -> Any:
    """A record with a ``fixed`` query pair, which is sent after the attributes."""
    return registry.RestOperation(
        operation_id=OP_FIXED_RECORD,
        method=METHOD_GET,
        path="/projects/:id/synthetic_fixed",
        params=(registry.Param(name="search", location=registry.Location.QUERY),),
        fixed=(("scope", "all"),),
    )


def upload_record(*, registry: ModuleType) -> Any:
    """A JSON-body record with a FILE attribute beside two body attributes: a given file makes the body multipart."""
    return registry.RestOperation(
        operation_id=OP_UPLOAD_RECORD,
        method=METHOD_POST,
        path="/projects/:id/synthetic_uploads",
        params=(
            registry.Param(name="file", location=registry.Location.BODY, kind=registry.Kind.FILE),
            registry.Param(name=FIELD_TITLE, location=registry.Location.BODY),
            registry.Param(name=FIELD_LABELS, location=registry.Location.BODY, kind=registry.Kind.ARRAY),
        ),
    )


def project_record(*, registry: ModuleType) -> Any:
    """``GET /projects/:id``: the path is ``/projects/:id`` itself, so ``id`` defaults to the configured project."""
    return registry.RestOperation(operation_id=OP_PROJECT_RECORD, method=METHOD_GET, path="/projects/:id")


def group_labels_record(*, registry: ModuleType) -> Any:
    """``GET /groups/:id/labels``: an ``:id`` that is not a project's, so it has no default."""
    return registry.RestOperation(operation_id=OP_GROUP_LABELS_RECORD, method=METHOD_GET, path="/groups/:id/labels")


def keyset_issues_record(*, registry: ModuleType) -> Any:
    """A KEYSET copy of ``plan#list-all-project-issues``: paged by ``Link`` rel="next" only."""
    listed = registry.lookup(operation_id=OP_LIST_ISSUES)
    return registry.RestOperation(
        operation_id=OP_KEYSET_ISSUES,
        method=listed.method,
        path=listed.path,
        params=listed.params,
        body=listed.body,
        paging=registry.Paging.KEYSET,
        fixed=listed.fixed,
    )


def project_query_record(*, registry: ModuleType) -> Any:
    """A GraphQL record without a connection: ``Transport.graphql``, its ``data`` printed."""
    return registry.GraphQLOperation(
        operation_id=OP_GRAPHQL_PROJECT, capability=SYNTHETIC_CAPABILITY, document=PROJECT_DOCUMENT
    )


def issues_connection_record(*, registry: ModuleType) -> Any:
    """A GraphQL record with a connection: ``Transport.graphql_nodes``, the nodes of every page printed."""
    return registry.GraphQLOperation(
        operation_id=OP_GRAPHQL_ISSUES,
        capability=SYNTHETIC_CAPABILITY,
        document=ISSUES_DOCUMENT,
        connection=ISSUES_CONNECTION,
    )


FORM_RECORD = Synthetic(module=PLAN, build=form_record)
FIXED_RECORD = Synthetic(module=PLAN, build=fixed_record)
UPLOAD_RECORD = Synthetic(module=PLAN, build=upload_record)
PROJECT_RECORD = Synthetic(module=PLAN, build=project_record)
GROUP_LABELS_RECORD = Synthetic(module=PLAN, build=group_labels_record)
KEYSET_ISSUES_RECORD = Synthetic(module=PLAN, build=keyset_issues_record)
GRAPHQL_PROJECT_RECORD = Synthetic(module=GRAPHQL_ONLY, build=project_query_record)
GRAPHQL_ISSUES_RECORD = Synthetic(module=GRAPHQL_ONLY, build=issues_connection_record)


# --- AC-1.1: the gated operations ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    argnames=("argv", "subcommand"),
    argvalues=[
        pytest.param((OP_MERGE_MR, OPTION_PATH, "merge_request_iid=1"), "mr merge", id="merge-a-merge-request"),
        pytest.param((OP_CREATE_ISSUE, OPTION_RAW_FIELD, "title=T"), "issue create", id="create-an-issue"),
    ],
)
def test_a_gated_operation_names_its_subcommand(
    argv: Tuple[str, ...],
    subcommand: str,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=argv)
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    assert argv[0] in messages[0] and subcommand in messages[0], (
        f"the first log record names the gated ID {argv[0]!r} and the subcommand to use, {subcommand!r} "
        f"(design.md D1, D4); logged: {messages!r}"
    )


# --- AC-1.2: the request a call sends -----------------------------------------------------------------------------


class SendCase(NamedTuple):
    """One call and the one request it sends: method, URL as sent, the body's media type and decoded body (``None``:
    no body and no ``Content-Type``), and the three credential headers."""

    argv: Tuple[str, ...]
    method: str
    url: str
    media: Optional[str] = None
    body: Any = None
    synthetic: Tuple[Synthetic, ...] = ()
    config: Tuple[Tuple[str, Any], ...] = ()
    credential: Tuple[Optional[str], Optional[str], Optional[str]] = (TOKEN, None, None)
    answer_status: int = STATUS_OK
    answer_text: str = "{}"


def send_cases() -> List[Any]:
    """AC-1.2's table (design.md "Correctness Properties")."""
    issue_path = (OPTION_PATH, f"issue_iid={ISSUE_IID}")
    return [
        pytest.param(SendCase(argv=(OP_RETRIEVE_ISSUE, *issue_path), method=METHOD_GET, url=ISSUE_URL), id="get"),
        pytest.param(
            SendCase(
                argv=(OP_DELETE_BRANCH, OPTION_PATH, f"branch={BRANCH}"),
                method=METHOD_DELETE,
                url=BRANCH_URL,
                answer_status=STATUS_NO_CONTENT,
                answer_text="",
            ),
            id="delete-one-encoded-segment",
        ),
        pytest.param(
            SendCase(
                argv=(OP_UPDATE_ISSUE, *issue_path, OPTION_RAW_FIELD, "title=T", OPTION_FIELD, "assignee_ids=[1, 2]"),
                method=METHOD_PUT,
                url=ISSUE_URL,
                media=CONTENT_TYPE_JSON,
                body={FIELD_TITLE: "T", FIELD_ASSIGNEE_IDS: [1, 2]},
            ),
            id="put-json-body",
        ),
        pytest.param(
            SendCase(
                argv=(
                    OP_LIST_ISSUES,
                    OPTION_QUERY,
                    "state=opened",
                    OPTION_QUERY,
                    "assignee_username=a",
                    OPTION_QUERY,
                    "assignee_username=b",
                    OPTION_QUERY,
                    "iids[]=3",
                ),
                method=METHOD_GET,
                # The query in the order given, then the `per_page` Transport.pages adds (MAX_PER_PAGE).
                url=project_url(path="/issues?state=opened&assignee_username[]=a&assignee_username[]=b&iids[]=3")
                + "&per_page=100",
                answer_text="[]",
            ),
            id="query-in-the-order-given",
        ),
        pytest.param(
            SendCase(
                argv=(OP_FORM_RECORD, OPTION_RAW_FIELD, "title=T", OPTION_FIELD, 'labels=["a", "b"]'),
                method=METHOD_POST,
                url=project_url(path="/synthetic_forms"),
                media=CONTENT_TYPE_FORM,
                body=((FIELD_TITLE, "T"), ("labels[]", "a"), ("labels[]", "b")),
                synthetic=(FORM_RECORD,),
            ),
            id="form-body",
        ),
        pytest.param(
            SendCase(
                argv=(OP_FIXED_RECORD, OPTION_QUERY, "search=x"),
                method=METHOD_GET,
                url=project_url(path="/synthetic_fixed?search=x&scope=all"),
                synthetic=(FIXED_RECORD,),
            ),
            id="fixed-pairs-after-the-attributes",
        ),
        pytest.param(
            SendCase(
                argv=(OP_RETRIEVE_ISSUE, *issue_path),
                method=METHOD_GET,
                url=ISSUE_URL,
                config=((FIELD_TOKEN_TYPE, TOKEN_TYPE_BEARER),),
                credential=(None, BEARER_PREFIX + TOKEN, None),
            ),
            id="bearer-token",
        ),
    ]


@pytest.mark.parametrize(argnames="case", argvalues=send_cases())
def test_an_operation_call_sends_its_record(
    case: SendCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    fake_gitlab.script_next(
        status=case.answer_status, headers=JSON_HEADERS, body=case.answer_text.encode(encoding=TEXT_ENCODING)
    )
    code = run_call(root=project, argv=case.argv, config_changes=dict(case.config))
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], (
        "one request: the record's method, its path with each :name one encoded segment, the query as sent (AC-1.2)"
    )
    request = fake_gitlab.requests[0]
    assert media_type(value=request.header(name=HEADER_CONTENT_TYPE)) == case.media, (
        f"the body's Content-Type: {request.header(name=HEADER_CONTENT_TYPE)!r}"
    )
    assert decoded_body(request=request) == case.body, "the body: JSON by default, form pairs for a FORM record"
    assert credentials(request=request) == case.credential, (
        "the configured token type's one credential header (PRIVATE-TOKEN, Authorization, JOB-TOKEN; #13 AC-2.1)"
    )


# --- AC-1.3: each Kind in its place -------------------------------------------------------------------------------

ATTRIBUTE = "options"
ATTRIBUTE_PATH = "/projects/:id/synthetic_attributes"
ATTRIBUTE_URL = project_url(path="/synthetic_attributes")
LOCATION_QUERY = "QUERY"
LOCATION_BODY = "BODY"
BODY_JSON = "JSON"
BODY_FORM = "FORM"


class Placement(NamedTuple):
    """Where the synthetic attribute is declared: its record's method, the ``Location`` and the ``BodyFormat``."""

    name: str
    method: str
    location: str
    body: str


PLACEMENTS = (
    Placement(name="json-body", method=METHOD_PUT, location=LOCATION_BODY, body=BODY_JSON),
    Placement(name="query", method=METHOD_GET, location=LOCATION_QUERY, body=BODY_JSON),
    Placement(name="form-body", method=METHOD_POST, location=LOCATION_BODY, body=BODY_FORM),
)


class KindValue(NamedTuple):
    """A value of one ``Kind``: the ``-F`` JSON text, the value it parses to, and ``registry.encode``'s pairs of it."""

    kind: str
    text: str
    value: Any
    pairs: Tuple[Tuple[str, str], ...]


# conventions.md "Arrays, hashes and arrays of hashes": `name[]=v`, `name[k]=v`, `name[0][k]=v`; booleans as `true` and
# `false` (#13 AC-2.3).
KIND_VALUES = (
    KindValue(kind="SCALAR", text="true", value=True, pairs=((ATTRIBUTE, "true"),)),
    KindValue(kind="ARRAY", text='["a", 2]', value=["a", 2], pairs=((f"{ATTRIBUTE}[]", "a"), (f"{ATTRIBUTE}[]", "2"))),
    KindValue(
        kind="HASH",
        text='{"k": "v", "n": 1, "flag": false}',
        value={"k": "v", "n": 1, "flag": False},
        pairs=((f"{ATTRIBUTE}[k]", "v"), (f"{ATTRIBUTE}[n]", "1"), (f"{ATTRIBUTE}[flag]", "false")),
    ),
    KindValue(
        kind="ARRAY_OF_HASHES",
        text='[{"key": "VAR1", "value": "hello"}, {"key": "VAR2", "value": "world"}]',
        value=[{"key": "VAR1", "value": "hello"}, {"key": "VAR2", "value": "world"}],
        pairs=(
            (f"{ATTRIBUTE}[0][key]", "VAR1"),
            (f"{ATTRIBUTE}[0][value]", "hello"),
            (f"{ATTRIBUTE}[1][key]", "VAR2"),
            (f"{ATTRIBUTE}[1][value]", "world"),
        ),
    ),
)


def attribute_record(*, kind: str, placement: Placement) -> Synthetic:
    """The synthetic record declaring one attribute, ``options``, of ``kind`` where ``placement`` says."""

    def build(*, registry: ModuleType) -> Any:
        return registry.RestOperation(
            operation_id=OP_ATTRIBUTE_RECORD,
            method=placement.method,
            path=ATTRIBUTE_PATH,
            params=(
                registry.Param(
                    name=ATTRIBUTE,
                    location=getattr(registry.Location, placement.location),
                    kind=getattr(registry.Kind, kind),
                ),
            ),
            body=getattr(registry.BodyFormat, placement.body),
        )

    return Synthetic(module=PLAN, build=build)


class AttributeCase(NamedTuple):
    """One call giving attributes, and its request: method, URL before the query, the query pairs, the body's media
    type and decoded body (multipart: its fields and its files)."""

    synthetic: Synthetic
    argv: Tuple[str, ...]
    method: str
    url: str
    query: Tuple[Tuple[str, str], ...]
    media: Optional[str]
    body: Any


def attribute_cases() -> List[Any]:
    """Each ``Kind`` natively in a JSON body and as bracket pairs in a query and in a form body; a ``--file``
    attribute beside two body attributes, sent as ``multipart/form-data`` (design.md "Correctness Properties")."""
    cases: List[Any] = []
    for kind_value in KIND_VALUES:
        for placement in PLACEMENTS:
            query: Tuple[Tuple[str, str], ...]
            media: Optional[str]
            body: Any
            if placement.location == LOCATION_QUERY:
                query, media, body = kind_value.pairs, None, None
            elif placement.body == BODY_FORM:
                query, media, body = (), CONTENT_TYPE_FORM, kind_value.pairs
            else:
                query, media, body = (), CONTENT_TYPE_JSON, {ATTRIBUTE: kind_value.value}
            case = AttributeCase(
                synthetic=attribute_record(kind=kind_value.kind, placement=placement),
                argv=(OP_ATTRIBUTE_RECORD, OPTION_FIELD, f"{ATTRIBUTE}={kind_value.text}"),
                method=placement.method,
                url=ATTRIBUTE_URL,
                query=query,
                media=media,
                body=body,
            )
            cases.append(pytest.param(case, id=f"{kind_value.kind.lower()}-{placement.name}"))
    upload = AttributeCase(
        synthetic=UPLOAD_RECORD,
        argv=(
            OP_UPLOAD_RECORD,
            OPTION_FILE,
            f"file={UPLOAD_MARK}",
            OPTION_RAW_FIELD,
            "title=T",
            OPTION_FIELD,
            'labels=["a", "b"]',
        ),
        method=METHOD_POST,
        url=project_url(path="/synthetic_uploads"),
        query=(),
        media=CONTENT_TYPE_MULTIPART,
        body=(((FIELD_TITLE, "T"), ("labels[]", "a"), ("labels[]", "b")), (("file", UPLOAD_BYTES),)),
    )
    cases.append(pytest.param(upload, id="file-multipart"))
    return cases


@pytest.mark.parametrize(argnames="case", argvalues=attribute_cases())
def test_an_attribute_carries_its_kind(
    case: AttributeCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install(monkeypatch=monkeypatch, records=(case.synthetic,))
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert [request.method for request in fake_gitlab.requests] == [case.method], f"sent: {sent(fake=fake_gitlab)}"
    request = fake_gitlab.requests[0]
    url, _, query = request.url.partition(QUERY_SEPARATOR)
    assert url == case.url, f"the record's path, id the configured project: {request.url}"
    assert tuple(urllib.parse.parse_qsl(qs=query, keep_blank_values=True)) == case.query, (
        f"a query attribute is sent as registry.encode's bracket pairs (AC-1.3): {request.url}"
    )
    assert media_type(value=request.header(name=HEADER_CONTENT_TYPE)) == case.media
    assert decoded_body(request=request) == case.body, (
        "natively in a JSON body, as bracket pairs in a form body, and with a file as multipart: the file's bytes "
        "unchanged and every other body attribute a form field (AC-1.3)"
    )


@pytest.mark.parametrize(
    argnames="text",
    argvalues=[
        pytest.param("NaN", id="nan"),
        pytest.param("Infinity", id="infinity"),
        pytest.param("-Infinity", id="minus-infinity"),
    ],
)
def test_a_field_that_is_not_json_is_refused(
    text: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    answer_anything(fake=fake_gitlab)
    code = run_call(
        root=project, argv=(OP_UPDATE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}", OPTION_FIELD, f"title={text}")
    )
    captured = capsys.readouterr()
    assert code == EXIT_USAGE, f"-F text that is not JSON exits {EXIT_USAGE}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [], "argparse refuses the text before the config is read: no request"
    assert USAGE_PREFIX in captured.err and FIELD_OPTION_NAME in captured.err, (
        f"argparse's usage message names the option {FIELD_OPTION_NAME} (design.md D2); stderr:\n{captured.err}"
    )
    assert json.dumps(obj=FIELD_TITLE) in captured.err, (
        f"the message names the attribute as json.dumps renders it, {json.dumps(obj=FIELD_TITLE)}; stderr:\n"
        f"{captured.err}"
    )
    assert text not in captured.err, f"the message never holds the value {text!r}; stderr:\n{captured.err}"


# --- AC-1.4 to AC-1.6: what prints --------------------------------------------------------------------------------

LABEL_ITEMS: Tuple[Dict[str, Any], ...] = (
    {FIELD_ID: 601, FIELD_NAME: "in-progress"},
    {FIELD_ID: 602, FIELD_NAME: "blocked"},
)
ISSUE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_IID: 7, FIELD_TITLE: "first"}, {FIELD_IID: 8, FIELD_TITLE: "second"})


class ListCase(NamedTuple):
    """A list call: the pages the host serves, in order, and every item they hold."""

    argv: Tuple[str, ...]
    answers: Tuple[Answer, ...]
    items: Tuple[Any, ...]
    synthetic: Tuple[Synthetic, ...] = ()


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            ListCase(
                argv=(OP_LIST_LABELS,),
                answers=(
                    json_answer(
                        method=METHOD_GET,
                        url=f"{LABELS_URL}?per_page=100",
                        value=[LABEL_ITEMS[0]],
                        headers=((HEADER_NEXT_PAGE, "2"),),
                    ),
                    json_answer(
                        method=METHOD_GET,
                        url=f"{LABELS_URL}?per_page=100&page=2",
                        value=[LABEL_ITEMS[1]],
                        headers=((HEADER_NEXT_PAGE, ""),),
                    ),
                ),
                items=LABEL_ITEMS,
            ),
            id="offset-by-x-next-page",
        ),
        pytest.param(
            ListCase(
                argv=(OP_KEYSET_ISSUES,),
                answers=(
                    json_answer(
                        method=METHOD_GET,
                        url=ISSUES_URL,
                        value=[ISSUE_ITEMS[0]],
                        headers=((HEADER_LINK, f'<{KEYSET_NEXT_URL}>; rel="next"'),),
                    ),
                    json_answer(method=METHOD_GET, url=KEYSET_NEXT_URL, value=[ISSUE_ITEMS[1]]),
                ),
                items=ISSUE_ITEMS,
                synthetic=(KEYSET_ISSUES_RECORD,),
            ),
            id="keyset-by-link-next",
        ),
    ],
)
def test_a_list_prints_every_page_as_one_array(
    case: ListCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    script_answers(fake=fake_gitlab, answers=case.answers)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(answer.method, answer.url) for answer in case.answers], (
        "each page requested as Transport.pages does (#13 AC-2.5, AC-2.6)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(case.items)), (
        f"one JSON array of every item of every page, in page order, as print_json writes it (AC-1.4):\n{captured.out}"
    )


# A title outside ASCII, sent as UTF-8 under `charset=utf-8` (written as an escape, so this file stays ASCII).
ISSUE: Dict[str, Any] = {FIELD_IID: ISSUE_IID, FIELD_TITLE: "Caf\u00e9 parser", FIELD_LABELS: ["bug"]}


class PrintCase(NamedTuple):
    """A call of a ``Paging.NONE`` record, the host's answer, and the text on standard output."""

    argv: Tuple[str, ...]
    answer: Answer
    printed: str


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            PrintCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"),
                answer=Answer(
                    method=METHOD_GET,
                    url=ISSUE_URL,
                    headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON_UTF8),),
                    body=json.dumps(obj=ISSUE, ensure_ascii=False).encode(encoding=TEXT_ENCODING),
                ),
                printed=printed_json(value=ISSUE),
            ),
            id="json-with-charset",
        ),
        pytest.param(
            PrintCase(
                argv=(OP_DELETE_BRANCH, OPTION_PATH, f"branch={BRANCH}"),
                answer=Answer(method=METHOD_DELETE, url=BRANCH_URL, status=STATUS_NO_CONTENT),
                printed="",
            ),
            id="empty-204",
        ),
        # An empty body under a JSON Content-Type: nothing, not print_json of the empty body's None (AC-1.5).
        pytest.param(
            PrintCase(
                argv=(OP_DELETE_BRANCH, OPTION_PATH, f"branch={BRANCH}"),
                answer=Answer(method=METHOD_DELETE, url=BRANCH_URL, status=STATUS_NO_CONTENT, headers=JSON_HEADERS),
                printed="",
            ),
            id="empty-204-json-content-type",
        ),
        pytest.param(
            PrintCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"),
                answer=Answer(method=METHOD_GET, url=ISSUE_URL, headers=JSON_HEADERS),
                printed="",
            ),
            id="empty-200-json-content-type",
        ),
    ],
)
def test_a_json_or_empty_body_prints_as_documented(
    case: PrintCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    script_answers(fake=fake_gitlab, answers=(case.answer,))
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.answer.method, case.answer.url)]
    assert captured.out == case.printed, (
        f"a JSON Content-Type prints print_json of the body, an empty body nothing (AC-1.5):\n{captured.out}"
    )


class RawCase(NamedTuple):
    """A call answered with a body that is not JSON by its ``Content-Type``, the bytes on standard output, and the
    URLs whose request must carry no credential header."""

    argv: Tuple[str, ...]
    answers: Tuple[Answer, ...]
    printed: bytes
    synthetic: Tuple[Synthetic, ...] = ()
    uncredentialed: Tuple[str, ...] = ()


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            RawCase(
                argv=(OP_JOB_TRACE, OPTION_PATH, f"job_id={JOB_ID}"),
                answers=(
                    Answer(
                        method=METHOD_GET,
                        url=TRACE_URL,
                        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_TEXT),),
                        body=TRACE_BYTES,
                    ),
                ),
                printed=TRACE_BYTES,
            ),
            id="text-plain-job-trace",
        ),
        pytest.param(
            RawCase(
                argv=(OP_JOB_TRACE, OPTION_PATH, f"job_id={JOB_ID}"),
                answers=(
                    Answer(
                        method=METHOD_GET,
                        url=TRACE_URL,
                        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_OCTET_STREAM),),
                        body=NOT_UTF8_BYTES,
                    ),
                ),
                printed=NOT_UTF8_BYTES,
            ),
            id="octet-stream-not-utf8",
        ),
        pytest.param(
            RawCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"),
                answers=(Answer(method=METHOD_GET, url=ISSUE_URL, body=JSON_TEXT_BYTES),),
                printed=JSON_TEXT_BYTES,
            ),
            id="json-text-without-content-type",
        ),
        pytest.param(
            RawCase(
                argv=(OP_DOWNLOAD_ARTIFACTS, OPTION_PATH, f"job_id={JOB_ID}"),
                answers=(
                    Answer(
                        method=METHOD_GET,
                        url=ARTIFACTS_URL,
                        status=STATUS_FOUND,
                        headers=((HEADER_LOCATION, STORAGE_URL),),
                    ),
                    Answer(
                        method=METHOD_GET,
                        url=STORAGE_URL,
                        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_ZIP),),
                        body=ZIP_BYTES,
                    ),
                ),
                printed=ZIP_BYTES,
                uncredentialed=(STORAGE_URL,),
            ),
            id="artifacts-after-a-redirect",
        ),
    ],
)
def test_a_body_that_is_not_json_is_written_unchanged(
    case: RawCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    script_answers(fake=fake_gitlab, answers=case.answers)
    code = run_call(root=project, argv=case.argv)
    captured = capsysbinary.readouterr()
    stderr = captured.err.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{stderr}"
    assert sent(fake=fake_gitlab) == [(answer.method, answer.url) for answer in case.answers]
    assert captured.out == case.printed, (
        f"the body's bytes unchanged, no line end added (AC-1.6); standard output: {captured.out!r}"
    )
    for request in fake_gitlab.requests:
        if request.url in case.uncredentialed:
            assert credentials(request=request) == (None, None, None), (
                f"the redirect to another origin drops the credential (#13 AC-3.1): {request.url}"
            )


# --- AC-1.7: an API error -----------------------------------------------------------------------------------------

NOT_FOUND_BODY: Dict[str, Any] = {FIELD_MESSAGE: "404 Issue Not Found"}
RATE_LIMITED_BODY: Dict[str, Any] = {FIELD_MESSAGE: "429 Too Many Requests"}
GRAPHQL_ERRORS_BODY: Dict[str, Any] = {FIELD_DATA: None, FIELD_ERRORS: [{FIELD_MESSAGE: GRAPHQL_ERROR}]}


class ErrorCase(NamedTuple):
    """A call that raises ``GitLabAPIError``: the answers (each served once, or once per attempt when ``retried``),
    the text its first log record names, and its details, the second record (``None``: it has none)."""

    argv: Tuple[str, ...]
    answers: Tuple[Answer, ...]
    named: str
    details: Optional[str]
    synthetic: Tuple[Synthetic, ...] = ()
    retried: bool = False


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            ErrorCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"),
                answers=(json_answer(method=METHOD_GET, url=ISSUE_URL, value=NOT_FOUND_BODY, status=STATUS_NOT_FOUND),),
                named=NOT_FOUND_BODY[FIELD_MESSAGE],
                details=json_text(value=NOT_FOUND_BODY),
            ),
            id="http-404",
        ),
        pytest.param(
            ErrorCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"),
                answers=(
                    json_answer(
                        method=METHOD_GET,
                        url=ISSUE_URL,
                        value=RATE_LIMITED_BODY,
                        status=STATUS_TOO_MANY_REQUESTS,
                        headers=((HEADER_RETRY_AFTER, "0"),),
                    ),
                ),
                named=RATE_LIMITED_BODY[FIELD_MESSAGE],
                details=json_text(value=RATE_LIMITED_BODY),
                retried=True,
            ),
            id="rate-limit-retries-spent",
        ),
        pytest.param(
            ErrorCase(
                argv=(OP_GRAPHQL_PROJECT, OPTION_RAW_FIELD, f"{VARIABLE_FULL_PATH}={FULL_PATH}"),
                answers=(json_answer(method=METHOD_POST, url=GRAPHQL_URL, value=GRAPHQL_ERRORS_BODY),),
                named=GRAPHQL_ERROR,
                details=json_text(value=GRAPHQL_ERRORS_BODY),
                synthetic=(GRAPHQL_PROJECT_RECORD,),
            ),
            id="graphql-errors-at-200",
        ),
        pytest.param(
            ErrorCase(argv=(OP_LIST_LABELS, OPTION_PATH, "id=.."), answers=(), named=PATH_ID, details=None),
            id="dot-dot-id-of-a-paged-record",
        ),
        pytest.param(
            ErrorCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, "issue_iid=.."), answers=(), named="issue_iid", details=None
            ),
            id="dot-dot-issue-iid",
        ),
    ],
)
def test_an_api_error_exits_1_with_its_details(
    case: ErrorCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    attempts = gitlab_module(name=TRANSPORT).RATE_LIMIT_MAX_RETRIES + 1 if case.retried else 1
    script_answers(fake=fake_gitlab, answers=case.answers, times=attempts)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_API_ERROR, f"call {list(case.argv)} exits {EXIT_API_ERROR}, got {code}; stderr:\n{captured.err}"
    assert captured.out == "", f"an API error prints nothing on standard output:\n{captured.out}"
    assert sent(fake=fake_gitlab) == [
        (answer.method, answer.url) for answer in case.answers for _ in range(attempts)
    ], "every attempt the transport makes, and none for a path value that is not one segment"
    messages = error_messages(caplog=caplog)
    expected = [case.named] if case.details is None else [case.named, case.details]
    assert len(messages) == len(expected), (
        f"main logs the error's message, then its details when it has any (AC-1.7); logged: {messages!r}"
    )
    assert names(text=messages[0], name=case.named), f"the message names {case.named!r}: {messages[0]!r}"
    if case.details is not None:
        assert messages[1] == case.details, f"the details are the response body: {messages[1]!r}"


# --- AC-1.8: the configured project -------------------------------------------------------------------------------


class ProjectCase(NamedTuple):
    """A call and the URL its one GET is sent to (``None``: refused as in AC-2.3, naming ``id``)."""

    argv: Tuple[str, ...]
    url: Optional[str]
    synthetic: Tuple[Synthetic, ...] = ()


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            ProjectCase(argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}"), url=ISSUE_URL),
            id="project-id-default",
        ),
        pytest.param(
            ProjectCase(
                argv=(OP_RETRIEVE_ISSUE, OPTION_PATH, f"issue_iid={ISSUE_IID}", OPTION_PATH, "id=group/project"),
                url=f"{REST_BASE}/projects/group%2Fproject/issues/{ISSUE_IID}",
            ),
            id="id-given",
        ),
        pytest.param(
            ProjectCase(
                argv=(OP_PROJECT_RECORD,), url=f"{REST_BASE}/projects/{PROJECT_ID}", synthetic=(PROJECT_RECORD,)
            ),
            id="projects-id-itself",
        ),
        pytest.param(
            ProjectCase(argv=(OP_GROUP_LABELS_RECORD,), url=None, synthetic=(GROUP_LABELS_RECORD,)),
            id="group-id-has-no-default",
        ),
    ],
)
def test_a_project_path_takes_the_configured_project(
    case: ProjectCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    if case.url is None:
        messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
        assert any(names(text=message, name=PATH_ID) for message in messages), (
            f"only a /projects/:id path defaults id; the refusal names the missing {PATH_ID!r}; logged: {messages!r}"
        )
        return
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, case.url)], (
        "without --path id the configured project_id, with it the value given, as one encoded segment (AC-1.8)"
    )


# --- AC-1.9: a GraphQL record -------------------------------------------------------------------------------------


def connection_page(*, nodes: Sequence[Any], has_next_page: bool, end_cursor: Optional[str]) -> Dict[str, Any]:
    """One page of the ``project.issues`` connection, as ``/api/graphql`` answers it."""
    page_info = {FIELD_HAS_NEXT_PAGE: has_next_page, FIELD_END_CURSOR: end_cursor}
    issues = {FIELD_NODES: list(nodes), FIELD_PAGE_INFO: page_info}
    return {FIELD_DATA: {FIELD_PROJECT: {FIELD_ISSUES: issues}}}


class GraphQLCase(NamedTuple):
    """A call of a GraphQL record: the document, each page the host answers, the variables each request sends, and
    the value printed."""

    argv: Tuple[str, ...]
    synthetic: Synthetic
    document: str
    pages: Tuple[Dict[str, Any], ...]
    variables: Tuple[Dict[str, Any], ...]
    printed: Any


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            GraphQLCase(
                argv=(
                    OP_GRAPHQL_PROJECT,
                    OPTION_RAW_FIELD,
                    f"{VARIABLE_FULL_PATH}={FULL_PATH}",
                    OPTION_FIELD,
                    f"{VARIABLE_FIRST}=2",
                ),
                synthetic=GRAPHQL_PROJECT_RECORD,
                document=PROJECT_DOCUMENT,
                pages=({FIELD_DATA: PROJECT_DATA},),
                variables=({VARIABLE_FULL_PATH: FULL_PATH, VARIABLE_FIRST: 2},),
                printed=PROJECT_DATA,
            ),
            id="data",
        ),
        pytest.param(
            GraphQLCase(
                argv=(OP_GRAPHQL_ISSUES, OPTION_RAW_FIELD, f"{VARIABLE_FULL_PATH}={FULL_PATH}"),
                synthetic=GRAPHQL_ISSUES_RECORD,
                document=ISSUES_DOCUMENT,
                pages=(
                    connection_page(nodes=ISSUE_NODES[:1], has_next_page=True, end_cursor=END_CURSOR),
                    connection_page(nodes=ISSUE_NODES[1:], has_next_page=False, end_cursor=None),
                ),
                variables=(
                    {VARIABLE_FULL_PATH: FULL_PATH, FIELD_AFTER: None},
                    {VARIABLE_FULL_PATH: FULL_PATH, FIELD_AFTER: END_CURSOR},
                ),
                printed=list(ISSUE_NODES),
            ),
            id="connection-over-two-pages",
        ),
    ],
)
def test_a_graphql_record_sends_its_document(
    case: GraphQLCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install(monkeypatch=monkeypatch, records=(case.synthetic,))
    for page in case.pages:
        fake_gitlab.script(method=METHOD_POST, url=GRAPHQL_URL, body=page)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_POST, GRAPHQL_URL)] * len(case.variables), "one POST per page"
    assert [request.json() for request in fake_gitlab.requests] == [
        {FIELD_QUERY: case.document, FIELD_VARIABLES: variables} for variables in case.variables
    ], "the record's document, each variable as the JSON value given, `after` the previous page's endCursor (AC-1.9)"
    assert [request.header(name=HEADER_AUTHORIZATION) for request in fake_gitlab.requests] == [
        BEARER_PREFIX + TOKEN
    ] * len(case.variables), "GraphQL carries the token as Authorization: Bearer (#13 AC-4.1)"
    assert captured.out == printed_json(value=case.printed), (
        f"data, or one array of the nodes of every page, as print_json writes it (AC-1.9):\n{captured.out}"
    )


# --- AC-2.1 to AC-2.4: the refusals -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    argnames="operation_id",
    argvalues=[
        pytest.param(OP_PENDING_ONLY, id="only-on-a-pending-list"),
        pytest.param(OP_UNDECLARED, id="not-in-the-reference"),
    ],
)
def test_an_unknown_operation_is_refused(
    operation_id: str,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=(operation_id,))
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    assert any(operation_id in message for message in messages), (
        f"the refusal names the ID {operation_id!r} (AC-2.1); logged: {messages!r}"
    )


class UndocumentedCase(NamedTuple):
    """A call giving parameters its record does not document, each with the option D4's message names it by."""

    argv: Tuple[str, ...]
    undocumented: Tuple[Tuple[str, str], ...]
    synthetic: Tuple[Synthetic, ...] = ()


ISSUE_PATH = (OPTION_PATH, f"issue_iid={ISSUE_IID}")


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            UndocumentedCase(
                argv=(OP_RETRIEVE_ISSUE, *ISSUE_PATH, OPTION_PATH, "number=5"), undocumented=(("number", OPTION_PATH),)
            ),
            id="path-parameter",
        ),
        pytest.param(
            UndocumentedCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_QUERY, "title=T"),
                undocumented=((FIELD_TITLE, OPTION_QUERY),),
            ),
            id="body-attribute-as-query",
        ),
        pytest.param(
            UndocumentedCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_RAW_FIELD, "colour=red"),
                undocumented=(("colour", OPTION_FIELDS),),
            ),
            id="attribute",
        ),
        pytest.param(
            UndocumentedCase(
                argv=(
                    OP_UPDATE_ISSUE,
                    *ISSUE_PATH,
                    OPTION_PATH,
                    "number=5",
                    OPTION_QUERY,
                    "title=T",
                    OPTION_RAW_FIELD,
                    "colour=red",
                ),
                undocumented=(("number", OPTION_PATH), (FIELD_TITLE, OPTION_QUERY), ("colour", OPTION_FIELDS)),
            ),
            id="all-three-in-one-message",
        ),
        pytest.param(
            UndocumentedCase(
                argv=(OP_GRAPHQL_PROJECT, OPTION_RAW_FIELD, "unknown=1", OPTION_QUERY, "x=1"),
                undocumented=(("unknown", OPTION_FIELDS), ("x", OPTION_QUERY)),
                synthetic=(GRAPHQL_PROJECT_RECORD,),
            ),
            id="graphql-variable-and-query",
        ),
        pytest.param(
            UndocumentedCase(
                argv=(OP_GRAPHQL_ISSUES, OPTION_RAW_FIELD, f"{FIELD_AFTER}=c"),
                undocumented=((FIELD_AFTER, OPTION_FIELDS),),
                synthetic=(GRAPHQL_ISSUES_RECORD,),
            ),
            id="connection-cursor",
        ),
    ],
)
def test_an_undocumented_parameter_is_refused(
    case: UndocumentedCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    registry = gitlab_module(name=REGISTRY)
    documented = documented_parameters(registry=registry, record=registry.lookup(operation_id=case.argv[0]))
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    # Each name the caller supplied is rendered with json.dumps (design.md D4), beside the option it was given with.
    supplied = [json.dumps(obj=name) for name, _ in case.undocumented]
    options = [option for _, option in case.undocumented]
    naming = [
        message
        for message in messages
        if all(text in message for text in (*supplied, *options))
        and all(names(text=message, name=name) for name in documented)
    ]
    assert naming, (
        f"one log record names each undocumented parameter {supplied} with its option {options}, and the record's "
        f"documented parameters {list(documented)} (AC-2.2); logged: {messages!r}"
    )


class MissingCase(NamedTuple):
    """A call leaving a path parameter without a value, once ``id`` has its default."""

    argv: Tuple[str, ...]
    missing: Tuple[str, ...]
    path_parameters: Tuple[str, ...]
    synthetic: Tuple[Synthetic, ...] = ()


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            MissingCase(argv=(OP_RETRIEVE_ISSUE,), missing=("issue_iid",), path_parameters=(PATH_ID, "issue_iid")),
            id="issue-iid",
        ),
        pytest.param(
            MissingCase(
                argv=(OP_GROUP_LABELS_RECORD,),
                missing=(PATH_ID,),
                path_parameters=(PATH_ID,),
                synthetic=(GROUP_LABELS_RECORD,),
            ),
            id="group-id",
        ),
    ],
)
def test_a_missing_path_parameter_is_refused(
    case: MissingCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    install(monkeypatch=monkeypatch, records=case.synthetic)
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    naming = [
        message
        for message in messages
        if all(names(text=message, name=name) for name in (*case.missing, *case.path_parameters))
    ]
    assert naming, (
        f"one log record names the missing {list(case.missing)} and the path parameters "
        f"{list(case.path_parameters)} (AC-2.3); logged: {messages!r}"
    )


class ShapeCase(NamedTuple):
    """A call giving an attribute a value of a shape its ``Kind`` (a ``registry.Kind`` member name) does not take."""

    argv: Tuple[str, ...]
    attribute: str
    kind: str


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            ShapeCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_RAW_FIELD, "assignee_ids=1"),
                attribute=FIELD_ASSIGNEE_IDS,
                kind="ARRAY",
            ),
            id="string-for-an-array",
        ),
        pytest.param(
            ShapeCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_FIELD, 'title={"a": 1}'),
                attribute=FIELD_TITLE,
                kind="SCALAR",
            ),
            id="object-for-a-scalar",
        ),
        pytest.param(
            ShapeCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_FILE, f"title={UPLOAD_MARK}"),
                attribute=FIELD_TITLE,
                kind="SCALAR",
            ),
            id="file-for-a-scalar",
        ),
        pytest.param(
            ShapeCase(argv=(OP_LIST_ISSUES, OPTION_QUERY, "not=x"), attribute="not", kind="HASH"),
            id="string-for-a-hash",
        ),
    ],
)
def test_a_value_of_the_wrong_shape_is_refused(
    case: ShapeCase,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    kind = getattr(gitlab_module(name=REGISTRY).Kind, case.kind)
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    # The attribute as registry.encode (repr) or call.py (json.dumps) renders it; its Kind by value or by name.
    renderings = (repr(case.attribute), json.dumps(obj=case.attribute))
    naming = [
        message
        for message in messages
        if any(rendering in message for rendering in renderings)
        and (
            names(text=message, name=kind.value, ignore_case=True)
            or names(text=message, name=kind.name, ignore_case=True)
        )
    ]
    assert naming, (
        f"one log record names the attribute {case.attribute!r} and its Kind {kind.value!r} (AC-2.4); logged: "
        f"{messages!r}"
    )


class MalformedCase(NamedTuple):
    """A call holding a ``NAME=VALUE`` argparse refuses (design.md D2 "Parsing", D4): the option as argparse's usage
    error names it, the name its message renders with ``json.dumps`` (the text before the first ``=``, all of it when
    there is none), and each value text standard error must not hold."""

    argv: Tuple[str, ...]
    option: str
    name: str
    withheld: Tuple[str, ...] = ()


PATH_ISSUE_IID = "issue_iid"
QUERY_STATE = "state"
EMPTY_NAME = ""
# The text after the first `=` of an empty name: a value, which no message holds (design.md D2).
WITHHELD_PATH_VALUE = "withheld-path-value"
WITHHELD_QUERY_VALUE = "withheld-query-value"
WITHHELD_FIELD_VALUE = "withheld-field-value"


def argument_named(*, option: str) -> str:
    """The start of argparse's usage error for ``option``: ``error: argument <option>: `` and then the message."""
    return f"error: argument {option}: "


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            MalformedCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_RAW_FIELD, FIELD_TITLE),
                option=RAW_FIELD_OPTION_NAME,
                name=FIELD_TITLE,
            ),
            id="raw-field-without-an-equals-sign",
        ),
        pytest.param(
            MalformedCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_RAW_FIELD, f"={WITHHELD_FIELD_VALUE}"),
                option=RAW_FIELD_OPTION_NAME,
                name=EMPTY_NAME,
                withheld=(WITHHELD_FIELD_VALUE,),
            ),
            id="raw-field-with-an-empty-name",
        ),
        pytest.param(
            MalformedCase(argv=(OP_UPDATE_ISSUE, OPTION_PATH, PATH_ISSUE_IID), option=OPTION_PATH, name=PATH_ISSUE_IID),
            id="path-without-an-equals-sign",
        ),
        pytest.param(
            MalformedCase(
                argv=(OP_UPDATE_ISSUE, *ISSUE_PATH, OPTION_PATH, f"={WITHHELD_PATH_VALUE}"),
                option=OPTION_PATH,
                name=EMPTY_NAME,
                withheld=(WITHHELD_PATH_VALUE,),
            ),
            id="path-with-an-empty-name",
        ),
        pytest.param(
            MalformedCase(argv=(OP_LIST_ISSUES, OPTION_QUERY, QUERY_STATE), option=OPTION_QUERY, name=QUERY_STATE),
            id="query-without-an-equals-sign",
        ),
        pytest.param(
            MalformedCase(
                argv=(OP_LIST_ISSUES, OPTION_QUERY, f"={WITHHELD_QUERY_VALUE}"),
                option=OPTION_QUERY,
                name=EMPTY_NAME,
                withheld=(WITHHELD_QUERY_VALUE,),
            ),
            id="query-with-an-empty-name",
        ),
    ],
)
def test_a_malformed_argument_is_refused_without_its_value(
    case: MalformedCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """Requirement 2, design.md D4 (a malformed ``NAME=VALUE``): exit 2 before any request, nothing on standard output,
    and standard error is argparse's usage message, whose error names the option and then the name as ``json.dumps``
    renders it, and holds no value (D2)."""
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_USAGE, f"a malformed NAME=VALUE exits {EXIT_USAGE}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [], "argparse refuses the argument before the config is read: no request"
    assert captured.out == "", f"a usage error prints nothing on standard output:\n{captured.out}"
    lines = captured.err.splitlines()
    assert any(line.startswith(USAGE_PREFIX) for line in lines), f"standard error holds no usage:\n{captured.err}"
    named_option = argument_named(option=case.option)
    messages = [line.split(sep=named_option, maxsplit=1)[1] for line in lines if named_option in line]
    assert messages, f"no usage error names the option {case.option} (design.md D2); stderr:\n{captured.err}"
    rendered = json.dumps(obj=case.name)
    assert any(rendered in message for message in messages), (
        f"the usage error names {rendered}, the name as json.dumps renders it (design.md D2): {messages}"
    )
    leaking = [value for value in case.withheld if value in captured.err]
    assert leaking == [], f"standard error holds the value {leaking} (design.md D2); stderr:\n{captured.err}"


# --- UB-2.1: no token option --------------------------------------------------------------------------------------


def subcommand_parser(*, parser: argparse.ArgumentParser, name: str) -> Optional[argparse.ArgumentParser]:
    """The parser of the top-level subcommand ``name``; ``None`` when the entry script has no such subcommand."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices.get(name)
    return None


def test_call_takes_no_token_option() -> None:
    parser = fixtures.load_wrapper(module_name=WRAPPER_MODULE).build_parser()
    call_parser = subcommand_parser(parser=parser, name=CALL)
    assert call_parser is not None, (
        "the entry script's parser has no `call` subcommand: build_parser registers commands/call.py (design.md D1)"
    )
    options = [option for action in call_parser._actions for option in action.option_strings]
    assert [option for option in options if TOKEN_TEXT in option.lower()] == [], (
        f"no option string of `call` holds {TOKEN_TEXT!r}: the credential comes from config/gitlab.json only "
        f"(UB-2.1); options: {options}"
    )


# --- Issue #40 AC-2.3, AC-2.4, AC-3.2: an optional path parameter and the raw body ------------------------------------

# Issue #40's records the cases call (families/openapi_only.py), each the Reference of its index row:
# `GET` and `PUT /projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name`, and
# `GET /projects/:id/packages/npm/*package_name` (rest/openapi-only.md "Download package file", "Upload package file",
# "NPM registry metadata endpoint").
OP_DOWNLOAD_PACKAGE_FILE = "openapi-only#download-package-file"
OP_UPLOAD_PACKAGE_FILE = "openapi-only#upload-package-file"
OP_NPM_METADATA = "openapi-only#npm-registry-metadata-endpoint-2"
# The generic package's path values but `file_name` and the optional group's `path`; then with `file_name`.
PACKAGE_PATH = (OPTION_PATH, "package_name=pkg", OPTION_PATH, "package_version=1.0")
PACKAGE_FILE_PATH = (*PACKAGE_PATH, OPTION_PATH, "file_name=file.txt")
# How check_parameters says a path parameter has no value, and how documented_text lists the record's path parameters
# (#41 design.md D4): `the path parameter <name> has no value`, `its path parameters: <a>, <b>; its attributes: ...`.
NO_VALUE_SUFFIX = " has no value"
PATH_PARAMETERS_LABEL = "its path parameters: "
PATH_PARAMETERS_END = ";"
PATH_PARAMETERS_SEPARATOR = ", "
# A file the raw body is read from that is never written into the project.
MISSING_INPUT_NAME = "missing.bin"


class OptionalCase(NamedTuple):
    """A call leaving path parameters without a value (issue #40 AC-2.3, AC-2.4): those outside an optional group,
    which one log record says have no value; those of an optional group, which no log record says have none; and the
    record's path parameters as that log record lists them, in path order."""

    argv: Tuple[str, ...]
    missing: Tuple[str, ...]
    left_out: Tuple[str, ...]
    path_parameters: Tuple[str, ...]


def says_no_value(*, text: str, name: str) -> bool:
    """Whether ``text`` says the path parameter ``name``, a word of its own, has no value."""
    pattern = f"{NAME_EDGE_BEFORE}{re.escape(pattern=name)}{re.escape(pattern=NO_VALUE_SUFFIX)}"
    return re.search(pattern=pattern, string=text) is not None


def listed_path_parameters(*, text: str) -> Optional[Tuple[str, ...]]:
    """The path parameters ``text`` lists after ``its path parameters: ``, in its order; ``None`` when it lists none."""
    _, label, rest = text.partition(PATH_PARAMETERS_LABEL)
    if not label:
        return None
    return tuple(rest.partition(PATH_PARAMETERS_END)[0].split(sep=PATH_PARAMETERS_SEPARATOR))


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            OptionalCase(
                argv=(OP_DOWNLOAD_PACKAGE_FILE, *PACKAGE_PATH),
                missing=("file_name",),
                left_out=("path",),
                path_parameters=(PATH_ID, "package_name", "package_version", "path", "file_name"),
            ),
            id="optional-group-left-out-beside-a-missing-segment",
        ),
        pytest.param(
            OptionalCase(
                argv=(OP_NPM_METADATA,),
                missing=("package_name",),
                left_out=(),
                path_parameters=(PATH_ID, "package_name"),
            ),
            id="glob-outside-a-group",
        ),
    ],
)
def test_a_missing_path_parameter_is_refused_unless_optional(
    case: OptionalCase,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #40 AC-2.3, AC-2.4 (design.md D2): a path parameter outside an optional group left without a value, a glob
    included, is refused as #41 AC-2.3 refuses one, exit 2 with no request; one log record says it has no value and
    lists the record's path parameters, an optional group's among them; and no log record says that an optional
    group's parameter the call leaves out has none."""
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=case.argv)
    messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
    naming = [
        message
        for message in messages
        if all(says_no_value(text=message, name=name) for name in case.missing)
        and listed_path_parameters(text=message) == case.path_parameters
    ]
    assert naming, (
        f"one log record says {list(case.missing)} have no value and lists the path parameters "
        f"{list(case.path_parameters)} (issue #40 AC-2.3, AC-2.4); logged: {messages!r}"
    )
    refusing_a_group = [
        message for message in messages if any(says_no_value(text=message, name=name) for name in case.left_out)
    ]
    assert refusing_a_group == [], (
        f"a call may leave out the optional group's parameter {list(case.left_out)}, and the group is then not sent: "
        f"no log record says it has no value (issue #40 AC-2.3); logged: {refusing_a_group!r}"
    )


class RawBodyCase(NamedTuple):
    """A call given a raw body it cannot send (issue #40 AC-3.2, design.md D5): the arguments before the raw body's
    option; the texts one log record holds beside that option's name; whether the file the option names is the
    ``project`` fixture's upload or a file never written; and the synthetic records."""

    argv: Tuple[str, ...]
    named: Tuple[str, ...] = ()
    written: bool = True
    synthetic: Tuple[Synthetic, ...] = ()


# A refusal of a raw body beside `-f` or `-F` names both body options as argparse names them, and `--query`, with which
# a raw-body record's attributes are given (design.md D5 step 1).
BOTH_BODIES_NAMED = (RAW_FIELD_OPTION_NAME, FIELD_OPTION_NAME, OPTION_QUERY)


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            RawBodyCase(
                argv=(OP_UPLOAD_PACKAGE_FILE, *PACKAGE_FILE_PATH, OPTION_RAW_FIELD, "status=hidden"),
                named=BOTH_BODIES_NAMED,
            ),
            id="beside-a-raw-field",
        ),
        pytest.param(
            RawBodyCase(
                argv=(OP_UPLOAD_PACKAGE_FILE, *PACKAGE_FILE_PATH, OPTION_FIELD, 'status="hidden"'),
                named=BOTH_BODIES_NAMED,
            ),
            id="beside-a-field",
        ),
        pytest.param(
            RawBodyCase(argv=(OP_RETRIEVE_ISSUE, *ISSUE_PATH), named=(OP_RETRIEVE_ISSUE,)),
            id="json-bodied-rest-record",
        ),
        pytest.param(
            RawBodyCase(argv=(OP_GRAPHQL_PROJECT,), named=(OP_GRAPHQL_PROJECT,), synthetic=(GRAPHQL_PROJECT_RECORD,)),
            id="graphql-record",
        ),
        pytest.param(
            RawBodyCase(argv=(OP_UPLOAD_PACKAGE_FILE, *PACKAGE_FILE_PATH), written=False),
            id="file-that-does-not-exist",
        ),
    ],
)
def test_a_raw_body_the_call_cannot_send_is_refused(
    case: RawBodyCase,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #40 AC-3.2 (design.md D5): ``--input`` beside ``-f`` or ``-F`` on a raw-body record, and ``--input`` on a
    record that is none (a JSON-bodied REST record, a GraphQL record), each exit 2 with no request and one log record
    naming ``--input`` and, beside ``-f`` or ``-F``, ``-f/--raw-field``, ``-F/--field`` and ``--query``, else the ID;
    ``--input`` naming a file that does not exist is argparse's usage error, whose ``argument --input:`` message names
    the path as ``json.dumps`` renders it, exit 2 with no request."""
    option_input = "--input"
    install(monkeypatch=monkeypatch, records=case.synthetic)
    source = UPLOAD_MARK if case.written else str(project / MISSING_INPUT_NAME)
    answer_anything(fake=fake_gitlab)
    code = run_call(root=project, argv=(*case.argv, option_input, source))
    if case.written:
        messages = refused_messages(code=code, fake=fake_gitlab, caplog=caplog, capsys=capsys)
        expected = (option_input, *case.named)
        assert any(all(text in message for text in expected) for message in messages), (
            f"one log record names {list(expected)} (issue #40 design.md D5); logged: {messages!r}"
        )
        return
    captured = capsys.readouterr()
    assert code == EXIT_USAGE, f"a {option_input} file that does not exist exits {EXIT_USAGE}, got {code}"
    assert sent(fake=fake_gitlab) == [], "argparse refuses the file before the config is read: no request"
    assert captured.out == "", f"a usage error prints nothing on standard output:\n{captured.out}"
    named_option = argument_named(option=option_input)
    messages = [
        line.split(sep=named_option, maxsplit=1)[1] for line in captured.err.splitlines() if named_option in line
    ]
    assert messages, f"no usage error names the option {option_input} (design.md D5); stderr:\n{captured.err}"
    rendered = json.dumps(obj=source)
    assert any(rendered in message for message in messages), (
        f"the usage error names the path as json.dumps renders it, {rendered} (design.md D5): {messages}"
    )
