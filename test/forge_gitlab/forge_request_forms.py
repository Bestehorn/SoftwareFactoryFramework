"""F:request_forms (#63): the request forms of issue #63 that ``call`` gives, against this run's project (issue #11,
design.md D6; AC-4.2, AC-8.1, AC-8.5, AC-8.6).

Part of the GitLab forge suite (``test/forge_gitlab/``), run only by ``python scripts/run_tests.py --workers 1
test/forge_gitlab`` against gitlab.com. Each test takes the session's ``ephemeral_project``: the private ``sff-test-*``
project of the test group this run created, seeded with one ``README.md``, and the clone of it at the seed commit. The
product GitLab wrapper runs through the fixture's ``wrapper``, with the test marker set and the clone as its working
directory, so every record takes the configured project and no invocation names a project. Each invocation's exit
code and printed answer are asserted against what the test knows in advance: the project as the fixture and the test
made it, or the answer GitLab documents (AC-8.1).

The request forms the ``call.py`` module docstring lists for issue #63, and how each is handled here (AC-8.5):

- ``--endpoint``, by ``test_an_endpoint_named_by_endpoint``. Its setup pushes a branch ``forge-emoji-<hex>`` with git
  from the clone (the support module's ``push_branch``) and opens a merge request of it with ``mr create``. Then ``call
  plan#add-an-emoji-reaction-to-a-resource`` is sent on the endpoint ``POST
  /projects/:id/merge_requests/:merge_request_iid/award_emoji`` with ``-f name=thumbsup``, and answers the reaction
  ``thumbsup`` with ``awardable_type`` ``MergeRequest``; ``call plan#list-all-emoji-reactions-for-a-resource`` on
  ``GET /projects/:id/merge_requests/:merge_request_iid/award_emoji`` lists that one reaction. Without ``--endpoint``
  either ID sends its base record, the issue endpoint.
- a ``[.format]`` suffix, by ``test_a_format_suffix``: ``call create#retrieve-file-archive-from-a-repository --path
  format=zip --query sha=<seed>`` prints the archive's bytes unchanged (``print_bytes``), which
  ``Invocation.stdout.encode(encoding="utf-8", errors="surrogateescape")`` gives back (D10): a zip archive whose one
  file ends ``/README.md`` and holds the text ``git show <seed>:README.md`` prints.
- a positional name given once per place, a container-registry record, ``--header``, and a form-body member below its
  first bracket level: not called (AC-8.6). Each record that declares one of these forms is named below with D6's
  reason, and the fake-host suites stay its proof (UB-1).

A positional name given once per place is declared only by group records:

- ``create#delete-a-group-ssh-certificate``: outside the ephemeral project (AC-8.7), a group record; and the group SSH
  certificates API is "Tier: Premium, Ultimate" (``docs/api-reference/gitlab/rest/create.md``).
- ``tenant-scale#revoke-a-personal-access-token-for-an-enterprise-user``: outside the ephemeral project (AC-8.7).
- ``tenant-scale#revoke-a-group-or-project-access-token-for-an-enterprise-user``: outside the ephemeral project.
- ``tenant-scale#rotate-a-personal-access-token-for-an-enterprise-user``: outside the ephemeral project (AC-8.7).
- ``tenant-scale#rotate-a-group-or-project-access-token-for-an-enterprise-user``: outside the ephemeral project.

The container-registry records (docs.gitlab.com/api/container_registry/):

- ``package#listing-all-container-repositories``: it needs "administrator credentials".
- ``package#delete-image-tags-by-reference``: no documented answer; GitLab documents no answer for a project without
  an image, beside "The `tag_delete` Container-Registry-Feature must be enabled".

``--header`` is declared by:

- ``software-supply-chain-security#set-status-of-an-external-control``: "Tier: Ultimate"
  (``docs/api-reference/gitlab/rest/software-supply-chain-security.md``).
- ``openapi-only#the-nuget-symbol-file-download-endpoint``: outside the ephemeral project (AC-8.7), a group record;
  "source: `openapi_v2.yaml` only", with no documented answer.
- ``openapi-only#the-nuget-symbol-file-download-endpoint-1``: no documented answer; "source: `openapi_v2.yaml` only".

A form-body member below its first bracket level is declared only by:

- ``gitlab-dedicated#import-a-project-from-an-aws-s3-bucket``: ``call``'s refusal; ``call`` refuses it before any
  request (``GATED_OPERATIONS``).

Everything the tests create, the branch, the merge request and the reaction, lives inside the run's project, which the
session's teardown deletes (AC-8.7).

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab``.
"""

from __future__ import annotations

import io
import sys
import uuid
import zipfile
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence

#: The ``sys.modules`` key ``conftest.py`` loads the support module ``ephemeral.py`` under (D1, D10); its
#: ``push_branch`` is read from there inside a test body.
SUPPORT_MODULE = "forge_gitlab_ephemeral"

WRAPPER_EXIT_OK = 0
GIT_EXIT_OK = 0
ARGUMENT_SEPARATOR = " "
PARAMETER_ASSIGNMENT = "="
TEXT_ENCODING = "utf-8"
#: D10: the error handler the wrapper runner decodes the standard output with; encoding with it gives back the bytes
#: the wrapper wrote.
STDOUT_ERRORS = "surrogateescape"

# The product GitLab wrapper's subcommands and their options (src/payload/scripts/gitlab_api/commands/).
CALL_SUBCOMMAND = "call"
MR_GROUP = "mr"
MR_CREATE = "create"
SOURCE_OPTION = "--source"
TARGET_OPTION = "--target"
TITLE_OPTION = "--title"
PATH_OPTION = "--path"
QUERY_OPTION = "--query"
RAW_FIELD_OPTION = "-f"
ENDPOINT_OPTION = "--endpoint"

# ``--endpoint`` (issue #63 design.md D1): the emoji-reaction records of ``gitlab_api/families/plan.py`` on their
# merge-request endpoint, and what the addition gives (docs.gitlab.com/api/emoji_reactions/).
EMOJI_ADDITION = "plan#add-an-emoji-reaction-to-a-resource"
EMOJI_LISTING = "plan#list-all-emoji-reactions-for-a-resource"
MERGE_REQUEST_EMOJI_ADDITION = "POST /projects/:id/merge_requests/:merge_request_iid/award_emoji"
MERGE_REQUEST_EMOJI_LISTING = "GET /projects/:id/merge_requests/:merge_request_iid/award_emoji"
MERGE_REQUEST_IID_PARAMETER = "merge_request_iid"
EMOJI_NAME_PARAMETER = "name"
EMOJI = "thumbsup"
AWARDABLE_MERGE_REQUEST = "MergeRequest"

# A ``[.format]`` suffix (issue #63 design.md D3): the archive record of ``gitlab_api/families/create.py``, its suffix
# value and the seed commit it is asked for.
ARCHIVE_RECORD = "create#retrieve-file-archive-from-a-repository"
FORMAT_PARAMETER = "format"
ZIP_FORMAT = "zip"
SHA_PARAMETER = "sha"
#: The one file of the seed commit ``initialize_with_readme`` creates.
SEED_FILE = "README.md"
ARCHIVE_PATH_SEPARATOR = "/"
GIT_SHOW = "show"
REVISION_PATH_SEPARATOR = ":"

# The fields of the printed records: a merge request and an emoji reaction (docs.gitlab.com/api/merge_requests/,
# docs.gitlab.com/api/emoji_reactions/).
FIELD_IID = "iid"
FIELD_ID = "id"
FIELD_NAME = "name"
FIELD_TITLE = "title"
FIELD_STATE = "state"
FIELD_SOURCE_BRANCH = "source_branch"
FIELD_TARGET_BRANCH = "target_branch"
FIELD_AWARDABLE_TYPE = "awardable_type"
STATE_OPENED = "opened"

# What the endpoint test creates: D6's ``forge-<purpose>-<hex>`` branch and a merge request naming the run.
BRANCH = "forge-emoji-{hex}"
MERGE_REQUEST_TITLE = "Forge emoji reaction of run {run_id}"


def _support() -> ModuleType:
    """The suite's support module as ``conftest.py`` loaded it under ``SUPPORT_MODULE`` (D10)."""
    module = sys.modules.get(SUPPORT_MODULE)
    assert module is not None, f"no module is loaded under {SUPPORT_MODULE}; conftest.py loads ephemeral.py there"
    return module


def _assignment(*, name: str, value: str) -> str:
    """A ``call`` parameter's ``<name>=<value>``."""
    return name + PARAMETER_ASSIGNMENT + value


def _invoke(*, project: Any, arguments: Sequence[str]) -> Any:
    """The ``Invocation`` of the product wrapper run in the clone with ``arguments``; an exit other than 0 fails the
    test with the wrapper's standard error."""
    invocation = project.wrapper.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{command}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation


def _record(*, project: Any, arguments: Sequence[str]) -> Mapping[str, Any]:
    """The one JSON object the product wrapper printed for ``arguments``."""
    answer = _invoke(project=project, arguments=arguments).json()
    assert isinstance(answer, dict), f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON object: {answer!r}"
    return answer


def _records(*, project: Any, arguments: Sequence[str]) -> List[Mapping[str, Any]]:
    """The JSON array of objects the product wrapper printed for ``arguments``."""
    answer = _invoke(project=project, arguments=arguments).json()
    assert isinstance(answer, list) and all(isinstance(item, dict) for item in answer), (
        f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON array of objects: {answer!r}"
    )
    return answer


def _git_output(*, project: Any, arguments: Sequence[str]) -> str:
    """The standard output of git run in the clone with ``arguments``, as the git runner read it; an exit other than 0
    fails the test with git's standard error."""
    invocation = project.git.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == GIT_EXIT_OK, (
        f"`git {command}` exited {invocation.returncode}, not {GIT_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return str(invocation.stdout)


def _read_as_git_output(*, data: bytes) -> str:
    """``data`` read as the git runner reads git's standard output: UTF-8 in text mode, where "all line endings in the
    output will be converted to '\\n'" (docs.python.org ``subprocess``, "Frequently Used Arguments"), as
    ``io.TextIOWrapper`` reads with ``newline=None``."""
    return io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=data), encoding=TEXT_ENCODING, newline=None).read()


def _merge_request_view(*, merge_request: Mapping[str, Any]) -> Dict[str, Any]:
    """What the endpoint test knows of its merge request in advance: its source and target branches, title and
    state."""
    fields = (FIELD_SOURCE_BRANCH, FIELD_TARGET_BRANCH, FIELD_TITLE, FIELD_STATE)
    return {field: merge_request.get(field) for field in fields}


def test_an_endpoint_named_by_endpoint(ephemeral_project: Any) -> None:
    """``--endpoint`` names the merge-request endpoint of an ID that several records declare: the reaction added there
    is the merge request's, and the listing on the same endpoint answers it alone."""
    project = ephemeral_project
    branch = BRANCH.format(hex=uuid.uuid4().hex)
    title = MERGE_REQUEST_TITLE.format(run_id=project.run_id)
    _support().push_branch(git=project.git, default_branch=project.default_branch, branch=branch)

    created = _record(
        project=project,
        arguments=[
            MR_GROUP,
            MR_CREATE,
            SOURCE_OPTION,
            branch,
            TARGET_OPTION,
            project.default_branch,
            TITLE_OPTION,
            title,
        ],
    )
    iid = created.get(FIELD_IID)
    assert isinstance(iid, int) and not isinstance(iid, bool), (
        f"the created merge request has no {FIELD_IID}: {created}"
    )
    expected = {
        FIELD_SOURCE_BRANCH: branch,
        FIELD_TARGET_BRANCH: project.default_branch,
        FIELD_TITLE: title,
        FIELD_STATE: STATE_OPENED,
    }
    assert _merge_request_view(merge_request=created) == expected, f"the created merge request is {created}"
    merge_request = _assignment(name=MERGE_REQUEST_IID_PARAMETER, value=str(iid))

    added = _record(
        project=project,
        arguments=[
            CALL_SUBCOMMAND,
            EMOJI_ADDITION,
            ENDPOINT_OPTION,
            MERGE_REQUEST_EMOJI_ADDITION,
            PATH_OPTION,
            merge_request,
            RAW_FIELD_OPTION,
            _assignment(name=EMOJI_NAME_PARAMETER, value=EMOJI),
        ],
    )
    assert (added.get(FIELD_NAME), added.get(FIELD_AWARDABLE_TYPE)) == (EMOJI, AWARDABLE_MERGE_REQUEST), (
        f"`{EMOJI_ADDITION}` on `{MERGE_REQUEST_EMOJI_ADDITION}` answered {added}, not the {FIELD_NAME} {EMOJI} with "
        f"the {FIELD_AWARDABLE_TYPE} {AWARDABLE_MERGE_REQUEST}"
    )
    reaction = added.get(FIELD_ID)
    assert isinstance(reaction, int) and not isinstance(reaction, bool), (
        f"the added reaction has no {FIELD_ID}: {added}"
    )

    listed = _records(
        project=project,
        arguments=[
            CALL_SUBCOMMAND,
            EMOJI_LISTING,
            ENDPOINT_OPTION,
            MERGE_REQUEST_EMOJI_LISTING,
            PATH_OPTION,
            merge_request,
        ],
    )
    assert [(each.get(FIELD_ID), each.get(FIELD_NAME)) for each in listed] == [(reaction, EMOJI)], (
        f"`{EMOJI_LISTING}` on `{MERGE_REQUEST_EMOJI_LISTING}` of merge request !{iid} lists {listed}, not the one "
        f"reaction {reaction} {EMOJI}"
    )


def test_a_format_suffix(ephemeral_project: Any) -> None:
    """A ``[.format]`` suffix given as ``--path format=zip`` sends the zip archive of the seed commit, printed as its
    bytes: one file, the seed's ``README.md``, under the archive's top directory."""
    project = ephemeral_project
    seed = project.seed_sha
    invocation = _invoke(
        project=project,
        arguments=[
            CALL_SUBCOMMAND,
            ARCHIVE_RECORD,
            PATH_OPTION,
            _assignment(name=FORMAT_PARAMETER, value=ZIP_FORMAT),
            QUERY_OPTION,
            _assignment(name=SHA_PARAMETER, value=seed),
        ],
    )
    data = invocation.stdout.encode(encoding=TEXT_ENCODING, errors=STDOUT_ERRORS)
    assert zipfile.is_zipfile(filename=io.BytesIO(initial_bytes=data)), (
        f"`{ARCHIVE_RECORD}` of the seed {seed} printed {len(data)} bytes that are no zip archive"
    )
    with zipfile.ZipFile(file=io.BytesIO(initial_bytes=data)) as archive:
        damaged = archive.testzip()
        assert damaged is None, f"the archive's member {damaged} fails its CRC check"
        files = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in files]
        assert len(files) == 1 and names[0].endswith(ARCHIVE_PATH_SEPARATOR + SEED_FILE), (
            f"the archive of the seed {seed} holds the files {names}, not one ending "
            f"{ARCHIVE_PATH_SEPARATOR}{SEED_FILE}"
        )
        member = archive.read(name=files[0])
    expected = _git_output(project=project, arguments=[GIT_SHOW, seed + REVISION_PATH_SEPARATOR + SEED_FILE])
    assert _read_as_git_output(data=member) == expected, (
        f"the archive's {names[0]} does not hold the text of `git {GIT_SHOW} {seed}{REVISION_PATH_SEPARATOR}"
        f"{SEED_FILE}`"
    )
