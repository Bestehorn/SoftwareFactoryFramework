"""Tests of the ``git`` family's records (``github_api/families/git.py``; issue #27 AC-1, AC-3, AC-4, AC-6, AC-7).

Installed from ``src/payload/test/test_github_api_git.py`` to ``test/test_github_api_git.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every expected value here is transcribed from
``docs/api-reference/github/rest/git.md`` and ``conventions.md``, never read from the records or from
``commands/call.py``'s ``GATED_OPERATIONS``:

- ``GIT_OPERATION_IDS``: the 13 operations of ``rest/git.md``, each of which has one record and none of which is
  pending (AC-1);
- ``MULTI_SEGMENT_PARAMETERS``: each operation whose ``Parameter`` table has a row reading "may contain ``/``
  (multi-segment path)", with those rows' names (AC-3);
- ``LIST_CASES``: one golden case per operation whose section has a ``Paging:`` line or a ``Link`` response header
  (AC-4, AC-6). In ``rest/git.md`` that is ``git/list-matching-refs`` alone, whose ``200`` is an array (no item key)
  and which documents no ``per_page``, so its two refs arrive on one page. Its ``ref`` holds ``/``
  (``heads/feature/login``, the shape of ``conventions.md`` "Path parameters"), and its route is on that path with the
  slashes literal, so a ``ref`` encoded as one segment reaches no route (AC-3);
- ``BRANCH_WRITING_IDS``: AC-7's IDs of this family, ``git/create-ref`` and ``git/update-ref``; each case gives a value
  for every parameter its section documents, so only the gate can refuse it.

``github_wrapper_fixtures.run_product_case`` (loaded by path) runs a case through the product entry script's
``main(argv=...)`` in the fixture project (``origin`` ``o/r``) against the fake GitHub host, and judges its exit code,
its standard output exactly, its requests other than ``GET`` (none at all for a refusal) and that every request was
routed. A refusal's log records are judged by ``fx.assert_log`` on ``caplog.records``. These rows are not in ``CASES``,
so the fork never runs them. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_api_git.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Tuple

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

REGISTRY = "registry"
TRANSPORT = "transport"
FAMILY_MODULE = f"{fx.PACKAGE}.families.git"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / "git.py"

AC_6 = "AC-6"
AC_7 = "AC-7"

CALL = "call"
OPTION_PATH = "--path"
OPTION_RAW_FIELD = "--raw-field"
OPTION_FIELD = "--field"
OPERATION_ID_INDEX = 1  # argv is ``call <operation-id> …``
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value from it.
STDERR_READ_BY_THE_RUN = ""

# rest/git.md, in its order: blobs, commits, refs, tags, trees.
OP_CREATE_BLOB = "git/create-blob"
OP_GET_BLOB = "git/get-blob"
OP_CREATE_COMMIT = "git/create-commit"
OP_GET_COMMIT = "git/get-commit"
OP_LIST_MATCHING_REFS = "git/list-matching-refs"
OP_GET_REF = "git/get-ref"
OP_CREATE_REF = "git/create-ref"
OP_UPDATE_REF = "git/update-ref"
OP_DELETE_REF = "git/delete-ref"
OP_CREATE_TAG = "git/create-tag"
OP_GET_TAG = "git/get-tag"
OP_CREATE_TREE = "git/create-tree"
OP_GET_TREE = "git/get-tree"

#: Every operation of ``rest/git.md`` ("GitHub REST API — ``git`` (13 operations)").
GIT_OPERATION_IDS: Tuple[str, ...] = (
    OP_CREATE_BLOB,
    OP_GET_BLOB,
    OP_CREATE_COMMIT,
    OP_GET_COMMIT,
    OP_LIST_MATCHING_REFS,
    OP_GET_REF,
    OP_CREATE_REF,
    OP_UPDATE_REF,
    OP_DELETE_REF,
    OP_CREATE_TAG,
    OP_GET_TAG,
    OP_CREATE_TREE,
    OP_GET_TREE,
)

PARAM_REF = "ref"
PARAM_COMMIT_SHA = "commit_sha"
PARAM_TREE_SHA = "tree_sha"
#: The path parameters whose ``Parameter`` row in ``rest/git.md`` reads "may contain ``/`` (multi-segment path)", by
#: operation; every other operation of the family has none.
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {
    OP_GET_COMMIT: frozenset({PARAM_COMMIT_SHA}),
    OP_LIST_MATCHING_REFS: frozenset({PARAM_REF}),
    OP_GET_REF: frozenset({PARAM_REF}),
    OP_UPDATE_REF: frozenset({PARAM_REF}),
    OP_DELETE_REF: frozenset({PARAM_REF}),
    OP_GET_TREE: frozenset({PARAM_TREE_SHA}),
}

# AC-6: ``git/list-matching-refs`` (``GET /repos/{owner}/{repo}/git/matching-refs/{ref}``; ``200``: an array of
# ``git-ref``, headers ``Link``). ``ref`` omits the ``refs/`` prefix and keeps its ``/`` (``conventions.md`` "Path
# parameters").
FIELD_OBJECT = "object"
FIELD_TYPE = "type"
OBJECT_COMMIT = "commit"
REF_PREFIX = "refs/"
MATCHED_REF = "heads/feature/login"
MATCHING_REFS_PATH = f"{fx.REPOSITORY_PATH}/git/matching-refs/{MATCHED_REF}"
SECOND_SHA = "cafebabe" * 5  # a full commit sha: 40 hex characters


def ref_entry(*, ref: str, sha: str) -> Dict[str, Any]:
    """A reference as ``git/list-matching-refs`` lists it (a ``git-ref``), cut to a few fields; ``ref`` is given
    without its ``refs/`` prefix."""
    commits_url = f"{fx.API_ORIGIN}{fx.REPOSITORY_PATH}/git/commits/{sha}"
    return {
        fx.FIELD_REF: f"{REF_PREFIX}{ref}",
        fx.FIELD_URL: f"{fx.API_ORIGIN}{fx.REPOSITORY_PATH}/git/{REF_PREFIX}{ref}",
        FIELD_OBJECT: {FIELD_TYPE: OBJECT_COMMIT, fx.FIELD_SHA: sha, fx.FIELD_URL: commits_url},
    }


#: The two refs whose names start with ``MATCHED_REF``.
MATCHED_REFS: Tuple[Dict[str, Any], ...] = (
    ref_entry(ref=MATCHED_REF, sha=fx.HEAD_SHA),
    ref_entry(ref=f"{MATCHED_REF}-v2", sha=SECOND_SHA),
)

#: One golden case per ``Paging.LINK`` operation of ``rest/git.md`` (#28 D8): ``call <id>`` with ``--path`` for each
#: path parameter but ``owner`` and ``repo`` (no ``--query per_page=1``: the section documents no ``per_page``), a
#: list route of two items (no item key: the ``200`` is an array), and both items printed as one JSON array.
LIST_CASES: Tuple[Any, ...] = (
    fx.GoldenCase(
        name=f"{AC_6}/exit-0/list-matching-refs-of-a-ref-holding-a-slash",
        argv=(CALL, OP_LIST_MATCHING_REFS, OPTION_PATH, f"{PARAM_REF}={MATCHED_REF}"),
        stdout=fx.printed_json(value=list(MATCHED_REFS)),
        exit_code=fx.EXIT_OK,
        routes=(fx.ListRouteSpec(url=MATCHING_REFS_PATH, items=MATCHED_REFS),),
    ),
)

# AC-7: ``git/create-ref`` creates a ref (``refs/heads/…`` creates a branch), ``git/update-ref`` moves one; both are
# refused by ``call``, and ``git/delete-ref`` stays callable (UB-4).
#: AC-7's IDs of this family, as a literal: never read from ``GATED_OPERATIONS``.
BRANCH_WRITING_IDS: Tuple[str, ...] = (OP_CREATE_REF, OP_UPDATE_REF)
BODY_REF = "ref"
BODY_SHA = "sha"
BODY_FORCE = "force"
TOPIC_REF = "heads/topic"
#: A value for every parameter each section documents (``git/create-ref``: body ``ref`` and ``sha``;
#: ``git/update-ref``: path ``ref``, body ``sha`` and ``force``), so no refusal but the gate's applies.
BRANCH_WRITING_ARGUMENTS: Dict[str, Tuple[str, ...]] = {
    OP_CREATE_REF: (
        OPTION_RAW_FIELD,
        f"{BODY_REF}={REF_PREFIX}{TOPIC_REF}",
        OPTION_RAW_FIELD,
        f"{BODY_SHA}={fx.HEAD_SHA}",
    ),
    OP_UPDATE_REF: (
        OPTION_PATH,
        f"{PARAM_REF}={TOPIC_REF}",
        OPTION_RAW_FIELD,
        f"{BODY_SHA}={fx.HEAD_SHA}",
        OPTION_FIELD,
        f"{BODY_FORCE}=false",
    ),
}
#: AC-7's wording: the refusal says that no subcommand sends the ID ("no subcommand", "no compatibility subcommand").
NO_SUBCOMMAND = r"(?i)\bno\s+(?:\w+\s+)?subcommand\b"
#: What ``GATED_OPERATIONS`` maps AC-7's IDs to; the refusal is worded for it, never rendering it.
NONE_RENDERED = "None"


def named(*, name: str) -> str:
    """A pattern for ``name`` as a refusal renders a name: with ``json.dumps`` (#28 design D4)."""
    return re.escape(json.dumps(obj=name))


def _branch_writing_cases() -> Tuple[Any, ...]:
    """AC-7: each of ``BRANCH_WRITING_IDS``, called with every documented parameter, exits 2 with nothing on standard
    output and no request; one log record names the ID and that no subcommand sends it, and none renders ``None``."""
    return tuple(
        fx.GoldenCase(
            name=f"{AC_7}/exit-2/{operation_id}",
            argv=(CALL, operation_id, *BRANCH_WRITING_ARGUMENTS[operation_id]),
            stdout="",
            exit_code=fx.EXIT_REFUSED,
            log=fx.LogExpectation(refusal=(named(name=operation_id), NO_SUBCOMMAND), withheld=(NONE_RENDERED,)),
        )
        for operation_id in BRANCH_WRITING_IDS
    )


BRANCH_WRITING_CASES = _branch_writing_cases()


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def _family() -> ModuleType:
    """``github_api.families.git`` from the product scripts directory beside this suite; one imported from any other
    directory fails the calling test."""
    fx.import_api_module(name=REGISTRY)  # puts the product scripts directory on ``sys.path``
    module = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}, not {FAMILY_FILE}"
    return module


def _declared_ids(*, family: ModuleType) -> List[str]:
    """The operation ID of every record of ``family.OPERATIONS``, in order, a duplicate kept."""
    return [record.operation_id for record in family.OPERATIONS]


def _record_of(*, operation_id: str) -> Any:
    """The one record of ``families/git.py`` with ``operation_id``; none, or more than one, fails the calling test."""
    matches = [record for record in _family().OPERATIONS if record.operation_id == operation_id]
    assert len(matches) == 1, (
        f"{json.dumps(obj=operation_id)}: families/git.py declares {len(matches)} records with this ID, one expected"
    )
    return matches[0]


def test_nothing_is_pending() -> None:
    """AC-1: ``git.PENDING`` is empty, and ``git.OPERATIONS`` holds one record for each operation of
    ``rest/git.md``, and no other."""
    family = _family()

    assert family.PENDING == frozenset(), f"families/git.py still has pending IDs: {sorted(family.PENDING)}"
    declared = _declared_ids(family=family)
    assert sorted(declared) == sorted(GIT_OPERATION_IDS), (
        f"families/git.py declares {declared}; one record of each of {list(GIT_OPERATION_IDS)} is expected"
    )


@pytest.mark.parametrize(argnames="operation_id", argvalues=GIT_OPERATION_IDS)
def test_every_record_sends_the_default_version_and_media_type(operation_id: str) -> None:
    """AC-3: each record's ``api_version`` is ``API_VERSION_DEFAULT`` and its ``accept`` ``ACCEPT_JSON``. ``call`` and
    the compatibility subcommands send a record's version and media type on every request (#28 AC-1.2, in
    ``test_github_api_call.py``), and AC-7's records are refused before any request, so the record is the oracle."""
    transport = fx.import_api_module(name=TRANSPORT)
    record = _record_of(operation_id=operation_id)

    assert record.api_version == transport.API_VERSION_DEFAULT, f"{operation_id}: api_version {record.api_version!r}"
    assert record.accept == transport.ACCEPT_JSON, f"{operation_id}: accept {record.accept!r}"


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-3: ``{operation_id: multi_segment}`` over the records with a multi-segment parameter is exactly
    ``MULTI_SEGMENT_PARAMETERS``, the "may contain ``/``" rows of ``rest/git.md``."""
    family = _family()

    declared = {record.operation_id: record.multi_segment for record in family.OPERATIONS if record.multi_segment}

    assert declared == MULTI_SEGMENT_PARAMETERS, (
        f"families/git.py declares the multi-segment parameters {declared}; rest/git.md documents "
        f"{MULTI_SEGMENT_PARAMETERS}"
    )


def test_every_list_record_has_a_case() -> None:
    """AC-4: the family's ``Paging.LINK`` records are exactly the operations of ``LIST_CASES``, the sections with a
    ``Link`` response header; every other record of the family is ``Paging.NONE``."""
    registry = fx.import_api_module(name=REGISTRY)
    family = _family()

    listed = {record.operation_id for record in family.OPERATIONS if record.paging == registry.Paging.LINK}
    cased = {case.argv[OPERATION_ID_INDEX] for case in LIST_CASES}

    assert listed == cased, f"families/git.py pages {sorted(listed)} by Link; rest/git.md pages {sorted(cased)}"


@pytest.mark.parametrize(argnames="case", argvalues=LIST_CASES, ids=fx.case_name)
def test_a_list_record_prints_every_item(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6 (and AC-3 on the wire): ``call git/list-matching-refs`` with a ``ref`` holding ``/`` exits 0 and prints
    both refs the host serves as one indented JSON array; the request reached the route on the path with the slashes
    of ``ref`` literal, and every request was routed."""
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)


@pytest.mark.parametrize(argnames="case", argvalues=BRANCH_WRITING_CASES, ids=fx.case_name)
def test_a_branch_writing_record_is_refused(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-7: ``registry.lookup`` returns the family's record for the ID, and ``call <id>`` with every documented
    parameter exits 2 with no request, one log record naming the ID and that no subcommand sends it."""
    registry = fx.import_api_module(name=REGISTRY)
    operation_id = case.argv[OPERATION_ID_INDEX]
    declared = _record_of(operation_id=operation_id)

    assert registry.lookup(operation_id=operation_id) == declared, f"{operation_id}: lookup returns another record"
    caplog.set_level(level=logging.DEBUG)
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)
    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)
