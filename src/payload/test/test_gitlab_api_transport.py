"""Tests for ``gitlab_api/transport.py`` — credentials, bodies, paging, redirects, rate limits, errors and GraphQL.

What is pinned (issue #13, ``design.md`` D4 and "Correctness Properties"):

- the token goes in exactly one header, the configured type's (AC-2.1); a JSON body carries native arrays and objects,
  and form pairs (plain, ``k[]``, ``k[key]``, ``k[0][key]``) are sent as an ``application/x-www-form-urlencoded`` body
  with the brackets literal and ``+`` as ``%2B`` (AC-2.3); a file is sent as ``multipart/form-data`` with its field
  name, its escaped file name and its bytes, every other value as a field (AC-2.4);
- offset paging follows ``x-next-page`` or ``Link`` ``rel="next"`` and never ``x-total-pages`` (AC-2.5); keyset paging
  follows ``Link`` ``rel="next"`` unchanged and nothing else (AC-2.6); a next URL on another origin is refused before
  it is fetched;
- a redirect to another origin (scheme, lower-cased host, port with the scheme's default) drops every credential
  header, a same-origin redirect keeps it, and a credential dropped once stays dropped (AC-3.1);
- ``429`` waits ``Retry-After``, else backs off increasingly, and raises ``GitLabRateLimitError`` when the retries are
  spent (AC-3.2 to AC-3.4); every ``conventions.md`` "Body shapes" error becomes a ``GitLabAPIError`` carrying the
  status, the raw body and the shape's text (AC-3.5);
- GraphQL POSTs ``{"query", "variables"}`` to ``/api/graphql`` (AC-4.1), pages a connection by ``endCursor``
  (AC-4.2), and raises on top-level ``errors`` or a mutation payload's ``errors`` even at HTTP ``200`` (AC-4.3);
- ``Response.is_json`` (issue #41, ``design.md`` D2) reads the ``Content-Type``, parameters ignored: true for
  ``application/json; charset=utf-8``, false for ``text/plain`` and with no ``Content-Type`` (#41 AC-1.5);
- issue #63 (``design.md`` D4, D5): ``base=Base.HOST`` sends under ``https://<hostname>``, outside ``/api/v4``, and
  ``Base.CONTAINER_REGISTRY`` is refused (AC-5.1); ``container_registry_token`` asks ``/jwt/auth`` with
  ``Authorization: Basic`` of ``<login>:<token>`` alone and ``container_registry_request`` sends ``Authorization:
  Bearer <registry token>`` alone, ``_send`` refusing every origin but its ``destination`` (AC-5.2, UB-2); a request
  header is sent beside ``Accept``, the ``Content-Type`` and the credential, and a name the transport owns or a value
  holding CR, LF or NUL is refused before anything is sent (AC-6.2).

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; each
test imports the production module inside its body, so a module not written yet fails the test on an assertion. The
fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.
Every ``Transport`` is built with a recording ``sleep``, a fixed ``clock`` and its default opener, so the redirect tests
exercise the opener the transport builds and no test really sleeps.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_transport.py`` (no network).
"""

from __future__ import annotations

import base64
import email.message
import importlib
import importlib.util
import json
import logging
import pathlib
import re
import sys
import urllib.parse
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "gitlab_api"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

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

HOST = fixtures.HOST
REST_BASE = fixtures.REST_BASE
GRAPHQL_URL = fixtures.GRAPHQL_URL

TOKEN = "transport-token-for-the-test"  # pragma: allowlist secret
FIXED_CLOCK_SECONDS = 1_000.0

TOKEN_TYPE_PRIVATE = "private"
TOKEN_TYPE_BEARER = "bearer"
TOKEN_TYPE_JOB = "job"
TOKEN_TYPES = (TOKEN_TYPE_PRIVATE, TOKEN_TYPE_BEARER, TOKEN_TYPE_JOB)

# The credential each token type sends, by lower-cased header name (conventions.md "Credential types").
HEADER_PRIVATE_TOKEN = "private-token"
HEADER_JOB_TOKEN = "job-token"
HEADER_AUTHORIZATION = "authorization"
CREDENTIAL_HEADER_NAMES = frozenset({HEADER_PRIVATE_TOKEN, HEADER_JOB_TOKEN, HEADER_AUTHORIZATION})
BEARER_CREDENTIAL = {HEADER_AUTHORIZATION: f"Bearer {TOKEN}"}
EXPECTED_CREDENTIAL: Dict[str, Dict[str, str]] = {
    TOKEN_TYPE_PRIVATE: {HEADER_PRIVATE_TOKEN: TOKEN},
    TOKEN_TYPE_BEARER: BEARER_CREDENTIAL,
    TOKEN_TYPE_JOB: {HEADER_JOB_TOKEN: TOKEN},
}

HEADER_CONTENT_TYPE = "Content-Type"
HEADER_LOCATION = "Location"
HEADER_LINK = "Link"
HEADER_RETRY_AFTER = "Retry-After"
HEADER_NEXT_PAGE = "x-next-page"
HEADER_PAGE = "x-page"
HEADER_TOTAL_PAGES = "x-total-pages"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"

FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_AFTER = "after"
FIELD_DATA = "data"
FIELD_ERRORS = "errors"

# conventions.md "Offset-based": `per_page` maximum.
DOCUMENTED_MAX_PER_PAGE = 100
PER_PAGE = str(DOCUMENTED_MAX_PER_PAGE)

RATE_LIMITED_BODY = "Retry later"

# --- shared doubles -----------------------------------------------------------------------------------------------


class RecordingSleep:
    """Stands in for ``time.sleep``: records each pause and returns at once; positional only, as ``time.sleep``."""

    def __init__(self) -> None:
        self.calls: List[float] = []

    def __call__(self, seconds: float, /) -> None:
        self.calls.append(seconds)


def fixed_clock() -> float:
    return FIXED_CLOCK_SECONDS


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def sleeper() -> RecordingSleep:
    return RecordingSleep()


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` inside a test, so a module not written yet fails it on an assertion."""
    source = PACKAGE_DIR / f"{name}.py"
    assert source.is_file(), f"gitlab_api/{name}.py does not exist under {SCRIPTS_DIR}"
    return importlib.import_module(name=f"gitlab_api.{name}")


def make_client(*, transport: ModuleType, sleeper: RecordingSleep, token_type: str = TOKEN_TYPE_PRIVATE) -> Any:
    """A ``Transport`` on the fake host with the recording sleep, the fixed clock and the default opener (D4)."""
    return transport.Transport(
        host=HOST,
        token=TOKEN,
        token_type=transport.TokenType(token_type),
        sleep=sleeper,
        clock=fixed_clock,
    )


def credentials_sent(*, request: Any) -> Dict[str, str]:
    """Every credential header the recorded request carried, by lower-cased name."""
    return {name.lower(): value for name, value in request.headers.items() if name.lower() in CREDENTIAL_HEADER_NAMES}


def media_type(*, value: Any) -> str:
    """A ``Content-Type`` value without its parameters, lower-cased; empty when the header is absent."""
    return str(value or "").split(";")[0].strip().lower()


def recorded_urls(*, fake: Any) -> List[str]:
    return [request.url for request in fake.requests]


def link_header(*, links: Sequence[Tuple[str, str]]) -> str:
    """A ``Link`` header value of ``(url, rel)`` pairs, in GitLab's spelling."""
    return ", ".join(f'<{url}>; rel="{rel}"' for url, rel in links)


# --- multipart parsing (RFC 2046 section 5.1.1) ---------------------------------------------------------------------

CRLF = b"\r\n"
DISPOSITION_PARAM = re.compile(r'(\w+)="([^"]*)"')
HEADER_CONTENT_DISPOSITION = "content-disposition"


class MultipartPart:
    """One body part: its headers by lower-cased name, the disposition type and parameters, its raw content."""

    def __init__(self, *, headers: Dict[str, str], content: bytes) -> None:
        self.headers = headers
        self.content = content
        disposition = headers.get(HEADER_CONTENT_DISPOSITION, "")
        self.disposition_type = disposition.split(";")[0].strip().lower()
        self.disposition = dict(DISPOSITION_PARAM.findall(disposition))


def multipart_boundary(*, content_type: Any) -> str:
    """The boundary parameter of a ``multipart/form-data`` content type."""
    message = email.message.Message()
    message[HEADER_CONTENT_TYPE] = str(content_type)
    assert message.get_content_type() == CONTENT_TYPE_MULTIPART, f"Content-Type {content_type!r} is not multipart"
    boundary = message.get_param(param="boundary")
    assert isinstance(boundary, str) and boundary, f"Content-Type {content_type!r} names no boundary"
    return boundary


def multipart_parts(*, body: bytes, boundary: str) -> List[MultipartPart]:
    """The parts of a multipart body, split on ``CRLF--boundary`` exactly as RFC 2046 delimits them."""
    delimiter = CRLF + b"--" + boundary.encode("ascii")
    chunks = (CRLF + body).split(delimiter)
    assert chunks[0] == b"", "a multipart body starts with its first boundary"
    assert chunks[-1].startswith(b"--"), "a multipart body ends with the close delimiter"
    parts = []
    for chunk in chunks[1:-1]:
        assert chunk.startswith(CRLF), "a boundary line ends with CRLF"
        head, separator, content = chunk[len(CRLF) :].partition(CRLF + CRLF)
        assert separator, "a part separates its headers from its content with an empty line"
        headers: Dict[str, str] = {}
        for line in head.decode("utf-8").split("\r\n"):
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
        parts.append(MultipartPart(headers=headers, content=content))
    return parts


# Windows cannot store `"` in a file name, so the uploaded bytes come from a file with a plain name and the path object
# reports a name carrying the quotes — the name the transport writes into the part (D4 "Multipart").
REPORTED_FILE_NAME = 'report"final".log'
ESCAPED_FILE_NAME = "report%22final%22.log"
FILE_BYTES = b"first line\r\nsecond line\r\n\x00\xff binary tail"

if sys.platform == "win32":
    ConcretePath = pathlib.WindowsPath
else:
    ConcretePath = pathlib.PosixPath


class ReportedNamePath(ConcretePath):
    """A real file whose ``name`` is ``REPORTED_FILE_NAME``."""

    @property
    def name(self) -> str:
        return REPORTED_FILE_NAME


# --- AC-2.1 credentials -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
def test_one_credential_header_per_token_type(fake_gitlab: Any, sleeper: RecordingSleep, token_type: str) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method="GET", url=f"{REST_BASE}/projects/1", body={"id": 1})

    response = client.request(method="GET", path="/projects/1")

    assert response.value == {"id": 1}, "a JSON response is decoded"
    assert recorded_urls(fake=fake_gitlab) == [f"{REST_BASE}/projects/1"]
    sent = fake_gitlab.requests[0]
    assert credentials_sent(request=sent) == EXPECTED_CREDENTIAL[token_type], (
        f"token type {token_type!r} sends exactly its one credential header (AC-2.1)"
    )
    assert TOKEN not in sent.url, "the token never enters a URL"


# --- AC-2.3 JSON and form bodies, AC-2.4 multipart --------------------------------------------------------------------

JSON_BODY = {
    "assignee_ids": [11, 12],
    "variables": [{"key": "VAR1", "value": "hello"}, {"key": "VAR2", "value": "world"}],
    "options": {"remove_source_branch": True, "squash": None},
}


def test_json_body_is_native(fake_gitlab: Any, sleeper: RecordingSleep) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    url = f"{REST_BASE}/projects/1/issues/2"
    fake_gitlab.script(method="PUT", url=url, body={"iid": 2})

    response = client.request(method="PUT", path="/projects/1/issues/2", json_body=JSON_BODY)

    assert response.value == {"iid": 2}
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("PUT", url)]
    sent = fake_gitlab.requests[0]
    assert media_type(value=sent.header(name=HEADER_CONTENT_TYPE)) == CONTENT_TYPE_JSON
    assert sent.json() == JSON_BODY, "a JSON body holds arrays and objects natively, not bracket pairs (AC-2.3)"


CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"

# Form pairs in the shapes `registry.encode` gives them (D5): SCALAR `name=v`, ARRAY `name[]=v`, HASH `name[k]=v`,
# ARRAY_OF_HASHES `name[0][k]=v`. The raw body is D4's join, `urlencode(pairs, safe="[]", quote_via=quote)`:
# brackets literal, `+` as %2B, a space as %20 (conventions.md "Arrays, hashes and arrays of hashes", "`+` in dates").
FORM_CASES = [
    pytest.param(
        "POST",
        "/projects/1/issues",
        (
            ("title", "Release 1.0 notes"),
            ("created_at", "2026-11-11T10:00:00+01:00"),
            ("description", ""),
            ("confidential", "true"),
        ),
        "title=Release%201.0%20notes&created_at=2026-11-11T10%3A00%3A00%2B01%3A00&description=&confidential=true",
        id="plain-pairs",
    ),
    pytest.param(
        "PUT",
        "/projects/1/issues/2",
        (("labels[]", "bug"), ("labels[]", "ui+ux"), ("assignee_ids[]", "11")),
        "labels[]=bug&labels[]=ui%2Bux&assignee_ids[]=11",
        id="array-pairs",
    ),
    pytest.param(
        "POST",
        "/projects/1/trigger/pipeline",
        (("ref", "main"), ("variables[DEPLOY_ENV]", "staging"), ("variables[RELEASE]", "v1+build")),
        "ref=main&variables[DEPLOY_ENV]=staging&variables[RELEASE]=v1%2Bbuild",
        id="hash-pairs",
    ),
    pytest.param(
        "POST",
        "/projects/1/pipeline",
        (
            ("ref", "main"),
            ("variables[0][key]", "VAR1"),
            ("variables[0][value]", "hello world"),
            ("variables[1][key]", "VAR2"),
            ("variables[1][value]", "a&b=c+d"),
        ),
        "ref=main&variables[0][key]=VAR1&variables[0][value]=hello%20world&variables[1][key]=VAR2"
        "&variables[1][value]=a%26b%3Dc%2Bd",
        id="array-of-hashes",
    ),
]


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
@pytest.mark.parametrize(("method", "path", "pairs", "raw_body"), FORM_CASES)
def test_form_pairs_send_a_form_body(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    token_type: str,
    method: str,
    path: str,
    pairs: Tuple[Tuple[str, str], ...],
    raw_body: str,
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    url = f"{REST_BASE}{path}"
    fake_gitlab.script(method=method, url=url, body={"id": 1})

    response = client.request(method=method, path=path, form=pairs)

    assert response.value == {"id": 1}
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [(method, url)], (
        "one request; the form pairs travel in the body, not in the URL"
    )
    sent = fake_gitlab.requests[0]
    assert sent.header(name=HEADER_CONTENT_TYPE) == CONTENT_TYPE_FORM, (
        "form pairs are sent as an application/x-www-form-urlencoded body (AC-2.3)"
    )
    assert sent.body is not None, f"{method} {url} carried no body"
    text = sent.body.decode("ascii")
    assert urllib.parse.parse_qsl(qs=text, keep_blank_values=True) == list(pairs), (
        "the form body decodes to exactly the pairs, in order, `+` kept (sent as %2B)"
    )
    assert text == raw_body, (
        "the pairs are joined as D4 names (urlencode, safe='[]', quote_via=quote): brackets literal, `+` as %2B"
    )
    assert credentials_sent(request=sent) == EXPECTED_CREDENTIAL[token_type], (
        f"token type {token_type!r} sends exactly its one credential header with a form body (AC-2.1)"
    )
    assert TOKEN not in sent.url and TOKEN not in text, "the token enters neither the URL nor the body"


def test_file_value_sends_multipart(fake_gitlab: Any, sleeper: RecordingSleep, tmp_path: Path) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    stored = tmp_path / "report.log"
    stored.write_bytes(FILE_BYTES)
    upload = ReportedNamePath(stored)
    url = f"{REST_BASE}/projects/1/uploads"
    fake_gitlab.script(method="POST", url=url, status=201, body={"url": "/uploads/0/report.log"})

    client.request(
        method="POST",
        path="/projects/1/uploads",
        form=(("description", "the build log"),),
        files=(("file", upload),),
    )

    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("POST", url)]
    sent = fake_gitlab.requests[0]
    boundary = multipart_boundary(content_type=sent.header(name=HEADER_CONTENT_TYPE))
    assert len(boundary) <= 70, "RFC 2046 section 5.1.1 limits a boundary to 70 characters"
    assert sent.body is not None
    parts = multipart_parts(body=sent.body, boundary=boundary)
    by_name = {part.disposition.get("name"): part for part in parts}
    assert sorted(by_name, key=str) == ["description", "file"], "one part per file and per other value (AC-2.4)"
    assert all(part.disposition_type == "form-data" for part in parts)

    field = by_name["description"]
    assert field.disposition == {"name": "description"}, "a non-file value is a plain form field"
    assert field.content == b"the build log"

    file_part = by_name["file"]
    assert file_part.disposition == {"name": "file", "filename": ESCAPED_FILE_NAME}, (
        'the file part carries its field name and its file name, `"` written as %22 (the HTML multipart encoding)'
    )
    assert media_type(value=file_part.headers.get("content-type")) == CONTENT_TYPE_OCTET_STREAM
    assert file_part.content == FILE_BYTES, "the file's bytes are sent unchanged"


# --- AC-2.5 offset paging, AC-2.6 keyset paging --------------------------------------------------------------------

ISSUES_PATH = "/projects/1/issues"
ISSUES_URL = f"{REST_BASE}{ISSUES_PATH}"
OFFSET_FIRST_URL = f"{ISSUES_URL}?per_page={PER_PAGE}"
# x-next-page re-issues the first request with `page` added (D4 `pages`).
OFFSET_SECOND_URL = f"{ISSUES_URL}?per_page={PER_PAGE}&page=2"
# The Link next URL is followed as given; the comma inside it must not split the header.
OFFSET_THIRD_URL = f"{ISSUES_URL}?labels=bug,ui&page=3&per_page={PER_PAGE}"
OFFSET_FIRST_PAGE_LINK = f"{ISSUES_URL}?page=1&per_page={PER_PAGE}"
OFFSET_SECOND_PAGE_LINK = f"{ISSUES_URL}?page=2&per_page={PER_PAGE}"


@pytest.mark.parametrize(
    "last_page_next",
    [[(HEADER_NEXT_PAGE, "")], []],
    ids=["x-next-page-empty", "x-next-page-absent"],
)
def test_offset_paging_follows_next_and_ignores_total_pages(
    fake_gitlab: Any, sleeper: RecordingSleep, last_page_next: List[Tuple[str, str]]
) -> None:
    transport = gitlab_module(name="transport")
    registry = gitlab_module(name="registry")
    assert transport.MAX_PER_PAGE == DOCUMENTED_MAX_PER_PAGE, "conventions.md 'Offset-based': per_page maximum 100"
    client = make_client(transport=transport, sleeper=sleeper)
    fake_gitlab.script(
        method="GET",
        url=OFFSET_FIRST_URL,
        headers=[
            (HEADER_PAGE, "1"),
            (HEADER_NEXT_PAGE, "2"),
            (HEADER_TOTAL_PAGES, "1"),  # wrong on purpose: paging never reads it
            (
                HEADER_LINK,
                link_header(links=[(OFFSET_FIRST_PAGE_LINK, "first"), (OFFSET_FIRST_PAGE_LINK, "last")]),
            ),
        ],
        body=[{"id": 1}, {"id": 2}],
    )
    fake_gitlab.script(
        method="GET",
        url=OFFSET_SECOND_URL,
        headers=[
            (HEADER_PAGE, "2"),
            (HEADER_NEXT_PAGE, "3"),
            (HEADER_TOTAL_PAGES, "2"),
            (
                HEADER_LINK,
                link_header(
                    links=[
                        (OFFSET_FIRST_PAGE_LINK, "prev"),
                        (OFFSET_THIRD_URL, "next"),
                        (OFFSET_FIRST_PAGE_LINK, "first"),
                    ]
                ),
            ),
        ],
        body=[{"id": 3}],
    )
    fake_gitlab.script(
        method="GET",
        url=OFFSET_THIRD_URL,
        headers=[
            (HEADER_PAGE, "3"),
            *last_page_next,
            (HEADER_TOTAL_PAGES, "9"),  # wrong on purpose: a fourth request would fail on the fake
            (
                HEADER_LINK,
                link_header(links=[(OFFSET_SECOND_PAGE_LINK, "prev"), (OFFSET_FIRST_PAGE_LINK, "first")]),
            ),
        ],
        body=[{"id": 4}],
    )

    items = iter(client.pages(path=ISSUES_PATH, paging=registry.Paging.OFFSET))
    first = next(items)
    assert len(fake_gitlab.requests) == 1, "a page is fetched only when the previous one is exhausted"
    collected = [first, *items]

    assert collected == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}], "the items of every page, in page order"
    assert recorded_urls(fake=fake_gitlab) == [OFFSET_FIRST_URL, OFFSET_SECOND_URL, OFFSET_THIRD_URL], (
        "page 1 -> 2 by x-next-page, 2 -> 3 by Link rel=next as given, stop when neither names a next page (AC-2.5)"
    )


PIPELINES_PATH = "/pipelines"
KEYSET_QUERY = (("order_by", "created_at"), ("sort", "desc"), ("per_page", PER_PAGE))
KEYSET_FIRST_URL = f"{REST_BASE}{PIPELINES_PATH}?order_by=created_at&sort=desc&per_page={PER_PAGE}"
# Percent-escapes and a parameter order unlike the first request: any re-encoding or rebuilding changes the bytes.
KEYSET_SECOND_URL = f"{REST_BASE}{PIPELINES_PATH}?cursor=page%3Dtwo%2Csorted&order_by=created_at&per_page={PER_PAGE}"
KEYSET_THIRD_URL = f"{REST_BASE}{PIPELINES_PATH}?cursor=page%3Dthree%2Csorted&order_by=created_at&per_page={PER_PAGE}"


def test_keyset_paging_follows_link_unchanged(fake_gitlab: Any, sleeper: RecordingSleep) -> None:
    transport = gitlab_module(name="transport")
    registry = gitlab_module(name="registry")
    client = make_client(transport=transport, sleeper=sleeper)
    fake_gitlab.script(
        method="GET",
        url=KEYSET_FIRST_URL,
        headers=[(HEADER_LINK, link_header(links=[(KEYSET_SECOND_URL, "next")]))],
        body=[{"id": 30}, {"id": 29}],
    )
    fake_gitlab.script(
        method="GET",
        url=KEYSET_SECOND_URL,
        headers=[(HEADER_LINK, link_header(links=[(KEYSET_THIRD_URL, "next")]))],
        body=[{"id": 28}],
    )
    # The last page: no Link header, an empty array; the stray x-next-page is not a keyset signal (D4 KEYSET).
    fake_gitlab.script(method="GET", url=KEYSET_THIRD_URL, headers=[(HEADER_NEXT_PAGE, "4")], body=[])

    collected = list(client.pages(path=PIPELINES_PATH, query=KEYSET_QUERY, paging=registry.Paging.KEYSET))

    assert collected == [{"id": 30}, {"id": 29}, {"id": 28}], "the items of every page, in page order"
    assert recorded_urls(fake=fake_gitlab) == [KEYSET_FIRST_URL, KEYSET_SECOND_URL, KEYSET_THIRD_URL], (
        "each follow-up URL is the Link rel=next URL byte for byte, and paging stops when Link is absent (AC-2.6)"
    )


FOREIGN_NEXT_URLS = [
    pytest.param(f"https://evil.example{ISSUES_PATH}?page=2", id="another-host"),
    pytest.param(f"http://{HOST}/api/v4{ISSUES_PATH}?page=2", id="another-scheme"),
    pytest.param(f"https://{HOST}:8443/api/v4{ISSUES_PATH}?page=2", id="another-port"),
    pytest.param(f"https://{HOST}@evil.example/api/v4{ISSUES_PATH}?page=2", id="userinfo-host"),
    pytest.param(f"https://{HOST}:abc/api/v4{ISSUES_PATH}?page=2", id="non-integer-port"),
]


@pytest.mark.parametrize("paging_name", ["OFFSET", "KEYSET"])
@pytest.mark.parametrize("next_url", FOREIGN_NEXT_URLS)
def test_next_url_on_another_origin_is_refused(
    fake_gitlab: Any, sleeper: RecordingSleep, paging_name: str, next_url: str
) -> None:
    transport = gitlab_module(name="transport")
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    client = make_client(transport=transport, sleeper=sleeper)
    first_url = f"{ISSUES_URL}?per_page={PER_PAGE}"
    fake_gitlab.script(
        method="GET",
        url=first_url,
        headers=[(HEADER_LINK, link_header(links=[(next_url, "next")]))],
        body=[{"id": 1}],
    )

    with pytest.raises(errors.GitLabAPIError, match=re.escape(next_url)):
        list(
            client.pages(
                path=ISSUES_PATH,
                query=(("per_page", PER_PAGE),),
                paging=getattr(registry.Paging, paging_name),
            )
        )

    assert recorded_urls(fake=fake_gitlab) == [first_url], "a next URL on another origin is never fetched"


# --- AC-3.1 redirects ---------------------------------------------------------------------------------------------

ARTIFACTS_PATH = "/projects/1/jobs/5/artifacts"
ARTIFACTS_URL = f"{REST_BASE}{ARTIFACTS_PATH}"

CROSS_ORIGIN_TARGETS = [
    pytest.param(f"https://{HOST}.evil.example/", id="suffixed-host"),
    pytest.param(f"https://{HOST}@evil.example/", id="userinfo-host"),
    pytest.param(f"http://{HOST}/", id="http-scheme"),
    pytest.param(f"https://{HOST}:8443/", id="other-port"),
]


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
@pytest.mark.parametrize("target", CROSS_ORIGIN_TARGETS)
def test_cross_origin_redirect_drops_credentials(
    fake_gitlab: Any, sleeper: RecordingSleep, token_type: str, target: str
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method="GET", url=ARTIFACTS_URL, status=302, headers=[(HEADER_LOCATION, target)])
    fake_gitlab.script(method="GET", url=target, body="artifact")

    client.request(method="GET", path=ARTIFACTS_PATH)

    assert recorded_urls(fake=fake_gitlab) == [ARTIFACTS_URL, target], "the redirect is followed"
    assert credentials_sent(request=fake_gitlab.requests[0]) == EXPECTED_CREDENTIAL[token_type]
    assert credentials_sent(request=fake_gitlab.requests[1]) == {}, (
        f"a redirect to {target} (another origin) carries no credential header (AC-3.1)"
    )


SAME_ORIGIN_TARGETS = [
    pytest.param(f"{REST_BASE}/projects/2", id="moved-project"),
    pytest.param(f"https://{HOST.upper()}:443/api/v4/projects/2", id="upper-case-host-default-port"),
    pytest.param(f"https://{HOST}:/api/v4/projects/2", id="empty-port"),
]


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
@pytest.mark.parametrize("target", SAME_ORIGIN_TARGETS)
def test_same_origin_redirect_keeps_credential(
    fake_gitlab: Any, sleeper: RecordingSleep, token_type: str, target: str
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    start = f"{REST_BASE}/projects/1"
    fake_gitlab.script(method="GET", url=start, status=301, headers=[(HEADER_LOCATION, target)])
    fake_gitlab.script(method="GET", url=target, body={"id": 2})

    response = client.request(method="GET", path="/projects/1")

    assert response.value == {"id": 2}
    assert recorded_urls(fake=fake_gitlab) == [start, target], "the redirect is followed"
    assert credentials_sent(request=fake_gitlab.requests[1]) == EXPECTED_CREDENTIAL[token_type], (
        f"a redirect to {target} (the configured origin) keeps the configured credential"
    )


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
def test_credential_stays_dropped_on_return_hop(fake_gitlab: Any, sleeper: RecordingSleep, token_type: str) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    foreign = "https://objects.example.net/bucket/artifact"
    back = f"{ARTIFACTS_URL}/landed"
    fake_gitlab.script(method="GET", url=ARTIFACTS_URL, status=302, headers=[(HEADER_LOCATION, foreign)])
    fake_gitlab.script(method="GET", url=foreign, status=302, headers=[(HEADER_LOCATION, back)])
    fake_gitlab.script(method="GET", url=back, body="artifact")

    client.request(method="GET", path=ARTIFACTS_PATH)

    assert recorded_urls(fake=fake_gitlab) == [ARTIFACTS_URL, foreign, back], "both redirects are followed"
    assert [credentials_sent(request=request) for request in fake_gitlab.requests] == [
        EXPECTED_CREDENTIAL[token_type],
        {},
        {},
    ], "a credential dropped on the way to another origin stays dropped back on the configured host"


# --- AC-3.2 to AC-3.4 rate limits ---------------------------------------------------------------------------------


def test_429_waits_retry_after(fake_gitlab: Any, sleeper: RecordingSleep, caplog: pytest.LogCaptureFixture) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    caplog.set_level(level=logging.DEBUG)
    url = f"{REST_BASE}/projects/1/issues/7"
    fake_gitlab.script(method="GET", url=url, status=429, headers=[(HEADER_RETRY_AFTER, "3")], body=RATE_LIMITED_BODY)
    fake_gitlab.script(method="GET", url=url, body={"iid": 7})

    response = client.request(method="GET", path="/projects/1/issues/7")

    assert response.value == {"iid": 7}, "the retried request's result is returned"
    assert sleeper.calls == [3], "a 429 with Retry-After waits that many seconds, once (AC-3.2)"
    assert recorded_urls(fake=fake_gitlab) == [url, url], "the same request is sent again"
    assert credentials_sent(request=fake_gitlab.requests[1]) == EXPECTED_CREDENTIAL[TOKEN_TYPE_PRIVATE]
    assert TOKEN not in caplog.text, "no log record carries the token"


def test_429_without_headers_backs_off_increasingly(
    fake_gitlab: Any, sleeper: RecordingSleep, caplog: pytest.LogCaptureFixture
) -> None:
    transport = gitlab_module(name="transport")
    retries = transport.RATE_LIMIT_MAX_RETRIES
    assert retries >= 2, "at least two consecutive 429s are retried, so a growing back-off is observable"
    client = make_client(transport=transport, sleeper=sleeper)
    caplog.set_level(level=logging.DEBUG)
    url = f"{REST_BASE}/projects/1"
    for _ in range(retries):
        fake_gitlab.script(method="GET", url=url, status=429, body=RATE_LIMITED_BODY)
    fake_gitlab.script(method="GET", url=url, body={"id": 1})

    response = client.request(method="GET", path="/projects/1")

    assert response.value == {"id": 1}, "the request succeeds once the 429s stop"
    assert len(sleeper.calls) == retries, "one sleep per header-less 429"
    assert all(seconds > 0 for seconds in sleeper.calls), f"every back-off waits: {sleeper.calls}"
    assert all(later > earlier for earlier, later in zip(sleeper.calls, sleeper.calls[1:])), (
        f"the back-off grows with each consecutive 429 (AC-3.3): {sleeper.calls}"
    )
    assert len(fake_gitlab.requests) == retries + 1
    assert TOKEN not in caplog.text, "no log record carries the token"


def test_429_after_retries_raises(fake_gitlab: Any, sleeper: RecordingSleep) -> None:
    transport = gitlab_module(name="transport")
    errors = gitlab_module(name="errors")
    retries = transport.RATE_LIMIT_MAX_RETRIES
    client = make_client(transport=transport, sleeper=sleeper)
    url = f"{REST_BASE}/projects/1"
    for _ in range(retries + 1):
        fake_gitlab.script(
            method="GET", url=url, status=429, headers=[(HEADER_RETRY_AFTER, "2")], body=RATE_LIMITED_BODY
        )

    with pytest.raises(errors.GitLabRateLimitError) as raised:
        client.request(method="GET", path="/projects/1")

    assert isinstance(raised.value, errors.GitLabAPIError), "the rate-limit error is a GitLabAPIError (exit 1)"
    assert raised.value.status_code == 429, "AC-3.4: status_code 429"
    assert sleeper.calls == [2] * retries, "RATE_LIMIT_MAX_RETRIES sleeps, then the error"
    assert len(fake_gitlab.requests) == retries + 1, "the first attempt and RATE_LIMIT_MAX_RETRIES retries"


# --- AC-3.5 error body shapes -------------------------------------------------------------------------------------

SCOPE_DESCRIPTION = "The request requires higher privileges than provided by the access token."
PLAIN_TEXT_ERROR = (
    "RequestBody: upload failed: the upload size 400000000 is over maximum of 314572800 bytes: entity is too large"
)
SPAM_MESSAGE = "Your snippet has been recognized as spam and has been discarded."

ERROR_SHAPES = [
    pytest.param(
        404, CONTENT_TYPE_JSON, '{"message": "404 Project Not Found"}', "404 Project Not Found", id="message-string"
    ),
    pytest.param(
        400,
        CONTENT_TYPE_JSON,
        '{"message": {"bio": ["is too long (maximum is 255 characters)"]}}',
        "bio: is too long (maximum is 255 characters)",
        id="message-field-hash",
    ),
    pytest.param(
        400,
        CONTENT_TYPE_JSON,
        '{"error": "glql_yaml is missing, glql_yaml is empty"}',
        "glql_yaml is missing, glql_yaml is empty",
        id="error-string",
    ),
    pytest.param(
        403,
        CONTENT_TYPE_JSON,
        json.dumps(obj={"error": "insufficient_scope", "error_description": SCOPE_DESCRIPTION, "scope": "api"}),
        f"insufficient_scope: {SCOPE_DESCRIPTION}",
        id="oauth-scope",
    ),
    pytest.param(
        400,
        CONTENT_TYPE_JSON,
        json.dumps(obj={"message": {"error": SPAM_MESSAGE}}),
        f"error: {SPAM_MESSAGE}",
        id="spam-hash",
    ),
    pytest.param(413, CONTENT_TYPE_TEXT, PLAIN_TEXT_ERROR, PLAIN_TEXT_ERROR, id="plain-text"),
]


@pytest.mark.parametrize(("status", "content_type", "raw_body", "expected_text"), ERROR_SHAPES)
def test_error_shape_raises_gitlab_api_error(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    status: int,
    content_type: str,
    raw_body: str,
    expected_text: str,
) -> None:
    transport = gitlab_module(name="transport")
    errors = gitlab_module(name="errors")
    client = make_client(transport=transport, sleeper=sleeper)
    fake_gitlab.script(
        method="GET",
        url=f"{REST_BASE}/projects/1",
        status=status,
        headers=[(HEADER_CONTENT_TYPE, content_type)],
        body=raw_body,
    )

    with pytest.raises(errors.GitLabAPIError) as raised:
        client.request(method="GET", path="/projects/1")

    error = raised.value
    assert error.status_code == status, "status_code is the response status (AC-3.5)"
    assert error.details == raw_body, "details is the raw response body"
    assert expected_text in str(error), f"the message carries the body shape's text {expected_text!r}"
    assert TOKEN not in str(error), "no exception message carries the token"
    assert sleeper.calls == [], f"a {status} is not retried"


# --- AC-4.1 to AC-4.3 GraphQL -------------------------------------------------------------------------------------

PROJECT_QUERY = "query Project($fullPath: ID!) { project(fullPath: $fullPath) { id name } }"
PROJECT_VARIABLES = {"fullPath": "group/project"}
ISSUES_QUERY = (
    "query Issues($fullPath: ID!, $after: String) { project(fullPath: $fullPath) { issues(first: 2, after: $after) "
    "{ nodes { iid } pageInfo { hasNextPage endCursor } } } }"
)
CREATE_NOTE_MUTATION = (
    "mutation CreateNote($input: CreateNoteInput!) { createNote(input: $input) { note { id } errors } }"
)
NOTE_VARIABLES = {"input": {"noteableId": "gid://gitlab/Issue/7", "body": "a note"}}
CI_CONFIG_QUERY = (
    "query CiConfig($projectPath: ID!, $content: String!) "
    "{ ciConfig(projectPath: $projectPath, content: $content) { status errors } }"
)
CI_CONFIG_VARIABLES = {"projectPath": "group/project", "content": "stages: [test]"}


@pytest.mark.parametrize("token_type", [TOKEN_TYPE_PRIVATE, TOKEN_TYPE_BEARER])
def test_graphql_posts_to_api_graphql(fake_gitlab: Any, sleeper: RecordingSleep, token_type: str) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    data = {"project": {"id": "gid://gitlab/Project/1", "name": "project"}}
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, body={FIELD_DATA: data})

    result = client.graphql(document=PROJECT_QUERY, variables=PROJECT_VARIABLES)

    assert result == data, "graphql returns the response's data"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("POST", GRAPHQL_URL)], (
        "one POST to /api/graphql on the configured host, not under /api/v4 (AC-4.1)"
    )
    sent = fake_gitlab.requests[0]
    assert media_type(value=sent.header(name=HEADER_CONTENT_TYPE)) == CONTENT_TYPE_JSON
    assert sent.json() == {FIELD_QUERY: PROJECT_QUERY, FIELD_VARIABLES: PROJECT_VARIABLES}
    assert credentials_sent(request=sent) == BEARER_CREDENTIAL, (
        "GraphQL always sends Authorization: Bearer, the only header graphql/conventions.md documents"
    )


def test_graphql_pages_by_end_cursor(fake_gitlab: Any, sleeper: RecordingSleep) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    first_page = {
        "project": {
            "issues": {
                "nodes": [{"iid": "1"}, {"iid": "2"}],
                "pageInfo": {"hasNextPage": True, "endCursor": "cursor-after-two"},
            }
        }
    }
    second_page = {
        "project": {
            "issues": {
                "nodes": [{"iid": "3"}],
                "pageInfo": {"hasNextPage": False, "endCursor": "cursor-after-three"},
            }
        }
    }
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, body={FIELD_DATA: first_page})
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, body={FIELD_DATA: second_page})

    nodes = client.graphql_nodes(document=ISSUES_QUERY, variables=PROJECT_VARIABLES, connection=("project", "issues"))

    assert list(nodes) == [{"iid": "1"}, {"iid": "2"}, {"iid": "3"}], "the nodes of every page, in order (AC-4.2)"
    sent = [request.json() for request in fake_gitlab.requests]
    assert [body[FIELD_QUERY] for body in sent] == [ISSUES_QUERY, ISSUES_QUERY]
    assert [body[FIELD_VARIABLES] for body in sent] == [
        {**PROJECT_VARIABLES, FIELD_AFTER: None},
        {**PROJECT_VARIABLES, FIELD_AFTER: "cursor-after-two"},
    ], "the first page is asked with after: null, the next with after = the previous pageInfo.endCursor"


GRAPHQL_ERROR_CASES = [
    pytest.param(
        PROJECT_QUERY,
        PROJECT_VARIABLES,
        {
            FIELD_DATA: {"project": {"id": "gid://gitlab/Project/1", "name": None}},
            FIELD_ERRORS: [
                {"message": "Insufficient permissions to read the project name", "path": ["project", "name"]},
                {"message": "A second failure of the same request"},
            ],
        },
        ("Insufficient permissions to read the project name", "A second failure of the same request"),
        id="top-level-errors-with-partial-data",
    ),
    pytest.param(
        CREATE_NOTE_MUTATION,
        NOTE_VARIABLES,
        {FIELD_DATA: {"createNote": {"note": None, FIELD_ERRORS: ["Note can't be blank"]}}},
        ("Note can't be blank",),
        id="mutation-payload-errors",
    ),
]


@pytest.mark.parametrize(("document", "variables", "response_body", "messages"), GRAPHQL_ERROR_CASES)
def test_graphql_errors_at_200_raise(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    document: str,
    variables: Mapping[str, Any],
    response_body: Mapping[str, Any],
    messages: Tuple[str, ...],
) -> None:
    transport = gitlab_module(name="transport")
    errors = gitlab_module(name="errors")
    client = make_client(transport=transport, sleeper=sleeper)
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, status=200, body=response_body)

    with pytest.raises(errors.GitLabGraphQLResponseError) as raised:
        client.graphql(document=document, variables=variables)

    error = raised.value
    assert isinstance(error, errors.GitLabAPIError), "a GraphQL response error is a GitLabAPIError (exit 1)"
    assert error.status_code == 200, "the error carries the HTTP status, 200 here"
    for message in messages:
        assert message in str(error), f"the error carries the message {message!r} (AC-4.3)"


GRAPHQL_DATA_CASES = [
    pytest.param(
        CREATE_NOTE_MUTATION,
        NOTE_VARIABLES,
        {"createNote": {"note": {"id": "gid://gitlab/Note/9"}, FIELD_ERRORS: []}},
        id="mutation-payload-with-empty-errors",
    ),
    pytest.param(
        CI_CONFIG_QUERY,
        CI_CONFIG_VARIABLES,
        {"ciConfig": {"status": "INVALID", FIELD_ERRORS: ["jobs config should contain at least one visible job"]}},
        id="query-object-with-an-errors-field",
    ),
]


@pytest.mark.parametrize(("document", "variables", "data"), GRAPHQL_DATA_CASES)
def test_empty_payload_errors_and_query_errors_fields_return_data(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    document: str,
    variables: Mapping[str, Any],
    data: Mapping[str, Any],
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, body={FIELD_DATA: data})

    result = client.graphql(document=document, variables=variables)

    assert result == data, (
        "an empty mutation `errors` list, and an `errors` field of a query's object, are data, not a failure"
    )


# --- issue #41 AC-1.5 Response.is_json ----------------------------------------------------------------------------

CONTENT_TYPE_JSON_UTF8 = f"{CONTENT_TYPE_JSON}; charset=utf-8"

# (scripted headers, raw body, is_json): a str body is served verbatim and gains no Content-Type from the fake host.
IS_JSON_CASES = [
    pytest.param(((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON_UTF8),), '{"id": 1}', True, id="json-with-charset"),
    pytest.param(((HEADER_CONTENT_TYPE, CONTENT_TYPE_TEXT),), "a job trace", False, id="text-plain"),
    pytest.param((), "a job trace", False, id="no-content-type"),
]


@pytest.mark.parametrize(("headers", "raw_body", "expected"), IS_JSON_CASES)
def test_is_json_reads_the_content_type(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    headers: Tuple[Tuple[str, str], ...],
    raw_body: str,
    expected: bool,
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    url = f"{REST_BASE}/projects/1"
    fake_gitlab.script(method="GET", url=url, headers=headers, body=raw_body)

    response = client.request(method="GET", path="/projects/1")

    assert recorded_urls(fake=fake_gitlab) == [url]
    assert (response.headers.get_all(HEADER_CONTENT_TYPE) or []) == [value for _, value in headers], (
        "the response carries exactly the scripted Content-Type, or none"
    )
    assert response.is_json is expected, (
        f"is_json is {expected} for Content-Type {headers!r}: the media type alone decides, parameters ignored and "
        "text/plain assumed when the header is absent (#41 D2, AC-1.5)"
    )


# --- issue #44 AC-3.1 the multipart GraphQL request ----------------------------------------------------------------

UPLOAD_MUTATION = (
    "mutation DesignUpload($projectPath: ID!, $iid: ID!, $files: [Upload!]!) "
    "{ designManagementUpload(input: {projectPath: $projectPath, iid: $iid, files: $files}) "
    "{ designs { id } skippedDesigns { id } errors } }"
)
# The variables as `registry.split_uploads` gives them to `Transport.graphql`: each Upload item `null` (#44 D4).
UPLOAD_VARIABLES = {"projectPath": "group/project", "iid": "5", "files": [None, None]}
# Each file: the operations path it fills, its name in `tmp_path`, its bytes (a CRLF and bytes that are not UTF-8).
UPLOADS = (
    ("variables.files.0", "first.png", b"\x89PNG\r\n\x1a\nfirst design\r\n\xff\xfe"),
    ("variables.files.1", "second.png", b"\x89PNG\r\n\x1a\nsecond design\r\n\xfd"),
)
PART_OPERATIONS = "operations"
PART_MAP = "map"
# graphql/conventions.md "File uploads" and #44 D4: `operations`, then `map`, then one part per file named `str(i)`.
UPLOAD_PART_ORDER = [PART_OPERATIONS, PART_MAP, "0", "1"]
UPLOAD_MAP = {"0": ["variables.files.0"], "1": ["variables.files.1"]}
UPLOAD_DATA = {
    "designManagementUpload": {
        "designs": [
            {"id": "gid://gitlab/DesignManagement::Design/1"},
            {"id": "gid://gitlab/DesignManagement::Design/2"},
        ],
        "skippedDesigns": [],
        FIELD_ERRORS: [],
    }
}
# The text of the job-token refusal; a file read first would raise `_file_part`'s "cannot read the file" instead.
JOB_TOKEN_REFUSAL = "job tokens cannot authenticate GraphQL"


def test_graphql_sends_files_as_one_multipart_request(
    fake_gitlab: Any, sleeper: RecordingSleep, tmp_path: Path
) -> None:
    transport = gitlab_module(name="transport")
    errors = gitlab_module(name="errors")
    client = make_client(transport=transport, sleeper=sleeper)
    files = []
    for operations_path, file_name, content in UPLOADS:
        stored = tmp_path / file_name
        stored.write_bytes(content)
        files.append((operations_path, stored))
    fake_gitlab.script(method="POST", url=GRAPHQL_URL, body={FIELD_DATA: UPLOAD_DATA})

    result = client.graphql(document=UPLOAD_MUTATION, variables=UPLOAD_VARIABLES, files=tuple(files))

    assert result == UPLOAD_DATA, "graphql returns the response's data"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("POST", GRAPHQL_URL)], (
        "the files and the operation travel in one POST to /api/graphql (AC-3.1)"
    )
    sent = fake_gitlab.requests[0]
    assert credentials_sent(request=sent) == BEARER_CREDENTIAL, (
        "a multipart GraphQL request sends Authorization: Bearer"
    )
    boundary = multipart_boundary(content_type=sent.header(name=HEADER_CONTENT_TYPE))
    assert sent.body is not None
    assert TOKEN.encode("ascii") not in sent.body, "the token never enters the body"
    parts = multipart_parts(body=sent.body, boundary=boundary)
    assert [part.disposition.get("name") for part in parts] == UPLOAD_PART_ORDER, (
        "the parts are `operations`, `map`, then one per file named after its `map` key, in that order (#44 D4)"
    )
    assert all(part.disposition_type == "form-data" for part in parts)
    by_name = {part.disposition.get("name"): part for part in parts}

    operations = by_name[PART_OPERATIONS]
    assert operations.disposition == {"name": PART_OPERATIONS}, "`operations` is a plain form field"
    assert json.loads(operations.content.decode("utf-8")) == {
        FIELD_QUERY: UPLOAD_MUTATION,
        FIELD_VARIABLES: UPLOAD_VARIABLES,
    }, "`operations` is the JSON of the document and the variables, each Upload item null (AC-3.1)"

    file_map = by_name[PART_MAP]
    assert file_map.disposition == {"name": PART_MAP}, "`map` is a plain form field"
    assert json.loads(file_map.content.decode("utf-8")) == UPLOAD_MAP, (
        "`map` maps each file part's name to the operations path it fills (AC-3.1)"
    )

    for index, (_, file_name, content) in enumerate(UPLOADS):
        file_part = by_name[str(index)]
        assert file_part.disposition == {"name": str(index), "filename": file_name}, (
            f"file {index} is the part {str(index)!r} with its file name"
        )
        assert media_type(value=file_part.headers.get("content-type")) == CONTENT_TYPE_OCTET_STREAM
        assert file_part.content == content, f"file {index}'s bytes are sent unchanged"

    job_client = make_client(transport=transport, sleeper=sleeper, token_type=TOKEN_TYPE_JOB)
    never_written = tmp_path / "never-written.png"

    with pytest.raises(errors.GitLabAPIError, match=JOB_TOKEN_REFUSAL):
        job_client.graphql(
            document=UPLOAD_MUTATION,
            variables=UPLOAD_VARIABLES,
            files=((UPLOADS[0][0], never_written),),
        )

    assert len(fake_gitlab.requests) == 1, "a job token is refused before any file is read and before any request"


# --- issue #40 AC-3.2 raw bodies --------------------------------------------------------------------------------------

# Bytes a raw body carries as given (#40 design.md D5): a CRLF, a NUL, bytes that are no UTF-8 (`\xff`, `\xc3(`), and
# the characters a form or query encoding would rewrite (`+`, `=`, `&`, `%`, a space).
RAW_BODY_BYTES = b"name=a+b&size=10%\r\n\x00\xff\xfe\xc3( binary tail\r\n"
RAW_UPLOAD_PATH = "/projects/1/packages/generic/p/1.0/f.bin"
RAW_UPLOAD_QUERY = (("select", "package_file"),)
RAW_UPLOAD_URL = f"{REST_BASE}{RAW_UPLOAD_PATH}?select=package_file"
RAW_UPLOAD_ANSWER = {"message": "201 Created"}


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
def test_a_raw_body_is_sent_unchanged(fake_gitlab: Any, sleeper: RecordingSleep, token_type: str) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    assert CRLF in RAW_BODY_BYTES, "the bytes hold a CRLF"
    with pytest.raises(UnicodeDecodeError):
        RAW_BODY_BYTES.decode(encoding="utf-8")
    fake_gitlab.script(method="PUT", url=RAW_UPLOAD_URL, status=201, body=RAW_UPLOAD_ANSWER)
    fake_gitlab.script(method="PUT", url=RAW_UPLOAD_URL, status=201, body=RAW_UPLOAD_ANSWER)

    response = client.request_raw(
        method="PUT",
        path=RAW_UPLOAD_PATH,
        query=RAW_UPLOAD_QUERY,
        data=RAW_BODY_BYTES,
        content_type=CONTENT_TYPE_OCTET_STREAM,
    )

    assert response.status == 201
    assert response.value == RAW_UPLOAD_ANSWER, "request_raw returns the response, decoded as request's is"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("PUT", RAW_UPLOAD_URL)], (
        "one request to the configured origin, its query pairs in the URL (#40 AC-3.2)"
    )
    sent = fake_gitlab.requests[0]
    assert sent.body == RAW_BODY_BYTES, "the bytes are the body, unchanged: no envelope and no encoding (#40 AC-3.2)"
    assert sent.header(name=HEADER_CONTENT_TYPE) == CONTENT_TYPE_OCTET_STREAM, "the body carries the Content-Type given"
    assert credentials_sent(request=sent) == EXPECTED_CREDENTIAL[token_type], (
        f"token type {token_type!r} sends exactly its one credential header with a raw body (AC-2.1)"
    )
    assert TOKEN not in sent.url and TOKEN.encode(encoding="ascii") not in sent.body, (
        "the token enters neither the URL nor the body"
    )

    unsent = client.request_raw(
        method="PUT",
        path=RAW_UPLOAD_PATH,
        query=RAW_UPLOAD_QUERY,
        data=None,
        content_type=CONTENT_TYPE_OCTET_STREAM,
    )

    assert unsent.status == 201
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("PUT", RAW_UPLOAD_URL)] * 2
    empty = fake_gitlab.requests[1]
    assert empty.body is None, "data=None sends no body"
    assert empty.header(name=HEADER_CONTENT_TYPE) is None, "a request with no body carries no Content-Type"
    assert credentials_sent(request=empty) == EXPECTED_CREDENTIAL[token_type], (
        f"token type {token_type!r} sends exactly its one credential header with no body (AC-2.1)"
    )


def test_a_raw_body_answered_429_is_retried(
    fake_gitlab: Any, sleeper: RecordingSleep, caplog: pytest.LogCaptureFixture
) -> None:
    """Issue #40 design.md D5: ``request_raw`` returns what ``_send`` returns, so a raw-body request answered ``429``
    with ``Retry-After: 3`` and then ``200`` waits three seconds, is sent again with the same bytes and
    ``Content-Type``, and returns the ``200``, as ``request`` does (#13 AC-3.2)."""
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper)
    caplog.set_level(level=logging.DEBUG)
    fake_gitlab.script(
        method="PUT", url=RAW_UPLOAD_URL, status=429, headers=[(HEADER_RETRY_AFTER, "3")], body=RATE_LIMITED_BODY
    )
    fake_gitlab.script(method="PUT", url=RAW_UPLOAD_URL, status=200, body=RAW_UPLOAD_ANSWER)

    response = client.request_raw(
        method="PUT",
        path=RAW_UPLOAD_PATH,
        query=RAW_UPLOAD_QUERY,
        data=RAW_BODY_BYTES,
        content_type=CONTENT_TYPE_OCTET_STREAM,
    )

    assert response.status == 200, f"the retried raw-body request's answer is returned, got {response.status}"
    assert response.value == RAW_UPLOAD_ANSWER, "the 200's body is returned, decoded as request's is"
    assert sleeper.calls == [3], "a 429 with Retry-After waits that many seconds, once (#13 AC-3.2)"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("PUT", RAW_UPLOAD_URL)] * 2, (
        "the same raw-body request is sent again after the 429"
    )
    assert [request.body for request in fake_gitlab.requests] == [RAW_BODY_BYTES] * 2, (
        "the retry carries the same bytes, unchanged"
    )
    assert [request.header(name=HEADER_CONTENT_TYPE) for request in fake_gitlab.requests] == [
        CONTENT_TYPE_OCTET_STREAM
    ] * 2, "the retry carries the same Content-Type"
    assert TOKEN not in caplog.text, "no log record carries the token"


# --- issue #63 AC-5.1 the host root -----------------------------------------------------------------------------------

# software-supply-chain-security.md "Retrieve the token information": `GET https://HOST/oauth/token/info`, the host's
# root outside /api/v4 (#63 design.md D4 "The host root"). The answer is docs.gitlab.com `oauth2`'s example shape.
TOKEN_INFO_PATH = "/oauth/token/info"
TOKEN_INFO_URL = f"https://{HOST}/oauth/token/info"
TOKEN_INFO_ANSWER = {"resource_owner_id": 1, "scope": ["api"], "expires_in": None, "created_at": 1575890427}
REGISTRY_CATALOG_PATH = "/v2/_catalog"


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
def test_a_host_request_is_sent_outside_the_api(fake_gitlab: Any, sleeper: RecordingSleep, token_type: str) -> None:
    transport = gitlab_module(name="transport")
    registry = gitlab_module(name="registry")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method="GET", url=TOKEN_INFO_URL, body=TOKEN_INFO_ANSWER)
    fake_gitlab.script(method="GET", url=TOKEN_INFO_URL, body=TOKEN_INFO_ANSWER)

    response = client.request(method="GET", path=TOKEN_INFO_PATH, base=registry.Base.HOST)
    raw = client.request_raw(
        method="GET",
        path=TOKEN_INFO_PATH,
        data=None,
        content_type=CONTENT_TYPE_OCTET_STREAM,
        base=registry.Base.HOST,
    )

    assert response.value == TOKEN_INFO_ANSWER, "request's answer is decoded"
    assert raw.value == TOKEN_INFO_ANSWER, "request_raw's answer is decoded"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("GET", TOKEN_INFO_URL)] * 2, (
        "request and request_raw with base=Base.HOST send under https://<hostname>, outside /api/v4 (AC-5.1)"
    )
    assert [credentials_sent(request=request) for request in fake_gitlab.requests] == [
        EXPECTED_CREDENTIAL[token_type]
    ] * 2, f"token type {token_type!r} sends exactly its one credential header to the host's root (AC-5.1)"
    assert all(TOKEN not in url for url in recorded_urls(fake=fake_gitlab)), "the token never enters a URL"

    with pytest.raises(ValueError):
        client.request(method="GET", path=REGISTRY_CATALOG_PATH, base=registry.Base.CONTAINER_REGISTRY)
    with pytest.raises(ValueError):
        client.request_raw(
            method="GET",
            path=REGISTRY_CATALOG_PATH,
            data=None,
            content_type=CONTENT_TYPE_OCTET_STREAM,
            base=registry.Base.CONTAINER_REGISTRY,
        )

    assert len(fake_gitlab.requests) == 2, (
        "base=Base.CONTAINER_REGISTRY is refused before anything is sent: only container_registry_request reaches the "
        "registry (D4)"
    )


# --- issue #63 AC-5.2 the container registry --------------------------------------------------------------------------

# #63 design.md D4 steps 3 and 4. The registry origin is what step 2 reads from `container_registry_image_prefix`
# (`registry.example.com/group/project`); each scope is a record's `token_scope` with the call's value written in.
REGISTRY_ORIGIN = "https://registry.example.com"
REGISTRY_TOKEN = "registry-token-for-the-test"  # pragma: allowlist secret
FIELD_TOKEN = "token"
BASIC_PREFIX = "Basic "
REGISTRY_BEARER_CREDENTIAL = {HEADER_AUTHORIZATION: f"Bearer {REGISTRY_TOKEN}"}

# gitlab-org/gitlab `lib/gitlab/auth.rb`: a job token logs in as `gitlab-ci-token` (CI_JOB_USER); a personal token as
# its user's `username` (D4 step 1).
LOGIN_CASES = [
    pytest.param(TOKEN_TYPE_PRIVATE, "john_smith", id="private-as-its-username"),
    pytest.param(TOKEN_TYPE_JOB, "gitlab-ci-token", id="job-as-gitlab-ci-token"),
]

# doc/api/container_registry.md: `${CI_SERVER_URL}/jwt/auth?service=container_registry&scope=${SCOPE}`; the scope is
# a query value, so `:` is %3A, `/` %2F and `*` %2A.
JWT_AUTH_CASES = [
    pytest.param(
        "repository:group/project:delete",
        f"https://{HOST}/jwt/auth?service=container_registry&scope=repository%3Agroup%2Fproject%3Adelete",
        id="repository-delete",
    ),
    pytest.param(
        "registry:catalog:*",
        f"https://{HOST}/jwt/auth?service=container_registry&scope=registry%3Acatalog%3A%2A",
        id="registry-catalog",
    ),
]


@pytest.mark.parametrize(("token_type", "login"), LOGIN_CASES)
@pytest.mark.parametrize(("scope", "jwt_url"), JWT_AUTH_CASES)
def test_the_registry_token_is_asked_for_with_basic_credentials(
    fake_gitlab: Any, sleeper: RecordingSleep, token_type: str, login: str, scope: str, jwt_url: str
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method="GET", url=jwt_url, body={FIELD_TOKEN: REGISTRY_TOKEN})

    token = client.container_registry_token(login=login, scope=scope)

    assert token == REGISTRY_TOKEN, "the registry token is the answer's `token` field (D4 step 3)"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("GET", jwt_url)], (
        "one GET of /jwt/auth on the configured host, outside /api/v4, the scope percent-encoded (D4 step 3)"
    )
    sent = fake_gitlab.requests[0]
    basic = BASIC_PREFIX + base64.b64encode(s=f"{login}:{TOKEN}".encode(encoding="utf-8")).decode(encoding="ascii")
    assert credentials_sent(request=sent) == {HEADER_AUTHORIZATION: basic}, (
        "Authorization: Basic of <login>:<token> (RFC 7617) is the request's only credential header; the configured "
        "token type's header is not sent beside it"
    )
    assert sent.body is None, "the token request carries no body"
    assert TOKEN not in sent.url, "the token never enters a URL"


# D4 step 4 and doc/api/container_registry.md: the record's path after `/http(s)://${CI_REGISTRY}`, `${NAME}`s written.
REGISTRY_CASES = [
    pytest.param(
        "DELETE",
        "/v2/group/project/tags/reference/1a2b3c4",
        "https://registry.example.com/v2/group/project/tags/reference/1a2b3c4",
        202,
        None,
        id="delete-image-tags-by-reference",
    ),
    pytest.param(
        "GET",
        REGISTRY_CATALOG_PATH,
        "https://registry.example.com/v2/_catalog",
        200,
        {"repositories": ["group/project"]},
        id="listing-all-container-repositories",
    ),
]
# Origins other than the registry's: the configured host, another port of the registry host, another host.
OFF_REGISTRY_URLS = (
    f"{REST_BASE}/projects/1",
    "https://registry.example.com:5050/v2/_catalog",
    "https://evil.example/v2/_catalog",
)


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
@pytest.mark.parametrize(("method", "path", "url", "status", "answer"), REGISTRY_CASES)
def test_a_registry_request_carries_only_the_registry_token(
    fake_gitlab: Any,
    sleeper: RecordingSleep,
    token_type: str,
    method: str,
    path: str,
    url: str,
    status: int,
    answer: Any,
) -> None:
    transport = gitlab_module(name="transport")
    errors = gitlab_module(name="errors")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method=method, url=url, status=status, body=answer)

    response = client.container_registry_request(
        origin=REGISTRY_ORIGIN, method=method, path=path, query=(), token=REGISTRY_TOKEN
    )

    assert response.status == status, f"the registry's answer is returned, got {response.status}"
    assert response.value == answer, "the registry's answer is decoded as request's is"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [(method, url)], (
        "one request to the registry's origin, at the path given (D4 step 4)"
    )
    sent = fake_gitlab.requests[0]
    assert credentials_sent(request=sent) == REGISTRY_BEARER_CREDENTIAL, (
        f"Authorization: Bearer <registry token> is the only credential header; token type {token_type!r}'s header "
        "is not sent to the registry (UB-2)"
    )
    assert all(TOKEN not in value for value in sent.headers.values()), "no header carries the configured token (UB-2)"
    assert TOKEN not in sent.url, "the configured token never enters a URL"

    destination = transport.origin(url=REGISTRY_ORIGIN)
    for elsewhere in OFF_REGISTRY_URLS:
        with pytest.raises(errors.GitLabAPIError, match=re.escape(elsewhere)):
            client._send(
                method="GET",
                url=elsewhere,
                credential=(HEADER_AUTHORIZATION, f"Bearer {REGISTRY_TOKEN}"),
                destination=destination,
            )

    assert len(fake_gitlab.requests) == 1, (
        "a URL on an origin other than `destination` is refused before it is sent, the configured one included (D4)"
    )


# --- issue #63 AC-6.2 request headers ---------------------------------------------------------------------------------

# software-supply-chain-security.md "Set status of an external control" (`- Request headers:`), with AC-6.2's values.
EXTERNAL_CONTROL_PATH = "/projects/1/compliance_external_controls/3/status"
EXTERNAL_CONTROL_URL = f"{REST_BASE}/projects/1/compliance_external_controls/3/status"
EXTERNAL_CONTROL_BODY = {"status": "pass"}
HEADER_ACCEPT = "Accept"
HEADER_NONCE = "X-Gitlab-Nonce"
CONTROL_HEADERS = (("X-Gitlab-Timestamp", "1700000000"), (HEADER_NONCE, "n1"), ("X-Gitlab-Hmac-Sha256", "ab12"))
CONTROL_HEADERS_WITHOUT_NONCE = (("X-Gitlab-Timestamp", "1700000000"), ("X-Gitlab-Hmac-Sha256", "ab12"))
RAW_HEADERS = ((HEADER_NONCE, "n1"),)

OTHER_TOKEN = "another-token-for-the-test"  # pragma: allowlist secret
# #63 design.md D5: a name the transport sets, urllib adds (`AbstractHTTPHandler.do_request_`) or a token type sends,
# compared ignoring case; a value holding CR, LF or NUL (RFC 9110 section 5.5).
REFUSED_HEADERS = (
    ("Accept", "text/html"),
    ("content-type", "text/plain"),
    ("Content-Length", "0"),
    ("Transfer-Encoding", "chunked"),
    ("Host", "evil.example"),
    ("host", "evil.example"),
    ("User-Agent", "another-agent"),
    ("PRIVATE-TOKEN", OTHER_TOKEN),
    ("private-token", OTHER_TOKEN),
    ("Authorization", f"Bearer {OTHER_TOKEN}"),
    ("JOB-TOKEN", OTHER_TOKEN),
    (HEADER_NONCE, "n1\r\nX-Injected: 1"),
    (HEADER_NONCE, "n1\rX-Injected: 1"),
    (HEADER_NONCE, "n1\nX-Injected: 1"),
    (HEADER_NONCE, "n1\x00"),
)


def raises_value_error(*, send: Callable[..., Any], arguments: Mapping[str, Any]) -> bool:
    """Whether ``send(**arguments)`` raises ``ValueError``; a response is ``False``."""
    try:
        send(**arguments)
    except ValueError:
        return True
    return False


@pytest.mark.parametrize("token_type", TOKEN_TYPES)
def test_a_request_header_is_sent_beside_the_transport_headers(
    fake_gitlab: Any, sleeper: RecordingSleep, token_type: str
) -> None:
    transport = gitlab_module(name="transport")
    client = make_client(transport=transport, sleeper=sleeper, token_type=token_type)
    fake_gitlab.script(method="PATCH", url=EXTERNAL_CONTROL_URL, body=EXTERNAL_CONTROL_BODY)
    fake_gitlab.script(method="PATCH", url=EXTERNAL_CONTROL_URL, body=EXTERNAL_CONTROL_BODY)
    fake_gitlab.script(method="PUT", url=RAW_UPLOAD_URL, status=201, body=RAW_UPLOAD_ANSWER)

    client.request(method="PATCH", path=EXTERNAL_CONTROL_PATH, json_body=EXTERNAL_CONTROL_BODY, headers=CONTROL_HEADERS)
    client.request(
        method="PATCH",
        path=EXTERNAL_CONTROL_PATH,
        json_body=EXTERNAL_CONTROL_BODY,
        headers=CONTROL_HEADERS_WITHOUT_NONCE,
    )
    client.request_raw(
        method="PUT",
        path=RAW_UPLOAD_PATH,
        query=RAW_UPLOAD_QUERY,
        data=RAW_BODY_BYTES,
        content_type=CONTENT_TYPE_OCTET_STREAM,
        headers=RAW_HEADERS,
    )

    assert [(request.method, request.url) for request in fake_gitlab.requests] == [
        ("PATCH", EXTERNAL_CONTROL_URL),
        ("PATCH", EXTERNAL_CONTROL_URL),
        ("PUT", RAW_UPLOAD_URL),
    ]
    full, partial, raw = fake_gitlab.requests
    # urllib stores a name as `str.capitalize` writes it (`X-gitlab-nonce`): `header` compares names ignoring case.
    assert [(name, full.header(name=name)) for name, _ in CONTROL_HEADERS] == list(CONTROL_HEADERS), (
        "each header given is sent at its value (AC-6.2)"
    )
    assert partial.header(name=HEADER_NONCE) is None, "a header the call does not give is not sent (AC-6.2)"
    assert [(name, partial.header(name=name)) for name, _ in CONTROL_HEADERS_WITHOUT_NONCE] == list(
        CONTROL_HEADERS_WITHOUT_NONCE
    ), "each header given is sent at its value (AC-6.2)"
    for sent in (full, partial):
        assert sent.header(name=HEADER_ACCEPT) == CONTENT_TYPE_JSON, "beside the transport's Accept (AC-6.2)"
        assert media_type(value=sent.header(name=HEADER_CONTENT_TYPE)) == CONTENT_TYPE_JSON, "beside its Content-Type"
        assert credentials_sent(request=sent) == EXPECTED_CREDENTIAL[token_type], (
            f"beside token type {token_type!r}'s one credential header (AC-6.2)"
        )
        assert sent.json() == EXTERNAL_CONTROL_BODY, "the JSON body is sent unchanged"
    assert [(name, raw.header(name=name)) for name, _ in RAW_HEADERS] == list(RAW_HEADERS), (
        "request_raw sends a header given as request does (D5)"
    )
    assert raw.header(name=HEADER_CONTENT_TYPE) == CONTENT_TYPE_OCTET_STREAM, "beside the raw body's Content-Type"
    assert raw.body == RAW_BODY_BYTES, "the raw body is sent unchanged"
    assert credentials_sent(request=raw) == EXPECTED_CREDENTIAL[token_type], "beside the one credential header"

    sent_before = len(fake_gitlab.requests)
    not_refused: List[str] = []
    for name, value in REFUSED_HEADERS:
        headers = ((name, value),)
        attempts = (
            (client.request, dict(method="GET", path="/projects/1", headers=headers)),
            (
                client.request_raw,
                dict(
                    method="PUT",
                    path=RAW_UPLOAD_PATH,
                    data=RAW_BODY_BYTES,
                    content_type=CONTENT_TYPE_OCTET_STREAM,
                    headers=headers,
                ),
            ),
        )
        for send, arguments in attempts:
            # A request sent despite its header is answered, so it is reported below rather than by the fake.
            fake_gitlab.script_next(body={"id": 1})
            if not raises_value_error(send=send, arguments=arguments):
                not_refused.append(f"{send.__name__} with {name}: {value!r}")

    assert not_refused == [], (
        "a name the transport owns, a credential header of any token type, and a value holding CR, LF or NUL each "
        f"raise ValueError (D5); not refused: {not_refused}"
    )
    assert fake_gitlab.requests[sent_before:] == [], "a refused header is refused before anything is sent (D5)"
