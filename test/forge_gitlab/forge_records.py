"""F:records: ``call`` on GitLab's Projects, Commits, Repositories, Issues, Notes and Merge requests REST records,
against this run's ephemeral project (issue #11, design.md D6; AC-1.3, AC-4.2, AC-8.1, AC-8.3).

Each test takes the session's ``ephemeral_project`` (``test/forge_gitlab/conftest.py``): the private project
``bestehorn-sff-test/sff-test-<run id>`` this run created with ``initialize_with_readme`` ("Whether to create a Git
repository with just a ``README.md`` file", docs.gitlab.com/api/projects/), so its seed commit's tree holds one file,
``README.md``, and the clone of it at that commit. The product GitLab wrapper runs through the fixture's ``wrapper``,
with the test marker set and the clone as its working directory (AC-4.2, AC-8.1). No call gives a project ``id``, so
every record takes the configured project, the ``project_id`` of the clone's ``config/gitlab.json``. Each invocation's
exit code and printed JSON are asserted against what the test knows in advance (AC-8.1, AC-8.3); ``<hex>`` is a fresh
``uuid.uuid4().hex`` of the test.

- ``test_the_repository_records_read_the_seed`` (AC-1.3): ``call tenant-scale#retrieve-a-project`` answers as
  ``default_branch`` the branch the creation answered; ``call create#retrieve-a-commit`` of the seed answers the seed's
  SHA as ``id`` and no parent (``parent_ids`` ``[]``); ``call create#list-all-repository-trees-in-a-project`` at the
  seed lists one entry, the blob ``README.md``, whose ``id`` is the clone's ``git rev-parse <seed>:README.md``. The
  default branch moves when F:subcommands merges its merge request, so the commit and the tree are read by the seed's
  SHA, never by the branch: the tree record resolves its ``ref`` as a commit, ``project.commit(ref)``, and reads the
  tree at that commit's ``id`` (gitlab-org/gitlab ``app/finders/repositories/tree_finder.rb``).
- ``test_the_issue_and_note_records``: the issue is made with ``issue create`` and its note with ``issue comment``,
  since ``call`` refuses ``plan#create-an-issue`` and names that subcommand; then ``call plan#retrieve-a-project-issue``
  answers the issue's ``iid`` and ``title``, and ``call plan#list-all-issue-notes`` lists a note whose ``body`` is the
  comment. The issue is this test's own, so the other slices' issues change no answer.
- ``test_the_merge_request_records``: the branch ``forge-records-<hex>`` with one new file, pushed by ``push_branch``,
  and a merge request of it into the default branch, made with ``mr create``; ``wait_until_checked`` then reads it
  until GitLab has decided its mergeability, since GitLab creates the merge request diff, which the commits record
  lists, after the creation answers (``preparing``: "Merge request diff is being created",
  docs.gitlab.com/api/merge_requests/). Then ``call ai-coding#retrieve-a-merge-request`` answers the branch as
  ``source_branch`` and the pushed commit as ``sha``, and ``call ai-coding#retrieve-merge-request-commits`` lists
  exactly that commit, the one commit of the branch that the default branch does not hold.

Every record here is a read; the setup's ``issue create``, ``issue comment``, push and ``mr create`` write only inside
the run's project, which the session's teardown deletes. The token's scope ``api`` covers each (D6's table).
``push_branch`` and ``wait_until_checked`` are the support module's, ``sys.modules["forge_gitlab_ephemeral"]``, which
``conftest.py`` registers when it loads ``ephemeral.py`` by path; they are read inside the test bodies.

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab``.
"""

from __future__ import annotations

import sys
import uuid
from types import ModuleType
from typing import Any, List, Mapping, Sequence

#: The ``sys.modules`` key of the by-path load of ``ephemeral.py`` that ``conftest.py`` registers (D1).
SUPPORT_MODULE = "forge_gitlab_ephemeral"

WRAPPER_EXIT_OK = 0
GIT_EXIT_OK = 0
ARGUMENT_SEPARATOR = " "

# The product wrapper's subcommands and options (``gitlab_api/commands/call.py``, ``issue.py``, ``mr.py``).
CALL = "call"
ISSUE_GROUP = "issue"
MR_GROUP = "mr"
CREATE = "create"
COMMENT = "comment"
TITLE_OPTION = "--title"
BODY_OPTION = "--body"
SOURCE_OPTION = "--source"
TARGET_OPTION = "--target"
PATH_OPTION = "--path"
QUERY_OPTION = "--query"
ASSIGNMENT = "="

# The records this slice reads, by operation ID (``gitlab_api/families/tenant_scale.py``, ``create.py``, ``plan.py``,
# ``ai_coding.py``), and their parameters: the commit's ``:sha`` and the issue's and merge request's iids are path
# parameters, the tree's ``ref`` a query attribute.
PROJECT_RECORD = "tenant-scale#retrieve-a-project"
COMMIT_RECORD = "create#retrieve-a-commit"
TREE_RECORD = "create#list-all-repository-trees-in-a-project"
ISSUE_RECORD = "plan#retrieve-a-project-issue"
ISSUE_NOTES_RECORD = "plan#list-all-issue-notes"
MERGE_REQUEST_RECORD = "ai-coding#retrieve-a-merge-request"
MERGE_REQUEST_COMMITS_RECORD = "ai-coding#retrieve-merge-request-commits"
SHA_PARAMETER = "sha"
REF_PARAMETER = "ref"
ISSUE_IID_PARAMETER = "issue_iid"
MERGE_REQUEST_IID_PARAMETER = "merge_request_iid"

# The fields of the answers this slice reads: a project's ``default_branch``; a commit's ``id`` and ``parent_ids``; a
# tree entry's ``id``, ``name`` and ``type``; an issue's ``iid`` and ``title``; a note's ``body``; a merge request's
# ``iid``, ``title``, ``source_branch``, ``target_branch`` and ``sha`` (docs/api-reference/gitlab/rest/, and
# docs.gitlab.com/api/repositories/ "List all repository trees in a project" for the tree entry).
FIELD_DEFAULT_BRANCH = "default_branch"
FIELD_ID = "id"
FIELD_PARENT_IDS = "parent_ids"
FIELD_NAME = "name"
FIELD_TYPE = "type"
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_BODY = "body"
FIELD_SOURCE_BRANCH = "source_branch"
FIELD_TARGET_BRANCH = "target_branch"
FIELD_SHA = "sha"
#: The one file of the seed commit ``initialize_with_readme`` creates, and its tree entry's type.
SEED_FILE = "README.md"
BLOB_TYPE = "blob"

# The git command that names the seed's blob of ``README.md`` in the clone: ``git rev-parse <seed>:README.md``.
GIT_REV_PARSE = "rev-parse"
REVISION_PATH_SEPARATOR = ":"

# What the issue and merge-request tests create, each naming the run and the test's ``<hex>`` (D6).
ISSUE_TITLE = "Forge records issue {hex} of run {run_id}"
ISSUE_NOTE = "The note of the forge records issue {hex} of run {run_id}."
BRANCH = "forge-records-{hex}"
MERGE_REQUEST_TITLE = "Forge records merge request {hex} of run {run_id}"


def _support() -> ModuleType:
    """The GitLab forge suite's support module ``ephemeral.py``, as ``conftest.py`` registered its by-path load."""
    module = sys.modules.get(SUPPORT_MODULE)
    assert module is not None, f"no {SUPPORT_MODULE} in sys.modules: conftest.py did not load ephemeral.py"
    return module


def _assignment(*, option: str, name: str, value: str) -> List[str]:
    """One ``NAME=VALUE`` of ``call``: ``<option> <name>=<value>``."""
    return [option, name + ASSIGNMENT + value]


def _answer(*, project: Any, arguments: Sequence[str]) -> Any:
    """The JSON the product wrapper printed for ``arguments``, run in the clone, after asserting that it exited 0."""
    invocation = project.wrapper.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{command}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.json()


def _record(*, project: Any, arguments: Sequence[str]) -> Mapping[str, Any]:
    """The one JSON object the product wrapper printed for ``arguments``."""
    answer = _answer(project=project, arguments=arguments)
    assert isinstance(answer, dict), f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON object: {answer!r}"
    return answer


def _records(*, project: Any, arguments: Sequence[str]) -> List[Mapping[str, Any]]:
    """The JSON array of objects the product wrapper printed for ``arguments``, every page of a paged record."""
    answer = _answer(project=project, arguments=arguments)
    assert isinstance(answer, list) and all(isinstance(item, dict) for item in answer), (
        f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON array of objects: {answer!r}"
    )
    return answer


def _git(*, project: Any, arguments: Sequence[str]) -> str:
    """The standard output, stripped, of git run in the clone with ``arguments``, after asserting that it exited 0."""
    invocation = project.git.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == GIT_EXIT_OK, (
        f"`git {command}` exited {invocation.returncode} in the clone, not {GIT_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return str(invocation.stdout).strip()


def _iid(*, record: Mapping[str, Any], command: str) -> int:
    """The ``iid`` a created issue or merge request answered, asserted to be an integer."""
    iid = record.get(FIELD_IID)
    assert isinstance(iid, int) and not isinstance(iid, bool), f"`{command}` answered the {FIELD_IID} {iid!r}"
    return iid


def test_the_repository_records_read_the_seed(ephemeral_project: Any) -> None:
    """The project record names the creation's default branch; the commit and tree records of the seed, read by its
    SHA, answer the seed commit, a root commit, and its one blob ``README.md``."""
    seed = ephemeral_project.seed_sha
    default_branch = ephemeral_project.default_branch

    project = _record(project=ephemeral_project, arguments=[CALL, PROJECT_RECORD])
    assert project.get(FIELD_DEFAULT_BRANCH) == default_branch, (
        f"`{PROJECT_RECORD}` answered the {FIELD_DEFAULT_BRANCH} {project.get(FIELD_DEFAULT_BRANCH)!r}; the creation "
        f"answered {default_branch!r}"
    )

    commit = _record(
        project=ephemeral_project,
        arguments=[CALL, COMMIT_RECORD, *_assignment(option=PATH_OPTION, name=SHA_PARAMETER, value=seed)],
    )
    assert commit.get(FIELD_ID) == seed, (
        f"`{COMMIT_RECORD}` answered the {FIELD_ID} {commit.get(FIELD_ID)!r}, not the seed {seed}"
    )
    assert commit.get(FIELD_PARENT_IDS) == [], (
        f"`{COMMIT_RECORD}` of the seed {seed} answered the {FIELD_PARENT_IDS} {commit.get(FIELD_PARENT_IDS)!r}, not []"
    )

    blob = _git(project=ephemeral_project, arguments=[GIT_REV_PARSE, seed + REVISION_PATH_SEPARATOR + SEED_FILE])
    entries = _records(
        project=ephemeral_project,
        arguments=[CALL, TREE_RECORD, *_assignment(option=QUERY_OPTION, name=REF_PARAMETER, value=seed)],
    )
    listed = [(entry.get(FIELD_NAME), entry.get(FIELD_TYPE), entry.get(FIELD_ID)) for entry in entries]
    assert listed == [(SEED_FILE, BLOB_TYPE, blob)], (
        f"`{TREE_RECORD}` at the seed {seed} listed {listed}, not the one {BLOB_TYPE} {SEED_FILE} {blob} of the clone"
    )


def test_the_issue_and_note_records(ephemeral_project: Any) -> None:
    """An issue and its note, made through ``issue create`` and ``issue comment``, read back through the issue and the
    notes records."""
    fresh = uuid.uuid4().hex
    run_id = ephemeral_project.run_id
    title = ISSUE_TITLE.format(hex=fresh, run_id=run_id)
    note = ISSUE_NOTE.format(hex=fresh, run_id=run_id)

    create = [ISSUE_GROUP, CREATE, TITLE_OPTION, title]
    created = _record(project=ephemeral_project, arguments=create)
    assert created.get(FIELD_TITLE) == title, (
        f"`{ISSUE_GROUP} {CREATE}` answered the {FIELD_TITLE} {created.get(FIELD_TITLE)!r}, not {title!r}"
    )
    iid = _iid(record=created, command=ARGUMENT_SEPARATOR.join(create))

    comment = _record(project=ephemeral_project, arguments=[ISSUE_GROUP, COMMENT, str(iid), BODY_OPTION, note])
    assert comment.get(FIELD_BODY) == note, (
        f"`{ISSUE_GROUP} {COMMENT} {iid}` answered the {FIELD_BODY} {comment.get(FIELD_BODY)!r}, not {note!r}"
    )

    issue_path = _assignment(option=PATH_OPTION, name=ISSUE_IID_PARAMETER, value=str(iid))
    issue = _record(project=ephemeral_project, arguments=[CALL, ISSUE_RECORD, *issue_path])
    assert issue.get(FIELD_IID) == iid, f"`{ISSUE_RECORD}` answered the {FIELD_IID} {issue.get(FIELD_IID)!r}, not {iid}"
    assert issue.get(FIELD_TITLE) == title, (
        f"`{ISSUE_RECORD}` answered the {FIELD_TITLE} {issue.get(FIELD_TITLE)!r}, not {title!r}"
    )

    notes = _records(project=ephemeral_project, arguments=[CALL, ISSUE_NOTES_RECORD, *issue_path])
    bodies = [item.get(FIELD_BODY) for item in notes]
    assert note in bodies, f"`{ISSUE_NOTES_RECORD}` of the issue {iid} listed the bodies {bodies}, none {note!r}"


def test_the_merge_request_records(ephemeral_project: Any) -> None:
    """A merge request of a pushed branch, once GitLab has prepared it, read back through the merge request and its
    commits records."""
    support = _support()
    fresh = uuid.uuid4().hex
    branch = BRANCH.format(hex=fresh)
    title = MERGE_REQUEST_TITLE.format(hex=fresh, run_id=ephemeral_project.run_id)
    default_branch = ephemeral_project.default_branch

    pushed = support.push_branch(git=ephemeral_project.git, default_branch=default_branch, branch=branch)
    assert pushed != ephemeral_project.seed_sha, f"the commit pushed on {branch} is the seed {pushed} itself"

    create = [MR_GROUP, CREATE, SOURCE_OPTION, branch, TARGET_OPTION, default_branch, TITLE_OPTION, title]
    created = _record(project=ephemeral_project, arguments=create)
    opened = (created.get(FIELD_SOURCE_BRANCH), created.get(FIELD_TARGET_BRANCH), created.get(FIELD_TITLE))
    assert opened == (branch, default_branch, title), (
        f"`{MR_GROUP} {CREATE}` answered the {FIELD_SOURCE_BRANCH}, {FIELD_TARGET_BRANCH} and {FIELD_TITLE} {opened}, "
        f"not {(branch, default_branch, title)}"
    )
    iid = _iid(record=created, command=ARGUMENT_SEPARATOR.join(create))

    checked = support.wait_until_checked(wrapper=ephemeral_project.wrapper, iid=iid)
    assert checked.get(FIELD_IID) == iid, (
        f"`wait_until_checked` of the merge request {iid} answered the {FIELD_IID} {checked.get(FIELD_IID)!r}"
    )

    merge_request_path = _assignment(option=PATH_OPTION, name=MERGE_REQUEST_IID_PARAMETER, value=str(iid))
    merge_request = _record(project=ephemeral_project, arguments=[CALL, MERGE_REQUEST_RECORD, *merge_request_path])
    assert merge_request.get(FIELD_SOURCE_BRANCH) == branch, (
        f"`{MERGE_REQUEST_RECORD}` of {iid} answered the {FIELD_SOURCE_BRANCH} "
        f"{merge_request.get(FIELD_SOURCE_BRANCH)!r}, not {branch!r}"
    )
    assert merge_request.get(FIELD_SHA) == pushed, (
        f"`{MERGE_REQUEST_RECORD}` of {iid} answered the {FIELD_SHA} {merge_request.get(FIELD_SHA)!r}, not the pushed "
        f"commit {pushed}"
    )

    commits = _records(project=ephemeral_project, arguments=[CALL, MERGE_REQUEST_COMMITS_RECORD, *merge_request_path])
    listed = [commit.get(FIELD_ID) for commit in commits]
    assert listed == [pushed], (
        f"`{MERGE_REQUEST_COMMITS_RECORD}` of {iid} listed the commits {listed}, not the one pushed commit {pushed}"
    )
