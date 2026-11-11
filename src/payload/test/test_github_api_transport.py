"""Tests for the GitHub wrapper's transport, ``github_api/transport.py``, and its errors, ``github_api/errors.py``.

Installed from ``src/payload/test/test_github_api_transport.py`` to ``test/test_github_api_transport.py``, beside
``scripts/github_api/``. Every request reaches the fake GitHub host of ``github_wrapper_fixtures.py`` (loaded by
path), which answers inside urllib's HTTP and HTTPS handlers: the transport's own opener, with its redirect handler and
urllib's error processing, runs unchanged, and no socket is opened. Waiting is a recording ``sleep`` and time a fixed
``clock``. Each test imports the package itself, so while a module is not written the test fails on the assertion that
names it.

Run: ``python scripts/run_tests.py test/test_github_api_transport.py`` (no network).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pytest

FIXTURES_PATH = Path(__file__).resolve().parent / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module)
    return module


fx = _load_fixtures()

TOKEN = "transport-test-token"  # pragma: allowlist secret
BEARER = f"Bearer {TOKEN}"
CLOCK = 1_800_000_000.0
API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"
VERSION_DEFAULT = "2022-11-28"
VERSION_NEXT = "2026-03-10"
VERSION_UNSUPPORTED = "2099-01-01"

METHOD_GET = "GET"
METHOD_POST = "POST"
HEADER_ACCEPT = "accept"
HEADER_API_VERSION = "x-github-api-version"
HEADER_AUTHORIZATION = "authorization"
HEADER_CONTENT_TYPE = "content-type"
HEADER_LINK = "link"
HEADER_RETRY_AFTER = "retry-after"
HEADER_REMAINING = "x-ratelimit-remaining"
HEADER_RESET = "x-ratelimit-reset"
HEADER_RESOURCE = "x-ratelimit-resource"

FIELD_NUMBER = "number"
FIELD_FULL_NAME = "full_name"
FIELD_ID = "id"
FIELD_MESSAGE = "message"
FIELD_DOCUMENTATION_URL = "documentation_url"
FIELD_STATUS = "status"
FIELD_ERRORS = "errors"
FIELD_TOTAL_COUNT = "total_count"
FIELD_WORKFLOW_RUNS = "workflow_runs"
FIELD_QUERY = "query"
FIELD_VARIABLES = "variables"
FIELD_DATA = "data"
FIELD_REPOSITORY = "repository"
FIELD_ISSUES = "issues"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_HAS_NEXT_PAGE = "hasNextPage"
FIELD_END_CURSOR = "endCursor"
FIELD_AFTER = "after"
FIELD_OWNER = "owner"
FIELD_NAME = "name"

REPO_PATH = "/repos/o/r"
ISSUES_PATH = "/repos/o/r/issues"
LOGS_PATH = "/repos/o/r/actions/runs/7/logs"
UPLOAD_URL = f"{UPLOADS}/repos/o/r/releases/3/assets"
UPLOAD_TEMPLATE = f"{UPLOAD_URL}{{?name,label}}"
ASSET_NAME = "build artifacts.zip"
ASSET_BYTES = b"PK\x03\x04 release asset bytes"
ASSET_MEDIA_TYPE = "application/zip"
LOG_ARCHIVE = b"PK\x05\x06 log archive bytes"


@dataclass(frozen=True)
class Api:
    """The two modules under test."""

    transport: ModuleType
    errors: ModuleType


def load_api() -> Api:
    """The transport and errors modules; while either is not written, the calling test fails on its assertion."""
    return Api(transport=fx.import_api_module(name="transport"), errors=fx.import_api_module(name="errors"))


class RecordingSleep:
    """Stands in for ``time.sleep``: records each wait in seconds and never waits."""

    def __init__(self) -> None:
        self.calls: List[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def make_transport(*, api: Api, sleep: RecordingSleep) -> Any:
    """A ``Transport`` on its default opener (``transport.build_opener()``), a recording sleep and a fixed clock."""
    return api.transport.Transport(token=TOKEN, sleep=sleep, clock=lambda: CLOCK)


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    host = fx.FakeGitHub()
    host.install(monkeypatch=monkeypatch)
    yield host
    host.assert_every_request_routed()


@pytest.fixture
def sleep() -> RecordingSleep:
    return RecordingSleep()


def numbered(*numbers: int) -> Tuple[Dict[str, int], ...]:
    """List items that say which they are."""
    return tuple({FIELD_NUMBER: number} for number in numbers)


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.1 — X-GitHub-Api-Version on every REST request
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("selected", "expected"),
    [(None, VERSION_DEFAULT), (VERSION_NEXT, VERSION_NEXT)],
    ids=["default", "selected-2026-03-10"],
)
def test_every_rest_request_sends_the_api_version(
    selected: Optional[str], expected: str, fake: Any, sleep: RecordingSleep
) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    with pytest.raises(ValueError):
        transport.request(method=METHOD_GET, path=REPO_PATH, api_version=VERSION_UNSUPPORTED)
    with pytest.raises(ValueError):
        list(transport.pages(path=ISSUES_PATH, query={"per_page": 1}, api_version=VERSION_UNSUPPORTED))
    assert fake.requests == [], "an API version outside API_VERSIONS is refused before anything is sent"

    version: Dict[str, str] = {} if selected is None else {"api_version": selected}
    next_page = f"{API}/repositories/42/issues?per_page=1&page=2"
    fake.route(method=METHOD_GET, url=REPO_PATH, replies=[fx.Reply(body={FIELD_FULL_NAME: "o/r"})])
    fake.route(
        method=METHOD_GET,
        url=f"{ISSUES_PATH}?per_page=1",
        replies=[fx.Reply(body=list(numbered(1)), headers={HEADER_LINK: f'<{next_page}>; rel="next"'})],
    )
    fake.route(method=METHOD_GET, url=next_page, replies=[fx.Reply(body=list(numbered(2)))])
    transport.request(method=METHOD_GET, path=REPO_PATH, **version)
    assert list(transport.pages(path=ISSUES_PATH, query={"per_page": 1}, **version)) == list(numbered(1, 2))
    if selected is None:
        fake.route(
            method=METHOD_POST,
            url=UPLOAD_URL,
            query={FIELD_NAME: ASSET_NAME},
            replies=[fx.Reply(status=201, body={FIELD_ID: 1})],
        )
        transport.upload(upload_url=UPLOAD_TEMPLATE, name=ASSET_NAME, data=ASSET_BYTES, media_type=ASSET_MEDIA_TYPE)
        fake.route(method=METHOD_GET, url=LOGS_PATH, replies=[fx.Reply(body=LOG_ARCHIVE)])
        assert transport.download(path=LOGS_PATH) == LOG_ARCHIVE

    sent = [(request.url, request.header(name=HEADER_API_VERSION)) for request in fake.requests]
    assert sent == [(request.url, expected) for request in fake.requests]
    assert len(sent) == (5 if selected is None else 3), "a call, two Link pages, and by default an upload, a download"


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.2, AC-2.3 — Link pages followed exactly as given, items in page order
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Page:
    """One page of a list: the URL it is served at, its items, and the ``link`` header it sends (``None``: none)."""

    url: str
    items: Tuple[Any, ...]
    link: Optional[str] = None

    def headers(self) -> Dict[str, str]:
        return {} if self.link is None else {HEADER_LINK: self.link}


@dataclass(frozen=True)
class LinkCase:
    """A list the transport is asked for (``path`` and ``query``) and the pages the host serves, in order. When
    ``refused``, the last page's ``rel="next"`` is on another origin: the transport raises and never requests it."""

    name: str
    path: str
    query: Tuple[Tuple[str, Any], ...]
    pages: Tuple[Page, ...]
    refused: bool = False

    def items(self) -> List[Any]:
        return [item for page in self.pages for item in page.items]


RENAMED_ISSUES = f"{API}/repositories/42/issues"
RENAMED_PULLS = f"{API}/repositories/42/pulls"
ALERTS = f"{API}/repos/o/r/dependabot/alerts"
OPAQUE_CURSOR = "Y3Vyc29yOnYyOpHOAAAAAQ%3D%3D"


def _pulls_page(*, page: int) -> str:
    return f"{RENAMED_PULLS}?state=all&per_page=1&page={page}"


LINK_CASES = (
    LinkCase(
        name="one-page-without-link",
        path=ISSUES_PATH,
        query=(("per_page", 2),),
        pages=(Page(url=f"{API}{ISSUES_PATH}?per_page=2", items=numbered(1, 2)),),
    ),
    LinkCase(
        name="page-numbers",
        path=ISSUES_PATH,
        query=(("per_page", 2),),
        pages=(
            Page(
                url=f"{API}{ISSUES_PATH}?per_page=2",
                items=numbered(1, 2),
                link=f'<{RENAMED_ISSUES}?per_page=2&page=2>; rel="next"',
            ),
            Page(
                url=f"{RENAMED_ISSUES}?per_page=2&page=2",
                items=numbered(3, 4),
                link=f'<{RENAMED_ISSUES}?per_page=2&page=3>; rel="next"',
            ),
            Page(url=f"{RENAMED_ISSUES}?per_page=2&page=3", items=numbered(5)),
        ),
    ),
    LinkCase(
        name="opaque-after-cursor",
        path="/repos/o/r/dependabot/alerts",
        query=(("per_page", 2),),
        pages=(
            Page(
                url=f"{ALERTS}?per_page=2",
                items=numbered(1, 2),
                link=f'<{ALERTS}?per_page=2&after={OPAQUE_CURSOR}>; rel="next"',
            ),
            Page(url=f"{ALERTS}?per_page=2&after={OPAQUE_CURSOR}", items=numbered(3)),
        ),
    ),
    LinkCase(
        name="next-among-prev-first-last",
        path="/repos/o/r/pulls",
        query=(("state", "all"), ("per_page", 1)),
        pages=(
            Page(
                url=f"{API}/repos/o/r/pulls?state=all&per_page=1",
                items=numbered(1),
                link=f'<{_pulls_page(page=3)}>; rel="last", <{_pulls_page(page=2)}>; rel="next"',
            ),
            Page(
                url=_pulls_page(page=2),
                items=numbered(2),
                link=(
                    f'<{_pulls_page(page=1)}>; rel="first", <{_pulls_page(page=3)}>; rel="last", '
                    f'<{_pulls_page(page=1)}>; rel="prev", <{_pulls_page(page=3)}>; rel="next"'
                ),
            ),
            Page(
                url=_pulls_page(page=3),
                items=numbered(3),
                link=f'<{_pulls_page(page=1)}>; rel="first", <{_pulls_page(page=2)}>; rel="prev"',
            ),
        ),
    ),
    LinkCase(
        name="comma-in-the-next-query",
        path=ISSUES_PATH,
        query=(("labels", "bug,ui"), ("per_page", 2)),
        pages=(
            Page(
                url=f"{API}{ISSUES_PATH}?labels=bug%2Cui&per_page=2",
                items=numbered(1, 2),
                link=(
                    f'<{RENAMED_ISSUES}?labels=bug,ui&per_page=2&page=2>; rel="next", '
                    f'<{RENAMED_ISSUES}?labels=bug,ui&per_page=2&page=2>; rel="last"'
                ),
            ),
            Page(url=f"{RENAMED_ISSUES}?labels=bug,ui&per_page=2&page=2", items=numbered(3)),
        ),
    ),
)

FOREIGN_NEXT = (
    ("next-on-another-host", "https://api.github.com.example.net/repositories/42/issues?per_page=2&page=2"),
    ("next-over-http", "http://api.github.com/repositories/42/issues?per_page=2&page=2"),
    ("next-on-another-port", "https://api.github.com:8443/repositories/42/issues?per_page=2&page=2"),
)

REFUSED_CASES = tuple(
    LinkCase(
        name=name,
        path=ISSUES_PATH,
        query=(("per_page", 2),),
        pages=(Page(url=f"{API}{ISSUES_PATH}?per_page=2", items=numbered(1, 2), link=f'<{target}>; rel="next"'),),
        refused=True,
    )
    for name, target in FOREIGN_NEXT
)


@pytest.mark.parametrize("case", LINK_CASES + REFUSED_CASES, ids=lambda case: case.name)
def test_link_pages_are_followed_as_given(case: LinkCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    for page in case.pages:
        fake.route(method=METHOD_GET, url=page.url, replies=[fx.Reply(body=list(page.items), headers=page.headers())])

    if case.refused:
        with pytest.raises(api.errors.GitHubAPIError):
            list(transport.pages(path=case.path, query=dict(case.query)))
    else:
        assert list(transport.pages(path=case.path, query=dict(case.query))) == case.items()
    assert fake.urls() == [page.url for page in case.pages], "the first URL, then each rel=next target byte for byte"


@pytest.mark.parametrize("case", LINK_CASES, ids=lambda case: case.name)
def test_wrapped_pages_return_the_item_key_items(case: LinkCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    total = len(case.items())
    for page in case.pages:
        wrapped = {FIELD_TOTAL_COUNT: total, FIELD_WORKFLOW_RUNS: list(page.items)}
        fake.route(method=METHOD_GET, url=page.url, replies=[fx.Reply(body=wrapped, headers=page.headers())])

    listed = list(transport.pages(path=case.path, query=dict(case.query), item_key=FIELD_WORKFLOW_RUNS))
    assert listed == case.items(), "the item-key lists of every page, in page order"
    assert fake.urls() == [page.url for page in case.pages]


# ---------------------------------------------------------------------------------------------------------------------
# #28 AC-1.2 — every Link page sends the Accept it is given
# ---------------------------------------------------------------------------------------------------------------------

ACCEPT_FULL = "application/vnd.github.full+json"
COMMENTS_PATH = "/repos/o/r/issues/5/comments"


def test_link_pages_send_the_given_accept(fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    assert ACCEPT_FULL != api.transport.ACCEPT_JSON, "a media type other than the transport's default"
    fake.list_route(url=COMMENTS_PATH, items=list(numbered(1, 2)))

    listed = list(transport.pages(path=COMMENTS_PATH, query={"per_page": 1}, accept=ACCEPT_FULL))
    assert listed == list(numbered(1, 2)), "the items of both pages, in page order"
    assert fake.urls() == [
        f"{API}{COMMENTS_PATH}?per_page=1",
        f"{API}{COMMENTS_PATH}?per_page=1&page=2",
    ], "the first page, then its rel=next target"
    sent = [(request.url, request.header(name=HEADER_ACCEPT)) for request in fake.requests]
    assert sent == [(request.url, ACCEPT_FULL) for request in fake.requests], "the given Accept on every page"


# ---------------------------------------------------------------------------------------------------------------------
# AC-2.4 — release assets go to the upload URL
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "expected_query"),
    [
        (None, {FIELD_NAME: [ASSET_NAME]}),
        ("Linux build", {FIELD_NAME: [ASSET_NAME], "label": ["Linux build"]}),
    ],
    ids=["name", "name-and-label"],
)
def test_an_asset_is_uploaded_to_the_upload_url(
    label: Optional[str], expected_query: Dict[str, List[str]], fake: Any, sleep: RecordingSleep
) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    for foreign in (f"{API}/repos/o/r/releases/3/assets{{?name,label}}", "https://uploads.example.com/a{?name,label}"):
        with pytest.raises(api.errors.GitHubAPIError):
            transport.upload(upload_url=foreign, name=ASSET_NAME, data=ASSET_BYTES, media_type=ASSET_MEDIA_TYPE)
    assert fake.requests == [], "an upload_url off UPLOAD_ORIGIN is refused before anything is sent"

    fake.route(method=METHOD_POST, url=UPLOAD_URL, query=expected_query, replies=[fx.Reply(status=201, body={})])
    labelled: Dict[str, str] = {} if label is None else {"label": label}
    transport.upload(
        upload_url=UPLOAD_TEMPLATE, name=ASSET_NAME, data=ASSET_BYTES, media_type=ASSET_MEDIA_TYPE, **labelled
    )
    (request,) = fake.requests
    assert request.method == METHOD_POST
    assert request.url.split("?")[0] == UPLOAD_URL, "the upload_url without its {?name,label} template"
    assert request.query == expected_query
    assert request.body == ASSET_BYTES
    assert request.header(name=HEADER_CONTENT_TYPE) == ASSET_MEDIA_TYPE


# ---------------------------------------------------------------------------------------------------------------------
# #46 AC-1.2, AC-2.2 — a raw body is sent unchanged to its root, and only a root in REST_ROOTS receives one
# ---------------------------------------------------------------------------------------------------------------------

MEDIA_TYPE_OCTET_STREAM = "application/octet-stream"
MEDIA_TYPE_TEXT = "text/plain"
MEDIA_TYPE_HTML = "text/html; charset=utf-8"
MARKDOWN_RAW_PATH = "/markdown/raw"
MARKDOWN_BYTES = b"# Title\r\n\r\nA byte that is not UTF-8: \xff\n"
RENDERED_HTML = b"<h1>Title</h1>\n<p>A byte that is not UTF-8: \xef\xbf\xbd</p>\n"
ASSETS_PATH = "/repos/o/r/releases/3/assets"
RAW_ASSET_BYTES = b"PK\x03\x04\xff\xfe\x00\x80 release asset bytes"
#: Roots outside REST_ROOTS: another host, the API host over http and on another port, and another upload host.
FOREIGN_ROOTS = (
    "https://api.github.com.example.net",
    "http://api.github.com",
    "https://api.github.com:8443",
    "https://uploads.example.com",
)


@dataclass(frozen=True)
class RawCase:
    """A body ``request_raw`` sends as given: its root, path, query, bytes and media type, and the host's answer."""

    name: str
    root: str
    path: str
    query: Tuple[Tuple[str, str], ...]
    data: bytes
    media_type: str
    answer: Any  # a ``fx.Reply``


RAW_CASES = (
    RawCase(
        name="markdown-on-the-api-root",
        root=API,
        path=MARKDOWN_RAW_PATH,
        query=(),
        data=MARKDOWN_BYTES,
        media_type=MEDIA_TYPE_TEXT,
        answer=fx.Reply(body=RENDERED_HTML, headers={HEADER_CONTENT_TYPE: MEDIA_TYPE_HTML}),
    ),
    RawCase(
        name="asset-on-the-upload-origin",
        root=UPLOADS,
        path=ASSETS_PATH,
        query=((FIELD_NAME, ASSET_NAME),),
        data=RAW_ASSET_BYTES,
        media_type=MEDIA_TYPE_OCTET_STREAM,
        answer=fx.Reply(status=201, body={FIELD_ID: 1, FIELD_NAME: ASSET_NAME}),
    ),
)


@pytest.mark.parametrize("case", RAW_CASES, ids=lambda case: case.name)
def test_a_raw_body_is_sent_unchanged_to_its_root(case: RawCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    assert set(api.transport.REST_ROOTS) == {API, UPLOADS}, "the API root and the upload origin, and no other"
    for foreign in FOREIGN_ROOTS:
        with pytest.raises(ValueError):
            transport.request_raw(
                method=METHOD_POST, root=foreign, path=case.path, data=case.data, content_type=case.media_type
            )
    assert fake.requests == [], "a root outside REST_ROOTS is refused before anything is sent"

    fake.route(method=METHOD_POST, url=f"{case.root}{case.path}", query=dict(case.query), replies=[case.answer])
    query = dict(case.query) or None
    response = transport.request_raw(
        method=METHOD_POST, root=case.root, path=case.path, query=query, data=case.data, content_type=case.media_type
    )
    transport.request_raw(
        method=METHOD_POST, root=case.root, path=case.path, query=query, data=None, content_type=case.media_type
    )

    for request in fake.requests:
        assert request.method == METHOD_POST
        assert request.url.split("?")[0] == f"{case.root}{case.path}", "the path under the root as given"
        assert request.query == {name: [value] for name, value in case.query}
        assert request.header(name=HEADER_AUTHORIZATION) == BEARER, "the credential, on that root's origin"
    with_data, without_data = fake.requests
    assert with_data.body == case.data, "the bytes as given"
    assert with_data.header(name=HEADER_CONTENT_TYPE) == case.media_type, "the media type as given"
    assert without_data.body is None, "data=None sends no body"
    assert without_data.header(name=HEADER_CONTENT_TYPE) is None, "data=None sends no Content-Type"
    assert (response.status, response.body) == (case.answer.status, case.answer.encoded()), "the host's answer"


# ---------------------------------------------------------------------------------------------------------------------
# AC-3.1 — a redirect to another origin drops the credential
# ---------------------------------------------------------------------------------------------------------------------

ENTRY_REQUEST = "request"
ENTRY_DOWNLOAD = "download"
STORAGE = "https://productionresultssa1.blob.core.windows.net/actions-results/7/logs.zip?sv=2025-01-05&sig=c2ln"
USERINFO_TARGET = "https://user:pw@api.github.com/repositories/42/actions/runs/7/logs"  # pragma: allowlist secret


@dataclass(frozen=True)
class RedirectCase:
    """A redirect chain from ``GET <API><LOGS_PATH>``: each hop's status and ``location``, and for each redirected
    request whether it carries ``Authorization``. When ``refused``, the transport raises before the last target."""

    name: str
    entry: str
    hops: Tuple[Tuple[int, str], ...]
    keeps: Tuple[bool, ...]
    refused: bool = False


REDIRECT_CASES = (
    RedirectCase(name="another-host-from-request", entry=ENTRY_REQUEST, hops=((302, STORAGE),), keeps=(False,)),
    RedirectCase(name="another-host-from-download", entry=ENTRY_DOWNLOAD, hops=((302, STORAGE),), keeps=(False,)),
    RedirectCase(
        name="back-to-the-api-host",
        entry=ENTRY_DOWNLOAD,
        hops=((302, STORAGE), (302, f"{API}/repositories/42/actions/runs/7/logs")),
        keeps=(False, False),
    ),
    RedirectCase(
        name="same-origin-301",
        entry=ENTRY_REQUEST,
        hops=((301, f"{API}/repositories/42/actions/runs/7/logs"),),
        keeps=(True,),
    ),
    RedirectCase(
        name="same-host-over-http",
        entry=ENTRY_REQUEST,
        hops=((302, "http://api.github.com/repositories/42/actions/runs/7/logs"),),
        keeps=(False,),
    ),
    RedirectCase(
        name="api-host-on-another-port",
        entry=ENTRY_REQUEST,
        hops=((302, "https://api.github.com:8443/repositories/42/actions/runs/7/logs"),),
        keeps=(False,),
    ),
    RedirectCase(
        name="api-host-with-its-default-port",
        entry=ENTRY_REQUEST,
        hops=((302, "https://api.github.com:443/repositories/42/actions/runs/7/logs"),),
        keeps=(True,),
    ),
    RedirectCase(
        name="api-host-with-an-empty-port",
        entry=ENTRY_REQUEST,
        hops=((302, "https://api.github.com:/repositories/42/actions/runs/7/logs"),),
        keeps=(True,),
    ),
    RedirectCase(
        name="userinfo-is-refused",
        entry=ENTRY_REQUEST,
        hops=((302, USERINFO_TARGET),),
        keeps=(),
        refused=True,
    ),
)


def _route_redirect_chain(*, fake: Any, case: RedirectCase) -> None:
    """Route each hop's redirect, then a ``200`` at the last target unless the transport must refuse it."""
    urls = [f"{API}{LOGS_PATH}", *(location for _, location in case.hops)]
    for index, (status, location) in enumerate(case.hops):
        fake.route(method=METHOD_GET, url=urls[index], replies=[fx.redirect(status=status, location=location)])
    if not case.refused:
        fake.route(method=METHOD_GET, url=urls[-1], replies=[fx.Reply(body=LOG_ARCHIVE)])


def _fetch(*, transport: Any, entry: str) -> Any:
    if entry == ENTRY_DOWNLOAD:
        return transport.download(path=LOGS_PATH)
    return transport.request(method=METHOD_GET, path=LOGS_PATH)


@pytest.mark.parametrize("case", REDIRECT_CASES, ids=lambda case: case.name)
def test_a_cross_origin_redirect_drops_the_credential(case: RedirectCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    _route_redirect_chain(fake=fake, case=case)

    if case.refused:
        with pytest.raises(api.errors.GitHubAPIError):
            _fetch(transport=transport, entry=case.entry)
    else:
        _fetch(transport=transport, entry=case.entry)
    reached = case.hops[:-1] if case.refused else case.hops
    assert fake.urls() == [f"{API}{LOGS_PATH}", *(location for _, location in reached)]
    carried = [request.header(name=HEADER_AUTHORIZATION) for request in fake.requests]
    assert carried == [BEARER, *(BEARER if keep else None for keep in case.keeps)]


# ---------------------------------------------------------------------------------------------------------------------
# #46 AC-3.1, AC-3.2, UB-2.2 — a same-origin 307 of a PATCH or DELETE is re-sent once; another origin's is not followed
# ---------------------------------------------------------------------------------------------------------------------

METHOD_PATCH = "PATCH"
METHOD_DELETE = "DELETE"
TEMPORARY_REDIRECT = 307
NO_CONTENT = 204
FIELD_DESCRIPTION = "description"
REPOSITORY_URL = f"{API}{REPO_PATH}"
MOVED_PATH = "/repositories/42"
MOVED_URL = f"{API}{MOVED_PATH}"
MOVED_ON_THE_DEFAULT_PORT = f"{API}:443{MOVED_PATH}"
MOVED_AGAIN_URL = f"{API}/repositories/43"
UPDATE_BODY = {FIELD_DESCRIPTION: "d"}
UPDATED = {FIELD_ID: 42, FIELD_FULL_NAME: "o/r", FIELD_DESCRIPTION: "d"}


@dataclass(frozen=True)
class ResendCase:
    """``method`` on ``REPO_PATH`` (with ``body`` as JSON) answered ``307`` with ``location``; ``target`` is that
    location resolved against the request's URL, where the re-sent request is answered ``status`` with ``answer``."""

    name: str
    method: str
    body: Optional[Dict[str, str]]
    location: str
    target: str
    status: int
    answer: Any


RESEND_CASES = (
    ResendCase(
        name="patch-absolute-location",
        method=METHOD_PATCH,
        body=UPDATE_BODY,
        location=MOVED_URL,
        target=MOVED_URL,
        status=200,
        answer=UPDATED,
    ),
    ResendCase(
        name="patch-relative-location",
        method=METHOD_PATCH,
        body=UPDATE_BODY,
        location=MOVED_PATH,
        target=MOVED_URL,
        status=200,
        answer=UPDATED,
    ),
    ResendCase(
        name="patch-location-with-the-default-port",
        method=METHOD_PATCH,
        body=UPDATE_BODY,
        location=MOVED_ON_THE_DEFAULT_PORT,
        target=MOVED_ON_THE_DEFAULT_PORT,
        status=200,
        answer=UPDATED,
    ),
    ResendCase(
        name="delete-without-a-body",
        method=METHOD_DELETE,
        body=None,
        location=MOVED_URL,
        target=MOVED_URL,
        status=NO_CONTENT,
        answer=None,
    ),
)


def _as_sent(*, request: Any) -> Tuple[str, Optional[bytes], Optional[str], Optional[str]]:
    """What a re-sent request repeats: its method, its body bytes, its ``content-type`` and its ``authorization``."""
    return (
        request.method,
        request.body,
        request.header(name=HEADER_CONTENT_TYPE),
        request.header(name=HEADER_AUTHORIZATION),
    )


@pytest.mark.parametrize("case", RESEND_CASES, ids=lambda case: case.name)
def test_a_same_origin_307_is_re_sent_once(case: ResendCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    redirected = fx.redirect(status=TEMPORARY_REDIRECT, location=case.location)
    fake.route(method=case.method, url=REPO_PATH, replies=[redirected])
    fake.route(method=case.method, url=case.target, replies=[fx.Reply(status=case.status, body=case.answer)])

    response = transport.request(method=case.method, path=REPO_PATH, body=case.body)
    assert fake.urls() == [REPOSITORY_URL, case.target], "the request, then one re-send to the resolved Location"
    first, resent = fake.requests
    assert first.json() == case.body, "the request's own JSON body, or none"
    assert first.header(name=HEADER_AUTHORIZATION) == BEARER
    assert _as_sent(request=resent) == _as_sent(request=first), "the same method, body, content-type and credential"
    assert (response.status, response.json()) == (case.status, case.answer), "the re-sent request's answer"


@pytest.mark.parametrize(
    ("method", "body"), [(METHOD_PATCH, UPDATE_BODY), (METHOD_DELETE, None)], ids=["patch", "delete"]
)
def test_a_second_307_ends_as_an_http_error(
    method: str, body: Optional[Dict[str, str]], fake: Any, sleep: RecordingSleep
) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    fake.route(method=method, url=REPO_PATH, replies=[fx.redirect(status=TEMPORARY_REDIRECT, location=MOVED_URL)])
    fake.route(method=method, url=MOVED_URL, replies=[fx.redirect(status=TEMPORARY_REDIRECT, location=MOVED_AGAIN_URL)])
    # Reached only by a transport that re-sends a second time.
    fake.route(method=method, url=MOVED_AGAIN_URL, replies=[fx.Reply(body=UPDATED)])

    with pytest.raises(api.errors.GitHubAPIError) as raised:
        transport.request(method=method, path=REPO_PATH, body=body)
    assert raised.value.status_code == TEMPORARY_REDIRECT, "the second 307, as an HTTP error"
    assert fake.urls() == [REPOSITORY_URL, MOVED_URL], "the request and its one re-send; the second 307 is not followed"


FOREIGN_307_LOCATIONS = [
    pytest.param("https://api.github.com.example.net/repositories/42", id="another-host"),
    pytest.param("http://api.github.com/repositories/42", id="the-api-host-over-http"),
    pytest.param("https://api.github.com:8443/repositories/42", id="the-api-host-on-another-port"),
    pytest.param(f"{UPLOADS}/repositories/42", id="the-upload-origin"),
]


# UB-2.2: green before the re-send exists, since urllib refuses every 307 of a PATCH. A re-send that skips the origin
# comparison sends the body and the credential to the routed foreign target, whose 200 then raises nothing.
@pytest.mark.parametrize("location", FOREIGN_307_LOCATIONS)
def test_a_cross_origin_307_is_not_followed(location: str, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    fake.route(method=METHOD_PATCH, url=REPO_PATH, replies=[fx.redirect(status=TEMPORARY_REDIRECT, location=location)])
    # Reached only by a transport that follows a 307 to another origin.
    fake.route(method=METHOD_PATCH, url=location, replies=[fx.Reply(body=UPDATED)])

    with pytest.raises(api.errors.GitHubAPIError) as raised:
        transport.request(method=METHOD_PATCH, path=REPO_PATH, body=UPDATE_BODY)
    assert raised.value.status_code == TEMPORARY_REDIRECT, "the 307, as an HTTP error"
    assert fake.urls() == [REPOSITORY_URL], "only the original request: nothing is sent to another origin"


# ---------------------------------------------------------------------------------------------------------------------
# AC-3.2, AC-3.3 — rate limits are waited out, then raise naming the limit
# ---------------------------------------------------------------------------------------------------------------------

LIMITED_PATH = "/repos/o/r/issues/1"
RATE_LIMITED = {
    FIELD_MESSAGE: "API rate limit exceeded for user ID 1.",
    FIELD_DOCUMENTATION_URL: "https://docs.github.com/rest/overview/rate-limits-for-the-rest-api",
}


@dataclass
class Limit:
    """A rate-limited answer and the wait, in seconds, it asks for at ``CLOCK``."""

    status: int
    headers: Dict[str, str]
    waited: float

    def reply(self) -> Any:
        return fx.Reply(status=self.status, body=RATE_LIMITED, headers=self.headers)


def _reset_in(*, seconds: int) -> str:
    return str(int(CLOCK) + seconds)


LIMIT_CASES = [
    pytest.param(Limit(status=429, headers={HEADER_RETRY_AFTER: "7"}, waited=7), id="429-retry-after"),
    pytest.param(
        Limit(
            status=403,
            headers={HEADER_REMAINING: "0", HEADER_RESET: _reset_in(seconds=60), HEADER_RESOURCE: "core"},
            waited=60,
        ),
        id="403-remaining-0-until-reset",
    ),
    pytest.param(
        Limit(
            status=403,
            headers={HEADER_RETRY_AFTER: "5", HEADER_REMAINING: "0", HEADER_RESET: _reset_in(seconds=3600)},
            waited=5,
        ),
        id="403-retry-after-before-reset",
    ),
]


@pytest.mark.parametrize("limit", LIMIT_CASES)
def test_a_rate_limit_is_waited_out_and_retried(limit: Limit, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    fake.route(method=METHOD_GET, url=LIMITED_PATH, replies=[limit.reply(), fx.Reply(body={FIELD_NUMBER: 1})])

    response = transport.request(method=METHOD_GET, path=LIMITED_PATH)
    assert response.json() == {FIELD_NUMBER: 1}, "the retried request's 200 body"
    assert sleep.calls == [limit.waited]
    assert fake.urls() == [f"{API}{LIMITED_PATH}"] * 2


@dataclass
class SpentCase:
    """An always-limited host: the first answer, then the one that repeats, and what the error's message names."""

    name: str
    first: Limit
    then: Limit
    named: str


PRIMARY_LIMIT = Limit(status=403, headers={HEADER_REMAINING: "0", HEADER_RESET: _reset_in(seconds=45)}, waited=45)
RETRY_AFTER_LIMIT = Limit(status=429, headers={HEADER_RETRY_AFTER: "3"}, waited=3)
SPENT_CASES = (
    SpentCase(
        name="the-bucket",
        first=Limit(status=429, headers={HEADER_RETRY_AFTER: "2", HEADER_RESOURCE: "search"}, waited=2),
        then=Limit(
            status=403,
            headers={HEADER_REMAINING: "0", HEADER_RESET: _reset_in(seconds=30), HEADER_RESOURCE: "search"},
            waited=30,
        ),
        named=json.dumps("search"),
    ),
    SpentCase(name="the-retry-after-limit", first=RETRY_AFTER_LIMIT, then=RETRY_AFTER_LIMIT, named="retry-after"),
    SpentCase(name="the-primary-limit", first=PRIMARY_LIMIT, then=PRIMARY_LIMIT, named="primary"),
)


@pytest.mark.parametrize("case", SPENT_CASES, ids=lambda case: case.name)
def test_spent_retries_raise_naming_the_limit(case: SpentCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    retries = api.transport.RATE_LIMIT_MAX_RETRIES
    assert isinstance(retries, int) and retries >= 1, "a bounded, positive number of retries"
    fake.route(method=METHOD_GET, url=LIMITED_PATH, replies=[case.first.reply(), case.then.reply()])

    with pytest.raises(api.errors.GitHubRateLimitError) as raised:
        transport.request(method=METHOD_GET, path=LIMITED_PATH)
    assert isinstance(raised.value, api.errors.GitHubAPIError)
    assert raised.value.status_code == case.then.status, "the last response's status"
    assert case.named in str(raised.value).lower(), f"the message names {case.named}"
    assert len(fake.requests) == retries + 1, "the request, then RATE_LIMIT_MAX_RETRIES retries"
    assert sleep.calls == [case.first.waited] + [case.then.waited] * (retries - 1)


# ---------------------------------------------------------------------------------------------------------------------
# AC-3.4 — any other error status raises with the documented body
# ---------------------------------------------------------------------------------------------------------------------

ERROR_PATH = "/repos/o/r/issues"
NOT_FOUND = {
    FIELD_MESSAGE: "Not Found",
    FIELD_DOCUMENTATION_URL: "https://docs.github.com/rest/issues/issues#list-repository-issues",
    FIELD_STATUS: "404",
}
VALIDATION_FAILED = {
    FIELD_MESSAGE: "Validation Failed",
    FIELD_ERRORS: [{"resource": "Issue", "code": "missing_field", "field": "title"}],
    FIELD_DOCUMENTATION_URL: "https://docs.github.com/rest/issues/issues#create-an-issue",
    FIELD_STATUS: "422",
}
FORBIDDEN = {
    FIELD_MESSAGE: "Resource not accessible by personal access token",
    FIELD_DOCUMENTATION_URL: "https://docs.github.com/rest/issues/issues#create-an-issue",
    FIELD_STATUS: "403",
}
SERVER_ERROR_PAGE = b"<html><body><h1>Server Error</h1></body></html>"


@dataclass
class ErrorCase:
    """A request, the error status and body the host answers with, and the ``details`` the error must carry."""

    method: str
    status: int
    reply_body: Any
    details: Any
    request_body: Any = field(default=None)


ERROR_CASES = [
    pytest.param(ErrorCase(method=METHOD_GET, status=404, reply_body=NOT_FOUND, details=NOT_FOUND), id="404-basic"),
    pytest.param(
        ErrorCase(
            method=METHOD_POST,
            status=422,
            reply_body=VALIDATION_FAILED,
            details=VALIDATION_FAILED,
            request_body={"body": "no title"},
        ),
        id="422-validation",
    ),
    pytest.param(
        ErrorCase(method=METHOD_GET, status=500, reply_body=SERVER_ERROR_PAGE, details=None), id="500-not-json"
    ),
    pytest.param(
        ErrorCase(method=METHOD_POST, status=403, reply_body=FORBIDDEN, details=FORBIDDEN, request_body={"title": "t"}),
        id="403-without-rate-headers",
    ),
]


@pytest.mark.parametrize("case", ERROR_CASES)
def test_an_error_status_raises_with_the_documented_body(case: ErrorCase, fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    fake.route(method=case.method, url=ERROR_PATH, replies=[fx.Reply(status=case.status, body=case.reply_body)])

    with pytest.raises(api.errors.GitHubAPIError) as raised:
        transport.request(method=case.method, path=ERROR_PATH, body=case.request_body)
    assert raised.value.status_code == case.status
    assert raised.value.details == case.details, "the parsed error body, None when it is not JSON"
    assert not isinstance(raised.value, api.errors.GitHubRateLimitError)
    assert sleep.calls == [], "no wait"
    assert len(fake.requests) == 1, "no retry"


# A 403/429 whose rate header is not an integer is no limit AC-3.2 waits out: D3 "Failures" routes it to AC-3.4's plain
# GitHubAPIError. Each case would be a limit if its non-integer value were read as 0.
NON_INTEGER_RATE_HEADERS = [
    pytest.param({HEADER_RETRY_AFTER: "Wed, 21 Oct 2026 07:28:00 GMT"}, id="retry-after-http-date"),
    pytest.param({HEADER_REMAINING: "none", HEADER_RESET: _reset_in(seconds=60)}, id="remaining-not-a-number"),
    pytest.param({HEADER_REMAINING: "0", HEADER_RESET: "1800000060.5"}, id="reset-not-an-integer"),
]


@pytest.mark.parametrize("headers", NON_INTEGER_RATE_HEADERS)
@pytest.mark.parametrize("status", [403, 429], ids=["403", "429"])
def test_a_non_integer_rate_limit_header_raises_without_retry(
    status: int, headers: Dict[str, str], fake: Any, sleep: RecordingSleep
) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    reply = fx.Reply(status=status, body=RATE_LIMITED, headers=headers)
    fake.route(method=METHOD_GET, url=LIMITED_PATH, replies=[reply])

    with pytest.raises(api.errors.GitHubAPIError) as raised:
        transport.request(method=METHOD_GET, path=LIMITED_PATH)
    assert type(raised.value) is api.errors.GitHubAPIError, "the plain GitHubAPIError, not GitHubRateLimitError"
    assert raised.value.status_code == status
    assert raised.value.details == RATE_LIMITED, "the parsed error body"
    message = str(raised.value)
    assert message.startswith(f"GitHub API {METHOD_GET} "), "D3: GitHub API <method> <url> failed: HTTP <code>"
    assert message.endswith(f" failed: HTTP {status}"), "D3: GitHub API <method> <url> failed: HTTP <code>"
    assert len(fake.requests) == 1, "no retry"
    assert sleep.calls == [], "no wait"


# ---------------------------------------------------------------------------------------------------------------------
# AC-4.1, AC-4.2, AC-4.3 — GraphQL
# ---------------------------------------------------------------------------------------------------------------------

GRAPHQL_URL = f"{API}/graphql"
REPOSITORY_QUERY = "query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { id } }"
ISSUES_QUERY = (
    "query($owner: String!, $name: String!, $after: String) { repository(owner: $owner, name: $name) "
    "{ issues(first: 2, after: $after) { nodes { number } pageInfo { hasNextPage endCursor } } } }"
)
REPOSITORY_VARIABLES = {FIELD_OWNER: "o", FIELD_NAME: "r"}


def test_graphql_posts_query_and_variables(fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    data = {FIELD_REPOSITORY: {FIELD_ID: "R_kgDOAbc"}}
    fake.route(method=METHOD_POST, url="/graphql", replies=[fx.Reply(body={FIELD_DATA: data})])

    assert transport.graphql(document=REPOSITORY_QUERY, variables=REPOSITORY_VARIABLES) == data
    (request,) = fake.requests
    assert request.method == METHOD_POST
    assert request.url == GRAPHQL_URL
    assert request.json() == {FIELD_QUERY: REPOSITORY_QUERY, FIELD_VARIABLES: REPOSITORY_VARIABLES}


def _connection_page(*, numbers: Tuple[int, ...], has_next: bool, end_cursor: str) -> Dict[str, Any]:
    connection = {
        FIELD_NODES: list(numbered(*numbers)),
        FIELD_PAGE_INFO: {FIELD_HAS_NEXT_PAGE: has_next, FIELD_END_CURSOR: end_cursor},
    }
    return {FIELD_DATA: {FIELD_REPOSITORY: {FIELD_ISSUES: connection}}}


def test_graphql_follows_page_info_cursors(fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    pages = [
        _connection_page(numbers=(1, 2), has_next=True, end_cursor="Y3Vyc29yOjI="),
        _connection_page(numbers=(3,), has_next=True, end_cursor="Y3Vyc29yOjM="),
        _connection_page(numbers=(4, 5), has_next=False, end_cursor="Y3Vyc29yOjU="),
    ]
    fake.route(method=METHOD_POST, url="/graphql", replies=[fx.Reply(body=page) for page in pages])

    nodes = transport.graphql_nodes(
        document=ISSUES_QUERY, variables=REPOSITORY_VARIABLES, connection=(FIELD_REPOSITORY, FIELD_ISSUES)
    )
    assert list(nodes) == list(numbered(1, 2, 3, 4, 5)), "the nodes of every page, in page order"
    sent = [request.json()[FIELD_VARIABLES] for request in fake.requests]
    assert sent == [
        {**REPOSITORY_VARIABLES, FIELD_AFTER: None},
        {**REPOSITORY_VARIABLES, FIELD_AFTER: "Y3Vyc29yOjI="},
        {**REPOSITORY_VARIABLES, FIELD_AFTER: "Y3Vyc29yOjM="},
    ], "after is the previous endCursor, and nothing is sent after hasNextPage: false"
    assert [request.json()[FIELD_QUERY] for request in fake.requests] == [ISSUES_QUERY] * 3


GRAPHQL_ERRORS = [
    {
        "type": "NOT_FOUND",
        "path": [FIELD_REPOSITORY],
        "locations": [{"line": 1, "column": 41}],
        FIELD_MESSAGE: "Could not resolve to a Repository with the name 'o/missing'.",
    }
]


@pytest.mark.parametrize(
    "data",
    [{"viewer": {"login": "octocat"}, FIELD_REPOSITORY: None}, None],
    ids=["errors-with-data", "errors-with-data-null"],
)
def test_graphql_errors_raise_even_with_200(data: Optional[Dict[str, Any]], fake: Any, sleep: RecordingSleep) -> None:
    api = load_api()
    transport = make_transport(api=api, sleep=sleep)
    fake.route(
        method=METHOD_POST, url="/graphql", replies=[fx.Reply(body={FIELD_DATA: data, FIELD_ERRORS: GRAPHQL_ERRORS})]
    )

    with pytest.raises(api.errors.GitHubGraphQLResponseError) as raised:
        transport.graphql(document=REPOSITORY_QUERY, variables=REPOSITORY_VARIABLES)
    assert isinstance(raised.value, api.errors.GitHubAPIError)
    assert raised.value.status_code == 200
    assert raised.value.details == GRAPHQL_ERRORS
