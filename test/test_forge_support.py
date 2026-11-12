"""The forge suite's support logic (S): ``test/forge/ephemeral.py`` exercised in the default collection.

``test/forge/`` is the forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge``) against github.com. What its support module decides without the forge is proven here: the refusal of a
distributed run, the per-command credential helper git authenticates with, where the test credential file is found,
and the CI step's write of it; the run id and the repository name it gives (D4); the marker on every product-wrapper
invocation (D10); the teardown guard and the leftover sweep (D9); and the provision around them, its steps in order, the
test credential's refusals and the token written only to the clone (D3 "The clone", D8, D9). Only local git runs (``git
init``, ``git worktree add``, ``git credential fill``, ``git remote add``, ``git config``), in checkouts under pytest's
``tmp_path``; the wrapper runner's ``subprocess.run`` is replaced by a recorder, and the teardown and the sweep are
given ``RecordingWrapperRunner``, a ``WrapperRunner`` that records each argv and answers it from the test's script. A
provision is also given ``ScriptedGitRunner``, a ``GitRunner`` that records each argv, hands ``init`` and ``remote`` to
real local git in the clone and answers the rest (``fetch``, ``checkout``, the seed's reads) from the script without a
process. No test opens a connection or needs a test credential file (UB-1).

``ephemeral.py`` is loaded by path from inside each test body through ``_ephemeral``, never at import and never in a
fixture, and nothing at this module's level names one of its symbols: this file collects whatever ``ephemeral.py``
holds, and a test whose symbol does not exist yet fails in its own body (``_require``). The test doubles are built from
the loaded module the same way, inside a helper a test body calls. ``test/forge/write_credential.py``, the CI step's
command, is loaded the same way, through ``_credential_step`` from inside the one test that runs its ``main``, and the
``SFF_TEST_TOKEN`` that ``main`` reads is set or removed only through that test's ``monkeypatch``. The product
wrapper, whose marker and origin pattern are the oracles of D10 and D4, is loaded by path for the test that reads it,
and its directory is on ``sys.path`` only until that test ends.

Run: ``python scripts/run_tests.py test/test_forge_support.py`` (needs git on PATH).
"""

from __future__ import annotations

import builtins
import importlib.util
import io
import json
import logging
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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
# D8 "CI": the CI step's command, loaded by path as ``ephemeral.py`` is, the one environment variable its ``main``
# reads, and the exit codes ``main`` returns.
WRITE_CREDENTIAL_PATH = ROOT / "test" / "forge" / "write_credential.py"
WRITE_CREDENTIAL_MODULE = "forge_write_credential"
SECRET_VARIABLE = "SFF_TEST_TOKEN"  # pragma: allowlist secret
STEP_WROTE = 0
STEP_REFUSED = 1

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

# The product wrapper, loaded by path for the constants its guard and ``_detect_repo`` read (D2, D4).
PRODUCT_SCRIPTS = ROOT / "src" / "payload" / "scripts"
PRODUCT_WRAPPER_PATH = PRODUCT_SCRIPTS / "github_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_support_product_wrapper"

# D4, D5: the test organization, the ephemeral name's prefix, and the run id's form and its origin URL (D3).
TEST_ORGANIZATION = "bestehorn-sff-test"
EPHEMERAL_PREFIX = "sff-test-"
RUN_ID_PATTERN = re.compile(r"([0-9]{14})-([0-9a-f]{32})")
RUN_ID_TIME_FORMAT = "%Y%m%d%H%M%S"
RUN_ID_SAMPLES = 64
UUID_VERSION = 4
ORIGIN_URL = "https://github.com/{owner}/{name}.git"
DEFAULT_BRANCH = "main"

# D10: what ``SubprocessWrapperRunner`` passes ``subprocess.run``.
INTERPRETER_OPTION = "-X"
MARKER_ARGV_LENGTH = 4
ARGV_KEYWORD = "args"
ENV_KEYWORD = "env"
CWD_KEYWORD = "cwd"
SHELL_KEYWORD = "shell"
RUN_ATTRIBUTE = "run"

# D9: the records the teardown and the sweep send.
CALL_SUBCOMMAND = "call"
DELETE_OPERATION = "repos/delete"
LIST_OPERATION = "repos/list-for-org"
PATH_OPTION = "--path"
OWNER_PARAMETER = "owner"
REPO_PARAMETER = "repo"
ORG_PARAMETER = "org"
LISTING_ARGUMENTS = (CALL_SUBCOMMAND, LIST_OPERATION, PATH_OPTION, f"{ORG_PARAMETER}={TEST_ORGANIZATION}")
#: A listed repository's fields (docs.github.com "List organization repositories"), and its ``created_at`` form.
FIELD_NAME = "name"
FIELD_FULL_NAME = "full_name"
FIELD_OWNER = "owner"
FIELD_LOGIN = "login"
FIELD_PRIVATE = "private"
FIELD_CREATED_AT = "created_at"
CREATED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ONE_DAY = timedelta(days=1)
ONE_SECOND = timedelta(seconds=1)
LONG_AGO = timedelta(days=30)
SWEEP_NOW = datetime(year=2026, month=11, day=12, hour=12, tzinfo=timezone.utc)
#: The product wrapper's exit on a ``GitHubAPIError`` and the ``ERROR:`` line it writes (``transport._http_failure``).
WRAPPER_API_FAILURE = 1
HTTP_FAILURE = "ERROR: GitHub API DELETE https://api.github.com/repos/{full_name} failed: HTTP {status}"
NOT_FOUND_STATUS = 404
FORBIDDEN_STATUS = 403
OTHER_OWNER = "Bestehorn"
UNPREFIXED_NAME = "SoftwareFactoryFramework"

# The symbols each test needs of ``ephemeral.py`` (D4, D9, D10).
RUNNER_SYMBOLS = ("WrapperRunner", "Invocation")
RUN_ID_SYMBOLS = ("new_run_id", "ephemeral_name", "TEST_ORGANIZATION")
SUBPROCESS_RUNNER_SYMBOLS = (*RUNNER_SYMBOLS, "SubprocessWrapperRunner", "PRODUCT_WRAPPER")
TEARDOWN_SYMBOLS = (*RUNNER_SYMBOLS, "CreatedRepository", "delete_ephemeral")
SWEEP_SYMBOLS = (
    *RUNNER_SYMBOLS,
    "RepositoryRecord",
    "LEFTOVER_AGE",
    "is_leftover",
    "select_leftovers",
    "sweep_leftovers",
    "delete_leftover",
)

# AC-3.1, AC-3.2: the property's listings. Each drawn repository's owner, prefix and age side are drawn first, so the
# expected deletions follow from the draw and never from the code under test.
OTHER_OWNERS = (OTHER_OWNER, "octocat", "sff-test", "bestehorn-sff-test-archive")
NAME_SUFFIXES = st.from_regex(regex=r"[a-z0-9][a-z0-9-]{0,24}", fullmatch=True)
#: Names without the prefix, among them near misses (``sff-testing``, ``sff_test-1``, the prefix after the start).
UNPREFIXED_NAMES = st.from_regex(
    regex=r"(?:sff-test|sff_test-|test-sff-test-|x)?[a-z0-9][a-z0-9-]{0,24}", fullmatch=True
).filter(lambda name: not name.startswith(EPHEMERAL_PREFIX))
#: Ages in seconds at the sweep: a day or less (an hour in the future included) is kept, more than a day is deleted.
DAY_SECONDS = 86400
YOUNG_AGES = st.integers(min_value=-3600, max_value=DAY_SECONDS)
OLD_AGES = st.integers(min_value=DAY_SECONDS + 1, max_value=DAY_SECONDS * 400)
#: Whole seconds, as ``created_at`` is, so a drawn age is exactly the difference the sweep computes.
SWEEP_MOMENTS = st.datetimes(
    min_value=datetime(year=2024, month=1, day=1),
    max_value=datetime(year=2035, month=12, day=31),
    timezones=st.just(value=timezone.utc),
).map(lambda moment: moment.replace(microsecond=0))
MAX_LISTING = 12
SWEEP_EXAMPLES = 60


def _load_by_path(*, path: Path, name: str, description: str) -> ModuleType:
    """The file ``path``, loaded by path as the module ``name`` once per process and reused while ``sys.modules`` holds
    it; it is registered there before it runs, so its dataclasses resolve their module.

    Called from inside a test body, so a missing file fails that test with this assertion, never the collection.
    """
    loaded = sys.modules.get(name)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == path:
        return loaded
    assert path.is_file(), f"{description} {path.relative_to(ROOT).as_posix()} does not exist"
    spec = importlib.util.spec_from_file_location(name=name, location=path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _ephemeral() -> ModuleType:
    """``test/forge/ephemeral.py``, the forge suite's support module, loaded by path (``_load_by_path``)."""
    return _load_by_path(path=EPHEMERAL_PATH, name=EPHEMERAL_MODULE, description="the forge suite's support module")


def _credential_step() -> ModuleType:
    """``test/forge/write_credential.py``, the CI step's command, loaded by path (``_load_by_path``)."""
    return _load_by_path(path=WRITE_CREDENTIAL_PATH, name=WRITE_CREDENTIAL_MODULE, description="the CI step's command")


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


def test_a_missing_secret_fails_the_credential_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-5.3 (D5, D8 "CI"): an empty secret is refused and nothing is written; a token is written followed by a line
    end, as the checkout's test credential file. ``write_credential.main``, the CI step's command, given
    ``SFF_TEST_TOKEN`` unset or empty, logs the refusal, writes nothing and returns 1; given a token, it writes the
    checkout's test credential file and returns 0."""
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

    _assert_the_credential_step_judges_the_secret(
        step=_credential_step(), checkout=tmp_path / "ci step checkout", monkeypatch=monkeypatch, caplog=caplog
    )


def _assert_the_credential_step_judges_the_secret(
    *, step: ModuleType, checkout: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-5.3 (D5, D8 "CI"): ``step.main(checkout=checkout)`` with ``SFF_TEST_TOKEN`` removed, then empty, logs the
    refusal, returns 1 and leaves ``checkout`` as it was; with a token, it writes the token and a line end as the
    checkout's test credential file, touches no other file, logs no record holding the token and returns 0."""
    (checkout / CREDENTIALS_DIRECTORY).mkdir(parents=True)
    before = _tree(root=checkout)
    caplog.set_level(level=logging.DEBUG)

    for unavailable in (None, ""):
        if unavailable is None:
            monkeypatch.delenv(name=SECRET_VARIABLE, raising=False)
        else:
            monkeypatch.setenv(name=SECRET_VARIABLE, value=unavailable)
        state = "unset" if unavailable is None else "empty"
        caplog.clear()
        exit_code = step.main(checkout=checkout)
        assert exit_code == STEP_REFUSED, f"main returned {exit_code!r} with {SECRET_VARIABLE} {state}, not 1"
        refusals = [record for record in caplog.records if UNAVAILABLE_TOKEN_MESSAGE in record.getMessage()]
        assert refusals, (
            f"main logged no record saying {UNAVAILABLE_TOKEN_MESSAGE!r} with {SECRET_VARIABLE} {state}: "
            f"{caplog.messages}"
        )
        assert _tree(root=checkout) == before, f"main left a file in the checkout with {SECRET_VARIABLE} {state}"

    token = _new_token(label="ci-step")
    monkeypatch.setenv(name=SECRET_VARIABLE, value=token)
    caplog.clear()
    exit_code = step.main(checkout=checkout)
    assert exit_code == STEP_WROTE, f"main returned {exit_code!r} with a token in {SECRET_VARIABLE}, not 0"
    written = checkout / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    assert _tree(root=checkout) == sorted([*before, written.relative_to(checkout).as_posix()]), (
        "main touched another file than the checkout's test credential file"
    )
    assert written.read_bytes() in (
        (token + LINE_END).encode(encoding=TEXT_ENCODING),
        (token + WINDOWS_LINE_END).encode(encoding=TEXT_ENCODING),
    ), "main's test credential file does not hold the token followed by a line end"
    assert token not in caplog.text, "a record main logged holds the token"


# ---------------------------------------------------------------------------------------------------------------------
# The runners, the run id and the two deletion paths (D4, D9, D10)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Answer:
    """What a scripted product-wrapper invocation answers: its exit code, standard output and standard error."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


SUCCESS = _Answer(returncode=0)


@dataclass(frozen=True)
class _SubprocessCall:
    """One call of the replaced ``subprocess.run``: its positional and keyword arguments, as given."""

    positional: Tuple[Any, ...]
    keywords: Dict[str, Any]

    def argv(self) -> List[str]:
        """The argv the call starts, each part as text; a call given none, or given a command string, fails the test."""
        given = self.keywords.get(ARGV_KEYWORD, self.positional[0] if self.positional else None)
        assert given is not None, f"subprocess.run received no argv: {self}"
        assert not isinstance(given, (str, bytes)), f"subprocess.run received a command string, not a list: {given!r}"
        return [str(part) for part in given]


@dataclass(frozen=True)
class _ListedRepository:
    """One repository of a drawn listing, with the three properties the expected deletions are computed from."""

    owner: str
    name: str
    age_seconds: int
    leftover: bool


def _listed_repository(
    *,
    in_organization: bool,
    prefixed: bool,
    old: bool,
    other_owner: str,
    suffix: str,
    unprefixed_name: str,
    young_age: int,
    old_age: int,
) -> _ListedRepository:
    """A listed repository built from its drawn owner side, prefix side and age side; it is a leftover exactly when it
    is the test organization's, its name has the prefix, and it is more than a day old (AC-3.1, AC-3.2)."""
    return _ListedRepository(
        owner=TEST_ORGANIZATION if in_organization else other_owner,
        name=EPHEMERAL_PREFIX + suffix if prefixed else unprefixed_name,
        age_seconds=old_age if old else young_age,
        leftover=in_organization and prefixed and old,
    )


LISTED_REPOSITORIES = st.builds(
    _listed_repository,
    in_organization=st.booleans(),
    prefixed=st.booleans(),
    old=st.booleans(),
    other_owner=st.sampled_from(elements=OTHER_OWNERS),
    suffix=NAME_SUFFIXES,
    unprefixed_name=UNPREFIXED_NAMES,
    young_age=YOUNG_AGES,
    old_age=OLD_AGES,
)
LISTINGS = st.lists(
    elements=LISTED_REPOSITORIES,
    max_size=MAX_LISTING,
    unique_by=lambda repository: (repository.owner, repository.name),
)


def _require(*, module: ModuleType, names: Sequence[str]) -> None:
    """Fails the calling test on this assertion while ``ephemeral.py`` lacks one of ``names``."""
    missing = [name for name in names if not hasattr(module, name)]
    assert not missing, f"the forge suite's support module defines no {', '.join(missing)}"


def _product_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """``src/payload/scripts/github_wrapper.py``, loaded by path as a fresh module, for the constants its guard and
    ``_detect_repo`` read; its directory is first on ``sys.path``, and the module in ``sys.modules``, until the test
    ends."""
    assert PRODUCT_WRAPPER_PATH.is_file(), f"the product wrapper {PRODUCT_WRAPPER_PATH} does not exist"
    monkeypatch.syspath_prepend(path=str(PRODUCT_SCRIPTS))
    spec = importlib.util.spec_from_file_location(name=PRODUCT_WRAPPER_MODULE, location=PRODUCT_WRAPPER_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {PRODUCT_WRAPPER_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    monkeypatch.setitem(dic=sys.modules, name=PRODUCT_WRAPPER_MODULE, value=module)
    spec.loader.exec_module(module=module)
    return module


def _recording_runner(*, forge: ModuleType, script: Callable[..., _Answer]) -> Any:
    """A ``RecordingWrapperRunner``, the loaded module's ``WrapperRunner`` double: it records each argv in
    ``recorded`` and answers it with ``script(arguments=<the argv>)`` as an ``Invocation``; no process starts."""
    _require(module=forge, names=RUNNER_SYMBOLS)
    wrapper_runner: Any = forge.WrapperRunner

    class RecordingWrapperRunner(wrapper_runner):
        """Records each product-wrapper argv and answers it from the test's script."""

        def __init__(self) -> None:
            self.recorded: List[List[str]] = []

        def run(self, *, arguments: Sequence[str]) -> Any:
            argv = [str(part) for part in arguments]
            self.recorded.append(argv)
            answer = script(arguments=argv)
            return forge.Invocation(returncode=answer.returncode, stdout=answer.stdout, stderr=answer.stderr)

    return RecordingWrapperRunner()


def _answer_every_invocation(*, answer: _Answer) -> Callable[..., _Answer]:
    """A script that answers every invocation with ``answer``."""

    def script(*, arguments: List[str]) -> _Answer:
        return answer

    return script


def _refuse_every_invocation(*, arguments: List[str]) -> _Answer:
    """A script for a runner that may be sent nothing: any invocation fails the test."""
    raise AssertionError(f"the product wrapper was invoked where nothing may be sent: {arguments}")


def _listing_item(*, owner: str, name: str, created_at: datetime) -> Dict[str, Any]:
    """One item of ``call repos/list-for-org``'s printed array, as GitHub lists a repository."""
    return {
        FIELD_NAME: name,
        FIELD_FULL_NAME: f"{owner}/{name}",
        FIELD_OWNER: {FIELD_LOGIN: owner},
        FIELD_PRIVATE: True,
        FIELD_CREATED_AT: created_at.strftime(CREATED_AT_FORMAT),
    }


def _sweep_script(*, items: Sequence[Dict[str, Any]], deletion: _Answer) -> Callable[..., _Answer]:
    """A script answering D9's listing with ``items`` printed as ``call`` prints a list, and every ``call
    repos/delete`` with ``deletion``; any other invocation fails the test."""
    listing = _Answer(returncode=0, stdout=json.dumps(obj=list(items), indent=2) + LINE_END)

    def script(*, arguments: List[str]) -> _Answer:
        if arguments == list(LISTING_ARGUMENTS):
            return listing
        if arguments[:2] == [CALL_SUBCOMMAND, DELETE_OPERATION]:
            return deletion
        raise AssertionError(f"the sweep sent an invocation the test scripted no answer for: {arguments}")

    return script


def _deletion(*, owner: str, name: str) -> List[str]:
    """D9's ``call repos/delete`` of ``owner/name``."""
    return [
        CALL_SUBCOMMAND,
        DELETE_OPERATION,
        PATH_OPTION,
        f"{OWNER_PARAMETER}={owner}",
        PATH_OPTION,
        f"{REPO_PARAMETER}={name}",
    ]


def _http_failure(*, full_name: str, status: int) -> _Answer:
    """The product wrapper's answer to a deletion GitHub refused with ``status``: exit 1 and its ``ERROR:`` line."""
    return _Answer(returncode=WRAPPER_API_FAILURE, stderr=HTTP_FAILURE.format(full_name=full_name, status=status))


def _run_id() -> str:
    """A run id of D4's form, made by the test: the UTC time, ``-``, a fresh ``uuid4`` hex."""
    return f"{datetime.now(tz=timezone.utc).strftime(RUN_ID_TIME_FORMAT)}-{uuid.uuid4().hex}"


def _fake_subprocess_run(*, calls: List[_SubprocessCall], answers: Sequence[_Answer]) -> Callable[..., Any]:
    """A ``subprocess.run`` that records each call in ``calls`` and answers the calls with ``answers`` in turn."""
    pending = list(answers)

    def run(*positional: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        call = _SubprocessCall(positional=positional, keywords=dict(keywords))
        calls.append(call)
        assert pending, f"subprocess.run was called more often than the runner was: {call.argv()}"
        answer = pending.pop(0)
        return subprocess.CompletedProcess(
            args=call.argv(), returncode=answer.returncode, stdout=answer.stdout, stderr=answer.stderr
        )

    return run


#: AC-4.3: product-wrapper invocations in two working directories, each with the answer its process gives.
MARKER_CASES: Tuple[Tuple[str, Tuple[str, ...], _Answer], ...] = (
    ("clone one", (CALL_SUBCOMMAND, "repos/get"), _Answer(returncode=0, stdout='{"name": "sff-test-x"}\n')),
    (
        "clone two",
        ("get-issue", "1"),
        _http_failure(full_name=f"{TEST_ORGANIZATION}/sff-test-x", status=NOT_FOUND_STATUS),
    ),
    ("clone two", LISTING_ARGUMENTS, _Answer(returncode=2, stderr="ERROR: refused\n")),
)


def test_a_run_id_is_unique_and_names_a_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1.2 (D4): repeated ``new_run_id`` calls give pairwise distinct ids, each the UTC time of the call as
    ``%Y%m%d%H%M%S``, ``-``, and a ``uuid4`` hex; ``ephemeral_name`` prefixes the product wrapper's
    ``EPHEMERAL_REPOSITORY_PREFIX``, and the product's ``GITHUB_REPOSITORY_PATTERN`` reads D3's origin URL of that name
    back as ``("bestehorn-sff-test", <the name>)``."""
    forge = _ephemeral()
    _require(module=forge, names=RUN_ID_SYMBOLS)
    wrapper = _product_wrapper(monkeypatch=monkeypatch)
    assert forge.TEST_ORGANIZATION == TEST_ORGANIZATION, f"TEST_ORGANIZATION is {forge.TEST_ORGANIZATION!r} (D5)"

    started = datetime.now(tz=timezone.utc).replace(microsecond=0)
    run_ids = [forge.new_run_id() for _ in range(RUN_ID_SAMPLES)]
    finished = datetime.now(tz=timezone.utc)
    assert len(set(run_ids)) == len(run_ids), f"repeated calls gave an id twice: {sorted(run_ids)}"

    for run_id in run_ids:
        form = RUN_ID_PATTERN.fullmatch(string=run_id)
        assert form is not None, f"the run id {run_id!r} is not <UTC %Y%m%d%H%M%S>-<uuid4 hex> (D4)"
        stamp = datetime.strptime(form.group(1), RUN_ID_TIME_FORMAT).replace(tzinfo=timezone.utc)
        assert started <= stamp <= finished, f"the run id {run_id!r} does not hold the UTC time of the call"
        assert uuid.UUID(hex=form.group(2)).version == UUID_VERSION, f"the run id {run_id!r} holds no uuid4 hex"

        name = forge.ephemeral_name(run_id=run_id)
        assert name == wrapper.EPHEMERAL_REPOSITORY_PREFIX + run_id, f"ephemeral_name gave {name!r} for {run_id!r}"
        origin = ORIGIN_URL.format(owner=TEST_ORGANIZATION, name=name)
        read_back = wrapper.GITHUB_REPOSITORY_PATTERN.search(string=origin)
        assert read_back is not None and read_back.groups() == (TEST_ORGANIZATION, name), (
            f"the product wrapper reads the origin {origin} as {read_back.groups() if read_back else None}"
        )


def test_every_wrapper_invocation_carries_the_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-4.3 (D10): every ``SubprocessWrapperRunner.run`` starts ``[sys.executable, "-X", <the product's
    TEST_MARKER_OPTION>, str(PRODUCT_WRAPPER), *arguments]`` as a list, in its directory, and passes ``subprocess.run``
    no ``env``; ``PRODUCT_WRAPPER`` is the product wrapper's absolute path, and the answer comes back as the
    ``Invocation``."""
    forge = _ephemeral()
    _require(module=forge, names=SUBPROCESS_RUNNER_SYMBOLS)
    assert issubclass(forge.SubprocessWrapperRunner, forge.WrapperRunner), "SubprocessWrapperRunner is a WrapperRunner"
    marker = _product_wrapper(monkeypatch=monkeypatch).TEST_MARKER_OPTION
    product_wrapper = Path(forge.PRODUCT_WRAPPER)
    assert product_wrapper.is_absolute() and product_wrapper.resolve() == PRODUCT_WRAPPER_PATH, (
        f"PRODUCT_WRAPPER is {product_wrapper}, not the absolute path of {PRODUCT_WRAPPER_PATH}"
    )

    calls: List[_SubprocessCall] = []
    answers = [answer for _, _, answer in MARKER_CASES]
    monkeypatch.setattr(
        target=forge.subprocess, name=RUN_ATTRIBUTE, value=_fake_subprocess_run(calls=calls, answers=answers)
    )
    for directory_name, arguments, answer in MARKER_CASES:
        directory = tmp_path / directory_name
        directory.mkdir(exist_ok=True)
        invocation = forge.SubprocessWrapperRunner(directory=directory).run(arguments=list(arguments))
        assert (invocation.returncode, invocation.stdout, invocation.stderr) == (
            answer.returncode,
            answer.stdout,
            answer.stderr,
        ), f"the Invocation of {list(arguments)} does not carry the process's answer: {invocation!r}"

    assert len(calls) == len(MARKER_CASES), f"{len(MARKER_CASES)} invocations started {len(calls)} processes"
    for call, (directory_name, arguments, _) in zip(calls, MARKER_CASES):
        argv = call.argv()
        assert argv[:MARKER_ARGV_LENGTH] == [sys.executable, INTERPRETER_OPTION, marker, str(forge.PRODUCT_WRAPPER)], (
            f"the invocation does not start with the interpreter, -X {marker} and the product wrapper: {argv}"
        )
        assert argv[MARKER_ARGV_LENGTH:] == list(arguments), (
            f"the wrapper's arguments are not {list(arguments)}: {argv}"
        )
        assert ENV_KEYWORD not in call.keywords, f"subprocess.run received an env for {argv}"
        assert len(call.positional) <= 1, f"subprocess.run received positional arguments past the argv: {call}"
        assert not call.keywords.get(SHELL_KEYWORD, False), f"subprocess.run ran {argv} through a shell"
        working_directory = call.keywords.get(CWD_KEYWORD)
        assert working_directory is not None and (
            Path(working_directory).resolve() == (tmp_path / directory_name).resolve()
        ), f"{argv} ran in {working_directory}, not in the runner's directory {tmp_path / directory_name}"


def test_the_teardown_deletes_only_this_runs_repository() -> None:
    """AC-2.1 (D9): given the record of this run's creation, the teardown sends exactly one ``call repos/delete
    --path owner=bestehorn-sff-test --path repo=sff-test-<run id>``."""
    forge = _ephemeral()
    _require(module=forge, names=TEARDOWN_SYMBOLS)
    run_id = _run_id()
    name = EPHEMERAL_PREFIX + run_id
    runner = _recording_runner(forge=forge, script=_answer_every_invocation(answer=SUCCESS))
    created = forge.CreatedRepository(owner=TEST_ORGANIZATION, name=name, default_branch=DEFAULT_BRANCH)

    forge.delete_ephemeral(wrapper=runner, created=created, run_id=run_id)

    assert runner.recorded == [_deletion(owner=TEST_ORGANIZATION, name=name)], (
        f"the teardown of {TEST_ORGANIZATION}/{name} sent {runner.recorded}"
    )


@pytest.mark.parametrize(
    argnames=("owner", "name_template"),
    argvalues=(
        pytest.param(OTHER_OWNER, "{prefix}{run_id}", id="another-owner"),
        pytest.param(TEST_ORGANIZATION, "{run_id}", id="a-name-without-the-prefix"),
        pytest.param(TEST_ORGANIZATION, "{prefix}{other_run_id}", id="another-runs-id"),
    ),
)
def test_the_teardown_refuses_any_other_target(owner: str, name_template: str) -> None:
    """AC-2.2 (D9): a created record of another owner, of a name without the prefix, or of another run's id is
    refused with ``ForgeTeardownRefusedError`` naming the refused ``owner/name`` and this run's; nothing is sent."""
    forge = _ephemeral()
    _require(module=forge, names=TEARDOWN_SYMBOLS)
    run_id = _run_id()
    name = name_template.format(prefix=EPHEMERAL_PREFIX, run_id=run_id, other_run_id=_run_id())
    runner = _recording_runner(forge=forge, script=_refuse_every_invocation)
    created = forge.CreatedRepository(owner=owner, name=name, default_branch=DEFAULT_BRANCH)

    with pytest.raises(expected_exception=forge.ForgeTeardownRefusedError) as refused:
        forge.delete_ephemeral(wrapper=runner, created=created, run_id=run_id)

    message = str(refused.value)
    assert f"{owner}/{name}" in message, f"the refusal does not name {owner}/{name}: {message}"
    own = f"{TEST_ORGANIZATION}/{EPHEMERAL_PREFIX}{run_id}"
    assert own in message, f"the refusal does not name this run's repository {own}: {message}"
    assert runner.recorded == [], f"the refused teardown sent {runner.recorded}"


@settings(deadline=None, max_examples=SWEEP_EXAMPLES)
@given(listing=LISTINGS, now=SWEEP_MOMENTS)
def test_the_sweep_deletes_exactly_the_old_ephemeral_repositories(
    listing: List[_ListedRepository], now: datetime
) -> None:
    """AC-3.1, AC-3.2 (D9): over listings of repositories of the test organization or another owner, with a name with
    the prefix or not, created either side of the one-day line, the sweep lists the organization once and then sends
    one ``call repos/delete`` per repository that is the organization's, prefixed and more than a day old, and none
    for any other; ``is_leftover`` and ``select_leftovers`` agree. The expected deletions come from the drawn sides."""
    forge = _ephemeral()
    _require(module=forge, names=SWEEP_SYMBOLS)
    items = [
        _listing_item(owner=drawn.owner, name=drawn.name, created_at=now - timedelta(seconds=drawn.age_seconds))
        for drawn in listing
    ]
    runner = _recording_runner(forge=forge, script=_sweep_script(items=items, deletion=SUCCESS))

    forge.sweep_leftovers(wrapper=runner, now=now)

    expected = sorted(_deletion(owner=drawn.owner, name=drawn.name) for drawn in listing if drawn.leftover)
    assert runner.recorded[:1] == [list(LISTING_ARGUMENTS)], f"the sweep did not list first: {runner.recorded}"
    assert sorted(runner.recorded[1:]) == expected, (
        f"the sweep at {now:%Y-%m-%dT%H:%M:%SZ} deleted {runner.recorded[1:]}, not {expected}"
    )
    records = [forge.RepositoryRecord.of(item=item) for item in items]
    leftovers = [forge.is_leftover(record=record, now=now) for record in records]
    assert leftovers == [drawn.leftover for drawn in listing], f"is_leftover judged {listing} as {leftovers}"
    selected = list(forge.select_leftovers(records=records, now=now))
    assert selected == [record for record, drawn in zip(records, listing) if drawn.leftover], (
        f"select_leftovers kept {selected} of {listing}"
    )


def test_the_sweep_boundaries_and_refusals() -> None:
    """AC-3.1, AC-3.2 (D9): exactly a day old is kept and a second more is deleted; a deletion answered with exit 1 and
    ``HTTP 404`` counts as deleted, any other failure raises ``ForgeCommandError``; ``delete_leftover`` of a repository
    that is no leftover raises ``ForgeSweepRefusedError`` naming it, and sends nothing."""
    forge = _ephemeral()
    _require(module=forge, names=SWEEP_SYMBOLS)
    assert forge.LEFTOVER_AGE == ONE_DAY, f"LEFTOVER_AGE is {forge.LEFTOVER_AGE!r}, not a day (D9)"
    a_day_old = _listing_item(
        owner=TEST_ORGANIZATION, name=f"{EPHEMERAL_PREFIX}a-day-old", created_at=SWEEP_NOW - ONE_DAY
    )
    just_over = _listing_item(
        owner=TEST_ORGANIZATION, name=f"{EPHEMERAL_PREFIX}just-over-a-day", created_at=SWEEP_NOW - ONE_DAY - ONE_SECOND
    )
    just_over_deletion = _deletion(owner=TEST_ORGANIZATION, name=just_over[FIELD_NAME])
    assert not forge.is_leftover(record=forge.RepositoryRecord.of(item=a_day_old), now=SWEEP_NOW), (
        "a repository exactly a day old is a leftover"
    )
    assert forge.is_leftover(record=forge.RepositoryRecord.of(item=just_over), now=SWEEP_NOW), (
        "a repository a day and a second old is no leftover"
    )

    swept = _recording_runner(forge=forge, script=_sweep_script(items=[a_day_old, just_over], deletion=SUCCESS))
    forge.sweep_leftovers(wrapper=swept, now=SWEEP_NOW)
    assert swept.recorded == [list(LISTING_ARGUMENTS), just_over_deletion], f"the sweep sent {swept.recorded}"

    not_found = _http_failure(full_name=just_over[FIELD_FULL_NAME], status=NOT_FOUND_STATUS)
    gone = _recording_runner(forge=forge, script=_sweep_script(items=[just_over], deletion=not_found))
    forge.sweep_leftovers(wrapper=gone, now=SWEEP_NOW)
    assert gone.recorded == [list(LISTING_ARGUMENTS), just_over_deletion], f"the sweep sent {gone.recorded}"

    forbidden = _http_failure(full_name=just_over[FIELD_FULL_NAME], status=FORBIDDEN_STATUS)
    refused_by_github = _recording_runner(forge=forge, script=_answer_every_invocation(answer=forbidden))
    with pytest.raises(expected_exception=forge.ForgeCommandError):
        forge.delete_leftover(
            wrapper=refused_by_github, record=forge.RepositoryRecord.of(item=just_over), now=SWEEP_NOW
        )
    assert refused_by_github.recorded == [just_over_deletion], f"the deletion sent {refused_by_github.recorded}"

    for no_leftover in (
        a_day_old,
        _listing_item(owner=OTHER_OWNER, name=f"{EPHEMERAL_PREFIX}another-owner", created_at=SWEEP_NOW - LONG_AGO),
        _listing_item(owner=TEST_ORGANIZATION, name=UNPREFIXED_NAME, created_at=SWEEP_NOW - LONG_AGO),
    ):
        runner = _recording_runner(forge=forge, script=_refuse_every_invocation)
        with pytest.raises(expected_exception=forge.ForgeSweepRefusedError) as refused:
            forge.delete_leftover(wrapper=runner, record=forge.RepositoryRecord.of(item=no_leftover), now=SWEEP_NOW)
        full_name = no_leftover[FIELD_FULL_NAME]
        assert full_name in str(refused.value), f"the refusal does not name {full_name}: {refused.value}"
        assert runner.recorded == [], f"the refused deletion of {full_name} sent {runner.recorded}"


# ---------------------------------------------------------------------------------------------------------------------
# Provisioning (D3 "The clone", D8, D9 steps 1 to 7)
# ---------------------------------------------------------------------------------------------------------------------

# The symbols the provisioning tests need of ``ephemeral.py`` (D9, D10).
GIT_RUNNER_SYMBOLS = ("GitRunner", "Invocation")
PROVISION_SYMBOLS = (
    *RUNNER_SYMBOLS,
    *GIT_RUNNER_SYMBOLS,
    "ForgeSetupError",
    "ForgeCommandError",
    "EphemeralRepository",
    "provision",
)

# D9: the test's tree. The workspace stands for the session fixture's ``tempfile.mkdtemp`` directory; the clone is
# ``<workspace>/clone``, and its git files are read where git writes them.
CHECKOUT_NAME = "checkout"
WORKSPACE_NAME = "workspace"
CLONE_NAME = "clone"
GIT_DIRECTORY = ".git"
GIT_CONFIG_NAME = "config"
GIT_INFO_DIRECTORY = "info"
GIT_EXCLUDE_NAME = "exclude"
ORIGIN_URL_KEY = "remote.origin.url"
#: D8: the line the clone's ``.git/info/exclude`` gains, so no commit of the clone holds its credential file.
EXCLUDED_CREDENTIALS = "credentials/"
SENTINEL_LABEL = "sentinel"

# D9 step 5: the creation, and the repository GitHub answers it with (docs.github.com "Create an organization
# repository"). The default branch is not ``main``, so a checkout of a branch the answer did not name is seen.
CREATE_OPERATION = "repos/create-in-org"
RAW_FIELD_OPTION = "-f"
TYPED_FIELD_OPTION = "-F"
NAME_FIELD = "name="
PRIVATE_FIELD = "private=true"
AUTO_INIT_FIELD = "auto_init=true"
FIELD_DEFAULT_BRANCH = "default_branch"
SEED_BRANCH = "trunk"
EMPTY_LISTING = _Answer(returncode=0, stdout=json.dumps(obj=[]) + LINE_END)
CREATION_FAILURE = _Answer(
    returncode=WRAPPER_API_FAILURE,
    stderr=f"ERROR: GitHub API POST https://api.github.com/orgs/{TEST_ORGANIZATION}/repos failed: HTTP 422",
)
DELETION_FAILURE = _http_failure(full_name=f"{TEST_ORGANIZATION}/{EPHEMERAL_PREFIX}this-run", status=FORBIDDEN_STATUS)

# D3, D9 step 6: the git commands a provision runs, and what the scripted git answers them with.
GIT_INIT = "init"
GIT_REMOTE = "remote"
GIT_FETCH = "fetch"
GIT_CHECKOUT = "checkout"
GIT_REV_PARSE = "rev-parse"
GIT_LS_TREE = "ls-tree"
ORIGIN_REMOTE = "origin"
OPTION_PREFIX = "-"
#: The commands the scripted git hands to real local git in the clone: they write only the clone's ``.git/``.
LOCAL_GIT_SUBCOMMANDS = (GIT_INIT, GIT_REMOTE)
REMOTE_ADD = (GIT_REMOTE, "add", ORIGIN_REMOTE)
FETCH_ARGUMENTS = (GIT_FETCH, ORIGIN_REMOTE)
CHECKOUT_ARGUMENTS = (GIT_CHECKOUT, "-B", SEED_BRANCH, "--track", f"{ORIGIN_REMOTE}/{SEED_BRANCH}")
LS_TREE_ARGUMENTS = (GIT_LS_TREE, "-r", "--name-only", "HEAD")
SEED_SHA = "5eed" * 10
SEED_TREE_SHA = "7ee5" * 10
#: ``rev-parse``'s answer per revision D9 step 6 asks for.
SEED_REVISIONS = {"HEAD": SEED_SHA, "HEAD^{tree}": SEED_TREE_SHA}
SEED_TREE = ("README.md",)
WORKFLOW_SEED_TREE = (*SEED_TREE, ".github/workflows/ci.yml")

# AC-1.1: a provision's timeline, as the steps of D9 it shows.
WRAPPER_RUNNER = "wrapper"
GIT_RUNNER = "git"
BODY_RUNNER = "body"
STEP_INIT = "git init"
STEP_REMOTE = "git remote add origin <this run's URL>"
STEP_LISTING = "the listing"
STEP_CREATION = "the creation"
STEP_FETCH = "the authenticated git fetch origin"
STEP_CHECKOUT = "git checkout -B <default branch> --track origin/<default branch>"
STEP_READ = "the seed's reads"
STEP_BODY = "the body"
STEP_DELETION = "the deletion"
PREPARED_STEPS = (STEP_INIT, STEP_REMOTE, STEP_LISTING, STEP_CREATION, STEP_FETCH, STEP_CHECKOUT, STEP_READ)

# AC-6.2: the bad test credential files, one per refusal ``_load_token`` makes.
MISSING_CREDENTIAL = "missing"
EMPTY_CREDENTIAL = "empty"
PLACEHOLDER_CREDENTIAL = "the-placeholder"
TWO_TOKENS_CREDENTIAL = "two-tokens-on-two-lines"

# UB-2: the calls a read or a write of a file goes through, replaced by a recorder during a provision.
OPEN_TARGETS: Tuple[Tuple[ModuleType, str], ...] = ((builtins, "open"), (io, "open"), (os, "open"))


class _BodyFailure(Exception):
    """What a test body raises, to show that the teardown runs whatever the body does (AC-1.4)."""


@dataclass(frozen=True)
class _Event:
    """One entry of a provision's timeline: a wrapper or git invocation, or the body's entry. At a wrapper invocation,
    ``origin`` is the URL the clone's ``.git/config`` named then, ``None`` when it named none."""

    runner: str
    arguments: Tuple[str, ...] = ()
    authenticated: bool = False
    origin: Optional[str] = None


def _origin_url(*, name: str) -> str:
    """D3's origin URL of the test organization's repository ``name``."""
    return ORIGIN_URL.format(owner=TEST_ORGANIZATION, name=name)


def _creation(*, name: str) -> List[str]:
    """D9 step 5's ``call repos/create-in-org`` of ``name``."""
    return [
        CALL_SUBCOMMAND,
        CREATE_OPERATION,
        PATH_OPTION,
        f"{ORG_PARAMETER}={TEST_ORGANIZATION}",
        RAW_FIELD_OPTION,
        NAME_FIELD + name,
        TYPED_FIELD_OPTION,
        PRIVATE_FIELD,
        TYPED_FIELD_OPTION,
        AUTO_INIT_FIELD,
    ]


def _requested_name(*, arguments: Sequence[str]) -> str:
    """The repository name a creation asks for with ``-f name=<name>``; a creation naming none fails the test."""
    for option, value in zip(arguments, arguments[1:]):
        if option == RAW_FIELD_OPTION and value.startswith(NAME_FIELD):
            return value[len(NAME_FIELD) :]
    raise AssertionError(f"the creation names no repository with {RAW_FIELD_OPTION} {NAME_FIELD}<name>: {arguments}")


def _created_item(*, name: str) -> Dict[str, Any]:
    """The repository the creation of ``name`` answers with, as GitHub answers it: private, ``SEED_BRANCH`` its
    default branch."""
    return {
        FIELD_NAME: name,
        FIELD_FULL_NAME: f"{TEST_ORGANIZATION}/{name}",
        FIELD_OWNER: {FIELD_LOGIN: TEST_ORGANIZATION},
        FIELD_PRIVATE: True,
        FIELD_DEFAULT_BRANCH: SEED_BRANCH,
    }


def _origin_of(*, clone: Path) -> Optional[str]:
    """The ``origin`` URL the clone's ``.git/config`` names, read by local git from that file alone; ``None`` while the
    file is absent or names none."""
    config = clone / GIT_DIRECTORY / GIT_CONFIG_NAME
    if not config.is_file():
        return None
    result = subprocess.run(
        args=[GIT, "config", "--file", str(config), "--get", ORIGIN_URL_KEY],
        capture_output=True,
        text=True,
        encoding=TEXT_ENCODING,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    return result.stdout.strip() if result.returncode == GIT_EXIT_OK else None


def _revisions(*, arguments: Sequence[str]) -> _Answer:
    """``rev-parse``'s answer: one line per revision asked for, options aside; a revision D9 step 6 does not ask for
    fails the test."""
    asked = [argument for argument in arguments[1:] if not argument.startswith(OPTION_PREFIX)]
    unknown = [revision for revision in asked if revision not in SEED_REVISIONS]
    assert asked and not unknown, f"the provision asked rev-parse for revisions the test scripted none for: {arguments}"
    return _Answer(returncode=GIT_EXIT_OK, stdout="".join(SEED_REVISIONS[revision] + LINE_END for revision in asked))


class _ProvisionScript:
    """The forge and the git one provision meets, scripted, noting every invocation and the body's entry in one
    ``timeline``, in order.

    The wrapper answers the listing with no repository, the creation with the repository it names (``_created_item``)
    or with ``creation`` when one is given, and the deletion with ``deletion``; at each invocation it notes the clone's
    ``origin``. The git hands ``init`` and ``remote`` to real local git in the clone, which must exist by then, and
    answers ``fetch`` and ``checkout`` with success, ``rev-parse`` from ``SEED_REVISIONS`` and ``ls-tree -r --name-only
    HEAD`` with ``seed_tree``, starting no process. Any other invocation fails the test.
    """

    def __init__(
        self, *, clone: Path, seed_tree: Sequence[str], creation: Optional[_Answer], deletion: _Answer
    ) -> None:
        self.clone = clone
        self.seed_tree = tuple(seed_tree)
        self.creation = creation
        self.deletion = deletion
        self.timeline: List[_Event] = []
        #: The repository name the creation asked for, once it was sent.
        self.name: Optional[str] = None

    def wrapper(self, *, arguments: List[str]) -> _Answer:
        """The script of the provision's ``RecordingWrapperRunner``."""
        self.timeline.append(
            _Event(runner=WRAPPER_RUNNER, arguments=tuple(arguments), origin=_origin_of(clone=self.clone))
        )
        if arguments == list(LISTING_ARGUMENTS):
            return EMPTY_LISTING
        if arguments[:2] == [CALL_SUBCOMMAND, CREATE_OPERATION]:
            self.name = _requested_name(arguments=arguments)
            if self.creation is not None:
                return self.creation
            return _Answer(returncode=0, stdout=json.dumps(obj=_created_item(name=self.name), indent=2) + LINE_END)
        if arguments[:2] == [CALL_SUBCOMMAND, DELETE_OPERATION]:
            return self.deletion
        raise AssertionError(f"the provision sent an invocation the test scripted no answer for: {arguments}")

    def git(self, *, arguments: List[str], authenticated: bool) -> _Answer:
        """The script of the provision's ``ScriptedGitRunner``."""
        self.timeline.append(_Event(runner=GIT_RUNNER, arguments=tuple(arguments), authenticated=authenticated))
        subcommand = arguments[0] if arguments else ""
        if subcommand in LOCAL_GIT_SUBCOMMANDS:
            assert self.clone.is_dir(), f"`git {' '.join(arguments)}` ran before the clone {self.clone} existed"
            completed = _git(arguments=arguments, cwd=self.clone)
            return _Answer(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
        if subcommand in (GIT_FETCH, GIT_CHECKOUT):
            return SUCCESS
        if subcommand == GIT_REV_PARSE:
            return _revisions(arguments=arguments)
        if arguments == list(LS_TREE_ARGUMENTS):
            return _Answer(returncode=GIT_EXIT_OK, stdout="".join(path + LINE_END for path in self.seed_tree))
        raise AssertionError(f"the provision ran a git command the test scripted no answer for: {arguments}")

    def enter(self) -> None:
        """Notes the body's entry."""
        self.timeline.append(_Event(runner=BODY_RUNNER))

    def steps(self) -> List[str]:
        """The timeline as D9's steps, consecutive seed reads as one; an invocation of no step is named as sent."""
        steps: List[str] = []
        for event in self.timeline:
            step = self._step(event=event)
            if step != STEP_READ or steps[-1:] != [STEP_READ]:
                steps.append(step)
        return steps

    def _step(self, *, event: _Event) -> str:
        if event.runner == BODY_RUNNER:
            return STEP_BODY
        if event.runner == GIT_RUNNER and not event.authenticated:
            if event.arguments[:1] == (GIT_INIT,):
                return STEP_INIT
            if event.arguments[:1] == (GIT_REV_PARSE,) or event.arguments == LS_TREE_ARGUMENTS:
                return STEP_READ
        name = self.name or ""
        steps = {
            (GIT_RUNNER, (*REMOTE_ADD, _origin_url(name=name)), False): STEP_REMOTE,
            (WRAPPER_RUNNER, LISTING_ARGUMENTS, False): STEP_LISTING,
            (WRAPPER_RUNNER, tuple(_creation(name=name)), False): STEP_CREATION,
            (GIT_RUNNER, FETCH_ARGUMENTS, True): STEP_FETCH,
            (GIT_RUNNER, CHECKOUT_ARGUMENTS, False): STEP_CHECKOUT,
            (WRAPPER_RUNNER, tuple(_deletion(owner=TEST_ORGANIZATION, name=name)), False): STEP_DELETION,
        }
        unexpected = (
            f"an unexpected {event.runner} invocation {list(event.arguments)} (authenticated: {event.authenticated})"
        )
        return steps.get((event.runner, event.arguments, event.authenticated), unexpected)


def _scripted_git_runner(*, forge: ModuleType, script: Callable[..., _Answer]) -> Any:
    """A ``ScriptedGitRunner``, the loaded module's ``GitRunner`` double: it records each argv with its
    ``authenticated`` flag in ``recorded`` and answers it with ``script(arguments=<the argv>, authenticated=<the
    flag>)`` as an ``Invocation``; it starts a process only where ``script`` does."""
    _require(module=forge, names=GIT_RUNNER_SYMBOLS)
    git_runner: Any = forge.GitRunner

    class ScriptedGitRunner(git_runner):
        """Records each git argv and answers it from the test's script."""

        def __init__(self) -> None:
            self.recorded: List[Tuple[List[str], bool]] = []

        def run(self, *, arguments: Sequence[str], authenticated: bool = False) -> Any:
            argv = [str(part) for part in arguments]
            self.recorded.append((argv, authenticated))
            answer = script(arguments=argv, authenticated=authenticated)
            return forge.Invocation(returncode=answer.returncode, stdout=answer.stdout, stderr=answer.stderr)

    return ScriptedGitRunner()


def _refuse_every_git_command(*, arguments: List[str], authenticated: bool) -> _Answer:
    """A script for a git runner that may run nothing: any command fails the test."""
    raise AssertionError(f"git was run where nothing may run: {arguments} (authenticated: {authenticated})")


@dataclass(frozen=True)
class _Provisioning:
    """A scripted provision's inputs: under ``root``, a ``git init`` checkout holding the test credential file with
    ``token`` and a sentinel ``credentials/github-pat.txt`` (UB-2), the workspace, and the two doubles, which note in
    ``script``'s timeline."""

    root: Path
    checkout: Path
    workspace: Path
    token: str
    test_credential: Path
    sentinel: Path
    script: _ProvisionScript
    wrapper: Any
    git: Any

    @property
    def clone(self) -> Path:
        """D9 step 3's ``<workspace>/clone``."""
        return self.workspace / CLONE_NAME


def _provisioning(
    *,
    forge: ModuleType,
    tmp_path: Path,
    seed_tree: Sequence[str] = SEED_TREE,
    creation: Optional[_Answer] = None,
    deletion: _Answer = SUCCESS,
) -> _Provisioning:
    """A scripted provision's tree under ``tmp_path`` and its two doubles, sharing one ``_ProvisionScript``."""
    checkout = tmp_path / CHECKOUT_NAME
    _init_checkout(path=checkout)
    token = _new_token(label="test")
    test_credential = _write_credential(directory=checkout, name=TEST_CREDENTIAL_NAME, token=token)
    sentinel = _write_credential(directory=checkout, name=CLONE_CREDENTIAL_NAME, token=_new_token(label=SENTINEL_LABEL))
    workspace = tmp_path / WORKSPACE_NAME
    workspace.mkdir()
    script = _ProvisionScript(clone=workspace / CLONE_NAME, seed_tree=seed_tree, creation=creation, deletion=deletion)
    return _Provisioning(
        root=tmp_path,
        checkout=checkout,
        workspace=workspace,
        token=token,
        test_credential=test_credential,
        sentinel=sentinel,
        script=script,
        wrapper=_recording_runner(forge=forge, script=script.wrapper),
        git=_scripted_git_runner(forge=forge, script=script.git),
    )


@dataclass(frozen=True)
class _Entered:
    """What a provision's body found on entry: the yielded repository and its ``repr``, the moment, the clone's files,
    and the files of the test's tree that held the token, the sentinel aside (its content is compared on its own)."""

    repository: Any
    representation: str
    at: datetime
    clone_is_directory: bool
    #: Kept out of the ``repr``, so that pytest's introspection of a failed assertion never prints the token.
    clone_credential: Optional[bytes] = field(repr=False)
    exclude_lines: Tuple[str, ...]
    git_config: str
    holders: Tuple[str, ...]


def _holders(*, setup: _Provisioning) -> List[str]:
    """The files under the test's tree holding the token, relative and in forward-slash form, the sentinel aside."""
    token = setup.token.encode(encoding=TEXT_ENCODING)
    return sorted(
        path.relative_to(setup.root).as_posix()
        for path in setup.root.rglob(pattern="*")
        if path.is_file() and path != setup.sentinel and token in path.read_bytes()
    )


def _text_of(*, path: Path) -> str:
    """The text of ``path``; empty while it is no file."""
    return path.read_text(encoding=TEXT_ENCODING) if path.is_file() else ""


def _enter(*, repository: Any, setup: _Provisioning) -> _Entered:
    """What the body of a provision over ``setup`` finds on entry (``_Entered``)."""
    git_directory = setup.clone / GIT_DIRECTORY
    credential = setup.clone / CREDENTIALS_DIRECTORY / CLONE_CREDENTIAL_NAME
    exclude = _text_of(path=git_directory / GIT_INFO_DIRECTORY / GIT_EXCLUDE_NAME)
    return _Entered(
        repository=repository,
        representation=repr(repository),
        at=datetime.now(tz=timezone.utc),
        clone_is_directory=setup.clone.is_dir(),
        clone_credential=credential.read_bytes() if credential.is_file() else None,
        exclude_lines=tuple(line.strip() for line in exclude.splitlines()),
        git_config=_text_of(path=git_directory / GIT_CONFIG_NAME),
        holders=tuple(_holders(setup=setup)),
    )


def _provide(*, forge: ModuleType, setup: _Provisioning, entered: List[_Entered], body_raises: bool) -> None:
    """One ``provision`` over ``setup``. Its body notes what it found in ``entered`` and its entry in the timeline, then
    returns or raises ``_BodyFailure``; it asserts nothing, so a teardown error cannot hide a failed assertion."""
    with forge.provision(
        checkout=setup.checkout, workspace=setup.workspace, wrapper=setup.wrapper, git=setup.git
    ) as repository:
        entered.append(_enter(repository=repository, setup=setup))
        setup.script.enter()
        if body_raises:
            raise _BodyFailure("the test body raised")


@dataclass(frozen=True)
class _ProvisionCase:
    """One way a provision ends: the seed's tree, whether the body raises, the deletion's answer, whether the body is
    entered, and the error of ``ephemeral.py`` the context then raises, by name (``None``: the body's own, or none)."""

    seed_tree: Tuple[str, ...]
    body_raises: bool
    deletion: _Answer
    yields: bool
    error: Optional[str] = None


PROVISION_CASES = (
    pytest.param(
        _ProvisionCase(seed_tree=SEED_TREE, body_raises=False, deletion=SUCCESS, yields=True), id="the-body-returns"
    ),
    pytest.param(
        _ProvisionCase(seed_tree=SEED_TREE, body_raises=True, deletion=SUCCESS, yields=True), id="the-body-raises"
    ),
    pytest.param(
        _ProvisionCase(
            seed_tree=WORKFLOW_SEED_TREE, body_raises=False, deletion=SUCCESS, yields=False, error="ForgeSetupError"
        ),
        id="a-workflow-in-the-seed",
    ),
    pytest.param(
        _ProvisionCase(
            seed_tree=SEED_TREE, body_raises=False, deletion=DELETION_FAILURE, yields=True, error="ForgeCommandError"
        ),
        id="the-deletion-fails",
    ),
)


def _expected_error(*, forge: ModuleType, case: _ProvisionCase) -> Any:
    """The exception the context raises in ``case``: the body's ``_BodyFailure``, the named error of ``ephemeral.py``,
    or ``None``."""
    if case.body_raises:
        return _BodyFailure
    return getattr(forge, case.error) if case.error is not None else None


def _deletions(*, setup: _Provisioning) -> List[List[str]]:
    """The ``call repos/delete`` invocations the provision's wrapper recorded."""
    return [argv for argv in setup.wrapper.recorded if argv[:2] == [CALL_SUBCOMMAND, DELETE_OPERATION]]


def _assert_yielded(*, forge: ModuleType, entered: _Entered, setup: _Provisioning, started: datetime) -> None:
    """AC-1.1, AC-1.3 (D9): the yielded ``EphemeralRepository`` names this run's repository as the creation answered
    it, the seed the git reads answered, the time of the sweep, the existing clone, and the runners it was given."""
    repository = entered.repository
    assert isinstance(repository, forge.EphemeralRepository), f"provision yielded {type(repository)}, no record"
    assert (repository.owner, repository.name, repository.default_branch) == (
        TEST_ORGANIZATION,
        setup.script.name,
        SEED_BRANCH,
    ), f"the yielded repository is {repository.owner}/{repository.name} on {repository.default_branch}"
    assert repository.name == EPHEMERAL_PREFIX + repository.run_id, (
        f"the run id {repository.run_id!r} is not the name's"
    )
    assert (repository.seed_sha, repository.seed_tree_sha) == (SEED_SHA, SEED_TREE_SHA), (
        f"the yielded seed is {repository.seed_sha} {repository.seed_tree_sha}, not the git reads' answer"
    )
    swept_at = repository.swept_at
    assert isinstance(swept_at, datetime) and swept_at.utcoffset() == timedelta(0), f"swept_at is {swept_at!r}"
    assert started.replace(microsecond=0) <= swept_at <= entered.at, f"swept_at {swept_at} is not this run's sweep"
    assert entered.clone_is_directory and Path(repository.clone).resolve() == setup.clone.resolve(), (
        f"the yielded clone is {repository.clone}, not the existing {setup.clone}"
    )
    assert repository.wrapper is setup.wrapper and repository.git is setup.git, "the yielded runners are not the given"


@pytest.mark.parametrize(argnames="case", argvalues=PROVISION_CASES)
def test_provisioning_runs_in_order(tmp_path: Path, case: _ProvisionCase) -> None:
    """AC-1.1, AC-1.3, AC-1.4 (D3 "The clone", D9): one provision runs ``git init`` in the created ``<workspace>/clone``
    and adds D3's origin, lists the organization, sends exactly one creation of ``sff-test-<run id>``, fetches
    authenticated and checks the answered default branch out, then reads the seed; every wrapper invocation meets the
    clone's origin of this run's repository. Whether the body returns or raises, after the context exactly one
    deletion of this run's repository is recorded and the workspace no longer exists; a seed naming
    ``.github/workflows/ci.yml`` raises ``ForgeSetupError`` before the yield and the deletion is still sent; a deletion
    answering exit 1 raises ``ForgeCommandError`` and the workspace is still removed."""
    forge = _ephemeral()
    _require(module=forge, names=PROVISION_SYMBOLS)
    setup = _provisioning(forge=forge, tmp_path=tmp_path, seed_tree=case.seed_tree, deletion=case.deletion)
    expected_error = _expected_error(forge=forge, case=case)
    entered: List[_Entered] = []
    started = datetime.now(tz=timezone.utc)

    if expected_error is None:
        _provide(forge=forge, setup=setup, entered=entered, body_raises=case.body_raises)
    else:
        with pytest.raises(expected_exception=expected_error):
            _provide(forge=forge, setup=setup, entered=entered, body_raises=case.body_raises)

    expected_steps = [*PREPARED_STEPS, *([STEP_BODY] if case.yields else []), STEP_DELETION]
    assert setup.script.steps() == expected_steps, f"the provision ran {setup.script.steps()}, not {expected_steps}"
    name = str(setup.script.name)
    assert name.startswith(EPHEMERAL_PREFIX) and RUN_ID_PATTERN.fullmatch(string=name[len(EPHEMERAL_PREFIX) :]), (
        f"the creation asked for {name!r}, not sff-test-<run id> (D4)"
    )
    origins = [event.origin for event in setup.script.timeline if event.runner == WRAPPER_RUNNER]
    assert set(origins) == {_origin_url(name=name)}, f"the wrapper ran where the clone's origin was {origins}"
    assert _deletions(setup=setup) == [_deletion(owner=TEST_ORGANIZATION, name=name)], (
        f"the provision sent the deletions {_deletions(setup=setup)}"
    )
    assert not setup.workspace.exists(), f"the workspace {setup.workspace} outlived the provision"
    assert len(entered) == (1 if case.yields else 0), f"the body was entered {len(entered)} times"
    if case.yields:
        _assert_yielded(forge=forge, entered=entered[0], setup=setup, started=started)


def test_no_creation_no_deletion(tmp_path: Path) -> None:
    """AC-2.3 (D9): ``delete_ephemeral`` given ``created=None`` sends nothing; a provision whose creation answers exit
    1 raises ``ForgeCommandError`` without entering the body, sends no ``repos/delete``, and removes the workspace."""
    forge = _ephemeral()
    _require(module=forge, names=(*PROVISION_SYMBOLS, "delete_ephemeral"))
    untouched = _recording_runner(forge=forge, script=_refuse_every_invocation)
    assert forge.delete_ephemeral(wrapper=untouched, created=None, run_id=_run_id()) is None
    assert untouched.recorded == [], f"the teardown of no creation sent {untouched.recorded}"

    setup = _provisioning(forge=forge, tmp_path=tmp_path, creation=CREATION_FAILURE)
    entered: List[_Entered] = []
    with pytest.raises(expected_exception=forge.ForgeCommandError):
        _provide(forge=forge, setup=setup, entered=entered, body_raises=False)

    expected_steps = [STEP_INIT, STEP_REMOTE, STEP_LISTING, STEP_CREATION]
    assert setup.script.steps() == expected_steps, f"the provision ran {setup.script.steps()}, not {expected_steps}"
    assert _deletions(setup=setup) == [], f"the provision whose creation failed sent {_deletions(setup=setup)}"
    assert entered == [], "the provision yielded though its creation failed"
    assert not setup.workspace.exists(), f"the workspace {setup.workspace} outlived the provision"


def _bad_credential_text(*, kind: str, placeholder: str) -> Optional[str]:
    """The text of a bad test credential file of ``kind``; ``None`` for a missing one."""
    texts = {
        EMPTY_CREDENTIAL: "",
        PLACEHOLDER_CREDENTIAL: placeholder + LINE_END,
        TWO_TOKENS_CREDENTIAL: _new_token(label="first") + LINE_END + _new_token(label="second") + LINE_END,
    }
    return texts.get(kind)


@pytest.mark.parametrize(
    argnames="kind", argvalues=(MISSING_CREDENTIAL, EMPTY_CREDENTIAL, PLACEHOLDER_CREDENTIAL, TWO_TOKENS_CREDENTIAL)
)
def test_a_bad_test_credential_fails_before_any_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """AC-6.2 (D8, D9 step 2): a test credential file that is missing, empty, the product wrapper's ``PLACEHOLDER`` or
    two tokens on two lines makes ``provision`` raise ``ForgeSetupError`` naming the file and none of its text, before
    any wrapper or git invocation and without entering the body; the workspace no longer exists."""
    forge = _ephemeral()
    _require(module=forge, names=PROVISION_SYMBOLS)
    checkout = tmp_path / CHECKOUT_NAME
    _init_checkout(path=checkout)
    credential = checkout / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    text = _bad_credential_text(kind=kind, placeholder=str(_product_wrapper(monkeypatch=monkeypatch).PLACEHOLDER))
    if text is not None:
        credential.parent.mkdir()
        credential.write_bytes(data=text.encode(encoding=TEXT_ENCODING))
    workspace = tmp_path / WORKSPACE_NAME
    workspace.mkdir()
    wrapper = _recording_runner(forge=forge, script=_refuse_every_invocation)
    git = _scripted_git_runner(forge=forge, script=_refuse_every_git_command)
    yielded: List[Any] = []

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        with forge.provision(checkout=checkout, workspace=workspace, wrapper=wrapper, git=git) as repository:
            yielded.append(repository)

    message = str(refused.value)
    assert _names_one_of(message=message, paths=(credential,)), f"the refusal does not name {credential}: {message}"
    held = [line.strip() for line in (text or "").splitlines() if line.strip()]
    assert not [line for line in held if line in message], "the refusal holds the test credential file's text"
    assert (wrapper.recorded, git.recorded) == ([], []), f"the refused provision ran {wrapper.recorded} {git.recorded}"
    assert yielded == [], "the provision yielded with a bad test credential file"
    assert not workspace.exists(), f"the workspace {workspace} outlived the refused provision"


def _noting_open(*, original: Callable[..., Any], opened: List[Path]) -> Callable[..., Any]:
    """``original``, an ``open``, that first notes in ``opened`` the resolved path of a file it is given by name."""

    def noting_open(file: Any, *positional: Any, **keywords: Any) -> Any:
        if isinstance(file, (str, bytes, os.PathLike)):
            opened.append(Path(os.fsdecode(filename=file)).resolve())
        return original(file, *positional, **keywords)

    return noting_open


def _record_opens(*, patch: pytest.MonkeyPatch) -> List[Path]:
    """Replaces ``open``, ``io.open`` and ``os.open`` through ``patch`` with ``_noting_open``; returns the list the
    opened paths are noted in."""
    opened: List[Path] = []
    for target, attribute in OPEN_TARGETS:
        original = getattr(target, attribute)
        patch.setattr(target=target, name=attribute, value=_noting_open(original=original, opened=opened))
    return opened


def _assert_sentinel_untouched(*, setup: _Provisioning, content: bytes, opened: Sequence[Path]) -> None:
    """UB-2: the checkout's ``credentials/github-pat.txt`` keeps ``content``, and of the files named
    ``credentials/github-pat.txt`` the provision opened, none lies outside the clone."""
    assert setup.sentinel.read_bytes() == content, "the checkout's credentials/github-pat.txt changed"
    sentinel = setup.sentinel.resolve()
    assert sentinel not in opened, f"the provision opened the checkout's {sentinel}"
    clone = setup.workspace.resolve() / CLONE_NAME
    outside = [
        path
        for path in opened
        if (path.parent.name, path.name) == (CREDENTIALS_DIRECTORY, CLONE_CREDENTIAL_NAME) and clone not in path.parents
    ]
    assert outside == [], f"the provision opened a credentials/github-pat.txt outside its clone: {outside}"


def test_the_token_is_written_only_to_the_clone(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """AC-6.3, UB-2 (D3, D8): in a scripted provision's body, the files of the test's tree holding the token are the
    test credential file and the clone's ``credentials/github-pat.txt``, which holds exactly the token and ``\\n``; no
    recorded argv holds it, nor the clone's ``.git/config``, and its ``.git/info/exclude`` names ``credentials/``; no
    record captured at DEBUG holds it, nor the ``repr`` of the yielded ``EphemeralRepository``; afterwards only the
    test credential file holds it. The checkout's own ``credentials/github-pat.txt`` keeps its content, and no
    ``credentials/github-pat.txt`` outside the clone is opened."""
    forge = _ephemeral()
    _require(module=forge, names=PROVISION_SYMBOLS)
    setup = _provisioning(forge=forge, tmp_path=tmp_path)
    sentinel_content = setup.sentinel.read_bytes()
    entered: List[_Entered] = []
    caplog.set_level(level=logging.DEBUG)

    with pytest.MonkeyPatch.context() as patch:
        opened = _record_opens(patch=patch)
        _provide(forge=forge, setup=setup, entered=entered, body_raises=False)

    assert len(entered) == 1, f"the body was entered {len(entered)} times"
    found = entered[0]
    test_credential = setup.test_credential.relative_to(setup.root).as_posix()
    clone_credential = (setup.clone / CREDENTIALS_DIRECTORY / CLONE_CREDENTIAL_NAME).relative_to(setup.root).as_posix()
    assert list(found.holders) == sorted([test_credential, clone_credential]), f"the token was in {found.holders}"
    # Compared into a bool first, so that no assertion prints the file's bytes.
    written = found.clone_credential == (setup.token + LINE_END).encode(encoding=TEXT_ENCODING)
    assert written, "the clone's credentials/github-pat.txt does not hold exactly the test token and a \\n"
    recorded = [*setup.wrapper.recorded, *(argv for argv, _ in setup.git.recorded)]
    assert not [argv for argv in recorded if any(setup.token in part for part in argv)], (
        "a recorded argv holds the token"
    )
    assert setup.token not in found.git_config, "the clone's .git/config holds the token"
    assert EXCLUDED_CREDENTIALS in found.exclude_lines, f"the clone's .git/info/exclude names no {EXCLUDED_CREDENTIALS}"
    holding = [f"{record.name} {record.levelname}" for record in caplog.records if setup.token in record.getMessage()]
    assert holding == [] and setup.token not in caplog.text, f"captured log records hold the token: {holding}"
    assert setup.token not in found.representation, "the repr of the yielded EphemeralRepository holds the token"
    assert _holders(setup=setup) == [test_credential], "a file holding the token outlived the provision"
    _assert_sentinel_untouched(setup=setup, content=sentinel_content, opened=opened)
