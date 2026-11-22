"""The GitLab forge suite's support module: what ``test/forge_gitlab/`` runs beside pytest against the test group (D10).

The GitLab forge suite (``test/forge_gitlab/``, run by ``python scripts/run_tests.py --workers 1 test/forge_gitlab``)
drives the product GitLab wrapper against an ephemeral ``sff-test-*`` project of the test group. This module holds the
logic that decides without the forge, so the default collection proves it (``test/test_forge_gitlab_support.py``): the
refusal of a distributed run, naming this suite's command (D1); the per-command git credential helper for gitlab.com,
``CLONE_GIT_HELPER`` (D3); the project path a run id gives (D4); where the GitLab test credential file is found and how
the CI step writes it (D8); the teardown guard and the leftover sweep (D9). ``SubprocessWrapperRunner`` is the suite's
one way out to the product wrapper, with the test marker and the bytes of its answer kept (D10); the teardown and the
sweep take a ``WrapperRunner``, so a test gives them a double.

What issue #10 settled is reused, not copied (design.md Overview): ``test/forge/ephemeral.py`` is loaded by path under
its own ``sys.modules`` key ``forge_ephemeral``, with the reuse rule of ``test/forge/conftest.py`` ``_load_ephemeral``,
and its symbols are bound here under their own names. Its keyword-only parameters are given this suite's constants:
here by ``refuse_distributed_run``, ``CLONE_GIT_HELPER`` and ``product_wrapper``, and by the callers of
``find_test_credential`` (``credential_file=TEST_CREDENTIAL_FILE``), ``write_test_credential``
(``credential_file=TEST_CREDENTIAL_FILE, secret_name=SECRET_NAME``) and ``SubprocessGitRunner``
(``helper=CLONE_GIT_HELPER``), whose defaults stay the GitHub suite's.

Loaded by path, never imported by name and never collected: its name matches neither the default ``python_files`` nor
the suite's ``forge_*.py``, and under ``--import-mode=importlib`` a test directory's utility module is not importable.
At module level it imports only the standard library and loads ``test/forge/ephemeral.py``, which runs only its own
standard-library imports and constants, so no ``sys.path`` changes; the product GitLab wrapper, whose constants it
reads, is loaded by path on first use (``product_wrapper``). No function logs or prints a token.
"""

from __future__ import annotations

import functools
import importlib.util
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

# Overview: #10's support module, in the sibling directory ``test/forge/``, and the fixed ``sys.modules`` key of its
# by-path load, the key ``test/forge/conftest.py`` and ``test/test_forge_support.py`` load it under too, so one process
# holds one copy of it and one family of its exception classes.
REUSED_PATH = Path(__file__).resolve().parents[1] / "forge" / "ephemeral.py"
REUSED_MODULE = "forge_ephemeral"


def _load_reused() -> ModuleType:
    """``test/forge/ephemeral.py``, loaded by path once per process and reused while ``sys.modules`` holds an entry
    whose ``__file__`` resolves to it (the rule of ``test/forge/conftest.py`` ``_load_ephemeral``); it is registered
    there before it runs, so its dataclasses resolve their module, and taken off again when it raises. A file that
    cannot be loaded raises ``ImportError``."""
    loaded = sys.modules.get(REUSED_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == REUSED_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=REUSED_MODULE, location=REUSED_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"The forge suite's support module {REUSED_PATH} cannot be loaded",
            name=REUSED_MODULE,
            path=str(REUSED_PATH),
        )
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[REUSED_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(REUSED_MODULE, None)
        raise
    return module


_REUSED = _load_reused()

# Overview: the symbols reused as settled, bound under their names. ``ForgeSetupError`` and its siblings are
# ``ForgeSuiteError``s; ``find_test_credential`` and ``write_test_credential`` keep their keyword-only parameters.
ForgeSuiteError = _REUSED.ForgeSuiteError
ForgeSetupError = _REUSED.ForgeSetupError
ForgeCommandError = _REUSED.ForgeCommandError
ForgeTeardownRefusedError = _REUSED.ForgeTeardownRefusedError
ForgeSweepRefusedError = _REUSED.ForgeSweepRefusedError
Invocation = _REUSED.Invocation
WrapperRunner = _REUSED.WrapperRunner
GitRunner = _REUSED.GitRunner
SubprocessGitRunner = _REUSED.SubprocessGitRunner
new_run_id = _REUSED.new_run_id
main_working_tree = _REUSED.main_working_tree
remove_tree = _REUSED.remove_tree
find_test_credential = _REUSED.find_test_credential
write_test_credential = _REUSED.write_test_credential
COMMIT_IDENTITY = _REUSED.COMMIT_IDENTITY
CONTROLLER_WORKER_ID = _REUSED.CONTROLLER_WORKER_ID
LEFTOVER_AGE = _REUSED.LEFTOVER_AGE
SUBPROCESS_TIMEOUT_SECONDS = _REUSED.SUBPROCESS_TIMEOUT_SECONDS

# D1: the GitLab forge suite's one-process command, which the refusal of a distributed run names.
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"

# D3: #10's helper, set under the gitlab.com key. GitLab does not validate the username of a personal access token over
# HTTPS (docs.gitlab.com/user/profile/personal_access_tokens/); the token is read from a file inside the clone's
# ``.git/``, since the clone's ``config/gitlab.json`` is JSON, which the helper's shell built-ins do not parse.
GITLAB_HELPER_KEY = "credential.https://gitlab.com.helper"
GIT_USERNAME = "sff-forge-suite"
GIT_METADATA_DIRECTORY = ".git"
#: The clone's git token file, relative to the clone: the token and a line end.
CLONE_GIT_TOKEN_FILE = Path(GIT_METADATA_DIRECTORY) / "sff-forge-token"

# D4, D5: the test group, the one place the suite names it, and the separator of a project's full path.
TEST_GROUP = "bestehorn-sff-test"
PROJECT_PATH_SEPARATOR = "/"

# D8: the credential file, relative to a working tree, and the secret the CI step writes it from.
CREDENTIALS_DIRECTORY = Path("credentials")
#: The operator's test token for the test group, git-ignored like every file of ``credentials/``.
TEST_CREDENTIAL_FILE = CREDENTIALS_DIRECTORY / "gitlab-sff-testing-pat.txt"
SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret

#: D8: the working tree holding the suite, the repository root above ``test/forge_gitlab/``: the ``checkout`` whose test
#: credential file a run reads.
CHECKOUT = Path(__file__).resolve().parents[2]
# D10: the product entry script the suite starts, an absolute resolved path as #10's ``product_wrapper`` compares it,
# and the fixed ``sys.modules`` key of its by-path load, whose constants this module reads rather than redefines.
PRODUCT_WRAPPER = CHECKOUT / "src" / "payload" / "scripts" / "gitlab_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_gitlab_product_wrapper"
# D10: the interpreter option the test marker is given with, and how the runner decodes the two streams it captures as
# bytes: the standard output so that its ``surrogateescape`` encoding is the exact bytes the wrapper wrote, the
# standard error so that any byte still reads.
INTERPRETER_OPTION = "-X"
TEXT_ENCODING = "utf-8"
STDOUT_ERRORS = "surrogateescape"
STDERR_ERRORS = "replace"

# D9: the records the teardown and the sweep send, as ``call`` arguments, and the fields of a listed project
# (docs.gitlab.com/api/groups/, "List projects").
CALL_SUBCOMMAND = "call"
PROJECT_DELETION = "tenant-scale#delete-a-project"
PROJECT_LISTING = "tenant-scale#list-projects"
PATH_OPTION = "--path"
ID_PARAMETER = "id"
PARAMETER_ASSIGNMENT = "="
FIELD_ID = "id"
FIELD_NAMESPACE = "namespace"
FIELD_FULL_PATH = "full_path"
FIELD_PATH = "path"
FIELD_CREATED_AT = "created_at"
FIELD_MARKED_FOR_DELETION_ON = "marked_for_deletion_on"
#: ``created_at`` in ISO 8601, with a fraction of a second or without; ``%z`` reads a final ``Z`` as UTC.
CREATED_AT_FORMATS = ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z")
WRAPPER_EXIT_OK = 0
#: The product GitLab wrapper's exit on a ``GitLabAPIError``; its standard error then carries ``Transport._send``'s
#: ``"{method} {url} answered {status}: {error_text}"``, logged by ``main`` ``_report``.
WRAPPER_API_FAILURE = 1
#: A project a concurrent run's sweep marked, which renamed it, so its old path answers 404.
NOT_FOUND_ANSWER = re.compile(r"\banswered 404\b")
BAD_REQUEST_ANSWER = re.compile(r"\banswered 400\b")
#: ``mark_for_deletion_base_service.rb``: "#{resource_name.titleize} has already been marked for deletion".
ALREADY_MARKED = "has already been marked for deletion"

#: D3, D10: the global git options that make one git command authenticate to gitlab.com as ``GIT_USERNAME`` with the
#: token of the clone's ``CLONE_GIT_TOKEN_FILE``, called as ``CLONE_GIT_HELPER(clone=<clone>)``: #10's
#: ``credential_helper_arguments`` with its other three keywords bound. A clone path holding ``'`` raises
#: ``ForgeSetupError``. ``SubprocessGitRunner`` is given it as ``helper``.
CLONE_GIT_HELPER = functools.partial(
    _REUSED.credential_helper_arguments,
    helper_key=GITLAB_HELPER_KEY,
    username=GIT_USERNAME,
    credential_file=CLONE_GIT_TOKEN_FILE,
)


def refuse_distributed_run(*, worker_id: str) -> None:
    """D1: raises ``ForgeSetupError`` unless ``worker_id`` (xdist's fixture) is ``master``, since a session fixture
    runs once per xdist worker and each would create its own project: #10's refusal, its message naming
    ``GITLAB_FORGE_COMMAND``."""
    _REUSED.refuse_distributed_run(worker_id=worker_id, command=GITLAB_FORGE_COMMAND)


def product_wrapper() -> ModuleType:
    """D10: the product GitLab wrapper ``PRODUCT_WRAPPER``, loaded by #10's ``product_wrapper`` under the
    ``sys.modules`` key ``PRODUCT_WRAPPER_MODULE`` on first use and reused while ``sys.modules`` holds it there.

    Never loaded at import, so loading this module changes no ``sys.path``; the directory the wrapper puts on
    ``sys.path`` for its package is taken off again once it is loaded. A missing script raises ``ForgeSetupError``.
    """
    module: ModuleType = _REUSED.product_wrapper(path=PRODUCT_WRAPPER, module_name=PRODUCT_WRAPPER_MODULE)
    return module


def _ephemeral_prefix() -> str:
    """The product wrapper's ``EPHEMERAL_PROJECT_PREFIX``, the prefix of every path its guard serves (D2)."""
    return str(product_wrapper().EPHEMERAL_PROJECT_PREFIX)


def ephemeral_path(*, run_id: str) -> str:
    """D4: the path of the run's project, the product wrapper's ``EPHEMERAL_PROJECT_PREFIX`` then ``run_id``."""
    return _ephemeral_prefix() + run_id


def ephemeral_full_path(*, run_id: str) -> str:
    """D4: the full path of the run's project, ``TEST_GROUP``, ``/``, then ``ephemeral_path(run_id=run_id)``: the
    ``<namespace>/sff-test-*`` path the product wrapper's guard serves while the test marker is set (D2)."""
    return TEST_GROUP + PROJECT_PATH_SEPARATOR + ephemeral_path(run_id=run_id)


# ---------------------------------------------------------------------------------------------------------------------
# The wrapper runner and the records (D10, D9)
# ---------------------------------------------------------------------------------------------------------------------


class SubprocessWrapperRunner(WrapperRunner):
    """D10: the one place the suite starts the product GitLab wrapper: this interpreter, the test marker ``-X
    <TEST_MARKER_OPTION>``, ``PRODUCT_WRAPPER`` and the arguments, in ``directory`` (the clone, whose
    ``config/gitlab.json`` names the project every record targets), as a list, never through a shell, with no standard
    input and no ``env``.

    Both streams are captured as bytes. The standard output is decoded as UTF-8 with ``surrogateescape``, so
    ``Invocation.stdout.encode(encoding="utf-8", errors="surrogateescape")`` gives back the exact bytes the wrapper
    wrote, an archive ``print_bytes`` wrote included; the standard error is decoded with ``replace``. A process that
    cannot start, or outlives ``SUBPROCESS_TIMEOUT_SECONDS``, raises ``ForgeCommandError``.
    """

    def __init__(self, *, directory: Path) -> None:
        self.directory = directory

    def run(self, *, arguments: Sequence[str]) -> Invocation:
        marker = str(product_wrapper().TEST_MARKER_OPTION)
        argv = [sys.executable, INTERPRETER_OPTION, marker, str(PRODUCT_WRAPPER), *arguments]
        try:
            completed = subprocess.run(
                args=argv,
                cwd=self.directory,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ForgeCommandError(message=f"`{' '.join(argv)}` could not run in {self.directory}: {exc}") from exc
        return Invocation(
            returncode=completed.returncode,
            stdout=completed.stdout.decode(encoding=TEXT_ENCODING, errors=STDOUT_ERRORS),
            stderr=completed.stderr.decode(encoding=TEXT_ENCODING, errors=STDERR_ERRORS),
        )


@dataclass(frozen=True)
class CreatedProject:
    """The project this run's creation answered with (D9 step 6), the one the teardown may delete: its ``id``, its
    ``namespace.full_path``, its ``path`` and its ``default_branch``."""

    project_id: int
    namespace: str
    path: str
    default_branch: str

    @property
    def full_path(self) -> str:
        return self.namespace + PROJECT_PATH_SEPARATOR + self.path


def _created_at(*, text: str, full_path: str) -> datetime:
    """A listed project's ``created_at`` ``text`` as aware UTC: ISO 8601, a fraction of a second allowed, a final ``Z``
    read as UTC; another form raises ``ForgeCommandError`` naming the project ``full_path``."""
    for form in CREATED_AT_FORMATS:
        try:
            return datetime.strptime(text, form).astimezone(tz=timezone.utc)
        except ValueError:
            continue
    raise ForgeCommandError(
        message=(
            f"The listed project {full_path} has a {FIELD_CREATED_AT} that is no ISO 8601 time with a final Z or an "
            f"offset: {text!r}"
        )
    )


@dataclass(frozen=True)
class ProjectRecord:
    """One project of the test group's listing, as the sweep judges it: ``created_at`` is aware UTC, and
    ``marked_for_deletion_on`` is ``None`` unless GitLab has already scheduled the project for deletion."""

    project_id: int
    namespace: str
    path: str
    created_at: datetime
    marked_for_deletion_on: Optional[str]

    @property
    def full_path(self) -> str:
        return self.namespace + PROJECT_PATH_SEPARATOR + self.path

    @property
    def scheduled(self) -> bool:
        """Whether GitLab has already scheduled the project for deletion (AC-3.3)."""
        return self.marked_for_deletion_on is not None

    @classmethod
    def of(cls, *, item: Mapping[str, Any]) -> ProjectRecord:
        """The record of one listed item: its ``id`` (a number), ``namespace.full_path``, ``path`` and ``created_at``
        (``_created_at``), and its ``marked_for_deletion_on``, which absent or null means not scheduled. An item
        without the first four raises ``ForgeCommandError``."""
        project_id = item.get(FIELD_ID)
        namespace = item.get(FIELD_NAMESPACE)
        group = namespace.get(FIELD_FULL_PATH) if isinstance(namespace, Mapping) else None
        path = item.get(FIELD_PATH)
        created = item.get(FIELD_CREATED_AT)
        numbered = isinstance(project_id, int) and not isinstance(project_id, bool)
        if not (numbered and isinstance(group, str) and isinstance(path, str) and isinstance(created, str)):
            raise ForgeCommandError(
                message=(
                    f"A listed project holds no {FIELD_ID} number and no {FIELD_NAMESPACE}.{FIELD_FULL_PATH}, "
                    f"{FIELD_PATH} and {FIELD_CREATED_AT} text; its fields are {sorted(item)}"
                )
            )
        marked = item.get(FIELD_MARKED_FOR_DELETION_ON)
        return cls(
            project_id=project_id,
            namespace=group,
            path=path,
            created_at=_created_at(text=created, full_path=group + PROJECT_PATH_SEPARATOR + path),
            marked_for_deletion_on=None if marked is None else str(marked),
        )


# ---------------------------------------------------------------------------------------------------------------------
# The two deletion paths (D9 "The teardown guard", "The sweep")
# ---------------------------------------------------------------------------------------------------------------------


def _deletion_arguments(*, full_path: str) -> List[str]:
    """D9's ``call tenant-scale#delete-a-project --path id=<namespace>/<path>``."""
    return [CALL_SUBCOMMAND, PROJECT_DELETION, PATH_OPTION, ID_PARAMETER + PARAMETER_ASSIGNMENT + full_path]


def _failure(*, action: str, invocation: Invocation) -> ForgeCommandError:
    """The error of a wrapper invocation that exited with a failure: ``action``, the exit code and its standard
    error."""
    return ForgeCommandError(
        message=(
            f"{action} failed: the product GitLab wrapper exited {invocation.returncode}: {invocation.stderr.strip()}"
        )
    )


def delete_ephemeral(*, wrapper: WrapperRunner, created: Optional[CreatedProject], run_id: str) -> None:
    """D9 step 8, the teardown guard: deletes the project this run created, and only it.

    ``created`` is ``None`` when the creation never succeeded: nothing is sent (AC-2.3). A record whose
    ``(namespace, path)`` is not ``(TEST_GROUP, ephemeral_path(run_id=run_id))`` raises ``ForgeTeardownRefusedError``
    naming it and this run's project, nothing sent (AC-2.2). Otherwise one ``call tenant-scale#delete-a-project``
    is sent, which gitlab.com answers by marking the project for deletion; a non-zero exit raises ``ForgeCommandError``
    naming the target (AC-2.1).
    """
    if created is None:
        logger.info("This run created no project; the teardown deletes nothing")
        return
    own = ephemeral_path(run_id=run_id)
    if (created.namespace, created.path) != (TEST_GROUP, own):
        raise ForgeTeardownRefusedError(
            message=(
                f"The teardown refuses to delete {created.full_path}: this run's project is "
                f"{TEST_GROUP}{PROJECT_PATH_SEPARATOR}{own}; nothing was sent"
            )
        )
    invocation = wrapper.run(arguments=_deletion_arguments(full_path=created.full_path))
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Deleting this run's project {created.full_path}", invocation=invocation)
    logger.info("Deleted this run's project %s (marked for deletion)", created.full_path)


def _listed_records(*, invocation: Invocation) -> List[ProjectRecord]:
    """The records of a listing's printed JSON array; anything but an array of objects raises
    ``ForgeCommandError``."""
    listed = invocation.json()
    if not isinstance(listed, list) or not all(isinstance(item, Mapping) for item in listed):
        raise ForgeCommandError(message=f"The listing of {TEST_GROUP} printed no array of projects")
    return [ProjectRecord.of(item=item) for item in listed]


def list_group_projects(*, wrapper: WrapperRunner) -> List[ProjectRecord]:
    """D9 "The sweep": the test group's projects, ``call tenant-scale#list-projects --path id=bestehorn-sff-test``
    (``call`` reads every page), each item's ``ProjectRecord.of``. No ``active`` filter, so an archived project and
    one marked for deletion are listed too; a non-zero exit raises ``ForgeCommandError``."""
    invocation = wrapper.run(
        arguments=[CALL_SUBCOMMAND, PROJECT_LISTING, PATH_OPTION, ID_PARAMETER + PARAMETER_ASSIGNMENT + TEST_GROUP]
    )
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Listing the projects of {TEST_GROUP}", invocation=invocation)
    return _listed_records(invocation=invocation)


def is_leftover(*, record: ProjectRecord, now: datetime) -> bool:
    """D9: whether ``record``'s namespace is ``TEST_GROUP``, its path starts with the product's
    ``EPHEMERAL_PROJECT_PREFIX``, and it was created more than ``LEFTOVER_AGE`` before ``now`` (aware UTC); a day old
    or less is kept. Whether GitLab has scheduled it for deletion is not judged here."""
    return (
        record.namespace == TEST_GROUP
        and record.path.startswith(_ephemeral_prefix())
        and now - record.created_at > LEFTOVER_AGE
    )


def select_leftovers(*, records: Iterable[ProjectRecord], now: datetime) -> List[ProjectRecord]:
    """D9: exactly the records of ``records`` that ``is_leftover`` at ``now``, in their order."""
    return [record for record in records if is_leftover(record=record, now=now)]


def sweep_leftovers(*, wrapper: WrapperRunner, now: datetime) -> None:
    """D9 step 4: lists the test group's projects (``list_group_projects``), then, for each leftover at ``now``, logs
    one GitLab has already scheduled for deletion and sends nothing for it (AC-3.3), and deletes any other with
    ``delete_leftover``."""
    for record in select_leftovers(records=list_group_projects(wrapper=wrapper), now=now):
        if record.scheduled:
            logger.info(
                "The leftover project %s is already marked for deletion (on %s); the sweep sends nothing",
                record.full_path,
                record.marked_for_deletion_on,
            )
            continue
        delete_leftover(wrapper=wrapper, record=record, now=now)


def _already_handled(*, invocation: Invocation) -> bool:
    """Whether a deletion's failure means the project is gone or marked already: exit 1 with standard error holding
    ``answered 404`` (a concurrent run's sweep marked it, which renamed it), or ``answered 400`` and ``has already been
    marked for deletion``."""
    if invocation.returncode != WRAPPER_API_FAILURE:
        return False
    stderr = invocation.stderr
    if NOT_FOUND_ANSWER.search(string=stderr):
        return True
    return BAD_REQUEST_ANSWER.search(string=stderr) is not None and ALREADY_MARKED in stderr


def delete_leftover(*, wrapper: WrapperRunner, record: ProjectRecord, now: datetime) -> None:
    """D9: deletes one leftover with ``call tenant-scale#delete-a-project --path id=<namespace>/<path>``.

    A record that is no leftover at ``now``, or that GitLab has already scheduled for deletion, raises
    ``ForgeSweepRefusedError`` naming it, nothing sent. A failure ``_already_handled`` judges so counts as handled;
    any other raises ``ForgeCommandError``.
    """
    if record.scheduled:
        raise ForgeSweepRefusedError(
            message=(
                f"The sweep refuses to delete {record.full_path}: GitLab marked it for deletion on "
                f"{record.marked_for_deletion_on}; nothing was sent"
            )
        )
    if not is_leftover(record=record, now=now):
        raise ForgeSweepRefusedError(
            message=(
                f"The sweep refuses to delete {record.full_path}: it is no {TEST_GROUP} project whose path starts "
                f"{_ephemeral_prefix()} and created more than {LEFTOVER_AGE} before {now.isoformat()}; nothing was "
                "sent"
            )
        )
    invocation = wrapper.run(arguments=_deletion_arguments(full_path=record.full_path))
    if invocation.returncode == WRAPPER_EXIT_OK:
        logger.info("Deleted the leftover project %s, created %s", record.full_path, record.created_at.isoformat())
        return
    if _already_handled(invocation=invocation):
        logger.info("The leftover project %s was already deleted or marked for deletion", record.full_path)
        return
    raise _failure(action=f"Deleting the leftover project {record.full_path}", invocation=invocation)
