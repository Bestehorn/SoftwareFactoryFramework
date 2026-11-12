"""The forge suite's support logic (S): ``test/forge/ephemeral.py`` exercised in the default collection.

``test/forge/`` is the forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge``) against github.com. What its support module decides without the forge is proven here: the refusal of a
distributed run, the per-command credential helper git authenticates with, where the test credential file is found,
and the CI step's write of it; the run id and the repository name it gives (D4); the marker on every product-wrapper
invocation (D10); the teardown guard and the leftover sweep (D9). Only local git runs (``git init``, ``git worktree
add``, ``git credential fill``), in checkouts under pytest's ``tmp_path``; the wrapper runner's ``subprocess.run`` is
replaced by a recorder, and the teardown and the sweep are given ``RecordingWrapperRunner``, a ``WrapperRunner`` that
records each argv and answers it from the test's script. No test opens a connection or needs a test credential file
(UB-1).

``ephemeral.py`` is loaded by path from inside each test body through ``_ephemeral``, never at import and never in a
fixture, and nothing at this module's level names one of its symbols: this file collects whatever ``ephemeral.py``
holds, and a test whose symbol does not exist yet fails in its own body (``_require``). The test doubles are built from
the loaded module the same way, inside a helper a test body calls. The product wrapper, whose marker and origin pattern
are the oracles of D10 and D4, is loaded by path for the test that reads it, and its directory is on ``sys.path`` only
until that test ends.

Run: ``python scripts/run_tests.py test/test_forge_support.py`` (needs git on PATH).
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Sequence, Tuple

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
