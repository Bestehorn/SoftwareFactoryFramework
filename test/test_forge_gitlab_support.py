"""The GitLab forge suite's support logic (S): ``test/forge_gitlab/ephemeral.py`` exercised in the default collection.

``test/forge_gitlab/`` is the GitLab forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge_gitlab``) against gitlab.com (issue #11, design D1). What its support module decides without the forge is
proven here: the refusal of a distributed run, naming that command (D1); the run id and the project path it gives,
which the product GitLab wrapper's guard accepts (D4, D2); the per-command credential helper git authenticates to
gitlab.com with, ``CLONE_GIT_HELPER`` (D3, D10); where the GitLab test credential file is found, and the CI step's write
of it, by ``write_test_credential`` and by ``test/forge_gitlab/write_credential.py`` ``main`` (D8); the marker on every
product-wrapper invocation and the bytes of its answer (D10); the teardown guard and the leftover sweep (D9); and the
provision around them: its steps in order, the refusal of a project created other than private, no deletion without a
creation, the test credential's refusals, the token written only to the clone, and a clone commit holding neither of
the clone's credential files (D3 "The clone", D8, D9). Only local git runs (``git init``, ``git commit``, ``git
worktree add``, ``git rev-parse``, ``git credential fill``, ``git remote add``, ``git config``, ``git add``, ``git
ls-files``), in checkouts under pytest's ``tmp_path``, and every ``git credential fill`` is given ``-c
credential.helper=`` first, so no helper a configuration file names is asked. The wrapper runner's ``subprocess.run``
is replaced by a recorder, and the teardown, the sweep and a provision are given ``RecordingWrapperRunner``, a
``WrapperRunner`` that records each argv and answers it from the test's script. A provision is also given
``ScriptedGitRunner``, a ``GitRunner`` that records each argv, hands ``init`` and ``remote`` to real local git in the
clone and answers the rest (``fetch``, ``checkout``, the seed's reads) from the script without a process. No test opens
a connection or needs a test credential file (UB-1).

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

import builtins
import importlib.util
import io
import json
import locale
import logging
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------------------------------------------------
# Provisioning (D3 "The clone", D8, D9 steps 1 to 8)
# ---------------------------------------------------------------------------------------------------------------------

# The symbols the provisioning tests need of ``ephemeral.py`` (D8, D9, D10).
GIT_RUNNER_SYMBOLS = ("GitRunner", "Invocation")
PROVISION_SYMBOLS = (
    *RUNNER_SYMBOLS,
    *GIT_RUNNER_SYMBOLS,
    "ForgeSetupError",
    "ForgeCommandError",
    "EphemeralProject",
    "provision",
)
NO_CREATION_SYMBOLS = (*PROVISION_SYMBOLS, "delete_ephemeral")
READING_SYMBOLS = (*PROVISION_SYMBOLS, "read_test_token")
WRITTEN_SYMBOLS = (*PROVISION_SYMBOLS, "CLONE_CONFIG_FILE", "CLONE_GIT_TOKEN_FILE")
CLONE_SYMBOLS = (
    "CLONE_CONFIG_FILE",
    "CLONE_GIT_TOKEN_FILE",
    "CLONE_GIT_HELPER",
    "SubprocessGitRunner",
    "prepare_clone",
)

# D9: the test's tree. The workspace stands for the session fixture's ``tempfile.mkdtemp`` directory; the clone is
# ``<workspace>/clone``, and its git files are read where git writes them.
CHECKOUT_NAME = "checkout"
WORKSPACE_NAME = "workspace"
CLONE_NAME = "clone"
GIT_CONFIG_FILE = Path(GIT_DIRECTORY) / "config"
GIT_EXCLUDE_FILE = Path(GIT_DIRECTORY) / "info" / "exclude"
ORIGIN_URL_KEY = "remote.origin.url"
#: D3: the clone's ``origin``, the test group's project without userinfo, so ``.git/config`` holds no token.
ORIGIN_URL = "https://gitlab.com/{full_path}.git"
#: D8, UB-2: the product GitLab wrapper's credential file, relative to a working tree: the clone's, which a provision
#: writes, and the checkout's, a sentinel no provision opens.
CLONE_CONFIG_FILE = Path("config") / "gitlab.json"
#: D8: the line the clone's ``.git/info/exclude`` gains, so no commit of the clone holds its ``config/gitlab.json``.
EXCLUDED_CONFIG = "config/"
# AC-1.3, D8: the keys of a ``config/gitlab.json`` (``gitlab_api/transport.py``) and the host the clone's names; the
# UB-2 sentinel also holds a ``token_type``.
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"
FIELD_TOKEN_TYPE = "token_type"
CLONE_CONFIG_KEYS = (FIELD_HOSTNAME, FIELD_PROJECT_ID, FIELD_TOKEN)
GITLAB_HOSTNAME = "gitlab.com"
SENTINEL_LABEL = "sentinel"
SENTINEL_TOKEN_TYPE = "private"
#: The GitHub forge suite's test credential, beside the GitLab one in every scripted checkout: a provision that reads it
#: (``find_test_credential`` without this suite's ``credential_file``) writes its token, not the test token.
DECOY_LABEL = "github-decoy"

# D9 steps 5 and 6: the group read and the creation, and what GitLab answers them with (docs.gitlab.com/api/groups/,
# "Get a single group"; docs.gitlab.com/api/projects/, "Create a project"). The default branch is not ``main``, so a
# checkout of a branch the answer did not name is seen.
GROUP_READ_OPERATION = "tenant-scale#retrieve-a-group"
QUERY_OPTION = "--query"
GROUP_READ_ARGUMENTS = (
    CALL_SUBCOMMAND,
    GROUP_READ_OPERATION,
    PATH_OPTION,
    f"{ID_PARAMETER}{PARAMETER_ASSIGNMENT}{TEST_GROUP}",
    QUERY_OPTION,
    "with_projects=false",
)
TEST_GROUP_ID = 12345678
CREATE_OPERATION = "tenant-scale#create-a-project"
RAW_FIELD_OPTION = "-f"
TYPED_FIELD_OPTION = "-F"
NAME_FIELD = "name="
PATH_FIELD = "path="
#: D9 step 6: the creation's attributes beside its name and path, as ``(option, attribute)``.
CREATION_SETTINGS = (
    (TYPED_FIELD_OPTION, f"namespace_id={TEST_GROUP_ID}"),
    (RAW_FIELD_OPTION, "visibility=private"),
    (TYPED_FIELD_OPTION, "initialize_with_readme=true"),
    (TYPED_FIELD_OPTION, "auto_devops_enabled=false"),
)
FIELD_VISIBILITY = "visibility"
FIELD_DEFAULT_BRANCH = "default_branch"
PRIVATE_VISIBILITY = "private"
SEED_BRANCH = "trunk"
EMPTY_LISTING = _Answer(returncode=0, stdout=json.dumps(obj=[]) + LINE_END)
GROUP_ANSWER = _Answer(
    returncode=0,
    stdout=json.dumps(
        obj={FIELD_ID: TEST_GROUP_ID, FIELD_NAME: TEST_GROUP, FIELD_PATH: TEST_GROUP, FIELD_FULL_PATH: TEST_GROUP},
        indent=2,
    )
    + LINE_END,
)
#: D9 step 6: the product GitLab wrapper's answer to a creation GitLab refused (a taken path, D4).
CREATION_FAILURE = _Answer(
    returncode=WRAPPER_API_FAILURE,
    stderr=(
        "POST https://gitlab.com/api/v4/projects answered 400: Bad Request"
        + LINE_END
        + json.dumps(obj={FIELD_MESSAGE: {FIELD_PATH: ["has already been taken"]}})
        + LINE_END
    ),
)
DELETION_FAILURE = _api_failure(
    full_path=f"{TEST_GROUP}/{EPHEMERAL_PREFIX}this-run", status=FORBIDDEN_STATUS, message=FORBIDDEN_MESSAGE
)

# D3, D9 step 7: the git commands a provision runs, and what the scripted git answers them with.
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
HEAD = "HEAD"
NAME_ONLY_OPTION = "--name-only"
#: The options of the seed's listing, ``git ls-tree [-r] --name-only HEAD`` (#10's ``fetch_seed``).
LS_TREE_OPTIONS = ("-r", NAME_ONLY_OPTION)
SEED_SHA = "5eed" * 10
SEED_TREE_SHA = "7ee5" * 10
#: ``rev-parse``'s answer per revision D9 step 7 asks for.
SEED_REVISIONS = {HEAD: SEED_SHA, "HEAD^{tree}": SEED_TREE_SHA}
SEED_FILE = "README.md"
SEED_TREE = (SEED_FILE,)
#: AC-1.3: a seed whose root holds GitLab's default CI configuration file, which a push would run.
GITLAB_CI_SEED_TREE = (SEED_FILE, ".gitlab-ci.yml")
#: D4: a run id as #10's ``new_run_id`` makes it.
RUN_ID_PATTERN = re.compile(r"[0-9]{14}-[0-9a-f]{32}")

# AC-1.1: a provision's timeline, as the steps of D9 it shows.
WRAPPER_RUNNER = "wrapper"
GIT_RUNNER = "git"
BODY_RUNNER = "body"
STEP_INIT = "git init"
STEP_REMOTE = "git remote add origin <this run's URL>"
STEP_LISTING = "the listing"
STEP_GROUP_READ = "the group read"
STEP_CREATION = "the creation of this run's path in the group, private, seeded, without Auto DevOps"
STEP_FETCH = "the authenticated git fetch origin"
STEP_CHECKOUT = "git checkout -B <default branch> --track origin/<default branch>"
STEP_READ = "the seed's reads"
STEP_BODY = "the body"
STEP_DELETION = "the deletion of this run's project"
CREATED_STEPS = (STEP_INIT, STEP_REMOTE, STEP_LISTING, STEP_GROUP_READ, STEP_CREATION)
PREPARED_STEPS = (*CREATED_STEPS, STEP_FETCH, STEP_CHECKOUT, STEP_READ)

# AC-6.2: the bad test credential files, one per refusal of D8 "Reading".
MISSING_CREDENTIAL = "missing"
EMPTY_CREDENTIAL = "empty"
LONE_LINE_END_CREDENTIAL = "a-lone-line-end"
PLACEHOLDER_CREDENTIAL = "the-placeholder"
SPACE_CREDENTIAL = "a-token-holding-a-space"
NON_ASCII_CREDENTIAL = "a-non-ascii-character"
TWO_LINES_CREDENTIAL = "two-lines"
BAD_CREDENTIAL_KINDS = (
    MISSING_CREDENTIAL,
    EMPTY_CREDENTIAL,
    LONE_LINE_END_CREDENTIAL,
    PLACEHOLDER_CREDENTIAL,
    SPACE_CREDENTIAL,
    NON_ASCII_CREDENTIAL,
    TWO_LINES_CREDENTIAL,
)
#: AC-6.2: a text starting with ``PASTE_``, the product's placeholder marker.
PLACEHOLDER_TOKEN = "PASTE_TOKEN"
NON_ASCII_CHARACTER = "é"
SPACE = " "
#: D8 "Reading": the final line ends a token is read without.
ACCEPTED_LINE_ENDS = (WINDOWS_LINE_END, LINE_END)

# UB-2: the calls a read or a write of a file goes through, replaced by a recorder during a provision.
OPEN_TARGETS: Tuple[Tuple[ModuleType, str], ...] = ((builtins, "open"), (io, "open"), (os, "open"))


class _BodyFailure(Exception):
    """What a test body raises, to show that the teardown runs whatever the body does (AC-1.4)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class _CloneView:
    """What a wrapper invocation in the clone meets: the ``hostname`` and ``project_id`` of the clone's
    ``config/gitlab.json``, read into those two values alone, and the ``origin`` its ``.git/config`` names; ``None``
    where a file is absent or names none."""

    hostname: Any
    project_id: Any
    origin: Optional[str]


@dataclass(frozen=True)
class _Event:
    """One entry of a provision's timeline: a wrapper or git invocation, or the body's entry. At a wrapper invocation,
    ``view`` is what the clone held then (``_CloneView``)."""

    runner: str
    arguments: Tuple[str, ...] = ()
    authenticated: bool = False
    view: Optional[_CloneView] = None


def _origin_url(*, path: str) -> str:
    """D3's origin URL of the test group's project ``path``."""
    return ORIGIN_URL.format(full_path=_full_path(namespace=TEST_GROUP, path=path))


def _creation_pairs(*, arguments: Sequence[str]) -> List[Tuple[str, str]]:
    """The ``(option, attribute)`` pairs after a creation's ``call tenant-scale#create-a-project``, sorted; a lone
    trailing part is a pair with an empty attribute."""
    rest = [str(part) for part in arguments[2:]]
    if len(rest) % 2:
        rest.append("")
    return sorted(zip(rest[::2], rest[1::2]))


def _expected_creation_pairs(*, path: str) -> List[Tuple[str, str]]:
    """D9 step 6's ``-f name=<path> -f path=<path> -F namespace_id=<group id> -f visibility=private -F
    initialize_with_readme=true -F auto_devops_enabled=false``, as sorted ``(option, attribute)`` pairs."""
    return sorted([(RAW_FIELD_OPTION, NAME_FIELD + path), (RAW_FIELD_OPTION, PATH_FIELD + path), *CREATION_SETTINGS])


def _is_creation(*, arguments: Sequence[str], path: str) -> bool:
    """Whether ``arguments`` is D9 step 6's creation of ``path`` in the group, holding exactly its attributes."""
    return list(arguments[:2]) == [CALL_SUBCOMMAND, CREATE_OPERATION] and _creation_pairs(
        arguments=arguments
    ) == _expected_creation_pairs(path=path)


def _requested_path(*, arguments: Sequence[str]) -> str:
    """The project path a creation asks for with ``-f path=<path>``; a creation naming none fails the test."""
    for option, value in zip(arguments, arguments[1:]):
        if option == RAW_FIELD_OPTION and value.startswith(PATH_FIELD):
            return value[len(PATH_FIELD) :]
    raise AssertionError(f"the creation names no path with {RAW_FIELD_OPTION} {PATH_FIELD}<path>: {arguments}")


def _created_item(*, path: str, visibility: str) -> Dict[str, Any]:
    """The project the creation of ``path`` answers with, as GitLab answers it: ``CREATED_PROJECT_ID``, the test group
    its namespace, ``visibility`` as given, ``SEED_BRANCH`` its default branch."""
    return {
        FIELD_ID: CREATED_PROJECT_ID,
        FIELD_NAME: path,
        FIELD_PATH: path,
        FIELD_PATH_WITH_NAMESPACE: _full_path(namespace=TEST_GROUP, path=path),
        FIELD_NAMESPACE: {
            FIELD_ID: TEST_GROUP_ID,
            FIELD_PATH: TEST_GROUP,
            FIELD_FULL_PATH: TEST_GROUP,
            FIELD_KIND: GROUP_KIND,
        },
        FIELD_VISIBILITY: visibility,
        FIELD_DEFAULT_BRANCH: SEED_BRANCH,
    }


def _clone_config(*, clone: Path) -> Dict[str, Any]:
    """The JSON object of the clone's ``config/gitlab.json``; empty while the file is absent or holds no JSON object.
    It holds the token: a caller keeps only what it compares, never the mapping."""
    config = clone / CLONE_CONFIG_FILE
    if not config.is_file():
        return {}
    try:
        loaded = json.loads(s=config.read_text(encoding=TEXT_ENCODING))
    except ValueError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _origin_of(*, clone: Path) -> Optional[str]:
    """The ``origin`` URL the clone's ``.git/config`` names, read by local git from that file alone; ``None`` while the
    file is absent or names none."""
    config = clone / GIT_CONFIG_FILE
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


def _clone_view(*, clone: Path) -> _CloneView:
    """What a wrapper invocation in ``clone`` meets now (``_CloneView``)."""
    config = _clone_config(clone=clone)
    return _CloneView(
        hostname=config.get(FIELD_HOSTNAME), project_id=config.get(FIELD_PROJECT_ID), origin=_origin_of(clone=clone)
    )


def _revisions(*, arguments: Sequence[str]) -> _Answer:
    """``rev-parse``'s answer: one line per revision asked for, options aside; a revision D9 step 7 does not ask for
    fails the test."""
    asked = [argument for argument in arguments[1:] if not argument.startswith(OPTION_PREFIX)]
    unknown = [revision for revision in asked if revision not in SEED_REVISIONS]
    assert asked and not unknown, f"the provision asked rev-parse for revisions the test scripted none for: {arguments}"
    return _Answer(returncode=GIT_EXIT_OK, stdout="".join(SEED_REVISIONS[revision] + LINE_END for revision in asked))


def _is_seed_listing(*, arguments: Sequence[str]) -> bool:
    """Whether ``arguments`` is the seed's listing, ``ls-tree``, ``--name-only`` and at most ``-r``, then ``HEAD``."""
    options = list(arguments[1:-1])
    return (
        list(arguments[:1]) == [GIT_LS_TREE]
        and list(arguments[-1:]) == [HEAD]
        and NAME_ONLY_OPTION in options
        and set(options) <= set(LS_TREE_OPTIONS)
    )


def _local_git_step(*, event: _Event) -> Optional[str]:
    """The step of an unauthenticated git invocation that names no project: ``git init`` or one of the seed's reads;
    ``None`` for any other event."""
    if event.runner != GIT_RUNNER or event.authenticated:
        return None
    if event.arguments[:1] == (GIT_INIT,):
        return STEP_INIT
    if event.arguments[:1] == (GIT_REV_PARSE,) or _is_seed_listing(arguments=event.arguments):
        return STEP_READ
    return None


class _ProvisionScript:
    """The forge and the git one provision meets, scripted, noting every invocation and the body's entry in one
    ``timeline``, in order.

    The wrapper answers the listing with no project, the group read with the test group and ``TEST_GROUP_ID``, the
    creation with the project it names, ``visibility`` as given (``_created_item``), or with ``creation`` when one is
    given, and the deletion with ``deletion``; at each invocation it notes what the clone holds (``_CloneView``). The
    git hands ``init`` and ``remote`` to real local git in the clone, which must exist by then, and answers ``fetch``
    and ``checkout`` with success, ``rev-parse`` from ``SEED_REVISIONS`` and the seed's listing with ``seed_tree``,
    starting no process. Any other invocation fails the test.
    """

    def __init__(
        self,
        *,
        clone: Path,
        seed_tree: Sequence[str],
        creation: Optional[_Answer],
        deletion: _Answer,
        visibility: str = PRIVATE_VISIBILITY,
    ) -> None:
        self.clone = clone
        self.seed_tree = tuple(seed_tree)
        self.creation = creation
        self.deletion = deletion
        self.visibility = visibility
        self.timeline: List[_Event] = []
        #: The project path the creation asked for, once it was sent.
        self.path: Optional[str] = None

    def wrapper(self, *, arguments: List[str]) -> _Answer:
        """The script of the provision's ``RecordingWrapperRunner``."""
        self.timeline.append(
            _Event(runner=WRAPPER_RUNNER, arguments=tuple(arguments), view=_clone_view(clone=self.clone))
        )
        if arguments == list(LISTING_ARGUMENTS):
            return EMPTY_LISTING
        if arguments == list(GROUP_READ_ARGUMENTS):
            return GROUP_ANSWER
        if arguments[:2] == [CALL_SUBCOMMAND, CREATE_OPERATION]:
            self.path = _requested_path(arguments=arguments)
            if self.creation is not None:
                return self.creation
            created = _created_item(path=self.path, visibility=self.visibility)
            return _Answer(returncode=0, stdout=json.dumps(obj=created, indent=2) + LINE_END)
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
        if _is_seed_listing(arguments=arguments):
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
        local = _local_git_step(event=event)
        if local is not None:
            return local
        path = self.path or ""
        if event.runner == WRAPPER_RUNNER and _is_creation(arguments=event.arguments, path=path):
            return STEP_CREATION
        steps = {
            (GIT_RUNNER, (*REMOTE_ADD, _origin_url(path=path)), False): STEP_REMOTE,
            (WRAPPER_RUNNER, LISTING_ARGUMENTS, False): STEP_LISTING,
            (WRAPPER_RUNNER, GROUP_READ_ARGUMENTS, False): STEP_GROUP_READ,
            (GIT_RUNNER, FETCH_ARGUMENTS, True): STEP_FETCH,
            (GIT_RUNNER, CHECKOUT_ARGUMENTS, False): STEP_CHECKOUT,
            (WRAPPER_RUNNER, tuple(_deletion(namespace=TEST_GROUP, path=path)), False): STEP_DELETION,
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
    ``token``, the GitHub suite's test credential file with another token, and a sentinel ``config/gitlab.json``
    (UB-2); the workspace; and the two doubles, which note in ``script``'s timeline."""

    root: Path
    checkout: Path
    workspace: Path
    #: Kept out of the ``repr``, so that pytest's introspection of a failed assertion never prints the token.
    token: str = field(repr=False)
    test_credential: Path
    sentinel: Path
    script: _ProvisionScript
    wrapper: Any
    git: Any

    @property
    def clone(self) -> Path:
        """D9 step 3's ``<workspace>/clone``."""
        return self.workspace / CLONE_NAME


def _write_sentinel(*, checkout: Path) -> Path:
    """UB-2: the checkout's own ``config/gitlab.json``, naming another project with another token and a
    ``token_type``; returns its path."""
    sentinel = checkout / CLONE_CONFIG_FILE
    sentinel.parent.mkdir(parents=True)
    content = {
        FIELD_HOSTNAME: GITLAB_HOSTNAME,
        FIELD_PROJECT_ID: _full_path(namespace=OTHER_NAMESPACE, path=UNPREFIXED_PATH),
        FIELD_TOKEN: _new_token(label=SENTINEL_LABEL),
        FIELD_TOKEN_TYPE: SENTINEL_TOKEN_TYPE,
    }
    sentinel.write_bytes(data=(json.dumps(obj=content, indent=2) + LINE_END).encode(encoding=TEXT_ENCODING))
    return sentinel


def _provisioning(
    *,
    forge: ModuleType,
    tmp_path: Path,
    seed_tree: Sequence[str] = SEED_TREE,
    creation: Optional[_Answer] = None,
    deletion: _Answer = DELETION_ACCEPTED,
    visibility: str = PRIVATE_VISIBILITY,
) -> _Provisioning:
    """A scripted provision's tree under ``tmp_path`` and its two doubles, sharing one ``_ProvisionScript``."""
    checkout = tmp_path / CHECKOUT_NAME
    _init_checkout(path=checkout)
    token = _new_token(label="test")
    test_credential = _write_credential(directory=checkout, name=TEST_CREDENTIAL_NAME, token=token)
    _write_credential(directory=checkout, name=GITHUB_TEST_CREDENTIAL_NAME, token=_new_token(label=DECOY_LABEL))
    sentinel = _write_sentinel(checkout=checkout)
    workspace = tmp_path / WORKSPACE_NAME
    workspace.mkdir()
    script = _ProvisionScript(
        clone=workspace / CLONE_NAME,
        seed_tree=seed_tree,
        creation=creation,
        deletion=deletion,
        visibility=visibility,
    )
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
    """What a provision's body found on entry: the yielded project, the moment, whether the clone exists, the keys of
    the clone's ``config/gitlab.json`` and its ``hostname`` and ``project_id``, the lines of its ``.git/info/exclude``,
    and the files of the test's tree that held the token, the sentinel aside (its content is compared on its own).
    Every comparison with the token is kept as a bool, so that no failed assertion prints a file's bytes."""

    project: Any
    representation_holds_the_token: bool
    at: datetime
    clone_is_directory: bool
    config_keys: Tuple[str, ...]
    config_target: Tuple[Any, Any]
    config_token_is_the_test_token: bool
    git_token_file_is_the_test_token: bool
    git_config_holds_the_token: bool
    exclude_lines: Tuple[str, ...]
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


def _bytes_of(*, path: Path) -> Optional[bytes]:
    """The bytes of ``path``; ``None`` while it is no file."""
    return path.read_bytes() if path.is_file() else None


def _enter(*, project: Any, setup: _Provisioning) -> _Entered:
    """What the body of a provision over ``setup`` finds on entry (``_Entered``)."""
    clone = setup.clone
    config = _clone_config(clone=clone)
    exclude = _text_of(path=clone / GIT_EXCLUDE_FILE)
    git_token = _bytes_of(path=clone / CLONE_GIT_TOKEN_FILE)
    return _Entered(
        project=project,
        representation_holds_the_token=setup.token in repr(project),
        at=datetime.now(tz=timezone.utc),
        clone_is_directory=clone.is_dir(),
        config_keys=tuple(sorted(config)),
        config_target=(config.get(FIELD_HOSTNAME), config.get(FIELD_PROJECT_ID)),
        config_token_is_the_test_token=config.get(FIELD_TOKEN) == setup.token,
        git_token_file_is_the_test_token=git_token == (setup.token + LINE_END).encode(encoding=TEXT_ENCODING),
        git_config_holds_the_token=setup.token in _text_of(path=clone / GIT_CONFIG_FILE),
        exclude_lines=tuple(line.strip() for line in exclude.splitlines()),
        holders=tuple(_holders(setup=setup)),
    )


def _provide(*, forge: ModuleType, setup: _Provisioning, entered: List[_Entered], body_raises: bool) -> None:
    """One ``provision`` over ``setup``. Its body notes what it found in ``entered`` and its entry in the timeline, then
    returns or raises ``_BodyFailure``; it asserts nothing, so a teardown error cannot hide a failed assertion."""
    with forge.provision(
        checkout=setup.checkout, workspace=setup.workspace, wrapper=setup.wrapper, git=setup.git
    ) as project:
        entered.append(_enter(project=project, setup=setup))
        setup.script.enter()
        if body_raises:
            raise _BodyFailure(message="the test body raised")


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
        _ProvisionCase(seed_tree=SEED_TREE, body_raises=False, deletion=DELETION_ACCEPTED, yields=True),
        id="the-body-returns",
    ),
    pytest.param(
        _ProvisionCase(seed_tree=SEED_TREE, body_raises=True, deletion=DELETION_ACCEPTED, yields=True),
        id="the-body-raises",
    ),
    pytest.param(
        _ProvisionCase(
            seed_tree=GITLAB_CI_SEED_TREE,
            body_raises=False,
            deletion=DELETION_ACCEPTED,
            yields=False,
            error="ForgeSetupError",
        ),
        id="a-gitlab-ci-file-in-the-seed",
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
    """The ``call tenant-scale#delete-a-project`` invocations the provision's wrapper recorded."""
    return [argv for argv in setup.wrapper.recorded if argv[:2] == [CALL_SUBCOMMAND, DELETE_OPERATION]]


def _creations(*, setup: _Provisioning) -> List[List[str]]:
    """The ``call tenant-scale#create-a-project`` invocations the provision's wrapper recorded."""
    return [argv for argv in setup.wrapper.recorded if argv[:2] == [CALL_SUBCOMMAND, CREATE_OPERATION]]


def _assert_yielded(*, forge: ModuleType, entered: _Entered, setup: _Provisioning, started: datetime) -> None:
    """AC-1.1, AC-1.3 (D9): the yielded ``EphemeralProject`` names this run's project as the creation answered it, the
    seed the git reads answered, the time of the sweep, the existing clone, and the runners it was given."""
    project = entered.project
    assert isinstance(project, forge.EphemeralProject), f"provision yielded {type(project)}, no EphemeralProject"
    path = str(setup.script.path)
    expected = (TEST_GROUP, path, _full_path(namespace=TEST_GROUP, path=path), CREATED_PROJECT_ID, SEED_BRANCH)
    named = (project.group, project.path, project.full_path, project.project_id, project.default_branch)
    assert named == expected, f"the yielded project is {named}, not the creation's answer {expected}"
    assert project.path == EPHEMERAL_PREFIX + project.run_id, f"the run id {project.run_id!r} is not the path's"
    assert (project.seed_sha, project.seed_tree_sha) == (SEED_SHA, SEED_TREE_SHA), (
        f"the yielded seed is {project.seed_sha} {project.seed_tree_sha}, not the git reads' answer"
    )
    swept_at = project.swept_at
    assert isinstance(swept_at, datetime) and swept_at.utcoffset() == timedelta(0), f"swept_at is {swept_at!r}"
    assert started.replace(microsecond=0) <= swept_at <= entered.at, f"swept_at {swept_at} is not this run's sweep"
    assert entered.clone_is_directory and Path(project.clone).resolve() == setup.clone.resolve(), (
        f"the yielded clone is {project.clone}, not the existing {setup.clone}"
    )
    assert project.wrapper is setup.wrapper and project.git is setup.git, "the yielded runners are not the given"


@pytest.mark.parametrize(argnames="case", argvalues=PROVISION_CASES)
def test_provisioning_runs_in_order(tmp_path: Path, case: _ProvisionCase) -> None:
    """AC-1.1, AC-1.3, AC-1.4 (D3 "The clone", D9): one provision runs ``git init`` in the created
    ``<workspace>/clone`` and adds D3's origin, lists the test group, reads the group, sends exactly one creation of
    ``sff-test-<run id>`` holding ``-F namespace_id=<the group's id>``, ``-f visibility=private``, ``-F
    initialize_with_readme=true`` and ``-F auto_devops_enabled=false``, fetches authenticated and checks the answered
    default branch out, then reads the seed; at every wrapper invocation the clone's ``config/gitlab.json`` names
    gitlab.com and this run's project and its origin is this run's project, so every invocation in the clone targets
    it. Whether the body returns or raises, after the context exactly one deletion of this run's project is recorded
    and the workspace no longer exists; a seed holding ``.gitlab-ci.yml`` raises ``ForgeSetupError`` before the yield
    and the deletion is still sent; a deletion answering exit 1 raises ``ForgeCommandError`` and the workspace is still
    removed."""
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
    path = str(setup.script.path)
    assert path.startswith(EPHEMERAL_PREFIX) and RUN_ID_PATTERN.fullmatch(string=path[len(EPHEMERAL_PREFIX) :]), (
        f"the creation asked for {path!r}, not sff-test-<run id> (D4)"
    )
    creations = _creations(setup=setup)
    expected_pairs = _expected_creation_pairs(path=path)
    assert [_creation_pairs(arguments=argv) for argv in creations] == [expected_pairs], (
        f"the provision sent the creations {creations}, not one holding exactly {expected_pairs}"
    )
    expected_view = _CloneView(
        hostname=GITLAB_HOSTNAME, project_id=_full_path(namespace=TEST_GROUP, path=path), origin=_origin_url(path=path)
    )
    views = [event.view for event in setup.script.timeline if event.runner == WRAPPER_RUNNER]
    assert views and all(view == expected_view for view in views), (
        f"the wrapper ran where the clone held {views}, not {expected_view}"
    )
    assert _deletions(setup=setup) == [_deletion(namespace=TEST_GROUP, path=path)], (
        f"the provision sent the deletions {_deletions(setup=setup)}"
    )
    assert not setup.workspace.exists(), f"the workspace {setup.workspace} outlived the provision"
    assert len(entered) == (1 if case.yields else 0), f"the body was entered {len(entered)} times"
    if case.yields:
        _assert_yielded(forge=forge, entered=entered[0], setup=setup, started=started)


@pytest.mark.parametrize(
    argnames="visibility", argvalues=(pytest.param("internal", id="internal"), pytest.param("public", id="public"))
)
def test_a_project_created_other_than_private_is_refused_and_deleted(tmp_path: Path, visibility: str) -> None:
    """AC-1.1, AC-1.4 (D9 steps 6 and 8): a creation answered with ``visibility`` ``internal`` or ``public`` makes
    ``provision`` raise ``ForgeSetupError`` before the seed is fetched and without entering the body; the teardown still
    sends exactly one ``call tenant-scale#delete-a-project`` of the project the creation answered with, and the
    workspace no longer exists."""
    forge = _ephemeral()
    _require(module=forge, names=PROVISION_SYMBOLS)
    setup = _provisioning(forge=forge, tmp_path=tmp_path, visibility=visibility)
    entered: List[_Entered] = []

    with pytest.raises(expected_exception=forge.ForgeSetupError):
        _provide(forge=forge, setup=setup, entered=entered, body_raises=False)

    expected_steps = [*CREATED_STEPS, STEP_DELETION]
    assert setup.script.steps() == expected_steps, f"the provision ran {setup.script.steps()}, not {expected_steps}"
    path = str(setup.script.path)
    assert _deletions(setup=setup) == [_deletion(namespace=TEST_GROUP, path=path)], (
        f"the provision of a project created {visibility} sent the deletions {_deletions(setup=setup)}"
    )
    assert entered == [], f"the provision yielded a project created {visibility}"
    assert not setup.workspace.exists(), f"the workspace {setup.workspace} outlived the provision"


def test_no_creation_no_deletion(tmp_path: Path) -> None:
    """AC-2.3 (D9): ``delete_ephemeral`` given ``created=None`` sends nothing; a provision whose creation answers exit
    1 raises ``ForgeCommandError`` without entering the body, sends no ``call tenant-scale#delete-a-project``, and
    removes the workspace."""
    forge = _ephemeral()
    _require(module=forge, names=NO_CREATION_SYMBOLS)
    untouched = _recording_runner(forge=forge, script=_refuse_every_invocation)
    assert forge.delete_ephemeral(wrapper=untouched, created=None, run_id=_run_id()) is None
    assert untouched.recorded == [], f"the teardown of no creation sent {untouched.recorded}"

    setup = _provisioning(forge=forge, tmp_path=tmp_path, creation=CREATION_FAILURE)
    entered: List[_Entered] = []
    with pytest.raises(expected_exception=forge.ForgeCommandError):
        _provide(forge=forge, setup=setup, entered=entered, body_raises=False)

    expected_steps = list(CREATED_STEPS)
    assert setup.script.steps() == expected_steps, f"the provision ran {setup.script.steps()}, not {expected_steps}"
    assert _deletions(setup=setup) == [], f"the provision whose creation failed sent {_deletions(setup=setup)}"
    assert entered == [], "the provision yielded though its creation failed"
    assert not setup.workspace.exists(), f"the workspace {setup.workspace} outlived the provision"


@dataclass(frozen=True)
class _BadCredential:
    """A bad test credential file: its bytes (``None``: no file) and the parts of its text a refusal must not hold."""

    data: Optional[bytes]
    parts: Tuple[str, ...]


def _bad_credential(*, kind: str) -> _BadCredential:
    """The bad test credential file of ``kind``, each token in it fresh."""
    if kind == MISSING_CREDENTIAL:
        return _BadCredential(data=None, parts=())
    first = _new_token(label="first")
    second = _new_token(label="second")
    texts: Dict[str, Tuple[str, Tuple[str, ...]]] = {
        EMPTY_CREDENTIAL: ("", ()),
        LONE_LINE_END_CREDENTIAL: (LINE_END, ()),
        PLACEHOLDER_CREDENTIAL: (PLACEHOLDER_TOKEN + LINE_END, (PLACEHOLDER_TOKEN,)),
        SPACE_CREDENTIAL: (first + SPACE + second + LINE_END, (first, second)),
        NON_ASCII_CREDENTIAL: (first + NON_ASCII_CHARACTER + second + LINE_END, (first, second)),
        TWO_LINES_CREDENTIAL: (first + LINE_END + second + LINE_END, (first, second)),
    }
    text, parts = texts[kind]
    return _BadCredential(data=text.encode(encoding=TEXT_ENCODING), parts=parts)


def _assert_a_final_line_end_is_read_away(*, forge: ModuleType, directory: Path) -> None:
    """AC-6.2 (D8 "Reading"): ``read_test_token`` of a test credential file holding a token and a final ``\\r\\n``, or
    a final ``\\n``, answers the token alone."""
    credential = directory / TEST_CREDENTIAL_FILE
    credential.parent.mkdir(parents=True)
    for line_end in ACCEPTED_LINE_ENDS:
        token = _new_token(label="accepted")
        credential.write_bytes(data=(token + line_end).encode(encoding=TEXT_ENCODING))
        # Compared into a bool first, so that no assertion prints the token.
        read_the_token = forge.read_test_token(path=credential) == token
        assert read_the_token, f"read_test_token did not answer the token of a file ending {line_end!r}"


@pytest.mark.parametrize(argnames="kind", argvalues=BAD_CREDENTIAL_KINDS)
def test_a_bad_test_credential_fails_before_any_request(tmp_path: Path, kind: str) -> None:
    """AC-6.2 (D8, D9 step 2): a test credential file ``credentials/gitlab-sff-testing-pat.txt`` that is missing,
    empty, a lone line end, ``PASTE_TOKEN``, a token holding a space, one holding a non-ASCII character, or two lines
    makes ``provision`` raise ``ForgeSetupError`` naming the file and none of its text, before any wrapper or git
    invocation and without entering the body, the GitHub suite's valid test credential file beside it passed over; the
    workspace no longer exists. A token with a final ``\\r\\n`` (or ``\\n``) is read as the token alone."""
    forge = _ephemeral()
    _require(module=forge, names=READING_SYMBOLS)
    checkout = tmp_path / CHECKOUT_NAME
    _init_checkout(path=checkout)
    _write_credential(directory=checkout, name=GITHUB_TEST_CREDENTIAL_NAME, token=_new_token(label=DECOY_LABEL))
    credential = checkout / TEST_CREDENTIAL_FILE
    bad = _bad_credential(kind=kind)
    if bad.data is not None:
        credential.write_bytes(data=bad.data)
    workspace = tmp_path / WORKSPACE_NAME
    workspace.mkdir()
    wrapper = _recording_runner(forge=forge, script=_refuse_every_invocation)
    git = _scripted_git_runner(forge=forge, script=_refuse_every_git_command)
    yielded: List[Any] = []

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        with forge.provision(checkout=checkout, workspace=workspace, wrapper=wrapper, git=git) as project:
            yielded.append(project)

    message = str(refused.value)
    assert _names_one_of(message=message, paths=(credential,)), f"the refusal does not name {credential}: {message}"
    quotes_the_text = any(part in message for part in bad.parts)
    assert not quotes_the_text, "the refusal holds the test credential file's text"
    assert (wrapper.recorded, git.recorded) == ([], []), f"the refused provision ran {wrapper.recorded} {git.recorded}"
    assert yielded == [], f"the provision yielded with a {kind} test credential file"
    assert not workspace.exists(), f"the workspace {workspace} outlived the refused provision"
    _assert_a_final_line_end_is_read_away(forge=forge, directory=tmp_path / "accepted")


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


def _assert_sentinel_untouched(*, setup: _Provisioning, content: bytes, opened: Sequence[Path], clone: Path) -> None:
    """UB-2: the checkout's ``config/gitlab.json`` keeps ``content``, and of the files named ``config/gitlab.json``
    the provision opened, none lies outside ``clone`` (resolved)."""
    kept = setup.sentinel.read_bytes() == content
    assert kept, "the checkout's config/gitlab.json changed"
    sentinel = setup.sentinel.resolve()
    assert sentinel not in opened, f"the provision opened the checkout's {sentinel}"
    named = (CLONE_CONFIG_FILE.parent.name, CLONE_CONFIG_FILE.name)
    outside = [path for path in opened if (path.parent.name, path.name) == named and clone not in path.parents]
    assert outside == [], f"the provision opened a config/gitlab.json outside its clone: {outside}"


def test_the_token_is_written_only_to_the_clone(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """AC-6.3, UB-2 (D3, D8): in a scripted provision's body, the files of the test's tree holding the token are
    exactly the test credential file, the clone's ``config/gitlab.json`` and its ``.git/sff-forge-token``; the clone's
    ``config/gitlab.json`` holds exactly the keys ``hostname`` (gitlab.com), ``project_id`` (this run's project) and
    ``token`` (the test token), its ``.git/sff-forge-token`` exactly the token and ``\\n``, its ``.git/info/exclude``
    names ``config/``, and its ``.git/config`` does not hold the token; no recorded argv, no record captured at DEBUG
    and no ``repr`` of the yielded ``EphemeralProject`` holds it; afterwards only the test credential file holds it.
    The checkout's own ``config/gitlab.json``, holding another token and a ``token_type``, keeps its content, and no
    ``config/gitlab.json`` outside the clone is opened."""
    forge = _ephemeral()
    _require(module=forge, names=WRITTEN_SYMBOLS)
    assert Path(forge.CLONE_CONFIG_FILE) == CLONE_CONFIG_FILE, (
        f"CLONE_CONFIG_FILE is {forge.CLONE_CONFIG_FILE!r}, not {CLONE_CONFIG_FILE.as_posix()} (D8)"
    )
    assert Path(forge.CLONE_GIT_TOKEN_FILE) == CLONE_GIT_TOKEN_FILE, (
        f"CLONE_GIT_TOKEN_FILE is {forge.CLONE_GIT_TOKEN_FILE!r}, not {CLONE_GIT_TOKEN_FILE.as_posix()} (D3)"
    )
    setup = _provisioning(forge=forge, tmp_path=tmp_path)
    sentinel_content = setup.sentinel.read_bytes()
    clone = setup.workspace.resolve() / CLONE_NAME
    entered: List[_Entered] = []
    caplog.set_level(level=logging.DEBUG)

    with pytest.MonkeyPatch.context() as patch:
        opened = _record_opens(patch=patch)
        _provide(forge=forge, setup=setup, entered=entered, body_raises=False)

    assert len(entered) == 1, f"the body was entered {len(entered)} times"
    found = entered[0]
    test_credential = setup.test_credential.relative_to(setup.root).as_posix()
    clone_files = [setup.clone / CLONE_CONFIG_FILE, setup.clone / CLONE_GIT_TOKEN_FILE]
    clone_credentials = [path.relative_to(setup.root).as_posix() for path in clone_files]
    assert list(found.holders) == sorted([test_credential, *clone_credentials]), f"the token was in {found.holders}"
    assert found.config_keys == tuple(sorted(CLONE_CONFIG_KEYS)), (
        f"the clone's config/gitlab.json holds the keys {found.config_keys}, not exactly {sorted(CLONE_CONFIG_KEYS)}"
    )
    target = (GITLAB_HOSTNAME, _full_path(namespace=TEST_GROUP, path=str(setup.script.path)))
    assert found.config_target == target, f"the clone's config/gitlab.json names {found.config_target}, not {target}"
    assert found.config_token_is_the_test_token, "the token of the clone's config/gitlab.json is not the test token"
    assert found.git_token_file_is_the_test_token, (
        "the clone's .git/sff-forge-token does not hold exactly the test token and a \\n"
    )
    assert not found.git_config_holds_the_token, "the clone's .git/config holds the token"
    assert EXCLUDED_CONFIG in found.exclude_lines, f"the clone's .git/info/exclude names no {EXCLUDED_CONFIG}"
    recorded = [*setup.wrapper.recorded, *(argv for argv, _ in setup.git.recorded)]
    argv_holds_the_token = any(setup.token in part for argv in recorded for part in argv)
    assert not argv_holds_the_token, "a recorded argv holds the token"
    holding = [f"{record.name} {record.levelname}" for record in caplog.records if setup.token in record.getMessage()]
    logged = setup.token in caplog.text
    assert holding == [] and not logged, f"captured log records hold the token: {holding}"
    assert not found.representation_holds_the_token, "the repr of the yielded EphemeralProject holds the token"
    assert _holders(setup=setup) == [test_credential], "a file holding the token outlived the provision"
    _assert_sentinel_untouched(setup=setup, content=sentinel_content, opened=opened, clone=clone)


def test_the_clone_commits_no_credential(tmp_path: Path) -> None:
    """AC-6.3 (D3, D8): ``prepare_clone`` with the real git runner, ``SubprocessGitRunner`` given ``CLONE_GIT_HELPER``
    (local commands only: ``git init``, ``git remote add``), writes the clone's ``config/gitlab.json`` and
    ``.git/sff-forge-token``; with a file added beside them, ``git add -A`` stages it and ``git ls-files`` names it
    alone, neither credential file."""
    forge = _ephemeral()
    _require(module=forge, names=CLONE_SYMBOLS)
    workspace = tmp_path / WORKSPACE_NAME
    workspace.mkdir()
    clone = workspace / CLONE_NAME
    git = forge.SubprocessGitRunner(clone=clone, helper=forge.CLONE_GIT_HELPER)

    forge.prepare_clone(clone=clone, token=_new_token(label="clone"), path=EPHEMERAL_PREFIX + _run_id(), git=git)

    credential_files = [clone / forge.CLONE_CONFIG_FILE, clone / forge.CLONE_GIT_TOKEN_FILE]
    unwritten = [path for path in credential_files if not path.is_file()]
    assert unwritten == [], f"prepare_clone wrote no {unwritten}"
    (clone / SEED_FILE).write_bytes(data=("seed" + LINE_END).encode(encoding=TEXT_ENCODING))
    _git(arguments=["add", "-A"], cwd=clone)
    listed = _git(arguments=["ls-files"], cwd=clone).stdout.splitlines()
    assert listed == [SEED_FILE], f"after git add -A, git ls-files names {listed}, not {SEED_FILE} alone"
