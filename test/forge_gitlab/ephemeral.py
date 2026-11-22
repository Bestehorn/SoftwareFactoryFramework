"""The GitLab forge suite's support module: what ``test/forge_gitlab/`` runs beside pytest against the test group (D10).

The GitLab forge suite (``test/forge_gitlab/``, run by ``python scripts/run_tests.py --workers 1 test/forge_gitlab``)
drives the product GitLab wrapper against an ephemeral ``sff-test-*`` project of the test group. This module holds the
logic that decides without the forge, so the default collection proves it (``test/test_forge_gitlab_support.py``): the
refusal of a distributed run, naming this suite's command (D1); the per-command git credential helper for gitlab.com,
``CLONE_GIT_HELPER`` (D3); the project path a run id gives (D4); where the GitLab test credential file is found, how
its token is read and how the CI step writes it (D8); the teardown guard and the leftover sweep (D9); and
``provision``, the context manager around one run's project: it reads the test token, prepares the clone, sweeps,
reads the test group, creates and seeds the project, and afterwards deletes it and removes the workspace (D3 "The
clone", D9); and the two helpers the merge-request tests share (D10): ``push_branch``, which pushes a fresh branch with
one new file from the clone, and ``wait_until_checked``, which reads a merge request until GitLab has decided its
mergeability (D6 "Mergeability"). ``SubprocessWrapperRunner`` is the suite's one way out to the product wrapper, with
the test marker and the bytes of its answer kept (D10); the teardown, the sweep and ``provision`` take a
``WrapperRunner``, and ``provision`` a ``GitRunner`` too, so a test gives them doubles; so do ``push_branch`` and
``wait_until_checked``.

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
import json
import logging
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

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
NOT_FOUND_ANSWER = re.compile(pattern=r"\banswered 404\b")
BAD_REQUEST_ANSWER = re.compile(pattern=r"\banswered 400\b")
#: ``mark_for_deletion_base_service.rb``: "#{resource_name.titleize} has already been marked for deletion".
ALREADY_MARKED = "has already been marked for deletion"

# D8 "Reading": the test token's encoding, a byte outside it refused, and the final line ends it is read without,
# ``\r\n`` first; the setup note every refusal of the test credential file points to, #10's.
TOKEN_ENCODING = "ascii"
LINE_END = "\n"
WINDOWS_LINE_END = "\r\n"
TOKEN_LINE_ENDS = (WINDOWS_LINE_END, LINE_END)
SETUP_NOTE = _REUSED.SETUP_NOTE

# D3 "The clone", D8 "Writing": the clone under the workspace, its two credential files, the line its
# ``.git/info/exclude`` gains, the host its ``config/gitlab.json`` names, and its ``origin``.
CLONE_DIRECTORY = "clone"
#: The product GitLab wrapper's credential file, relative to the clone: the only ``config/gitlab.json`` the suite
#: writes (UB-2).
CLONE_CONFIG_FILE = Path("config") / "gitlab.json"
GIT_EXCLUDE_FILE = Path(GIT_METADATA_DIRECTORY) / "info" / "exclude"
#: The line the clone's ``.git/info/exclude`` gains, so no commit of the clone holds its ``config/gitlab.json``.
EXCLUDED_CONFIG = CLONE_CONFIG_FILE.parent.as_posix() + "/"
#: Owner-only where the OS honours it; on Windows only the read-only flag follows a mode (docs.python.org ``os.chmod``).
CLONE_CREDENTIAL_MODE = 0o600
GITLAB_HOSTNAME = "gitlab.com"
ORIGIN_REMOTE = "origin"
#: D3: the test group's project without userinfo, so ``.git/config`` holds no token.
ORIGIN_URL = "https://" + GITLAB_HOSTNAME + "/{full_path}.git"

# D3 "The clone", D9 steps 3 and 7: the git commands that prepare and seed the clone, and the seed's file that would
# start a pipeline (GitLab's default CI configuration file, ``ci_config_path`` unset).
GIT = "git"
GIT_EXIT_OK = 0
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
GIT_NAME_ONLY_OPTION = "--name-only"
HEAD = "HEAD"
HEAD_TREE = "HEAD^{tree}"
SEED_REVISION_COUNT = 2
GITLAB_CI_FILE = ".gitlab-ci.yml"

# D9 steps 5 and 6: the group read (docs.gitlab.com/api/groups/, "Get a single group"; ``with_projects=false`` keeps
# its answer free of the projects' details on API v4, where GitLab has deprecated the parameter for removal in v5) and
# the creation (docs.gitlab.com/api/projects/, "Create a project"), as ``call`` arguments, and the fields of the
# creation's answer the record is made of; ``details`` of the refusal of a project created other than private keep the
# record.
GROUP_READ = "tenant-scale#retrieve-a-group"
QUERY_OPTION = "--query"
WITH_PROJECTS_PARAMETER = "with_projects"
PROJECT_CREATION = "tenant-scale#create-a-project"
RAW_FIELD_OPTION = "-f"
TYPED_FIELD_OPTION = "-F"
FIELD_NAME = "name"
FIELD_NAMESPACE_ID = "namespace_id"
FIELD_VISIBILITY = "visibility"
FIELD_INITIALIZE_WITH_README = "initialize_with_readme"
FIELD_AUTO_DEVOPS_ENABLED = "auto_devops_enabled"
FIELD_DEFAULT_BRANCH = "default_branch"
PRIVATE_VISIBILITY = "private"
TEXT_TRUE = "true"
TEXT_FALSE = "false"
DETAIL_CREATED = "created"

# D10 ``push_branch``: the git commands that make, commit, push and leave one branch of the clone, and its one new file,
# ``forge/<branch>.txt``: a name no other branch gives, outside ``config/`` and ``.git/``, holding a line of text that
# names the branch and no token.
GIT_NEW_BRANCH_OPTION = "-b"
GIT_ADD = "add"
GIT_COMMIT = "commit"
GIT_MESSAGE_OPTION = "-m"
GIT_PATHSPEC_SEPARATOR = "--"
GIT_PUSH = "push"
GIT_SHOW_TOPLEVEL_OPTION = "--show-toplevel"
BRANCH_FILE_DIRECTORY = Path("forge")
BRANCH_FILE_SUFFIX = ".txt"
BRANCH_FILE_TEXT = "The forge suite's file of the branch {branch}." + LINE_END
BRANCH_COMMIT_MESSAGE = "Add the forge suite's file of the branch {branch}"

# D6 "Mergeability", D10 ``wait_until_checked``: the read it repeats, ``mr get <iid>``, which prints the merge request
# record (``gitlab_api/commands/mr.py`` ``get_mr``); the field it judges and the values that mean GitLab has not decided
# the mergeability yet (docs.gitlab.com/api/merge_requests/); the pause between two reads, and the deadline of the
# wait, measured with ``time.monotonic`` from before the first read.
MR_GROUP = "mr"
MR_GET = "get"
FIELD_DETAILED_MERGE_STATUS = "detailed_merge_status"
UNDECIDED_MERGE_STATUSES = ("unchecked", "checking", "preparing", "approvals_syncing")
CHECK_PAUSE_SECONDS = 2.0
CHECK_DEADLINE_SECONDS = 180.0

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
            logger.debug(
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


# ---------------------------------------------------------------------------------------------------------------------
# The test token (D8) and the provision of one run's project (D3 "The clone", D9 steps 1 to 8)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EphemeralProject:
    """The project one run owns, as ``provision`` yields it (D9): the run id; the project's group, path and full path
    (D4), the full path being the ``project_id`` of the clone's ``config/gitlab.json``; its numeric id and default
    branch, as its creation answered them; its seed commit and tree; the moment of the run's sweep (aware UTC); the
    clone; and the two runners bound to the clone. It holds no token, so neither does its ``repr``."""

    run_id: str
    group: str
    path: str
    full_path: str
    project_id: int
    default_branch: str
    seed_sha: str
    seed_tree_sha: str
    swept_at: datetime
    clone: Path
    wrapper: WrapperRunner
    git: GitRunner


def _credential_refusal(*, path: Path, problem: str) -> ForgeSetupError:
    """The refusal of the test credential file ``path`` for ``problem``: it names the file and the setup note, never
    the file's text."""
    return ForgeSetupError(
        message=(
            f"The test credential file {path} {problem}. Paste only the test group's token, on one line, into this "
            f"file ({SETUP_NOTE})"
        )
    )


def _without_final_line_end(*, text: str) -> str:
    """``text`` less one final ``\\r\\n`` or ``\\n``."""
    for line_end in TOKEN_LINE_ENDS:
        if text.endswith(line_end):
            return text[: -len(line_end)]
    return text


def read_test_token(*, path: Path) -> str:
    """D8 "Reading": the token of the test credential file ``path``, refused as the product GitLab wrapper refuses the
    ``token`` of its ``config/gitlab.json``.

    The file's bytes are decoded as ASCII and read less one final ``\\r\\n`` or ``\\n``. A file that cannot be read, a
    byte outside ASCII, an empty text, a text starting with the product's ``PLACEHOLDER_MARKER``, and a text the
    product's ``_refuse_token_characters`` refuses each raise ``ForgeSetupError`` naming ``path`` and none of its
    contents, the cause dropped (``from None``). Nothing logs the token.
    """
    product = product_wrapper()
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise _credential_refusal(path=path, problem=f"cannot be read ({exc.strerror})") from None
    try:
        text = data.decode(encoding=TOKEN_ENCODING)
    except UnicodeDecodeError:
        raise _credential_refusal(path=path, problem="holds a byte outside ASCII") from None
    token = _without_final_line_end(text=text)
    if not token or token.startswith(str(product.PLACEHOLDER_MARKER)):
        raise _credential_refusal(path=path, problem="is empty or still holds the placeholder")
    try:
        product._refuse_token_characters(token=token)
    except product.GitLabAPIError:
        refused = (
            f"holds a character outside '{product.PRINTABLE_FIRST}' to '{product.PRINTABLE_LAST}' (a space, a second "
            "line or an invisible character)"
        )
        raise _credential_refusal(path=path, problem=refused) from None
    return token


def _origin_url(*, path: str) -> str:
    """D3's ``origin`` of the test group's project ``path``: no userinfo, so ``.git/config`` holds no token."""
    return ORIGIN_URL.format(full_path=TEST_GROUP + PROJECT_PATH_SEPARATOR + path)


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


def _write_owner_only(*, path: Path, data: bytes) -> None:
    """D8 "Writing": ``path`` created owner-only (``CLONE_CREDENTIAL_MODE``) and then given ``data``; a file already
    there raises ``FileExistsError``, so none is overwritten."""
    path.touch(mode=CLONE_CREDENTIAL_MODE, exist_ok=False)
    path.write_bytes(data=data)


def _write_clone_config(*, clone: Path, token: str, path: str) -> None:
    """D8 "Writing": the clone's ``config/gitlab.json``, ``json.dumps`` of ``hostname`` gitlab.com, ``project_id`` the
    full path of the test group's project ``path`` and ``token``, keyed by the product's ``FIELD_HOSTNAME``,
    ``FIELD_PROJECT_ID`` and ``FIELD_TOKEN``."""
    product = product_wrapper()
    config = {
        product.FIELD_HOSTNAME: GITLAB_HOSTNAME,
        product.FIELD_PROJECT_ID: TEST_GROUP + PROJECT_PATH_SEPARATOR + path,
        product.FIELD_TOKEN: token,
    }
    target = clone / CLONE_CONFIG_FILE
    target.parent.mkdir()
    _write_owner_only(path=target, data=json.dumps(obj=config).encode(encoding=TEXT_ENCODING))


def _exclude_config(*, clone: Path) -> None:
    """D8 "Writing": appends ``config/`` to the clone's ``.git/info/exclude``, on a line of its own, so no commit of
    the clone holds its ``config/gitlab.json``."""
    exclude = clone / GIT_EXCLUDE_FILE
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_bytes() if exclude.is_file() else b""
    line_end = LINE_END.encode(encoding=TEXT_ENCODING)
    separator = line_end if existing and not existing.endswith(line_end) else b""
    exclude.write_bytes(data=existing + separator + EXCLUDED_CONFIG.encode(encoding=TEXT_ENCODING) + line_end)


def prepare_clone(*, clone: Path, token: str, path: str, git: GitRunner) -> None:
    """D9 step 3 (D3 "The clone"): creates ``clone`` with ``Path.mkdir`` and runs ``git init`` in it, writes its
    ``config/gitlab.json`` and its ``.git/sff-forge-token`` (the token and ``\\n``) and the exclude line (D8), then
    ``git remote add origin`` of the test group's project ``path``. ``git`` is bound to ``clone``; its commands run
    unauthenticated, and a failure raises ``ForgeCommandError``."""
    clone.mkdir()
    _run_git(git=git, arguments=[GIT_INIT])
    _write_clone_config(clone=clone, token=token, path=path)
    _write_owner_only(path=clone / CLONE_GIT_TOKEN_FILE, data=(token + LINE_END).encode(encoding=TEXT_ENCODING))
    _exclude_config(clone=clone)
    _run_git(git=git, arguments=[GIT_REMOTE, GIT_REMOTE_ADD, ORIGIN_REMOTE, _origin_url(path=path)])


def _assignment(*, name: str, value: str) -> str:
    """A ``call`` parameter's ``<name>=<value>``."""
    return name + PARAMETER_ASSIGNMENT + value


def read_test_group(*, wrapper: WrapperRunner) -> int:
    """D9 step 5: the numeric id of the test group, ``call tenant-scale#retrieve-a-group --path id=bestehorn-sff-test
    --query with_projects=false``, which a creation's ``namespace_id`` needs.

    A non-zero exit raises ``ForgeCommandError``; an answer whose ``full_path`` is not ``TEST_GROUP`` or whose ``id`` is
    no integer raises ``ForgeSetupError``.
    """
    invocation = wrapper.run(
        arguments=[
            CALL_SUBCOMMAND,
            GROUP_READ,
            PATH_OPTION,
            _assignment(name=ID_PARAMETER, value=TEST_GROUP),
            QUERY_OPTION,
            _assignment(name=WITH_PROJECTS_PARAMETER, value=TEXT_FALSE),
        ]
    )
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Reading the group {TEST_GROUP}", invocation=invocation)
    answer = invocation.json()
    fields: Mapping[str, Any] = answer if isinstance(answer, Mapping) else {}
    group_id = fields.get(FIELD_ID)
    full_path = fields.get(FIELD_FULL_PATH)
    numbered = isinstance(group_id, int) and not isinstance(group_id, bool)
    if full_path != TEST_GROUP or not numbered:
        raise ForgeSetupError(
            message=(
                f"The read of the group {TEST_GROUP} answered the {FIELD_FULL_PATH} {full_path!r} and the {FIELD_ID} "
                f"{group_id!r}, not {TEST_GROUP} and an integer"
            )
        )
    return int(group_id)


def _creation_arguments(*, group_id: int, path: str) -> List[str]:
    """D9 step 6's ``call tenant-scale#create-a-project -f name=<path> -f path=<path> -F namespace_id=<group id> -f
    visibility=private -F initialize_with_readme=true -F auto_devops_enabled=false``."""
    return [
        CALL_SUBCOMMAND,
        PROJECT_CREATION,
        RAW_FIELD_OPTION,
        _assignment(name=FIELD_NAME, value=path),
        RAW_FIELD_OPTION,
        _assignment(name=FIELD_PATH, value=path),
        TYPED_FIELD_OPTION,
        _assignment(name=FIELD_NAMESPACE_ID, value=str(group_id)),
        RAW_FIELD_OPTION,
        _assignment(name=FIELD_VISIBILITY, value=PRIVATE_VISIBILITY),
        TYPED_FIELD_OPTION,
        _assignment(name=FIELD_INITIALIZE_WITH_README, value=TEXT_TRUE),
        TYPED_FIELD_OPTION,
        _assignment(name=FIELD_AUTO_DEVOPS_ENABLED, value=TEXT_FALSE),
    ]


def _created_record(*, fields: Mapping[str, Any], requested: str) -> CreatedProject:
    """The record of a creation's printed answer ``fields``: its ``id`` (a number), ``namespace.full_path``, ``path``
    and ``default_branch``; an answer without them raises ``ForgeCommandError``."""
    project_id = fields.get(FIELD_ID)
    namespace = fields.get(FIELD_NAMESPACE)
    group = namespace.get(FIELD_FULL_PATH) if isinstance(namespace, Mapping) else None
    path = fields.get(FIELD_PATH)
    branch = fields.get(FIELD_DEFAULT_BRANCH)
    numbered = isinstance(project_id, int) and not isinstance(project_id, bool)
    if not (numbered and isinstance(group, str) and isinstance(path, str) and isinstance(branch, str)):
        raise ForgeCommandError(
            message=(
                f"The creation of {TEST_GROUP}{PROJECT_PATH_SEPARATOR}{requested} answered no {FIELD_ID} number and no "
                f"{FIELD_NAMESPACE}.{FIELD_FULL_PATH}, {FIELD_PATH} and {FIELD_DEFAULT_BRANCH} text"
            )
        )
    return CreatedProject(project_id=int(project_id), namespace=group, path=path, default_branch=branch)


def create_ephemeral(*, wrapper: WrapperRunner, group_id: int, path: str) -> CreatedProject:
    """D9 step 6: creates the test group's project ``path``, private, seeded with a ``README.md``, without Auto
    DevOps.

    A non-zero exit raises ``ForgeCommandError``: nothing was created. The answer's ``id``, ``namespace.full_path``,
    ``path`` and ``default_branch`` make the record; an answer whose ``visibility`` is not ``private`` raises
    ``ForgeSetupError`` whose ``details`` keep the record under ``DETAIL_CREATED``, so the teardown still deletes the
    project.
    """
    target = TEST_GROUP + PROJECT_PATH_SEPARATOR + path
    invocation = wrapper.run(arguments=_creation_arguments(group_id=group_id, path=path))
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Creating this run's project {target}", invocation=invocation)
    answer = invocation.json()
    fields: Mapping[str, Any] = answer if isinstance(answer, Mapping) else {}
    created = _created_record(fields=fields, requested=path)
    logger.info("Created this run's project %s", created.full_path)
    visibility = fields.get(FIELD_VISIBILITY)
    if visibility != PRIVATE_VISIBILITY:
        raise ForgeSetupError(
            message=(
                f"This run's project {created.full_path} was created with {FIELD_VISIBILITY} {visibility!r}, not "
                f"{PRIVATE_VISIBILITY}; the teardown deletes it"
            ),
            details={DETAIL_CREATED: created},
        )
    return created


def _kept_record(*, error: ForgeSuiteError) -> Optional[CreatedProject]:
    """The record a refused creation kept in its ``details`` (``create_ephemeral``), else ``None``."""
    kept = (error.details or {}).get(DETAIL_CREATED)
    return kept if isinstance(kept, CreatedProject) else None


def fetch_seed(*, git: GitRunner, default_branch: str) -> Tuple[str, str]:
    """D9 step 7 (D3 "The clone"): an authenticated ``git fetch origin`` and ``git checkout -B <default branch> --track
    origin/<default branch>``, then the seed's commit and tree (``git rev-parse HEAD HEAD^{tree}``), answered in that
    order.

    A seed whose root, ``git ls-tree --name-only HEAD``, holds ``.gitlab-ci.yml`` raises ``ForgeSetupError``; a git
    failure, or a ``rev-parse`` answering other than two revisions, raises ``ForgeCommandError``.
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
    root = _run_git(git=git, arguments=[GIT_LS_TREE, GIT_NAME_ONLY_OPTION, HEAD]).stdout.splitlines()
    if GITLAB_CI_FILE in root:
        raise ForgeSetupError(
            message=(
                f"The seed of this run's project holds {GITLAB_CI_FILE} at its root, whose pipeline a push would run"
            )
        )
    return revisions[0], revisions[1]


@contextmanager
def provision(*, checkout: Path, workspace: Path, wrapper: WrapperRunner, git: GitRunner) -> Iterator[EphemeralProject]:
    """D9: one run's project around the ``with`` body; ``wrapper`` and ``git`` are bound to ``<workspace>/clone``.

    1. Before the ``try``, the run id, the project's path and full path; nothing is sent. 2. The test token,
    ``read_test_token`` of ``find_test_credential(checkout=checkout, credential_file=TEST_CREDENTIAL_FILE)``, a local
    of this function only, deleted once ``prepare_clone`` returns or raises. 3. ``prepare_clone``. 4.
    ``sweep_leftovers`` at the UTC now, kept as ``swept_at``. 5. ``read_test_group``. 6. ``create_ephemeral``. 7.
    ``fetch_seed``, then the yield of the ``EphemeralProject``. 8. In the ``finally``, whether a step or the body
    returned or raised: ``delete_ephemeral`` of step 6's record (``None`` when the creation never succeeded, so nothing
    is deleted), then, in its own ``finally``, ``remove_tree`` of ``workspace``; a failure of either is raised.
    """
    run_id = new_run_id()
    path = ephemeral_path(run_id=run_id)
    full_path = ephemeral_full_path(run_id=run_id)
    clone = workspace / CLONE_DIRECTORY
    created: Optional[CreatedProject] = None
    try:
        token = read_test_token(path=find_test_credential(checkout=checkout, credential_file=TEST_CREDENTIAL_FILE))
        try:
            prepare_clone(clone=clone, token=token, path=path, git=git)
        finally:
            # The generator's frame lives on through the yield; the token does not.
            del token
        swept_at = datetime.now(tz=timezone.utc)
        sweep_leftovers(wrapper=wrapper, now=swept_at)
        group_id = read_test_group(wrapper=wrapper)
        try:
            record = create_ephemeral(wrapper=wrapper, group_id=group_id, path=path)
        except ForgeSetupError as refused:
            created = _kept_record(error=refused)
            raise
        created = record
        seed_sha, seed_tree_sha = fetch_seed(git=git, default_branch=record.default_branch)
        yield EphemeralProject(
            run_id=run_id,
            group=TEST_GROUP,
            path=path,
            full_path=full_path,
            project_id=record.project_id,
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


# ---------------------------------------------------------------------------------------------------------------------
# The pushed branch and the mergeability wait of the merge-request tests (D10, D6 "Mergeability")
# ---------------------------------------------------------------------------------------------------------------------


def _branch_file(*, branch: str) -> Path:
    """D10: the one new file of ``branch``, relative to the clone: ``forge/<branch>.txt``."""
    return BRANCH_FILE_DIRECTORY / (branch + BRANCH_FILE_SUFFIX)


def _working_tree(*, git: GitRunner) -> Path:
    """The working tree ``git`` is bound to, as ``git rev-parse --show-toplevel`` answers it; a git failure, or an
    empty answer, raises ``ForgeCommandError``."""
    answer = _run_git(git=git, arguments=[GIT_REV_PARSE, GIT_SHOW_TOPLEVEL_OPTION]).stdout.strip()
    if not answer:
        raise ForgeCommandError(message=f"`{GIT} {GIT_REV_PARSE} {GIT_SHOW_TOPLEVEL_OPTION}` answered no working tree")
    return Path(answer)


def push_branch(*, git: GitRunner, default_branch: str, branch: str) -> str:
    """D10: pushes ``branch``, made from ``default_branch`` with one new file, and answers its commit's SHA.

    ``git checkout -b <branch> <default branch>``; the file ``forge/<branch>.txt`` (``_branch_file``) written in the
    working tree, added and committed by name, never with ``git add -A``; the commit's SHA, ``git rev-parse HEAD``; an
    authenticated ``git push origin <branch>``; then, in a ``finally``, ``git checkout <default branch>``, so the clone
    is back on the default branch even when a step failed. Every git command runs through ``git``, bound to the clone;
    an exit other than 0 raises ``ForgeCommandError`` naming the command, which never holds the token.
    """
    _run_git(git=git, arguments=[GIT_CHECKOUT, GIT_NEW_BRANCH_OPTION, branch, default_branch])
    try:
        relative = _branch_file(branch=branch)
        target = _working_tree(git=git) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data=BRANCH_FILE_TEXT.format(branch=branch).encode(encoding=TEXT_ENCODING))
        named = relative.as_posix()
        message = BRANCH_COMMIT_MESSAGE.format(branch=branch)
        _run_git(git=git, arguments=[GIT_ADD, GIT_PATHSPEC_SEPARATOR, named])
        _run_git(git=git, arguments=[GIT_COMMIT, GIT_MESSAGE_OPTION, message, GIT_PATHSPEC_SEPARATOR, named])
        pushed = _run_git(git=git, arguments=[GIT_REV_PARSE, HEAD]).stdout.strip()
        _run_git(git=git, arguments=[GIT_PUSH, ORIGIN_REMOTE, branch], authenticated=True)
    finally:
        _run_git(git=git, arguments=[GIT_CHECKOUT, default_branch])
    logger.info("Pushed the branch %s at %s", branch, pushed)
    return pushed


def _merge_request(*, wrapper: WrapperRunner, iid: int) -> Mapping[str, Any]:
    """One read of the merge request ``iid``, ``mr get <iid>``: the record it printed. A non-zero exit, or an answer
    that is no JSON object, raises ``ForgeCommandError``."""
    invocation = wrapper.run(arguments=[MR_GROUP, MR_GET, str(iid)])
    if invocation.returncode != WRAPPER_EXIT_OK:
        raise _failure(action=f"Reading the merge request !{iid}", invocation=invocation)
    answer = invocation.json()
    if not isinstance(answer, Mapping):
        raise ForgeCommandError(message=f"`{MR_GROUP} {MR_GET} {iid}` printed no JSON object")
    return answer


def wait_until_checked(*, wrapper: WrapperRunner, iid: int) -> Mapping[str, Any]:
    """D10: reads the merge request ``iid`` with ``mr get <iid>`` until its ``detailed_merge_status`` is none of
    ``UNDECIDED_MERGE_STATUSES``, and answers that last record.

    GitLab checks a merge request's mergeability asynchronously when it is read (D6 "Mergeability"), so the reads are
    ``CHECK_PAUSE_SECONDS`` apart (``time.sleep``), and a status still undecided ``CHECK_DEADLINE_SECONDS`` after the
    first read began (``time.monotonic``) raises ``ForgeCommandError`` naming it. A failed read raises
    ``ForgeCommandError`` (``_merge_request``).
    """
    deadline = time.monotonic() + CHECK_DEADLINE_SECONDS
    while True:
        record = _merge_request(wrapper=wrapper, iid=iid)
        status = record.get(FIELD_DETAILED_MERGE_STATUS)
        if status not in UNDECIDED_MERGE_STATUSES:
            logger.info("Merge request !%s is checked: its %s is %r", iid, FIELD_DETAILED_MERGE_STATUS, status)
            return record
        if time.monotonic() >= deadline:
            raise ForgeCommandError(
                message=(
                    f"Merge request !{iid} still has the {FIELD_DETAILED_MERGE_STATUS} {status!r} "
                    f"{CHECK_DEADLINE_SECONDS:g} seconds after the first read: GitLab has not decided its mergeability"
                )
            )
        logger.debug("Merge request !%s has the %s %r; reading it again", iid, FIELD_DETAILED_MERGE_STATUS, status)
        time.sleep(CHECK_PAUSE_SECONDS)
