"""The GitLab forge CI job's credential step: ``python test/forge_gitlab/write_credential.py`` (D5, D8 "CI"; AC-5.3).

The step's ``env:`` block hands it the repository Actions secret ``SFF_GITLAB_TEST_TOKEN``, and ``main`` reads it — the
one environment read of the change (AC-6.3) — and writes it as the checkout's GitLab test credential file through the
reused ``write_test_credential`` of the GitLab forge suite's support module, given this suite's ``credential_file`` and
``secret_name`` (the function's defaults are the GitHub suite's). An unset or empty secret, as a fork's or Dependabot's
pull request receives, is logged as a refusal and exits 1, which fails the job before the suite runs.

``test/forge_gitlab/ephemeral.py`` is loaded by path, as ``test/forge_gitlab/conftest.py`` loads it (D1), under the
``sys.modules`` key ``forge_gitlab_ephemeral``, and an entry already there for the same file is reused. Nothing logs or
prints the token.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)

#: The GitLab forge suite's support module beside this file, and the fixed ``sys.modules`` key of its by-path load (D1).
EPHEMERAL_PATH = Path(__file__).resolve().parent / "ephemeral.py"
EPHEMERAL_MODULE = "forge_gitlab_ephemeral"
#: ``main``'s exit codes: the test credential file was written, or the secret was refused.
EXIT_WROTE = 0
EXIT_REFUSED = 1
LOG_FORMAT = "%(levelname)s: %(message)s"


def load_ephemeral() -> ModuleType:
    """``test/forge_gitlab/ephemeral.py``, loaded by path as ``forge_gitlab_ephemeral`` and reused while
    ``sys.modules`` holds it for the same file; it is registered there before it runs, so its dataclasses resolve their
    module, and taken off again when it raises."""
    loaded = sys.modules.get(EPHEMERAL_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == EPHEMERAL_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=EPHEMERAL_MODULE, location=EPHEMERAL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"The GitLab forge suite's support module {EPHEMERAL_PATH} cannot be loaded")
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[EPHEMERAL_MODULE] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(EPHEMERAL_MODULE, None)
        raise
    return module


ephemeral = load_ephemeral()
#: The working tree holding the suite, whose test credential file the step writes (``ephemeral.CHECKOUT``).
CHECKOUT: Path = ephemeral.CHECKOUT


def main(*, checkout: Path = CHECKOUT) -> int:
    """Writes the secret ``SFF_GITLAB_TEST_TOKEN`` as ``checkout``'s test credential file
    ``credentials/gitlab-sff-testing-pat.txt`` and returns 0; an unset or empty secret is refused by
    ``write_test_credential``, the refusal logged, nothing written, and 1 returned."""
    token = os.getenv(key=ephemeral.SECRET_NAME, default="")
    try:
        ephemeral.write_test_credential(
            token=token,
            checkout=checkout,
            credential_file=ephemeral.TEST_CREDENTIAL_FILE,
            secret_name=ephemeral.SECRET_NAME,
        )
    except ephemeral.ForgeSetupError as refused:
        logger.error("%s", refused)
        return EXIT_REFUSED
    return EXIT_WROTE


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    sys.exit(main())
