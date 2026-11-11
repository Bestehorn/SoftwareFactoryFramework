"""Tests of the GitHub wrapper's ``users`` family, ``github_api/families/users.py`` (issue #29 ``change.md``; AC-1,
AC-2, AC-3).

Every expected value here is transcribed from ``docs/api-reference/github/operations-index.md``,
``docs/api-reference/github/rest/users.md`` and ``conventions.md``, never read from the records or from
``commands/call.py``:

- ``USERS_OPERATION_IDS``: the operation ID of every ``users/`` row of ``operations-index.md``, one per section of
  ``rest/users.md``; ``users/get-authenticated`` is among them, its record kept as it is (UB-1);
- ``MULTI_SEGMENT_PARAMETERS``: for each section with one, the path parameters whose ``Parameter`` row reads "may
  contain `/` (multi-segment path)" (AC-2);
- ``LIST_RECORDS``: each section with a ``Paging:`` line or a ``Link`` response header (AC-2), but
  ``users/list-attestations-bulk`` (``POST``, #28 D3): its path, the one key after "items in" (``None`` where the
  ``Paging:`` line reads "the response body is the array"), and whether its ``Parameter`` table documents
  ``per_page``.

``test_a_list_record_prints_every_item`` is #28 design D8's slice test (AC-3): one golden case per ``Paging.LINK``
record, argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page; standard output is both as one JSON array. ``users/list-attestations`` is called with a
``subject_digest`` holding ``/`` (``conventions.md`` "Path parameters" names ``subject_digest`` among the parameters
whose value may contain ``/``), whose route is reached only with the slash kept literal. Each case runs with
``fx.run_product_case`` through the product entry script's ``main(argv=...)`` in the fixture project (``origin``
``o/r``), which judges its exit code, its standard output exactly, its requests other than ``GET`` and that every
request was routed.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_users.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

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
FAMILY = "users"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_3 = "AC-3"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
PATH_OWNER = "owner"
PATH_REPO = "repo"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"

#: AC-1: every ``users/`` operation ID of ``operations-index.md``, one per section of ``rest/users.md``.
USERS_OPERATION_IDS: Tuple[str, ...] = (
    "users/add-email-for-authenticated-user",
    "users/add-social-account-for-authenticated-user",
    "users/block",
    "users/check-blocked",
    "users/check-following-for-user",
    "users/check-person-is-followed-by-authenticated",
    "users/create-gpg-key-for-authenticated-user",
    "users/create-public-ssh-key-for-authenticated-user",
    "users/create-ssh-signing-key-for-authenticated-user",
    "users/delete-attestations-bulk",
    "users/delete-attestations-by-id",
    "users/delete-attestations-by-subject-digest",
    "users/delete-email-for-authenticated-user",
    "users/delete-gpg-key-for-authenticated-user",
    "users/delete-public-ssh-key-for-authenticated-user",
    "users/delete-social-account-for-authenticated-user",
    "users/delete-ssh-signing-key-for-authenticated-user",
    "users/follow",
    "users/get-authenticated",
    "users/get-by-id",
    "users/get-by-username",
    "users/get-context-for-user",
    "users/get-gpg-key-for-authenticated-user",
    "users/get-public-ssh-key-for-authenticated-user",
    "users/get-ssh-signing-key-for-authenticated-user",
    "users/list",
    "users/list-attestations",
    "users/list-attestations-bulk",
    "users/list-blocked-by-authenticated-user",
    "users/list-emails-for-authenticated-user",
    "users/list-followed-by-authenticated-user",
    "users/list-followers-for-authenticated-user",
    "users/list-followers-for-user",
    "users/list-following-for-user",
    "users/list-gpg-keys-for-authenticated-user",
    "users/list-gpg-keys-for-user",
    "users/list-public-emails-for-authenticated-user",
    "users/list-public-keys-for-user",
    "users/list-public-ssh-keys-for-authenticated-user",
    "users/list-social-accounts-for-authenticated-user",
    "users/list-social-accounts-for-user",
    "users/list-ssh-signing-keys-for-authenticated-user",
    "users/list-ssh-signing-keys-for-user",
    "users/set-primary-email-visibility-for-authenticated-user",
    "users/unblock",
    "users/unfollow",
    "users/update-authenticated",
)

#: AC-2: for each ``users/`` section with one, its path parameters whose row reads "may contain `/` (multi-segment
#: path)". No body ``Field`` row of ``rest/users.md`` reads so.
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {
    "users/delete-attestations-by-subject-digest": frozenset({"subject_digest"}),
    "users/list-attestations": frozenset({"subject_digest"}),
}

#: A ``subject_digest`` holding ``/``: ``conventions.md`` "Path parameters" lists ``subject_digest`` among the
#: parameters whose value may contain ``/``, kept literal. Apart from the ``/`` it is alphanumeric (64 hex digits after
#: the algorithm name), so nothing else is encoded.
SUBJECT_DIGEST_WITH_A_SLASH = "sha256/" + "deadbeef" * 8


@dataclass(frozen=True)
class ListRecord:
    """A ``Paging.LINK`` record as its section documents it: the operation ID, the path template, the key its items
    sit under (``None``: the body is the array), whether it documents ``per_page``, and each path value the case gives
    in place of ``path_value``'s, as ``(name, value)`` pairs."""

    operation_id: str
    path: str
    item_key: Optional[str]
    per_page: bool
    values: Tuple[Tuple[str, str], ...] = ()


#: AC-2, AC-3: every ``users/`` section with a ``Paging:`` line or a ``Link`` response header, but
#: ``users/list-attestations-bulk`` (``POST``).
LIST_RECORDS: Tuple[ListRecord, ...] = (
    ListRecord(
        operation_id="users/list",
        path="/users",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-attestations",
        path="/users/{username}/attestations/{subject_digest}",
        item_key="attestations",
        per_page=True,
        values=(("subject_digest", SUBJECT_DIGEST_WITH_A_SLASH),),
    ),
    ListRecord(
        operation_id="users/list-blocked-by-authenticated-user",
        path="/user/blocks",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-emails-for-authenticated-user",
        path="/user/emails",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-followed-by-authenticated-user",
        path="/user/following",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-followers-for-authenticated-user",
        path="/user/followers",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-followers-for-user",
        path="/users/{username}/followers",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-following-for-user",
        path="/users/{username}/following",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-gpg-keys-for-authenticated-user",
        path="/user/gpg_keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-gpg-keys-for-user",
        path="/users/{username}/gpg_keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-public-emails-for-authenticated-user",
        path="/user/public_emails",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-public-keys-for-user",
        path="/users/{username}/keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-public-ssh-keys-for-authenticated-user",
        path="/user/keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-social-accounts-for-authenticated-user",
        path="/user/social_accounts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-social-accounts-for-user",
        path="/users/{username}/social_accounts",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-ssh-signing-keys-for-authenticated-user",
        path="/user/ssh_signing_keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="users/list-ssh-signing-keys-for-user",
        path="/users/{username}/ssh_signing_keys",
        item_key=None,
        per_page=True,
    ),
)

#: The two items every list case serves, one per page where the record documents ``per_page``.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def path_value(*, name: str) -> str:
    """A path parameter's test value: alphanumeric, so nothing needs encoding, and made from its name, so a value
    given under another name changes the path."""
    return f"{TEST_VALUE_PREFIX}{NON_ALPHANUMERIC.sub(repl='', string=name)}"


def path_values(*, listed: ListRecord) -> Dict[str, str]:
    """The value of each placeholder of ``listed.path``, in path order: the fixture's ``origin`` for ``owner`` and
    ``repo``, else the record's own value or ``path_value``'s."""
    origin = {PATH_OWNER: fx.OWNER, PATH_REPO: fx.REPOSITORY}
    given = dict(listed.values)
    return {
        name: origin.get(name, given.get(name, path_value(name=name)))
        for name in PATH_PLACEHOLDER.findall(string=listed.path)
    }


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written, a ``/`` kept literal."""
    return PATH_PLACEHOLDER.sub(repl=lambda match: values[match.group(1)], string=path)


def list_argv(*, listed: ListRecord, values: Mapping[str, str]) -> Tuple[str, ...]:
    """``call <id>``, ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, and ``--query
    per_page=1`` when the record documents ``per_page`` (#28 design D8)."""
    argv = [CALL, listed.operation_id]
    for name, value in values.items():
        if name not in ORIGIN_PARAMETERS:
            argv.extend((OPTION_PATH, f"{name}={value}"))
    if listed.per_page:
        argv.extend((OPTION_QUERY, QUERY_ONE_PER_PAGE))
    return tuple(argv)


def list_case(*, listed: ListRecord) -> Any:
    """#28 design D8's golden case of ``listed``: exit 0, standard output both items as one JSON array, against a list
    route serving them under the record's item key on its expanded path."""
    values = path_values(listed=listed)
    return fx.GoldenCase(
        name=f"{AC_3}/exit-0/{listed.operation_id}",
        argv=list_argv(listed=listed, values=values),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.ListRouteSpec(
                url=expanded(path=listed.path, values=values), items=LISTED_ITEMS, item_key=listed.item_key
            ),
        ),
    )


def list_record_name(listed: ListRecord) -> str:
    """The test id of a ``LIST_RECORDS`` row."""
    return listed.operation_id


def users_family() -> ModuleType:
    """``github_api.families.users``, imported from the ``scripts`` directory beside this suite
    (``fx.import_api_module`` puts it on ``sys.path``); a copy imported from anywhere else fails here."""
    fx.import_api_module(name=REGISTRY)
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def records_by_id(*, family: ModuleType) -> Dict[str, Any]:
    """Each ``RestOperation`` of ``family.OPERATIONS``, keyed by its operation ID."""
    registry = fx.import_api_module(name=REGISTRY)
    return {record.operation_id: record for record in family.OPERATIONS if isinstance(record, registry.RestOperation)}


def differences(*, declared: Mapping[str, Any], expected: Mapping[str, Any]) -> List[str]:
    """One line per ID whose value in ``declared`` is not its value in ``expected``, absent counted as a value."""
    return [
        f"{json.dumps(obj=operation_id)}: declared {declared.get(operation_id)!r}, "
        f"the section documents {expected.get(operation_id)!r}"
        for operation_id in sorted(set(declared) | set(expected))
        if declared.get(operation_id) != expected.get(operation_id)
    ]


def test_nothing_is_pending() -> None:
    """AC-1: ``PENDING`` is empty, and ``OPERATIONS`` holds one record of every ``users/`` ID of the index, none twice
    and none of another ID."""
    family = users_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    expected = frozenset(USERS_OPERATION_IDS)
    problems = []
    pending = frozenset(family.PENDING)
    if pending:
        problems.append(f"PENDING holds {len(pending)} IDs: {sorted(pending)}")
    missing = sorted(expected - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - expected)
    if extra:
        problems.append(f"records of IDs that are not the family's: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-2: every ``users/`` ID has a record, and each declares ``API_VERSION_DEFAULT`` and ``ACCEPT_JSON``, so
    ``call`` sends them."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=users_family())
    problems = []
    for operation_id in USERS_OPERATION_IDS:
        record = records.get(operation_id)
        if record is None:
            problems.append(f"{json.dumps(obj=operation_id)}: no record")
            continue
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{json.dumps(obj=operation_id)}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{json.dumps(obj=operation_id)}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-2: ``{operation_id: multi_segment}`` over the records with a multi-segment parameter is
    ``MULTI_SEGMENT_PARAMETERS``, the path parameters whose row reads "may contain `/` (multi-segment path)"."""
    records = records_by_id(family=users_family())
    declared = {
        operation_id: frozenset(record.multi_segment)
        for operation_id, record in records.items()
        if record.multi_segment
    }

    problems = differences(declared=declared, expected=MULTI_SEGMENT_PARAMETERS)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-2: the family's ``Paging.LINK`` records are exactly the sections of ``LIST_RECORDS``, so every other record,
    ``users/list-attestations-bulk`` included, is ``Paging.NONE``; and every ``Paging.NONE`` record's ``item_key`` is
    ``None``."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=users_family())
    paged = {operation_id for operation_id, record in records.items() if record.paging == registry.Paging.LINK}
    cased = {listed.operation_id for listed in LIST_RECORDS}
    keyed = sorted(
        operation_id
        for operation_id, record in records.items()
        if record.paging == registry.Paging.NONE and record.item_key is not None
    )
    problems = []
    if paged != cased:
        problems.append(
            f"Paging.LINK records without a case: {sorted(paged - cased)}; "
            f"cases without a Paging.LINK record: {sorted(cased - paged)}"
        )
    if keyed:
        problems.append(f"Paging.NONE records with an item_key: {keyed}")

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(argnames="listed", argvalues=LIST_RECORDS, ids=list_record_name)
def test_a_list_record_prints_every_item(
    listed: ListRecord, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record against a fake host serving two items under its
    item key prints both as one JSON array and exits 0, having asked for one page per item where the record documents
    ``per_page``; every request was routed, so a multi-segment value reached its path with its ``/``."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"
