"""Tests for ``gitlab_api/families/deploy.py``: the records of the deploy endpoint family, the model registry API's
three ``ml_models`` file keys (issue #40, ``requirements.md`` AC-1.2 to AC-1.6, AC-2.3, AC-2.6, AC-3.2; ``design.md``
D4, D6).

What is pinned:

- nothing is pending, and the records' operation IDs are the References of the three ``rest/deploy.md`` rows of
  ``docs/api-reference/gitlab/operations-index.md`` (AC-1.2, AC-1.6);
- no record declares the ``openapi-only#`` Reference of those keys: ``registry.lookup`` refuses each as an ID no
  record declares, with the ``openapi_only`` family among the families it reads (AC-1.2);
- no record has a ``Param``, since each section's rows are ``In`` ``path`` (the ``(*path/)`` group's ``path``
  included, AC-1.4) or, for "Send the file", the raw body's ``file`` row; ``deploy#send-the-file`` is the raw-body
  record, sent as ``application/octet-stream``, and the other two have no media type; every record has a JSON body,
  no ``fixed`` pairs and ``Paging.NONE`` (AC-1.3, AC-1.5, AC-3.2);
- through the product's ``main(argv=["call", ...])`` against the fake host, the ``(*path/)`` group is sent with its
  ``/`` kept when ``--path path`` is given and left out when it is not, ``id`` the configured project (AC-2.3,
  AC-2.6);
- ``call deploy#send-the-file ... --input -`` sends the bytes of standard input's binary buffer, unchanged, as the
  whole body of one ``PUT`` with ``Content-Type: application/octet-stream`` (AC-3.2).

Every expected operation ID, media type and URL is a literal table transcribed from ``operations-index.md`` and
``rest/deploy.md``, never read from the records. The names and ``In`` of the rows, and one call of every record, are
proven by ``test/test_gitlab_wrapper_contract.py``.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_deploy.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import io
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_deploy_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.deploy"
OPENAPI_ONLY_MODULE = "families.openapi_only"
REGISTRY = "registry"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CALL = "call"
REST_BASE = fixtures.REST_BASE

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-deploy-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
HEADER_CONTENT_TYPE = "Content-Type"
# The media type a raw-body record's bytes are sent as (requirements.md AC-3.2, design.md D5).
MEDIA_TYPE_OCTET_STREAM = "application/octet-stream"

METHOD_GET = "GET"
METHOD_PUT = "PUT"
# The `--path` option of `call` (#41 design.md D2); `id` defaults to the configured project on a `/projects/:id` path
# (#41 AC-1.8), so no case gives it.
OPTION_PATH = "--path"
ASSIGNED = "="
# The text `call`'s raw-body option reads standard input for, as `gh api --input -` spells it.
INPUT_FROM_STDIN = "-"
# The `sys` attribute the upload test replaces with a text layer over the bytes, and that layer's encoding: strict
# UTF-8, which fails on `\xff`.
ATTRIBUTE_STDIN = "stdin"
STDIN_ENCODING = "utf-8"

# The `registry.BodyFormat` and `registry.Paging` member names the tables hold.
BODY_JSON = "JSON"
PAGING_NONE = "NONE"

# --- The tables, transcribed from the reference -----------------------------------------------------------------

# The Reference of every row of operations-index.md that links rest/deploy.md, written `deploy#<anchor>`, in index
# order. Each Reference carries one row.
OP_AUTHORIZE_THE_UPLOAD = "deploy#authorize-the-upload"  # PUT …/files/(*path/):file_name/authorize
OP_DOWNLOAD_A_MODEL_FILE = "deploy#download-a-machine-learning-model-package-file"  # GET …/files/(*path/):file_name
OP_SEND_THE_FILE = "deploy#send-the-file"  # PUT …/files/(*path/):file_name
OPERATION_IDS: Tuple[str, ...] = (OP_AUTHORIZE_THE_UPLOAD, OP_DOWNLOAD_A_MODEL_FILE, OP_SEND_THE_FILE)

# The `rest/openapi-only.md` Reference of each of the same three keys, in index order: no record declares any of them
# (AC-1.2). `openapi-only#no-such-operation` is an ID no index row carries, refused as unknown.
OPENAPI_ONLY_MODEL_IDS: Tuple[str, ...] = (
    "openapi-only#workhorse-authorize-model-package-file",
    "openapi-only#download-an-ml_model-package-file",
    "openapi-only#workhorse-upload-model-package-file",
)
UNDECLARED_ID = "openapi-only#no-such-operation"
ID_MARKER = "<id>"

# The media type of each record's raw body: "Send the file"'s `file` row is the body Workhorse's requestBodyUploader
# stores unparsed (design.md D4), and the other two records send no raw body.
MEDIA_TYPES: Dict[str, Optional[str]] = {
    OP_AUTHORIZE_THE_UPLOAD: None,
    OP_DOWNLOAD_A_MODEL_FILE: None,
    OP_SEND_THE_FILE: MEDIA_TYPE_OCTET_STREAM,
}

# --- The calls ----------------------------------------------------------------------------------------------------

MODEL_VERSION_ID = f"model_version_id{ASSIGNED}3"
FILE_NAME = f"file_name{ASSIGNED}model.bin"
GROUP_PATH = f"path{ASSIGNED}dir/sub"
UPLOAD_GROUP_PATH = f"path{ASSIGNED}dir"
MODEL_ARGV: Tuple[str, ...] = (OPTION_PATH, MODEL_VERSION_ID, OPTION_PATH, FILE_NAME)
FILES_URL = f"{REST_BASE}/projects/{PROJECT_ID}/packages/ml_models/3/files"
DOWNLOAD_IN_GROUP_URL = f"{FILES_URL}/dir/sub/model.bin"
DOWNLOAD_URL = f"{FILES_URL}/model.bin"
AUTHORIZE_URL = f"{FILES_URL}/model.bin/authorize"
UPLOAD_URL = f"{FILES_URL}/dir/model.bin"
# Model bytes with a CR LF line end, which a read through the text layer would translate to LF, and the byte 0xFF,
# which no UTF-8 decoder accepts.
MODEL_BYTES = b"model weights\r\n\xff\x00 tail\r\n"


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory; the entry script reads ``config/gitlab.json`` under it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` (``families.deploy`` for the family) inside a test, after asserting its file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def unknown_refusal(*, registry: ModuleType, operation_id: str) -> str:
    """``registry.lookup``'s ``ValueError`` message for ``operation_id``, the ID replaced by ``ID_MARKER``; the test
    fails when ``lookup`` returns a record for it."""
    with pytest.raises(ValueError, match=re.escape(operation_id)) as refusal:
        registry.lookup(operation_id=operation_id)
    return str(refusal.value).replace(operation_id, ID_MARKER)


# --- AC-1.2, AC-1.6: nothing is pending ---------------------------------------------------------------------------


def test_nothing_is_pending() -> None:
    """AC-1.2, AC-1.6: ``PENDING`` is empty, and ``OPERATIONS`` declares one record per Reference of the family's index
    rows, each ID once."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"PENDING holds {len(pending)} key(s); each has its record (AC-1.6): {pending}"
    declared = sorted(record.operation_id for record in family.OPERATIONS)
    missing = sorted(frozenset(OPERATION_IDS) - frozenset(declared))
    unknown = sorted(frozenset(declared) - frozenset(OPERATION_IDS))
    assert declared == sorted(OPERATION_IDS), (
        f"OPERATIONS declares {len(declared)} record(s), the index has {len(OPERATION_IDS)} References; missing: "
        f"{missing}; not a Reference of the family: {unknown}"
    )


# --- AC-1.2: the ml_models file keys are deploy's -------------------------------------------------------------------


def test_no_record_declares_an_openapi_only_model_id() -> None:
    """AC-1.2: the three ``ml_models`` file keys are ``deploy``'s, so ``registry.lookup``, reading the ``openapi_only``
    family among the others, refuses the ``openapi-only#`` Reference of each as it refuses an ID no record declares —
    not as one declared twice."""
    registry = gitlab_module(name=REGISTRY)
    openapi_only = gitlab_module(name=OPENAPI_ONLY_MODULE)
    discovered = [family.__name__ for family in registry.discover_families()]
    assert openapi_only.__name__ in discovered, (
        f"lookup reads the family a model record of rest/openapi-only.md would be declared in; it reads {discovered}"
    )
    refused_as_unknown = unknown_refusal(registry=registry, operation_id=UNDECLARED_ID)
    for operation_id in OPENAPI_ONLY_MODEL_IDS:
        assert unknown_refusal(registry=registry, operation_id=operation_id) == refused_as_unknown, (
            f"{operation_id} is refused as an ID no record declares (AC-1.2)"
        )


# --- AC-1.3, AC-1.4, AC-1.5, AC-3.2: every record typed as its section ------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-1.3, AC-1.4, AC-1.5, AC-3.2: no record has a ``Param`` — every row is ``In`` ``path``, the ``(*path/)``
    group's ``path`` included, but "Send the file"'s ``file``, which is its raw body; ``deploy#send-the-file`` sends
    that body as ``application/octet-stream`` and the other two send none; every record has a JSON body, no ``fixed``
    pairs and ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    records = tuple(family.OPERATIONS)
    params = {record.operation_id: tuple(record.params) for record in records}
    assert params == {operation_id: () for operation_id in OPERATION_IDS}, (
        f"each of the three records declares no Param: its rows are path parameters or the raw body (AC-1.3, AC-1.4, "
        f"AC-3.2): {params}"
    )
    media_types = {record.operation_id: record.content_type for record in records}
    assert media_types == MEDIA_TYPES, (
        f"deploy#send-the-file is the raw-body record, application/octet-stream; the others have none (AC-3.2): "
        f"{media_types}"
    )
    shapes = {record.operation_id: (record.body.name, tuple(record.fixed), record.paging.name) for record in records}
    assert shapes == {operation_id: (BODY_JSON, (), PAGING_NONE) for operation_id in OPERATION_IDS}, (
        f"every record has body BodyFormat.JSON, no fixed pairs and Paging.NONE (AC-1.3, AC-1.5): {shapes}"
    )


# --- AC-2.3, AC-2.6: the optional group sent only when given --------------------------------------------------------


class GroupCase(NamedTuple):
    """A call of a record whose path holds ``(*path/)``, and the one request it sends."""

    argv: Tuple[str, ...]
    method: str
    url: str


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        pytest.param(
            GroupCase(
                argv=(OP_DOWNLOAD_A_MODEL_FILE, *MODEL_ARGV, OPTION_PATH, GROUP_PATH),
                method=METHOD_GET,
                url=DOWNLOAD_IN_GROUP_URL,
            ),
            id="download-group-given",
        ),
        pytest.param(
            GroupCase(argv=(OP_DOWNLOAD_A_MODEL_FILE, *MODEL_ARGV), method=METHOD_GET, url=DOWNLOAD_URL),
            id="download-group-left-out",
        ),
        pytest.param(
            GroupCase(argv=(OP_AUTHORIZE_THE_UPLOAD, *MODEL_ARGV), method=METHOD_PUT, url=AUTHORIZE_URL),
            id="authorize-group-left-out",
        ),
    ],
)
def test_the_optional_group_is_sent_only_when_given(
    case: GroupCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.3, AC-2.6: with ``--path model_version_id=3`` and ``--path file_name=model.bin``, the call exits 0 and
    sends one request to the configured project: ``--path path=dir/sub`` writes the group as ``dir/sub/`` with its
    ``/`` kept, and a call without ``path`` leaves the whole group out and is refused nothing for it."""
    # Any request is answered, so a wrong URL fails this test on its oracle below, not on the fake's unscripted error.
    fake_gitlab.script_next()
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], (
        "one request, the group written when its parameter is given and left out when it is not (AC-2.3)"
    )


# --- AC-3.2: the upload sends the bytes as its body -----------------------------------------------------------------


def test_the_upload_sends_the_bytes_as_its_body(
    project: Path, fake_gitlab: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3.2: ``call deploy#send-the-file --path model_version_id=3 --path path=dir --path file_name=model.bin
    --input -``, standard input a text layer over bytes holding a CR LF line end and the byte 0xFF, exits 0 and sends
    one ``PUT`` to the configured project's file whose body is those bytes, unchanged, read from standard input's
    binary buffer, with ``Content-Type: application/octet-stream``."""
    option_input = "--input"  # call's raw-body option (design.md D5)
    argv = (OP_SEND_THE_FILE, *MODEL_ARGV, OPTION_PATH, UPLOAD_GROUP_PATH, option_input, INPUT_FROM_STDIN)
    stdin = io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=MODEL_BYTES), encoding=STDIN_ENCODING)
    monkeypatch.setattr(target=sys, name=ATTRIBUTE_STDIN, value=stdin)
    # Any request is answered, so a wrong URL fails this test on its oracle below, not on the fake's unscripted error.
    fake_gitlab.script_next()
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_PUT, UPLOAD_URL)], (
        "one PUT to the record's path, the group written and id the configured project"
    )
    upload = fake_gitlab.requests[0]
    assert upload.header(name=HEADER_CONTENT_TYPE) == MEDIA_TYPE_OCTET_STREAM, (
        f"the raw body's Content-Type (AC-3.2): {upload.header(name=HEADER_CONTENT_TYPE)!r}"
    )
    assert upload.body == MODEL_BYTES, f"the body sent is not the bytes of standard input (AC-3.2): {upload.body!r}"
