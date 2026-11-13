"""F:fixture: the run's own repository, as the session fixture made it (issue #10, design.md D6, D9; AC-1.1, AC-1.3,
AC-3.1).

Every other forge module stands on ``ephemeral_repository`` (``test/forge/conftest.py``, session scope): it swept the
test organization's leftovers, created one private repository ``bestehorn-sff-test/sff-test-<run id>`` with an initial
commit, and cloned it. These tests read that state back, through the product wrapper started as a subprocess with the
test marker in the clone (``ephemeral_repository.wrapper``) and through git in the clone (``ephemeral_repository.git``).
No owner or repository path parameter is given, so the repository record targets the clone's ``origin``; nothing is
created, changed or deleted here.

- ``test_the_run_owns_a_private_seeded_repository`` (AC-1.1, AC-1.3): the record ``repos/get`` names this run's
  repository and answers that it is private; the clone's ``HEAD`` is the seed commit its ``origin/<default branch>``
  names, the seed holds nothing under ``.github/workflows/``, the clone's ``origin`` is the repository's URL (D3), and
  the clone's own ``credentials/github-pat.txt`` exists. Only its existence is checked: nothing here reads it.
- ``test_no_leftover_survives_the_sweep`` (AC-3.1): the record ``repos/list-for-org`` of the test organization, every
  page, lists no repository that is a leftover at the moment the fixture swept (``swept_at``), so a repository that
  crossed the one-day line after the sweep, which AC-3.2 spares, fails nothing.

Both records need the token's repository permission Metadata (read), which D6's table records as in place. The support
module (``RepositoryRecord``, ``is_leftover``, ``TEST_ORGANIZATION``) is ``sys.modules["forge_ephemeral"]``, which
``conftest.py`` registers when it loads ``ephemeral.py`` by path; it is read inside the test bodies (DL-005).

Run: ``python scripts/run_tests.py --workers 1 test/forge`` (with the test credential file, ``docs/forge-suite.md``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import Any, List

#: The ``sys.modules`` key of the by-path load of ``ephemeral.py`` that ``conftest.py`` registers (DL-005).
SUPPORT_MODULE = "forge_ephemeral"

WRAPPER_EXIT_OK = 0
GIT_EXIT_OK = 0
ARGUMENT_SEPARATOR = " "

# The records, as ``call`` arguments (D6).
CALL_SUBCOMMAND = "call"
REPOSITORY_RECORD = "repos/get"
ORGANIZATION_LISTING = "repos/list-for-org"
PATH_OPTION = "--path"
ORG_PARAMETER = "org"
PARAMETER_ASSIGNMENT = "="

# The fields of the repository record that are asserted (docs.github.com "Get a repository").
FIELD_FULL_NAME = "full_name"
FIELD_PRIVATE = "private"

# This run's repository, known in advance: the test organization, the ephemeral prefix and the run id (D4), and its
# URL, the clone's ``origin`` with no userinfo (D3 "The clone").
EPHEMERAL_REPOSITORY_PREFIX = "sff-test-"
FULL_NAME_SEPARATOR = "/"
REPOSITORY_URL = "https://github.com/{full_name}.git"

# The git commands that read the clone (D3 "The clone", D9 step 6).
GIT_REV_PARSE = "rev-parse"
GIT_LS_TREE = "ls-tree"
GIT_RECURSIVE_OPTION = "-r"
GIT_NAME_ONLY_OPTION = "--name-only"
GIT_REMOTE = "remote"
GIT_GET_URL = "get-url"
GIT_COMMAND = "git"
HEAD = "HEAD"
ORIGIN_REMOTE = "origin"
REMOTE_BRANCH_SEPARATOR = "/"
#: A seed path under this directory would start a workflow on the first push; the seed holds none (AC-1.3).
WORKFLOW_DIRECTORY = ".github/workflows/"
#: ``git ls-tree`` quotes a path holding an unusual character (``core.quotePath``); the directory part stays literal.
GIT_PATH_QUOTE = '"'
#: The clone's own credential file (D8 "Writing"), relative to the clone.
CLONE_CREDENTIAL_FILE = Path("credentials") / "github-pat.txt"


def _support() -> ModuleType:
    """The forge suite's support module ``ephemeral.py``, as ``conftest.py`` registered its by-path load (DL-005)."""
    module = sys.modules.get(SUPPORT_MODULE)
    assert module is not None, f"no {SUPPORT_MODULE} in sys.modules: conftest.py did not load ephemeral.py"
    return module


def _wrapper_answer(*, repository: Any, arguments: List[str]) -> Any:
    """The printed JSON of the product wrapper run with ``arguments`` in the clone, after asserting its exit 0."""
    invocation = repository.wrapper.run(arguments=arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"the product wrapper's `{ARGUMENT_SEPARATOR.join(arguments)}` exited {invocation.returncode}, not "
        f"{WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.json()


def _git_output(*, repository: Any, arguments: List[str]) -> str:
    """The standard output, stripped, of git run with ``arguments`` in the clone, after asserting its exit 0."""
    invocation = repository.git.run(arguments=arguments)
    assert invocation.returncode == GIT_EXIT_OK, (
        f"`{ARGUMENT_SEPARATOR.join([GIT_COMMAND, *arguments])}` exited {invocation.returncode} in the clone, not "
        f"{GIT_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return str(invocation.stdout).strip()


def _tree_paths(*, listing: str) -> List[str]:
    """The paths of a ``git ls-tree -r --name-only`` listing, a quoted path read without its opening quote."""
    return [line[len(GIT_PATH_QUOTE) :] if line.startswith(GIT_PATH_QUOTE) else line for line in listing.splitlines()]


def test_the_run_owns_a_private_seeded_repository(ephemeral_repository: Any) -> None:
    support = _support()
    full_name = (
        support.TEST_ORGANIZATION + FULL_NAME_SEPARATOR + EPHEMERAL_REPOSITORY_PREFIX + ephemeral_repository.run_id
    )

    answer = _wrapper_answer(repository=ephemeral_repository, arguments=[CALL_SUBCOMMAND, REPOSITORY_RECORD])
    assert isinstance(answer, dict), f"`{CALL_SUBCOMMAND} {REPOSITORY_RECORD}` printed no JSON object: {answer!r}"
    assert answer.get(FIELD_FULL_NAME) == full_name, (
        f"`{CALL_SUBCOMMAND} {REPOSITORY_RECORD}` names {answer.get(FIELD_FULL_NAME)!r}, not this run's {full_name!r}"
    )
    assert answer.get(FIELD_PRIVATE) is True, (
        f"`{CALL_SUBCOMMAND} {REPOSITORY_RECORD}` answers {FIELD_PRIVATE} {answer.get(FIELD_PRIVATE)!r} for "
        f"{full_name}, not true"
    )

    tracked = ORIGIN_REMOTE + REMOTE_BRANCH_SEPARATOR + ephemeral_repository.default_branch
    head = _git_output(repository=ephemeral_repository, arguments=[GIT_REV_PARSE, HEAD])
    tracked_head = _git_output(repository=ephemeral_repository, arguments=[GIT_REV_PARSE, tracked])
    assert head == tracked_head, f"the clone's {HEAD} is {head}, {tracked} is {tracked_head}"
    assert head == ephemeral_repository.seed_sha, (
        f"the clone's {HEAD} is {head}, not the seed commit {ephemeral_repository.seed_sha}"
    )

    listing = _git_output(
        repository=ephemeral_repository, arguments=[GIT_LS_TREE, GIT_RECURSIVE_OPTION, GIT_NAME_ONLY_OPTION, HEAD]
    )
    workflows = [path for path in _tree_paths(listing=listing) if path.startswith(WORKFLOW_DIRECTORY)]
    assert not workflows, f"the seed of {full_name} holds paths under {WORKFLOW_DIRECTORY}: {workflows}"

    origin = _git_output(repository=ephemeral_repository, arguments=[GIT_REMOTE, GIT_GET_URL, ORIGIN_REMOTE])
    expected_origin = REPOSITORY_URL.format(full_name=full_name)
    assert origin == expected_origin, f"the clone's {ORIGIN_REMOTE} is {origin!r}, not {expected_origin!r}"

    credential = Path(ephemeral_repository.clone) / CLONE_CREDENTIAL_FILE
    assert credential.is_file(), f"the clone holds no credential file {CLONE_CREDENTIAL_FILE.as_posix()}"


def test_no_leftover_survives_the_sweep(ephemeral_repository: Any) -> None:
    support = _support()
    organization = support.TEST_ORGANIZATION
    arguments = [
        CALL_SUBCOMMAND,
        ORGANIZATION_LISTING,
        PATH_OPTION,
        ORG_PARAMETER + PARAMETER_ASSIGNMENT + organization,
    ]

    listed = _wrapper_answer(repository=ephemeral_repository, arguments=arguments)
    assert isinstance(listed, list) and all(isinstance(item, dict) for item in listed), (
        f"`{CALL_SUBCOMMAND} {ORGANIZATION_LISTING}` printed no JSON array of repositories of {organization}"
    )
    swept_at = ephemeral_repository.swept_at
    records = [support.RepositoryRecord.of(item=item) for item in listed]
    leftovers = [record.full_name for record in records if support.is_leftover(record=record, now=swept_at)]
    assert not leftovers, (
        f"{organization} still holds repositories that were leftovers when the run swept at {swept_at.isoformat()}: "
        f"{leftovers}"
    )
