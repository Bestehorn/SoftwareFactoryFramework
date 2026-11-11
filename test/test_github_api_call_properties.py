"""The Hypothesis properties of the ``call`` command's request bodies: its body members (issue #28 design D2, AC-1.3)
and its raw body (issue #46 design D1 and D2, AC-1.2).

``-F/--field NAME=JSON`` gives a body member whose value is the JSON text after the first ``=``, parsed by
``json.loads``. ``github_api.commands.call.json_member`` is that option's argparse ``type``; ``body_of`` joins the
members into the request body, one JSON object, or ``None`` when no member was given. The property: for a name drawn
from ``[a-z_][a-z0-9_]*`` and any JSON value, ``body_of(members=[json_member(text=f"{name}={json.dumps(obj=value)}")])``
is ``{name: value}``, and ``body_of(members=[])`` is ``None``.

``--input FILE`` gives the raw body: ``github_api.commands.call.read_input`` is that option's argparse ``type`` and
returns the file's bytes, which ``Transport.request_raw`` sends unchanged with the record's media type. The property:
for any bytes and each of ``application/octet-stream`` and ``text/plain``, the bytes written to a file in a
``tempfile.TemporaryDirectory`` come back from ``read_input(text=<the file's path>)``, and ``request_raw`` of them on
``https://api.github.com`` + ``/markdown/raw`` sends one request whose body is exactly those bytes and whose
``content-type`` is that media type. The fake host is ``src/payload/test/github_wrapper_fixtures.py``, loaded by path
as ``test_github_wrapper_contract.py`` loads it, and installed for each example in its own
``pytest.MonkeyPatch.context()``, with every socket connection refused, since Hypothesis refuses a function-scoped
fixture such as ``monkeypatch`` in the signature of a ``@given`` test.

Hypothesis is a dev dependency, so this module lives in ``test/`` and is never installed into a project (cross-wrapper
decision X1); the shipped suite under ``src/payload/test/`` stays pytest-only. It loads ``github_api`` from
``src/payload/scripts/``, put on ``sys.path`` by the ``scripts_on_path`` fixture as ``test_github_wrapper_coverage.py``
does. Each test takes that fixture through ``usefixtures``, not as an argument, because Hypothesis's
``function_scoped_fixture`` health check refuses a function-scoped fixture in the signature of a ``@given`` test. Each
test imports ``commands/call.py`` itself, so while the file is not written it fails on the assertion that names it.

Run: ``python scripts/run_tests.py test/test_github_api_call_properties.py``
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "src" / "payload" / "scripts"
PACKAGE = "github_api"
COMMANDS = "commands"
CALL = "call"
CALL_MODULE = f"{PACKAGE}.{COMMANDS}.{CALL}"
CALL_FILE = SCRIPTS_DIR / PACKAGE / COMMANDS / f"{CALL}.py"

#: A body member name as AC-1.3's property draws it.
NAME_PATTERN = r"[a-z_][a-z0-9_]*"
NAMES = st.from_regex(regex=NAME_PATTERN, fullmatch=True)
#: Any JSON value: ``null``, a boolean, a number, a string, and arrays and objects of them (design § Correctness
#: Properties, AC-1.3). NaN and the infinities are not JSON, so ``json.dumps`` would write text no parser accepts.
JSON_VALUES: st.SearchStrategy[Any] = st.recursive(
    base=st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(),
    extend=lambda inner: st.lists(elements=inner) | st.dictionaries(keys=st.text(), values=inner),
)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The product scripts directory first on ``sys.path``, so ``github_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_call_module() -> ModuleType:
    """``github_api.commands.call`` from the product scripts directory; while its file is not written, the calling test
    fails on this assertion, and a ``github_api`` imported from any other directory fails it too."""
    assert CALL_FILE.is_file(), f"{PACKAGE}/{COMMANDS}/{CALL}.py is not written: {CALL_FILE} does not exist"
    module = importlib.import_module(name=CALL_MODULE)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == CALL_FILE.resolve(), f"{module.__name__} was imported from {loaded_from}, not {CALL_FILE}"
    return module


@pytest.mark.usefixtures("scripts_on_path")
# The first example imports ``commands/call.py`` and the modules it imports; a deadline would time that one-time cost
# against the later examples and report it as unreliable timing, which is not what the property states.
@settings(deadline=None)
@given(name=NAMES, value=JSON_VALUES)
def test_any_json_value_becomes_the_body_member(name: str, value: Any) -> None:
    """AC-1.3: a ``-F/--field`` member given as ``NAME=<the value as JSON>`` makes the body ``{name: value}``, and no
    member makes no body. The body also serializes as ``{name: value}`` does, since ``==`` alone holds ``1``, ``1.0``
    and ``true`` equal while JSON tells a number from a boolean."""
    call = _import_call_module()

    assert call.body_of(members=[]) is None

    expected = {name: value}
    body = call.body_of(members=[call.json_member(text=f"{name}={json.dumps(obj=value)}")])

    assert body == expected
    assert json.dumps(obj=body) == json.dumps(obj=expected)


# ---------------------------------------------------------------------------------------------------------------------
# Issue #46 AC-1.2 — the raw body: any bytes ``--input`` reads are sent as given
# ---------------------------------------------------------------------------------------------------------------------

FIXTURES_PATH = ROOT / "src" / "payload" / "test" / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"
TRANSPORT = "transport"
TRANSPORT_MODULE = f"{PACKAGE}.{TRANSPORT}"
TRANSPORT_FILE = SCRIPTS_DIR / PACKAGE / f"{TRANSPORT}.py"
#: The request the property sends and the two media types it sends it as (design D2), as this module's own constants.
API_ROOT = "https://api.github.com"
MARKDOWN_RAW_PATH = "/markdown/raw"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
CONTENT_TYPE_TEXT = "text/plain"
RAW_MEDIA_TYPES = (CONTENT_TYPE_OCTET_STREAM, CONTENT_TYPE_TEXT)
RAW_MEDIA_TYPE_IDS = ("octet-stream", "text-plain")
INPUT_FILE_NAME = "body"
#: The fake host's answer to the request: rendered HTML, which the property does not judge.
RENDERED_HTML = b"<p>rendered</p>\n"
MEDIA_TYPE_HTML = "text/html; charset=utf-8"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()


def _import_transport_module() -> ModuleType:
    """``github_api.transport`` from the product scripts directory; one imported from any other directory fails the
    calling test on this assertion."""
    module = importlib.import_module(name=TRANSPORT_MODULE)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == TRANSPORT_FILE.resolve(), f"{module.__name__} was imported from {loaded_from}"
    return module


@pytest.mark.usefixtures("scripts_on_path")
@pytest.mark.parametrize(argnames="media_type", argvalues=RAW_MEDIA_TYPES, ids=RAW_MEDIA_TYPE_IDS)
# As for the property above: the first example's imports would count against a deadline as unreliable timing.
@settings(deadline=None)
@given(body=st.binary())
def test_any_bytes_are_sent_as_given(media_type: str, body: bytes) -> None:
    """Issue #46 AC-1.2: any bytes, written to a file, come back from ``read_input(text=<the file's path>)`` as they
    are, and ``Transport.request_raw`` of them as ``media_type`` sends one request whose body is exactly those bytes,
    none added, removed, re-encoded or reordered, and whose ``content-type`` is ``media_type``."""
    call = _import_call_module()
    transport = _import_transport_module()

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / INPUT_FILE_NAME
        path.write_bytes(data=body)
        read = call.read_input(text=str(path))

    assert read == body, "read_input did not return the file's bytes"

    with pytest.MonkeyPatch.context() as patch:
        fx.refuse_connections(monkeypatch=patch)
        host = fx.FakeGitHub()
        answer = fx.Reply(body=RENDERED_HTML, headers={fx.HEADER_CONTENT_TYPE: MEDIA_TYPE_HTML})
        host.route(method=fx.METHOD_POST, url=MARKDOWN_RAW_PATH, replies=(answer,))
        host.install(monkeypatch=patch)
        transport.Transport(token=fx.FIXTURE_TOKEN).request_raw(
            method=fx.METHOD_POST, root=API_ROOT, path=MARKDOWN_RAW_PATH, data=read, content_type=media_type
        )

    host.assert_every_request_routed()
    assert len(host.requests) == 1, f"{len(host.requests)} requests: {host.urls()}"
    sent = host.requests[0]
    assert sent.url == f"{API_ROOT}{MARKDOWN_RAW_PATH}"
    assert sent.body == body, "the request's body is not the bytes given"
    assert sent.header(name=fx.HEADER_CONTENT_TYPE) == media_type
