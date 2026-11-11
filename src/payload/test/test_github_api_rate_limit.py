"""Tests of the ``rate-limit`` records of the GitHub wrapper (``github_api/families/rate_limit.py``; issue #33 AC-1 to
AC-3, the slice test module of #28 design D8).

Installed from ``src/payload/test/test_github_api_rate_limit.py`` to ``test/test_github_api_rate_limit.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every operation ID below is transcribed from the
``rate-limit/`` rows of ``docs/api-reference/github/operations-index.md`` and the sections they link in
``rest/rate-limit.md``, never read from the records:

- ``UNPAGED_IDS``: the family's one section, ``rate-limit/get``, which has no ``Paging:`` line;
- ``RESIDUAL_PENDING``: none: every ID of the family has its record (AC-2).

The family has no ``Paging.LINK`` record, so this module has no per-page test (DL-006: an empty parametrization would
run as a skip). The structural tests read the family module imported from the ``scripts`` directory beside this suite.
No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_rate_limit.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, FrozenSet, List

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
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
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

REGISTRY = "registry"
TRANSPORT = "transport"
FAMILY = "rate_limit"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING = "PENDING"

#: AC-2: what ``PENDING`` keeps: nothing.
RESIDUAL_PENDING: FrozenSet[str] = frozenset()

#: The sections of the family without a ``Paging:`` line.
UNPAGED_IDS: FrozenSet[str] = frozenset({"rate-limit/get"})

#: The family has no section with a ``Paging:`` line and no ``200`` array with a ``Link`` header, so no record is
#: ``Paging.LINK`` (AC-3, DL-006).
PAGED_IDS: FrozenSet[str] = frozenset()
FAMILY_IDS: FrozenSet[str] = PAGED_IDS | UNPAGED_IDS
#: AC-1: the IDs ``OPERATIONS`` holds a record of, each once: every ID of the family but ``RESIDUAL_PENDING``'s.
RECORDED_IDS: FrozenSet[str] = FAMILY_IDS - RESIDUAL_PENDING


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def _family() -> ModuleType:
    """``github_api.families.rate_limit``, imported from the ``scripts`` directory beside this suite."""
    fx.import_api_module(name=REGISTRY)  # puts that ``scripts`` directory on ``sys.path``
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def _rule_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """AC-3's problems with ``record``: a ``multi_segment`` name, an item key (no record of the family pages), an API
    version other than ``API_VERSION_DEFAULT`` or a media type other than ``ACCEPT_JSON``."""
    name = record.operation_id
    problems = []
    if record.multi_segment:
        problems.append(f"{name}: multi_segment {sorted(record.multi_segment)}, expected none")
    if record.item_key is not None:
        problems.append(f"{name}: item_key {record.item_key!r}, expected None")
    if record.api_version != transport.API_VERSION_DEFAULT:
        problems.append(f"{name}: api_version {record.api_version!r}, expected {transport.API_VERSION_DEFAULT!r}")
    if record.accept != transport.ACCEPT_JSON:
        problems.append(f"{name}: accept {record.accept!r}, expected {transport.ACCEPT_JSON!r}")
    return problems


def test_only_the_residual_ids_are_pending() -> None:
    """AC-2: ``rate_limit.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == RESIDUAL_PENDING, (
        f"{FAMILY_MODULE}.PENDING holds {sorted(pending)}, expected {sorted(RESIDUAL_PENDING)}"
    )


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections to record, one each; none is ``Paging.LINK``, the family
    having no section with a ``Paging:`` line; and every record has no ``multi_segment`` name, no item key,
    ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(RECORDED_IDS), (
        f"{FAMILY_MODULE} declares {declared}, its sections to record are {sorted(RECORDED_IDS)}"
    )
    paged = frozenset(record.operation_id for record in records if record.paging == registry.Paging.LINK)
    assert paged == PAGED_IDS, f"Paging.LINK records {sorted(paged)}, sections with a Paging line {sorted(PAGED_IDS)}"
    problems = [problem for record in records for problem in _rule_problems(record=record, transport=transport)]
    assert problems == [], f"{FAMILY_MODULE}: {problems}"
