"""The forge suite's support module: what ``test/forge/`` runs beside pytest against the test organization (D10).

The forge suite (``test/forge/``, run by ``python scripts/run_tests.py --workers 1 test/forge``) drives the product
wrapper against an ephemeral ``sff-test-*`` repository of the test organization. This module holds the logic that
decides without the forge, so the default collection proves it (``test/test_forge_support.py``): the refusal of a
distributed run (D1), the per-command git credential helper (D3), and where the test credential file is found and how
the CI step writes it (D8).

Loaded by path, never imported by name and never collected: its name matches neither the default ``python_files`` nor
the suite's ``forge_*.py``, and under ``--import-mode=importlib`` a test directory's utility module is not importable.
It imports only the standard library at module level. No function logs or prints a token.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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
