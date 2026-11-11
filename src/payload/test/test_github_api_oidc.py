"""Tests of the ``oidc`` records of the GitHub wrapper (``github_api/families/oidc.py``; issue #33 AC-2 and AC-3, the
slice test module of #28 design D8).

Installed from ``src/payload/test/test_github_api_oidc.py`` to ``test/test_github_api_oidc.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every operation ID below is transcribed from
``docs/api-reference/github/operations-index.md``, whose ``oidc/`` rows link the ``oidc`` sections of
``rest/actions.md``, and from those sections, never read from the records:

- ``FAMILY_IDS``: the family's sections. None has a ``Paging:`` line, and none answers ``200`` with a ``Link`` header
  (the two ``list-oidc-custom-property-inclusions-for-*`` sections answer an array without one), so no record pages
  and the family has no per-page test (issue #33 DL-006); "Lists wrapped in an object" names no ``oidc`` operation, so
  no record has an item key.

The structural tests read the family module imported from the ``scripts`` directory beside this suite. No test opens
a connection.

Run: ``python scripts/run_tests.py test/test_github_api_oidc.py`` (no network).
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
FAMILY = "oidc"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING = "PENDING"

#: AC-2: what ``PENDING`` keeps. The slice's residuals, ``markdown/render-raw`` and
#: ``copilot/set-copilot-content-exclusion-for-organization``, are not this family's.
RESIDUAL_PENDING: FrozenSet[str] = frozenset()

#: The ``oidc`` sections of ``rest/actions.md``, the targets of the index's ``oidc/`` rows.
FAMILY_IDS: FrozenSet[str] = frozenset(
    {
        "oidc/list-oidc-custom-property-inclusions-for-enterprise",
        "oidc/create-oidc-custom-property-inclusion-for-enterprise",
        "oidc/delete-oidc-custom-property-inclusion-for-enterprise",
        "oidc/list-oidc-custom-property-inclusions-for-org",
        "oidc/create-oidc-custom-property-inclusion-for-org",
        "oidc/delete-oidc-custom-property-inclusion-for-org",
        "oidc/get-oidc-custom-sub-template-for-org",
        "oidc/update-oidc-custom-sub-template-for-org",
    }
)
#: The sections with a ``Paging:`` line or an array ``200`` with a ``Link`` header: none.
PAGED_IDS: FrozenSet[str] = frozenset()


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def _family() -> ModuleType:
    """``github_api.families.oidc``, imported from the ``scripts`` directory beside this suite."""
    fx.import_api_module(name=REGISTRY)  # puts that ``scripts`` directory on ``sys.path``
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def _rule_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """AC-3's problems with ``record``: a ``multi_segment`` name, an item key (no section of the family has one), an
    API version other than ``API_VERSION_DEFAULT`` or a media type other than ``ACCEPT_JSON``."""
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
    """AC-2: ``oidc.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == RESIDUAL_PENDING, f"{FAMILY_MODULE}.PENDING still holds {sorted(pending - RESIDUAL_PENDING)}"


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections, one each; none is ``Paging.LINK``, since no section pages; and
    every record has no ``multi_segment`` name, no item key, ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(FAMILY_IDS), f"{FAMILY_MODULE} declares {declared}, its sections are {sorted(FAMILY_IDS)}"
    paged = frozenset(record.operation_id for record in records if record.paging == registry.Paging.LINK)
    assert paged == PAGED_IDS, f"Paging.LINK records {sorted(paged)}, no section of the family pages"
    problems = [problem for record in records for problem in _rule_problems(record=record, transport=transport)]
    assert problems == [], f"{FAMILY_MODULE}: {problems}"
