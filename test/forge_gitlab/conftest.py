"""The GitLab forge suite's session fixture: one ephemeral project for the whole run (issue #11, design.md D1, D9, D10).

``ephemeral_project`` (session scope) first refuses a run that xdist distributes, since each worker would create its
own project (D1 "One project per run"), then holds ``provision`` of ``test/forge_gitlab/ephemeral.py`` open around the
session: the test token and the clone, the leftover sweep, the private project ``bestehorn-sff-test/sff-test-<run id>``
with its seed, under a ``tempfile.mkdtemp`` workspace (not pytest's ``tmp_path_factory``, whose directories outlive the
session), with the wrapper and git runners bound to ``<workspace>/clone`` and the git runner given the gitlab.com
credential helper ``CLONE_GIT_HELPER`` (D10), since the reused runner's default helper is the github.com one. After
the session it deletes the project and removes the workspace; a failure of either ends the session in an error (D9).

``ephemeral.py`` is loaded by path once per process and registered as ``sys.modules["forge_gitlab_ephemeral"]`` before
it runs, so its dataclasses resolve their module, and a GitLab forge module reads the support symbols there inside its
test bodies: under ``--import-mode=importlib`` a test directory's utility module is not importable by name. The default
collection imports this file too, and collects no GitLab forge test: this file imports only the standard library and
pytest at module level, defines this one fixture and no hook, and loading ``ephemeral.py`` runs only its
standard-library imports and constants and its by-path load of ``test/forge/ephemeral.py``, which runs only its own, so
no ``sys.path`` changes and nothing is sent.

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab`` (with the GitLab test credential file,
``docs/forge-suite.md``).
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator

import pytest

#: The GitLab forge suite's support module, beside this file, and the fixed ``sys.modules`` key of its by-path load, the
#: key ``test/test_forge_gitlab_support.py`` and ``write_credential.py`` load it under too (D1).
EPHEMERAL_PATH = Path(__file__).resolve().parent / "ephemeral.py"
EPHEMERAL_MODULE = "forge_gitlab_ephemeral"
#: The prefix of the run's workspace directory, created under the temporary directory.
WORKSPACE_PREFIX = "sff-forge-gitlab-suite-"


def _load_ephemeral() -> ModuleType:
    """``ephemeral.py``, loaded by path once per process and reused while ``sys.modules`` holds an entry whose
    ``__file__`` resolves to it; it is registered there before it runs, so its dataclasses resolve their module, and
    taken off again when it raises. A file that cannot be loaded raises ``ImportError``."""
    loaded = sys.modules.get(EPHEMERAL_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == EPHEMERAL_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=EPHEMERAL_MODULE, location=EPHEMERAL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"The GitLab forge suite's support module {EPHEMERAL_PATH} cannot be loaded",
            name=EPHEMERAL_MODULE,
            path=str(EPHEMERAL_PATH),
        )
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[EPHEMERAL_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(EPHEMERAL_MODULE, None)
        raise
    return module


EPHEMERAL = _load_ephemeral()


@pytest.fixture(scope="session")
def ephemeral_project(worker_id: str) -> Iterator[Any]:
    """The run's ``EphemeralProject`` (D9), provisioned once for the session and torn down after it.

    ``worker_id`` is xdist's fixture: any value but ``master`` raises ``ForgeSetupError`` before anything is created
    (D1). The workspace is a fresh ``tempfile.mkdtemp`` directory; ``provision`` creates ``<workspace>/clone``, to which
    both runners are bound, the git runner with ``CLONE_GIT_HELPER`` (D10), and removes the workspace in its
    ``finally``.
    """
    EPHEMERAL.refuse_distributed_run(worker_id=worker_id)
    workspace = Path(tempfile.mkdtemp(prefix=WORKSPACE_PREFIX))
    clone = workspace / EPHEMERAL.CLONE_DIRECTORY
    with EPHEMERAL.provision(
        checkout=EPHEMERAL.CHECKOUT,
        workspace=workspace,
        wrapper=EPHEMERAL.SubprocessWrapperRunner(directory=clone),
        git=EPHEMERAL.SubprocessGitRunner(clone=clone, helper=EPHEMERAL.CLONE_GIT_HELPER),
    ) as project:
        yield project
