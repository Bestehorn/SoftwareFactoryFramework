"""Tests for ``scripts/gitlab_wrapper.py``, the GitLab wrapper's entry script, and the subcommands it serves.

What is pinned (issue #13, ``design.md`` D3 and D7; UB-1, UB-2): ``_load_config`` refuses, with ``GitLabAPIError``, a
missing ``config/gitlab.json``, an absent, empty or ``PASTE_`` value of ``hostname``, ``project_id`` or ``token``, a
``token`` holding any character outside ``!`` to ``~`` (the message names the key, and neither it nor ``details``
holds the value) and a ``token_type`` other than ``private``, ``bearer`` and ``job``; ``main(argv=...)`` hands a
delivery verb to ``steward_delegate`` with the rest of argv unparsed and returns the steward's exit code; the script
exits 2 on a usage error; and a fresh interpreter loads the file by path with
``importlib.util.spec_from_file_location``, which the import bootstrap keeps possible once the entry script imports
``gitlab_api`` (D3).

The in-process tests write ``config/gitlab.json`` into ``tmp_path``, the working directory by ``monkeypatch.chdir``,
load the entry script by path as ``test_wrapper_delivery.load`` does and call ``main(argv=...)``; the exit code is the
return value or the ``SystemExit`` code. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test. The subprocess tests run ``sys.executable`` with ``cwd=tmp_path``.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_compat.py`` (no network).
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
WRAPPER_FILE = SCRIPTS_DIR / "gitlab_wrapper.py"
WRAPPER_MODULE = "gitlab_wrapper_compat_under_test"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

CONFIG_DIR = "config"
CONFIG_FILE_NAME = "gitlab.json"
DELIVERY_FILE_NAME = "delivery.json"
TEXT_ENCODING = "utf-8"

# The keys of config/gitlab.json (templates/config/gitlab.json.template, design.md D7) and of config/delivery.json.
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_TOKEN_TYPE = "token_type"
FIELD_IN_PROGRESS_LABEL = "in_progress_label"
FIELD_MERGE = "merge"
FIELD_HOST = "host"
REQUIRED_KEYS = (FIELD_HOSTNAME, FIELD_PROJECT_ID, FIELD_TOKEN)
PLACEHOLDER_MARKER = "PASTE_"

# Keys of the arguments the fake `subprocess.run` records.
SEEN_COMMAND = "command"
SEEN_INPUT = "input"

TOKEN = "glpat-wrapper-compat-test"  # pragma: allowlist secret
# Two printable halves around a refused character; neither may reach a refusal's message or details.
TOKEN_HEAD = "glpat-HeadPart"  # pragma: allowlist secret
TOKEN_TAIL = "TailPart-42"  # pragma: allowlist secret
# The characters a token may hold: `!` to `~`, printable ASCII without the space (design.md D7).
TOKEN_REFUSED_RUN = "[^!-~]+"
# Refused characters, built from their code points so this file stays ASCII.
ZERO_WIDTH_SPACE = chr(0x200B)
DELETE = chr(0x7F)
E_ACUTE = chr(0xE9)

STEWARD_SCRIPT_SUFFIX = "scripts/merge_steward.py"
STEWARD_TOKEN_FLAG = "--token-stdin"
STEWARD_EXIT_REFUSED = 4
EXIT_USAGE = 2
USAGE_PREFIX = "usage:"
TRACEBACK = "Traceback"
CHILD_TIMEOUT_SECONDS = 120

# A fresh interpreter's program: load the entry script from the absolute path in argv[1] the way
# test_wrapper_delivery.load does; nothing puts the scripts directory on sys.path but the script itself (D3).
LOAD_BY_PATH = "; ".join(
    (
        "import importlib.util, logging, sys",
        "spec = importlib.util.spec_from_file_location('gitlab_wrapper_loaded_by_path', sys.argv[1])",
        "module = importlib.util.module_from_spec(spec)",
        "spec.loader.exec_module(module)",
        "assert issubclass(module.GitLabAPIError, Exception), 'gitlab_wrapper.GitLabAPIError stays importable'",
        "assert callable(module.main), 'gitlab_wrapper.main is callable'",
        "assert not logging.getLogger().handlers, 'loading gitlab_wrapper sets up no logging'",
    )
)


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

TEMPLATE_CONFIG: Dict[str, Any] = {
    FIELD_HOSTNAME: fixtures.HOST,
    FIELD_PROJECT_ID: 1,
    FIELD_TOKEN: TOKEN,
    FIELD_IN_PROGRESS_LABEL: "in-progress",
}


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory, with an empty ``config/``."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / CONFIG_DIR).mkdir()
    return tmp_path


def load_wrapper() -> ModuleType:
    """The entry script, loaded by path afresh, as ``test_wrapper_delivery.load`` loads a wrapper."""
    spec = importlib.util.spec_from_file_location(name=WRAPPER_MODULE, location=WRAPPER_FILE)
    assert spec and spec.loader, f"{WRAPPER_FILE} is missing"
    module = importlib.util.module_from_spec(spec=spec)
    spec.loader.exec_module(module=module)
    return module


def config_with(*, changes: Optional[Mapping[str, Any]] = None, removed: Sequence[str] = ()) -> Dict[str, Any]:
    """The template's keys with ``changes`` applied and the ``removed`` keys left out."""
    config = {key: value for key, value in TEMPLATE_CONFIG.items() if key not in removed}
    config.update(changes or {})
    return config


def write_json(*, path: Path, content: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(content), encoding=TEXT_ENCODING)


def main_exit_code(*, wrapper: ModuleType, argv: Sequence[str]) -> Any:
    """``main(argv=argv)``'s exit code: its return value, or the code of the ``SystemExit`` it raised."""
    assert "argv" in inspect.signature(wrapper.main).parameters, (
        "the entry script's main takes the argument vector: main(argv=None) -> int (design.md D7)"
    )
    try:
        return wrapper.main(argv=list(argv))
    except SystemExit as exit_request:
        return exit_request.code


def capture_steward(*, monkeypatch: pytest.MonkeyPatch, code: int) -> Dict[str, Any]:
    """Replace ``subprocess.run`` so the steward is not executed; the returned dict fills with what it was given."""
    seen: Dict[str, Any] = {}

    def fake_run(command: List[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen[SEEN_COMMAND] = list(command)
        seen.update(kwargs)
        return subprocess.CompletedProcess(args=command, returncode=code)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return seen


def run_child(*, args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run ``args`` in a child process from ``cwd`` and decode its output as UTF-8 (D7 reconfigures both streams)."""
    return subprocess.run(
        args=list(args),
        cwd=str(cwd),
        capture_output=True,
        encoding=TEXT_ENCODING,
        errors="replace",
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )


def printable_pieces(*, value: str) -> List[str]:
    """The runs of ``value`` a token may hold; a refusal that echoed the value would echo one of them."""
    return [piece for piece in re.split(pattern=TOKEN_REFUSED_RUN, string=value) if piece]


def refusal_cases() -> List[Any]:
    """One case per refusal rule of ``_load_config`` (design.md D7): the config written (``None``: no file), the
    text the message names (``None``: not pinned), the value nothing reported may contain (``None``: not pinned)."""
    cases = [pytest.param(None, str(Path(CONFIG_DIR) / CONFIG_FILE_NAME), None, id="file-missing")]
    for key in REQUIRED_KEYS:
        placeholder = f"{PLACEHOLDER_MARKER}YOUR_{key.upper()}_HERE"
        cases.append(pytest.param(config_with(removed=(key,)), key, None, id=f"{key}-absent"))
        cases.append(pytest.param(config_with(changes={key: ""}), key, None, id=f"{key}-empty"))
        cases.append(pytest.param(config_with(changes={key: placeholder}), key, None, id=f"{key}-placeholder"))
    refused_tokens = [
        ("token-trailing-newline", f"{TOKEN}\n"),
        ("token-zero-width-space", f"{TOKEN_HEAD}{ZERO_WIDTH_SPACE}{TOKEN_TAIL}"),
        ("token-space", f"{TOKEN_HEAD} {TOKEN_TAIL}"),  # U+0020, just below `!`
        ("token-delete", f"{TOKEN_HEAD}{DELETE}{TOKEN_TAIL}"),  # U+007F, just above `~`
        ("token-non-ascii", f"{TOKEN_HEAD}{E_ACUTE}{TOKEN_TAIL}"),
    ]
    for case, token in refused_tokens:
        cases.append(pytest.param(config_with(changes={FIELD_TOKEN: token}), FIELD_TOKEN, token, id=case))
    cases.append(pytest.param(config_with(changes={FIELD_TOKEN_TYPE: "oauth"}), None, None, id="token_type-unknown"))
    return cases


@pytest.mark.parametrize(("config", "named", "hidden"), refusal_cases())
def test_load_config_refusals(
    config: Optional[Dict[str, Any]], named: Optional[str], hidden: Optional[str], project: Path
) -> None:
    if config is not None:
        write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=config)
    wrapper = load_wrapper()
    with pytest.raises(wrapper.GitLabAPIError) as refusal:
        wrapper._load_config()
    message = str(refusal.value)
    if named is not None:
        assert named in message, f"the refusal names {named!r}: {message!r}"
    if hidden is not None:
        details = refusal.value.details
        reported = message if details is None else f"{message}\n{details}"
        for piece in printable_pieces(value=hidden):
            assert piece not in reported, "a refused token is named by its key, never echoed (design.md D7)"


@pytest.mark.parametrize(
    ("verb", "args", "steward_verb"),
    [
        pytest.param("dequeue-pr", ["77", "--reason", "x"], "dequeue", id="dequeue-pr"),
        pytest.param("enqueue-pr", ["77"], "enqueue", id="enqueue-pr"),
        pytest.param("queue-status", ["--json"], "status", id="queue-status"),
        pytest.param("wait-landed", ["77", "--timeout-seconds", "540"], "wait-landed", id="wait-landed"),
        pytest.param("check-handoff", ["412"], "check-handoff", id="check-handoff"),
        pytest.param("check-landed", ["77", "78"], "check-landed", id="check-landed"),
    ],
)
def test_delivery_verb_through_main(
    verb: str,
    args: List[str],
    steward_verb: str,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
) -> None:
    write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=TEMPLATE_CONFIG)
    write_json(path=project / CONFIG_DIR / DELIVERY_FILE_NAME, content={FIELD_MERGE: "steward", FIELD_HOST: "gitlab"})
    seen = capture_steward(monkeypatch=monkeypatch, code=STEWARD_EXIT_REFUSED)
    wrapper = load_wrapper()
    assert main_exit_code(wrapper=wrapper, argv=[verb, *args]) == STEWARD_EXIT_REFUSED, (
        "main returns the steward's exit code unchanged"
    )
    command = seen.get(SEEN_COMMAND)
    assert command is not None, f"main({[verb, *args]}) did not run the merge steward"
    assert command[1].replace("\\", "/").endswith(STEWARD_SCRIPT_SUFFIX)
    assert command[2:] == [STEWARD_TOKEN_FLAG, steward_verb, *args], "the rest of argv reaches the steward unparsed"
    assert TOKEN not in " ".join(command), "the token never reaches argv"
    assert str(seen.get(SEEN_INPUT, "")).startswith(TOKEN), "the token of config/gitlab.json goes on stdin"
    assert fake_gitlab.requests == [], "a delivery verb sends no GitLab request of its own"


@pytest.mark.parametrize(
    "argv",
    [pytest.param([], id="no-subcommand"), pytest.param(["no-such-command"], id="unknown-subcommand")],
)
def test_script_usage_error_exits_2(argv: List[str], tmp_path: Path) -> None:
    # No config/gitlab.json: main parses before it loads the config (design.md D7), so a usage error is reported as
    # one whatever the config, and the child has no host it could reach.
    completed = run_child(args=[sys.executable, str(WRAPPER_FILE), *argv], cwd=tmp_path)
    assert completed.returncode == EXIT_USAGE, (
        f"a usage error exits {EXIT_USAGE} through argparse, got {completed.returncode}; stderr:\n{completed.stderr}"
    )
    assert USAGE_PREFIX in completed.stderr, f"argparse prints the usage on stderr:\n{completed.stderr}"
    assert TRACEBACK not in completed.stderr, f"a usage error is not a crash:\n{completed.stderr}"


def test_script_loads_by_path(tmp_path: Path) -> None:
    # `-I`: neither the working directory, the program's directory nor PYTHONPATH reaches sys.path, so only the
    # entry script's own bootstrap can make `gitlab_api` importable (design.md D3).
    completed = run_child(args=[sys.executable, "-I", "-c", LOAD_BY_PATH, str(WRAPPER_FILE)], cwd=tmp_path)
    assert completed.returncode == 0, (
        f"a fresh interpreter loads {WRAPPER_FILE} by path; exit {completed.returncode}, stderr:\n{completed.stderr}"
    )
