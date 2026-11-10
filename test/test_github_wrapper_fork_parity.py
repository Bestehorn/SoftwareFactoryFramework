"""Fork parity of the GitHub wrapper's golden cases (UB-1.1): the installed fork produces every golden value.

The golden table ``CASES`` of ``src/payload/test/github_wrapper_fixtures.py`` is what the product's entry script must
reproduce (``src/payload/test/test_github_wrapper_compat.py``). Its oracle is the fork this repository runs,
``scripts/github_wrapper.py`` (``config/toolchain.json`` ``deviations``): each case that is neither ``c_only`` (a
deviation UB-1.1 makes on purpose) nor a delivery verb's runs against the fork in the temporary project and with the
fixture token the compatibility test builds, through the same fake GitHub host, comparing standard output, exit code
and the requests other than ``GET``. The fork's ``main()`` takes no ``argv``, so ``sys.argv`` is set.

Both the fork and the fixtures exist only in this repository, so this module lives in ``test/`` and is never installed
into a project. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_wrapper_fork_parity.py`` (no network).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = ROOT / "src" / "payload" / "test" / "github_wrapper_fixtures.py"
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

FORK_SCRIPT = ROOT / "scripts" / "github_wrapper.py"
FORK_MODULE = "github_wrapper_fork"
#: Every golden case the fork can produce: the C-only deviations and the delivery verbs (the steward's) left out.
FORK_CASES = tuple(case for case in fx.CASES if not case.c_only and case.argv[0] not in fx.DELIVERY_SUBCOMMANDS)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def run_fork(*, argv: Any, monkeypatch: pytest.MonkeyPatch) -> int:
    """The exit code of the fork's ``main()`` with ``sys.argv`` set to ``argv``: its return value, or the code of the
    ``SystemExit`` it raises."""
    fork = fx.load_script(path=FORK_SCRIPT, name=FORK_MODULE, monkeypatch=monkeypatch)
    monkeypatch.setattr(target=sys, name="argv", value=[str(FORK_SCRIPT), *argv])
    try:
        result = fork.main()
    except SystemExit as exc:
        return fx.exit_code_of(exc=exc)
    assert isinstance(result, int), f"the fork's main returned {result!r}, not an exit code"
    return result


@pytest.mark.parametrize(argnames="case", argvalues=FORK_CASES, ids=fx.case_name)
def test_the_fork_produces_the_golden_case(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-1.1's oracle: the fork, run on the case's project and host, writes the golden standard output, exits with the
    golden code and sends the golden requests other than ``GET``."""
    host = fx.enter_project(project=case.project, root=tmp_path, monkeypatch=monkeypatch, routes=case.routes)
    exit_code = run_fork(argv=case.argv, monkeypatch=monkeypatch)
    captured = capsys.readouterr()
    fx.assert_outcome(
        case=case, outcome=fx.Outcome(stdout=captured.out, exit_code=exit_code, requests=tuple(host.requests))
    )
    host.assert_every_request_routed()
