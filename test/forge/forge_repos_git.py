"""The real-forge tests of the ``repos`` and ``git`` records (F:repos_git, slice #27): ``call`` read against the seed.

Part of the forge suite (``test/forge/``), run only by ``python scripts/run_tests.py --workers 1 test/forge`` against
github.com (D1, D6). Each test takes the session's ``ephemeral_repository``: the ``bestehorn-sff-test`` repository this
run created with ``auto_init`` ("Pass true to create an initial commit with empty README.", docs.github.com "Create an
organization repository"), so its seed commit's tree holds one file, ``README.md``, and the clone of it checked out at
that commit. The product wrapper runs through the fixture's ``wrapper``, with the test marker set and the clone as its
working directory, so every record targets the clone's ``origin`` and no test names an owner or a repository.

Each invocation's exit code and printed JSON are asserted against what the fixture knows in advance (AC-8.1, AC-8.3):
``repos/get`` answers as ``default_branch`` the branch the creation answered, which is the branch the clone has checked
out; ``git/get-commit`` of the seed commit answers its ``sha`` and, as ``tree.sha``, the seed's tree; ``git/get-tree``
of that tree answers its ``sha`` and one entry, ``README.md`` (AC-1.3). Every record here is a read: nothing is
created, changed or deleted (AC-8.6).
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

# The ``call`` subcommand and its path parameters (``--path NAME=VALUE``); ``owner`` and ``repo`` are never given.
CALL_SUBCOMMAND = "call"
PATH_OPTION = "--path"
PARAMETER_ASSIGNMENT = "="
ARGUMENT_SEPARATOR = " "
WRAPPER_EXIT_OK = 0

# The records of slice #27 this module reads (``github_api/families/repos.py``, ``github_api/families/git.py``).
REPOSITORY_RECORD = "repos/get"
COMMIT_RECORD = "git/get-commit"
TREE_RECORD = "git/get-tree"
COMMIT_SHA_PARAMETER = "commit_sha"
TREE_SHA_PARAMETER = "tree_sha"

# The fields of the answers: a repository's ``default_branch``; a git commit's ``sha`` and ``tree.sha``; a git tree's
# ``sha`` and its ``tree`` entries' ``path``.
FIELD_DEFAULT_BRANCH = "default_branch"
FIELD_SHA = "sha"
FIELD_TREE = "tree"
FIELD_PATH = "path"
#: The one file of the seed commit ``auto_init`` creates.
SEED_FILE = "README.md"

# The branch the clone has checked out: ``git symbolic-ref --short HEAD`` prints it, and exits non-zero on a detached
# HEAD.
GIT_EXIT_OK = 0
CHECKED_OUT_BRANCH = ("symbolic-ref", "--short", "HEAD")


def call_arguments(*, operation: str, parameters: Mapping[str, str]) -> List[str]:
    """``call <operation>`` with each of ``parameters`` as ``--path <name>=<value>``."""
    arguments = [CALL_SUBCOMMAND, operation]
    for name, value in parameters.items():
        arguments += [PATH_OPTION, name + PARAMETER_ASSIGNMENT + value]
    return arguments


def answer_of(*, repository: Any, operation: str, parameters: Mapping[str, str]) -> Dict[str, Any]:
    """The JSON object the product wrapper printed for ``call <operation>`` in ``repository``'s clone, once its exit
    code is asserted to be 0 and its printed answer an object."""
    arguments = call_arguments(operation=operation, parameters=parameters)
    command = ARGUMENT_SEPARATOR.join(arguments)
    invocation = repository.wrapper.run(arguments=arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{command}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}:\n{invocation.stderr}"
    )
    answer = invocation.json()
    assert isinstance(answer, dict), f"`{command}` printed no JSON object:\n{invocation.stdout}"
    return answer


def test_the_repository_record_names_the_seed_branch(ephemeral_repository: Any) -> None:
    """``call repos/get`` answers as ``default_branch`` the branch the creation answered, and the clone has that branch
    checked out."""
    expected = ephemeral_repository.default_branch
    record = answer_of(repository=ephemeral_repository, operation=REPOSITORY_RECORD, parameters={})
    assert record.get(FIELD_DEFAULT_BRANCH) == expected, (
        f"`{REPOSITORY_RECORD}` answered {FIELD_DEFAULT_BRANCH} {record.get(FIELD_DEFAULT_BRANCH)!r}; the creation "
        f"answered {expected!r}"
    )
    checked_out = ephemeral_repository.git.run(arguments=list(CHECKED_OUT_BRANCH))
    git_command = ARGUMENT_SEPARATOR.join(CHECKED_OUT_BRANCH)
    assert checked_out.returncode == GIT_EXIT_OK, (
        f"`git {git_command}` exited {checked_out.returncode} in the clone:\n{checked_out.stderr}"
    )
    assert checked_out.stdout.strip() == expected, (
        f"the clone has {checked_out.stdout.strip()!r} checked out, not the default branch {expected!r}"
    )


def test_the_git_records_read_the_seed_commit(ephemeral_repository: Any) -> None:
    """``call git/get-commit`` of the seed commit answers its ``sha`` and the seed's tree as ``tree.sha``; ``call
    git/get-tree`` of that tree answers its ``sha`` and one entry, ``README.md``."""
    seed_sha = ephemeral_repository.seed_sha
    seed_tree_sha = ephemeral_repository.seed_tree_sha
    commit = answer_of(
        repository=ephemeral_repository, operation=COMMIT_RECORD, parameters={COMMIT_SHA_PARAMETER: seed_sha}
    )
    assert commit.get(FIELD_SHA) == seed_sha, (
        f"`{COMMIT_RECORD}` answered {FIELD_SHA} {commit.get(FIELD_SHA)!r}, not the seed commit {seed_sha!r}"
    )
    commit_tree = commit.get(FIELD_TREE)
    assert isinstance(commit_tree, dict) and commit_tree.get(FIELD_SHA) == seed_tree_sha, (
        f"`{COMMIT_RECORD}` answered {FIELD_TREE} {commit_tree!r}, whose {FIELD_SHA} is not the seed's tree "
        f"{seed_tree_sha!r}"
    )
    tree = answer_of(
        repository=ephemeral_repository, operation=TREE_RECORD, parameters={TREE_SHA_PARAMETER: seed_tree_sha}
    )
    assert tree.get(FIELD_SHA) == seed_tree_sha, (
        f"`{TREE_RECORD}` answered {FIELD_SHA} {tree.get(FIELD_SHA)!r}, not the seed's tree {seed_tree_sha!r}"
    )
    entries = tree.get(FIELD_TREE)
    assert isinstance(entries, list), f"`{TREE_RECORD}` answered no {FIELD_TREE} array: {tree!r}"
    paths = [entry.get(FIELD_PATH) if isinstance(entry, dict) else entry for entry in entries]
    assert paths == [SEED_FILE], f"the seed's tree lists {paths}, not the one file {SEED_FILE!r} of the creation"
