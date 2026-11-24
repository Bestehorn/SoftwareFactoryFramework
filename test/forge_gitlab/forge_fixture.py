"""F:fixture: the run's own project, as the session fixture made it (issue #11, design.md D6, D9; AC-1.1, AC-1.3,
AC-3.1).

Every other GitLab forge module stands on ``ephemeral_project`` (``test/forge_gitlab/conftest.py``, session scope): it
swept the test group's leftovers, created one private project ``bestehorn-sff-test/sff-test-<run id>`` seeded with a
``README.md``, and cloned it. These tests read that state back, through the product GitLab wrapper started as a
subprocess with the test marker in the clone (``ephemeral_project.wrapper``) and through git in the clone
(``ephemeral_project.git``). No project is named on a command line, so the project record targets the ``project_id``
of the clone's ``config/gitlab.json``; that the wrapper answers it with the marker set is AC-4.2's integration half.
Every invocation's exit code and printed answer are asserted against what the fixture made (AC-8.1); nothing is
created, changed or deleted here.

- ``test_the_run_owns_a_private_seeded_project`` (AC-1.1, AC-1.3, AC-8.3): the record
  ``tenant-scale#retrieve-a-project`` answers this run's full path as ``path_with_namespace``, ``visibility``
  ``private``, and the default branch and the id the creation answered; the clone's ``HEAD`` is the seed commit its
  ``origin/<default branch>`` names, the seed holds exactly ``README.md`` (so no ``.gitlab-ci.yml``), the clone's
  ``origin`` is ``https://gitlab.com/<full path>.git`` (D3), and the clone's ``config/gitlab.json`` holds ``hostname``
  ``gitlab.com`` and ``project_id`` the full path. Only those two values are read from that file: it also holds the
  test token (D8 "Writing"), so the loaded mapping is never compared or printed.
- ``test_no_leftover_survives_the_sweep`` (AC-3.1): the test group's listing, ``list_group_projects`` (record
  ``tenant-scale#list-projects``, every page), names this run's project once and unscheduled, and every project it
  lists that was a leftover at the moment the fixture swept (``swept_at``) is marked for deletion
  (``marked_for_deletion_on`` set), since a deletion on gitlab.com marks the project (D9). The leftovers are selected
  here from the records' own fields, not through ``is_leftover``: namespace ``TEST_GROUP``, path starting
  ``sff-test-``, ``created_at`` more than a day before ``swept_at``. A project that crossed the one-day line after the
  sweep, which AC-3.2 spares, fails nothing.

Both records need what D6's table records as in place: the token's scope ``api`` and the Owner role in the test group.
The support module (``list_group_projects`` and its ``ProjectRecord``, ``TEST_GROUP``, ``CLONE_CONFIG_FILE``) is
``sys.modules["forge_gitlab_ephemeral"]``, which ``conftest.py`` registers when it loads ``ephemeral.py`` by path; it
is read inside the test bodies (#10's DL-005).

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab`` (with the test credential file,
``docs/forge-suite.md``).
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path
from types import ModuleType
from typing import Any, List, Mapping, Tuple

#: The ``sys.modules`` key of the by-path load of ``ephemeral.py`` that ``conftest.py`` registers (D1, DL-005 of #10).
SUPPORT_MODULE = "forge_gitlab_ephemeral"

WRAPPER_EXIT_OK = 0
GIT_EXIT_OK = 0
ARGUMENT_SEPARATOR = " "

# The project record, as ``call`` arguments (D6); with no ``id`` given, ``call`` sends the configured ``project_id``.
CALL_SUBCOMMAND = "call"
PROJECT_RECORD = "tenant-scale#retrieve-a-project"

# The fields of the project record that are asserted (docs.gitlab.com/api/projects/, "Get a single project").
FIELD_ID = "id"
FIELD_PATH_WITH_NAMESPACE = "path_with_namespace"
FIELD_VISIBILITY = "visibility"
FIELD_DEFAULT_BRANCH = "default_branch"
PRIVATE_VISIBILITY = "private"

# This run's project, known in advance: the test group, the ephemeral prefix and the run id (D4), and its URL, the
# clone's ``origin`` with no userinfo (D3 "The clone").
EPHEMERAL_PROJECT_PREFIX = "sff-test-"
PROJECT_PATH_SEPARATOR = "/"
GITLAB_HOSTNAME = "gitlab.com"
PROJECT_URL = "https://" + GITLAB_HOSTNAME + "/{full_path}.git"

# The two keys of the clone's ``config/gitlab.json`` that are read, the product's ``FIELD_HOSTNAME`` and
# ``FIELD_PROJECT_ID`` (``gitlab_api/transport.py``); its third key, the token, is never read here (D6, D8).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
CONFIG_ENCODING = "utf-8"

# The git commands that read the clone (D3 "The clone", D9 step 7).
GIT_COMMAND = "git"
GIT_REV_PARSE = "rev-parse"
GIT_LS_TREE = "ls-tree"
GIT_RECURSIVE_OPTION = "-r"
GIT_NAME_ONLY_OPTION = "--name-only"
GIT_REMOTE = "remote"
GIT_GET_URL = "get-url"
HEAD = "HEAD"
ORIGIN_REMOTE = "origin"
REMOTE_BRANCH_SEPARATOR = "/"
#: The seed's one file: the creation asks for "a Git repository with just a ``README.md`` file" (D9 step 6), so the
#: seed holds no ``.gitlab-ci.yml`` (AC-1.3).
SEED_FILE = "README.md"

#: AC-3.1: a leftover was created more than a day before the sweep; a day old or less is spared (AC-3.2).
LEFTOVER_AGE = timedelta(days=1)


def _support() -> ModuleType:
    """The GitLab forge suite's support module ``ephemeral.py``, as ``conftest.py`` registered its by-path load."""
    module = sys.modules.get(SUPPORT_MODULE)
    assert module is not None, f"no {SUPPORT_MODULE} in sys.modules: conftest.py did not load ephemeral.py"
    return module


def _wrapper_answer(*, project: Any, arguments: List[str]) -> Any:
    """The printed JSON of the product GitLab wrapper run with ``arguments`` in the clone, after asserting its exit 0.
    The exit code is taken out first, so a failed assertion prints it and the standard error, never the answer."""
    invocation = project.wrapper.run(arguments=arguments)
    returncode = invocation.returncode
    assert returncode == WRAPPER_EXIT_OK, (
        f"the product GitLab wrapper's `{ARGUMENT_SEPARATOR.join(arguments)}` exited {returncode}, not "
        f"{WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.json()


def _printed_object(*, answer: Any, arguments: List[str]) -> Mapping[str, Any]:
    """``answer`` after asserting that it is a JSON object; a failed assertion names its type alone."""
    is_object = isinstance(answer, dict)
    assert is_object, f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed a JSON {type(answer).__name__}, not an object"
    return answer


def _git_output(*, project: Any, arguments: List[str]) -> str:
    """The standard output, stripped, of git run with ``arguments`` in the clone, after asserting its exit 0."""
    invocation = project.git.run(arguments=arguments)
    returncode = invocation.returncode
    assert returncode == GIT_EXIT_OK, (
        f"`{ARGUMENT_SEPARATOR.join([GIT_COMMAND, *arguments])}` exited {returncode} in the clone, not "
        f"{GIT_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return str(invocation.stdout).strip()


def _clone_config_values(*, clone: Path, config_file: Path) -> Tuple[Any, Any]:
    """The ``hostname`` and ``project_id`` values of the clone's ``config_file``, and nothing else of it.

    The file also holds the test token (D8 "Writing"), so the loaded mapping stays a local of this function, which
    asserts nothing: no assertion compares or prints it (D6). A file holding no JSON object gives ``None`` for both.
    """
    loaded = json.loads(s=(clone / config_file).read_text(encoding=CONFIG_ENCODING))
    if not isinstance(loaded, dict):
        return None, None
    return loaded.get(FIELD_HOSTNAME), loaded.get(FIELD_PROJECT_ID)


def test_the_run_owns_a_private_seeded_project(ephemeral_project: Any) -> None:
    support = _support()
    full_path = support.TEST_GROUP + PROJECT_PATH_SEPARATOR + EPHEMERAL_PROJECT_PREFIX + ephemeral_project.run_id
    created_branch = ephemeral_project.default_branch
    created_id = ephemeral_project.project_id
    seed = ephemeral_project.seed_sha

    arguments = [CALL_SUBCOMMAND, PROJECT_RECORD]
    answer = _wrapper_answer(project=ephemeral_project, arguments=arguments)
    record = _printed_object(answer=answer, arguments=arguments)
    named = record.get(FIELD_PATH_WITH_NAMESPACE)
    assert named == full_path, (
        f"`{CALL_SUBCOMMAND} {PROJECT_RECORD}` names {FIELD_PATH_WITH_NAMESPACE} {named!r}, not this run's "
        f"{full_path!r}"
    )
    visibility = record.get(FIELD_VISIBILITY)
    assert visibility == PRIVATE_VISIBILITY, (
        f"`{CALL_SUBCOMMAND} {PROJECT_RECORD}` answers {FIELD_VISIBILITY} {visibility!r} for {full_path}, not "
        f"{PRIVATE_VISIBILITY!r}"
    )
    default_branch = record.get(FIELD_DEFAULT_BRANCH)
    assert default_branch == created_branch, (
        f"`{CALL_SUBCOMMAND} {PROJECT_RECORD}` answers {FIELD_DEFAULT_BRANCH} {default_branch!r} for {full_path}, not "
        f"the creation's {created_branch!r}"
    )
    numeric_id = record.get(FIELD_ID)
    assert numeric_id == created_id, (
        f"`{CALL_SUBCOMMAND} {PROJECT_RECORD}` answers {FIELD_ID} {numeric_id!r} for {full_path}, not the creation's "
        f"{created_id!r}"
    )

    tracked = ORIGIN_REMOTE + REMOTE_BRANCH_SEPARATOR + created_branch
    head = _git_output(project=ephemeral_project, arguments=[GIT_REV_PARSE, HEAD])
    tracked_head = _git_output(project=ephemeral_project, arguments=[GIT_REV_PARSE, tracked])
    assert head == tracked_head, f"the clone's {HEAD} is {head}, {tracked} is {tracked_head}"
    assert head == seed, f"the clone's {HEAD} is {head}, not the seed commit {seed}"

    listing = _git_output(
        project=ephemeral_project, arguments=[GIT_LS_TREE, GIT_RECURSIVE_OPTION, GIT_NAME_ONLY_OPTION, seed]
    )
    seed_paths = listing.splitlines()
    assert seed_paths == [SEED_FILE], f"the seed {seed} of {full_path} holds {seed_paths}, not exactly {[SEED_FILE]}"

    origin = _git_output(project=ephemeral_project, arguments=[GIT_REMOTE, GIT_GET_URL, ORIGIN_REMOTE])
    expected_origin = PROJECT_URL.format(full_path=full_path)
    assert origin == expected_origin, f"the clone's {ORIGIN_REMOTE} is {origin!r}, not {expected_origin!r}"

    configured_hostname, configured_project = _clone_config_values(
        clone=Path(ephemeral_project.clone), config_file=support.CLONE_CONFIG_FILE
    )
    config_name = support.CLONE_CONFIG_FILE.as_posix()
    assert configured_hostname == GITLAB_HOSTNAME, (
        f"the clone's {config_name} holds {FIELD_HOSTNAME} {configured_hostname!r}, not {GITLAB_HOSTNAME!r}"
    )
    assert configured_project == full_path, (
        f"the clone's {config_name} holds {FIELD_PROJECT_ID} {configured_project!r}, not this run's {full_path!r}"
    )


def test_no_leftover_survives_the_sweep(ephemeral_project: Any) -> None:
    support = _support()
    group = support.TEST_GROUP
    path = EPHEMERAL_PROJECT_PREFIX + ephemeral_project.run_id
    full_path = group + PROJECT_PATH_SEPARATOR + path
    swept_at = ephemeral_project.swept_at

    records = support.list_group_projects(wrapper=ephemeral_project.wrapper)

    own = [record for record in records if (record.namespace, record.path) == (group, path)]
    listed_own = len(own)
    assert listed_own == 1, f"the listing of {group} names this run's project {full_path} {listed_own} times, not once"
    own_marked = own[0].marked_for_deletion_on
    assert own_marked is None, (
        f"the listing of {group} answers this run's project {full_path} marked for deletion on {own_marked}"
    )

    leftovers = [
        record
        for record in records
        if record.namespace == group
        and record.path.startswith(EPHEMERAL_PROJECT_PREFIX)
        and swept_at - record.created_at > LEFTOVER_AGE
    ]
    unscheduled = [
        f"{record.namespace}{PROJECT_PATH_SEPARATOR}{record.path} (created {record.created_at.isoformat()})"
        for record in leftovers
        if record.marked_for_deletion_on is None
    ]
    assert not unscheduled, (
        f"{group} still holds projects that were leftovers when the run swept at {swept_at.isoformat()} and are not "
        f"marked for deletion: {unscheduled}"
    )
