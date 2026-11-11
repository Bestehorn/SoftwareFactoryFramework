"""The Hypothesis property of the GitLab ``call`` command's ``-F/--field`` attributes (H of issue #41's design, AC-1.3).

``-F/--field NAME=JSON`` gives an attribute whose value is the JSON text after the first ``=``, parsed by
``json.loads``. ``gitlab_api.commands.call.json_member`` is that option's argparse ``type`` and returns
``(name, value)`` (design.md D2); ``gitlab_api.registry.encode`` places a BODY attribute of a JSON record natively in
``EncodedRequest.json_body`` (#13 AC-2.3). The property, for a name drawn from ``[a-z_][a-z0-9_]*`` and a value drawn
from the domain of one ``Kind`` (design.md "Correctness Properties", AC-1.3, its ``kind_values``):

- ``json_member(text=f"{name}={json.dumps(obj=value)}") == (name, value)``;
- ``registry.encode`` on a JSON record whose one BODY ``Param`` has that ``Kind``, given the value, has
  ``json_body == {name: value}``.

Each half also compares the JSON text of the two sides, since ``==`` alone holds ``1``, ``1.0`` and ``true`` equal
while JSON tells a number from a boolean. ``FILE`` is not in the domain (its value is a path, given by ``--file``), and
neither is a top-level ``null``, which ``encode`` does not send (requirements.md Residuals).

Hypothesis is a dev dependency, so this module lives in ``test/`` and is never installed into a project (cross-wrapper
decision X1); the shipped suite under ``src/payload/test/`` stays pytest-only. It loads ``gitlab_api`` from
``src/payload/scripts/``, put on ``sys.path`` by the ``scripts_on_path`` fixture, as
``test/test_github_api_call_properties.py`` does for ``github_api``. The test takes that fixture through
``usefixtures``, not as an argument, because Hypothesis's ``function_scoped_fixture`` health check refuses a
function-scoped fixture in the signature of a ``@given`` test. The test imports ``commands/call.py`` itself, after
asserting its file exists, so while the file is not written it fails on the assertion that names it.

Run: ``python scripts/run_tests.py test/test_gitlab_api_call_properties.py``
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
PACKAGE = "gitlab_api"
COMMANDS = "commands"
CALL = "call"
REGISTRY = "registry"
CALL_MODULE = f"{PACKAGE}.{COMMANDS}.{CALL}"
REGISTRY_MODULE = f"{PACKAGE}.{REGISTRY}"
CALL_FILE = SCRIPTS_DIR / PACKAGE / COMMANDS / f"{CALL}.py"
REGISTRY_FILE = SCRIPTS_DIR / PACKAGE / f"{REGISTRY}.py"

#: The record ``encode`` is given: a JSON-body ``PUT`` on a path without placeholders, so every value is an attribute.
OPERATION_ID = "properties#json-body-attribute"
METHOD_PUT = "PUT"
PLACEHOLDER_FREE_PATH = "/issues"

#: An attribute name as AC-1.3's property draws it.
NAME_PATTERN = r"[a-z_][a-z0-9_]*"
NAMES = st.from_regex(regex=NAME_PATTERN, fullmatch=True)
#: A string, number or boolean. NaN and the infinities are not JSON, so ``json.dumps`` would write text no parser
#: accepts and ``json_member`` refuses (D2).
SCALARS: st.SearchStrategy[Any] = (
    st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text()
)
#: Any JSON value: ``null``, a scalar, and arrays and objects of them.
JSON_VALUES: st.SearchStrategy[Any] = st.recursive(
    base=st.none() | SCALARS,
    extend=lambda inner: st.lists(elements=inner) | st.dictionaries(keys=st.text(), values=inner),
)
#: The domain of each ``Kind`` a ``-F`` value can take, keyed by the ``registry.Kind`` member name (design.md
#: "Correctness Properties", AC-1.3).
KIND_VALUES: dict[str, st.SearchStrategy[Any]] = {
    "SCALAR": SCALARS,
    "ARRAY": st.lists(elements=JSON_VALUES),
    "HASH": st.dictionaries(keys=st.text(), values=JSON_VALUES),
    "ARRAY_OF_HASHES": st.lists(elements=st.dictionaries(keys=st.text(), values=JSON_VALUES)),
}
#: A ``Kind`` member name with a value drawn from that ``Kind``'s domain.
KINDS_AND_VALUES: st.SearchStrategy[tuple[str, Any]] = st.sampled_from(elements=sorted(KIND_VALUES)).flatmap(
    expand=lambda kind: st.tuples(st.just(value=kind), KIND_VALUES[kind])
)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The product scripts directory first on ``sys.path``, so ``gitlab_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_product_module(*, module_name: str, module_file: Path) -> ModuleType:
    """``module_name`` from the product scripts directory; while ``module_file`` is not written, the calling test fails
    on this assertion, and a ``gitlab_api`` imported from any other directory fails it too."""
    assert module_file.is_file(), f"{module_name} is not written: {module_file} does not exist"
    module = importlib.import_module(name=module_name)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == module_file.resolve(), f"{module.__name__} was imported from {loaded_from}, not {module_file}"
    return module


def _json_body_operation(*, registry: ModuleType, name: str, kind: Any) -> Any:
    """A JSON-body record whose one ``Param`` is the BODY attribute ``name`` of ``kind``."""
    return registry.RestOperation(
        operation_id=OPERATION_ID,
        method=METHOD_PUT,
        path=PLACEHOLDER_FREE_PATH,
        params=(registry.Param(name=name, location=registry.Location.BODY, kind=kind),),
        body=registry.BodyFormat.JSON,
    )


@pytest.mark.usefixtures("scripts_on_path")
# The first example imports ``commands/call.py`` and the modules it imports; a deadline would time that one-time cost
# against the later examples and report it as unreliable timing, which is not what the property states.
@settings(deadline=None)
@given(name=NAMES, kind_and_value=KINDS_AND_VALUES)
def test_any_json_value_becomes_the_attribute_value(name: str, kind_and_value: tuple[str, Any]) -> None:
    """AC-1.3: an attribute given as ``-F NAME=<the value as JSON>`` is ``(name, value)``, and a JSON record's BODY
    attribute of that ``Kind`` given the value is sent natively as the body ``{name: value}``."""
    call = _import_product_module(module_name=CALL_MODULE, module_file=CALL_FILE)
    registry = _import_product_module(module_name=REGISTRY_MODULE, module_file=REGISTRY_FILE)
    kind_name, value = kind_and_value

    member = call.json_member(text=f"{name}={json.dumps(obj=value)}")

    assert member == (name, value)
    member_name, member_value = member
    assert json.dumps(obj=member_value) == json.dumps(obj=value)

    operation = _json_body_operation(registry=registry, name=name, kind=registry.Kind[kind_name])
    encoded = registry.encode(operation=operation, values={member_name: member_value})

    expected = {name: value}
    assert encoded.json_body == expected
    assert json.dumps(obj=encoded.json_body) == json.dumps(obj=expected)
