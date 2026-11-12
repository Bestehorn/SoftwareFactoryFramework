"""The forge suite's support module: what ``test/forge/`` runs beside pytest against the test organization (D10).

The forge suite (``test/forge/``, run by ``python scripts/run_tests.py --workers 1 test/forge``) drives the product
wrapper against an ephemeral ``sff-test-*`` repository of the test organization. This module holds the logic that
decides without the forge, so the default collection proves it (``test/test_forge_support.py``): the refusal of a
distributed run (D1), the per-command git credential helper (D3), the run id and the repository name it gives (D4),
where the test credential file is found, how its token is read and how the CI step writes it (D8), the teardown guard
and the leftover sweep (D9), and ``provision``, the context manager around one run's repository: it reads the test
token, prepares the clone, sweeps, creates and seeds the repository, and afterwards deletes it and removes the
workspace (D3 "The clone", D9). The runners are its one way out to a process (D10): ``SubprocessWrapperRunner`` starts
the product wrapper with the test marker, ``SubprocessGitRunner`` starts git, and the logic above takes a
``WrapperRunner`` or ``GitRunner``, so a test gives it a double.

Loaded by path, never imported by name and never collected: its name matches neither the default ``python_files`` nor
the suite's ``forge_*.py``, and under ``--import-mode=importlib`` a test directory's utility module is not importable.
It imports only the standard library at module level; the product wrapper, whose constants it reads, is loaded by path
on first use (``product_wrapper``). No function logs or prints a token.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# D1: xdist's ``worker_id`` fixture is ``master`` when xdist does not distribute; a worker's is ``gw<n>``.
CONTROLLER_WORKER_ID = "master"
FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge"

# D3 and D8: the credential files, relative to a working tree.
CREDENTIALS_DIRECTORY = Path("credentials")
#: The file the product wrapper reads its token from; the suite writes it only under its clone (UB-2).
CLONE_CREDENTIAL_FILE = CREDENTIALS_DIRECTORY / "github-pat.txt"
#: The operator's test token for the test organization, git-ignored like every file of ``credentials/``.
TEST_CREDENTIAL_FILE = CREDENTIALS_DIRECTORY / "github-sff-testing-pat.txt"
#: The test credential's setup note (D7), which every refusal of the test credential file points to.
SETUP_NOTE = "docs/forge-suite.md"

# D3: the global git options of an authenticated command. The empty value empties the helper list, so no configured
# helper (Git Credential Manager) is asked; the github.com helper is a shell snippet that answers only ``get``, from
# the clone's credential file, through the shell built-ins ``read`` and ``printf``.
CONFIG_OPTION = "-c"
HELPER_RESET = "credential.helper="
GITHUB_HELPER_KEY = "credential.https://github.com.helper"
CONFIG_ASSIGNMENT = "="
ACCESS_TOKEN_USERNAME = "x-access-token"
SHELL_QUOTE = "'"
HELPER_SNIPPET = (
    '!f() {{ test "$1" = get || return 0; read -r t < \'{credential}\' || test -n "$t"; '
    "printf 'username={username}\\npassword=%s\\n' \"$t\"; }}; f"
)

# D8: the main working tree is the parent of git's common directory, asked of git in the checkout.
GIT = "git"
GIT_COMMON_DIR_ARGUMENTS = ("rev-parse", "--path-format=absolute", "--git-common-dir")
GIT_EXIT_OK = 0
SECRET_NAME = "SFF_TEST_TOKEN"  # pragma: allowlist secret
LINE_END = "\n"
TEXT_ENCODING = "utf-8"
#: The bound of every subprocess the suite starts.
SUBPROCESS_TIMEOUT_SECONDS = 300

#: D8: the working tree holding the suite, the repository root above ``test/forge/``: the ``checkout`` whose test
#: credential file a run reads.
CHECKOUT = Path(__file__).resolve().parents[2]
# D10: the product entry script the suite starts, and the fixed ``sys.modules`` key of its by-path load, whose
# ``TEST_MARKER_OPTION`` and ``EPHEMERAL_REPOSITORY_PREFIX`` this module reads rather than redefines.
PRODUCT_WRAPPER = CHECKOUT / "src" / "payload" / "scripts" / "github_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_product_wrapper"
INTERPRETER_OPTION = "-X"
# D3, D10: every git command's working tree option and the suite's commit identity (a runner has no global one), with
# signing off, so no commit asks for a signing key on a machine whose git configuration signs (DL-003).
GIT_DIRECTORY_OPTION = "-C"
COMMIT_USER_NAME = "SFF Forge Suite"
COMMIT_USER_EMAIL = "forge-suite@example.invalid"
COMMIT_SIGNING = "false"
COMMIT_IDENTITY = (
    CONFIG_OPTION,
    f"user.name{CONFIG_ASSIGNMENT}{COMMIT_USER_NAME}",
    CONFIG_OPTION,
    f"user.email{CONFIG_ASSIGNMENT}{COMMIT_USER_EMAIL}",
    CONFIG_OPTION,
    f"commit.gpgSign{CONFIG_ASSIGNMENT}{COMMIT_SIGNING}",
)

# D4, D5: the run id, the UTC time of its creation then a random part, and the test organization, the one place the
# suite names it.
RUN_ID_TIME_FORMAT = "%Y%m%d%H%M%S"
RUN_ID_SEPARATOR = "-"
TEST_ORGANIZATION = "bestehorn-sff-test"

# D9: the records the teardown and the sweep send, as ``call`` arguments, and the listed repository's fields
# (docs.github.com "List organization repositories").
CALL_SUBCOMMAND = "call"
REPOSITORY_DELETE = "repos/delete"
REPOSITORY_LISTING = "repos/list-for-org"
PATH_OPTION = "--path"
PARAMETER_ASSIGNMENT = "="
OWNER_PARAMETER = "owner"
REPO_PARAMETER = "repo"
ORG_PARAMETER = "org"
FIELD_OWNER = "owner"
FIELD_LOGIN = "login"
FIELD_NAME = "name"
FIELD_CREATED_AT = "created_at"
CREATED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FULL_NAME_SEPARATOR = "/"
#: A repository the test organization holds under the prefix is a leftover once it is older than this.
LEFTOVER_AGE = timedelta(days=1)
WRAPPER_EXIT_OK = 0
#: The product wrapper's exit on a ``GitHubAPIError``, and the status its ``ERROR:`` line names for a repository that
#: no longer exists (``transport._http_failure``: ``... failed: HTTP <status>``).
WRAPPER_API_FAILURE = 1
NOT_FOUND_ANSWER = re.compile(r"\bHTTP 404\b")

# D9 step 5: the creation (docs.github.com "Create an organization repository"), as ``call`` arguments, and the fields
# of its answer the record is made of; ``details`` of the refusal of a public repository carries the kept record.
REPOSITORY_CREATION = "repos/create-in-org"
RAW_FIELD_OPTION = "-f"
TYPED_FIELD_OPTION = "-F"
FIELD_PRIVATE = "private"
FIELD_AUTO_INIT = "auto_init"
FIELD_DEFAULT_BRANCH = "default_branch"
TYPED_TRUE = "true"
DETAIL_CREATED = "created"

# D3 "The clone", D8 "Writing", D9 steps 3 and 6: the clone under the workspace, its git files, its origin and the git
# commands that prepare and seed it.
CLONE_DIRECTORY = "clone"
GIT_METADATA_DIRECTORY = ".git"
GIT_EXCLUDE_FILE = Path(GIT_METADATA_DIRECTORY) / "info" / "exclude"
#: The line the clone's ``.git/info/exclude`` gains, so no commit of the clone holds its credential file.
EXCLUDED_CREDENTIALS = CREDENTIALS_DIRECTORY.as_posix() + "/"
#: Owner-only where the OS honours it; on Windows only the read-only flag follows a mode (docs.python.org ``os.chmod``).
CLONE_CREDENTIAL_MODE = 0o600
ORIGIN_REMOTE = "origin"
ORIGIN_URL = "https://github.com/{owner}/{name}.git"
GIT_INIT = "init"
GIT_REMOTE = "remote"
GIT_REMOTE_ADD = "add"
GIT_FETCH = "fetch"
GIT_CHECKOUT = "checkout"
GIT_RESET_BRANCH_OPTION = "-B"
GIT_TRACK_OPTION = "--track"
REMOTE_BRANCH_SEPARATOR = "/"
GIT_REV_PARSE = "rev-parse"
GIT_LS_TREE = "ls-tree"
GIT_RECURSIVE_OPTION = "-r"
GIT_NAME_ONLY_OPTION = "--name-only"
HEAD = "HEAD"
HEAD_TREE = "HEAD^{tree}"
SEED_REVISION_COUNT = 2
#: A seed path under this directory would start a workflow on the first push; the seed must hold none.
WORKFLOW_DIRECTORY = ".github/workflows/"
#: ``git ls-tree`` quotes a path holding an unusual character (``core.quotePath``); the directory part stays literal.
GIT_PATH_QUOTE = '"'

# D9 step 7: ``remove_tree``'s retries, for the read-only attribute git gives its object files on Windows and a brief
# "in use by another process" lock there.
REMOVAL_ATTEMPTS = 5
REMOVAL_PAUSE_SECONDS = 0.5


class ForgeSuiteError(Exception):
    """A refusal or failure of the forge suite's support logic; ``details`` carries structured context, if any."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details


class ForgeSetupError(ForgeSuiteError):
    """The run cannot start, or its setup is refused: a distributed run, a missing or bad test credential, a clone
    path the credential helper cannot quote."""


class ForgeCommandError(ForgeSuiteError):
    """A wrapper or git invocation the suite depends on exited with a failure."""


class ForgeTeardownRefusedError(ForgeSuiteError):
    """The teardown was given a repository other than this run's; nothing was sent."""


class ForgeSweepRefusedError(ForgeSuiteError):
    """The sweep was given a repository that is no leftover; nothing was sent."""


def refuse_distributed_run(*, worker_id: str) -> None:
    """D1: raises ``ForgeSetupError`` unless ``worker_id`` (xdist's fixture) is ``master``, since a session fixture
    runs once per xdist worker and each would create its own repository."""
    if worker_id != CONTROLLER_WORKER_ID:
        raise ForgeSetupError(
            message=(
                f"The forge suite is running in the xdist worker {worker_id}, and each worker would create its own "
                f"repository; run it in one process with --workers 1: {FORGE_COMMAND}"
            )
        )


def credential_helper_arguments(*, clone: Path) -> List[str]:
    """D3: the global options that make one git command authenticate to github.com with the clone's token.

    The helper string holds the clone credential file's absolute path in forward-slash form, single-quoted so a space
    is literal, and never the token; a path holding a single quote raises ``ForgeSetupError``.
    """
    credential = (clone.absolute() / CLONE_CREDENTIAL_FILE).as_posix()
    if SHELL_QUOTE in credential:
        raise ForgeSetupError(
            message=(
                f"The clone credential file {credential} holds a single quote, which the credential helper cannot "
                "quote; use a workspace whose path holds none"
            )
        )
    helper = HELPER_SNIPPET.format(credential=credential, username=ACCESS_TOKEN_USERNAME)
    return [CONFIG_OPTION, HELPER_RESET, CONFIG_OPTION, GITHUB_HELPER_KEY + CONFIG_ASSIGNMENT + helper]


def _git_output(*, arguments: Sequence[str], directory: Path) -> str:
    """The standard output of local git run in ``directory``, stripped; a failure to run raises ``ForgeSetupError``
    with git's standard error."""
    command = " ".join([GIT, *arguments])
    try:
        completed = subprocess.run(
            args=[GIT, *arguments],
            cwd=directory,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding=TEXT_ENCODING,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ForgeSetupError(message=f"`{command}` could not run in {directory}: {exc}") from exc
    if completed.returncode != GIT_EXIT_OK:
        raise ForgeSetupError(
            message=f"`{command}` exited {completed.returncode} in {directory}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def main_working_tree(*, checkout: Path) -> Path:
    """The main working tree of the repository ``checkout`` belongs to: the parent of git's common directory, which a
    linked worktree shares with it."""
    return Path(_git_output(arguments=GIT_COMMON_DIR_ARGUMENTS, directory=checkout)).parent


def find_test_credential(*, checkout: Path) -> Path:
    """D8: ``checkout``'s own test credential file, else the main working tree's (a linked worktree holds no
    git-ignored file); with neither, ``ForgeSetupError`` naming both paths."""
    own = checkout / TEST_CREDENTIAL_FILE
    if own.is_file():
        logger.debug("The test credential file is %s", own)
        return own
    shared = main_working_tree(checkout=checkout) / TEST_CREDENTIAL_FILE
    if shared.is_file():
        logger.debug("The test credential file is the main working tree's %s", shared)
        return shared
    searched = f"{own} is not a file" if shared.resolve() == own.resolve() else f"neither {own} nor {shared} is a file"
    raise ForgeSetupError(
        message=(
            f"No test credential file: {searched}. Paste the test organization's token, on one line, into the "
            f"checkout's file ({SETUP_NOTE})"
        )
    )


def write_test_credential(*, token: str, checkout: Path) -> None:
    """D8 "CI": writes ``token`` and a line end as ``checkout``'s test credential file; an empty ``token`` raises
    ``ForgeSetupError`` and writes nothing."""
    if not token:
        raise ForgeSetupError(
            message=(
                f"Wrote no test credential file: the secret {SECRET_NAME} is unavailable to this run (it is unset, or "
                "the run is a fork's or Dependabot's pull request, which receives no secrets)"
            )
        )
    path = checkout / TEST_CREDENTIAL_FILE
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data=(token + LINE_END).encode(encoding=TEXT_ENCODING))
    logger.info("Wrote the test credential file %s", path)


# ---------------------------------------------------------------------------------------------------------------------
# The records, the runners and the product wrapper (D10)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Invocation:
    """What one product-wrapper or git process answered: its exit code, standard output and standard error."""

    returncode: int
    stdout: str
    stderr: str

    def json(self) -> Any:
        """The standard output read as JSON, as the wrapper prints a record's answer; output that is no JSON raises
        ``ForgeCommandError``."""
        try:
            return json.loads(s=self.stdout)
        except ValueError as exc:
            raise ForgeCommandError(message=f"The invocation printed no JSON: {exc}") from exc


@dataclass(frozen=True)
class CreatedRepository:
    """The repository this run's creation answered with (D9 step 5): the one the teardown may delete."""

    owner: str
    name: str
    default_branch: str


@dataclass(frozen=True)
class RepositoryRecord:
    """One repository of the test organization's listing, as the sweep judges it: ``created_at`` is aware UTC."""

    owner: str
    name: str
    created_at: datetime

    @property
    def full_name(self) -> str:
        return self.owner + FULL_NAME_SEPARATOR + self.name

    @classmethod
    def of(cls, *, item: Mapping[str, Any]) -> RepositoryRecord:
        """The record of one listed item: its ``owner.login``, ``name`` and ``created_at`` (``%Y-%m-%dT%H:%M:%SZ``,
        UTC); an item without them, or with a ``created_at`` of another form, raises ``ForgeCommandError``."""
        owner = item.get(FIELD_OWNER)
        login = owner.get(FIELD_LOGIN) if isinstance(owner, Mapping) else None
        name = item.get(FIELD_NAME)
        created = item.get(FIELD_CREATED_AT)
        if not (isinstance(login, str) and isinstance(name, str) and isinstance(created, str)):
            raise ForgeCommandError(
                message=(
                    f"A listed repository holds no {FIELD_OWNER}.{FIELD_LOGIN}, {FIELD_NAME} and {FIELD_CREATED_AT} "
                    f"text; its fields are {sorted(item)}"
                )
            )
        try:
            created_at = datetime.strptime(created, CREATED_AT_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ForgeCommandError(
                message=(
                    f"The listed repository {login}{FULL_NAME_SEPARATOR}{name} has a {FIELD_CREATED_AT} not of the "
                    f"form {CREATED_AT_FORMAT}: {created!r}"
                )
            ) from exc
        return cls(owner=login, name=name, created_at=created_at)


def _invoke(*, argv: List[str], directory: Optional[Path]) -> Invocation:
    """Runs ``argv`` as a list, never through a shell, in ``directory`` (the current one when ``None``), with no
    standard input, no ``env`` and the suite's timeout; a process that cannot start or outlives the timeout raises
    ``ForgeCommandError``."""
    try:
        completed = subprocess.run(
            args=argv,
            cwd=directory,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding=TEXT_ENCODING,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ForgeCommandError(message=f"`{' '.join(argv)}` could not run in {directory}: {exc}") from exc
    return Invocation(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


class WrapperRunner(ABC):
    """Runs the product wrapper with given arguments and answers with the process's ``Invocation``."""

    @abstractmethod
    def run(self, *, arguments: Sequence[str]) -> Invocation:
        """The ``Invocation`` of the product wrapper run with ``arguments``."""


class SubprocessWrapperRunner(WrapperRunner):
    """The one place the suite starts the product wrapper: this interpreter, the test marker ``-X
    <TEST_MARKER_OPTION>``, ``PRODUCT_WRAPPER`` and the arguments, in ``directory`` (the clone, whose ``origin`` every
    record targets)."""

    def __init__(self, *, directory: Path) -> None:
        self.directory = directory

    def run(self, *, arguments: Sequence[str]) -> Invocation:
        marker = str(product_wrapper().TEST_MARKER_OPTION)
        argv = [sys.executable, INTERPRETER_OPTION, marker, str(PRODUCT_WRAPPER), *arguments]
        return _invoke(argv=argv, directory=self.directory)


class GitRunner(ABC):
    """Runs git in the clone with given arguments and answers with the process's ``Invocation``."""

    @abstractmethod
    def run(self, *, arguments: Sequence[str], authenticated: bool = False) -> Invocation:
        """The ``Invocation`` of git run with ``arguments``; ``authenticated`` adds D3's credential helper options."""


class SubprocessGitRunner(GitRunner):
    """Starts git: D3's helper options when ``authenticated``, the suite's commit identity, ``-C <clone>`` and the
    arguments."""

    def __init__(self, *, clone: Path) -> None:
        self.clone = clone

    def run(self, *, arguments: Sequence[str], authenticated: bool = False) -> Invocation:
        helper = credential_helper_arguments(clone=self.clone) if authenticated else []
        argv = [GIT, *helper, *COMMIT_IDENTITY, GIT_DIRECTORY_OPTION, str(self.clone), *arguments]
        return _invoke(argv=argv, directory=None)


def product_wrapper() -> ModuleType:
    """The product wrapper ``PRODUCT_WRAPPER``, loaded by path on first use and reused while ``sys.modules`` holds it.

    Never loaded at import, so loading this module changes no ``sys.path``; the directory the wrapper puts on
    ``sys.path`` for its package is taken off again once it is loaded. A missing script raises ``ForgeSetupError``.
    """
    loaded = sys.modules.get(PRODUCT_WRAPPER_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == PRODUCT_WRAPPER:
        return loaded
    if not PRODUCT_WRAPPER.is_file():
        raise ForgeSetupError(message=f"The product wrapper {PRODUCT_WRAPPER} does not exist")
    spec = importlib.util.spec_from_file_location(name=PRODUCT_WRAPPER_MODULE, location=PRODUCT_WRAPPER)
    if spec is None or spec.loader is None:
        raise ForgeSetupError(message=f"The product wrapper {PRODUCT_WRAPPER} cannot be loaded")
    module = importlib.util.module_from_spec(spec=spec)
    search_path = list(sys.path)
    sys.modules[PRODUCT_WRAPPER_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(PRODUCT_WRAPPER_MODULE, None)
        raise
    finally:
        sys.path[:] = search_path
    return module


def _ephemeral_prefix() -> str:
    """The product wrapper's ``EPHEMERAL_REPOSITORY_PREFIX``, the prefix the marker lets through (D2)."""
    return str(product_wrapper().EPHEMERAL_REPOSITORY_PREFIX)


# ---------------------------------------------------------------------------------------------------------------------
# The run id (D4) and the two deletion paths (D9)
# ---------------------------------------------------------------------------------------------------------------------


def new_run_id() -> str:
    """D4: the UTC time as ``%Y%m%d%H%M%S``, ``-``, then a fresh ``uuid4`` hex; digits, lowercase hex and ``-`` only, so
    the product wrapper's ``GITHUB_REPOSITORY_PATTERN`` reads the repository name it gives back whole."""
    return datetime.now(tz=timezone.utc).strftime(RUN_ID_TIME_FORMAT) + RUN_ID_SEPARATOR + uuid.uuid4().hex


def ephemeral_name(*, run_id: str) -> str:
    """D4: the name of the run's repository, the product wrapper's ``EPHEMERAL_REPOSITORY_PREFIX`` then ``run_id``."""
    return _ephemeral_prefix() + run_id


def _path_argument(*, parameter: str, value: str) -> List[str]:
    """A ``call`` path parameter, ``--path <parameter>=<value>``."""
    return [PATH_OPTION, parameter + PARAMETER_ASSIGNMENT + value]


def _deletion_arguments(*, owner: str, name: str) -> List[str]:
    """D9's ``call repos/delete --path owner=<owner> --path repo=<name>``."""
    return [
        CALL_SUBCOMMAND,
        REPOSITORY_DELETE,
        *_path_argument(parameter=OWNER_PARAMETER, value=owner),
        *_path_argument(parameter=REPO_PARAMETER, value=name),
    ]


def _failure(*, action: str, invocation: Invocation) -> ForgeCommandError:
    """The error of a wrapper invocation that exited with a failure: ``action``, the exit code and its standard
    error."""
    return ForgeCommandError(
        message=f"{action} failed: the product wrapper exited {invocation.returncode}: {invocation.stderr.strip()}"
    )


def delete_ephemeral(*, wrapper: WrapperRunner, created: Optional[CreatedRepository], run_id: str) -> None:
    """D9 step 7, the teardown guard: deletes the repository this run created, and only it.

    ``created`` is ``None`` when the creation never succeeded: nothing is sent (AC-2.3). A record that is not
    ``bestehorn-sff-test/<ephemeral_name(run_id)>`` raises ``ForgeTeardownRefusedError`` naming it and this run's
    repository, nothing sent (AC-2.2). Otherwise one ``call repos/delete`` is sent; a failure raises
    ``ForgeCommandError`` naming the target (AC-2.1).
    """
    if created is None:
        logger.info("This run created no repository; the teardown deletes nothing")
        return
    own = ephemeral_name(run_id=run_id)
    target = created.owner + FULL_NAME_SEPARATOR + created.name
    if (created.owner, created.name) != (TEST_ORGANIZATION, own):
        raise ForgeTeardownRefusedError(
            message=(
                f"The teardown refuses to delete {target}: this run's repository is "
                f"{TEST_ORGANIZATION}{FULL_NAME_SEPARATOR}{own}; nothing was sent"
            )
        )
    invocation = wrapper.run(arguments=_deletion_arguments(owner=created.owner, name=created.name))
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Deleting this run's repository {target}", invocation=invocation)
    logger.info("Deleted this run's repository %s", target)


def is_leftover(*, record: RepositoryRecord, now: datetime) -> bool:
    """D9: whether ``record`` is the test organization's, its name starts with ``EPHEMERAL_REPOSITORY_PREFIX``, and
    it was created more than ``LEFTOVER_AGE`` before ``now`` (aware UTC); a day old or less is kept."""
    return (
        record.owner == TEST_ORGANIZATION
        and record.name.startswith(_ephemeral_prefix())
        and now - record.created_at > LEFTOVER_AGE
    )


def select_leftovers(*, records: Iterable[RepositoryRecord], now: datetime) -> List[RepositoryRecord]:
    """D9: exactly the records of ``records`` that ``is_leftover`` at ``now``, in their order."""
    return [record for record in records if is_leftover(record=record, now=now)]


def _listed_records(*, invocation: Invocation) -> List[RepositoryRecord]:
    """The records of a listing's printed JSON array; anything but an array of objects raises
    ``ForgeCommandError``."""
    listed = invocation.json()
    if not isinstance(listed, list) or not all(isinstance(item, Mapping) for item in listed):
        raise ForgeCommandError(message=f"The listing of {TEST_ORGANIZATION} printed no array of repositories")
    return [RepositoryRecord.of(item=item) for item in listed]


def sweep_leftovers(*, wrapper: WrapperRunner, now: datetime) -> None:
    """D9 step 4: lists the test organization's repositories with ``call repos/list-for-org --path
    org=bestehorn-sff-test`` (``call`` reads every page), a failure raising ``ForgeCommandError``, then deletes each
    leftover at ``now`` with ``delete_leftover``."""
    invocation = wrapper.run(
        arguments=[
            CALL_SUBCOMMAND,
            REPOSITORY_LISTING,
            *_path_argument(parameter=ORG_PARAMETER, value=TEST_ORGANIZATION),
        ]
    )
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Listing the repositories of {TEST_ORGANIZATION}", invocation=invocation)
    for record in select_leftovers(records=_listed_records(invocation=invocation), now=now):
        delete_leftover(wrapper=wrapper, record=record, now=now)


def delete_leftover(*, wrapper: WrapperRunner, record: RepositoryRecord, now: datetime) -> None:
    """D9: deletes one leftover with ``call repos/delete``.

    A record that is no leftover at ``now`` raises ``ForgeSweepRefusedError`` naming it, nothing sent. An answer of
    exit 1 with ``HTTP 404`` on standard error counts as deleted (a concurrent run's sweep deleted it first); any other
    failure raises ``ForgeCommandError``.
    """
    if not is_leftover(record=record, now=now):
        raise ForgeSweepRefusedError(
            message=(
                f"The sweep refuses to delete {record.full_name}: it is no {TEST_ORGANIZATION} repository named "
                f"{_ephemeral_prefix()}* and created more than {LEFTOVER_AGE} before {now.isoformat()}; nothing was "
                "sent"
            )
        )
    invocation = wrapper.run(arguments=_deletion_arguments(owner=record.owner, name=record.name))
    if invocation.returncode == WRAPPER_EXIT_OK:
        logger.info("Deleted the leftover repository %s, created %s", record.full_name, record.created_at.isoformat())
        return
    if invocation.returncode == WRAPPER_API_FAILURE and NOT_FOUND_ANSWER.search(string=invocation.stderr):
        logger.info("The leftover repository %s was already deleted", record.full_name)
        return
    raise _failure(action=f"Deleting the leftover repository {record.full_name}", invocation=invocation)


# ---------------------------------------------------------------------------------------------------------------------
# The test token (D8) and the provision of one run's repository (D3 "The clone", D9 steps 1 to 7)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EphemeralRepository:
    """The repository one run owns, as ``provision`` yields it (D9): the run id, the repository's owner, name and
    default branch, its seed commit and tree, the moment of the run's sweep (aware UTC), the clone, and the two
    runners bound to the clone. It holds no token, so neither does its ``repr``."""

    run_id: str
    owner: str
    name: str
    default_branch: str
    seed_sha: str
    seed_tree_sha: str
    swept_at: datetime
    clone: Path
    wrapper: WrapperRunner
    git: GitRunner


def read_test_token(*, path: Path) -> str:
    """D8 "Reading": the token of the test credential file ``path``, refused as the product wrapper's ``_load_token``
    refuses its own file, through the product's ``_one_token`` and ``PLACEHOLDER``.

    A missing or unreadable file, a file that is not one token, an empty one and the placeholder each raise
    ``ForgeSetupError`` naming ``path`` and none of its contents. Nothing logs the token.
    """
    product = product_wrapper()
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ForgeSetupError(
            message=f"The test credential file {path} cannot be read ({exc.strerror}); see {SETUP_NOTE}"
        ) from None
    not_one_token = (
        f"The test credential file {path} does not hold a single token. Paste only the test organization's token, on "
        f"one line, into this file ({SETUP_NOTE})"
    )
    try:
        token: str = product._one_token(data=data, refusal=not_one_token)
    except product.GitHubAPIError:
        raise ForgeSetupError(message=not_one_token) from None
    if not token or token == product.PLACEHOLDER:
        raise ForgeSetupError(
            message=(
                f"The test credential file {path} is empty or still holds the placeholder. Paste the test "
                f"organization's token, on one line, into this file ({SETUP_NOTE})"
            )
        )
    return token


def _origin_url(*, name: str) -> str:
    """D3's ``origin`` of the test organization's repository ``name``: no userinfo, so ``.git/config`` holds no
    token."""
    return ORIGIN_URL.format(owner=TEST_ORGANIZATION, name=name)


def _run_git(*, git: GitRunner, arguments: Sequence[str], authenticated: bool = False) -> Invocation:
    """``git`` run with ``arguments``; an exit other than 0 raises ``ForgeCommandError`` with git's standard error."""
    invocation = git.run(arguments=arguments, authenticated=authenticated)
    if invocation.returncode != GIT_EXIT_OK:
        raise ForgeCommandError(
            message=(
                f"`{GIT} {' '.join(arguments)}` exited {invocation.returncode} in the clone: "
                f"{invocation.stderr.strip()}"
            )
        )
    return invocation


def _write_clone_credential(*, clone: Path, token: str) -> None:
    """D8 "Writing": the clone's ``credentials/github-pat.txt``, created owner-only (``CLONE_CREDENTIAL_MODE``) and
    then given ``token`` and ``\\n`` as bytes; a file already there raises ``FileExistsError``, so none is
    overwritten."""
    credential = clone / CLONE_CREDENTIAL_FILE
    credential.parent.mkdir()
    credential.touch(mode=CLONE_CREDENTIAL_MODE, exist_ok=False)
    credential.write_bytes(data=(token + LINE_END).encode(encoding=TEXT_ENCODING))


def _exclude_credentials(*, clone: Path) -> None:
    """D8 "Writing": appends ``credentials/`` to the clone's ``.git/info/exclude``, on a line of its own, so no commit
    of the clone holds its credential file."""
    exclude = clone / GIT_EXCLUDE_FILE
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_bytes() if exclude.is_file() else b""
    line_end = LINE_END.encode(encoding=TEXT_ENCODING)
    separator = line_end if existing and not existing.endswith(line_end) else b""
    exclude.write_bytes(data=existing + separator + EXCLUDED_CREDENTIALS.encode(encoding=TEXT_ENCODING) + line_end)


def prepare_clone(*, clone: Path, token: str, name: str, git: GitRunner) -> None:
    """D9 step 3 (D3 "The clone"): creates ``clone`` with ``Path.mkdir`` and runs ``git init`` in it, writes its
    credential file and exclude line (D8), then ``git remote add origin`` of the test organization's repository
    ``name``. ``git`` is bound to ``clone``; its commands run unauthenticated, and a failure raises
    ``ForgeCommandError``."""
    clone.mkdir()
    _run_git(git=git, arguments=[GIT_INIT])
    _write_clone_credential(clone=clone, token=token)
    _exclude_credentials(clone=clone)
    _run_git(git=git, arguments=[GIT_REMOTE, GIT_REMOTE_ADD, ORIGIN_REMOTE, _origin_url(name=name)])


def _field_argument(*, option: str, field: str, value: str) -> List[str]:
    """A ``call`` body member, ``<option> <field>=<value>``: ``-f`` for text, ``-F`` for a JSON value."""
    return [option, field + PARAMETER_ASSIGNMENT + value]


def _creation_arguments(*, name: str) -> List[str]:
    """D9 step 5's ``call repos/create-in-org --path org=bestehorn-sff-test -f name=<name> -F private=true -F
    auto_init=true``."""
    return [
        CALL_SUBCOMMAND,
        REPOSITORY_CREATION,
        *_path_argument(parameter=ORG_PARAMETER, value=TEST_ORGANIZATION),
        *_field_argument(option=RAW_FIELD_OPTION, field=FIELD_NAME, value=name),
        *_field_argument(option=TYPED_FIELD_OPTION, field=FIELD_PRIVATE, value=TYPED_TRUE),
        *_field_argument(option=TYPED_FIELD_OPTION, field=FIELD_AUTO_INIT, value=TYPED_TRUE),
    ]


def _created_record(*, answer: Any, requested: str) -> CreatedRepository:
    """The record of a creation's printed answer, its ``owner.login``, ``name`` and ``default_branch``; an answer
    without them raises ``ForgeCommandError``."""
    fields: Mapping[str, Any] = answer if isinstance(answer, Mapping) else {}
    owner = fields.get(FIELD_OWNER)
    login = owner.get(FIELD_LOGIN) if isinstance(owner, Mapping) else None
    name = fields.get(FIELD_NAME)
    branch = fields.get(FIELD_DEFAULT_BRANCH)
    if not (isinstance(login, str) and isinstance(name, str) and isinstance(branch, str)):
        raise ForgeCommandError(
            message=(
                f"The creation of {TEST_ORGANIZATION}{FULL_NAME_SEPARATOR}{requested} answered no "
                f"{FIELD_OWNER}.{FIELD_LOGIN}, {FIELD_NAME} and {FIELD_DEFAULT_BRANCH} text"
            )
        )
    return CreatedRepository(owner=login, name=name, default_branch=branch)


def create_ephemeral(*, wrapper: WrapperRunner, name: str) -> CreatedRepository:
    """D9 step 5: creates the test organization's repository ``name``, private, with an initial commit.

    A non-zero exit raises ``ForgeCommandError``: nothing was created. The answer's ``owner.login``, ``name`` and
    ``default_branch`` make the record; an answer whose ``private`` is not true raises ``ForgeSetupError`` whose
    ``details`` keep the record under ``DETAIL_CREATED``, so the teardown still deletes the repository.
    """
    target = TEST_ORGANIZATION + FULL_NAME_SEPARATOR + name
    invocation = wrapper.run(arguments=_creation_arguments(name=name))
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Creating this run's repository {target}", invocation=invocation)
    answer = invocation.json()
    created = _created_record(answer=answer, requested=name)
    logger.info("Created this run's repository %s", created.owner + FULL_NAME_SEPARATOR + created.name)
    private = answer.get(FIELD_PRIVATE)
    if private is not True:
        raise ForgeSetupError(
            message=(
                f"This run's repository {target} was created with {FIELD_PRIVATE} {private!r}, not private; the "
                "teardown deletes it"
            ),
            details={DETAIL_CREATED: created},
        )
    return created


def _kept_record(*, error: ForgeSuiteError) -> Optional[CreatedRepository]:
    """The record a refused creation kept in its ``details`` (``create_ephemeral``), else ``None``."""
    kept = (error.details or {}).get(DETAIL_CREATED)
    return kept if isinstance(kept, CreatedRepository) else None


def _seed_workflows(*, listing: str) -> List[str]:
    """The paths of a ``git ls-tree -r --name-only`` ``listing`` under ``.github/workflows/``; a quoted path is read
    without its opening quote, since the quoting escapes only the unusual characters after the directory part."""
    paths = [line[len(GIT_PATH_QUOTE) :] if line.startswith(GIT_PATH_QUOTE) else line for line in listing.splitlines()]
    return [path for path in paths if path.startswith(WORKFLOW_DIRECTORY)]


def fetch_seed(*, git: GitRunner, default_branch: str) -> Tuple[str, str]:
    """D9 step 6 (D3 "The clone"): an authenticated ``git fetch origin`` and ``git checkout -B <default branch> --track
    origin/<default branch>``, then the seed's commit and tree (``git rev-parse HEAD HEAD^{tree}``), answered in that
    order.

    A seed whose ``git ls-tree -r --name-only HEAD`` names a path under ``.github/workflows/`` raises
    ``ForgeSetupError``; a git failure, or a ``rev-parse`` answering other than two revisions, raises
    ``ForgeCommandError``.
    """
    tracked = ORIGIN_REMOTE + REMOTE_BRANCH_SEPARATOR + default_branch
    _run_git(git=git, arguments=[GIT_FETCH, ORIGIN_REMOTE], authenticated=True)
    _run_git(git=git, arguments=[GIT_CHECKOUT, GIT_RESET_BRANCH_OPTION, default_branch, GIT_TRACK_OPTION, tracked])
    revisions = _run_git(git=git, arguments=[GIT_REV_PARSE, HEAD, HEAD_TREE]).stdout.split()
    if len(revisions) != SEED_REVISION_COUNT:
        raise ForgeCommandError(
            message=(
                f"`{GIT} {GIT_REV_PARSE} {HEAD} {HEAD_TREE}` answered {len(revisions)} revisions, not "
                f"{SEED_REVISION_COUNT}"
            )
        )
    listing = _run_git(git=git, arguments=[GIT_LS_TREE, GIT_RECURSIVE_OPTION, GIT_NAME_ONLY_OPTION, HEAD]).stdout
    workflows = _seed_workflows(listing=listing)
    if workflows:
        raise ForgeSetupError(
            message=(
                f"The seed of this run's repository holds paths under {WORKFLOW_DIRECTORY}, whose workflows a push "
                f"would start: {workflows}"
            )
        )
    return revisions[0], revisions[1]


def _clear_read_only(*, root: Path) -> None:
    """Adds the owner's write permission to ``root`` and to everything under it that is no symbolic link: on Windows
    that clears the read-only attribute git gives its object files, which refuses their removal. A path that cannot be
    changed is passed over; the next removal attempt names what is left."""
    try:
        paths = [root, *root.rglob(pattern="*")]
    except OSError as exc:
        logger.debug("Could not list %s to clear its read-only attributes: %s", root, exc)
        return
    for path in paths:
        try:
            if not path.is_symlink():
                path.chmod(mode=path.stat().st_mode | stat.S_IWRITE)
        except OSError as exc:
            logger.debug("Could not clear the read-only attribute of %s: %s", path, exc)


def remove_tree(*, path: Path) -> None:
    """D9 step 7: removes the directory ``path`` and everything under it; a ``path`` that no longer exists is done.

    A refused removal is retried, up to ``REMOVAL_ATTEMPTS`` attempts ``REMOVAL_PAUSE_SECONDS`` apart, after clearing
    the read-only attribute git gives its object files on Windows; the pause also outlasts a brief "in use by another
    process" lock there. The last refusal raises ``ForgeSuiteError`` naming ``path``.
    """
    for attempt in range(1, REMOVAL_ATTEMPTS + 1):
        if not path.exists():
            return
        try:
            shutil.rmtree(path=path)
            return
        except OSError as exc:
            if attempt == REMOVAL_ATTEMPTS:
                raise ForgeSuiteError(message=f"Could not remove {path} in {REMOVAL_ATTEMPTS} attempts: {exc}") from exc
            logger.debug("Removing %s was refused (%s); retrying", path, exc)
        _clear_read_only(root=path)
        time.sleep(REMOVAL_PAUSE_SECONDS)


@contextmanager
def provision(
    *, checkout: Path, workspace: Path, wrapper: WrapperRunner, git: GitRunner
) -> Iterator[EphemeralRepository]:
    """D9: one run's repository around the ``with`` body; ``wrapper`` and ``git`` are bound to ``<workspace>/clone``.

    1. Before the ``try``, the run id and the repository's name; nothing is sent. 2. The test token,
    ``read_test_token`` of ``find_test_credential(checkout=checkout)``, a local of this function only. 3.
    ``prepare_clone``. 4. ``sweep_leftovers`` at the UTC now, kept as ``swept_at``. 5. ``create_ephemeral``. 6.
    ``fetch_seed``, then the yield of the ``EphemeralRepository``. 7. In the ``finally``, whether a step or the body
    returned or raised: ``delete_ephemeral`` of step 5's record (``None`` when the creation never succeeded, so
    nothing is deleted), then, in its own ``finally``, ``remove_tree`` of ``workspace``; a failure of either is raised.
    """
    run_id = new_run_id()
    name = ephemeral_name(run_id=run_id)
    clone = workspace / CLONE_DIRECTORY
    created: Optional[CreatedRepository] = None
    try:
        token = read_test_token(path=find_test_credential(checkout=checkout))
        prepare_clone(clone=clone, token=token, name=name, git=git)
        # The generator's frame lives on through the yield; the token does not.
        del token
        swept_at = datetime.now(tz=timezone.utc)
        sweep_leftovers(wrapper=wrapper, now=swept_at)
        try:
            record = create_ephemeral(wrapper=wrapper, name=name)
        except ForgeSetupError as refused:
            created = _kept_record(error=refused)
            raise
        created = record
        seed_sha, seed_tree_sha = fetch_seed(git=git, default_branch=record.default_branch)
        yield EphemeralRepository(
            run_id=run_id,
            owner=record.owner,
            name=record.name,
            default_branch=record.default_branch,
            seed_sha=seed_sha,
            seed_tree_sha=seed_tree_sha,
            swept_at=swept_at,
            clone=clone,
            wrapper=wrapper,
            git=git,
        )
    finally:
        try:
            delete_ephemeral(wrapper=wrapper, created=created, run_id=run_id)
        finally:
            remove_tree(path=workspace)
