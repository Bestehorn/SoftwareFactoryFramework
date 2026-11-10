"""The GitHub wrapper's one request path: REST and GraphQL over a credential-stripping urllib opener.

``Transport`` sends every request through ``_send``, which refuses a URL off the origin the credential belongs to,
sets the headers ``conventions.md`` "Headers, media types and API versions" requires, waits out a rate limit a bounded
number of times, and turns every failure into a ``GitHubAPIError``. ``CredentialStrippingRedirectHandler`` follows a
redirect and drops ``Authorization`` when the target is on another origin (``origin``: scheme, host and port, parsed as
urllib connects with them), so a storage host never receives the token. Waiting is the injected ``sleep`` and time the
injected ``clock``, so a test waits for nothing.

Every value a response supplied that a message or a log line names (a URL, a bucket, a GraphQL error message) is
rendered with ``json.dumps``, and every URL a message names has its userinfo replaced first, so no credential and no
control character reaches stderr. The token itself is never logged.
"""

from __future__ import annotations

import http.client
import json
import logging
import re
import time
import urllib.request
from dataclasses import dataclass
from typing import IO, Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from github_api.errors import GitHubAPIError, GitHubGraphQLResponseError, GitHubRateLimitError

API_ROOT = "https://api.github.com"
GRAPHQL_URL = f"{API_ROOT}/graphql"
UPLOAD_ORIGIN = "https://uploads.github.com"  # conventions.md "Hosts and base URLs": the one other origin
ACCEPT_JSON = "application/vnd.github+json"
CONTENT_TYPE_JSON = "application/json"
USER_AGENT = "software-factory-github-wrapper/1.0"
API_VERSION_DEFAULT = "2022-11-28"
API_VERSION_NEXT = "2026-03-10"
API_VERSIONS = (API_VERSION_DEFAULT, API_VERSION_NEXT)

HEADER_ACCEPT = "Accept"
HEADER_AUTHORIZATION = "Authorization"
HEADER_USER_AGENT = "User-Agent"
HEADER_API_VERSION = "X-GitHub-Api-Version"
HEADER_CONTENT_TYPE = "Content-Type"
#: The only credential header the transport sets; a cross-origin redirect removes each of them.
CREDENTIAL_HEADERS = (HEADER_AUTHORIZATION,)

# Response headers, read case-insensitively (``Response.headers`` lower-cases their names).
HEADER_LINK = "link"
HEADER_RETRY_AFTER = "retry-after"
HEADER_RATE_REMAINING = "x-ratelimit-remaining"
HEADER_RATE_RESET = "x-ratelimit-reset"
HEADER_RATE_RESOURCE = "x-ratelimit-resource"

RATE_LIMIT_STATUSES = frozenset({403, 429})
RATE_LIMIT_MAX_RETRIES = 3
LIMIT_RETRY_AFTER = "the retry-after limit"
LIMIT_PRIMARY = "the primary rate limit"

FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_ERRORS = "errors"
FIELD_MESSAGE = "message"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"

QUERY_NAME = "name"
QUERY_LABEL = "label"

METHOD_GET = "GET"
METHOD_POST = "POST"
PATH_ROOT = "/"
PATH_PROTOCOL_RELATIVE = "//"
URI_TEMPLATE_START = "{"
ENCODING = "utf-8"
#: A ``link`` entry; ``rel`` may list several space-separated values, and a comma inside ``<...>`` splits nothing.
LINK_PATTERN = re.compile(r'<([^>]*)>\s*;\s*rel="([^"]*)"')
LINK_REL_NEXT = "next"
#: The authority of a URL as urllib's ``_splithost`` cuts it: after ``//``, up to the first ``/``, ``?`` or ``#``.
AUTHORITY_PATTERN = re.compile(r"//([^/?#]*)")
USERINFO_SEPARATOR = "@"
USERINFO_REDACTED = "***"
PORT_SEPARATOR = ":"
IPV6_CLOSE = "]"
IPV6_OPEN = "["
#: The port ``http.client`` connects to when a URL names none (``HTTPConnection.default_port``).
DEFAULT_PORTS = {"http": http.client.HTTP_PORT, "https": http.client.HTTPS_PORT}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Origin:
    """Where a request connects: the lower-cased scheme and host, and the port (the scheme's default when none)."""

    scheme: str
    host: str
    port: Optional[int]


@dataclass(frozen=True)
class Response:
    """One successful response: its status, its headers with lower-cased names, its body, and the URL it was sent to
    (never the redirect target, whose query may carry a storage signature)."""

    status: int
    headers: Dict[str, str]
    body: bytes
    url: str

    def json(self) -> Any:
        """The body parsed as JSON; ``None`` for an empty body, as the fork; ``GitHubAPIError`` when it is not JSON."""
        if not self.body:
            return None
        try:
            return json.loads(self.body.decode(ENCODING))
        except ValueError as error:
            raise GitHubAPIError(
                message=f"GitHub API {render_url(url=self.url)} returned a body that is not JSON",
                status_code=self.status,
            ) from error


@dataclass(frozen=True)
class _RateLimit:
    """A rate-limited answer the transport can wait out: the seconds to wait and the limit's name for a message."""

    seconds: float
    name: str


@dataclass(frozen=True)
class _ConnectionPage:
    """One page of a GraphQL connection: its nodes, whether another page follows, and the cursor that asks for it."""

    nodes: List[Any]
    has_next: bool
    end_cursor: Optional[str]


def render_url(*, url: str) -> str:
    """``url`` as a message names it: any userinfo replaced by ``***``, then quoted with ``json.dumps``."""
    match = AUTHORITY_PATTERN.search(url)
    if match is not None and USERINFO_SEPARATOR in match.group(1):
        host = match.group(1).rpartition(USERINFO_SEPARATOR)[2]
        url = f"{url[: match.start(1)]}{USERINFO_REDACTED}{USERINFO_SEPARATOR}{host}{url[match.end(1) :]}"
    return json.dumps(url)


def _split_port(*, authority: str, url: str) -> Tuple[str, Optional[int]]:
    """The host and port of ``authority``, split as ``http.client.HTTPConnection._get_hostport`` splits them: at the
    last ``:`` outside ``[...]``, an empty port counting as none, IPv6 brackets removed; a port that is not an integer
    raises ``GitHubAPIError`` naming ``url``."""
    colon = authority.rfind(PORT_SEPARATOR)
    if colon <= authority.rfind(IPV6_CLOSE):
        host, port_text = authority, ""
    else:
        host, port_text = authority[:colon], authority[colon + 1 :]
    if host.startswith(IPV6_OPEN) and host.endswith(IPV6_CLOSE):
        host = host[1:-1]
    if not port_text:
        return host, None
    try:
        return host, int(port_text)
    except ValueError:
        raise GitHubAPIError(message=f"Refusing {render_url(url=url)}: its port is not a number") from None


def origin(url: str) -> Origin:
    """The origin of ``url`` from the scheme and authority urllib's ``AbstractHTTPHandler.do_open`` connects with.

    A URL carrying userinfo has it in the host, so it never matches the API's origin; one whose port is not an integer
    (which the ``:`` of a ``user:password@`` part also yields) raises ``GitHubAPIError``.
    """
    try:
        request = urllib.request.Request(url=url)
    except ValueError:
        raise GitHubAPIError(message=f"Refusing {render_url(url=url)}: it is not an absolute URL") from None
    scheme = request.type.lower()
    host, port = _split_port(authority=request.host, url=url)
    return Origin(scheme=scheme, host=host.lower(), port=DEFAULT_PORTS.get(scheme) if port is None else port)


class CredentialStrippingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow a redirect as urllib does, removing every ``CREDENTIAL_HEADERS`` name when the target is on another
    origin than the request that received the redirect. A redirected request copies the headers of the hop it follows,
    so a credential removed once stays removed on every later hop, back on the API host too."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        redirected = super().redirect_request(req=req, fp=fp, code=code, msg=msg, headers=headers, newurl=newurl)
        # The origin of the request's own URL, never ``req.host``, which ``ProxyHandler`` rewrites to the proxy's.
        if redirected is not None and origin(url=redirected.full_url) != origin(url=req.full_url):
            for name in CREDENTIAL_HEADERS:
                # ``Request.add_header`` stores a name capitalized; ``remove_header`` drops it from both header maps.
                redirected.remove_header(header_name=name.capitalize())
        return redirected


def build_opener() -> urllib.request.OpenerDirector:
    """The transport's opener: urllib's defaults, with ``CredentialStrippingRedirectHandler`` for redirects."""
    return urllib.request.build_opener(CredentialStrippingRedirectHandler())


def _check_api_version(*, api_version: str) -> None:
    """Refuse an ``X-GitHub-Api-Version`` outside ``API_VERSIONS`` with ``ValueError``, before anything is sent."""
    if api_version not in API_VERSIONS:
        raise ValueError(f"Unsupported GitHub API version {json.dumps(api_version)}: use one of {list(API_VERSIONS)}")


def _api_url(*, path: str, query: Optional[Mapping[str, Any]]) -> str:
    """``API_ROOT`` + ``path``, plus ``query`` urlencoded; a path not root-relative raises ``GitHubAPIError``."""
    if not path.startswith(PATH_ROOT) or path.startswith(PATH_PROTOCOL_RELATIVE):
        raise GitHubAPIError(message=f"Refusing a GitHub API path that is not root-relative: {render_url(url=path)}")
    encoded = urlencode(query=query, doseq=True) if query else ""
    return f"{API_ROOT}{path}?{encoded}" if encoded else f"{API_ROOT}{path}"


def _headers_of(*, message: Any) -> Dict[str, str]:
    """A response's headers with lower-cased names; a name sent twice has its values joined as ``getheader`` joins."""
    headers: Dict[str, str] = {}
    for name, value in message.items():
        key = str(name).lower()
        headers[key] = f"{headers[key]}, {value}" if key in headers else str(value)
    return headers


def _http_error_details(*, error: HTTPError) -> Any:
    """GitHub's error body of ``error`` parsed as JSON (``basic-error``, ``validation-error``); ``None`` when it cannot
    be read or parsed, so that no failure to read the body replaces the error it belongs to (the fork's)."""
    try:
        return json.loads(error.read().decode(ENCODING))
    except (ValueError, OSError, http.client.HTTPException):
        return None


def _integer_header(*, value: Optional[str]) -> Optional[int]:
    """A header's integer value; ``None`` when the header is absent; ``ValueError`` when it is not an integer."""
    return None if value is None else int(value)


def _limit_name(*, resource: Optional[str], kind: str) -> str:
    """How a message names a limit: the ``x-ratelimit-resource`` bucket when sent, else the kind of limit."""
    return kind if resource is None else f"the {json.dumps(resource)} rate limit"


def _rate_limit_of(*, error: HTTPError, now: float) -> Optional[_RateLimit]:
    """The wait a rate-limited ``error`` asks for (``conventions.md`` "When limited"): ``retry-after`` seconds, else
    until ``x-ratelimit-reset`` when ``x-ratelimit-remaining`` is ``0``. ``None`` for any other error, including a
    ``403``/``429`` without those headers or with a rate header that is not an integer."""
    if error.code not in RATE_LIMIT_STATUSES:
        return None
    headers = error.headers
    try:
        retry_after = _integer_header(value=headers.get(HEADER_RETRY_AFTER))
        remaining = _integer_header(value=headers.get(HEADER_RATE_REMAINING))
        reset = _integer_header(value=headers.get(HEADER_RATE_RESET))
    except ValueError:
        return None
    resource = headers.get(HEADER_RATE_RESOURCE)
    if retry_after is not None:
        return _RateLimit(
            seconds=float(max(0, retry_after)), name=_limit_name(resource=resource, kind=LIMIT_RETRY_AFTER)
        )
    if remaining == 0 and reset is not None:
        return _RateLimit(seconds=max(0.0, reset - now), name=_limit_name(resource=resource, kind=LIMIT_PRIMARY))
    return None


def _http_failure(*, method: str, url: str, error: HTTPError, limit: Optional[_RateLimit]) -> GitHubAPIError:
    """The error an unretried ``HTTPError`` raises: ``GitHubRateLimitError`` once a limit's retries are spent, else
    ``GitHubAPIError``; each with the status and the parsed error body."""
    failed = f"GitHub API {method} {render_url(url=url)} failed: HTTP {error.code}"
    details = _http_error_details(error=error)
    if limit is None:
        return GitHubAPIError(message=failed, status_code=error.code, details=details)
    return GitHubRateLimitError(
        message=f"{failed}; {limit.name} still applied after {RATE_LIMIT_MAX_RETRIES} retries",
        status_code=error.code,
        details=details,
    )


def _next_url(*, link: Optional[str]) -> Optional[str]:
    """The ``rel="next"`` target of a ``link`` header, exactly as given; ``None`` when there is no header or no next."""
    for match in LINK_PATTERN.finditer(link or ""):
        if LINK_REL_NEXT in match.group(2).split():
            return match.group(1)
    return None


def _items_of(*, page: Any, item_key: Optional[str], url: str) -> List[Any]:
    """A page's items: the page itself, or the list under ``item_key``; a page without its list raises."""
    if item_key is None:
        items = page
    elif isinstance(page, dict):
        items = page.get(item_key)
    else:
        items = None
    if not isinstance(items, list):
        where = "" if item_key is None else f" under {json.dumps(item_key)}"
        raise GitHubAPIError(message=f"GitHub API {METHOD_GET} {render_url(url=url)} returned no item list{where}")
    return items


def _graphql_data(*, response: Response) -> Any:
    """The ``data`` of a GraphQL response; a top-level ``errors`` key raises ``GitHubGraphQLResponseError``."""
    parsed = response.json()
    if not isinstance(parsed, dict):
        raise GitHubAPIError(
            message=f"GitHub GraphQL {render_url(url=response.url)} returned no JSON object",
            status_code=response.status,
        )
    if FIELD_ERRORS in parsed:
        errors = parsed[FIELD_ERRORS]
        first = errors[0] if isinstance(errors, list) and errors else None
        message = first.get(FIELD_MESSAGE) if isinstance(first, dict) else None
        raise GitHubGraphQLResponseError(
            message=f"GitHub GraphQL {render_url(url=response.url)} returned errors: {json.dumps(message)}",
            status_code=response.status,
            details=errors,
        )
    return parsed.get(FIELD_DATA)


def _no_connection(*, connection: Sequence[str]) -> GitHubAPIError:
    """The error for a GraphQL page whose connection, its ``nodes``, its ``pageInfo`` or its next cursor is missing."""
    return GitHubAPIError(message=f"GitHub GraphQL response has no connection at {json.dumps(list(connection))}")


def _connection_page(*, data: Any, connection: Sequence[str]) -> _ConnectionPage:
    """The connection at the key path ``connection`` under ``data``; a missing level or page field raises."""
    node = data
    for key in connection:
        if not isinstance(node, dict) or not isinstance(node.get(key), dict):
            raise _no_connection(connection=connection)
        node = node[key]
    nodes = node.get(FIELD_NODES)
    page_info = node.get(FIELD_PAGE_INFO)
    if not isinstance(nodes, list) or not isinstance(page_info, dict):
        raise _no_connection(connection=connection)
    has_next = page_info.get(FIELD_HAS_NEXT_PAGE) is True
    end_cursor = page_info.get(FIELD_END_CURSOR)
    if has_next and not isinstance(end_cursor, str):
        raise _no_connection(connection=connection)
    return _ConnectionPage(nodes=nodes, has_next=has_next, end_cursor=end_cursor)


class Transport:
    """Sends the wrapper's GitHub requests with one token: REST calls, ``link`` pages, uploads, downloads, GraphQL."""

    def __init__(
        self,
        token: str,
        *,
        opener: Optional[urllib.request.OpenerDirector] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._token = token
        self._opener = build_opener() if opener is None else opener
        self._sleep = sleep
        self._clock = clock

    def request(
        self,
        *,
        method: str,
        path: str,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
        api_version: str = API_VERSION_DEFAULT,
        accept: str = ACCEPT_JSON,
    ) -> Response:
        """One REST call to ``API_ROOT`` + ``path``; any ``body`` but ``None`` is sent as JSON, on ``DELETE`` too."""
        _check_api_version(api_version=api_version)
        url = _api_url(path=path, query=query)
        data = None if body is None else json.dumps(body).encode(ENCODING)
        headers = {HEADER_ACCEPT: accept}
        if data is not None:
            headers[HEADER_CONTENT_TYPE] = CONTENT_TYPE_JSON
        return self._send(
            method=method, url=url, data=data, headers=headers, api_version=api_version, allowed_origin=API_ROOT
        )

    def pages(
        self,
        *,
        path: str,
        query: Optional[Mapping[str, Any]] = None,
        item_key: Optional[str] = None,
        api_version: str = API_VERSION_DEFAULT,
    ) -> Iterator[Any]:
        """The items of every page of a list, in page order, following each ``rel="next"`` target as given. The API
        version and the path are checked here, so a refusal comes before anything is sent."""
        _check_api_version(api_version=api_version)
        return self._page_items(url=_api_url(path=path, query=query), item_key=item_key, api_version=api_version)

    def upload(
        self, *, upload_url: str, name: str, data: bytes, media_type: str, label: Optional[str] = None
    ) -> Response:
        """``POST`` a release asset to ``upload_url`` cut at its ``{?name,label}`` template, ``name`` (and ``label``)
        as the query, the bytes as the body and ``media_type`` as ``Content-Type``; only ``UPLOAD_ORIGIN`` receives
        it."""
        query = {QUERY_NAME: name} if label is None else {QUERY_NAME: name, QUERY_LABEL: label}
        url = f"{upload_url.split(URI_TEMPLATE_START, 1)[0]}?{urlencode(query=query)}"
        headers = {HEADER_ACCEPT: ACCEPT_JSON, HEADER_CONTENT_TYPE: media_type}
        return self._send(
            method=METHOD_POST,
            url=url,
            data=data,
            headers=headers,
            api_version=API_VERSION_DEFAULT,
            allowed_origin=UPLOAD_ORIGIN,
        )

    def download(self, *, path: str) -> bytes:
        """A REST ``GET`` returning the body's bytes; a redirect to a storage host is followed without the token."""
        response = self._send(
            method=METHOD_GET,
            url=_api_url(path=path, query=None),
            data=None,
            headers={HEADER_ACCEPT: ACCEPT_JSON},
            api_version=API_VERSION_DEFAULT,
            allowed_origin=API_ROOT,
        )
        return response.body

    def graphql(self, *, document: str, variables: Mapping[str, Any]) -> Any:
        """``POST`` ``{"query": document, "variables": variables}`` to ``GRAPHQL_URL`` and return its ``data``; no
        ``X-GitHub-Api-Version`` (``graphql/conventions.md`` documents it for REST only)."""
        payload = {FIELD_QUERY: document, FIELD_VARIABLES: dict(variables)}
        response = self._send(
            method=METHOD_POST,
            url=GRAPHQL_URL,
            data=json.dumps(payload).encode(ENCODING),
            headers={HEADER_ACCEPT: ACCEPT_JSON, HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON},
            api_version=None,
            allowed_origin=API_ROOT,
        )
        return _graphql_data(response=response)

    def graphql_nodes(self, *, document: str, variables: Mapping[str, Any], connection: Sequence[str]) -> Iterator[Any]:
        """The nodes of every page of the connection at the key path ``connection`` under ``data``, in page order:
        the first call sends ``after: null``, each next one the previous ``endCursor``, while ``hasNextPage``."""
        after: Optional[str] = None
        while True:
            data = self.graphql(document=document, variables={**variables, FIELD_AFTER: after})
            page = _connection_page(data=data, connection=connection)
            yield from page.nodes
            if not page.has_next:
                return
            after = page.end_cursor

    def _page_items(self, *, url: str, item_key: Optional[str], api_version: str) -> Iterator[Any]:
        next_url: Optional[str] = url
        while next_url is not None:
            response = self._send(
                method=METHOD_GET,
                url=next_url,
                data=None,
                headers={HEADER_ACCEPT: ACCEPT_JSON},
                api_version=api_version,
                allowed_origin=API_ROOT,
            )
            yield from _items_of(page=response.json(), item_key=item_key, url=next_url)
            next_url = _next_url(link=response.headers.get(HEADER_LINK))

    def _build_request(
        self, *, method: str, url: str, data: Optional[bytes], headers: Mapping[str, str], api_version: Optional[str]
    ) -> urllib.request.Request:
        """A fresh request per attempt, so no redirect state of an earlier attempt carries over. ``Authorization`` is
        added with ``add_header``, so the redirect handler decides whether a redirected request keeps it."""
        request = urllib.request.Request(url=url, data=data, method=method)
        for name, value in headers.items():
            request.add_header(key=name, val=value)
        request.add_header(key=HEADER_AUTHORIZATION, val=f"Bearer {self._token}")
        request.add_header(key=HEADER_USER_AGENT, val=USER_AGENT)
        if api_version is not None:
            request.add_header(key=HEADER_API_VERSION, val=api_version)
        return request

    def _open(self, *, request: urllib.request.Request, url: str) -> Response:
        with self._opener.open(request) as answer:
            return Response(
                status=answer.getcode(), headers=_headers_of(message=answer.headers), body=answer.read(), url=url
            )

    def _send(
        self,
        *,
        method: str,
        url: str,
        data: Optional[bytes],
        headers: Mapping[str, str],
        api_version: Optional[str],
        allowed_origin: str,
    ) -> Response:
        """The one send. ``api_version`` is the ``X-GitHub-Api-Version`` of a REST request, ``None`` for GraphQL;
        ``allowed_origin`` is the root whose origin alone may receive the token (``API_ROOT`` or ``UPLOAD_ORIGIN``)."""
        if origin(url=url) != origin(url=allowed_origin):
            raise GitHubAPIError(
                message=f"Refusing to send the GitHub credential to {render_url(url=url)}: not on {allowed_origin}"
            )
        retries = 0
        while True:
            request = self._build_request(method=method, url=url, data=data, headers=headers, api_version=api_version)
            try:
                return self._open(request=request, url=url)
            except HTTPError as error:
                limit = _rate_limit_of(error=error, now=self._clock())
                if limit is None or retries >= RATE_LIMIT_MAX_RETRIES:
                    raise _http_failure(method=method, url=url, error=error, limit=limit) from error
                retries += 1
                logger.warning(
                    "GitHub API %s %s hit %s: waiting %s seconds before retry %d of %d",
                    method,
                    render_url(url=url),
                    limit.name,
                    limit.seconds,
                    retries,
                    RATE_LIMIT_MAX_RETRIES,
                )
                self._sleep(limit.seconds)  # positional: time.sleep takes its seconds positional-only
            except URLError as error:
                raise GitHubAPIError(
                    message=f"GitHub API {method} {render_url(url=url)} failed: {json.dumps(str(error.reason))}"
                ) from error
            except (ValueError, http.client.InvalidURL):
                # Raised while urllib resolves or opens a redirect's Location; its text may hold that URL's userinfo.
                raise GitHubAPIError(
                    message=f"GitHub API {method} {render_url(url=url)} failed: a redirect named an unusable URL"
                ) from None
