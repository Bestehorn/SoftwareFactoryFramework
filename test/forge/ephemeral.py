"""The forge suite's support module: what ``test/forge/`` runs beside pytest against the test organization (D10).

The forge suite (``test/forge/``, run by ``python scripts/run_tests.py --workers 1 test/forge``) drives the product
wrapper against an ephemeral ``sff-test-*`` repository of the test organization. This module holds the logic that
decides without the forge, so the default collection proves it (``test/test_forge_support.py``): the refusal of a
distributed run (D1), the per-command git credential helper (D3), the run id and the repository name it gives (D4),
where the test credential file is found and how the CI step writes it (D8), the teardown guard and the leftover sweep
(D9). The runners are its one way out to a process (D10): ``SubprocessWrapperRunner`` starts the product wrapper with
the test marker, ``SubprocessGitRunner`` starts git, and the logic above takes a ``WrapperRunner`` or ``GitRunner``, so
a test gives it a double.

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
import subprocess
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

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

# D10: the product entry script the suite starts, and the fixed ``sys.modules`` key of its by-path load, whose
# ``TEST_MARKER_OPTION`` and ``EPHEMERAL_REPOSITORY_PREFIX`` this module reads rather than redefines.
PRODUCT_WRAPPER = Path(__file__).resolve().parents[2] / "src" / "payload" / "scripts" / "github_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_product_wrapper"
INTERPRETER_OPTION = "-X"
# D3, D10: every git command's working tree option and the suite's commit identity (a runner has no global one).
GIT_DIRECTORY_OPTION = "-C"
COMMIT_USER_NAME = "SFF Forge Suite"
COMMIT_USER_EMAIL = "forge-suite@example.invalid"
COMMIT_IDENTITY = (
    CONFIG_OPTION,
    f"user.name{CONFIG_ASSIGNMENT}{COMMIT_USER_NAME}",
    CONFIG_OPTION,
    f"user.email{CONFIG_ASSIGNMENT}{COMMIT_USER_EMAIL}",
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
            "checkout's file (credentials/README.md)"
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
