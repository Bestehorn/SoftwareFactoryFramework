"""Tests for ``gitlab_api/families/security_governance.py``, the ``security-governance`` endpoint family of the GitLab
wrapper (issue #42, the security slice of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4 and AC-5).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the one row whose Reference is ``rest/security-governance.md``) and
``docs/api-reference/gitlab/rest/security-governance.md`` (its one section's endpoint, its heading, and the ``In``,
``Type`` and ``Required`` columns of its ``| Attribute | In | Type | Required |`` table). What is pinned:

- AC-1: the ``(method, path)`` of the family's one record, mapped to its ID, the Reference of its row;
- AC-2: ``PENDING`` is empty — the section has one endpoint (DL-003);
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``ARRAY`` for the ``array of integers`` row), and the
  ``required`` ``Param``s, exactly the Required ``yes`` rows that are not path rows;
- AC-5: the record is ``Paging.NONE`` — a ``PUT``, no list — so no record of the family is ``Paging.OFFSET`` or
  ``Paging.KEYSET``.

AC-7 has no case here: the family has no ``Paging.OFFSET`` record, and an empty parametrization would be a skip.
AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, as ``test/test_gitlab_wrapper_coverage.py`` imports the registry. The socket guard
(``gitlab_wrapper_fixtures.py``, loaded by path as ``test_gitlab_api_call.py`` loads it) is installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_security_governance.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, FrozenSet, Mapping, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
PACKAGE = "gitlab_api"
REGISTRY = f"{PACKAGE}.registry"
FAMILY_MODULE = f"{PACKAGE}.families.security_governance"
MODULE_SEPARATOR = "."

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

# The `registry.Kind` and `registry.Paging` member names the tables hold (AC-4, AC-5).
KIND_ARRAY = "ARRAY"
PAGING_NONE = "NONE"

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md: the one row linking rest/security-governance.md, as (record ID, method, path); its section,
# "Update group security settings", has that one endpoint.
OP_UPDATE_SETTINGS = "security-governance#update-group-security-settings"
RECORDS: Tuple[Tuple[str, str, str], ...] = ((OP_UPDATE_SETTINGS, "PUT", "/groups/:id/security_settings"),)
RECORD_KEYS: Dict[Tuple[str, str], str] = {(method, path): operation_id for operation_id, method, path in RECORDS}

# AC-2: the section has one endpoint, so nothing stays pending.
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset()

# rest/security-governance.md: every body row whose Kind is not SCALAR, by (record ID, attribute name) — the
# `array of integers` row. The other body row is `boolean`, a SCALAR.
TYPED_PARAMS: Dict[Tuple[str, str], str] = {
    (OP_UPDATE_SETTINGS, "projects_to_exclude"): KIND_ARRAY,
}

# rest/security-governance.md: the rows whose Required reads `yes` and whose `In` is not `path`, by record.
REQUIRED_PARAMS: Dict[str, Tuple[str, ...]] = {
    OP_UPDATE_SETTINGS: ("secret_push_protection_enabled",),
}

# AC-5: no section of the page is a `GET` headed "List" or "Get all", and none of AC-5's exceptions is on it.
LIST_IDS: Tuple[str, ...] = ()


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


def gitlab_module(*, name: str) -> ModuleType:
    """``name`` (``gitlab_api.registry``, ``gitlab_api.families.security_governance``) imported inside a test, as
    ``test/test_gitlab_wrapper_coverage.py`` imports the registry: while it is absent the test fails on this
    assertion."""
    parts = name.split(MODULE_SEPARATOR)
    owners = {MODULE_SEPARATOR.join(parts[:count]) for count in range(1, len(parts) + 1)}
    try:
        return importlib.import_module(name=name)
    except ModuleNotFoundError as missing:
        if missing.name not in owners:
            raise
        raise AssertionError(f"{name} is not importable from {SCRIPTS_DIR}: {missing}") from missing


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
    return "\n".join(lines)


def mapping_difference(*, declared: Mapping[Any, Any], expected: Mapping[Any, Any]) -> str:
    """The keys ``declared`` lacks or has beyond ``expected``, and each key whose value differs."""
    lines = [set_difference(declared=set(declared), expected=set(expected))]
    lines.extend(
        f"{key!r}: declared {declared[key]!r}, expected {expected[key]!r}"
        for key in sorted(set(declared) & set(expected))
        if declared[key] != expected[key]
    )
    return "\n".join(line for line in lines if line)


# --- AC-1, AC-2: the key has its record, nothing stays pending ------------------------------------------------------


def test_every_key_has_its_record() -> None:
    """AC-1: ``{(method, path): operation_id}`` over the family's records is ``RECORD_KEYS``, the key declared once."""
    family = gitlab_module(name=FAMILY_MODULE)
    keys = [(record.method, record.path) for record in family.OPERATIONS]
    repeated = sorted({key for key in keys if keys.count(key) > 1})
    assert not repeated, f"security_governance.OPERATIONS declares these keys more than once: {repeated}"
    declared = {(record.method, record.path): record.operation_id for record in family.OPERATIONS}
    assert declared == RECORD_KEYS, "the records are not the family's index row (AC-1):\n" + mapping_difference(
        declared=declared, expected=RECORD_KEYS
    )


def test_only_the_unmapped_keys_are_pending() -> None:
    """AC-2: ``PENDING`` is empty, the family's one index key having its record."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "security_governance.PENDING is not AC-2's set:\n" + set_difference(
        declared=pending, expected=PENDING_KEYS
    )


# --- AC-4: kinds and required attributes ----------------------------------------------------------------------------


def test_every_kind_is_its_rows_type() -> None:
    """AC-4: every ``Param`` that is not ``SCALAR``, with its ``Kind``, is the table's non-SCALAR row."""
    registry = gitlab_module(name=REGISTRY)
    family = gitlab_module(name=FAMILY_MODULE)
    declared = {
        (record.operation_id, param.name): param.kind.name
        for record in family.OPERATIONS
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }
    assert declared == TYPED_PARAMS, "the non-SCALAR Params are not the section's (AC-4):\n" + mapping_difference(
        declared=declared, expected=TYPED_PARAMS
    )


def test_the_required_attributes_are_the_sections() -> None:
    """AC-4: ``{operation_id: names}`` over the records with a ``required`` ``Param`` is the table's Required ``yes``
    rows that are not path rows."""
    family = gitlab_module(name=FAMILY_MODULE)
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required)
        for record in family.OPERATIONS
    }
    declared = {operation_id: names for operation_id, names in required.items() if names}
    expected = {operation_id: frozenset(names) for operation_id, names in REQUIRED_PARAMS.items()}
    assert declared == expected, "the required Params are not the section's (AC-4):\n" + mapping_difference(
        declared=declared, expected=expected
    )


# --- AC-5: no list record ---------------------------------------------------------------------------------------------


def test_every_list_record_has_a_case() -> None:
    """AC-5: every record's ``Paging`` is ``NONE`` — ``LIST_IDS`` is empty — so no record of the family is
    ``Paging.OFFSET`` or ``Paging.KEYSET`` and AC-7 has no case."""
    family = gitlab_module(name=FAMILY_MODULE)
    declared = {record.operation_id: record.paging.name for record in family.OPERATIONS}
    expected = {operation_id: PAGING_NONE for operation_id, _, _ in RECORDS if operation_id not in LIST_IDS}
    assert declared == expected, "the records' Paging is not AC-5's:\n" + mapping_difference(
        declared=declared, expected=expected
    )
