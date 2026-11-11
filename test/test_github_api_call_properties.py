"""The Hypothesis property of the ``call`` command's body members (issue #28 design D2, AC-1.3).

``-F/--field NAME=JSON`` gives a body member whose value is the JSON text after the first ``=``, parsed by
``json.loads``. ``github_api.commands.call.json_member`` is that option's argparse ``type``; ``body_of`` joins the
members into the request body, one JSON object, or ``None`` when no member was given. The property: for a name drawn
from ``[a-z_][a-z0-9_]*`` and any JSON value, ``body_of(members=[json_member(text=f"{name}={json.dumps(obj=value)}")])``
is ``{name: value}``, and ``body_of(members=[])`` is ``None``.

Hypothesis is a dev dependency, so this module lives in ``test/`` and is never installed into a project (cross-wrapper
decision X1); the shipped suite under ``src/payload/test/`` stays pytest-only. It loads ``github_api`` from
``src/payload/scripts/``, put on ``sys.path`` by the ``scripts_on_path`` fixture as ``test_github_wrapper_coverage.py``
does. The test takes that fixture through ``usefixtures``, not as an argument, because Hypothesis's
``function_scoped_fixture`` health check refuses a function-scoped fixture in the signature of a ``@given`` test. The
test imports ``commands/call.py`` itself, so while the file is not written it fails on the assertion that names it.

Run: ``python scripts/run_tests.py test/test_github_api_call_properties.py``
"""

from __future__ import annotations

import importlib
import json
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
