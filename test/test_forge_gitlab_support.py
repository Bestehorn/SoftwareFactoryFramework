"""The GitLab forge suite's support logic (S): ``test/forge_gitlab/ephemeral.py`` exercised in the default collection.

``test/forge_gitlab/`` is the GitLab forge suite, run only by its own command (``python scripts/run_tests.py --workers 1
test/forge_gitlab``) against gitlab.com (issue #11, design D1). What its support module decides without the forge is
proven here: the refusal of a distributed run, naming that command (D1); the run id and the project path it gives,
which the product GitLab wrapper's guard accepts (D4, D2); the per-command credential helper git authenticates to
gitlab.com with, ``CLONE_GIT_HELPER`` (D3, D10); where the GitLab test credential file is found, and the CI step's write
of it (D8). Only local git runs (``git init``, ``git commit``, ``git worktree add``, ``git rev-parse``, ``git credential
fill``), in checkouts under pytest's ``tmp_path``, and every ``git credential fill`` is given ``-c credential.helper=``
first, so no helper a configuration file names is asked. No test opens a connection or needs a test credential file
(UB-1).

``ephemeral.py`` is loaded by path from inside each test body through ``_ephemeral``, under the ``sys.modules`` key its
``conftest.py`` uses, never at import and never in a fixture, and nothing at this module's level names one of its
symbols: this file collects whatever ``ephemeral.py`` holds, and a test whose symbol does not exist yet fails in its own
body (``_require``). A test double is built from the loaded module the same way, inside a helper a test body calls. The
product GitLab wrapper, whose ``EPHEMERAL_PROJECT_PREFIX`` and ``_is_ephemeral_project`` are the oracles of D4, is
loaded by path for the test that reads it, and its directory is on ``sys.path`` only until that test ends.

Run: ``python scripts/run_tests.py test/test_forge_gitlab_support.py`` (needs git on PATH).
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
EPHEMERAL_PATH = ROOT / "test" / "forge_gitlab" / "ephemeral.py"
#: The fixed ``sys.modules`` key of the by-path load, the key of ``test/forge_gitlab/conftest.py`` (D1); the module's
#: dataclasses resolve their module through it.
EPHEMERAL_MODULE = "forge_gitlab_ephemeral"

# D3, D8: the credential files, relative to a working tree or the clone.
CREDENTIALS_DIRECTORY = "credentials"
TEST_CREDENTIAL_NAME = "gitlab-sff-testing-pat.txt"
TEST_CREDENTIAL_FILE = Path(CREDENTIALS_DIRECTORY) / TEST_CREDENTIAL_NAME
#: The GitHub forge suite's test credential file: a decoy the GitLab lookup must pass over.
GITHUB_TEST_CREDENTIAL_NAME = "github-sff-testing-pat.txt"
GIT_DIRECTORY = ".git"
CLONE_GIT_TOKEN_FILE = Path(GIT_DIRECTORY) / "sff-forge-token"
#: The setup note every refusal of the test credential file points to (D7, D8).
SETUP_NOTE = "docs/forge-suite.md"
LINE_END = "\n"
WINDOWS_LINE_END = "\r\n"
TEXT_ENCODING = "utf-8"

# D1: xdist's ``worker_id`` fixture is ``master`` when xdist does not distribute, ``gw<n>`` in a worker; the GitLab
# forge suite's one-process command.
DISTRIBUTED_WORKER_ID = "gw0"
CONTROLLER_WORKER_ID = "master"
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"

# D3: the helper options, and what ``git credential fill`` is asked and answers.
CONFIG_OPTION = "-c"
HELPER_RESET = "credential.helper="
GITLAB_HELPER_PREFIX = "credential.https://gitlab.com.helper=!"
HELPER_OPTION_COUNT = 4
CREDENTIAL_REQUEST = "protocol=https\nhost=gitlab.com\n\n"
FIELD_SEPARATOR = "="
USER_FIELD = "username"
TOKEN_FIELD = "password"
GIT_USERNAME = "sff-forge-suite"
DECOY_VALUE = "decoy"
#: A helper configured before D3's options, as a config file's would be; their reset must keep git from asking it.
DECOY_HELPER = f"!f() {{ printf '{USER_FIELD}={DECOY_VALUE}\\n{TOKEN_FIELD}={DECOY_VALUE}\\n'; }}; f"

# D5, D8 "CI": the secret the CI step reads, and its refusal of an empty one.
SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret
UNAVAILABLE_TOKEN_MESSAGE = f"the secret {SECRET_NAME} is unavailable to this run"

GIT = "git"
GIT_EXIT_OK = 0
GIT_TIMEOUT_SECONDS = 60
#: Commits in the scratch checkouts: a runner has no global identity, and no signing key is asked for.
COMMIT_IDENTITY = (
    CONFIG_OPTION,
    "user.name=Forge GitLab Support Test",
    CONFIG_OPTION,
    "user.email=forge-gitlab-support-test@example.invalid",
    CONFIG_OPTION,
    "commit.gpgSign=false",
)

# D2, D4: the product GitLab wrapper, loaded by path for the prefix and the project test its guard reads.
PRODUCT_SCRIPTS = ROOT / "src" / "payload" / "scripts"
PRODUCT_WRAPPER_PATH = PRODUCT_SCRIPTS / "gitlab_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_gitlab_support_product_wrapper"
PRODUCT_SYMBOLS = ("EPHEMERAL_PROJECT_PREFIX", "_is_ephemeral_project")

# D4, D5: the test group, the ephemeral path's prefix, and GitLab's slug rule as the run's path meets it: lowercase
# letters, digits and single ``-``, a letter first and a hex digit last (docs.gitlab.com/user/reserved_names/).
TEST_GROUP = "bestehorn-sff-test"
EPHEMERAL_PREFIX = "sff-test-"
PROJECT_PATH_SEPARATOR = "/"
EPHEMERAL_PATH_FORM = re.compile(r"[a-z](?:-?[a-z0-9])*")
HEX_DIGITS = "0123456789abcdef"
RUN_ID_SAMPLES = 64

# The symbols each test needs of ``ephemeral.py`` (D1, D3, D4, D8, D10).
DISTRIBUTED_RUN_SYMBOLS = ("ForgeSuiteError", "ForgeSetupError", "GITLAB_FORGE_COMMAND", "refuse_distributed_run")
RUN_ID_SYMBOLS = ("new_run_id", "TEST_GROUP", "ephemeral_path", "ephemeral_full_path")
HELPER_SYMBOLS = ("ForgeSetupError", "CLONE_GIT_HELPER", "CLONE_GIT_TOKEN_FILE")
LOOKUP_SYMBOLS = ("ForgeSetupError", "TEST_CREDENTIAL_FILE", "find_test_credential")
CI_STEP_SYMBOLS = ("ForgeSetupError", "TEST_CREDENTIAL_FILE", "SECRET_NAME", "write_test_credential")


def _load_by_path(*, path: Path, name: str, description: str) -> ModuleType:
    """The file ``path``, loaded by path as the module ``name`` once per process and reused while ``sys.modules`` holds
    it; it is registered there before it runs, so its dataclasses resolve their module.

    Called from inside a test body, so a missing file fails that test with this assertion, never the collection.
    """
    loaded = sys.modules.get(name)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == path:
        return loaded
    assert path.is_file(), f"{description} {path.relative_to(ROOT).as_posix()} does not exist"
    spec = importlib.util.spec_from_file_location(name=name, location=path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _ephemeral() -> ModuleType:
    """``test/forge_gitlab/ephemeral.py``, the GitLab forge suite's support module, loaded by path
    (``_load_by_path``)."""
    return _load_by_path(
        path=EPHEMERAL_PATH, name=EPHEMERAL_MODULE, description="the GitLab forge suite's support module"
    )


def _require(*, module: ModuleType, names: Sequence[str]) -> None:
    """Fails the calling test on this assertion while ``module`` lacks one of ``names``."""
    missing = [name for name in names if not hasattr(module, name)]
    source = Path(str(module.__file__)).resolve().relative_to(ROOT).as_posix()
    assert not missing, f"{source} defines no {', '.join(missing)}"


def _product_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """``src/payload/scripts/gitlab_wrapper.py``, loaded by path as a fresh module, for the prefix and the project test
    its guard reads (D2, D4); its directory is first on ``sys.path``, so the wrapper's own bootstrap adds no entry, and
    the module is in ``sys.modules``, until the test ends."""
    assert PRODUCT_WRAPPER_PATH.is_file(), f"the product GitLab wrapper {PRODUCT_WRAPPER_PATH} does not exist"
    monkeypatch.syspath_prepend(path=str(PRODUCT_SCRIPTS))
    spec = importlib.util.spec_from_file_location(name=PRODUCT_WRAPPER_MODULE, location=PRODUCT_WRAPPER_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {PRODUCT_WRAPPER_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    monkeypatch.setitem(dic=sys.modules, name=PRODUCT_WRAPPER_MODULE, value=module)
    spec.loader.exec_module(module=module)
    return module


def _git(*, arguments: Sequence[str], cwd: Path, request: str = "") -> subprocess.CompletedProcess[str]:
    """Runs local git with ``request`` as its standard input; any exit but 0 fails the test with git's stderr."""
    result = subprocess.run(
        args=[GIT, *arguments],
        cwd=cwd,
        input=request,
        capture_output=True,
        text=True,
        encoding=TEXT_ENCODING,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == GIT_EXIT_OK, (
        f"`git {' '.join(arguments)}` exited {result.returncode}: {result.stderr.strip()}"
    )
    return result


def _init_checkout(*, path: Path) -> None:
    """A ``git init`` checkout at ``path`` with one empty commit, so a worktree can be added from it."""
    path.mkdir(parents=True)
    _git(arguments=["init", "--quiet"], cwd=path)
    _git(arguments=[*COMMIT_IDENTITY, "commit", "--allow-empty", "--quiet", "--message", "seed"], cwd=path)


def _new_token(*, label: str) -> str:
    """A token no other file of the test holds."""
    return f"{label}-{uuid.uuid4().hex}"


def _write_token(*, path: Path, token: str) -> Path:
    """``path`` holding ``token`` and a line end, its directories created; returns ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data=(token + LINE_END).encode(encoding=TEXT_ENCODING))
    return path


def _write_credential(*, directory: Path, name: str, token: str) -> Path:
    """``directory/credentials/<name>`` holding ``token`` and a line end; returns its path."""
    return _write_token(path=directory / CREDENTIALS_DIRECTORY / name, token=token)


def _answer_fields(*, text: str) -> Dict[str, str]:
    """The ``key=value`` lines of a ``git credential fill`` answer."""
    fields: Dict[str, str] = {}
    for line in text.splitlines():
        key, _, value = line.partition(FIELD_SEPARATOR)
        if key:
            fields[key] = value
    return fields


def _tree(*, root: Path) -> List[str]:
    """Every file and directory under ``root``, relative and in forward-slash form, sorted."""
    return sorted(path.relative_to(root).as_posix() for path in root.rglob(pattern="*"))


def _assert_found(*, found: object, expected: Path) -> None:
    assert isinstance(found, Path), f"find_test_credential returned {found!r}, not a Path"
    assert found.is_file(), f"find_test_credential returned {found}, which is not a file"
    assert found.samefile(other_path=expected), f"find_test_credential returned {found}, not {expected}"


def _names_one_of(*, message: str, paths: Sequence[Path]) -> bool:
    """Whether ``message`` holds one of ``paths`` (equivalent spellings of one file), native or forward-slash."""
    return any(form in message for path in paths for form in (str(path), path.as_posix()))


# ---------------------------------------------------------------------------------------------------------------------
# The distributed-run refusal (D1) and the run id (D4)
# ---------------------------------------------------------------------------------------------------------------------


def test_a_distributed_run_is_refused() -> None:
    """AC-1.1 (D1): a session fixture runs once per xdist worker, so ``refuse_distributed_run`` refuses any worker id
    but ``master`` with ``ForgeSetupError``, a ``ForgeSuiteError``, whose message names ``GITLAB_FORGE_COMMAND``, the
    GitLab forge suite's one-process command; ``master`` is let through."""
    forge = _ephemeral()
    _require(module=forge, names=DISTRIBUTED_RUN_SYMBOLS)
    assert forge.GITLAB_FORGE_COMMAND == GITLAB_FORGE_COMMAND, (
        f"GITLAB_FORGE_COMMAND is {forge.GITLAB_FORGE_COMMAND!r}, not D1's {GITLAB_FORGE_COMMAND!r}"
    )
    assert issubclass(forge.ForgeSetupError, forge.ForgeSuiteError), "ForgeSetupError is a ForgeSuiteError (D10)"

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.refuse_distributed_run(worker_id=DISTRIBUTED_WORKER_ID)

    message = str(refused.value)
    assert GITLAB_FORGE_COMMAND in message, f"the refusal does not name {GITLAB_FORGE_COMMAND}: {message}"
    assert forge.refuse_distributed_run(worker_id=CONTROLLER_WORKER_ID) is None


def test_a_run_id_names_an_ephemeral_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1.2 (D4): repeated ``new_run_id`` calls give pairwise distinct ids; ``ephemeral_path`` is the product GitLab
    wrapper's ``EPHEMERAL_PROJECT_PREFIX`` then the id, a path GitLab's slug rule admits, and ``ephemeral_full_path`` is
    ``bestehorn-sff-test/<that path>``, which the product's ``_is_ephemeral_project`` accepts, while it refuses the path
    alone (D2: a text without ``/`` is not one)."""
    forge = _ephemeral()
    _require(module=forge, names=RUN_ID_SYMBOLS)
    wrapper = _product_wrapper(monkeypatch=monkeypatch)
    _require(module=wrapper, names=PRODUCT_SYMBOLS)
    assert forge.TEST_GROUP == TEST_GROUP, f"TEST_GROUP is {forge.TEST_GROUP!r}, not {TEST_GROUP!r} (D5, DL-002)"
    assert wrapper.EPHEMERAL_PROJECT_PREFIX == EPHEMERAL_PREFIX, (
        f"the product's EPHEMERAL_PROJECT_PREFIX is {wrapper.EPHEMERAL_PROJECT_PREFIX!r} (D2)"
    )

    run_ids = [forge.new_run_id() for _ in range(RUN_ID_SAMPLES)]
    assert len(set(run_ids)) == len(run_ids), f"repeated calls gave an id twice: {sorted(run_ids)}"

    for run_id in run_ids:
        path = forge.ephemeral_path(run_id=run_id)
        assert path == EPHEMERAL_PREFIX + run_id, f"ephemeral_path gave {path!r} for {run_id!r}"
        assert EPHEMERAL_PATH_FORM.fullmatch(string=path) is not None and path[-1] in HEX_DIGITS, (
            f"the path {path!r} is not lowercase letters, digits and single '-', a letter first and a hex digit last"
        )
        full_path = forge.ephemeral_full_path(run_id=run_id)
        assert full_path == TEST_GROUP + PROJECT_PATH_SEPARATOR + path, (
            f"ephemeral_full_path gave {full_path!r} for {run_id!r}"
        )
        assert wrapper._is_ephemeral_project(project_id=full_path) is True, (
            f"the product's _is_ephemeral_project refuses {full_path!r}"
        )
        assert wrapper._is_ephemeral_project(project_id=path) is False, (
            f"the product's _is_ephemeral_project accepts the path {path!r} without its namespace"
        )


# ---------------------------------------------------------------------------------------------------------------------
# The credential helper (D3, D10), the test credential's lookup and the CI step's write (D8)
# ---------------------------------------------------------------------------------------------------------------------


def test_the_credential_helper_answers_git_with_the_clone_token(tmp_path: Path) -> None:
    """AC-6.3 (D3, D10): ``CLONE_GIT_HELPER(clone=...)`` gives exactly ``-c credential.helper=`` then ``-c
    credential.https://gitlab.com.helper=!...``, and no option holds the token; git, given a reset of its own, a decoy
    helper and then those options before ``credential fill``, answers ``protocol=https`` and ``host=gitlab.com`` with
    the username ``sff-forge-suite`` and the token of the clone's ``.git/sff-forge-token``, which is compared and never
    printed; a clone path holding ``'`` is refused with ``ForgeSetupError``."""
    forge = _ephemeral()
    _require(module=forge, names=HELPER_SYMBOLS)
    assert Path(forge.CLONE_GIT_TOKEN_FILE) == CLONE_GIT_TOKEN_FILE, (
        f"CLONE_GIT_TOKEN_FILE is {forge.CLONE_GIT_TOKEN_FILE!r}, not {CLONE_GIT_TOKEN_FILE.as_posix()} (D3)"
    )
    clone = tmp_path / "clone with space"
    token = _new_token(label="clone")
    _write_token(path=clone / CLONE_GIT_TOKEN_FILE, token=token)

    options = list(forge.CLONE_GIT_HELPER(clone=clone))
    assert not [option for option in options if token in str(option)], "a helper option holds the clone's token"
    assert len(options) == HELPER_OPTION_COUNT and options[:3] == [CONFIG_OPTION, HELPER_RESET, CONFIG_OPTION], (
        f"the options are not the helper reset then the gitlab.com helper: {options}"
    )
    assert str(options[3]).startswith(GITLAB_HELPER_PREFIX), (
        f"the second option is no gitlab.com shell helper: {options}"
    )

    answer = _git(
        arguments=[
            CONFIG_OPTION,
            HELPER_RESET,
            CONFIG_OPTION,
            f"credential.helper={DECOY_HELPER}",
            *options,
            "credential",
            "fill",
        ],
        cwd=tmp_path,
        request=CREDENTIAL_REQUEST,
    )
    fields = _answer_fields(text=answer.stdout)
    user = fields.get(USER_FIELD)
    assert user == GIT_USERNAME, f"git answered the user {user!r}, not {GIT_USERNAME!r}"
    # Compared into a bool first: pytest's introspection would print an answered password.
    answered_the_clone_token = fields.get(TOKEN_FIELD) == token
    assert answered_the_clone_token, "git did not answer the token of the clone's .git/sff-forge-token"

    quoted = tmp_path / "the clone's directory"
    _write_token(path=quoted / CLONE_GIT_TOKEN_FILE, token=_new_token(label="quoted"))
    with pytest.raises(expected_exception=forge.ForgeSetupError):
        forge.CLONE_GIT_HELPER(clone=quoted)


def test_the_test_credential_is_found_in_the_checkout_or_its_main_tree(tmp_path: Path) -> None:
    """AC-6.1 (D8): ``find_test_credential`` given this suite's ``TEST_CREDENTIAL_FILE``,
    ``credentials/gitlab-sff-testing-pat.txt``, finds the checkout's own file, else a linked worktree's main working
    tree's, and never the GitHub suite's file beside it; with neither GitLab file, the refusal names both paths and
    the setup note."""
    forge = _ephemeral()
    _require(module=forge, names=LOOKUP_SYMBOLS)
    assert Path(forge.TEST_CREDENTIAL_FILE) == TEST_CREDENTIAL_FILE, (
        f"TEST_CREDENTIAL_FILE is {forge.TEST_CREDENTIAL_FILE!r}, not {TEST_CREDENTIAL_FILE.as_posix()} (D8)"
    )
    credential_file = forge.TEST_CREDENTIAL_FILE
    main_tree = tmp_path / "main tree"
    _init_checkout(path=main_tree)
    _write_credential(directory=main_tree, name=GITHUB_TEST_CREDENTIAL_NAME, token=_new_token(label="github"))
    main_credential = _write_credential(directory=main_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="main"))
    _assert_found(
        found=forge.find_test_credential(checkout=main_tree, credential_file=credential_file), expected=main_credential
    )

    linked_tree = tmp_path / "linked tree"
    _git(arguments=["worktree", "add", "--detach", "--quiet", str(linked_tree)], cwd=main_tree)
    linked_credential = linked_tree / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    assert not linked_credential.exists(), f"the new worktree already holds {linked_credential}"
    _assert_found(
        found=forge.find_test_credential(checkout=linked_tree, credential_file=credential_file),
        expected=main_credential,
    )

    _write_credential(directory=linked_tree, name=TEST_CREDENTIAL_NAME, token=_new_token(label="linked"))
    _assert_found(
        found=forge.find_test_credential(checkout=linked_tree, credential_file=credential_file),
        expected=linked_credential,
    )

    common_dir = _git(arguments=["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=linked_tree)
    main_credential_by_git = Path(common_dir.stdout.strip()).parent / CREDENTIALS_DIRECTORY / TEST_CREDENTIAL_NAME
    linked_credential.unlink()
    main_credential.unlink()
    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.find_test_credential(checkout=linked_tree, credential_file=credential_file)
    message = str(refused.value)
    assert _names_one_of(message=message, paths=(linked_credential,)), (
        f"the refusal does not name {linked_credential}: {message}"
    )
    assert _names_one_of(message=message, paths=(main_credential, main_credential_by_git)), (
        f"the refusal does not name {main_credential}: {message}"
    )
    assert SETUP_NOTE in message, f"the refusal does not name {SETUP_NOTE}: {message}"


def test_a_missing_secret_fails_the_credential_step(tmp_path: Path) -> None:
    """AC-5.3 (D5, D8 "CI"): ``write_test_credential`` given this suite's ``credential_file`` and ``secret_name``
    refuses an empty token with "the secret SFF_GITLAB_TEST_TOKEN is unavailable to this run" and writes nothing; a
    token is written followed by a line end as the checkout's ``credentials/gitlab-sff-testing-pat.txt``, and no other
    file is touched."""
    forge = _ephemeral()
    _require(module=forge, names=CI_STEP_SYMBOLS)
    assert forge.SECRET_NAME == SECRET_NAME, f"SECRET_NAME is {forge.SECRET_NAME!r}, not {SECRET_NAME!r} (D8)"
    assert Path(forge.TEST_CREDENTIAL_FILE) == TEST_CREDENTIAL_FILE, (
        f"TEST_CREDENTIAL_FILE is {forge.TEST_CREDENTIAL_FILE!r}, not {TEST_CREDENTIAL_FILE.as_posix()} (D8)"
    )
    checkout = tmp_path / "checkout"
    (checkout / CREDENTIALS_DIRECTORY).mkdir(parents=True)
    before = _tree(root=checkout)

    with pytest.raises(expected_exception=forge.ForgeSetupError) as refused:
        forge.write_test_credential(
            token="", checkout=checkout, credential_file=forge.TEST_CREDENTIAL_FILE, secret_name=forge.SECRET_NAME
        )
    assert UNAVAILABLE_TOKEN_MESSAGE in str(refused.value), f"the refusal says: {refused.value}"
    assert _tree(root=checkout) == before, "the refused write left a file in the checkout"

    token = _new_token(label="ci")
    forge.write_test_credential(
        token=token, checkout=checkout, credential_file=forge.TEST_CREDENTIAL_FILE, secret_name=forge.SECRET_NAME
    )
    written = checkout / TEST_CREDENTIAL_FILE
    assert _tree(root=checkout) == sorted([*before, written.relative_to(checkout).as_posix()]), (
        "the write touched another file than the test credential file"
    )
    # Compared into a bool first, so that no assertion prints the file's bytes.
    holds_the_token = written.read_bytes() in (
        (token + LINE_END).encode(encoding=TEXT_ENCODING),
        (token + WINDOWS_LINE_END).encode(encoding=TEXT_ENCODING),
    )
    assert holds_the_token, "the test credential file does not hold the token followed by a line end"
