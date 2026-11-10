"""The fake GitHub host the wrapper suites share: every request is scripted, recorded and answered without a socket.

Loaded by path (``importlib.util.spec_from_file_location``, as ``test_wrapper_delivery.load`` loads a wrapper) and
never collected, since its name matches no ``test_*.py`` pattern. Installed from
``src/payload/test/github_wrapper_fixtures.py`` to ``test/github_wrapper_fixtures.py``, beside the suites that load it.

``FakeGitHub.install`` patches ``urllib.request.HTTPSHandler.https_open`` and ``HTTPHandler.http_open``. Every opener
in the process (the product wrapper's and the installed fork's) then reaches the fake instead of a socket, while
urllib's ``HTTPErrorProcessor`` and redirect handling, and any handler a wrapper adds, run unchanged on its answers.
An answer is a ``urllib.response.addinfourl`` with ``msg`` set, which ``HTTPErrorProcessor.http_response`` reads, as
``AbstractHTTPHandler.do_open`` sets it on a real response. Each request is recorded with its method, URL, body and
the headers ``do_open`` sends (``unredirected_hdrs`` merged with ``headers``), their names lower-cased so a lookup is
case-insensitive.

* A static route answers one method, endpoint and decoded query with its replies in order, the last one repeating.
* A list route answers ``GET`` with the ``page``/``per_page`` slice of a canned list, and a ``link`` ``rel="next"``
  while items remain.
* A list failure route answers ``GET`` on a list endpoint with one scripted reply whatever page is asked for, so a
  caller's own paging parameters meet it as they meet a list route.
* A request no route answers fails the test with ``pytest.fail``, which no ``except Exception`` swallows, and stays in
  ``unrouted`` for the teardown check.

A route named by a path is on ``https://api.github.com``; a route anywhere else is named by its absolute URL. An
endpoint is the scheme, the userinfo, the host, the port (the scheme's default when the URL names none) and the path,
so a request carrying userinfo never matches a route without it.

The golden table ``CASES`` (design "Testing Strategy", UB-1.1) holds, for each case, the argv, the host state (the
temporary project's files and the fake host's routes), the exact standard output, the exit code and the requests other
than ``GET`` (method, path, decoded query, JSON body). Every value is the installed fork's own output:
``test/test_github_wrapper_fork_parity.py`` runs every case that is not ``c_only`` against the fork, and
``test_github_wrapper_compat.py`` runs every case against the product's entry script. Both build the project with
``enter_project`` and judge with ``assert_outcome`` and ``assert_log``, so the two compare alike.
"""

from __future__ import annotations

import http.client
import importlib
import importlib.util
import io
import json
import logging
import re
import socket
import sys
import urllib.request
import urllib.response
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "github_api"
API_ORIGIN = "https://api.github.com"
DEFAULT_PORTS = {"http": 80, "https": 443}
DEFAULT_PER_PAGE = 30  # GitHub's page size when a list request names none (conventions.md "Pagination")
FIRST_PAGE = 1
QUERY_PAGE = "page"
QUERY_PER_PAGE = "per_page"
PAGING_PARAMETERS = (QUERY_PAGE, QUERY_PER_PAGE)
HEADER_CONTENT_TYPE = "content-type"
HEADER_LINK = "link"
HEADER_LOCATION = "location"
MEDIA_TYPE_JSON = "application/json; charset=utf-8"
FIELD_TOTAL_COUNT = "total_count"
METHOD_GET = "GET"

Query = Dict[str, List[str]]
QueryValue = Union[str, int, Sequence[Union[str, int]]]


def import_api_module(*, name: str) -> ModuleType:
    """Import ``github_api.<name>`` from the ``scripts`` directory beside this suite.

    While the module file is not written, the calling test fails on this assertion rather than on a collection error;
    a ``github_api`` imported from any other directory fails it too, so a suite never tests another copy.
    """
    path = SCRIPTS_DIR / PACKAGE / f"{name}.py"
    assert path.is_file(), f"{PACKAGE}/{name}.py is not written: {path} does not exist"
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    module = importlib.import_module(name=f"{PACKAGE}.{name}")
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == path.resolve(), f"{PACKAGE}.{name} was imported from {loaded_from}, not from {path}"
    return module


def decode_query(*, query: str) -> Query:
    """A URL query as ``parse_qs`` decodes it, blank values kept: the form routes and recorded requests compare in."""
    return parse_qs(qs=query, keep_blank_values=True)


def query_of(*, values: Optional[Mapping[str, QueryValue]]) -> Query:
    """A query given as a mapping, in ``decode_query``'s form: every value a list of strings."""
    decoded: Query = {}
    for name, value in (values or {}).items():
        items = list(value) if isinstance(value, (list, tuple)) else [value]
        decoded[name] = [str(item) for item in items]
    return decoded


@dataclass(frozen=True)
class Endpoint:
    """Where a request goes: scheme, userinfo, host, port (the scheme's default when the URL names none) and path."""

    scheme: str
    userinfo: str
    host: str
    port: int
    path: str

    @classmethod
    def of(cls, *, url: str) -> Endpoint:
        """The endpoint of an absolute URL; ``ValueError`` when its port is not a number."""
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        userinfo, _, _ = parts.netloc.rpartition("@")
        return cls(
            scheme=scheme,
            userinfo=userinfo,
            host=(parts.hostname or "").lower(),
            port=parts.port or DEFAULT_PORTS.get(scheme, 0),
            path=parts.path or "/",
        )


def _target_of(*, url: str) -> Tuple[Endpoint, Query]:
    """The endpoint and decoded query a route names: a path is on the API host, anything else is an absolute URL."""
    absolute = f"{API_ORIGIN}{url}" if url.startswith("/") else url
    return Endpoint.of(url=absolute), decode_query(query=urlsplit(absolute).query)


def _bytes_of(*, data: Any) -> Optional[bytes]:
    """A request body as bytes: what ``http.client`` sends for bytes, a file object or an iterable of bytes."""
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    if hasattr(data, "read"):
        return bytes(data.read())
    return b"".join(bytes(chunk) for chunk in data)


def _reason_of(*, status: int) -> str:
    """The reason phrase a server sends with ``status``; empty for a status ``http.HTTPStatus`` does not name."""
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return ""


def _last_int(*, query: Query, name: str, default: int) -> int:
    """The last value of the query parameter ``name`` as an integer, ``default`` when it is absent."""
    values = query.get(name)
    return int(values[-1]) if values else default


@dataclass
class RecordedRequest:
    """One request as the fake host received it."""

    method: str
    url: str
    body: Optional[bytes]
    headers: Dict[str, str]

    @classmethod
    def of(cls, *, request: urllib.request.Request) -> RecordedRequest:
        """Record ``request`` with the headers ``AbstractHTTPHandler.do_open`` sends, their names lower-cased."""
        sent = dict(request.unredirected_hdrs)
        sent.update({name: value for name, value in request.headers.items() if name not in sent})
        return cls(
            method=request.get_method(),
            url=request.full_url,
            body=_bytes_of(data=request.data),
            headers={name.lower(): value for name, value in sent.items()},
        )

    @property
    def path(self) -> str:
        """The URL's path, as sent."""
        return urlsplit(self.url).path

    @property
    def query(self) -> Query:
        """The URL's query, decoded."""
        return decode_query(query=urlsplit(self.url).query)

    def header(self, *, name: str) -> Optional[str]:
        """The value sent under ``name``, compared case-insensitively; ``None`` when it was not sent."""
        return self.headers.get(name.lower())

    def json(self) -> Any:
        """The body parsed as JSON; ``None`` when there is none."""
        return json.loads(self.body.decode("utf-8")) if self.body else None


class FakeResponse(urllib.response.addinfourl):
    """A scripted answer: an ``addinfourl`` whose ``msg`` is the reason phrase, as ``do_open`` sets it, and which also
    answers ``reason``, ``getheader`` and ``getheaders`` as ``http.client.HTTPResponse`` does."""

    def __init__(self, *, body: bytes, headers: http.client.HTTPMessage, url: str, status: int) -> None:
        super().__init__(fp=io.BytesIO(body), headers=headers, url=url, code=status)
        self.reason = _reason_of(status=status)
        self.msg = self.reason

    def getheader(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Every value sent under ``name``, joined as ``HTTPResponse.getheader`` joins them; ``default`` if none."""
        values = self.headers.get_all(name)
        return ", ".join(values) if values else default

    def getheaders(self) -> List[Tuple[str, str]]:
        """Every header as a ``(name, value)`` pair, in the order sent."""
        return list(self.headers.items())


@dataclass
class Reply:
    """One scripted response: its status, its headers and its body. A ``bytes`` body is sent as given; any other value
    but ``None`` is sent as JSON with a JSON ``content-type`` unless ``headers`` names one; ``None`` sends no body."""

    status: int = 200
    body: Any = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def _is_json(self) -> bool:
        return self.body is not None and not isinstance(self.body, (bytes, bytearray))

    def encoded(self) -> bytes:
        """The body's bytes on the wire."""
        if self.body is None:
            return b""
        if isinstance(self.body, (bytes, bytearray)):
            return bytes(self.body)
        return json.dumps(self.body).encode("utf-8")

    def response(self, *, url: str) -> FakeResponse:
        """This reply as the answer to a request for ``url``."""
        message = http.client.HTTPMessage()
        named = {name.lower() for name in self.headers}
        if self._is_json() and HEADER_CONTENT_TYPE not in named:
            message[HEADER_CONTENT_TYPE] = MEDIA_TYPE_JSON
        for name, value in self.headers.items():
            message[name] = value
        return FakeResponse(body=self.encoded(), headers=message, url=url, status=self.status)


def redirect(*, status: int, location: str) -> Reply:
    """A redirect to ``location``, in the ``location`` header urllib's ``HTTPRedirectHandler`` reads."""
    return Reply(status=status, headers={HEADER_LOCATION: location})


@dataclass
class Route:
    """A static route: one method, endpoint and decoded query, answered with ``replies`` in order, the last repeated."""

    method: str
    endpoint: Endpoint
    query: Query
    replies: List[Reply]
    served: int = 0

    def matches(self, *, request: RecordedRequest, endpoint: Endpoint) -> bool:
        """Whether this route answers ``request``, sent to ``endpoint``."""
        return request.method == self.method and endpoint == self.endpoint and request.query == self.query

    def reply_to(self, *, request: RecordedRequest) -> Reply:
        """The next reply in order; the last one again once all have been served."""
        del request  # a static route answers every request it matches alike, in turn
        reply = self.replies[min(self.served, len(self.replies) - 1)]
        self.served += 1
        return reply


@dataclass
class ListRoute:
    """A list route: ``GET`` on one endpoint and decoded query (``page`` and ``per_page`` aside), answered with that
    page's slice of ``items`` (inside ``{"total_count": ..., <item_key>: [...]}`` when ``item_key`` is given) and a
    ``link`` ``rel="next"`` to the following page while items remain."""

    endpoint: Endpoint
    query: Query
    items: List[Any]
    item_key: Optional[str] = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def matches(self, *, request: RecordedRequest, endpoint: Endpoint) -> bool:
        """Whether this route answers ``request``, sent to ``endpoint``: its query apart from the paging parameters."""
        fixed = {name: values for name, values in request.query.items() if name not in PAGING_PARAMETERS}
        return request.method == METHOD_GET and endpoint == self.endpoint and fixed == self.query

    def reply_to(self, *, request: RecordedRequest) -> Reply:
        """The page ``request`` asks for, with a ``link`` to the next page while items remain."""
        page = max(_last_int(query=request.query, name=QUERY_PAGE, default=FIRST_PAGE), FIRST_PAGE)
        per_page = _last_int(query=request.query, name=QUERY_PER_PAGE, default=DEFAULT_PER_PAGE)
        start = (page - 1) * per_page
        chunk = self.items[start : start + per_page]
        headers = dict(self.headers)
        if start + per_page < len(self.items):
            next_url = self._page_url(request=request, page=page + 1, per_page=per_page)
            headers[HEADER_LINK] = f'<{next_url}>; rel="next"'
        body: Any = chunk if self.item_key is None else {FIELD_TOTAL_COUNT: len(self.items), self.item_key: chunk}
        return Reply(body=body, headers=headers)

    def _page_url(self, *, request: RecordedRequest, page: int, per_page: int) -> str:
        parts = urlsplit(request.url)
        pairs = [(name, value) for name, values in self.query.items() for value in values]
        pairs.extend([(QUERY_PER_PAGE, str(per_page)), (QUERY_PAGE, str(page))])
        return f"{parts.scheme}://{parts.netloc}{parts.path}?{urlencode(query=pairs)}"


@dataclass
class ListFailureRoute(ListRoute):
    """A list route whose every page fails: ``GET`` on one endpoint and decoded query (``page`` and ``per_page``
    aside), answered with ``failure`` whichever page is asked for."""

    failure: Reply = field(default_factory=Reply)

    def reply_to(self, *, request: RecordedRequest) -> Reply:
        """``failure``, for every page."""
        del request  # every page of a failing list fails alike
        return self.failure


class FakeGitHub:
    """The fake host: scripted routes, each request recorded in ``requests``, an unanswered one also in ``unrouted``."""

    def __init__(self) -> None:
        self.requests: List[RecordedRequest] = []
        self.unrouted: List[RecordedRequest] = []
        self._routes: List[Union[Route, ListRoute]] = []

    def route(
        self,
        *,
        method: str,
        url: str,
        replies: Sequence[Reply],
        query: Optional[Mapping[str, QueryValue]] = None,
    ) -> None:
        """Answer ``method`` on ``url`` (a path on the API host, or an absolute URL) with ``replies`` in order, the last
        repeating. The decoded query a request must carry is the URL's own, updated with ``query``."""
        assert replies, f"the route {method} {url} needs at least one reply"
        endpoint, decoded = _target_of(url=url)
        decoded.update(query_of(values=query))
        self._routes.append(Route(method=method.upper(), endpoint=endpoint, query=decoded, replies=list(replies)))

    def list_route(
        self,
        *,
        url: str,
        items: Sequence[Any],
        query: Optional[Mapping[str, QueryValue]] = None,
        item_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Serve ``items`` as a paged list on ``url`` (a path on the API host, or an absolute URL) for every request
        whose query, apart from ``page`` and ``per_page``, is the URL's own updated with ``query``."""
        endpoint, decoded = _target_of(url=url)
        decoded.update(query_of(values=query))
        self._routes.append(
            ListRoute(
                endpoint=endpoint, query=decoded, items=list(items), item_key=item_key, headers=dict(headers or {})
            )
        )

    def list_failure(self, *, url: str, failure: Reply, query: Optional[Mapping[str, QueryValue]] = None) -> None:
        """Answer every ``GET`` on ``url`` (a path on the API host, or an absolute URL) whose query, apart from ``page``
        and ``per_page``, is the URL's own updated with ``query``, with ``failure``: a list that fails on any page."""
        endpoint, decoded = _target_of(url=url)
        decoded.update(query_of(values=query))
        self._routes.append(ListFailureRoute(endpoint=endpoint, query=decoded, items=[], failure=failure))

    def install(self, *, monkeypatch: pytest.MonkeyPatch) -> None:
        """Answer every ``http`` and ``https`` request any urllib opener in this process sends, until the test ends."""

        def open_on_the_fake(handler: urllib.request.BaseHandler, req: urllib.request.Request) -> FakeResponse:
            del handler  # every opener's HTTP and HTTPS handler reaches the one fake host
            return self.answer(request=req)

        monkeypatch.setattr(target=urllib.request.HTTPSHandler, name="https_open", value=open_on_the_fake)
        monkeypatch.setattr(target=urllib.request.HTTPHandler, name="http_open", value=open_on_the_fake)

    def answer(self, *, request: urllib.request.Request) -> FakeResponse:
        """Record ``request`` and answer it from the first route that matches; fail the test when none does."""
        recorded = RecordedRequest.of(request=request)
        self.requests.append(recorded)
        route = self._route_for(request=recorded)
        if route is None:
            self.unrouted.append(recorded)
            pytest.fail(reason=f"the fake GitHub host has no route for {recorded.method} {recorded.url}", pytrace=False)
        return route.reply_to(request=recorded).response(url=recorded.url)

    def urls(self) -> List[str]:
        """The URL of every request received, in order."""
        return [request.url for request in self.requests]

    def assert_every_request_routed(self) -> None:
        """Fail when any request reached the host without a route, whatever the code under test did with the failure."""
        unrouted = [f"{request.method} {request.url}" for request in self.unrouted]
        assert not unrouted, f"the fake GitHub host received requests no route answers: {unrouted}"

    def _route_for(self, *, request: RecordedRequest) -> Optional[Union[Route, ListRoute]]:
        try:
            endpoint = Endpoint.of(url=request.url)
        except ValueError:
            return None
        for route in self._routes:
            if route.matches(request=request, endpoint=endpoint):
                return route
        return None


# ---------------------------------------------------------------------------------------------------------------------
# The golden case table (design "Testing Strategy"; UB-1.1)
# ---------------------------------------------------------------------------------------------------------------------

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_REFUSED = 2  # a usage error, a credential refusal or a repository refusal
EXIT_OF_A_MESSAGE = 1  # what the interpreter exits with when ``sys.exit`` is handed a message

METHOD_POST = "POST"
METHOD_PATCH = "PATCH"
HEADER_AUTHORIZATION = "authorization"
QUERY_STATE = "state"
QUERY_LABELS = "labels"
QUERY_ASSIGNEE = "assignee"

FIELD_NUMBER = "number"
FIELD_TITLE = "title"
FIELD_STATE = "state"
FIELD_BODY = "body"
FIELD_LABELS = "labels"
FIELD_NAME = "name"
FIELD_ID = "id"
FIELD_USER = "user"
FIELD_LOGIN = "login"
FIELD_URL = "url"
FIELD_HTML_URL = "html_url"
FIELD_PULL_REQUEST = "pull_request"
FIELD_MESSAGE = "message"
FIELD_DOCUMENTATION_URL = "documentation_url"
FIELD_STATUS = "status"
FIELD_ERRORS = "errors"
FIELD_RESOURCE = "resource"
FIELD_CODE = "code"
FIELD_FIELD = "field"

STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_ALL = "all"
LABEL_IN_PROGRESS = "in-progress"
ANY_ASSIGNEE = "*"
USER_LOGIN = "octocat"

OWNER = "o"
REPOSITORY = "r"
WEB_ORIGIN = "https://github.com"
ISSUES_PATH = f"/repos/{OWNER}/{REPOSITORY}/issues"
DOCUMENTATION_URL = "https://docs.github.com/rest"

CREDENTIALS_FILE = Path("credentials") / "github-pat.txt"
GIT_CONFIG_FILE = Path(".git") / "config"
FIXTURE_TOKEN = "ghp_TFixtureCredential"  # pragma: allowlist secret
PLACEHOLDER_TOKEN = "PASTE_YOUR_GITHUB_PAT_HERE"
TWO_TOKENS = "ghp_TFirstToken\nghp_TSecondToken\n"  # pragma: allowlist secret

ORIGIN_HTTPS = f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}.git"
ORIGIN_SSH = f"git@github.com:{OWNER}/{REPOSITORY}.git"
ORIGIN_FOREIGN = f"https://gitlab.com/{OWNER}/{REPOSITORY}.git"
#: A GitHub ``origin`` the fork's ``_detect_repo`` pattern does not parse, since its repository name holds a ``.``; the
#: userinfo cases put a token, and a user and password, in front of it (design UB-1.1).
ORIGIN_UNPARSEABLE = "https://github.com/o/socket.io.git"
ORIGIN_UNPARSEABLE_WITHOUT_SCHEME = "github.com/o/socket.io.git"
USERINFO_TOKEN = "ghp_T"  # pragma: allowlist secret
USERINFO_PASSWORD = "secret"  # pragma: allowlist secret
ORIGIN_USERINFO_TOKEN = "https://ghp_T@github.com/o/socket.io.git"  # pragma: allowlist secret
ORIGIN_USERINFO_PASSWORD = "https://user:secret@github.com/o/socket.io.git"  # pragma: allowlist secret
#: The ``.git/config`` file named in a refusal, in either separator: ``.git/config`` or this platform's spelling.
GIT_CONFIG_NAMED = r"\.git[/\\]config"

#: The delivery verbs (UB-1.2): their golden behaviour is the steward's, so the fork parity test runs no case of theirs.
DELIVERY_SUBCOMMANDS = frozenset(
    {"enqueue-pr", "dequeue-pr", "queue-status", "wait-landed", "check-handoff", "check-landed"}
)


def git_config(*, origin: Optional[str]) -> str:
    """A ``.git/config`` as ``git init`` and ``git remote add origin <origin>`` write it; without ``origin``, none."""
    lines = ["[core]", "\trepositoryformatversion = 0", "\tbare = false"]
    if origin is not None:
        lines.extend(['[remote "origin"]', f"\turl = {origin}", "\tfetch = +refs/heads/*:refs/remotes/origin/*"])
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Project:
    """The temporary project a case runs in: the text of ``credentials/github-pat.txt`` and of ``.git/config``
    (``None``: the file is absent) and further files, each a path relative to the project root and its text."""

    credential: Optional[str] = f"{FIXTURE_TOKEN}\n"
    config: Optional[str] = git_config(origin=ORIGIN_HTTPS)
    files: Tuple[Tuple[str, str], ...] = ()

    def build(self, *, root: Path) -> None:
        """Write the project's files under ``root`` as UTF-8 bytes, so no newline is translated."""
        written = [(Path(name), text) for name, text in self.files]
        if self.credential is not None:
            written.append((CREDENTIALS_FILE, self.credential))
        if self.config is not None:
            written.append((GIT_CONFIG_FILE, self.config))
        for name, text in written:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode(encoding="utf-8"))


class RouteSpec(ABC):
    """One route of a case's host state; ``install`` adds it to the fresh fake host of each run."""

    @abstractmethod
    def install(self, *, host: FakeGitHub) -> None:
        """Add this route to ``host``."""


@dataclass(frozen=True)
class StaticRouteSpec(RouteSpec):
    """``FakeGitHub.route``'s arguments: one method on one URL, answered with ``replies`` in turn, the last repeated."""

    method: str
    url: str
    replies: Tuple[Reply, ...]
    query: Mapping[str, QueryValue] = field(default_factory=dict)

    def install(self, *, host: FakeGitHub) -> None:
        """Add the static route to ``host``."""
        host.route(method=self.method, url=self.url, replies=self.replies, query=self.query)


@dataclass(frozen=True)
class ListRouteSpec(RouteSpec):
    """``FakeGitHub.list_route``'s arguments: ``items`` served as ``page``/``per_page`` slices with a ``link``."""

    url: str
    items: Tuple[Any, ...]
    query: Mapping[str, QueryValue] = field(default_factory=dict)

    def install(self, *, host: FakeGitHub) -> None:
        """Add the list route to ``host``."""
        host.list_route(url=self.url, items=self.items, query=self.query)


@dataclass(frozen=True)
class ListFailureRouteSpec(RouteSpec):
    """``FakeGitHub.list_failure``'s arguments: every page of a list answered with ``failure``."""

    url: str
    failure: Reply
    query: Mapping[str, QueryValue] = field(default_factory=dict)

    def install(self, *, host: FakeGitHub) -> None:
        """Add the list failure route to ``host``."""
        host.list_failure(url=self.url, failure=self.failure, query=self.query)


@dataclass(frozen=True)
class NonGetRequest:
    """A request other than ``GET`` as the golden comparison sees it: method, path as sent, decoded query, JSON body."""

    method: str
    path: str
    body: Any = None
    query: Query = field(default_factory=dict)

    @classmethod
    def of(cls, *, request: RecordedRequest) -> NonGetRequest:
        """``request`` in the comparison's form."""
        return cls(method=request.method, path=request.path, body=request.json(), query=request.query)


@dataclass(frozen=True)
class LogExpectation:
    """What a case's log records hold: one record matching every pattern of ``refusal``, and none of ``withheld`` in
    any record, nor on standard error."""

    refusal: Tuple[str, ...]
    withheld: Tuple[str, ...]


@dataclass(frozen=True)
class GoldenCase:
    """One row of ``CASES``: run ``argv`` in ``project`` against a fake host holding ``routes``; standard output is
    ``stdout`` exactly, the exit code ``exit_code`` and the requests other than ``GET`` ``writes``, in order. A
    ``c_only`` case is a deviation from the fork that UB-1.1 makes on purpose, so only the product runs it; ``log``,
    when set, is what its log records must and must not hold."""

    name: str
    argv: Tuple[str, ...]
    stdout: str
    exit_code: int
    project: Project = field(default_factory=Project)
    routes: Tuple[RouteSpec, ...] = ()
    writes: Tuple[NonGetRequest, ...] = ()
    c_only: bool = False
    log: Optional[LogExpectation] = None


def case_name(case: GoldenCase) -> str:
    """The test id of ``case``."""
    return case.name


def issue_entry(
    *,
    number: int,
    title: str,
    state: str = STATE_OPEN,
    body: Optional[str] = None,
    labels: Sequence[str] = (),
    pull_request: bool = False,
) -> Dict[str, Any]:
    """An issue as the issues endpoints return it, cut to the fields the commands read; with ``pull_request``, an entry
    of the issue list that is a pull request."""
    entry: Dict[str, Any] = {
        FIELD_NUMBER: number,
        FIELD_TITLE: title,
        FIELD_STATE: state,
        FIELD_BODY: body,
        FIELD_LABELS: [{FIELD_NAME: name} for name in labels],
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/issues/{number}",
    }
    if pull_request:
        entry[FIELD_PULL_REQUEST] = {FIELD_URL: f"{API_ORIGIN}/repos/{OWNER}/{REPOSITORY}/pulls/{number}"}
    return entry


def comment_entry(*, comment_id: int, issue_number: int, body: str) -> Dict[str, Any]:
    """An issue comment as the comments endpoints return it, cut to a few fields."""
    return {
        FIELD_ID: comment_id,
        FIELD_BODY: body,
        FIELD_USER: {FIELD_LOGIN: USER_LOGIN},
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/issues/{issue_number}#issuecomment-{comment_id}",
    }


def printed_json(*, value: Any) -> str:
    """What ``print(json.dumps(value, indent=2))`` writes: how the fork echoes a response."""
    return json.dumps(value, indent=2) + "\n"


def listed_issues(*, entries: Sequence[Mapping[str, Any]], limit: int) -> str:
    """The fork's ``list-issues`` lines for ``entries``: pull requests left out, at most ``limit`` lines."""
    issues = [entry for entry in entries if FIELD_PULL_REQUEST not in entry][:limit]
    return "".join(f"#{entry[FIELD_NUMBER]:<6} {entry[FIELD_STATE]:<8} {entry[FIELD_TITLE]}\n" for entry in issues)


NOT_FOUND = Reply(
    status=404, body={FIELD_MESSAGE: "Not Found", FIELD_DOCUMENTATION_URL: DOCUMENTATION_URL, FIELD_STATUS: "404"}
)
VALIDATION_FAILED = Reply(
    status=422,
    body={
        FIELD_MESSAGE: "Validation Failed",
        FIELD_ERRORS: [{FIELD_RESOURCE: "Issue", FIELD_CODE: "invalid", FIELD_FIELD: FIELD_TITLE}],
        FIELD_DOCUMENTATION_URL: DOCUMENTATION_URL,
        FIELD_STATUS: "422",
    },
)
CREATED = 201

PROJECT = Project()
NO_CREDENTIAL = Project(credential=None)
PLACEHOLDER_CREDENTIAL = Project(credential=f"{PLACEHOLDER_TOKEN}\n")
TWO_TOKEN_CREDENTIAL = Project(credential=TWO_TOKENS)
EMPTY_CREDENTIAL = Project(credential="")
NO_GIT_CONFIG = Project(config=None)
NO_ORIGIN = Project(config=git_config(origin=None))
FOREIGN_ORIGIN = Project(config=git_config(origin=ORIGIN_FOREIGN))
UNPARSEABLE_ORIGIN = Project(config=git_config(origin=ORIGIN_UNPARSEABLE))
USERINFO_REFUSAL = LogExpectation(
    refusal=(GIT_CONFIG_NAMED, re.escape(ORIGIN_UNPARSEABLE_WITHOUT_SCHEME)),
    withheld=(USERINFO_TOKEN, USERINFO_PASSWORD),
)


def _refusal_cases(
    *, command: str, argv: Tuple[str, ...], usage: Tuple[str, ...], credential: Project, repository: Project
) -> Tuple[GoldenCase, ...]:
    """Exit 2, nothing on standard output and no request: the usage error ``usage``, then ``argv`` refused for its
    credential and for its repository."""
    return (
        GoldenCase(name=f"{command}/exit-2/usage-error", argv=usage, stdout="", exit_code=EXIT_REFUSED),
        GoldenCase(
            name=f"{command}/exit-2/credential-refused",
            argv=argv,
            stdout="",
            exit_code=EXIT_REFUSED,
            project=credential,
        ),
        GoldenCase(
            name=f"{command}/exit-2/repository-refused",
            argv=argv,
            stdout="",
            exit_code=EXIT_REFUSED,
            project=repository,
        ),
    )


LISTED_ENTRIES = (
    issue_entry(number=7, title="Fix the parser"),
    issue_entry(number=8, title="Bump the toolchain", pull_request=True),
    issue_entry(number=12, title="Render the □ glyph", labels=("ui",)),
    issue_entry(number=31, title="Document the wrapper"),
)
CLAIMED_ENTRIES = (
    issue_entry(number=41, title="Claimed work", labels=(LABEL_IN_PROGRESS,)),
    issue_entry(number=42, title="Claimed pull request", labels=(LABEL_IN_PROGRESS,), pull_request=True),
    issue_entry(number=1043, title="Another claim", labels=(LABEL_IN_PROGRESS,)),
)
BACKLOG_SIZE = 160  # more than one page of the fork's 100, so the list crosses a page boundary
BACKLOG_PULL_REQUEST_EVERY = 10
BACKLOG_CLOSED_EVERY = 3
BACKLOG_LIMIT = 100  # reached on the second page, part-way through it
BACKLOG_ENTRIES = tuple(
    issue_entry(
        number=number,
        title=f"Backlog item {number}",
        state=STATE_CLOSED if number % BACKLOG_CLOSED_EVERY == 0 else STATE_OPEN,
        pull_request=number % BACKLOG_PULL_REQUEST_EVERY == 0,
    )
    for number in range(1, BACKLOG_SIZE + 1)
)


def _list_issues_cases() -> Tuple[GoldenCase, ...]:
    command = "list-issues"
    return (
        GoldenCase(
            name=f"{command}/exit-0/open-issues-without-pull-requests",
            argv=(command,),
            stdout=(
                "#7      open     Fix the parser\n#12     open     Render the □ glyph\n"
                "#31     open     Document the wrapper\n"
            ),
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=ISSUES_PATH, items=LISTED_ENTRIES, query={QUERY_STATE: STATE_OPEN}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/limit-reached-on-the-second-page",
            argv=(command, "--state", STATE_ALL, "--limit", str(BACKLOG_LIMIT)),
            stdout=listed_issues(entries=BACKLOG_ENTRIES, limit=BACKLOG_LIMIT),
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=ISSUES_PATH, items=BACKLOG_ENTRIES, query={QUERY_STATE: STATE_ALL}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/label-abbreviation-and-any-assignee",
            argv=(command, "--state", STATE_OPEN, "--assignee", ANY_ASSIGNEE, "--label", LABEL_IN_PROGRESS),
            stdout="#41     open     Claimed work\n#1043   open     Another claim\n",
            exit_code=EXIT_OK,
            routes=(
                ListRouteSpec(
                    url=ISSUES_PATH,
                    items=CLAIMED_ENTRIES,
                    query={QUERY_STATE: STATE_OPEN, QUERY_LABELS: LABEL_IN_PROGRESS, QUERY_ASSIGNEE: ANY_ASSIGNEE},
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command,),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(ListFailureRouteSpec(url=ISSUES_PATH, failure=NOT_FOUND, query={QUERY_STATE: STATE_OPEN}),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command,),
            usage=(command, "--state", "bogus"),
            credential=NO_CREDENTIAL,
            repository=NO_GIT_CONFIG,
        ),
        GoldenCase(
            name=f"{command}/exit-2/token-stdin-not-carried",
            argv=(command, "--token-stdin"),
            stdout="",
            exit_code=EXIT_REFUSED,
            c_only=True,
        ),
    )


ISSUE_5 = issue_entry(number=5, title="Wrapper rewrite", body="- [ ] transport\n- [x] design", labels=("enhancement",))


def _get_issue_cases() -> Tuple[GoldenCase, ...]:
    command = "get-issue"
    found = StaticRouteSpec(method=METHOD_GET, url=f"{ISSUES_PATH}/5", replies=(Reply(body=ISSUE_5),))
    return (
        GoldenCase(
            name=f"{command}/exit-0/https-origin",
            argv=(command, "5"),
            stdout=printed_json(value=ISSUE_5),
            exit_code=EXIT_OK,
            routes=(found,),
        ),
        GoldenCase(
            name=f"{command}/exit-0/ssh-origin",
            argv=(command, "5"),
            stdout=printed_json(value=ISSUE_5),
            exit_code=EXIT_OK,
            project=Project(config=git_config(origin=ORIGIN_SSH)),
            routes=(found,),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "6"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=f"{ISSUES_PATH}/6", replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5"),
            usage=(command, "five"),
            credential=PLACEHOLDER_CREDENTIAL,
            repository=FOREIGN_ORIGIN,
        ),
        GoldenCase(
            name=f"{command}/exit-2/origin-userinfo-token-not-logged",
            argv=(command, "1"),
            stdout="",
            exit_code=EXIT_REFUSED,
            project=Project(config=git_config(origin=ORIGIN_USERINFO_TOKEN)),
            c_only=True,
            log=USERINFO_REFUSAL,
        ),
        GoldenCase(
            name=f"{command}/exit-2/origin-userinfo-password-not-logged",
            argv=(command, "1"),
            stdout="",
            exit_code=EXIT_REFUSED,
            project=Project(config=git_config(origin=ORIGIN_USERINFO_PASSWORD)),
            c_only=True,
            log=USERINFO_REFUSAL,
        ),
    )


COMMENT_ID_BASE = 9000
COMMENTS_ON_5 = tuple(
    comment_entry(comment_id=COMMENT_ID_BASE + number, issue_number=5, body=f"Progress note {number}")
    for number in range(1, 102)  # one past the fork's full page of 100
)


def _get_issue_comments_cases() -> Tuple[GoldenCase, ...]:
    command = "get-issue-comments"
    return (
        GoldenCase(
            name=f"{command}/exit-0/every-page",
            argv=(command, "5"),
            stdout=printed_json(value=list(COMMENTS_ON_5)),
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=f"{ISSUES_PATH}/5/comments", items=COMMENTS_ON_5),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/no-comments",
            argv=(command, "6"),
            stdout="[]\n",
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=f"{ISSUES_PATH}/6/comments", items=()),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "7"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(ListFailureRouteSpec(url=f"{ISSUES_PATH}/7/comments", failure=NOT_FOUND),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5"),
            usage=(command,),
            credential=TWO_TOKEN_CREDENTIAL,
            repository=NO_ORIGIN,
        ),
    )


COMMENT_TEXT = "Implemented: `wait-run` exits 11 on a timeout."
NOTES_FILE = "notes.md"
NOTES_TEXT = "## Evidence\n\n```\n$ python scripts/run_tests.py\n47 passed\n```\n\nSee `wait-run` – exit 11.\n"
COMMENT_POSTED = comment_entry(comment_id=9201, issue_number=5, body=COMMENT_TEXT)
NOTES_POSTED = comment_entry(comment_id=9202, issue_number=5, body=NOTES_TEXT)
WITH_NOTES = Project(files=((NOTES_FILE, NOTES_TEXT),))


def _comment_issue_cases() -> Tuple[GoldenCase, ...]:
    command = "comment-issue"
    comments_of_5 = f"{ISSUES_PATH}/5/comments"
    comments_of_6 = f"{ISSUES_PATH}/6/comments"
    return (
        GoldenCase(
            name=f"{command}/exit-0/body",
            argv=(command, "5", "--body", COMMENT_TEXT),
            stdout=printed_json(value=COMMENT_POSTED),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST, url=comments_of_5, replies=(Reply(status=CREATED, body=COMMENT_POSTED),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_POST, path=comments_of_5, body={FIELD_BODY: COMMENT_TEXT}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/body-file",
            argv=(command, "5", "--body-file", NOTES_FILE),
            stdout=printed_json(value=NOTES_POSTED),
            exit_code=EXIT_OK,
            project=WITH_NOTES,
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST, url=comments_of_5, replies=(Reply(status=CREATED, body=NOTES_POSTED),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_POST, path=comments_of_5, body={FIELD_BODY: NOTES_TEXT}),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "6", "--body", COMMENT_TEXT),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=comments_of_6, replies=(NOT_FOUND,)),),
            writes=(NonGetRequest(method=METHOD_POST, path=comments_of_6, body={FIELD_BODY: COMMENT_TEXT}),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/no-body",
            argv=(command, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
        ),
        GoldenCase(
            name=f"{command}/exit-1/body-and-body-file",
            argv=(command, "5", "--body", COMMENT_TEXT, "--body-file", NOTES_FILE),
            stdout="",
            exit_code=EXIT_API_ERROR,
            project=WITH_NOTES,
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5", "--body", COMMENT_TEXT),
            usage=(command,),
            credential=EMPTY_CREDENTIAL,
            repository=UNPARSEABLE_ORIGIN,
        ),
    )


BODY_FILE = "body.md"
BODY_TEXT = "## Problem\n\n`update-issue --labels` replaces the whole set.\n"
CREATED_WITH_LABELS = issue_entry(number=44, title="Wrapper drops labels", body="Seen on #12.", labels=("bug", "ui"))
CREATED_FROM_FILE = issue_entry(number=45, title="Labels are replaced", body=BODY_TEXT)
CREATED_TITLE_ONLY = issue_entry(number=46, title="Title only")


def _create_issue_cases() -> Tuple[GoldenCase, ...]:
    command = "create-issue"
    refused = (command, "--title", "Refused")
    return (
        GoldenCase(
            name=f"{command}/exit-0/title-body-labels",
            argv=(command, "--title", "Wrapper drops labels", "--body", "Seen on #12.", "--labels", "bug, ui,"),
            stdout=printed_json(value=CREATED_WITH_LABELS),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST, url=ISSUES_PATH, replies=(Reply(status=CREATED, body=CREATED_WITH_LABELS),)
                ),
            ),
            writes=(
                NonGetRequest(
                    method=METHOD_POST,
                    path=ISSUES_PATH,
                    body={FIELD_TITLE: "Wrapper drops labels", FIELD_BODY: "Seen on #12.", FIELD_LABELS: ["bug", "ui"]},
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/body-file",
            argv=(command, "--title", "Labels are replaced", "--body-file", BODY_FILE),
            stdout=printed_json(value=CREATED_FROM_FILE),
            exit_code=EXIT_OK,
            project=Project(files=((BODY_FILE, BODY_TEXT),)),
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST, url=ISSUES_PATH, replies=(Reply(status=CREATED, body=CREATED_FROM_FILE),)
                ),
            ),
            writes=(
                NonGetRequest(
                    method=METHOD_POST,
                    path=ISSUES_PATH,
                    body={FIELD_TITLE: "Labels are replaced", FIELD_BODY: BODY_TEXT},
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/empty-body-left-out",
            argv=(command, "--title", "Title only", "--body", ""),
            stdout=printed_json(value=CREATED_TITLE_ONLY),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST, url=ISSUES_PATH, replies=(Reply(status=CREATED, body=CREATED_TITLE_ONLY),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_POST, path=ISSUES_PATH, body={FIELD_TITLE: "Title only"}),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/validation-failed",
            argv=(command, "--title", "Rejected"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=ISSUES_PATH, replies=(VALIDATION_FAILED,)),),
            writes=(NonGetRequest(method=METHOD_POST, path=ISSUES_PATH, body={FIELD_TITLE: "Rejected"}),),
        ),
        *_refusal_cases(
            command=command,
            argv=refused,
            usage=(command, "--body", "A body without a title"),
            credential=NO_CREDENTIAL,
            repository=NO_GIT_CONFIG,
        ),
        GoldenCase(
            name=f"{command}/exit-2/token-stdin-not-carried",
            argv=(*refused, "--token-stdin"),
            stdout="",
            exit_code=EXIT_REFUSED,
            c_only=True,
        ),
    )


OPEN_5 = issue_entry(number=5, title="Wrapper rewrite")
CLOSED_5 = issue_entry(number=5, title="Wrapper rewrite", state=STATE_CLOSED)
NEW_BODY_FILE = "new-body.md"
NEW_BODY_TEXT = "Rewritten body.\n\n- [x] transport\n"
UPDATED_5 = issue_entry(number=5, title="Wrapper rewrite, part 1", body=NEW_BODY_TEXT, labels=("a", "b"))


def _update_issue_cases() -> Tuple[GoldenCase, ...]:
    command = "update-issue"
    issue_5 = f"{ISSUES_PATH}/5"
    issue_6 = f"{ISSUES_PATH}/6"
    return (
        GoldenCase(
            name=f"{command}/exit-0/close",
            argv=(command, "5", "--state", STATE_CLOSED),
            stdout=printed_json(value=CLOSED_5),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(Reply(body=CLOSED_5),)),),
            writes=(NonGetRequest(method=METHOD_PATCH, path=issue_5, body={FIELD_STATE: STATE_CLOSED}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/title-body-file-labels",
            argv=(command, "5", "--title", "Wrapper rewrite, part 1", "--body-file", NEW_BODY_FILE, "--labels", "a, b"),
            stdout=printed_json(value=UPDATED_5),
            exit_code=EXIT_OK,
            project=Project(files=((NEW_BODY_FILE, NEW_BODY_TEXT),)),
            routes=(StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(Reply(body=UPDATED_5),)),),
            writes=(
                NonGetRequest(
                    method=METHOD_PATCH,
                    path=issue_5,
                    body={FIELD_TITLE: "Wrapper rewrite, part 1", FIELD_BODY: NEW_BODY_TEXT, FIELD_LABELS: ["a", "b"]},
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/nothing-to-update",
            argv=(command, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "6", "--state", STATE_CLOSED),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_PATCH, url=issue_6, replies=(NOT_FOUND,)),),
            writes=(NonGetRequest(method=METHOD_PATCH, path=issue_6, body={FIELD_STATE: STATE_CLOSED}),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5", "--state", STATE_CLOSED),
            usage=(command, "5", "--state", "reopened"),
            credential=PLACEHOLDER_CREDENTIAL,
            repository=FOREIGN_ORIGIN,
        ),
    )


def _reopen_issue_cases() -> Tuple[GoldenCase, ...]:
    command = "reopen-issue"
    issue_5 = f"{ISSUES_PATH}/5"
    reopen = NonGetRequest(method=METHOD_PATCH, path=issue_5, body={FIELD_STATE: STATE_OPEN})
    return (
        GoldenCase(
            name=f"{command}/exit-0/already-open-not-written",
            argv=(command, "5"),
            stdout='{"issue": 5, "state": "open", "changed": false}\n',
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(Reply(body=OPEN_5),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/reopened-and-verified",
            argv=(command, "5"),
            stdout='{"issue": 5, "state": "open", "changed": true}\n',
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(Reply(body=CLOSED_5), Reply(body=OPEN_5))),
                StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(Reply(body=OPEN_5),)),
            ),
            writes=(reopen,),
        ),
        GoldenCase(
            name=f"{command}/exit-1/still-closed-on-re-read",
            argv=(command, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(Reply(body=CLOSED_5),)),
                StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(Reply(body=CLOSED_5),)),
            ),
            writes=(reopen,),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "6"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=f"{ISSUES_PATH}/6", replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5"),
            usage=(command, "x"),
            credential=TWO_TOKEN_CREDENTIAL,
            repository=NO_ORIGIN,
        ),
    )


CHECKLIST_BEFORE = "Intro\n- [ ] wire the parser\n- [x] write tests\n* [ ] docs\n"
CHECKLIST_TICKED = "Intro\n- [x] wire the parser\n- [x] write tests\n* [ ] docs\n"
CHECKLIST_CRLF_BEFORE = "- [x] write tests\r\n- [ ] docs\r\n"
CHECKLIST_CRLF_UNTICKED = "- [ ] write tests\r\n- [ ] docs\r\n"


def _checklist_body(*, number: int, body: Optional[str]) -> Reply:
    """The issue ``number`` with ``body``, as the issue read answers it."""
    return Reply(body=issue_entry(number=number, title="Wrapper rewrite", body=body))


def _checklist_cases() -> Tuple[GoldenCase, ...]:
    command = "checklist"
    issue_5 = f"{ISSUES_PATH}/5"
    issue_9 = f"{ISSUES_PATH}/9"
    tick = NonGetRequest(method=METHOD_PATCH, path=issue_5, body={FIELD_BODY: CHECKLIST_TICKED})
    before = _checklist_body(number=5, body=CHECKLIST_BEFORE)
    ticked = _checklist_body(number=5, body=CHECKLIST_TICKED)
    return (
        GoldenCase(
            name=f"{command}/exit-0/count",
            argv=(command, "5"),
            stdout='{"issue": 5, "ticked": 1, "total": 3, "unticked": ["wire the parser", "docs"]}\n',
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(before,)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/count-of-no-body",
            argv=(command, "6"),
            stdout='{"issue": 6, "ticked": 0, "total": 0, "unticked": []}\n',
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_GET, url=f"{ISSUES_PATH}/6", replies=(_checklist_body(number=6, body=None),)
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/tick-verified",
            argv=(command, "5", "--tick", "wire"),
            stdout='{"issue": 5, "item": "wire", "ticked": 2, "total": 3, "unticked": ["docs"]}\n',
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(before, ticked)),
                StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(ticked,)),
            ),
            writes=(tick,),
        ),
        GoldenCase(
            name=f"{command}/exit-0/untick-keeps-crlf",
            argv=(command, "9", "--untick", "tests"),
            stdout='{"issue": 9, "item": "tests", "ticked": 0, "total": 2, "unticked": ["write tests", "docs"]}\n',
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_GET,
                    url=issue_9,
                    replies=(
                        _checklist_body(number=9, body=CHECKLIST_CRLF_BEFORE),
                        _checklist_body(number=9, body=CHECKLIST_CRLF_UNTICKED),
                    ),
                ),
                StaticRouteSpec(
                    method=METHOD_PATCH, url=issue_9, replies=(_checklist_body(number=9, body=CHECKLIST_CRLF_UNTICKED),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_PATCH, path=issue_9, body={FIELD_BODY: CHECKLIST_CRLF_UNTICKED}),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/tick-matches-no-unticked-item",
            argv=(command, "5", "--tick", "tests"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(before,)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/write-not-on-re-read",
            argv=(command, "5", "--tick", "wire"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=issue_5, replies=(before,)),
                StaticRouteSpec(method=METHOD_PATCH, url=issue_5, replies=(before,)),
            ),
            writes=(tick,),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "5"),
            usage=(command, "5", "--tick", "wire", "--untick", "docs"),
            credential=EMPTY_CREDENTIAL,
            repository=UNPARSEABLE_ORIGIN,
        ),
    )


#: The golden cases of the issues subcommands of UB-1.1, every value the installed fork's own output.
CASES: Tuple[GoldenCase, ...] = (
    *_list_issues_cases(),
    *_get_issue_cases(),
    *_get_issue_comments_cases(),
    *_comment_issue_cases(),
    *_create_issue_cases(),
    *_update_issue_cases(),
    *_reopen_issue_cases(),
    *_checklist_cases(),
)


# ---------------------------------------------------------------------------------------------------------------------
# Running a case: the steps the compatibility and the fork parity test share
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Outcome:
    """What one run of a wrapper produced: its standard output, its exit code and every request the host received."""

    stdout: str
    exit_code: int
    requests: Tuple[RecordedRequest, ...]


def load_script(*, path: Path, name: str, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The script at ``path`` loaded as the module ``name``, as ``test_wrapper_delivery.load`` loads a wrapper: a fresh
    module for each call. It is in ``sys.modules`` until the test ends: ``dataclasses._is_type`` (Python 3.14) reads
    the module of a class it processes from there with no guard for an absent entry, and the fork declares
    dataclasses."""
    assert path.is_file(), f"{path} does not exist"
    spec = importlib.util.spec_from_file_location(name=name, location=path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec=spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module=module)
    return module


def enter_project(
    *, project: Project, root: Path, monkeypatch: pytest.MonkeyPatch, routes: Sequence[RouteSpec] = ()
) -> FakeGitHub:
    """Build ``project`` in ``root``, make ``root`` the working directory, and answer every request from a fresh fake
    host holding ``routes``, until the test ends."""
    root.mkdir(parents=True, exist_ok=True)
    project.build(root=root)
    monkeypatch.chdir(root)
    host = FakeGitHub()
    for route in routes:
        route.install(host=host)
    host.install(monkeypatch=monkeypatch)
    return host


def exit_code_of(*, exc: SystemExit) -> int:
    """The process exit status ``exc`` stands for: ``0`` for no code, the code when it is an integer, else ``1``."""
    if exc.code is None:
        return EXIT_OK
    if isinstance(exc.code, int):
        return exc.code
    return EXIT_OF_A_MESSAGE


def assert_outcome(*, case: GoldenCase, outcome: Outcome) -> None:
    """Fail unless ``outcome`` has ``case``'s exit code, standard output and requests other than ``GET``, and unless a
    refusal (exit 2) sent no request at all."""
    assert outcome.exit_code == case.exit_code, (
        f"{case.name}: exit code {outcome.exit_code}, the golden is {case.exit_code}; stdout {outcome.stdout!r}"
    )
    assert outcome.stdout == case.stdout, f"{case.name}: the standard output differs from the golden"
    writes = [NonGetRequest.of(request=request) for request in outcome.requests if request.method != METHOD_GET]
    assert writes == list(case.writes), f"{case.name}: the requests other than GET differ from the golden"
    if case.exit_code == EXIT_REFUSED:
        sent = [f"{request.method} {request.url}" for request in outcome.requests]
        assert not sent, f"{case.name}: a refusal sent requests: {sent}"


def assert_log(*, case: GoldenCase, records: Sequence[logging.LogRecord], stderr: str) -> None:
    """Fail unless the log records of a case with a ``log`` expectation hold its refusal in one record, and neither
    any record nor ``stderr`` holds a withheld value."""
    if case.log is None:
        return
    messages = [record.getMessage() for record in records]
    patterns = [re.compile(pattern) for pattern in case.log.refusal]
    assert any(all(pattern.search(message) for pattern in patterns) for message in messages), (
        f"{case.name}: no log record matches every one of {list(case.log.refusal)}: {messages}"
    )
    formatter = logging.Formatter()
    rendered = [formatter.format(record=record) for record in records]
    for withheld in case.log.withheld:
        leaking = [text for text in rendered if withheld in text]
        assert not leaking, f"{case.name}: a log record holds the withheld {withheld!r}: {leaking}"
        assert withheld not in stderr, f"{case.name}: standard error holds the withheld {withheld!r}: {stderr!r}"


def _refuse_connection(self: socket.socket, address: object) -> None:
    del self  # every socket alike: no wrapper test may connect anywhere
    pytest.fail(reason=f"a wrapper test opened a connection to {address!r}; every request goes to the fake host")


def refuse_connections(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test on any socket connection, until it ends: requests reach the fake host inside urllib."""
    monkeypatch.setattr(target=socket.socket, name="connect", value=_refuse_connection)
    monkeypatch.setattr(target=socket.socket, name="connect_ex", value=_refuse_connection)
