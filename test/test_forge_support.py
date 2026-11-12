"""The forge suite's support logic (S): ``test/forge/ephemeral.py`` exercised in the default collection.

``test/forge/`` is the forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge``) against github.com. What its support module decides without the forge is proven here: the refusal of a
distributed run, the per-command credential helper git authenticates with, where the test credential file is found,
and the CI step's write of it. Only local git runs (``git init``, ``git worktree add``, ``git credential fill``), in
checkouts under pytest's ``tmp_path``; no test opens a connection or needs a test credential file (UB-1).

``ephemeral.py`` is loaded by path from inside each test body through ``_ephemeral``, never at import and never in a
fixture, and nothing at this module's level names one of its symbols: this file collects whatever ``ephemeral.py``
holds, and a test whose symbol does not exist yet fails in its own body.

Run: ``python scripts/run_tests.py test/test_forge_support.py`` (needs git on PATH).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
EPHEMERAL_PATH = ROOT / "test" / "forge" / "ephemeral.py"
#: The fixed ``sys.modules`` key of the by-path load; its dataclasses resolve their module through it.
EPHEMERAL_MODULE = "forge_ephemeral"

CREDENTIALS_DIRECTORY = "credentials"
TEST_CREDENTIAL_NAME = "github-sff-testing-pat.txt"
CLONE_CREDENTIAL_NAME = "github-pat.txt"
LINE_END = "\n"
WINDOWS_LINE_END = "\r\n"
TEXT_ENCODING = "utf-8"

# D1: xdist's ``worker_id`` fixture is ``master`` when xdist does not distribute, ``gw<n>`` in a worker.
DISTRIBUTED_WORKER_ID = "gw0"
CONTROLLER_WORKER_ID = "master"
SINGLE_WORKER_OPTION = "--workers 1"

# D3: the helper options, and what ``git credential fill`` is asked and answers.
CONFIG_OPTION = "-c"
HELPER_RESET = "credential.helper="
GITHUB_HELPER_PREFIX = "credential.https://github.com.helper=!"
HELPER_OPTION_COUNT = 4
CREDENTIAL_REQUEST = "protocol=https\nhost=github.com\n\n"
FIELD_SEPARATOR = "="
USER_FIELD = "username"
TOKEN_FIELD = "password"
ACCESS_TOKEN_USERNAME = "x-access-token"
DECOY_VALUE = "decoy"
#: A helper configured before D3's options, as a config file's would be; the reset must keep git from asking it.
DECOY_HELPER = f"!f() {{ printf '{USER_FIELD}={DECOY_VALUE}\\n{TOKEN_FIELD}={DECOY_VALUE}\\n'; }}; f"

# D8: the CI step's refusal of an empty secret.
UNAVAILABLE_TOKEN_MESSAGE = "the secret SFF_TEST_TOKEN is unavailable to this run"

GIT = "git"
GIT_EXIT_OK = 0
GIT_TIMEOUT_SECONDS = 60
#: Commits in the scratch checkouts: a runner has no global identity, and no signing key is asked for.
COMMIT_IDENTITY = (
    CONFIG_OPTION,
    "user.name=Forge Support Test",
    CONFIG_OPTION,
    "user.email=forge-support-test@example.invalid",
    CONFIG_OPTION,
    "commit.gpgSign=false",
)


def _ephemeral() -> ModuleType:
    """``test/forge/ephemeral.py``, loaded by path once per process and reused while ``sys.modules`` holds it.

    Called from inside each test body, so a missing module fails that test with this assertion, never the collection.
    """
    loaded = sys.modules.get(EPHEMERAL_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == EPHEMERAL_PATH:
        return loaded
    assert EPHEMERAL_PATH.is_file(), (
        f"the forge suite's support module {EPHEMERAL_PATH.relative_to(ROOT).as_posix()} does not exist"
    )
    spec = importlib.util.spec_from_file_location(name=EPHEMERAL_MODULE, location=EPHEMERAL_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {EPHEMERAL_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[EPHEMERAL_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(EPHEMERAL_MODULE, None)
        raise
    return module


def _git(*, arguments: Sequence[str], cwd: Path, request: str = "") -> subprocess.CompletedProcess[str]:
    """Runs local git with ``request`` as its standard input; any exit but 0 fails the test with git's stderr."""
    result = subprocess.run(
        args=[GIT, *arguments],
        cwd=cwd,
        input=request,
        capture_output=True,
        text=True,
        encoding=TEXT_ENCODING,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == GIT_EXIT_OK, (
        f"`git {' '.join(arguments)}` exited {result.returncode}: {result.stderr.strip()}"
    )
    return result


def _init_checkout(*, path: Path) -> None:
    """A ``git init`` checkout at ``path`` with one empty commit, so a worktree can be added from it."""
    path.mkdir(parents=True)
    _git(arguments=["init", "--quiet"], cwd=path)
    _git(arguments=[*COMMIT_IDENTITY, "commit", "--allow-empty", "--quiet", "--message", "seed"], cwd=path)


def _new_token(*, label: str) -> str:
    """A token no other file of the test holds."""
    return f"{label}-{uuid.uuid4().hex}"


def _write_credential(*, directory: Path, name: str, token: str) -> Path:
    """``directory/credentials/<name>`` holding ``token`` and a line end; returns its path."""
    path = directory / CREDENTIALS_DIRECTORY / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data=(token + LINE_END).encode(encoding=TEXT_ENCODING))
    return path


def _answer_fields(*, text: str) -> Dict[str, str]:
    """The ``key=value`` lines of a ``git credential fill`` answer."""
    fields: Dict[str, str] = {}
    for line in text.splitlines():
        key, _, value = line.partition(FIELD_SEPARATOR)
        if key:
            fields[key] = value
    return fields


def _tree(*, root: Path) -> List[str]:
    """Every file and directory under ``root``, relative and in forward-slash form, sorted."""
    return sorted(path.relative_to(root).as_posix() for path in root.rglob(pattern="*"))


def _assert_found(*, found: object, expected: Path) -> None:
    assert isinstance(found, Path), f"find_test_credential returned {found!r}, not a Path"
    assert found.is_file(), f"find_test_credential returned {found}, which is not a file"
    assert found.samefile(other_path=expected), f"find_test_credential returned {found}, not {expected}"


def _names_one_of(*, message: str, paths: Sequence[Path]) -> bool:
    """Whether ``message`` holds one of ``paths`` (equivalent spellings of one file), native or forward-slash."""
    return any(form in message for path in paths for form in (str(path), path.as_posix()))


def test_a_distributed_run_is_refused() -> None:
    """AC-1.1: a session fixture runs once per xdist worker, so any worker id but ``master`` is refused."""
    forge = _ephemeral()
    assert issubclass(forge.ForgeSetupError, forge.ForgeSuiteError), "ForgeSetupError is a ForgeSuiteError (D10)"
    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.refuse_distributed_run(worker_id=DISTRIBUTED_WORKER_ID)
    assert SINGLE_WORKER_OPTION in str(refused.value), f"the refusal does not say to run with {SINGLE_WORKER_OPTION}"
    assert forge.refuse_distributed_run(worker_id=CONTROLLER_WORKER_ID) is None


def test_the_credential_helper_answers_git_with_the_clone_token(tmp_path: Path) -> None:
    """AC-6.3 (D3): git, given the helper options, answers ``x-access-token`` and the clone file's token, though a
    helper is configured before them; no option holds the token; a clone path holding ``'`` is refused."""
    forge = _ephemeral()
    clone = tmp_path / "clone with space"
    token = _new_token(label="clone")
    _write_credential(directory=clone, name=CLONE_CREDENTIAL_NAME, token=token)

    options = list(forge.credential_helper_arguments(clone=clone))
    assert len(options) == HELPER_OPTION_COUNT and options[:3] == [CONFIG_OPTION, HELPER_RESET, CONFIG_OPTION], (
        f"the options are not the helper reset then the github.com helper: {options}"
    )
    assert options[3].startswith(GITHUB_HELPER_PREFIX), f"the second option is no github.com shell helper: {options}"
    assert not [option for option in options if token in option], "a helper option holds the clone's token"

    answer = _git(
        arguments=[CONFIG_OPTION, f"credential.helper={DECOY_HELPER}", *options, "credential", "fill"],
        cwd=tmp_path,
        request=CREDENTIAL_REQUEST,
    )
    fields = _answer_fields(text=answer.stdout)
    assert fields.get(USER_FIELD) == ACCESS_TOKEN_USERNAME, f"git answered the user {fields.get(USER_FIELD)!r}"
    # Compared into a bool first: pytest's introspection would print an answered password, which, were a configured
    # helper asked, is a real credential.
    answered_the_clone_token = fields.get(TOKEN_FIELD) == token
    assert answered_the_clone_token, "git did not answer the clone file's token"

    quoted = tmp_path / "the clone's directory"
    _write_credential(directory=quoted, name=CLONE_CREDENTIAL_NAME, token=_new_token(label="quoted"))
    with pytest.raises(expected_exception=forge.ForgeSetupError):
        forge.credential_helper_arguments(clone=quoted)


def test_the_test_credential_is_found_in_the_checkout_or_its_main_tree(tmp_path: Path) -> None:
    """AC-6.1 (D8): the checkout's own test credential file, else a linked worktree's main working tree's; with
    neither, the refusal names both paths."""
    forge = _ephemeral()
    main_tree = tmp_path / "main tree"
    _init_checkout(path=main_tree)
    main_credential = _write_credential(directory=main_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="main"))
    _assert_found(found=forge.find_test_credential(checkout=main_tree), expected=main_credential)

    linked_tree = tmp_path / "linked tree"
    _git(arguments=["worktree", "add", "--detach", "--quiet", str(linked_tree)], cwd=main_tree)
    linked_credential = linked_tree / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    assert not linked_credential.exists(), f"the new worktree already holds {linked_credential}"
    _assert_found(found=forge.find_test_credential(checkout=linked_tree), expected=main_credential)

    _write_credential(directory=linked_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="linked"))
    _assert_found(found=forge.find_test_credential(checkout=linked_tree), expected=linked_credential)

    common_dir = _git(arguments=["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=linked_tree)
    main_credential_by_git = Path(common_dir.stdout.strip()).parent / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    linked_credential.unlink()
    main_credential.unlink()
    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.find_test_credential(checkout=linked_tree)
    message = str(refused.value)
    assert _names_one_of(message=message, paths=(linked_credential,)), (
        f"the refusal does not name {linked_credential}: {message}"
    )
    assert _names_one_of(message=message, paths=(main_credential, main_credential_by_git)), (
        f"the refusal does not name {main_credential}: {message}"
    )


def test_a_missing_secret_fails_the_credential_step(tmp_path: Path) -> None:
    """AC-5.3 (D8 "CI"): an empty secret is refused and nothing is written; a token is written followed by a line
    end, as the checkout's test credential file."""
    forge = _ephemeral()
    checkout = tmp_path / "checkout"
    (checkout / CREDENTIALS_DIRECTORY).mkdir(parents=True)
    before = _tree(root=checkout)

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.write_test_credential(token="", checkout=checkout)
    assert UNAVAILABLE_TOKEN_MESSAGE in str(refused.value), f"the refusal says: {refused.value}"
    assert _tree(root=checkout) == before, "the refused write left a file in the checkout"

    token = _new_token(label="ci")
    forge.write_test_credential(token=token, checkout=checkout)
    written = checkout / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    assert _tree(root=checkout) == sorted([*before, written.relative_to(checkout).as_posix()]), (
        "the write touched another file than the test credential file"
    )
    assert written.read_bytes() in (
        (token + LINE_END).encode(encoding=TEXT_ENCODING),
        (token + WINDOWS_LINE_END).encode(encoding=TEXT_ENCODING),
    ), "the test credential file does not hold the token followed by a line end"
