"""The GitLab forge suite's support logic (S): ``test/forge_gitlab/ephemeral.py`` exercised in the default collection.

``test/forge_gitlab/`` is the GitLab forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge_gitlab``) against gitlab.com (issue #11, design D1). What its support module decides without the forge is
proven here: the refusal of a distributed run, naming that command (D1); the run id and the project path it gives,
which the product GitLab wrapper's guard accepts (D4, D2); the per-command credential helper git authenticates to
gitlab.com with, ``CLONE_GIT_HELPER`` (D3, D10); where the GitLab test credential file is found, and the CI step's write
of it, by ``write_test_credential`` and by ``test/forge_gitlab/write_credential.py`` ``main`` (D8); the marker on every
product-wrapper invocation and the bytes of its answer (D10); the teardown guard and the leftover sweep (D9). Only local
git runs (``git init``, ``git commit``, ``git worktree add``, ``git rev-parse``, ``git credential fill``), in checkouts
under pytest's ``tmp_path``, and every ``git credential fill`` is given ``-c credential.helper=`` first, so no helper a
configuration file names is asked. The wrapper runner's ``subprocess.run`` is replaced by a recorder, and the teardown
and the sweep are given ``RecordingWrapperRunner``, a ``WrapperRunner`` that records each argv and answers it from the
test's script. No test opens a connection or needs a test credential file (UB-1).

``ephemeral.py`` is loaded by path from inside each test body through ``_ephemeral``, under the ``sys.modules`` key its
``conftest.py`` uses, never at import and never in a fixture, and nothing at this module's level names one of its
symbols: this file collects whatever ``ephemeral.py`` holds, and a test whose symbol does not exist yet fails in its own
body (``_require``). A test double is built from the loaded module the same way, inside a helper a test body calls.
``write_credential.py``, the CI step's command, is loaded the same way, through ``_credential_step`` from inside the one
test that runs its ``main``, and the ``SFF_GITLAB_TEST_TOKEN`` that ``main`` reads is set or removed only through that
test's ``monkeypatch``. The product GitLab wrapper, whose ``EPHEMERAL_PROJECT_PREFIX``, ``_is_ephemeral_project`` and
``TEST_MARKER_OPTION`` are the oracles of D4 and D10, is loaded by path for the test that reads it, and its directory is
on ``sys.path`` only until that test ends.

Run: ``python scripts/run_tests.py test/test_forge_gitlab_support.py`` (needs git on PATH).
"""

from __future__ import annotations

import importlib.util
import json
import locale
import logging
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union
from urllib.parse import quote

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
EPHEMERAL_PATH = ROOT / "test" / "forge_gitlab" / "ephemeral.py"
#: The fixed ``sys.modules`` key of the by-path load, the key of ``test/forge_gitlab/conftest.py`` (D1); the module's
#: dataclasses resolve their module through it.
EPHEMERAL_MODULE = "forge_gitlab_ephemeral"

# D3, D8: the credential files, relative to a working tree or the clone.
CREDENTIALS_DIRECTORY = "credentials"
TEST_CREDENTIAL_NAME = "gitlab-sff-testing-pat.txt"
TEST_CREDENTIAL_FILE = Path(CREDENTIALS_DIRECTORY) / TEST_CREDENTIAL_NAME
#: The GitHub forge suite's test credential file: a decoy the GitLab lookup must pass over.
GITHUB_TEST_CREDENTIAL_NAME = "github-sff-testing-pat.txt"
GIT_DIRECTORY = ".git"
CLONE_GIT_TOKEN_FILE = Path(GIT_DIRECTORY) / "sff-forge-token"
#: The setup note every refusal of the test credential file points to (D7, D8).
SETUP_NOTE = "docs/forge-suite.md"
LINE_END = "\n"
WINDOWS_LINE_END = "\r\n"
TEXT_ENCODING = "utf-8"

# D1: xdist's ``worker_id`` fixture is ``master`` when xdist does not distribute, ``gw<n>`` in a worker; the GitLab
# forge suite's one-process command.
DISTRIBUTED_WORKER_ID = "gw0"
CONTROLLER_WORKER_ID = "master"
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"

# D3: the helper options, and what ``git credential fill`` is asked and answers.
CONFIG_OPTION = "-c"
HELPER_RESET = "credential.helper="
GITLAB_HELPER_PREFIX = "credential.https://gitlab.com.helper=!"
HELPER_OPTION_COUNT = 4
CREDENTIAL_REQUEST = "protocol=https\nhost=gitlab.com\n\n"
FIELD_SEPARATOR = "="
USER_FIELD = "username"
TOKEN_FIELD = "password"
GIT_USERNAME = "sff-forge-suite"
DECOY_VALUE = "decoy"
#: A helper configured before D3's options, as a config file's would be; their reset must keep git from asking it.
DECOY_HELPER = f"!f() {{ printf '{USER_FIELD}={DECOY_VALUE}\\n{TOKEN_FIELD}={DECOY_VALUE}\\n'; }}; f"

# D5, D8 "CI": the secret the CI step reads, and its refusal of an empty one.
SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret
UNAVAILABLE_TOKEN_MESSAGE = f"the secret {SECRET_NAME} is unavailable to this run"
# D8 "CI": the CI step's command, loaded by path as ``ephemeral.py`` is, and the exit codes its ``main`` returns.
WRITE_CREDENTIAL_PATH = ROOT / "test" / "forge_gitlab" / "write_credential.py"
WRITE_CREDENTIAL_MODULE = "forge_gitlab_write_credential"
STEP_WROTE = 0
STEP_REFUSED = 1

GIT = "git"
GIT_EXIT_OK = 0
GIT_TIMEOUT_SECONDS = 60
#: Commits in the scratch checkouts: a runner has no global identity, and no signing key is asked for.
COMMIT_IDENTITY = (
    CONFIG_OPTION,
    "user.name=Forge GitLab Support Test",
    CONFIG_OPTION,
    "user.email=forge-gitlab-support-test@example.invalid",
    CONFIG_OPTION,
    "commit.gpgSign=false",
)

# D2, D4: the product GitLab wrapper, loaded by path for the prefix and the project test its guard reads.
PRODUCT_SCRIPTS = ROOT / "src" / "payload" / "scripts"
PRODUCT_WRAPPER_PATH = PRODUCT_SCRIPTS / "gitlab_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_gitlab_support_product_wrapper"
PRODUCT_SYMBOLS = ("EPHEMERAL_PROJECT_PREFIX", "_is_ephemeral_project")

# D4, D5: the test group, the ephemeral path's prefix, and GitLab's slug rule as the run's path meets it: lowercase
# letters, digits and single ``-``, a letter first and a hex digit last (docs.gitlab.com/user/reserved_names/).
TEST_GROUP = "bestehorn-sff-test"
EPHEMERAL_PREFIX = "sff-test-"
PROJECT_PATH_SEPARATOR = "/"
EPHEMERAL_PATH_FORM = re.compile(r"[a-z](?:-?[a-z0-9])*")
HEX_DIGITS = "0123456789abcdef"
RUN_ID_SAMPLES = 64
#: A run id of #10 D4's form, made by the test: the UTC time, ``-``, a fresh ``uuid4`` hex.
RUN_ID_TIME_FORMAT = "%Y%m%d%H%M%S"
DEFAULT_BRANCH = "main"

# D10: what ``SubprocessWrapperRunner`` passes ``subprocess.run``, and the keywords under which ``subprocess.run`` hands
# a captured stream back as text rather than bytes (``text``, ``universal_newlines``, ``encoding``, ``errors``).
INTERPRETER_OPTION = "-X"
MARKER_ARGV_LENGTH = 4
ARGV_KEYWORD = "args"
ENV_KEYWORD = "env"
CWD_KEYWORD = "cwd"
SHELL_KEYWORD = "shell"
STDIN_KEYWORD = "stdin"
TEXT_MODE_SWITCHES = ("text", "universal_newlines")
ENCODING_KEYWORD = "encoding"
ERRORS_KEYWORD = "errors"
STRICT_ERRORS = "strict"
CARRIAGE_RETURN = "\r"
RUN_ATTRIBUTE = "run"
#: D10: the error handler that turns a standard output's text back into the exact bytes the process wrote.
SURROGATE_ESCAPE = "surrogateescape"

# D9: the records the teardown and the sweep send, and the fields of a listed project (docs.gitlab.com/api/groups/,
# "List projects"): ``created_at`` in ISO 8601 with milliseconds and ``Z``, ``marked_for_deletion_on`` a date or null.
CALL_SUBCOMMAND = "call"
DELETE_OPERATION = "tenant-scale#delete-a-project"
LIST_OPERATION = "tenant-scale#list-projects"
PATH_OPTION = "--path"
ID_PARAMETER = "id"
PARAMETER_ASSIGNMENT = "="
LISTING_ARGUMENTS = (CALL_SUBCOMMAND, LIST_OPERATION, PATH_OPTION, f"{ID_PARAMETER}{PARAMETER_ASSIGNMENT}{TEST_GROUP}")
FIELD_ID = "id"
FIELD_NAME = "name"
FIELD_PATH = "path"
FIELD_PATH_WITH_NAMESPACE = "path_with_namespace"
FIELD_NAMESPACE = "namespace"
FIELD_FULL_PATH = "full_path"
FIELD_KIND = "kind"
FIELD_CREATED_AT = "created_at"
FIELD_MARKED_FOR_DELETION_ON = "marked_for_deletion_on"
FIELD_MESSAGE = "message"
GROUP_KIND = "group"
CREATED_AT_SECONDS_FORMAT = "%Y-%m-%dT%H:%M:%S"
UTC_SUFFIX = "Z"
MICROSECONDS_PER_MILLISECOND = 1000
ONE_DAY = timedelta(days=1)
ONE_MILLISECOND = timedelta(milliseconds=1)
LONG_AGO = timedelta(days=30)
SWEEP_NOW = datetime(year=2026, month=11, day=22, hour=12, tzinfo=timezone.utc)
MARKED_ON = "2026-11-15"
CREATED_PROJECT_ID = 81234567
FIRST_LISTED_ID = 70000001
#: The answer of an accepted deletion as ``call`` prints it: gitlab.com marks the project and answers ``202``.
DELETION_ACCEPTED_MESSAGE = "202 Accepted"
#: The product GitLab wrapper's exit on a ``GitLabAPIError``, and the line ``main`` ``_report`` logs for it, which is
#: ``Transport._send``'s ``"{method} {url} answered {status}: {error_text}"``, followed by the body.
WRAPPER_API_FAILURE = 1
API_FAILURE = "DELETE https://gitlab.com/api/v4/projects/{encoded} answered {status}: {message}"
NOT_FOUND_STATUS = 404
BAD_REQUEST_STATUS = 400
FORBIDDEN_STATUS = 403
NOT_FOUND_MESSAGE = "404 Project Not Found"
#: ``mark_for_deletion_base_service.rb``: "#{resource_name.titleize} has already been marked for deletion".
ALREADY_MARKED_MESSAGE = "Project has already been marked for deletion"
OTHER_BAD_REQUEST_MESSAGE = "Project could not be marked for deletion"
FORBIDDEN_MESSAGE = "403 Forbidden"
OTHER_NAMESPACE = "Bestehorn"
SUBGROUP_NAMESPACE = f"{TEST_GROUP}/sub"
UNPREFIXED_PATH = "SoftwareFactoryFramework"

# The symbols each test needs of ``ephemeral.py`` (D1, D3, D4, D8, D9, D10).
DISTRIBUTED_RUN_SYMBOLS = ("ForgeSuiteError", "ForgeSetupError", "GITLAB_FORGE_COMMAND", "refuse_distributed_run")
RUN_ID_SYMBOLS = ("new_run_id", "TEST_GROUP", "ephemeral_path", "ephemeral_full_path")
HELPER_SYMBOLS = ("ForgeSetupError", "CLONE_GIT_HELPER", "CLONE_GIT_TOKEN_FILE")
LOOKUP_SYMBOLS = ("ForgeSetupError", "TEST_CREDENTIAL_FILE", "find_test_credential")
CI_STEP_SYMBOLS = ("ForgeSetupError", "TEST_CREDENTIAL_FILE", "SECRET_NAME", "write_test_credential")
RUNNER_SYMBOLS = ("WrapperRunner", "Invocation")
SUBPROCESS_RUNNER_SYMBOLS = (*RUNNER_SYMBOLS, "SubprocessWrapperRunner", "PRODUCT_WRAPPER")
TEARDOWN_SYMBOLS = (*RUNNER_SYMBOLS, "TEST_GROUP", "ForgeTeardownRefusedError", "CreatedProject", "delete_ephemeral")
PROPERTY_SYMBOLS = (*RUNNER_SYMBOLS, "sweep_leftovers")
SWEEP_SYMBOLS = (
    *RUNNER_SYMBOLS,
    "TEST_GROUP",
    "LEFTOVER_AGE",
    "ForgeCommandError",
    "ForgeSweepRefusedError",
    "ProjectRecord",
    "list_group_projects",
    "is_leftover",
    "select_leftovers",
    "sweep_leftovers",
    "delete_leftover",
)


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
    """``test/forge_gitlab/ephemeral.py``, the GitLab forge suite's support module, loaded by path
    (``_load_by_path``)."""
    return _load_by_path(
        path=EPHEMERAL_PATH, name=EPHEMERAL_MODULE, description="the GitLab forge suite's support module"
    )


def _credential_step() -> ModuleType:
    """``test/forge_gitlab/write_credential.py``, the GitLab forge job's credential step, loaded by path
    (``_load_by_path``)."""
    return _load_by_path(
        path=WRITE_CREDENTIAL_PATH, name=WRITE_CREDENTIAL_MODULE, description="the GitLab CI step's command"
    )


def _require(*, module: ModuleType, names: Sequence[str]) -> None:
    """Fails the calling test on this assertion while ``module`` lacks one of ``names``."""
    missing = [name for name in names if not hasattr(module, name)]
    source = Path(str(module.__file__)).resolve().relative_to(ROOT).as_posix()
    assert not missing, f"{source} defines no {', '.join(missing)}"


def _product_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """``src/payload/scripts/gitlab_wrapper.py``, loaded by path as a fresh module, for the prefix and the project test
    its guard reads (D2, D4); its directory is first on ``sys.path``, so the wrapper's own bootstrap adds no entry, and
    the module is in ``sys.modules``, until the test ends."""
    assert PRODUCT_WRAPPER_PATH.is_file(), f"the product GitLab wrapper {PRODUCT_WRAPPER_PATH} does not exist"
    monkeypatch.syspath_prepend(path=str(PRODUCT_SCRIPTS))
    spec = importlib.util.spec_from_file_location(name=PRODUCT_WRAPPER_MODULE, location=PRODUCT_WRAPPER_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {PRODUCT_WRAPPER_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    monkeypatch.setitem(dic=sys.modules, name=PRODUCT_WRAPPER_MODULE, value=module)
    spec.loader.exec_module(module=module)
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


def _write_token(*, path: Path, token: str) -> Path:
    """``path`` holding ``token`` and a line end, its directories created; returns ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data=(token + LINE_END).encode(encoding=TEXT_ENCODING))
    return path


def _write_credential(*, directory: Path, name: str, token: str) -> Path:
    """``directory/credentials/<name>`` holding ``token`` and a line end; returns its path."""
    return _write_token(path=directory / CREDENTIALS_DIRECTORY / name, token=token)


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


def _holds_the_token_and_a_line_end(*, path: Path, token: str) -> bool:
    """Whether ``path`` holds exactly ``token`` followed by one line end; a bool, so no assertion prints the bytes."""
    return path.read_bytes() in (
        (token + LINE_END).encode(encoding=TEXT_ENCODING),
        (token + WINDOWS_LINE_END).encode(encoding=TEXT_ENCODING),
    )


# ---------------------------------------------------------------------------------------------------------------------
# The distributed-run refusal (D1) and the run id (D4)
# ---------------------------------------------------------------------------------------------------------------------


def test_a_distributed_run_is_refused() -> None:
    """AC-1.1 (D1): a session fixture runs once per xdist worker, so ``refuse_distributed_run`` refuses any worker id
    but ``master`` with ``ForgeSetupError``, a ``ForgeSuiteError``, whose message names ``GITLAB_FORGE_COMMAND``, the
    GitLab forge suite's one-process command; ``master`` is let through."""
    forge = _ephemeral()
    _require(module=forge, names=DISTRIBUTED_RUN_SYMBOLS)
    assert forge.GITLAB_FORGE_COMMAND == GITLAB_FORGE_COMMAND, (
        f"GITLAB_FORGE_COMMAND is {forge.GITLAB_FORGE_COMMAND!r}, not D1's {GITLAB_FORGE_COMMAND!r}"
    )
    assert issubclass(forge.ForgeSetupError, forge.ForgeSuiteError), "ForgeSetupError is a ForgeSuiteError (D10)"

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.refuse_distributed_run(worker_id=DISTRIBUTED_WORKER_ID)

    message = str(refused.value)
    assert GITLAB_FORGE_COMMAND in message, f"the refusal does not name {GITLAB_FORGE_COMMAND}: {message}"
    assert forge.refuse_distributed_run(worker_id=CONTROLLER_WORKER_ID) is None


def test_a_run_id_names_an_ephemeral_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1.2 (D4): repeated ``new_run_id`` calls give pairwise distinct ids; ``ephemeral_path`` is the product GitLab
    wrapper's ``EPHEMERAL_PROJECT_PREFIX`` then the id, a path GitLab's slug rule admits, and ``ephemeral_full_path`` is
    ``bestehorn-sff-test/<that path>``, which the product's ``_is_ephemeral_project`` accepts, while it refuses the path
    alone (D2: a text without ``/`` is not one)."""
    forge = _ephemeral()
    _require(module=forge, names=RUN_ID_SYMBOLS)
    wrapper = _product_wrapper(monkeypatch=monkeypatch)
    _require(module=wrapper, names=PRODUCT_SYMBOLS)
    assert forge.TEST_GROUP == TEST_GROUP, f"TEST_GROUP is {forge.TEST_GROUP!r}, not {TEST_GROUP!r} (D5, DL-002)"
    assert wrapper.EPHEMERAL_PROJECT_PREFIX == EPHEMERAL_PREFIX, (
        f"the product's EPHEMERAL_PROJECT_PREFIX is {wrapper.EPHEMERAL_PROJECT_PREFIX!r} (D2)"
    )

    run_ids = [forge.new_run_id() for _ in range(RUN_ID_SAMPLES)]
    assert len(set(run_ids)) == len(run_ids), f"repeated calls gave an id twice: {sorted(run_ids)}"

    for run_id in run_ids:
        path = forge.ephemeral_path(run_id=run_id)
        assert path == EPHEMERAL_PREFIX + run_id, f"ephemeral_path gave {path!r} for {run_id!r}"
        assert EPHEMERAL_PATH_FORM.fullmatch(string=path) is not None and path[-1] in HEX_DIGITS, (
            f"the path {path!r} is not lowercase letters, digits and single '-', a letter first and a hex digit last"
        )
        full_path = forge.ephemeral_full_path(run_id=run_id)
        assert full_path == TEST_GROUP + PROJECT_PATH_SEPARATOR + path, (
            f"ephemeral_full_path gave {full_path!r} for {run_id!r}"
        )
        assert wrapper._is_ephemeral_project(project_id=full_path) is True, (
            f"the product's _is_ephemeral_project refuses {full_path!r}"
        )
        assert wrapper._is_ephemeral_project(project_id=path) is False, (
            f"the product's _is_ephemeral_project accepts the path {path!r} without its namespace"
        )


# ---------------------------------------------------------------------------------------------------------------------
# The credential helper (D3, D10), the test credential's lookup and the CI step's write (D8)
# ---------------------------------------------------------------------------------------------------------------------


def test_the_credential_helper_answers_git_with_the_clone_token(tmp_path: Path) -> None:
    """AC-6.3 (D3, D10): ``CLONE_GIT_HELPER(clone=...)`` gives exactly ``-c credential.helper=`` then ``-c
    credential.https://gitlab.com.helper=!...``, and no option holds the token; git, given a reset of its own, a decoy
    helper and then those options before ``credential fill``, answers ``protocol=https`` and ``host=gitlab.com`` with
    the username ``sff-forge-suite`` and the token of the clone's ``.git/sff-forge-token``, which is compared and never
    printed; a clone path holding ``'`` is refused with ``ForgeSetupError``."""
    forge = _ephemeral()
    _require(module=forge, names=HELPER_SYMBOLS)
    assert Path(forge.CLONE_GIT_TOKEN_FILE) == CLONE_GIT_TOKEN_FILE, (
        f"CLONE_GIT_TOKEN_FILE is {forge.CLONE_GIT_TOKEN_FILE!r}, not {CLONE_GIT_TOKEN_FILE.as_posix()} (D3)"
    )
    clone = tmp_path / "clone with space"
    token = _new_token(label="clone")
    _write_token(path=clone / CLONE_GIT_TOKEN_FILE, token=token)

    options = list(forge.CLONE_GIT_HELPER(clone=clone))
    assert not [option for option in options if token in str(option)], "a helper option holds the clone's token"
    assert len(options) == HELPER_OPTION_COUNT and options[:3] == [CONFIG_OPTION, HELPER_RESET, CONFIG_OPTION], (
        f"the options are not the helper reset then the gitlab.com helper: {options}"
    )
    assert str(options[3]).startswith(GITLAB_HELPER_PREFIX), (
        f"the second option is no gitlab.com shell helper: {options}"
    )

    answer = _git(
        arguments=[
            CONFIG_OPTION,
            HELPER_RESET,
            CONFIG_OPTION,
            f"credential.helper={DECOY_HELPER}",
            *options,
            "credential",
            "fill",
        ],
        cwd=tmp_path,
        request=CREDENTIAL_REQUEST,
    )
    fields = _answer_fields(text=answer.stdout)
    user = fields.get(USER_FIELD)
    assert user == GIT_USERNAME, f"git answered the user {user!r}, not {GIT_USERNAME!r}"
    # Compared into a bool first: pytest's introspection would print an answered password.
    answered_the_clone_token = fields.get(TOKEN_FIELD) == token
    assert answered_the_clone_token, "git did not answer the token of the clone's .git/sff-forge-token"

    quoted = tmp_path / "the clone's directory"
    _write_token(path=quoted / CLONE_GIT_TOKEN_FILE, token=_new_token(label="quoted"))
    with pytest.raises(expected_exception=forge.ForgeSetupError):
        forge.CLONE_GIT_HELPER(clone=quoted)


def test_the_test_credential_is_found_in_the_checkout_or_its_main_tree(tmp_path: Path) -> None:
    """AC-6.1 (D8): ``find_test_credential`` given this suite's ``TEST_CREDENTIAL_FILE``,
    ``credentials/gitlab-sff-testing-pat.txt``, finds the checkout's own file, else a linked worktree's main working
    tree's, and never the GitHub suite's file beside it; with neither GitLab file, the refusal names both paths and
    the setup note."""
    forge = _ephemeral()
    _require(module=forge, names=LOOKUP_SYMBOLS)
    assert Path(forge.TEST_CREDENTIAL_FILE) == TEST_CREDENTIAL_FILE, (
        f"TEST_CREDENTIAL_FILE is {forge.TEST_CREDENTIAL_FILE!r}, not {TEST_CREDENTIAL_FILE.as_posix()} (D8)"
    )
    credential_file = forge.TEST_CREDENTIAL_FILE
    main_tree = tmp_path / "main tree"
    _init_checkout(path=main_tree)
    _write_credential(directory=main_tree, name=GITHUB_TEST_CREDENTIAL_NAME, token=_new_token(label="github"))
    main_credential = _write_credential(directory=main_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="main"))
    _assert_found(
        found=forge.find_test_credential(checkout=main_tree, credential_file=credential_file), expected=main_credential
    )

    linked_tree = tmp_path / "linked tree"
    _git(arguments=["worktree", "add", "--detach", "--quiet", str(linked_tree)], cwd=main_tree)
    linked_credential = linked_tree / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    assert not linked_credential.exists(), f"the new worktree already holds {linked_credential}"
    _assert_found(
        found=forge.find_test_credential(checkout=linked_tree, credential_file=credential_file),
        expected=main_credential,
    )

    _write_credential(directory=linked_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="linked"))
    _assert_found(
        found=forge.find_test_credential(checkout=linked_tree, credential_file=credential_file),
        expected=linked_credential,
    )

    common_dir = _git(arguments=["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=linked_tree)
    main_credential_by_git = Path(common_dir.stdout.strip()).parent / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    linked_credential.unlink()
    main_credential.unlink()
    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.find_test_credential(checkout=linked_tree, credential_file=credential_file)
    message = str(refused.value)
    assert _names_one_of(message=message, paths=(linked_credential,)), (
        f"the refusal does not name {linked_credential}: {message}"
    )
    assert _names_one_of(message=message, paths=(main_credential, main_credential_by_git)), (
        f"the refusal does not name {main_credential}: {message}"
    )
    assert SETUP_NOTE in message, f"the refusal does not name {SETUP_NOTE}: {message}"


def test_a_missing_secret_fails_the_credential_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-5.3 (D5, D8 "CI"): ``write_test_credential`` given this suite's ``credential_file`` and ``secret_name``
    refuses an empty token with "the secret SFF_GITLAB_TEST_TOKEN is unavailable to this run" and writes nothing; a
    token is written followed by a line end as the checkout's ``credentials/gitlab-sff-testing-pat.txt``, and no other
    file is touched. ``write_credential.main``, the GitLab forge job's credential step, given ``SFF_GITLAB_TEST_TOKEN``
    unset or empty, logs one record holding that text, writes nothing and returns 1; given a token, it writes the
    checkout's test credential file and returns 0."""
    forge = _ephemeral()
    _require(module=forge, names=CI_STEP_SYMBOLS)
    assert forge.SECRET_NAME == SECRET_NAME, f"SECRET_NAME is {forge.SECRET_NAME!r}, not {SECRET_NAME!r} (D8)"
    assert Path(forge.TEST_CREDENTIAL_FILE) == TEST_CREDENTIAL_FILE, (
        f"TEST_CREDENTIAL_FILE is {forge.TEST_CREDENTIAL_FILE!r}, not {TEST_CREDENTIAL_FILE.as_posix()} (D8)"
    )
    checkout = tmp_path / "checkout"
    (checkout / CREDENTIALS_DIRECTORY).mkdir(parents=True)
    before = _tree(root=checkout)

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.write_test_credential(
            token="", checkout=checkout, credential_file=forge.TEST_CREDENTIAL_FILE, secret_name=forge.SECRET_NAME
        )
    assert UNAVAILABLE_TOKEN_MESSAGE in str(refused.value), f"the refusal says: {refused.value}"
    assert _tree(root=checkout) == before, "the refused write left a file in the checkout"

    token = _new_token(label="ci")
    forge.write_test_credential(
        token=token, checkout=checkout, credential_file=forge.TEST_CREDENTIAL_FILE, secret_name=forge.SECRET_NAME
    )
    written = checkout / TEST_CREDENTIAL_FILE
    assert _tree(root=checkout) == sorted([*before, written.relative_to(checkout).as_posix()]), (
        "the write touched another file than the test credential file"
    )
    holds_the_token = _holds_the_token_and_a_line_end(path=written, token=token)
    assert holds_the_token, "the test credential file does not hold the token followed by a line end"

    _assert_the_credential_step_judges_the_secret(
        step=_credential_step(), checkout=tmp_path / "ci step checkout", monkeypatch=monkeypatch, caplog=caplog
    )


def _assert_the_credential_step_judges_the_secret(
    *, step: ModuleType, checkout: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-5.3 (D5, D8 "CI"): ``step.main(checkout=checkout)`` with ``SFF_GITLAB_TEST_TOKEN`` removed, then empty, logs
    one record holding the refusal, returns 1 and leaves ``checkout`` as it was; with a token, it writes the token and a
    line end as the checkout's ``credentials/gitlab-sff-testing-pat.txt``, touches no other file, logs no record holding
    the token and returns 0."""
    (checkout / CREDENTIALS_DIRECTORY).mkdir(parents=True)
    before = _tree(root=checkout)
    caplog.set_level(level=logging.DEBUG)

    for unavailable in (None, ""):
        if unavailable is None:
            monkeypatch.delenv(name=SECRET_NAME, raising=False)
        else:
            monkeypatch.setenv(name=SECRET_NAME, value=unavailable)
        state = "unset" if unavailable is None else "empty"
        caplog.clear()
        exit_code = step.main(checkout=checkout)
        assert exit_code == STEP_REFUSED, f"main returned {exit_code!r} with {SECRET_NAME} {state}, not 1"
        refusals = [record for record in caplog.records if UNAVAILABLE_TOKEN_MESSAGE in record.getMessage()]
        assert len(refusals) == 1, (
            f"main logged {len(refusals)} records saying {UNAVAILABLE_TOKEN_MESSAGE!r} with {SECRET_NAME} {state}, "
            f"not one: {caplog.messages}"
        )
        assert _tree(root=checkout) == before, f"main left a file in the checkout with {SECRET_NAME} {state}"

    token = _new_token(label="ci-step")
    monkeypatch.setenv(name=SECRET_NAME, value=token)
    caplog.clear()
    exit_code = step.main(checkout=checkout)
    assert exit_code == STEP_WROTE, f"main returned {exit_code!r} with a token in {SECRET_NAME}, not 0"
    written = checkout / TEST_CREDENTIAL_FILE
    assert _tree(root=checkout) == sorted([*before, written.relative_to(checkout).as_posix()]), (
        "main touched another file than the checkout's test credential file"
    )
    holds_the_token = _holds_the_token_and_a_line_end(path=written, token=token)
    assert holds_the_token, "main's test credential file does not hold the token followed by a line end"
    logged_the_token = token in caplog.text
    assert not logged_the_token, "a record main logged holds the token"


# ---------------------------------------------------------------------------------------------------------------------
# The wrapper runner (D10), the teardown guard and the sweep (D9)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Answer:
    """What a scripted product-wrapper invocation answers, as ``Invocation`` carries it: its exit code, standard output
    and standard error."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


SUCCESS = _Answer(returncode=0)
DELETION_ACCEPTED = _Answer(
    returncode=0, stdout=json.dumps(obj={FIELD_MESSAGE: DELETION_ACCEPTED_MESSAGE}, indent=2) + LINE_END
)


@dataclass(frozen=True)
class _ProcessAnswer:
    """What a started product-wrapper process answers: its exit code and the bytes of its two streams."""

    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


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
class _ListedProject:
    """One project of a drawn listing, with the four properties its expected deletion is computed from (AC-3.1 to
    AC-3.3): ``deleted`` holds exactly when the project is the test group's, its path has the prefix, it is more than a
    day old, and no ``marked_for_deletion_on`` is set."""

    namespace: str
    path: str
    age_milliseconds: int
    marked_on: Optional[str]
    marked_key_listed: bool
    deleted: bool


def _listed_project(
    *,
    in_group: bool,
    prefixed: bool,
    old: bool,
    scheduled: bool,
    other_namespace: str,
    suffix: str,
    unprefixed_path: str,
    young_age: int,
    old_age: int,
    marked_on: str,
    unscheduled_key_listed: bool,
) -> _ListedProject:
    """A listed project built from its drawn namespace side, path side, age side and schedule side; an unscheduled one
    lists ``marked_for_deletion_on`` as null or not at all (D9 ``ProjectRecord.of``)."""
    return _ListedProject(
        namespace=TEST_GROUP if in_group else other_namespace,
        path=EPHEMERAL_PREFIX + suffix if prefixed else unprefixed_path,
        age_milliseconds=old_age if old else young_age,
        marked_on=marked_on if scheduled else None,
        marked_key_listed=scheduled or unscheduled_key_listed,
        deleted=in_group and prefixed and old and not scheduled,
    )


# AC-3.1 to AC-3.3: the property's listings. Each drawn project's four sides are drawn first, so the expected deletions
# follow from the draw and never from the code under test. The other namespaces and paths hold the near misses of
# design.md Correctness Properties: a subgroup and an ``-archive`` sibling of the test group, ``sff-test`` without the
# dash, and ``sff-test-`` inside a path.
OTHER_NAMESPACES = (OTHER_NAMESPACE, "bestehorn", "sff-test", f"{TEST_GROUP}-archive", SUBGROUP_NAMESPACE)
#: Suffixes after the prefix, among them the form GitLab renames a project marked for deletion to (D4).
PREFIXED_SUFFIXES = st.from_regex(regex=r"[a-z0-9][a-z0-9-]{0,24}(?:-deletion_scheduled-[0-9]{1,9})?", fullmatch=True)
#: Paths without the prefix, among them near misses (``sff-testing``, ``sff_test-1``, the prefix after the start).
UNPREFIXED_PATHS = st.from_regex(
    regex=r"(?:sff-test|sff_test-|x-sff-test-|test-sff-test-)?[a-z0-9][a-z0-9_.-]{0,24}", fullmatch=True
).filter(lambda path: not path.startswith(EPHEMERAL_PREFIX))
#: Ages in milliseconds at the sweep: a day or less (an hour in the future included) is kept, more than a day is not.
DAY_MILLISECONDS = 86_400_000
YOUNG_AGES = st.integers(min_value=-3_600_000, max_value=DAY_MILLISECONDS)
OLD_AGES = st.integers(min_value=DAY_MILLISECONDS + 1, max_value=DAY_MILLISECONDS * 400)
#: Whole seconds, so a drawn age in milliseconds is exactly the difference the sweep computes from ``created_at``.
SWEEP_MOMENTS = st.datetimes(
    min_value=datetime(year=2024, month=1, day=1),
    max_value=datetime(year=2035, month=12, day=31),
    timezones=st.just(value=timezone.utc),
).map(lambda moment: moment.replace(microsecond=0))
MARKED_DATES = st.dates(min_value=date(year=2024, month=1, day=1), max_value=date(year=2035, month=12, day=31)).map(
    lambda day: day.isoformat()
)
LISTED_PROJECTS = st.builds(
    _listed_project,
    in_group=st.booleans(),
    prefixed=st.booleans(),
    old=st.booleans(),
    scheduled=st.booleans(),
    other_namespace=st.sampled_from(elements=OTHER_NAMESPACES),
    suffix=PREFIXED_SUFFIXES,
    unprefixed_path=UNPREFIXED_PATHS,
    young_age=YOUNG_AGES,
    old_age=OLD_AGES,
    marked_on=MARKED_DATES,
    unscheduled_key_listed=st.booleans(),
)
MAX_LISTING = 12
SWEEP_EXAMPLES = 60
LISTINGS = st.lists(
    elements=LISTED_PROJECTS,
    max_size=MAX_LISTING,
    unique_by=lambda project: (project.namespace, project.path),
)


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
    raise AssertionError(f"the product GitLab wrapper was invoked where nothing may be sent: {arguments}")


def _gitlab_time(*, moment: datetime) -> str:
    """``moment`` (aware UTC) as GitLab writes ``created_at``: ISO 8601, its milliseconds when it has a fraction of a
    second, and ``Z``."""
    whole_seconds = moment.strftime(CREATED_AT_SECONDS_FORMAT)
    milliseconds = moment.microsecond // MICROSECONDS_PER_MILLISECOND
    fraction = f".{milliseconds:03d}" if moment.microsecond else ""
    return whole_seconds + fraction + UTC_SUFFIX


def _full_path(*, namespace: str, path: str) -> str:
    """A project's ``<namespace>/<path>``."""
    return namespace + PROJECT_PATH_SEPARATOR + path


def _project_item(
    *,
    project_id: int,
    namespace: str,
    path: str,
    created_at: datetime,
    marked_on: Optional[str] = None,
    marked_key_listed: bool = True,
) -> Dict[str, Any]:
    """One item of ``call tenant-scale#list-projects``'s printed array, as GitLab lists a project of a group;
    ``marked_for_deletion_on`` is ``marked_on`` when ``marked_key_listed``, else the item has no such key."""
    item: Dict[str, Any] = {
        FIELD_ID: project_id,
        FIELD_NAME: path,
        FIELD_PATH: path,
        FIELD_PATH_WITH_NAMESPACE: _full_path(namespace=namespace, path=path),
        FIELD_NAMESPACE: {
            FIELD_PATH: namespace.rpartition(PROJECT_PATH_SEPARATOR)[2],
            FIELD_FULL_PATH: namespace,
            FIELD_KIND: GROUP_KIND,
        },
        FIELD_CREATED_AT: _gitlab_time(moment=created_at),
    }
    if marked_key_listed:
        item[FIELD_MARKED_FOR_DELETION_ON] = marked_on
    return item


def _sweep_script(*, items: Sequence[Mapping[str, Any]], deletion: _Answer) -> Callable[..., _Answer]:
    """A script answering D9's listing with ``items`` printed as ``call`` prints a list, and every ``call
    tenant-scale#delete-a-project`` with ``deletion``; any other invocation fails the test."""
    listing = _Answer(returncode=0, stdout=json.dumps(obj=list(items), indent=2) + LINE_END)

    def script(*, arguments: List[str]) -> _Answer:
        if arguments == list(LISTING_ARGUMENTS):
            return listing
        if arguments[:2] == [CALL_SUBCOMMAND, DELETE_OPERATION]:
            return deletion
        raise AssertionError(f"the sweep sent an invocation the test scripted no answer for: {arguments}")

    return script


def _deletion(*, namespace: str, path: str) -> List[str]:
    """D9's ``call tenant-scale#delete-a-project --path id=<namespace>/<path>``."""
    return [
        CALL_SUBCOMMAND,
        DELETE_OPERATION,
        PATH_OPTION,
        ID_PARAMETER + PARAMETER_ASSIGNMENT + _full_path(namespace=namespace, path=path),
    ]


def _api_failure(*, full_path: str, status: int, message: str) -> _Answer:
    """The product GitLab wrapper's answer to a deletion GitLab refused with ``status`` and ``message``: exit 1, and on
    standard error the line ``main`` ``_report`` logs, then the body it logs as the error's details."""
    line = API_FAILURE.format(encoded=quote(string=full_path, safe=""), status=status, message=message)
    body = json.dumps(obj={FIELD_MESSAGE: message})
    return _Answer(returncode=WRAPPER_API_FAILURE, stderr=line + LINE_END + body + LINE_END)


def _run_id() -> str:
    """A run id of D4's form, made by the test: the UTC time, ``-``, a fresh ``uuid4`` hex."""
    return f"{datetime.now(tz=timezone.utc).strftime(RUN_ID_TIME_FORMAT)}-{uuid.uuid4().hex}"


def _created_project(*, forge: ModuleType, namespace: str, path: str) -> Any:
    """A ``CreatedProject`` of the loaded module, as D9 step 6 makes one from the creation's answer: its ``id``
    (``project_id``), ``namespace.full_path`` (``namespace``), ``path`` and ``default_branch``."""
    return forge.CreatedProject(
        project_id=CREATED_PROJECT_ID, namespace=namespace, path=path, default_branch=DEFAULT_BRANCH
    )


def _captured(*, data: bytes, keywords: Mapping[str, Any]) -> Union[bytes, str]:
    """``data`` as ``subprocess.run`` hands back a captured stream given ``keywords``: the bytes, or, under ``text``,
    ``universal_newlines``, ``encoding`` or ``errors``, the text that encoding (the locale's by default) and handler
    (``strict`` by default) decode, its line ends translated to ``\\n``."""
    text_mode = any(keywords.get(switch) for switch in TEXT_MODE_SWITCHES) or any(
        keywords.get(name) is not None for name in (ENCODING_KEYWORD, ERRORS_KEYWORD)
    )
    if not text_mode:
        return data
    encoding = keywords.get(ENCODING_KEYWORD) or locale.getpreferredencoding(do_setlocale=False)
    text = data.decode(encoding=encoding, errors=keywords.get(ERRORS_KEYWORD) or STRICT_ERRORS)
    return text.replace(WINDOWS_LINE_END, LINE_END).replace(CARRIAGE_RETURN, LINE_END)


def _fake_subprocess_run(*, calls: List[_SubprocessCall], answers: Sequence[_ProcessAnswer]) -> Callable[..., Any]:
    """A ``subprocess.run`` that records each call in ``calls`` and answers the calls with ``answers`` in turn, each
    stream handed back as ``subprocess.run`` would given the call's keywords (``_captured``)."""
    pending = list(answers)

    def run(*positional: Any, **keywords: Any) -> subprocess.CompletedProcess[Any]:
        call = _SubprocessCall(positional=positional, keywords=dict(keywords))
        calls.append(call)
        assert pending, f"subprocess.run was called more often than the runner was: {call.argv()}"
        answer = pending.pop(0)
        return subprocess.CompletedProcess(
            args=call.argv(),
            returncode=answer.returncode,
            stdout=_captured(data=answer.stdout, keywords=keywords),
            stderr=_captured(data=answer.stderr, keywords=keywords),
        )

    return run


#: AC-4.3, D10: an answer that is no UTF-8 text, as ``call`` writes an archive with ``print_bytes``: a zip header, bytes
#: no UTF-8 decoder accepts, and a ``\r\n`` that a text-mode capture would translate.
ARCHIVE_BYTES = b"PK\x03\x04\x14\x00\x08\x00\xff\xfe\r\n\x80\x9f\xc3sff-test-x/README.md\r\n"
#: AC-4.3: product-wrapper invocations in two working directories, each with the answer its process gives; the UTF-8
#: texts hold a character outside ASCII, which a locale decoder other than UTF-8 reads differently.
MARKER_CASES: Tuple[Tuple[str, Tuple[str, ...], _ProcessAnswer], ...] = (
    (
        "clone one",
        (CALL_SUBCOMMAND, "tenant-scale#retrieve-a-project"),
        _ProcessAnswer(
            returncode=0, stdout='{\n  "description": "Café sff-test-x"\n}\n'.encode(encoding=TEXT_ENCODING)
        ),
    ),
    (
        "clone two",
        (
            CALL_SUBCOMMAND,
            "create#retrieve-file-archive-from-a-repository",
            PATH_OPTION,
            "format=zip",
            "--query",
            "sha=" + "5eed" * 10,
        ),
        _ProcessAnswer(returncode=0, stdout=ARCHIVE_BYTES),
    ),
    (
        "clone two",
        ("issue", "show", "1"),
        _ProcessAnswer(
            returncode=WRAPPER_API_FAILURE,
            stderr=(
                "GET https://gitlab.com/api/v4/projects/bestehorn-sff-test%2Fsff-test-x/issues/1 answered 404: "
                "404 Not Found — café\n"
            ).encode(encoding=TEXT_ENCODING),
        ),
    ),
)


def test_every_wrapper_invocation_carries_the_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-4.3 (D10): every ``SubprocessWrapperRunner.run`` starts ``[sys.executable, "-X", <the product GitLab
    wrapper's TEST_MARKER_OPTION>, str(PRODUCT_WRAPPER), *arguments]`` as a list, in its directory, with standard input
    from ``DEVNULL``, never through a shell, and passes ``subprocess.run`` no ``env``; ``PRODUCT_WRAPPER`` is the
    product GitLab wrapper's absolute path. The process's answer comes back as the ``Invocation``: its exit code, its
    standard error as UTF-8 text, and its standard output as text whose ``surrogateescape`` encoding is the process's
    exact bytes, a non-UTF-8 answer included."""
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
    monkeypatch.setattr(target=subprocess, name=RUN_ATTRIBUTE, value=_fake_subprocess_run(calls=calls, answers=answers))
    for directory_name, arguments, answer in MARKER_CASES:
        directory = tmp_path / directory_name
        directory.mkdir(exist_ok=True)
        invocation = forge.SubprocessWrapperRunner(directory=directory).run(arguments=list(arguments))
        assert invocation.returncode == answer.returncode, (
            f"the Invocation of {list(arguments)} exited {invocation.returncode!r}, not {answer.returncode}"
        )
        assert isinstance(invocation.stdout, str) and isinstance(invocation.stderr, str), (
            f"the Invocation of {list(arguments)} does not carry its streams as text: {invocation!r}"
        )
        given_back = invocation.stdout.encode(encoding=TEXT_ENCODING, errors=SURROGATE_ESCAPE)
        assert given_back == answer.stdout, (
            f"the standard output of {list(arguments)} does not come back byte for byte: {given_back!r} is not "
            f"{answer.stdout!r}"
        )
        expected_stderr = answer.stderr.decode(encoding=TEXT_ENCODING)
        assert invocation.stderr == expected_stderr, (
            f"the standard error of {list(arguments)} is {invocation.stderr!r}, not {expected_stderr!r}"
        )

    assert len(calls) == len(MARKER_CASES), f"{len(MARKER_CASES)} invocations started {len(calls)} processes"
    for call, (directory_name, arguments, _) in zip(calls, MARKER_CASES):
        argv = call.argv()
        assert argv[:MARKER_ARGV_LENGTH] == [sys.executable, INTERPRETER_OPTION, marker, str(forge.PRODUCT_WRAPPER)], (
            f"the invocation does not start with the interpreter, -X {marker} and the product GitLab wrapper: {argv}"
        )
        assert argv[MARKER_ARGV_LENGTH:] == list(arguments), (
            f"the wrapper's arguments are not {list(arguments)}: {argv}"
        )
        assert ENV_KEYWORD not in call.keywords, f"subprocess.run received an env for {argv}"
        assert len(call.positional) <= 1, f"subprocess.run received positional arguments past the argv: {call}"
        assert not call.keywords.get(SHELL_KEYWORD, False), f"subprocess.run ran {argv} through a shell"
        assert call.keywords.get(STDIN_KEYWORD) == subprocess.DEVNULL, (
            f"subprocess.run gave {argv} the standard input {call.keywords.get(STDIN_KEYWORD)!r}, not DEVNULL"
        )
        working_directory = call.keywords.get(CWD_KEYWORD)
        assert working_directory is not None and (
            Path(working_directory).resolve() == (tmp_path / directory_name).resolve()
        ), f"{argv} ran in {working_directory}, not in the runner's directory {tmp_path / directory_name}"


def test_the_teardown_deletes_only_this_runs_project() -> None:
    """AC-2.1 (D9 "The teardown guard"): given the record of this run's creation, ``delete_ephemeral`` sends exactly
    one ``call tenant-scale#delete-a-project --path id=bestehorn-sff-test/sff-test-<run id>``."""
    forge = _ephemeral()
    _require(module=forge, names=TEARDOWN_SYMBOLS)
    run_id = _run_id()
    path = EPHEMERAL_PREFIX + run_id
    runner = _recording_runner(forge=forge, script=_answer_every_invocation(answer=DELETION_ACCEPTED))
    created = _created_project(forge=forge, namespace=TEST_GROUP, path=path)

    forge.delete_ephemeral(wrapper=runner, created=created, run_id=run_id)

    assert runner.recorded == [_deletion(namespace=TEST_GROUP, path=path)], (
        f"the teardown of {_full_path(namespace=TEST_GROUP, path=path)} sent {runner.recorded}"
    )


@pytest.mark.parametrize(
    argnames=("namespace", "path_template"),
    argvalues=(
        pytest.param(OTHER_NAMESPACE, "{prefix}{run_id}", id="another-namespace"),
        pytest.param(SUBGROUP_NAMESPACE, "{prefix}{run_id}", id="a-subgroup-of-the-test-group"),
        pytest.param(TEST_GROUP, "{run_id}", id="a-path-without-the-prefix"),
        pytest.param(TEST_GROUP, "{prefix}{other_run_id}", id="another-runs-id"),
    ),
)
def test_the_teardown_refuses_any_other_target(namespace: str, path_template: str) -> None:
    """AC-2.2 (D9 "The teardown guard"): a created record of another namespace, of a path without the prefix, or of
    another run's id is refused with ``ForgeTeardownRefusedError`` naming the refused ``<namespace>/<path>`` and this
    run's ``bestehorn-sff-test/sff-test-<run id>``; nothing is sent."""
    forge = _ephemeral()
    _require(module=forge, names=TEARDOWN_SYMBOLS)
    run_id = _run_id()
    path = path_template.format(prefix=EPHEMERAL_PREFIX, run_id=run_id, other_run_id=_run_id())
    runner = _recording_runner(forge=forge, script=_refuse_every_invocation)
    created = _created_project(forge=forge, namespace=namespace, path=path)

    with pytest.raises(expected_exception=forge.ForgeTeardownRefusedError) as refused:
        forge.delete_ephemeral(wrapper=runner, created=created, run_id=run_id)

    message = str(refused.value)
    target = _full_path(namespace=namespace, path=path)
    assert target in message, f"the refusal does not name {target}: {message}"
    own = _full_path(namespace=TEST_GROUP, path=EPHEMERAL_PREFIX + run_id)
    assert own in message, f"the refusal does not name this run's project {own}: {message}"
    assert runner.recorded == [], f"the refused teardown sent {runner.recorded}"


@settings(deadline=None, max_examples=SWEEP_EXAMPLES)
@given(listing=LISTINGS, now=SWEEP_MOMENTS)
def test_the_sweep_deletes_exactly_the_old_unscheduled_ephemeral_projects(
    listing: List[_ListedProject], now: datetime
) -> None:
    """AC-3.1, AC-3.2, AC-3.3 (D9 "The sweep"): over listings of projects of the test group or another namespace (a
    subgroup and an ``-archive`` sibling among them), with a path with the prefix or not (near misses among them),
    created either side of the one-day line, and with ``marked_for_deletion_on`` set or not (null or absent), the sweep
    lists the test group once and then sends one ``call tenant-scale#delete-a-project`` per project that has all four
    properties, and none for any other, without raising. The expected deletions come from the drawn sides, never from
    ``is_leftover`` or ``select_leftovers``."""
    forge = _ephemeral()
    _require(module=forge, names=PROPERTY_SYMBOLS)
    items = [
        _project_item(
            project_id=FIRST_LISTED_ID + index,
            namespace=drawn.namespace,
            path=drawn.path,
            created_at=now - timedelta(milliseconds=drawn.age_milliseconds),
            marked_on=drawn.marked_on,
            marked_key_listed=drawn.marked_key_listed,
        )
        for index, drawn in enumerate(listing)
    ]
    runner = _recording_runner(forge=forge, script=_sweep_script(items=items, deletion=DELETION_ACCEPTED))

    forge.sweep_leftovers(wrapper=runner, now=now)

    expected = sorted(_deletion(namespace=drawn.namespace, path=drawn.path) for drawn in listing if drawn.deleted)
    assert runner.recorded[:1] == [list(LISTING_ARGUMENTS)], f"the sweep did not list first: {runner.recorded}"
    assert sorted(runner.recorded[1:]) == expected, (
        f"the sweep at {now:%Y-%m-%dT%H:%M:%SZ} sent {runner.recorded[1:]}, not {expected}"
    )


def test_the_sweep_boundaries_and_refusals() -> None:
    """AC-3.1, AC-3.2, AC-3.3 (D9 "The sweep"): ``list_group_projects`` lists the test group and gives each item's
    ``ProjectRecord.of``; exactly a day old and a millisecond under a day are kept and a millisecond over a day is
    deleted, a scheduled leftover is sent nothing; a deletion answered with exit 1 and ``answered 404``, or with
    ``answered 400`` and "has already been marked for deletion", counts as handled, another ``400`` or a ``403`` raises
    ``ForgeCommandError``; ``delete_leftover`` of a record that is no leftover or is scheduled raises
    ``ForgeSweepRefusedError`` naming it, and sends nothing."""
    forge = _ephemeral()
    _require(module=forge, names=SWEEP_SYMBOLS)
    assert forge.LEFTOVER_AGE == ONE_DAY, f"LEFTOVER_AGE is {forge.LEFTOVER_AGE!r}, not a day (D9)"
    a_day_old = _project_item(
        project_id=FIRST_LISTED_ID,
        namespace=TEST_GROUP,
        path=f"{EPHEMERAL_PREFIX}a-day-old",
        created_at=SWEEP_NOW - ONE_DAY,
    )
    under_a_day = _project_item(
        project_id=FIRST_LISTED_ID + 1,
        namespace=TEST_GROUP,
        path=f"{EPHEMERAL_PREFIX}a-millisecond-under-a-day",
        created_at=SWEEP_NOW - ONE_DAY + ONE_MILLISECOND,
    )
    just_over = _project_item(
        project_id=FIRST_LISTED_ID + 2,
        namespace=TEST_GROUP,
        path=f"{EPHEMERAL_PREFIX}a-millisecond-over-a-day",
        created_at=SWEEP_NOW - ONE_DAY - ONE_MILLISECOND,
    )
    scheduled = _project_item(
        project_id=FIRST_LISTED_ID + 3,
        namespace=TEST_GROUP,
        path=f"{EPHEMERAL_PREFIX}scheduled",
        created_at=SWEEP_NOW - LONG_AGO,
        marked_on=MARKED_ON,
    )
    listing = [a_day_old, under_a_day, just_over, scheduled]
    records = [forge.ProjectRecord.of(item=item) for item in listing]
    just_over_record = records[2]
    just_over_path = str(just_over[FIELD_PATH_WITH_NAMESPACE])
    just_over_deletion = _deletion(namespace=TEST_GROUP, path=str(just_over[FIELD_PATH]))

    lister = _recording_runner(forge=forge, script=_sweep_script(items=listing, deletion=DELETION_ACCEPTED))
    listed = forge.list_group_projects(wrapper=lister)
    assert lister.recorded == [list(LISTING_ARGUMENTS)], f"list_group_projects sent {lister.recorded}"
    assert list(listed) == records, f"list_group_projects gave {listed}, not each item's ProjectRecord.of: {records}"
    leftovers = [forge.is_leftover(record=record, now=SWEEP_NOW) for record in records]
    assert leftovers == [False, False, True, True], (
        f"is_leftover judged a day old, a millisecond under, a millisecond over and the scheduled one as {leftovers}"
    )
    selected = list(forge.select_leftovers(records=records, now=SWEEP_NOW))
    assert selected == [just_over_record, records[3]], f"select_leftovers kept {selected} of {records}"

    swept = _recording_runner(forge=forge, script=_sweep_script(items=listing, deletion=DELETION_ACCEPTED))
    forge.sweep_leftovers(wrapper=swept, now=SWEEP_NOW)
    assert swept.recorded == [list(LISTING_ARGUMENTS), just_over_deletion], f"the sweep sent {swept.recorded}"

    for handled in (
        _api_failure(full_path=just_over_path, status=NOT_FOUND_STATUS, message=NOT_FOUND_MESSAGE),
        _api_failure(full_path=just_over_path, status=BAD_REQUEST_STATUS, message=ALREADY_MARKED_MESSAGE),
    ):
        gone = _recording_runner(forge=forge, script=_sweep_script(items=[just_over], deletion=handled))
        forge.sweep_leftovers(wrapper=gone, now=SWEEP_NOW)
        assert gone.recorded == [list(LISTING_ARGUMENTS), just_over_deletion], (
            f"the sweep answered {handled.stderr!r} sent {gone.recorded}"
        )

    for failure in (
        _api_failure(full_path=just_over_path, status=BAD_REQUEST_STATUS, message=OTHER_BAD_REQUEST_MESSAGE),
        _api_failure(full_path=just_over_path, status=FORBIDDEN_STATUS, message=FORBIDDEN_MESSAGE),
    ):
        refused_by_gitlab = _recording_runner(forge=forge, script=_answer_every_invocation(answer=failure))
        with pytest.raises(expected_exception=forge.ForgeCommandError):
            forge.delete_leftover(wrapper=refused_by_gitlab, record=just_over_record, now=SWEEP_NOW)
        assert refused_by_gitlab.recorded == [just_over_deletion], (
            f"the deletion answered {failure.stderr!r} sent {refused_by_gitlab.recorded}"
        )

    for no_leftover in (
        a_day_old,
        under_a_day,
        scheduled,
        _project_item(
            project_id=FIRST_LISTED_ID + 4,
            namespace=OTHER_NAMESPACE,
            path=f"{EPHEMERAL_PREFIX}another-namespace",
            created_at=SWEEP_NOW - LONG_AGO,
        ),
        _project_item(
            project_id=FIRST_LISTED_ID + 5,
            namespace=SUBGROUP_NAMESPACE,
            path=f"{EPHEMERAL_PREFIX}a-subgroup",
            created_at=SWEEP_NOW - LONG_AGO,
        ),
        _project_item(
            project_id=FIRST_LISTED_ID + 6, namespace=TEST_GROUP, path=UNPREFIXED_PATH, created_at=SWEEP_NOW - LONG_AGO
        ),
    ):
        runner = _recording_runner(forge=forge, script=_refuse_every_invocation)
        with pytest.raises(expected_exception=forge.ForgeSweepRefusedError) as refused:
            forge.delete_leftover(wrapper=runner, record=forge.ProjectRecord.of(item=no_leftover), now=SWEEP_NOW)
        full_path = str(no_leftover[FIELD_PATH_WITH_NAMESPACE])
        assert full_path in str(refused.value), f"the refusal does not name {full_path}: {refused.value}"
        assert runner.recorded == [], f"the refused deletion of {full_path} sent {runner.recorded}"
