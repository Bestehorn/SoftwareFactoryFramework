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
* An uncredentialed route answers as a static route does, but only a request that carries no ``authorization``
  header: a storage host's, which a download's redirect reaches without the GitHub credential. A request that carries
  one is unrouted.
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
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Type, Union
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
HEADER_AUTHORIZATION = "authorization"
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
class UncredentialedRoute(Route):
    """A static route that answers only a request carrying no ``authorization`` header: a storage host's, which a
    download's redirect reaches without the GitHub credential. A request that carries one stays unrouted."""

    def matches(self, *, request: RecordedRequest, endpoint: Endpoint) -> bool:
        """Whether this route answers ``request``, sent to ``endpoint`` without a credential."""
        uncredentialed = request.header(name=HEADER_AUTHORIZATION) is None
        return uncredentialed and super().matches(request=request, endpoint=endpoint)


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
        self._routes.append(self._static_route(kind=Route, method=method, url=url, replies=replies, query=query))

    def uncredentialed_route(
        self,
        *,
        method: str,
        url: str,
        replies: Sequence[Reply],
        query: Optional[Mapping[str, QueryValue]] = None,
    ) -> None:
        """As ``route``, but only for a request that carries no ``authorization`` header; one that carries it is left
        unrouted, so the test fails."""
        self._routes.append(
            self._static_route(kind=UncredentialedRoute, method=method, url=url, replies=replies, query=query)
        )

    @staticmethod
    def _static_route(
        *,
        kind: Type[Route],
        method: str,
        url: str,
        replies: Sequence[Reply],
        query: Optional[Mapping[str, QueryValue]],
    ) -> Route:
        assert replies, f"the route {method} {url} needs at least one reply"
        endpoint, decoded = _target_of(url=url)
        decoded.update(query_of(values=query))
        return kind(method=method.upper(), endpoint=endpoint, query=decoded, replies=list(replies))

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
        assert route is not None  # pytest.fail raises; this narrows the type where pytest's stubs are not installed
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
FIELD_ASSIGNEES = "assignees"
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
class UncredentialedRouteSpec(StaticRouteSpec):
    """``FakeGitHub.uncredentialed_route``'s arguments: a static route that a request carrying a credential misses."""

    def install(self, *, host: FakeGitHub) -> None:
        """Add the uncredentialed route to ``host``."""
        host.uncredentialed_route(method=self.method, url=self.url, replies=self.replies, query=self.query)


@dataclass(frozen=True)
class ListRouteSpec(RouteSpec):
    """``FakeGitHub.list_route``'s arguments: ``items`` served as ``page``/``per_page`` slices with a ``link``, inside
    ``{"total_count": ..., <item_key>: [...]}`` when ``item_key`` is given."""

    url: str
    items: Tuple[Any, ...]
    query: Mapping[str, QueryValue] = field(default_factory=dict)
    item_key: Optional[str] = None

    def install(self, *, host: FakeGitHub) -> None:
        """Add the list route to ``host``."""
        host.list_route(url=self.url, items=self.items, query=self.query, item_key=self.item_key)


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
    assignees: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """An issue as the issues endpoints return it, cut to the fields the commands read; with ``pull_request``, an entry
    of the issue list that is a pull request; with ``assignees``, the assignees' logins, which the claim commands
    read."""
    entry: Dict[str, Any] = {
        FIELD_NUMBER: number,
        FIELD_TITLE: title,
        FIELD_STATE: state,
        FIELD_BODY: body,
        FIELD_LABELS: [{FIELD_NAME: name} for name in labels],
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/issues/{number}",
    }
    if assignees is not None:
        entry[FIELD_ASSIGNEES] = [{FIELD_LOGIN: login} for login in assignees]
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


def error_reply(*, status: int, message: str) -> Reply:
    """GitHub's ``basic-error`` answer with ``status``: ``message``, the documentation URL and the status as text."""
    return Reply(
        status=status,
        body={FIELD_MESSAGE: message, FIELD_DOCUMENTATION_URL: DOCUMENTATION_URL, FIELD_STATUS: str(status)},
    )


def printed_line(*, value: Any) -> str:
    """What ``print(json.dumps(value))`` writes: how the fork prints a one-line verdict."""
    return json.dumps(value) + "\n"


# ---------------------------------------------------------------------------------------------------------------------
# The claim subcommands, each in its flat and its nested ``issue …`` spelling, which share one handler in the fork
# ---------------------------------------------------------------------------------------------------------------------

EXIT_OPEN_AND_UNCLAIMED = 3  # ``claim-check``: the issue is open and nobody has claimed it

METHOD_DELETE = "DELETE"
KEY_CLAIMED = "claimed"
KEY_EXIT_CODE = "exit_code"
KEY_VERIFIED = "verified"
KEY_UNASSIGNED = "unassigned"

ISSUE_GROUP = "issue"  # the nested spelling's first word: ``issue start 5`` is ``start-issue 5``
OTHER_LOGIN = "hubot"
LABEL_ENHANCEMENT = "enhancement"
CLAIM_NUMBER = 5
CLAIM_TITLE = "Wrapper rewrite"
ISSUE_5_PATH = f"{ISSUES_PATH}/5"
ISSUE_6_PATH = f"{ISSUES_PATH}/6"
USER_READ = StaticRouteSpec(
    method=METHOD_GET, url="/user", replies=(Reply(body={FIELD_LOGIN: USER_LOGIN, FIELD_ID: 583231}),)
)
LABEL_MISSING = error_reply(status=404, message="Label does not exist")


def claim_entry(
    *, state: str = STATE_OPEN, labels: Sequence[str] = (), assignees: Sequence[str] = ()
) -> Dict[str, Any]:
    """Issue 5 as the claim commands read it, with its labels and its assignees' logins."""
    return issue_entry(number=CLAIM_NUMBER, title=CLAIM_TITLE, state=state, labels=labels, assignees=assignees)


def label_list(*, names: Sequence[str]) -> List[Dict[str, Any]]:
    """An issue's labels as the labels endpoints answer them, cut to their names."""
    return [{FIELD_NAME: name} for name in names]


def issue_reads(*, entries: Sequence[Mapping[str, Any]]) -> StaticRouteSpec:
    """``GET`` of issue 5, answered with ``entries`` in turn and the last repeated: the read, then the re-read."""
    return StaticRouteSpec(method=METHOD_GET, url=ISSUE_5_PATH, replies=tuple(Reply(body=entry) for entry in entries))


def claim_check_verdict(
    *, state: str, labels: Sequence[str], assignees: Sequence[str], claimed: bool, exit_code: int
) -> str:
    """The fork's ``claim-check`` verdict on issue 5."""
    return printed_json(
        value={
            FIELD_NUMBER: CLAIM_NUMBER,
            FIELD_STATE: state,
            FIELD_LABELS: list(labels),
            FIELD_ASSIGNEES: list(assignees),
            KEY_CLAIMED: claimed,
            KEY_EXIT_CODE: exit_code,
        }
    )


def start_verdict(*, labels: Sequence[str], assignees: Sequence[str]) -> str:
    """The fork's ``start-issue`` verdict on issue 5: claimed, and verified by the re-read showing ``labels`` and
    ``assignees``."""
    return printed_json(
        value={
            FIELD_NUMBER: CLAIM_NUMBER,
            FIELD_STATE: STATE_OPEN,
            FIELD_LABELS: list(labels),
            FIELD_ASSIGNEES: list(assignees),
            KEY_CLAIMED: True,
            KEY_VERIFIED: True,
        }
    )


def release_verdict(*, labels: Sequence[str], unassigned: Sequence[str]) -> str:
    """The fork's ``release-issue`` verdict on issue 5: its labels after the release and the logins it unassigned."""
    return printed_json(
        value={
            FIELD_NUMBER: CLAIM_NUMBER,
            FIELD_LABELS: list(labels),
            KEY_CLAIMED: False,
            KEY_UNASSIGNED: list(unassigned),
        }
    )


def assign_verdict(*, assignees: Sequence[str], unassigned: Optional[Sequence[str]] = None) -> str:
    """The fork's ``assign`` verdict on issue 5; with ``unassigned``, the ``--unassign`` form."""
    value: Dict[str, Any] = {FIELD_NUMBER: CLAIM_NUMBER, FIELD_ASSIGNEES: list(assignees)}
    if unassigned is not None:
        value[KEY_UNASSIGNED] = list(unassigned)
    return printed_json(value=value)


def _name_of(*, words: Tuple[str, ...]) -> str:
    """The name a spelling's cases carry: ``claim-check``, or ``issue/claim-check`` for the nested one."""
    return "/".join(words)


def _claim_check_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    return (
        GoldenCase(
            name=f"{command}/exit-3/open-and-unclaimed",
            argv=(*words, "5"),
            stdout=claim_check_verdict(
                state=STATE_OPEN,
                labels=(LABEL_ENHANCEMENT,),
                assignees=(),
                claimed=False,
                exit_code=EXIT_OPEN_AND_UNCLAIMED,
            ),
            exit_code=EXIT_OPEN_AND_UNCLAIMED,
            routes=(issue_reads(entries=(claim_entry(labels=(LABEL_ENHANCEMENT,)),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/claimed-by-the-label",
            argv=(*words, "5"),
            stdout=claim_check_verdict(
                state=STATE_OPEN,
                labels=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS),
                assignees=(),
                claimed=True,
                exit_code=EXIT_OK,
            ),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(labels=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS)),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/claimed-by-an-assignee",
            argv=(*words, "5"),
            stdout=claim_check_verdict(
                state=STATE_OPEN, labels=(), assignees=(OTHER_LOGIN,), claimed=True, exit_code=EXIT_OK
            ),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(assignees=(OTHER_LOGIN,)),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/closed-and-unclaimed",
            argv=(*words, "5"),
            stdout=claim_check_verdict(state=STATE_CLOSED, labels=(), assignees=(), claimed=False, exit_code=EXIT_OK),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(state=STATE_CLOSED),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(*words, "6"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=ISSUE_6_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5"),
            usage=(*words, "five"),
            credential=credential,
            repository=repository,
        ),
    )


def _start_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    labels_path = f"{ISSUE_5_PATH}/labels"
    assignees_path = f"{ISSUE_5_PATH}/assignees"
    unclaimed = claim_entry(labels=(LABEL_ENHANCEMENT,))
    claimed = claim_entry(labels=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS), assignees=(USER_LOGIN,))
    yours = claim_entry(labels=(LABEL_IN_PROGRESS,), assignees=(USER_LOGIN,))
    theirs = claim_entry(labels=(LABEL_IN_PROGRESS,), assignees=(OTHER_LOGIN,))
    taken_over = claim_entry(labels=(LABEL_IN_PROGRESS,), assignees=(OTHER_LOGIN, USER_LOGIN))
    add_label = StaticRouteSpec(
        method=METHOD_POST,
        url=labels_path,
        replies=(Reply(body=label_list(names=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS))),),
    )
    add_assignee = StaticRouteSpec(
        method=METHOD_POST, url=assignees_path, replies=(Reply(status=CREATED, body=claimed),)
    )
    label_added = NonGetRequest(method=METHOD_POST, path=labels_path, body={FIELD_LABELS: [LABEL_IN_PROGRESS]})
    you_assigned = NonGetRequest(method=METHOD_POST, path=assignees_path, body={FIELD_ASSIGNEES: [USER_LOGIN]})
    return (
        GoldenCase(
            name=f"{command}/exit-0/open-and-unclaimed",
            argv=(*words, "5"),
            stdout=start_verdict(labels=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS), assignees=(USER_LOGIN,)),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(unclaimed, claimed)), USER_READ, add_label, add_assignee),
            writes=(label_added, you_assigned),
        ),
        GoldenCase(
            name=f"{command}/exit-0/already-yours-writes-nothing",
            argv=(*words, "5"),
            stdout=start_verdict(labels=(LABEL_IN_PROGRESS,), assignees=(USER_LOGIN,)),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(yours,)), USER_READ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/force-takes-over",
            argv=(*words, "5", "--force"),
            stdout=start_verdict(labels=(LABEL_IN_PROGRESS,), assignees=(OTHER_LOGIN, USER_LOGIN)),
            exit_code=EXIT_OK,
            routes=(
                issue_reads(entries=(theirs, taken_over)),
                USER_READ,
                StaticRouteSpec(
                    method=METHOD_POST, url=assignees_path, replies=(Reply(status=CREATED, body=taken_over),)
                ),
            ),
            writes=(you_assigned,),
        ),
        GoldenCase(
            name=f"{command}/exit-1/assigned-to-another",
            argv=(*words, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(issue_reads(entries=(claim_entry(assignees=(OTHER_LOGIN,)),)), USER_READ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/label-without-an-assignee",
            argv=(*words, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(issue_reads(entries=(claim_entry(labels=(LABEL_IN_PROGRESS,)),)), USER_READ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/strict-refuses-your-own-claim",
            argv=(*words, "5", "--strict"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(issue_reads(entries=(yours,)), USER_READ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-open",
            argv=(*words, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(issue_reads(entries=(claim_entry(state=STATE_CLOSED),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/claim-not-on-re-read",
            argv=(*words, "5"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(issue_reads(entries=(unclaimed,)), USER_READ, add_label, add_assignee),
            writes=(label_added, you_assigned),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(*words, "6"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=ISSUE_6_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5"),
            usage=words,
            credential=credential,
            repository=repository,
        ),
    )


def _release_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    assignees_path = f"{ISSUE_5_PATH}/assignees"
    unassign_route = StaticRouteSpec(
        method=METHOD_DELETE, url=assignees_path, replies=(Reply(body=claim_entry(labels=(LABEL_ENHANCEMENT,))),)
    )
    you_unassigned = NonGetRequest(method=METHOD_DELETE, path=assignees_path, body={FIELD_ASSIGNEES: [USER_LOGIN]})
    return (
        GoldenCase(
            name=f"{command}/exit-0/label-and-your-assignment-dropped",
            argv=(*words, "5"),
            stdout=release_verdict(labels=(LABEL_ENHANCEMENT,), unassigned=(USER_LOGIN,)),
            exit_code=EXIT_OK,
            routes=(
                issue_reads(
                    entries=(claim_entry(labels=(LABEL_ENHANCEMENT, LABEL_IN_PROGRESS), assignees=(USER_LOGIN,)),)
                ),
                USER_READ,
                StaticRouteSpec(
                    method=METHOD_PATCH,
                    url=ISSUE_5_PATH,
                    replies=(Reply(body=claim_entry(labels=(LABEL_ENHANCEMENT,), assignees=(USER_LOGIN,))),),
                ),
                unassign_route,
            ),
            writes=(
                NonGetRequest(method=METHOD_PATCH, path=ISSUE_5_PATH, body={FIELD_LABELS: [LABEL_ENHANCEMENT]}),
                you_unassigned,
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/not-claimed-writes-nothing",
            argv=(*words, "5"),
            stdout=release_verdict(labels=(LABEL_ENHANCEMENT,), unassigned=()),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(labels=(LABEL_ENHANCEMENT,)),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/another-assignee-kept",
            argv=(*words, "5"),
            stdout=release_verdict(labels=(), unassigned=()),
            exit_code=EXIT_OK,
            routes=(
                issue_reads(entries=(claim_entry(labels=(LABEL_IN_PROGRESS,), assignees=(OTHER_LOGIN,)),)),
                USER_READ,
                StaticRouteSpec(
                    method=METHOD_PATCH,
                    url=ISSUE_5_PATH,
                    replies=(Reply(body=claim_entry(assignees=(OTHER_LOGIN,))),),
                ),
            ),
            writes=(NonGetRequest(method=METHOD_PATCH, path=ISSUE_5_PATH, body={FIELD_LABELS: []}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/your-assignment-without-the-label",
            argv=(*words, "5"),
            stdout=release_verdict(labels=(), unassigned=(USER_LOGIN,)),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(assignees=(USER_LOGIN,)),)), USER_READ, unassign_route),
            writes=(you_unassigned,),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(*words, "6"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=ISSUE_6_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5"),
            usage=(*words, "x"),
            credential=credential,
            repository=repository,
        ),
    )


def _label_add_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    labels_of_5 = f"{ISSUE_5_PATH}/labels"
    labels_of_6 = f"{ISSUE_6_PATH}/labels"
    added = label_list(names=(LABEL_ENHANCEMENT, "bug", "ui"))
    return (
        GoldenCase(
            name=f"{command}/exit-0/added-beside-the-others",
            argv=(*words, "5", "--labels", "bug, ui,"),
            stdout=printed_json(value=added),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_POST, url=labels_of_5, replies=(Reply(body=added),)),),
            writes=(NonGetRequest(method=METHOD_POST, path=labels_of_5, body={FIELD_LABELS: ["bug", "ui"]}),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/no-label-name",
            argv=(*words, "5", "--labels", " , "),
            stdout="",
            exit_code=EXIT_API_ERROR,
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(*words, "6", "--labels", "bug"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=labels_of_6, replies=(NOT_FOUND,)),),
            writes=(NonGetRequest(method=METHOD_POST, path=labels_of_6, body={FIELD_LABELS: ["bug"]}),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5", "--labels", "bug"),
            usage=(*words, "5"),
            credential=credential,
            repository=repository,
        ),
    )


def _label_remove_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    remaining = label_list(names=(LABEL_ENHANCEMENT,))
    slashed = f"{ISSUE_5_PATH}/labels/area%2Fui"
    spaced = f"{ISSUE_5_PATH}/labels/help%20wanted"
    absent = f"{ISSUE_5_PATH}/labels/wontfix"
    return (
        GoldenCase(
            name=f"{command}/exit-0/name-with-a-slash",
            argv=(*words, "5", "--label", "area/ui"),
            stdout=printed_json(value=remaining),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_DELETE, url=slashed, replies=(Reply(body=remaining),)),),
            writes=(NonGetRequest(method=METHOD_DELETE, path=slashed),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/name-with-a-space",
            argv=(*words, "5", "--label", "help wanted"),
            stdout=printed_json(value=remaining),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_DELETE, url=spaced, replies=(Reply(body=remaining),)),),
            writes=(NonGetRequest(method=METHOD_DELETE, path=spaced),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/label-not-on-the-issue",
            argv=(*words, "5", "--label", "wontfix"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_DELETE, url=absent, replies=(LABEL_MISSING,)),),
            writes=(NonGetRequest(method=METHOD_DELETE, path=absent),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5", "--label", "wontfix"),
            usage=(*words, "5"),
            credential=credential,
            repository=repository,
        ),
    )


def _assign_cases(*, words: Tuple[str, ...], credential: Project, repository: Project) -> Tuple[GoldenCase, ...]:
    command = _name_of(words=words)
    assignees_of_5 = f"{ISSUE_5_PATH}/assignees"
    assignees_of_6 = f"{ISSUE_6_PATH}/assignees"
    both = (USER_LOGIN, OTHER_LOGIN)
    return (
        GoldenCase(
            name=f"{command}/exit-0/me",
            argv=(*words, "5", "--me"),
            stdout=assign_verdict(assignees=(USER_LOGIN,)),
            exit_code=EXIT_OK,
            routes=(
                USER_READ,
                StaticRouteSpec(
                    method=METHOD_POST,
                    url=assignees_of_5,
                    replies=(Reply(status=CREATED, body=claim_entry(assignees=(USER_LOGIN,))),),
                ),
            ),
            writes=(NonGetRequest(method=METHOD_POST, path=assignees_of_5, body={FIELD_ASSIGNEES: [USER_LOGIN]}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/user-beside-the-others",
            argv=(*words, "5", "--user", OTHER_LOGIN),
            stdout=assign_verdict(assignees=both),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_POST,
                    url=assignees_of_5,
                    replies=(Reply(status=CREATED, body=claim_entry(assignees=both)),),
                ),
            ),
            writes=(NonGetRequest(method=METHOD_POST, path=assignees_of_5, body={FIELD_ASSIGNEES: [OTHER_LOGIN]}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/unassign",
            argv=(*words, "5", "--unassign"),
            stdout=assign_verdict(assignees=(), unassigned=both),
            exit_code=EXIT_OK,
            routes=(
                issue_reads(entries=(claim_entry(assignees=both),)),
                StaticRouteSpec(method=METHOD_DELETE, url=assignees_of_5, replies=(Reply(body=claim_entry()),)),
            ),
            writes=(NonGetRequest(method=METHOD_DELETE, path=assignees_of_5, body={FIELD_ASSIGNEES: list(both)}),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/unassign-nobody-writes-nothing",
            argv=(*words, "5", "--unassign"),
            stdout=assign_verdict(assignees=(), unassigned=()),
            exit_code=EXIT_OK,
            routes=(issue_reads(entries=(claim_entry(),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(*words, "6", "--user", OTHER_LOGIN),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=assignees_of_6, replies=(NOT_FOUND,)),),
            writes=(NonGetRequest(method=METHOD_POST, path=assignees_of_6, body={FIELD_ASSIGNEES: [OTHER_LOGIN]}),),
        ),
        *_refusal_cases(
            command=command,
            argv=(*words, "5", "--user", OTHER_LOGIN),
            usage=(*words, "5", "--me", "--unassign"),
            credential=credential,
            repository=repository,
        ),
    )


# ---------------------------------------------------------------------------------------------------------------------
# The pull-request subcommands
# ---------------------------------------------------------------------------------------------------------------------

METHOD_PUT = "PUT"
NO_CONTENT = 204
METHOD_NOT_ALLOWED = 405

FIELD_HEAD = "head"
FIELD_BASE = "base"
FIELD_REF = "ref"
FIELD_SHA = "sha"
FIELD_HEAD_SHA = "head_sha"
FIELD_MERGEABLE = "mergeable"
FIELD_MERGEABLE_STATE = "mergeable_state"
FIELD_MERGED = "merged"
FIELD_EVENT = "event"
FIELD_MERGE_METHOD = "merge_method"
FIELD_COMMIT_MESSAGE = "commit_message"
FIELD_CHECK_RUNS = "check_runs"
FIELD_CONCLUSION = "conclusion"
FIELD_STATUSES = "statuses"
FIELD_CONTEXT = "context"
FIELD_DESCRIPTION = "description"
FIELD_COMBINED_STATUS = "combined_status"

REPOSITORY_PATH = f"/repos/{OWNER}/{REPOSITORY}"
PULLS_PATH = f"{REPOSITORY_PATH}/pulls"
PULL_77_PATH = f"{PULLS_PATH}/77"
PULL_78_PATH = f"{PULLS_PATH}/78"
BRANCH_MAIN = "main"
FEATURE_BRANCH = "issue-17-wrapper"
HEAD_SHA = "deadbeef" * 5  # a full commit sha: 40 hex characters
PULL_TITLE = "Rewrite the wrapper"
PULL_BODY = "Closes #17."
PR_BODY_FILE = "pr.md"
PR_BODY_TEXT = "## Summary\n\nRewrites the wrapper on `github_api/`.\n\n- [x] transport\n\nCloses #17.\n"
STATE_PENDING = "pending"
MERGEABLE_UNKNOWN = "unknown"


def pull_entry(
    *,
    number: int,
    title: str,
    body: Optional[str] = None,
    base: str = BRANCH_MAIN,
    mergeable: Optional[bool] = None,
    mergeable_state: str = MERGEABLE_UNKNOWN,
) -> Dict[str, Any]:
    """A pull request as the pulls endpoints return it, cut to the fields the commands read: its head is
    ``FEATURE_BRANCH`` at ``HEAD_SHA``."""
    return {
        FIELD_NUMBER: number,
        FIELD_TITLE: title,
        FIELD_STATE: STATE_OPEN,
        FIELD_BODY: body,
        FIELD_HEAD: {FIELD_REF: FEATURE_BRANCH, FIELD_SHA: HEAD_SHA},
        FIELD_BASE: {FIELD_REF: base},
        FIELD_MERGEABLE: mergeable,
        FIELD_MERGEABLE_STATE: mergeable_state,
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/pull/{number}",
    }


PULL_77 = pull_entry(number=77, title=PULL_TITLE, body=PULL_BODY, mergeable=True, mergeable_state="clean")
PULL_EXISTS = Reply(
    status=422,
    body={
        FIELD_MESSAGE: "Validation Failed",
        FIELD_ERRORS: [
            {
                FIELD_RESOURCE: "PullRequest",
                FIELD_CODE: "custom",
                FIELD_MESSAGE: f"A pull request already exists for {OWNER}:{FEATURE_BRANCH}.",
            }
        ],
        FIELD_DOCUMENTATION_URL: DOCUMENTATION_URL,
        FIELD_STATUS: "422",
    },
)


def _create_pr_cases() -> Tuple[GoldenCase, ...]:
    command = "create-pr"
    titled = pull_entry(number=77, title=PULL_TITLE, body=PULL_BODY)
    from_file = pull_entry(number=78, title=FEATURE_BRANCH, body=PR_BODY_TEXT, base="develop")
    bare = pull_entry(number=79, title=FEATURE_BRANCH)
    bare_body = {FIELD_TITLE: FEATURE_BRANCH, FIELD_HEAD: FEATURE_BRANCH, FIELD_BASE: BRANCH_MAIN}
    with_file = Project(files=((PR_BODY_FILE, PR_BODY_TEXT),))
    return (
        GoldenCase(
            name=f"{command}/exit-0/head-title-body",
            argv=(command, "--head", FEATURE_BRANCH, "--title", PULL_TITLE, "--body", PULL_BODY),
            stdout=printed_json(value=titled),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(method=METHOD_POST, url=PULLS_PATH, replies=(Reply(status=CREATED, body=titled),)),
            ),
            writes=(
                NonGetRequest(
                    method=METHOD_POST,
                    path=PULLS_PATH,
                    body={
                        FIELD_TITLE: PULL_TITLE,
                        FIELD_HEAD: FEATURE_BRANCH,
                        FIELD_BASE: BRANCH_MAIN,
                        FIELD_BODY: PULL_BODY,
                    },
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/title-of-the-head-base-body-file",
            argv=(command, "--head", FEATURE_BRANCH, "--base", "develop", "--body-file", PR_BODY_FILE),
            stdout=printed_json(value=from_file),
            exit_code=EXIT_OK,
            project=with_file,
            routes=(
                StaticRouteSpec(method=METHOD_POST, url=PULLS_PATH, replies=(Reply(status=CREATED, body=from_file),)),
            ),
            writes=(
                NonGetRequest(
                    method=METHOD_POST,
                    path=PULLS_PATH,
                    body={
                        FIELD_TITLE: FEATURE_BRANCH,
                        FIELD_HEAD: FEATURE_BRANCH,
                        FIELD_BASE: "develop",
                        FIELD_BODY: PR_BODY_TEXT,
                    },
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/empty-body-left-out",
            argv=(command, "--head", FEATURE_BRANCH, "--body", ""),
            stdout=printed_json(value=bare),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_POST, url=PULLS_PATH, replies=(Reply(status=CREATED, body=bare),)),),
            writes=(NonGetRequest(method=METHOD_POST, path=PULLS_PATH, body=bare_body),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/validation-failed",
            argv=(command, "--head", FEATURE_BRANCH),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=PULLS_PATH, replies=(PULL_EXISTS,)),),
            writes=(NonGetRequest(method=METHOD_POST, path=PULLS_PATH, body=bare_body),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/body-and-body-file",
            argv=(command, "--head", FEATURE_BRANCH, "--body", PULL_BODY, "--body-file", PR_BODY_FILE),
            stdout="",
            exit_code=EXIT_API_ERROR,
            project=with_file,
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "--head", FEATURE_BRANCH),
            usage=(command, "--title", "No head"),
            credential=EMPTY_CREDENTIAL,
            repository=UNPARSEABLE_ORIGIN,
        ),
    )


def _get_pr_cases() -> Tuple[GoldenCase, ...]:
    command = "get-pr"
    return (
        GoldenCase(
            name=f"{command}/exit-0/pull-request",
            argv=(command, "77"),
            stdout=printed_json(value=PULL_77),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_GET, url=PULL_77_PATH, replies=(Reply(body=PULL_77),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "78"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=PULL_78_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "77"),
            usage=(command, "seventy-seven"),
            credential=NO_CREDENTIAL,
            repository=NO_ORIGIN,
        ),
    )


def check_run_entry(*, check_id: int, name: str, status: str, conclusion: Optional[str]) -> Dict[str, Any]:
    """A check run of ``HEAD_SHA`` as the check-runs endpoint lists it, cut to a few fields."""
    return {
        FIELD_ID: check_id,
        FIELD_NAME: name,
        FIELD_HEAD_SHA: HEAD_SHA,
        FIELD_STATUS: status,
        FIELD_CONCLUSION: conclusion,
    }


def combined_status(*, state: str, statuses: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """The combined commit status of ``HEAD_SHA``: its ``state`` and its legacy ``statuses``."""
    return {FIELD_STATE: state, FIELD_SHA: HEAD_SHA, FIELD_TOTAL_COUNT: len(statuses), FIELD_STATUSES: list(statuses)}


def _get_pr_checks_cases() -> Tuple[GoldenCase, ...]:
    command = "get-pr-checks"
    check_runs_path = f"{REPOSITORY_PATH}/commits/{HEAD_SHA}/check-runs"
    status_path = f"{REPOSITORY_PATH}/commits/{HEAD_SHA}/status"
    blocked = pull_entry(number=77, title=PULL_TITLE, mergeable=True, mergeable_state="blocked")
    fresh = pull_entry(number=77, title=PULL_TITLE)
    check_runs = (
        check_run_entry(check_id=501, name="verify (lint)", status="completed", conclusion="success"),
        check_run_entry(check_id=502, name="verify (tests)", status="in_progress", conclusion=None),
    )
    legacy = {FIELD_CONTEXT: "ci/legacy", FIELD_STATE: STATE_PENDING, FIELD_DESCRIPTION: "Waiting for status"}
    return (
        GoldenCase(
            name=f"{command}/exit-0/check-runs-and-statuses",
            argv=(command, "77"),
            stdout=printed_json(
                value={
                    FIELD_HEAD: HEAD_SHA,
                    FIELD_MERGEABLE: True,
                    FIELD_MERGEABLE_STATE: "blocked",
                    FIELD_COMBINED_STATUS: STATE_PENDING,
                    FIELD_CHECK_RUNS: [
                        {FIELD_NAME: "verify (lint)", FIELD_STATUS: "completed", FIELD_CONCLUSION: "success"},
                        {FIELD_NAME: "verify (tests)", FIELD_STATUS: "in_progress", FIELD_CONCLUSION: None},
                    ],
                    FIELD_STATUSES: [legacy],
                }
            ),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=PULL_77_PATH, replies=(Reply(body=blocked),)),
                ListRouteSpec(url=check_runs_path, items=check_runs, item_key=FIELD_CHECK_RUNS),
                StaticRouteSpec(
                    method=METHOD_GET,
                    url=status_path,
                    replies=(Reply(body=combined_status(state=STATE_PENDING, statuses=(legacy,))),),
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-0/no-checks-yet",
            argv=(command, "77"),
            stdout=printed_json(
                value={
                    FIELD_HEAD: HEAD_SHA,
                    FIELD_MERGEABLE: None,
                    FIELD_MERGEABLE_STATE: MERGEABLE_UNKNOWN,
                    FIELD_COMBINED_STATUS: STATE_PENDING,
                    FIELD_CHECK_RUNS: [],
                    FIELD_STATUSES: [],
                }
            ),
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(method=METHOD_GET, url=PULL_77_PATH, replies=(Reply(body=fresh),)),
                ListRouteSpec(url=check_runs_path, items=(), item_key=FIELD_CHECK_RUNS),
                StaticRouteSpec(
                    method=METHOD_GET,
                    url=status_path,
                    replies=(Reply(body=combined_status(state=STATE_PENDING, statuses=())),),
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/pull-request-not-found",
            argv=(command, "78"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=PULL_78_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "77"),
            usage=(command,),
            credential=PLACEHOLDER_CREDENTIAL,
            repository=NO_GIT_CONFIG,
        ),
    )


def review_entry(*, body: str) -> Dict[str, Any]:
    """The approving review of pull request 77 as the reviews endpoint answers it, cut to a few fields."""
    return {
        FIELD_ID: 80,
        FIELD_USER: {FIELD_LOGIN: OTHER_LOGIN},
        FIELD_BODY: body,
        FIELD_STATE: "APPROVED",
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/pull/77#pullrequestreview-80",
    }


OWN_PULL_REQUEST = Reply(
    status=422,
    body={
        FIELD_MESSAGE: "Unprocessable Entity",
        FIELD_ERRORS: ["Review Can not approve your own pull request"],
        FIELD_DOCUMENTATION_URL: DOCUMENTATION_URL,
        FIELD_STATUS: "422",
    },
)


def _approve_pr_cases() -> Tuple[GoldenCase, ...]:
    command = "approve-pr"
    reviews_path = f"{PULL_77_PATH}/reviews"
    approved = review_entry(body="")
    commented = review_entry(body="Looks right.")
    approve = NonGetRequest(method=METHOD_POST, path=reviews_path, body={FIELD_EVENT: "APPROVE"})
    return (
        GoldenCase(
            name=f"{command}/exit-0/approve",
            argv=(command, "77"),
            stdout=printed_json(value=approved),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_POST, url=reviews_path, replies=(Reply(body=approved),)),),
            writes=(approve,),
        ),
        GoldenCase(
            name=f"{command}/exit-0/approve-with-a-comment",
            argv=(command, "77", "--body", "Looks right."),
            stdout=printed_json(value=commented),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_POST, url=reviews_path, replies=(Reply(body=commented),)),),
            writes=(
                NonGetRequest(
                    method=METHOD_POST, path=reviews_path, body={FIELD_EVENT: "APPROVE", FIELD_BODY: "Looks right."}
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/own-pull-request",
            argv=(command, "77"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_POST, url=reviews_path, replies=(OWN_PULL_REQUEST,)),),
            writes=(approve,),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "77"),
            usage=(command,),
            credential=TWO_TOKEN_CREDENTIAL,
            repository=FOREIGN_ORIGIN,
        ),
    )


def _merge_pr_cases() -> Tuple[GoldenCase, ...]:
    command = "merge-pr"
    merge_path = f"{PULL_77_PATH}/merge"
    merged = {FIELD_SHA: HEAD_SHA, FIELD_MERGED: True, FIELD_MESSAGE: "Pull Request successfully merged"}
    squash_message = "Rewrite the wrapper (#77)"
    merge = NonGetRequest(method=METHOD_PUT, path=merge_path, body={FIELD_MERGE_METHOD: "merge"})
    return (
        GoldenCase(
            name=f"{command}/exit-0/merge-by-default",
            argv=(command, "77"),
            stdout=printed_json(value=merged),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_PUT, url=merge_path, replies=(Reply(body=merged),)),),
            writes=(merge,),
        ),
        GoldenCase(
            name=f"{command}/exit-0/squash-with-a-message",
            argv=(command, "77", "--method", "squash", "--commit-message", squash_message),
            stdout=printed_json(value=merged),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_PUT, url=merge_path, replies=(Reply(body=merged),)),),
            writes=(
                NonGetRequest(
                    method=METHOD_PUT,
                    path=merge_path,
                    body={FIELD_MERGE_METHOD: "squash", FIELD_COMMIT_MESSAGE: squash_message},
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-mergeable",
            argv=(command, "77"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(
                StaticRouteSpec(
                    method=METHOD_PUT,
                    url=merge_path,
                    replies=(error_reply(status=METHOD_NOT_ALLOWED, message="Pull Request is not mergeable"),),
                ),
            ),
            writes=(merge,),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, "77"),
            usage=(command, "77", "--method", "fast-forward"),
            credential=EMPTY_CREDENTIAL,
            repository=NO_ORIGIN,
        ),
    )


def _delete_remote_branch_cases() -> Tuple[GoldenCase, ...]:
    command = "delete-remote-branch"
    heads_path = f"{REPOSITORY_PATH}/git/refs/heads"
    nested_branch = "feature/issue-17/part-1"
    return (
        GoldenCase(
            name=f"{command}/exit-0/branch",
            argv=(command, FEATURE_BRANCH),
            stdout=f"Deleted remote branch: {FEATURE_BRANCH}\n",
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_DELETE, url=f"{heads_path}/{FEATURE_BRANCH}", replies=(Reply(status=NO_CONTENT),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_DELETE, path=f"{heads_path}/{FEATURE_BRANCH}"),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/branch-with-slashes",
            argv=(command, nested_branch),
            stdout=f"Deleted remote branch: {nested_branch}\n",
            exit_code=EXIT_OK,
            routes=(
                StaticRouteSpec(
                    method=METHOD_DELETE, url=f"{heads_path}/{nested_branch}", replies=(Reply(status=NO_CONTENT),)
                ),
            ),
            writes=(NonGetRequest(method=METHOD_DELETE, path=f"{heads_path}/{nested_branch}"),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/no-such-reference",
            argv=(command, "gone"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(
                StaticRouteSpec(
                    method=METHOD_DELETE,
                    url=f"{heads_path}/gone",
                    replies=(error_reply(status=422, message="Reference does not exist"),),
                ),
            ),
            writes=(NonGetRequest(method=METHOD_DELETE, path=f"{heads_path}/gone"),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, FEATURE_BRANCH),
            usage=(command,),
            credential=NO_CREDENTIAL,
            repository=UNPARSEABLE_ORIGIN,
        ),
    )


# ---------------------------------------------------------------------------------------------------------------------
# The CI subcommands
# ---------------------------------------------------------------------------------------------------------------------

EXIT_WAIT_NOT_SUCCESS = 10  # ``wait-run``: the run completed with a conclusion other than ``success``
EXIT_WAIT_TIMEOUT = 11  # ``wait-run``: the timeout passed before the run completed
FOUND = 302

FIELD_PATH = "path"
FIELD_WORKFLOWS = "workflows"
FIELD_WORKFLOW_RUNS = "workflow_runs"
KEY_RUN_ID = "run_id"
KEY_TIMEOUT_SECONDS = "timeout_seconds"
RUN_IN_PROGRESS = "in_progress"
RUN_COMPLETED = "completed"
CONCLUSION_SUCCESS = "success"
CONCLUSION_FAILURE = "failure"
MEDIA_TYPE_ZIP = "application/zip"

ACTIONS_PATH = f"{REPOSITORY_PATH}/actions"
WORKFLOWS_PATH = f"{ACTIONS_PATH}/workflows"
RUNS_PATH = f"{ACTIONS_PATH}/runs"
RUN_ID = 4242
RUN_PATH = f"{RUNS_PATH}/{RUN_ID}"
MISSING_RUN_PATH = f"{RUNS_PATH}/4243"
RUN_URL = f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/actions/runs/{RUN_ID}"
#: Where the logs endpoint's ``302`` sends the download: a pre-signed storage URL, on another host than the API.
STORAGE_URL = "https://productionresultssa1.blob.core.windows.net/actions-results/4242/logs.zip?sv=2025-01-05&sp=r"
LOG_ARCHIVE_TIME = (2026, 11, 10, 10, 0, 0)

RunOutcome = Tuple[str, Optional[str]]  # a run's status and conclusion


def workflow_entry(*, workflow_id: int, name: str, state: str, file_name: str) -> Dict[str, Any]:
    """A workflow as the workflows endpoint lists it, cut to a few fields."""
    return {FIELD_ID: workflow_id, FIELD_NAME: name, FIELD_PATH: f".github/workflows/{file_name}", FIELD_STATE: state}


def run_entry(*, run_id: int, outcome: RunOutcome) -> Dict[str, Any]:
    """A run of the ``CI`` workflow as the runs endpoints return it, cut to a few fields."""
    status, conclusion = outcome
    return {
        FIELD_ID: run_id,
        FIELD_NAME: "CI",
        FIELD_HEAD_SHA: HEAD_SHA,
        FIELD_STATUS: status,
        FIELD_CONCLUSION: conclusion,
        FIELD_HTML_URL: f"{WEB_ORIGIN}/{OWNER}/{REPOSITORY}/actions/runs/{run_id}",
    }


def listed_runs(*, entries: Sequence[Mapping[str, Any]], limit: int) -> str:
    """The fork's ``list-runs`` lines for the first ``limit`` of ``entries``."""
    return "".join(
        f"{entry[FIELD_ID]:<12} {entry[FIELD_STATUS]:<12} {str(entry[FIELD_CONCLUSION]):<12} {entry[FIELD_NAME]}\n"
        for entry in entries[:limit]
    )


def log_archive(*, entries: Sequence[Tuple[str, str]]) -> bytes:
    """A run's log archive as the storage host serves it: a zip of each entry's text in UTF-8, in order, every entry
    with one fixed timestamp so the bytes never vary."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(file=buffer, mode="w") as archive:
        for name, text in entries:
            entry = zipfile.ZipInfo(filename=name, date_time=LOG_ARCHIVE_TIME)
            archive.writestr(zinfo_or_arcname=entry, data=text.encode(encoding="utf-8"))
    return buffer.getvalue()


def printed_logs(*, entries: Sequence[Tuple[str, str]]) -> str:
    """The fork's ``get-logs`` output for ``entries``: each name in a ``====`` line, then its text and a newline."""
    return "".join(f"==== {name} ====\n{text}\n" for name, text in entries)


WORKFLOWS = (
    workflow_entry(workflow_id=161335, name="CI", state="active", file_name="ci.yml"),
    workflow_entry(workflow_id=161336, name="Release", state="disabled_manually", file_name="release.yml"),
)
RUN_OUTCOMES: Tuple[RunOutcome, ...] = (
    (RUN_IN_PROGRESS, None),
    (RUN_COMPLETED, CONCLUSION_SUCCESS),
    (RUN_COMPLETED, CONCLUSION_FAILURE),
    (RUN_COMPLETED, "cancelled"),
)
RUN_HISTORY_SIZE = 12  # more than ``list-runs``' default ``--limit`` of 10, which the fork sends as ``per_page``
RUN_HISTORY = tuple(
    run_entry(run_id=RUN_ID - offset, outcome=RUN_OUTCOMES[offset % len(RUN_OUTCOMES)])
    for offset in range(RUN_HISTORY_SIZE)
)
COMPLETED_RUNS = tuple(entry for entry in RUN_HISTORY if entry[FIELD_STATUS] == RUN_COMPLETED)
LINT_LOG = (
    "0_verify (lint).txt",
    "\ufeff2026-11-10T10:00:01.0000000Z ruff check\n2026-11-10T10:00:02.0000000Z ✓ All checks passed!",
)
SETUP_LOG = ("verify (tests)/1_Set up job.txt", "2026-11-10T10:00:03.0000000Z Current runner version: '2.330.0'")
FAILED_STEP_LOG = ("verify (tests)/4_Run failed tests.txt", "2026-11-10T10:01:00.0000000Z 1 failed, 46 passed")
LOG_ENTRIES = (LINT_LOG, SETUP_LOG, FAILED_STEP_LOG)
#: The logs endpoint's answer, then the storage host's, which a request carrying the GitHub credential never reaches.
LOGS_ON_STORAGE = (
    StaticRouteSpec(method=METHOD_GET, url=f"{RUN_PATH}/logs", replies=(redirect(status=FOUND, location=STORAGE_URL),)),
    UncredentialedRouteSpec(
        method=METHOD_GET,
        url=STORAGE_URL,
        replies=(Reply(body=log_archive(entries=LOG_ENTRIES), headers={HEADER_CONTENT_TYPE: MEDIA_TYPE_ZIP}),),
    ),
)


def _list_workflows_cases() -> Tuple[GoldenCase, ...]:
    command = "list-workflows"
    return (
        GoldenCase(
            name=f"{command}/exit-0/every-workflow",
            argv=(command,),
            stdout="161335       active     CI\n161336       disabled_manually Release\n",
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=WORKFLOWS_PATH, items=WORKFLOWS, item_key=FIELD_WORKFLOWS),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command,),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(ListFailureRouteSpec(url=WORKFLOWS_PATH, failure=NOT_FOUND),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command,),
            usage=(command, "--all"),
            credential=PLACEHOLDER_CREDENTIAL,
            repository=FOREIGN_ORIGIN,
        ),
    )


def _list_runs_cases() -> Tuple[GoldenCase, ...]:
    command = "list-runs"
    return (
        GoldenCase(
            name=f"{command}/exit-0/default-limit-of-ten",
            argv=(command,),
            stdout=listed_runs(entries=RUN_HISTORY, limit=10),
            exit_code=EXIT_OK,
            routes=(ListRouteSpec(url=RUNS_PATH, items=RUN_HISTORY, item_key=FIELD_WORKFLOW_RUNS),),
        ),
        GoldenCase(
            name=f"{command}/exit-0/workflow-status-limit",
            argv=(command, "--workflow", "ci.yml", "--status", RUN_COMPLETED, "--limit", "2"),
            stdout=listed_runs(entries=COMPLETED_RUNS, limit=2),
            exit_code=EXIT_OK,
            routes=(
                ListRouteSpec(
                    url=f"{WORKFLOWS_PATH}/ci.yml/runs",
                    items=COMPLETED_RUNS,
                    query={FIELD_STATUS: RUN_COMPLETED},
                    item_key=FIELD_WORKFLOW_RUNS,
                ),
            ),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "--workflow", "missing.yml"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(ListFailureRouteSpec(url=f"{WORKFLOWS_PATH}/missing.yml/runs", failure=NOT_FOUND),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command,),
            usage=(command, "--limit", "ten"),
            credential=TWO_TOKEN_CREDENTIAL,
            repository=NO_GIT_CONFIG,
        ),
    )


def _get_run_cases() -> Tuple[GoldenCase, ...]:
    command = "get-run"
    succeeded = run_entry(run_id=RUN_ID, outcome=(RUN_COMPLETED, CONCLUSION_SUCCESS))
    return (
        GoldenCase(
            name=f"{command}/exit-0/run",
            argv=(command, str(RUN_ID)),
            stdout=printed_json(value=succeeded),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_GET, url=RUN_PATH, replies=(Reply(body=succeeded),)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "4243"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=MISSING_RUN_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, str(RUN_ID)),
            usage=(command, "latest"),
            credential=EMPTY_CREDENTIAL,
            repository=FOREIGN_ORIGIN,
        ),
    )


def _wait_run_cases() -> Tuple[GoldenCase, ...]:
    """The fork reads the run, returns once it is completed, checks its deadline and only then sleeps
    ``--interval-seconds``: ``--timeout-seconds 0`` times out after one read with no sleep, and ``--interval-seconds
    0`` makes the one poll's sleep take no time, so no case waits."""
    command = "wait-run"
    in_progress = Reply(body=run_entry(run_id=RUN_ID, outcome=(RUN_IN_PROGRESS, None)))
    succeeded = Reply(body=run_entry(run_id=RUN_ID, outcome=(RUN_COMPLETED, CONCLUSION_SUCCESS)))
    failed = Reply(body=run_entry(run_id=RUN_ID, outcome=(RUN_COMPLETED, CONCLUSION_FAILURE)))
    return (
        GoldenCase(
            name=f"{command}/exit-0/completed-success",
            argv=(command, str(RUN_ID)),
            stdout=printed_line(
                value={
                    KEY_RUN_ID: RUN_ID,
                    FIELD_STATUS: RUN_COMPLETED,
                    FIELD_CONCLUSION: CONCLUSION_SUCCESS,
                    FIELD_HTML_URL: RUN_URL,
                }
            ),
            exit_code=EXIT_OK,
            routes=(StaticRouteSpec(method=METHOD_GET, url=RUN_PATH, replies=(succeeded,)),),
        ),
        GoldenCase(
            name=f"{command}/exit-10/failure-after-one-poll",
            argv=(command, str(RUN_ID), "--interval-seconds", "0"),
            stdout=printed_line(
                value={
                    KEY_RUN_ID: RUN_ID,
                    FIELD_STATUS: RUN_COMPLETED,
                    FIELD_CONCLUSION: CONCLUSION_FAILURE,
                    FIELD_HTML_URL: RUN_URL,
                }
            ),
            exit_code=EXIT_WAIT_NOT_SUCCESS,
            routes=(StaticRouteSpec(method=METHOD_GET, url=RUN_PATH, replies=(in_progress, failed)),),
        ),
        GoldenCase(
            name=f"{command}/exit-11/timeout-of-zero-seconds",
            argv=(command, str(RUN_ID), "--timeout-seconds", "0"),
            stdout=printed_line(value={KEY_RUN_ID: RUN_ID, FIELD_STATUS: RUN_IN_PROGRESS, KEY_TIMEOUT_SECONDS: 0}),
            exit_code=EXIT_WAIT_TIMEOUT,
            routes=(StaticRouteSpec(method=METHOD_GET, url=RUN_PATH, replies=(in_progress,)),),
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "4243"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=MISSING_RUN_PATH, replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, str(RUN_ID)),
            usage=(command, str(RUN_ID), "--timeout-seconds", "soon"),
            credential=NO_CREDENTIAL,
            repository=NO_ORIGIN,
        ),
    )


def _get_logs_cases() -> Tuple[GoldenCase, ...]:
    command = "get-logs"
    return (
        GoldenCase(
            name=f"{command}/exit-0/archive-from-the-storage-host",
            argv=(command, str(RUN_ID)),
            stdout=printed_logs(entries=LOG_ENTRIES),
            exit_code=EXIT_OK,
            routes=LOGS_ON_STORAGE,
        ),
        GoldenCase(
            name=f"{command}/exit-0/failed-only",
            argv=(command, str(RUN_ID), "--failed-only"),
            stdout=printed_logs(entries=(FAILED_STEP_LOG,)),
            exit_code=EXIT_OK,
            routes=LOGS_ON_STORAGE,
        ),
        GoldenCase(
            name=f"{command}/exit-1/not-found",
            argv=(command, "4243"),
            stdout="",
            exit_code=EXIT_API_ERROR,
            routes=(StaticRouteSpec(method=METHOD_GET, url=f"{MISSING_RUN_PATH}/logs", replies=(NOT_FOUND,)),),
        ),
        *_refusal_cases(
            command=command,
            argv=(command, str(RUN_ID)),
            usage=(command,),
            credential=PLACEHOLDER_CREDENTIAL,
            repository=UNPARSEABLE_ORIGIN,
        ),
    )


#: The golden cases of the issues, claim, pull-request and CI subcommands of UB-1.1, and of each nested ``issue …``
#: spelling, every value the installed fork's own output.
CASES: Tuple[GoldenCase, ...] = (
    *_list_issues_cases(),
    *_get_issue_cases(),
    *_get_issue_comments_cases(),
    *_comment_issue_cases(),
    *_create_issue_cases(),
    *_update_issue_cases(),
    *_reopen_issue_cases(),
    *_checklist_cases(),
    *_claim_check_cases(words=("claim-check",), credential=NO_CREDENTIAL, repository=NO_GIT_CONFIG),
    *_claim_check_cases(
        words=(ISSUE_GROUP, "claim-check"), credential=PLACEHOLDER_CREDENTIAL, repository=FOREIGN_ORIGIN
    ),
    *_start_cases(words=("start-issue",), credential=TWO_TOKEN_CREDENTIAL, repository=NO_ORIGIN),
    *_start_cases(words=(ISSUE_GROUP, "start"), credential=EMPTY_CREDENTIAL, repository=UNPARSEABLE_ORIGIN),
    *_release_cases(words=("release-issue",), credential=PLACEHOLDER_CREDENTIAL, repository=NO_GIT_CONFIG),
    *_release_cases(words=(ISSUE_GROUP, "release"), credential=NO_CREDENTIAL, repository=FOREIGN_ORIGIN),
    *_label_add_cases(words=("label-add",), credential=EMPTY_CREDENTIAL, repository=NO_ORIGIN),
    *_label_add_cases(words=(ISSUE_GROUP, "label-add"), credential=TWO_TOKEN_CREDENTIAL, repository=UNPARSEABLE_ORIGIN),
    *_label_remove_cases(words=("label-remove",), credential=NO_CREDENTIAL, repository=UNPARSEABLE_ORIGIN),
    *_label_remove_cases(words=(ISSUE_GROUP, "label-remove"), credential=PLACEHOLDER_CREDENTIAL, repository=NO_ORIGIN),
    *_assign_cases(words=("assign",), credential=TWO_TOKEN_CREDENTIAL, repository=FOREIGN_ORIGIN),
    *_assign_cases(words=(ISSUE_GROUP, "assign"), credential=EMPTY_CREDENTIAL, repository=NO_GIT_CONFIG),
    *_create_pr_cases(),
    *_get_pr_cases(),
    *_get_pr_checks_cases(),
    *_approve_pr_cases(),
    *_merge_pr_cases(),
    *_delete_remote_branch_cases(),
    *_list_workflows_cases(),
    *_list_runs_cases(),
    *_get_run_cases(),
    *_wait_run_cases(),
    *_get_logs_cases(),
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
