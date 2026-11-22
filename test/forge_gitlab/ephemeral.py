"""The GitLab forge suite's support module: what ``test/forge_gitlab/`` runs beside pytest against the test group (D10).

The GitLab forge suite (``test/forge_gitlab/``, run by ``python scripts/run_tests.py --workers 1 test/forge_gitlab``)
drives the product GitLab wrapper against an ephemeral ``sff-test-*`` project of the test group. This module holds the
logic that decides without the forge, so the default collection proves it (``test/test_forge_gitlab_support.py``): the
refusal of a distributed run, naming this suite's command (D1); the per-command git credential helper for gitlab.com,
``CLONE_GIT_HELPER`` (D3); the project path a run id gives (D4); where the GitLab test credential file is found and how
the CI step writes it (D8).

What issue #10 settled is reused, not copied (design.md Overview): ``test/forge/ephemeral.py`` is loaded by path under
its own ``sys.modules`` key ``forge_ephemeral``, with the reuse rule of ``test/forge/conftest.py`` ``_load_ephemeral``,
and its symbols are bound here under their own names. Its keyword-only parameters are given this suite's constants:
here by ``refuse_distributed_run``, ``CLONE_GIT_HELPER`` and ``product_wrapper``, and by the callers of
``find_test_credential`` (``credential_file=TEST_CREDENTIAL_FILE``), ``write_test_credential``
(``credential_file=TEST_CREDENTIAL_FILE, secret_name=SECRET_NAME``) and ``SubprocessGitRunner``
(``helper=CLONE_GIT_HELPER``), whose defaults stay the GitHub suite's.

Loaded by path, never imported by name and never collected: its name matches neither the default ``python_files`` nor
the suite's ``forge_*.py``, and under ``--import-mode=importlib`` a test directory's utility module is not importable.
At module level it imports only the standard library and loads ``test/forge/ephemeral.py``, which runs only its own
standard-library imports and constants, so no ``sys.path`` changes; the product GitLab wrapper, whose constants it
reads, is loaded by path on first use (``product_wrapper``). No function logs or prints a token.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

# Overview: #10's support module, in the sibling directory ``test/forge/``, and the fixed ``sys.modules`` key of its
# by-path load, the key ``test/forge/conftest.py`` and ``test/test_forge_support.py`` load it under too, so one process
# holds one copy of it and one family of its exception classes.
REUSED_PATH = Path(__file__).resolve().parents[1] / "forge" / "ephemeral.py"
REUSED_MODULE = "forge_ephemeral"


def _load_reused() -> ModuleType:
    """``test/forge/ephemeral.py``, loaded by path once per process and reused while ``sys.modules`` holds an entry
    whose ``__file__`` resolves to it (the rule of ``test/forge/conftest.py`` ``_load_ephemeral``); it is registered
    there before it runs, so its dataclasses resolve their module, and taken off again when it raises. A file that
    cannot be loaded raises ``ImportError``."""
    loaded = sys.modules.get(REUSED_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == REUSED_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=REUSED_MODULE, location=REUSED_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"The forge suite's support module {REUSED_PATH} cannot be loaded",
            name=REUSED_MODULE,
            path=str(REUSED_PATH),
        )
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[REUSED_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(REUSED_MODULE, None)
        raise
    return module


_REUSED = _load_reused()

# Overview: the symbols reused as settled, bound under their names. ``ForgeSetupError`` and its siblings are
# ``ForgeSuiteError``s; ``find_test_credential`` and ``write_test_credential`` keep their keyword-only parameters.
ForgeSuiteError = _REUSED.ForgeSuiteError
ForgeSetupError = _REUSED.ForgeSetupError
ForgeCommandError = _REUSED.ForgeCommandError
ForgeTeardownRefusedError = _REUSED.ForgeTeardownRefusedError
ForgeSweepRefusedError = _REUSED.ForgeSweepRefusedError
Invocation = _REUSED.Invocation
WrapperRunner = _REUSED.WrapperRunner
GitRunner = _REUSED.GitRunner
SubprocessGitRunner = _REUSED.SubprocessGitRunner
new_run_id = _REUSED.new_run_id
main_working_tree = _REUSED.main_working_tree
remove_tree = _REUSED.remove_tree
find_test_credential = _REUSED.find_test_credential
write_test_credential = _REUSED.write_test_credential
COMMIT_IDENTITY = _REUSED.COMMIT_IDENTITY
CONTROLLER_WORKER_ID = _REUSED.CONTROLLER_WORKER_ID
LEFTOVER_AGE = _REUSED.LEFTOVER_AGE
SUBPROCESS_TIMEOUT_SECONDS = _REUSED.SUBPROCESS_TIMEOUT_SECONDS

# D1: the GitLab forge suite's one-process command, which the refusal of a distributed run names.
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"

# D3: #10's helper, set under the gitlab.com key. GitLab does not validate the username of a personal access token over
# HTTPS (docs.gitlab.com/user/profile/personal_access_tokens/); the token is read from a file inside the clone's
# ``.git/``, since the clone's ``config/gitlab.json`` is JSON, which the helper's shell built-ins do not parse.
GITLAB_HELPER_KEY = "credential.https://gitlab.com.helper"
GIT_USERNAME = "sff-forge-suite"
GIT_METADATA_DIRECTORY = ".git"
#: The clone's git token file, relative to the clone: the token and a line end.
CLONE_GIT_TOKEN_FILE = Path(GIT_METADATA_DIRECTORY) / "sff-forge-token"

# D4, D5: the test group, the one place the suite names it, and the separator of a project's full path.
TEST_GROUP = "bestehorn-sff-test"
PROJECT_PATH_SEPARATOR = "/"

# D8: the credential file, relative to a working tree, and the secret the CI step writes it from.
CREDENTIALS_DIRECTORY = Path("credentials")
#: The operator's test token for the test group, git-ignored like every file of ``credentials/``.
TEST_CREDENTIAL_FILE = CREDENTIALS_DIRECTORY / "gitlab-sff-testing-pat.txt"
SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret

#: D8: the working tree holding the suite, the repository root above ``test/forge_gitlab/``: the ``checkout`` whose test
#: credential file a run reads.
CHECKOUT = Path(__file__).resolve().parents[2]
# D10: the product entry script the suite starts, an absolute resolved path as #10's ``product_wrapper`` compares it,
# and the fixed ``sys.modules`` key of its by-path load, whose constants this module reads rather than redefines.
PRODUCT_WRAPPER = CHECKOUT / "src" / "payload" / "scripts" / "gitlab_wrapper.py"
PRODUCT_WRAPPER_MODULE = "forge_gitlab_product_wrapper"

#: D3, D10: the global git options that make one git command authenticate to gitlab.com as ``GIT_USERNAME`` with the
#: token of the clone's ``CLONE_GIT_TOKEN_FILE``, called as ``CLONE_GIT_HELPER(clone=<clone>)``: #10's
#: ``credential_helper_arguments`` with its other three keywords bound. A clone path holding ``'`` raises
#: ``ForgeSetupError``. ``SubprocessGitRunner`` is given it as ``helper``.
CLONE_GIT_HELPER = functools.partial(
    _REUSED.credential_helper_arguments,
    helper_key=GITLAB_HELPER_KEY,
    username=GIT_USERNAME,
    credential_file=CLONE_GIT_TOKEN_FILE,
)


def refuse_distributed_run(*, worker_id: str) -> None:
    """D1: raises ``ForgeSetupError`` unless ``worker_id`` (xdist's fixture) is ``master``, since a session fixture
    runs once per xdist worker and each would create its own project: #10's refusal, its message naming
    ``GITLAB_FORGE_COMMAND``."""
    _REUSED.refuse_distributed_run(worker_id=worker_id, command=GITLAB_FORGE_COMMAND)


def product_wrapper() -> ModuleType:
    """D10: the product GitLab wrapper ``PRODUCT_WRAPPER``, loaded by #10's ``product_wrapper`` under the
    ``sys.modules`` key ``PRODUCT_WRAPPER_MODULE`` on first use and reused while ``sys.modules`` holds it there.

    Never loaded at import, so loading this module changes no ``sys.path``; the directory the wrapper puts on
    ``sys.path`` for its package is taken off again once it is loaded. A missing script raises ``ForgeSetupError``.
    """
    module: ModuleType = _REUSED.product_wrapper(path=PRODUCT_WRAPPER, module_name=PRODUCT_WRAPPER_MODULE)
    return module


def ephemeral_path(*, run_id: str) -> str:
    """D4: the path of the run's project, the product wrapper's ``EPHEMERAL_PROJECT_PREFIX`` then ``run_id``."""
    return str(product_wrapper().EPHEMERAL_PROJECT_PREFIX) + run_id


def ephemeral_full_path(*, run_id: str) -> str:
    """D4: the full path of the run's project, ``TEST_GROUP``, ``/``, then ``ephemeral_path(run_id=run_id)``: the
    ``<namespace>/sff-test-*`` path the product wrapper's guard serves while the test marker is set (D2)."""
    return TEST_GROUP + PROJECT_PATH_SEPARATOR + ephemeral_path(run_id=run_id)
