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
* A request no route answers fails the test with ``pytest.fail``, which no ``except Exception`` swallows, and stays in
  ``unrouted`` for the teardown check.

A route named by a path is on ``https://api.github.com``; a route anywhere else is named by its absolute URL. An
endpoint is the scheme, the userinfo, the host, the port (the scheme's default when the URL names none) and the path,
so a request carrying userinfo never matches a route without it.
"""

from __future__ import annotations

import http.client
import importlib
import io
import json
import sys
import urllib.request
import urllib.response
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
