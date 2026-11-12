"""The forge CI job's credential step: ``python test/forge/write_credential.py`` (D5, D8 "CI"; AC-5.3).

The step's ``env:`` block hands it the repository Actions secret ``SFF_TEST_TOKEN``, and ``main`` reads it — the one
environment read of the change (AC-6.3) — and writes it as the checkout's test credential file through
``write_test_credential`` of the forge suite's support module. An unset or empty secret, as a fork's or Dependabot's
pull request receives, is logged as a refusal and exits 1, which fails the job before the suite runs.

``test/forge/ephemeral.py`` is loaded by path, as ``test/forge/conftest.py`` loads it (D10), under the ``sys.modules``
key ``forge_ephemeral``, and an entry already there for the same file is reused (DL-005). Nothing logs or prints the
token.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)

#: The forge suite's support module beside this file, and the fixed ``sys.modules`` key of its by-path load (DL-005).
EPHEMERAL_PATH = Path(__file__).resolve().parent / "ephemeral.py"
EPHEMERAL_MODULE = "forge_ephemeral"
#: ``main``'s exit codes: the test credential file was written, or the secret was refused.
EXIT_WROTE = 0
EXIT_REFUSED = 1
LOG_FORMAT = "%(levelname)s: %(message)s"


def load_ephemeral() -> ModuleType:
    """``test/forge/ephemeral.py``, loaded by path as ``forge_ephemeral`` and reused while ``sys.modules`` holds it for
    the same file; it is registered there before it runs, so its dataclasses resolve their module."""
    loaded = sys.modules.get(EPHEMERAL_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == EPHEMERAL_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=EPHEMERAL_MODULE, location=EPHEMERAL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"The forge suite's support module {EPHEMERAL_PATH} cannot be loaded")
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
    """Writes the secret ``SFF_TEST_TOKEN`` as ``checkout``'s test credential file and returns 0; an unset or empty
    secret is refused by ``write_test_credential``, the refusal logged, nothing written, and 1 returned."""
    token = os.getenv(key=ephemeral.SECRET_NAME, default="")
    try:
        ephemeral.write_test_credential(token=token, checkout=checkout)
    except ephemeral.ForgeSetupError as refused:
        logger.error("%s", refused)
        return EXIT_REFUSED
    return EXIT_WROTE


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    sys.exit(main())
