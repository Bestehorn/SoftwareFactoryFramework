"""The one request path of the GitLab wrapper: REST v4 and GraphQL over ``urllib`` (issue #13, design.md D4).

``Transport`` applies ``docs/api-reference/gitlab/conventions.md`` and ``graphql/conventions.md`` once, for every
operation record:

- the token travels in exactly one header, the configured ``TokenType``'s (AC-2.1), and only to the configured
  origin: ``_send`` refuses a URL on any other origin before sending it, and ``CredentialStrippingRedirectHandler``
  drops every credential header on a redirect to another origin, for every later hop as well (AC-3.1);
- query and form pairs keep their brackets literal and send ``+`` as ``%2B`` (AC-2.3); a JSON body is native JSON; a
  file makes the body ``multipart/form-data`` (AC-2.4); ``request_raw`` sends a raw body's bytes unchanged under the
  given ``Content-Type`` (#40 AC-3.2);
- ``pages`` follows offset paging by ``Link`` ``rel="next"`` or ``x-next-page`` and keyset paging by ``Link`` only,
  never by ``x-total-pages`` (AC-2.5, AC-2.6);
- a ``429`` waits ``Retry-After`` seconds, else backs off exponentially, and raises ``GitLabRateLimitError`` when the
  retries are spent (AC-3.2 to AC-3.4); any other error status raises ``GitLabAPIError`` carrying the status, the raw
  body and the text of the body's shape (AC-3.5);
- ``graphql`` POSTs ``{"query", "variables"}`` to ``/api/graphql`` and raises on GraphQL errors at HTTP ``200``;
  ``graphql_nodes`` pages a connection by ``pageInfo.endCursor`` (AC-4.1 to AC-4.3);
- ``graphql`` given files sends the multipart GraphQL request of ``graphql/conventions.md`` "File uploads", one
  ``multipart/form-data`` POST: the parts ``operations`` and ``map``, then one part per file (issue #44 D4, AC-3.1).

The token never enters a URL, a log record or an exception message. It comes from ``config/gitlab.json`` through
``Transport.from_config`` (the config keys are the ``FIELD_*`` constants below); nothing here reads the process
environment. Standard library only; Python 3.9.
"""

from __future__ import annotations

import http.client
import json
import logging
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

from gitlab_api.errors import GitLabAPIError, GitLabGraphQLResponseError, GitLabRateLimitError
from gitlab_api.registry import Paging, Pair

LOGGER = logging.getLogger(__name__)

# --- Constants ----------------------------------------------------------------------------------------------------

# The keys of config/gitlab.json (templates/config/gitlab.json.template; design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # nosec B105 — a config field name, not a secret
FIELD_TOKEN_TYPE = "token_type"  # nosec B105 — a config field name, not a secret
FIELD_IN_PROGRESS_LABEL = "in_progress_label"

HEADER_AUTHORIZATION = "Authorization"
BEARER_PREFIX = "Bearer "

HEADER_ACCEPT = "Accept"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "Content-Disposition"
HEADER_RETRY_AFTER = "Retry-After"
HEADER_LINK = "Link"
HEADER_NEXT_PAGE = "x-next-page"

CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"
DECODE_ERRORS = "replace"

METHOD_GET = "GET"
METHOD_HEAD = "HEAD"
METHOD_POST = "POST"
# A redirect of any other method is not followed, so a POST never turns into a GET (design.md D4 "Redirects").
FOLLOWED_REDIRECT_METHODS = frozenset({METHOD_GET, METHOD_HEAD})

REST_BASE_TEMPLATE = "https://{host}/api/v4"
GRAPHQL_URL_TEMPLATE = "https://{host}/api/graphql"
REST_PATH_PREFIX = "/"
# The scheme's default port, as `http.client` connects (`HTTPConnection.default_port`); any other scheme has none.
DEFAULT_PORTS: Dict[str, int] = {"https": http.client.HTTPS_PORT, "http": http.client.HTTP_PORT}
PORT_SEPARATOR = ":"
IPV6_CLOSE = "]"

# conventions.md "Arrays, hashes and arrays of hashes" and "`+` in dates": brackets literal, `+` as %2B.
QUERY_SAFE = "[]"
PARAM_PER_PAGE = "per_page"
PARAM_PAGE = "page"
# conventions.md "Offset-based": `per_page` is at most 100.
MAX_PER_PAGE = 100
# `<url>; rel="next"`: a comma inside the URL does not split it (design.md D4 `pages`).
LINK_RELATION = re.compile(pattern=r'<([^>]*)>\s*;\s*rel="([^"]*)"')
LINK_GROUP_URL = 1
LINK_GROUP_REL = 2
REL_NEXT = "next"

# conventions.md "Headers and the 429 response": wait `Retry-After` seconds, else back off exponentially.
# Five retries at a 2-second base wait 2, 4, 8, 16 and 32 seconds: past a one-minute quota window in total.
RATE_LIMIT_MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2.0
RETRY_AFTER_SECONDS = re.compile(pattern=r"[0-9]+")
REQUEST_TIMEOUT_SECONDS = 30

# RFC 2046 section 5.1.1 allows a boundary of at most 70 characters; 16 bytes are 32 hexadecimal digits.
MULTIPART_BOUNDARY_BYTES = 16
MULTIPART_DASHES = b"--"
CRLF = b"\r\n"
# The HTML multipart/form-data encoding of a field or file name (https://html.spec.whatwg.org/#multipart-form-data).
MULTIPART_NAME_ESCAPES = str.maketrans({'"': "%22", "\r": "%0D", "\n": "%0A"})

# Response keys: the REST error body shapes (conventions.md "Body shapes") and GraphQL (graphql/conventions.md).
FIELD_MESSAGE = "message"
FIELD_ERROR = "error"
FIELD_ERROR_DESCRIPTION = "error_description"
FIELD_SCOPE = "scope"
FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_ERRORS = "errors"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"
# graphql/conventions.md "File uploads": the form parts before the files, the i-th file's part named `str(i)`.
PART_OPERATIONS = "operations"
PART_MAP = "map"
# A document whose operation is a mutation: its keyword first, after the insignificant characters and comments of the
# GraphQL grammar (white space, commas, the byte order mark, `#` comments).
MUTATION_DOCUMENT = re.compile(pattern=r"\A(?:[\s,\ufeff]|#[^\n\r]*)*mutation\b")
MESSAGE_SEPARATOR = "; "
LIST_SEPARATOR = ", "


# --- Credentials and origins --------------------------------------------------------------------------------------


class TokenType(Enum):
    """The configured ``token_type`` (``config/gitlab.json``): which one header carries the token (AC-2.1)."""

    PRIVATE = "private"
    BEARER = "bearer"
    JOB = "job"


# conventions.md "Credential types and how to send them": the header each token type sends, as documented, and the
# text before the token.
TOKEN_HEADERS: Dict[TokenType, Tuple[str, str]] = {
    TokenType.PRIVATE: ("PRIVATE-TOKEN", ""),
    TokenType.BEARER: (HEADER_AUTHORIZATION, BEARER_PREFIX),
    TokenType.JOB: ("JOB-TOKEN", ""),
}
# Every credential header, spelled as `Request.add_header` stores a name (`str.capitalize`: `Private-token`,
# `Authorization`, `Job-token`) and as `Request.remove_header` matches it. Derived from TOKEN_HEADERS, so a header a
# token type sends cannot be missing from what a cross-origin redirect strips.
CREDENTIAL_HEADERS = tuple(name.capitalize() for name, _ in TOKEN_HEADERS.values())


def token_type_of(*, value: Union[TokenType, str]) -> TokenType:
    """A ``TokenType`` member, or the member whose value is the config string; another value raises."""
    try:
        return TokenType(value)
    except ValueError:
        accepted = LIST_SEPARATOR.join(member.value for member in TokenType)
        raise GitLabAPIError(f"token_type {value!r} is not one of {accepted}") from None


def credential_header(*, token_type: TokenType, token: str) -> Tuple[str, str]:
    """The one header name and value that carry ``token`` for ``token_type``."""
    name, prefix = TOKEN_HEADERS[token_type]
    return name, prefix + token


@dataclass(frozen=True)
class Origin:
    """The scheme, lower-cased host and port a URL connects to; two URLs share an origin only when all three match."""

    scheme: str
    host: str
    port: Optional[int]

    def __str__(self) -> str:
        return f"{self.scheme}://{self.host}{PORT_SEPARATOR}{self.port}"


def _port(*, url: str, scheme: str, text: str) -> Optional[int]:
    """The port after the authority's last ``:``; empty or absent is the scheme's default (``None`` for others)."""
    if not text:
        return DEFAULT_PORTS.get(scheme)
    try:
        return int(text)
    except ValueError:
        raise GitLabAPIError(f"the URL {url} has the port {text!r}, which is not an integer") from None


def origin(*, url: str) -> Origin:
    """The origin of ``url``, parsed as urllib connects to it (design.md D4 "URLs and origin").

    ``Request(url=url)`` gives the scheme (``type``) and the authority (``host``) that
    ``AbstractHTTPHandler.do_open`` connects with; the port is split after the last ``:`` outside ``[...]``, as
    ``http.client.HTTPConnection`` splits it. ``https://<host>@evil.example/`` therefore has the host
    ``<host>@evil.example``. A URL urllib cannot open and a port that is not an integer raise ``GitLabAPIError``."""
    try:
        request = urllib.request.Request(url=url)
    except ValueError:
        raise GitLabAPIError(f"the URL {url} has no scheme and host urllib can open") from None
    authority = request.host or ""
    port_text = ""
    separator = authority.rfind(PORT_SEPARATOR)
    if separator > authority.rfind(IPV6_CLOSE):
        authority, port_text = authority[:separator], authority[separator + 1 :]
    scheme = request.type.lower()
    return Origin(scheme=scheme, host=authority.lower(), port=_port(url=url, scheme=scheme, text=port_text))


class CredentialStrippingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follows a ``GET`` or ``HEAD`` redirect, without the credential when the target is on another origin.

    The parent copies the headers of the hop it follows, so a credential removed on one hop stays absent on every later
    hop, back on the configured host too; a same-origin hop (a moved project's ``301``) keeps it. The origins compared
    are the target's and that of ``req.full_url``, the request that received the redirect — never ``req.host``, which
    ``ProxyHandler`` rewrites to the proxy's. Sources: Python docs ``HTTPRedirectHandler.redirect_request`` and
    ``Request.remove_header``; ``conventions.md`` "Do not forward the token"."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        if req.get_method() not in FOLLOWED_REDIRECT_METHODS:
            raise urllib.error.HTTPError(url=req.full_url, code=code, msg=msg, hdrs=headers, fp=fp)
        followed = super().redirect_request(req=req, fp=fp, code=code, msg=msg, headers=headers, newurl=newurl)
        if followed is not None and origin(url=followed.full_url) != origin(url=req.full_url):
            for name in CREDENTIAL_HEADERS:
                followed.remove_header(header_name=name)
        return followed


# --- Responses and error text -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Response:
    """One response: its status, headers and raw body; ``value`` decodes it (``conventions.md`` "Responses")."""

    status: int
    headers: Message
    body: bytes

    @property
    def text(self) -> str:
        """The body as text."""
        return self.body.decode(encoding=TEXT_ENCODING, errors=DECODE_ERRORS)

    @property
    def is_json(self) -> bool:
        """Whether the ``Content-Type``'s media type is ``application/json`` (issue #41, design.md D2).

        ``get_content_type`` lower-cases the type and drops its parameters, so ``application/json; charset=utf-8`` is
        JSON, and reads an absent header as ``text/plain`` (Python docs, ``email.message.Message``)."""
        return self.headers.get_content_type() == CONTENT_TYPE_JSON

    @property
    def value(self) -> Any:
        """JSON when the ``Content-Type`` is JSON, the text otherwise (a job trace), ``None`` when the body is empty."""
        if not self.body:
            return None
        if not self.is_json:
            return self.text
        try:
            return json.loads(s=self.text)
        except ValueError:
            raise GitLabAPIError(
                "the response claims JSON but its body is not valid JSON", status_code=self.status, details=self.text
            ) from None


def _succeeded(*, status: int) -> bool:
    return HTTPStatus.OK <= status < HTTPStatus.MULTIPLE_CHOICES


def error_messages(*, errors: Any) -> List[str]:
    """The messages of an ``errors`` list: each entry's ``message``, or the entry itself when it is a string."""
    if not isinstance(errors, list):
        return []
    return [str(item.get(FIELD_MESSAGE, item)) if isinstance(item, Mapping) else str(item) for item in errors]


def _flattened(*, prefix: str, value: Any) -> Iterator[Tuple[str, str]]:
    """``(field, message)`` pairs of a validation hash: nested hashes with dotted names, lists joined."""
    if isinstance(value, Mapping):
        for key, entry in value.items():
            yield from _flattened(prefix=f"{prefix}.{key}" if prefix else str(key), value=entry)
    elif isinstance(value, list):
        yield prefix, LIST_SEPARATOR.join(str(item) for item in value)
    else:
        yield prefix, str(value)


def _message_text(*, message: Any) -> str:
    """``message`` as a string is itself; as a hash (validation, the spam hash) its ``field: message`` pairs."""
    if isinstance(message, str):
        return message
    if isinstance(message, Mapping):
        return MESSAGE_SEPARATOR.join(f"{name}: {text}" for name, text in _flattened(prefix="", value=message))
    return ""


def _error_field_text(*, decoded: Mapping[str, Any]) -> str:
    """``error`` with its optional ``error_description`` (``error: description``); the OAuth scope error adds its
    ``scope``."""
    error = decoded.get(FIELD_ERROR)
    if not isinstance(error, str):
        return ""
    description = decoded.get(FIELD_ERROR_DESCRIPTION)
    text = f"{error}: {description}" if description else error
    scope = decoded.get(FIELD_SCOPE)
    return f"{text} (scope: {scope})" if scope else text


def error_text(*, body: str) -> str:
    """The error text of a response body, for each ``conventions.md`` "Body shapes" entry (AC-3.5).

    ``message`` as a string or a field hash; ``error`` with ``error_description``; a GraphQL ``errors`` list; anything
    else, a non-JSON body included, is the body itself."""
    try:
        decoded = json.loads(s=body)
    except ValueError:
        return body
    if not isinstance(decoded, Mapping):
        return body
    return (
        _message_text(message=decoded.get(FIELD_MESSAGE))
        or _error_field_text(decoded=decoded)
        or MESSAGE_SEPARATOR.join(error_messages(errors=decoded.get(FIELD_ERRORS)))
        or body
    )


def graphql_error_messages(*, body: Mapping[str, Any], document: str) -> List[str]:
    """The top-level ``errors`` messages and, for a mutation, those of every ``data`` payload's ``errors`` list.

    A query's object may have a field named ``errors`` (``ciConfig``): that is data, so only a mutation's payloads are
    read (``graphql/conventions.md`` "Errors and partial data")."""
    messages = error_messages(errors=body.get(FIELD_ERRORS))
    data = body.get(FIELD_DATA)
    if isinstance(data, Mapping) and MUTATION_DOCUMENT.match(string=document):
        for payload in data.values():
            if isinstance(payload, Mapping):
                messages.extend(error_messages(errors=payload.get(FIELD_ERRORS)))
    return messages


def retry_seconds(*, headers: Message, retry: int) -> float:
    """The wait before the ``retry``-th consecutive retry of a ``429``: an integer ``Retry-After``, else
    ``BACKOFF_BASE_SECONDS * 2 ** (retry - 1)``."""
    value = str(headers.get(HEADER_RETRY_AFTER) or "").strip()
    if RETRY_AFTER_SECONDS.fullmatch(string=value):
        return float(value)
    return BACKOFF_BASE_SECONDS * 2 ** (retry - 1)


def link_next(*, headers: Message) -> Optional[str]:
    """The ``Link`` header's ``rel="next"`` URL as given, or ``None``."""
    for value in headers.get_all(HEADER_LINK) or []:
        for match in LINK_RELATION.finditer(string=str(value)):
            url = match.group(LINK_GROUP_URL)
            if url and REL_NEXT in match.group(LINK_GROUP_REL).split():
                return str(url)
    return None


# --- Request bodies -----------------------------------------------------------------------------------------------


def join_pairs(*, pairs: Sequence[Pair]) -> str:
    """Name-value pairs joined for a query string or a form body: brackets literal, ``+`` as ``%2B``."""
    return urllib.parse.urlencode(query=list(pairs), safe=QUERY_SAFE, quote_via=urllib.parse.quote)


def multipart_name(*, text: str) -> str:
    """A field or file name with ``"``, CR and LF written as ``%22``, ``%0D`` and ``%0A``."""
    return text.translate(MULTIPART_NAME_ESCAPES)


def _part(*, headers: Sequence[str], content: bytes) -> bytes:
    return CRLF.join(line.encode(encoding=TEXT_ENCODING) for line in headers) + CRLF + CRLF + content


def _form_part(*, name: str, value: str) -> bytes:
    disposition = f'{HEADER_CONTENT_DISPOSITION}: form-data; name="{multipart_name(text=name)}"'
    return _part(headers=(disposition,), content=value.encode(encoding=TEXT_ENCODING))


def _file_part(*, name: str, path: Path) -> bytes:
    """The part of one file: its field name, the given object's ``name`` as the file name, its bytes unchanged."""
    try:
        content = path.read_bytes()
    except OSError as error:
        raise GitLabAPIError(f"cannot read the file {path} sent as {name!r}: {error}") from error
    disposition = (
        f'{HEADER_CONTENT_DISPOSITION}: form-data; name="{multipart_name(text=name)}"; '
        f'filename="{multipart_name(text=path.name)}"'
    )
    return _part(headers=(disposition, f"{HEADER_CONTENT_TYPE}: {CONTENT_TYPE_OCTET_STREAM}"), content=content)


def multipart_body(*, form: Sequence[Pair], files: Sequence[Tuple[str, Path]], boundary: str) -> bytes:
    """A ``multipart/form-data`` body (RFC 7578): one part per form pair, then one per file."""
    delimiter = MULTIPART_DASHES + boundary.encode(encoding=ASCII_ENCODING)
    parts = [_form_part(name=name, value=value) for name, value in form]
    parts.extend(_file_part(name=name, path=path) for name, path in files)
    return b"".join(delimiter + CRLF + part + CRLF for part in parts) + delimiter + MULTIPART_DASHES + CRLF


def request_body(
    *, form: Sequence[Pair], json_body: Any, files: Sequence[Tuple[str, Path]]
) -> Tuple[Optional[bytes], Optional[str]]:
    """The body and its ``Content-Type``: multipart with a file, a form body with form pairs, JSON with a JSON body,
    else none. A JSON body beside form pairs or files raises ``ValueError``."""
    if json_body is not None and (form or files):
        raise ValueError("a request carries either a JSON body or form values and files, not both")
    if files:
        boundary = secrets.token_hex(nbytes=MULTIPART_BOUNDARY_BYTES)
        body = multipart_body(form=form, files=files, boundary=boundary)
        return body, f"{CONTENT_TYPE_MULTIPART}; boundary={boundary}"
    if form:
        return join_pairs(pairs=form).encode(encoding=ASCII_ENCODING), CONTENT_TYPE_FORM
    if json_body is not None:
        return json.dumps(obj=json_body).encode(encoding=TEXT_ENCODING), CONTENT_TYPE_JSON
    return None, None


def _build_request(
    *, method: str, url: str, data: Optional[bytes], content_type: Optional[str], credential: Tuple[str, str]
) -> urllib.request.Request:
    """A request carrying ``Accept``, its ``Content-Type`` and the credential, all set with ``add_header`` so the
    redirect handler decides on the credential at every hop."""
    request = urllib.request.Request(url=url, data=data, method=method)
    request.add_header(key=HEADER_ACCEPT, val=CONTENT_TYPE_JSON)
    if data is not None and content_type:
        request.add_header(key=HEADER_CONTENT_TYPE, val=content_type)
    name, value = credential
    request.add_header(key=name, val=value)
    return request


def _error_response(*, error: urllib.error.HTTPError) -> Response:
    """The response an ``HTTPError`` carries: its status, headers and body."""
    try:
        body = error.read()
    except (OSError, http.client.HTTPException):
        body = b""
    finally:
        error.close()
    return Response(status=error.code, headers=error.headers, body=body)


def _page_items(*, response: Response, url: str) -> List[Any]:
    value = response.value
    if not isinstance(value, list):
        raise GitLabAPIError(
            f"{METHOD_GET} {url} answered a page that is not a JSON array",
            status_code=response.status,
            details=response.text,
        )
    return value


def _connection(*, data: Any, connection: Sequence[str]) -> Mapping[str, Any]:
    """The connection object at the key path ``connection`` under ``data``; a ``null`` on the way raises."""
    node: Any = data
    for key in connection:
        node = node.get(key) if isinstance(node, Mapping) else None
    if not isinstance(node, Mapping):
        raise GitLabAPIError(f"the GraphQL connection {'.'.join(connection)} is absent or forbidden")
    return node


# --- The transport ------------------------------------------------------------------------------------------------


class Transport:
    """REST v4 and GraphQL requests to one GitLab host with one credential (design.md D4).

    ``sleep`` and ``clock`` are kept public for the callers that wait (``pipeline wait``); a test passes a recording
    ``sleep`` and a fixed ``clock``. ``opener`` defaults to the module's only opener, which follows redirects through
    ``CredentialStrippingRedirectHandler``."""

    def __init__(
        self,
        *,
        host: str,
        token: str,
        token_type: Union[TokenType, str],
        opener: Optional[urllib.request.OpenerDirector] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.host = host
        self.token_type = token_type_of(value=token_type)
        self.sleep = sleep
        self.clock = clock
        self._token = token
        self._credential = credential_header(token_type=self.token_type, token=token)
        self._opener = (
            opener if opener is not None else urllib.request.build_opener(CredentialStrippingRedirectHandler())
        )
        self._rest_base = REST_BASE_TEMPLATE.format(host=host)
        self._graphql_url = GRAPHQL_URL_TEMPLATE.format(host=host)
        self._origin = origin(url=self._rest_base)

    @classmethod
    def from_config(cls, *, config: Mapping[str, Any]) -> Transport:
        """The transport of a loaded ``config/gitlab.json``; an absent or empty ``token_type`` is ``private``."""
        return cls(
            host=str(config[FIELD_HOSTNAME]),
            token=str(config[FIELD_TOKEN]),
            token_type=str(config.get(FIELD_TOKEN_TYPE) or TokenType.PRIVATE.value),
        )

    # --- REST ---

    def request(
        self,
        *,
        method: str,
        path: str,
        query: Optional[Sequence[Pair]] = None,
        form: Optional[Sequence[Pair]] = None,
        json_body: Any = None,
        files: Optional[Sequence[Tuple[str, Path]]] = None,
    ) -> Response:
        """One REST request to ``path`` under ``/api/v4``; empty ``form`` and ``files`` count as absent."""
        url = self._rest_url(path=path, query=tuple(query or ()))
        data, content_type = request_body(form=tuple(form or ()), json_body=json_body, files=tuple(files or ()))
        return self._send(method=method, url=url, data=data, content_type=content_type, credential=self._credential)

    def request_raw(
        self,
        *,
        method: str,
        path: str,
        query: Optional[Sequence[Pair]] = None,
        data: Optional[bytes] = None,
        content_type: str,
    ) -> Response:
        """One REST request to ``path`` under ``/api/v4`` whose body is ``data``, unchanged, sent as ``content_type``;
        ``data`` ``None`` sends no body and no ``Content-Type``. The origin check, the one credential header and the
        redirect handler are ``request``'s (#40 design.md D5)."""
        url = self._rest_url(path=path, query=tuple(query or ()))
        return self._send(method=method, url=url, data=data, content_type=content_type, credential=self._credential)

    def pages(self, *, path: str, query: Optional[Sequence[Pair]] = None, paging: Paging) -> Iterator[Any]:
        """The items of every page of a list endpoint, in page order, each page fetched only when the previous one is
        used up. OFFSET adds ``per_page=MAX_PER_PAGE`` unless ``query`` holds ``per_page`` (AC-2.5); KEYSET follows
        only ``Link`` ``rel="next"`` (AC-2.6); NONE fetches one page."""
        first_query = tuple(query or ())
        if paging is Paging.OFFSET and all(name != PARAM_PER_PAGE for name, _ in first_query):
            first_query += ((PARAM_PER_PAGE, str(MAX_PER_PAGE)),)
        url: Optional[str] = self._rest_url(path=path, query=first_query)
        while url is not None:
            response = self._send(method=METHOD_GET, url=url, credential=self._credential)
            yield from _page_items(response=response, url=url)
            url = self._next_page_url(response=response, path=path, query=first_query, paging=paging)

    def _next_page_url(
        self, *, response: Response, path: str, query: Tuple[Pair, ...], paging: Paging
    ) -> Optional[str]:
        """The ``Link`` ``rel="next"`` URL as given; for OFFSET without one, the first request with ``page`` set to
        ``x-next-page``; ``None`` when neither names a next page. ``x-total-pages`` is never read."""
        if paging is Paging.NONE:
            return None
        linked = link_next(headers=response.headers)
        if linked or paging is Paging.KEYSET:
            return linked
        page = str(response.headers.get(HEADER_NEXT_PAGE) or "").strip()
        if not page:
            return None
        unpaged = tuple(pair for pair in query if pair[0] != PARAM_PAGE)
        return self._rest_url(path=path, query=unpaged + ((PARAM_PAGE, page),))

    def _rest_url(self, *, path: str, query: Sequence[Pair]) -> str:
        if not path.startswith(REST_PATH_PREFIX):
            raise ValueError(f"a REST path starts with {REST_PATH_PREFIX!r}: {path!r}")
        url = self._rest_base + path
        return f"{url}?{join_pairs(pairs=query)}" if query else url

    # --- GraphQL ---

    def graphql(
        self,
        *,
        document: str,
        variables: Optional[Mapping[str, Any]] = None,
        files: Sequence[Tuple[str, Path]] = (),
    ) -> Any:
        """POST ``document`` and ``variables`` to ``/api/graphql`` with ``Authorization: Bearer`` and return ``data``.

        ``files`` pairs an operations path (``variables.files.0``) with the file that fills it. Without files the body
        is the JSON ``{"query", "variables"}``; with files it is the ``multipart/form-data`` body of
        ``graphql/conventions.md`` "File uploads": ``operations`` (that JSON, each file's variable ``null``), ``map``
        (each part name ``str(i)`` to a list holding the i-th file's operations path), then the i-th file as the part
        ``str(i)`` (issue #44 D4). A job token raises before a file is read or anything is sent
        (``graphql/conventions.md`` "Credentials"), a file that cannot be read before anything is sent; top-level
        ``errors``, or a mutation payload's non-empty ``errors``, raise ``GitLabGraphQLResponseError`` (AC-4.3)."""
        if self.token_type is TokenType.JOB:
            raise GitLabAPIError("job tokens cannot authenticate GraphQL requests (graphql/conventions.md)")
        payload = {FIELD_QUERY: document, FIELD_VARIABLES: dict(variables or {})}
        if files:
            file_map = {str(index): [operations_path] for index, (operations_path, _) in enumerate(files)}
            data, content_type = request_body(
                form=((PART_OPERATIONS, json.dumps(obj=payload)), (PART_MAP, json.dumps(obj=file_map))),
                json_body=None,
                files=tuple((str(index), path) for index, (_, path) in enumerate(files)),
            )
        else:
            data, content_type = json.dumps(obj=payload).encode(encoding=TEXT_ENCODING), CONTENT_TYPE_JSON
        response = self._send(
            method=METHOD_POST,
            url=self._graphql_url,
            data=data,
            content_type=content_type,
            credential=(HEADER_AUTHORIZATION, BEARER_PREFIX + self._token),
        )
        body = response.value
        if not isinstance(body, Mapping):
            raise GitLabAPIError(
                f"{METHOD_POST} {self._graphql_url} answered a body that is not a JSON object",
                status_code=response.status,
                details=response.text,
            )
        messages = graphql_error_messages(body=body, document=document)
        if messages:
            raise GitLabGraphQLResponseError(
                f"{METHOD_POST} {self._graphql_url} answered GraphQL errors: {MESSAGE_SEPARATOR.join(messages)}",
                status_code=response.status,
                details=response.text,
            )
        return body.get(FIELD_DATA)

    def graphql_nodes(
        self, *, document: str, variables: Optional[Mapping[str, Any]] = None, connection: Sequence[str]
    ) -> List[Any]:
        """The ``nodes`` of every page of the connection at the key path ``connection`` under ``data``, in order: the
        first page with ``after: null``, each next with ``after`` = ``pageInfo.endCursor`` while
        ``pageInfo.hasNextPage`` is true (AC-4.2)."""
        nodes: List[Any] = []
        cursor: Optional[str] = None
        while True:
            data = self.graphql(document=document, variables={**(variables or {}), FIELD_AFTER: cursor})
            page = _connection(data=data, connection=connection)
            nodes.extend(page.get(FIELD_NODES) or [])
            info = page.get(FIELD_PAGE_INFO) or {}
            if not info.get(FIELD_HAS_NEXT_PAGE):
                return nodes
            cursor = info.get(FIELD_END_CURSOR)
            if not cursor:
                raise GitLabAPIError(f"the GraphQL connection {'.'.join(connection)} has a next page but no endCursor")

    # --- The one send ---

    def _send(
        self,
        *,
        method: str,
        url: str,
        credential: Tuple[str, str],
        data: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> Response:
        """Send one request to the configured origin, retrying a ``429``; an error status raises (AC-3.2 to AC-3.5).

        A URL on another origin raises ``GitLabAPIError`` naming it before anything is sent."""
        found = origin(url=url)
        if found != self._origin:
            raise GitLabAPIError(f"refusing {method} {url}: its origin {found} is not the configured {self._origin}")
        retries = 0
        while True:
            request = _build_request(
                method=method, url=url, data=data, content_type=content_type, credential=credential
            )
            response = self._attempt(request=request, method=method, url=url)
            if response.status != HTTPStatus.TOO_MANY_REQUESTS:
                break
            if retries >= RATE_LIMIT_MAX_RETRIES:
                raise GitLabRateLimitError(
                    f"{method} {url} answered {response.status} on {retries + 1} attempts; the retries are spent: "
                    f"{error_text(body=response.text)}",
                    status_code=response.status,
                    details=response.text,
                )
            retries += 1
            self._wait(response=response, method=method, url=url, retry=retries)
        if not _succeeded(status=response.status):
            raise GitLabAPIError(
                f"{method} {url} answered {response.status}: {error_text(body=response.text)}",
                status_code=response.status,
                details=response.text,
            )
        return response

    def _attempt(self, *, request: urllib.request.Request, method: str, url: str) -> Response:
        """One attempt: the response, an error status included; a failure without a response raises with status 0."""
        try:
            with self._opener.open(fullurl=request, timeout=REQUEST_TIMEOUT_SECONDS) as opened:
                return Response(status=opened.getcode(), headers=opened.headers, body=opened.read())
        except urllib.error.HTTPError as error:
            return _error_response(error=error)
        except (OSError, http.client.HTTPException) as error:
            raise GitLabAPIError(f"{method} {url} got no response: {error}") from error
        except ValueError:
            # The text of a ValueError urllib raises while it builds or redirects a request can quote a header value,
            # the credential's included, so neither the text nor the exception travels on.
            raise GitLabAPIError(f"{method} {url} got no response: urllib refused the request or a redirect") from None

    def _wait(self, *, response: Response, method: str, url: str, retry: int) -> None:
        seconds = retry_seconds(headers=response.headers, retry=retry)
        LOGGER.warning(
            "%s %s answered %d; retry %d of %d in %g seconds",
            method,
            url,
            response.status,
            retry,
            RATE_LIMIT_MAX_RETRIES,
            seconds,
        )
        self.sleep(seconds)
