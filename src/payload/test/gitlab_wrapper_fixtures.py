"""The fake GitLab host every GitLab wrapper suite installs: scripted responses, recorded requests, no network.

Not a test module: pytest does not collect it (its name does not match ``test_*.py``). A suite loads it by path from
its own directory (``importlib.util.spec_from_file_location``, as ``test_wrapper_delivery.load`` loads a wrapper) and
installs both guards as autouse fixtures::

    fake = FakeGitLab().install(monkeypatch=monkeypatch)
    install_socket_guard(monkeypatch=monkeypatch)
    fake.script(method="GET", url=f"{REST_BASE}/projects/1", body={"id": 1})
    ...  # the code under test sends its requests through any urllib opener
    assert [(request.method, request.url) for request in fake.requests] == [("GET", f"{REST_BASE}/projects/1")]

``FakeGitLab.install`` replaces ``urllib.request.HTTPSHandler.https_open`` and ``urllib.request.HTTPHandler.http_open``
for the test, so every opener in the process reaches the fake and no socket opens. Each scripted
``(status, headers, body)`` is served for its exact method and URL (the query string included), in the order it was
scripted, as a ``urllib.response.addinfourl`` with ``msg`` set and an ``http.client.HTTPMessage``: urllib's error
processor, its redirect machinery and any handler the wrapper adds run unchanged (``HTTPErrorProcessor.http_response``
reads ``code``, ``msg`` and ``info()``). Every request is recorded — method, URL, headers as urllib stores them
(``Private-token``), body. ``FakeGitLab.script_next`` queues a response for whatever request comes next with no scripted
response left for its method and URL; those are served in the order they were queued. An unscripted request with no
such response queued is recorded and then raises ``AssertionError``, which no ``OSError`` handler of the code under
test can swallow.

``install_socket_guard`` makes ``socket.socket.connect`` (and ``connect_ex``) raise ``AssertionError``, so a request
that bypasses the fake fails the test instead of reaching the network.

A suite that drives the product's entry script in-process uses the three entry-script helpers::

    write_config(root=tmp_path, config=config)  # config: the JSON object of config/gitlab.json, hostname HOST
    monkeypatch.chdir(tmp_path)  # the entry script reads config/gitlab.json from the working directory
    code = run_main(wrapper=load_wrapper(module_name="gitlab_wrapper_under_test"), argv=["issue", "show", "7"])

``load_wrapper`` loads ``src/payload/scripts/gitlab_wrapper.py`` by path, afresh on every call and without a
``sys.modules`` entry; ``run_main`` is ``main(argv=...)``'s exit code — its return value, or the code of the
``SystemExit`` it raised (argparse exits 2 on a usage error).

Python 3.9 standard library plus pytest. The module deliberately has no ``from __future__ import annotations``: its
dataclasses then need no ``sys.modules`` entry, so a suite may load it with or without registering it.
"""

import http.client
import importlib.util
import inspect
import io
import json
import socket
import urllib.request
import urllib.response
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Deque, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import pytest

HOST = "gitlab.example.com"
REST_BASE = f"https://{HOST}/api/v4"
GRAPHQL_URL = f"https://{HOST}/api/graphql"

HEADER_CONTENT_TYPE = "Content-Type"
CONTENT_TYPE_JSON = "application/json"
TEXT_ENCODING = "utf-8"

# The product's entry script, and where it reads its config from: config/gitlab.json under the working directory.
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
WRAPPER_FILE = SCRIPTS_DIR / "gitlab_wrapper.py"
CONFIG_DIR = "config"
CONFIG_FILE_NAME = "gitlab.json"
MAIN_ARGV = "argv"

HeaderItems = Union[Mapping[str, str], Sequence[Tuple[str, str]]]


@dataclass(frozen=True)
class RecordedRequest:
    """One request the code under test sent, as urllib handed it to the HTTP(S) handler."""

    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[bytes]

    def header(self, *, name: str) -> Optional[str]:
        """The value of header ``name``, compared case-insensitively; ``None`` when the request did not carry it."""
        wanted = name.lower()
        for key, value in self.headers.items():
            if key.lower() == wanted:
                return value
        return None

    def json(self) -> Any:
        """The body decoded as JSON."""
        assert self.body is not None, f"{self.method} {self.url} carried no body"
        return json.loads(self.body.decode(TEXT_ENCODING))


@dataclass(frozen=True)
class ScriptedResponse:
    """One response the fake serves: status, headers in order (a name may repeat), raw body."""

    status: int
    headers: Tuple[Tuple[str, str], ...]
    body: bytes


class FakeResponse(urllib.response.addinfourl):
    """``addinfourl`` carrying the reason phrase in ``msg``, which ``HTTPErrorProcessor.http_response`` reads."""

    def __init__(self, *, scripted: ScriptedResponse, url: str) -> None:
        message = http.client.HTTPMessage()
        for name, value in scripted.headers:
            message[name] = value
        super().__init__(fp=io.BytesIO(scripted.body), headers=message, url=url, code=scripted.status)
        self.msg = http.client.responses.get(scripted.status, "")
        self.reason = self.msg


def _header_items(*, headers: HeaderItems) -> List[Tuple[str, str]]:
    if isinstance(headers, Mapping):
        return [(str(name), str(value)) for name, value in headers.items()]
    return [(str(name), str(value)) for name, value in headers]


def _scripted_response(*, status: int, headers: HeaderItems, body: Any) -> ScriptedResponse:
    """``body``: bytes and text are sent verbatim, ``None`` as an empty body, anything else as JSON — with
    ``Content-Type: application/json`` unless ``headers`` names a content type."""
    items = _header_items(headers=headers)
    if body is None:
        raw = b""
    elif isinstance(body, bytes):
        raw = body
    elif isinstance(body, str):
        raw = body.encode(TEXT_ENCODING)
    else:
        raw = json.dumps(body).encode(TEXT_ENCODING)
        if not any(name.lower() == HEADER_CONTENT_TYPE.lower() for name, _ in items):
            items.append((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON))
    return ScriptedResponse(status=status, headers=tuple(items), body=raw)


def _sent_headers(*, request: urllib.request.Request) -> Dict[str, str]:
    """The headers urllib sends, merged as ``AbstractHTTPHandler.do_open`` merges them (unredirected ones first)."""
    headers = dict(request.unredirected_hdrs)
    headers.update({name: value for name, value in request.headers.items() if name not in headers})
    return headers


def _sent_body(*, request: urllib.request.Request) -> Optional[bytes]:
    data = request.data
    if data is None:
        return None
    assert isinstance(data, (bytes, bytearray)), (
        f"{request.get_method()} {request.full_url} sent a {type(data).__name__} body; the fake records bytes bodies"
    )
    return bytes(data)


class FakeGitLab:
    """A scripted GitLab host behind every urllib opener of the process (see the module docstring)."""

    def __init__(self) -> None:
        self.requests: List[RecordedRequest] = []
        self._scripted: Dict[Tuple[str, str], Deque[ScriptedResponse]] = {}
        self._unmatched: Deque[ScriptedResponse] = deque()

    def install(self, *, monkeypatch: pytest.MonkeyPatch) -> "FakeGitLab":
        """Route ``https_open`` and ``http_open`` of every handler to this fake for the rest of the test."""
        fake = self

        def serve(handler: urllib.request.BaseHandler, req: urllib.request.Request) -> FakeResponse:
            return fake.serve(request=req)

        monkeypatch.setattr(urllib.request.HTTPSHandler, "https_open", serve)
        monkeypatch.setattr(urllib.request.HTTPHandler, "http_open", serve)
        return self

    def script(
        self,
        *,
        method: str,
        url: str,
        status: int = 200,
        headers: HeaderItems = (),
        body: Any = None,
    ) -> None:
        """Queue one response for ``method`` and the exact ``url``; responses for one key are served in order."""
        key = (method.upper(), url)
        self._scripted.setdefault(key, deque()).append(_scripted_response(status=status, headers=headers, body=body))

    def script_next(self, *, status: int = 200, headers: HeaderItems = (), body: Any = None) -> None:
        """Queue one response for the next request that has no scripted response left for its method and URL; such
        responses are served in the order they were queued, and the request is recorded as every request is."""
        self._unmatched.append(_scripted_response(status=status, headers=headers, body=body))

    def remaining(self) -> List[Tuple[str, str]]:
        """``(method, url)`` of every scripted response not served yet."""
        return [key for key, queue in self._scripted.items() for _ in queue]

    def serve(self, *, request: urllib.request.Request) -> FakeResponse:
        """Record ``request``, then answer it with its next scripted response, else with the next ``script_next``
        response, else raise ``AssertionError``."""
        recorded = RecordedRequest(
            method=request.get_method(),
            url=request.full_url,
            headers=_sent_headers(request=request),
            body=_sent_body(request=request),
        )
        self.requests.append(recorded)
        queue = self._scripted.get((recorded.method.upper(), recorded.url))
        if queue:
            return FakeResponse(scripted=queue.popleft(), url=recorded.url)
        if self._unmatched:
            return FakeResponse(scripted=self._unmatched.popleft(), url=recorded.url)
        raise AssertionError(
            f"unscripted request: {recorded.method} {recorded.url} (still scripted: {self.remaining()})"
        )


def install_socket_guard(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every outgoing socket connection of the test raise ``AssertionError``."""

    def refuse(sock: socket.socket, address: Any) -> None:
        raise AssertionError(f"network access attempted: connect to {address!r}")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


# --- The entry script, run in-process --------------------------------------------------------------------------------


def load_wrapper(*, module_name: str) -> ModuleType:
    """``src/payload/scripts/gitlab_wrapper.py``, loaded by path afresh under ``module_name`` and not registered in
    ``sys.modules``, as ``test_wrapper_delivery.load`` loads a wrapper; the script's own bootstrap puts its directory
    on ``sys.path``."""
    spec = importlib.util.spec_from_file_location(name=module_name, location=WRAPPER_FILE)
    assert spec and spec.loader, f"{WRAPPER_FILE} is missing"
    module = importlib.util.module_from_spec(spec=spec)
    spec.loader.exec_module(module=module)
    return module


def write_config(*, root: Path, config: Mapping[str, Any]) -> Path:
    """Write ``config`` as ``config/gitlab.json`` under ``root``, creating ``config/``; the file written."""
    config_dir = root / CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / CONFIG_FILE_NAME
    config_file.write_text(data=json.dumps(obj=dict(config)), encoding=TEXT_ENCODING)
    return config_file


def run_main(*, wrapper: ModuleType, argv: Sequence[str]) -> Any:
    """``wrapper.main(argv=argv)``'s exit code: its return value, or the code of the ``SystemExit`` it raised."""
    assert MAIN_ARGV in inspect.signature(obj=wrapper.main).parameters, (
        "the entry script's main takes the argument vector: main(argv=None) -> int"
    )
    try:
        return wrapper.main(argv=list(argv))
    except SystemExit as exit_request:
        return exit_request.code
