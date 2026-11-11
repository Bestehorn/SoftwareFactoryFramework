"""Tests of the ``agent-merge`` records of the GitHub wrapper (``github_api/families/agent_merge.py``; issue #33 AC-2,
AC-3 and AC-6, the slice test module of #28 design D8).

Installed from ``src/payload/test/test_github_api_agent_merge.py`` to ``test/test_github_api_agent_merge.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. The family's index rows link the ``agent-merge`` part of
``docs/api-reference/github/rest/pulls.md``; every operation ID and argument below is transcribed from
``operations-index.md`` and those sections, never read from the records or from ``commands/call.py``:

- ``PAGED_IDS``: the sections with a ``Paging:`` line, of which the family has none (and no ``200`` array with a
  ``Link`` header), so no record is ``Paging.LINK`` and the module has no per-page test (an empty parametrization would
  run as a skip, issue #33 DL-006);
- ``UNPAGED_IDS``: the sections without a ``Paging:`` line, which is all three;
- ``BRANCH_WRITING_CALLS``: AC-6's record of this family, called with every path parameter but ``owner`` and ``repo``
  and every required body member its section documents, so only a refusal keeps the request from being sent.

``test_a_branch_writing_record_is_refused`` runs that call with ``github_wrapper_fixtures.run_product_case`` (loaded by
path, as ``test_github_api_call.py`` loads it) in the fixture project (``origin`` ``o/r``) and expects exit 2, no
request and a log record naming the ID and that no subcommand sends it. The structural tests read the family module
imported from the ``scripts`` directory beside this suite. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_agent_merge.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, FrozenSet, List, Mapping, Optional, Tuple

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
FAMILY = "agent_merge"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING = "PENDING"

AC_6 = "AC-6"
CALL = "call"
OPTION_PATH = "--path"
OPTION_FIELD = "--field"
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

#: AC-2: what ``PENDING`` keeps. Neither residual of the slice (``markdown/render-raw``,
#: ``copilot/set-copilot-content-exclusion-for-organization``) is this family's.
RESIDUAL_PENDING: FrozenSet[str] = frozenset()

#: The sections of the ``agent-merge`` part of ``rest/pulls.md`` with a ``Paging:`` line: none.
PAGED_IDS: FrozenSet[str] = frozenset()
#: The sections of the ``agent-merge`` part of ``rest/pulls.md`` without a ``Paging:`` line.
UNPAGED_IDS: FrozenSet[str] = frozenset(
    {
        "agent-merge/delete-agent-merge-enrollment",
        "agent-merge/get-agent-merge-enrollment",
        "agent-merge/put-agent-merge-enrollment",
    }
)
FAMILY_IDS: FrozenSet[str] = PAGED_IDS | UNPAGED_IDS
#: The item key each record must carry: ``None`` for every one, as none pages (AC-3).
ITEM_KEYS: Mapping[str, Optional[str]] = {}

#: The ``pull_number`` the case gives (an ``integer (int64)`` path parameter, min ``1``).
PARAM_PULL_NUMBER = "pull_number"
PULL_NUMBER = "77"
#: ``allowed_actions``: a required ``array of string``, items one of ``fix_ci``, ``resolve_merge_conflicts``.
ALLOWED_ACTIONS = ["fix_ci"]


@dataclass(frozen=True)
class BranchWritingCall:
    """An AC-6 record of this family and the arguments after ``call <id>``: every path parameter but ``owner`` and
    ``repo``, and every required body member its section documents."""

    operation_id: str
    arguments: Tuple[str, ...]


#: AC-6: the record of this family whose call writes a branch (it lets the agent push fixes to the pull request).
BRANCH_WRITING_CALLS: Tuple[BranchWritingCall, ...] = (
    BranchWritingCall(
        operation_id="agent-merge/put-agent-merge-enrollment",
        arguments=(
            OPTION_PATH,
            f"{PARAM_PULL_NUMBER}={PULL_NUMBER}",
            OPTION_FIELD,
            f"allowed_actions={json.dumps(obj=ALLOWED_ACTIONS)}",
        ),
    ),
)
#: AC-6's refusal: the log record says that no subcommand sends the operation (``commands/call.py`` maps it to none).
NO_SUBCOMMAND_SENDS_IT = r"(?i)\bno\b[\w\s-]*\bsubcommand\b[\w\s-]*\bsends\b"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def refusal_case(*, branch_writing: BranchWritingCall) -> Any:
    """AC-6's golden case of ``branch_writing``: exit 2, nothing on standard output, no request, and one log record
    naming the ID as ``json.dumps`` renders it (#28 D4) and that no subcommand sends it."""
    return fx.GoldenCase(
        name=f"{AC_6}/exit-2/{branch_writing.operation_id}",
        argv=(CALL, branch_writing.operation_id, *branch_writing.arguments),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(re.escape(json.dumps(obj=branch_writing.operation_id)), NO_SUBCOMMAND_SENDS_IT), withheld=()
        ),
    )


def branch_writing_name(branch_writing: BranchWritingCall) -> str:
    """The test id of a ``BRANCH_WRITING_CALLS`` row."""
    return branch_writing.operation_id


def _family() -> ModuleType:
    """``github_api.families.agent_merge``, imported from the ``scripts`` directory beside this suite."""
    fx.import_api_module(name=REGISTRY)  # puts that ``scripts`` directory on ``sys.path``
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def _rule_problems(*, record: Any, transport: ModuleType) -> List[str]:
    """AC-3's problems with ``record``: a ``multi_segment`` name, an item key other than ``ITEM_KEYS`` gives it, an API
    version other than ``API_VERSION_DEFAULT`` or a media type other than ``ACCEPT_JSON``."""
    name = record.operation_id
    expected_key = ITEM_KEYS.get(name)
    problems = []
    if record.multi_segment:
        problems.append(f"{name}: multi_segment {sorted(record.multi_segment)}, expected none")
    if record.item_key != expected_key:
        problems.append(f"{name}: item_key {record.item_key!r}, expected {expected_key!r}")
    if record.api_version != transport.API_VERSION_DEFAULT:
        problems.append(f"{name}: api_version {record.api_version!r}, expected {transport.API_VERSION_DEFAULT!r}")
    if record.accept != transport.ACCEPT_JSON:
        problems.append(f"{name}: accept {record.accept!r}, expected {transport.ACCEPT_JSON!r}")
    return problems


def test_only_the_residual_ids_are_pending() -> None:
    """AC-2: ``agent_merge.PENDING`` is empty; every ID of the family has its record."""
    pending = frozenset(getattr(_family(), ATTRIBUTE_PENDING))

    assert pending == RESIDUAL_PENDING, f"{FAMILY_MODULE}.PENDING still holds {sorted(pending - RESIDUAL_PENDING)}"


def test_the_records_follow_the_transcription_rules() -> None:
    """AC-3: the records are the family's sections, one each; none is ``Paging.LINK``, as no section has a ``Paging:``
    line; and every record has no ``multi_segment`` name, no item key, ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``."""
    registry = fx.import_api_module(name=REGISTRY)
    transport = fx.import_api_module(name=TRANSPORT)
    records = tuple(getattr(_family(), ATTRIBUTE_OPERATIONS))

    declared = sorted(record.operation_id for record in records)
    assert declared == sorted(FAMILY_IDS), f"{FAMILY_MODULE} declares {declared}, its sections are {sorted(FAMILY_IDS)}"
    paged = frozenset(record.operation_id for record in records if record.paging == registry.Paging.LINK)
    assert paged == PAGED_IDS, f"Paging.LINK records {sorted(paged)}, sections with a Paging line {sorted(PAGED_IDS)}"
    problems = [problem for record in records for problem in _rule_problems(record=record, transport=transport)]
    assert problems == [], f"{FAMILY_MODULE}: {problems}"


@pytest.mark.parametrize(argnames="branch_writing", argvalues=BRANCH_WRITING_CALLS, ids=branch_writing_name)
def test_a_branch_writing_record_is_refused(
    branch_writing: BranchWritingCall,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-6: the record is declared and ``registry.lookup`` returns it, yet its complete ``call`` exits 2 with no
    request, and a log record names the ID and that no subcommand sends it."""
    registry = fx.import_api_module(name=REGISTRY)
    records = {record.operation_id: record for record in getattr(_family(), ATTRIBUTE_OPERATIONS)}
    assert branch_writing.operation_id in records, f"{branch_writing.operation_id} has no record in {FAMILY_FILE.name}"
    assert registry.lookup(operation_id=branch_writing.operation_id) == records[branch_writing.operation_id]
    case = refusal_case(branch_writing=branch_writing)
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)
