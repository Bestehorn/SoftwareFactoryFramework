"""G: the GitLab forge suite's separation and its CI wiring, read from the repository (issue #11, design.md D1, D5).

The GitLab forge suite (``test/forge_gitlab/``) talks to gitlab.com and runs in its own CI job, ``forge-gitlab``,
beside ``verify`` and ``forge``; these tests run in the default collection with no network and no test credential
(UB-1). They load L, ``test/test_forge_suite_layout.py``, by path from inside each test body (``_layout``), registered
in ``sys.modules`` under its own key before it runs, as #10's S ``_load_by_path`` does, and never at import, so this
file collects whatever L holds. They apply L's workflow reader (``read_workflow``, ``job_named``, ``steps_of``,
``needs_of``, ``run_of``, ``run_commands``, ``scalars_of``, ``condition_of``) to the ``forge-gitlab`` and ``report``
jobs of ``.github/workflows/ci.yml`` (AC-5.1, AC-5.2, AC-5.4, AC-6.3), and L's ``collect_only`` to
``test/forge_gitlab`` under the default configuration, which no fixture runs under, so no token or network is needed
(AC-7.1).

Run: ``python scripts/run_tests.py test/test_forge_gitlab_layout.py``.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "test" / "test_forge_suite_layout.py"
#: The fixed ``sys.modules`` key of L's by-path load; its dataclasses resolve their module through it.
LAYOUT_MODULE = "forge_suite_layout"
LAYOUT_DESCRIPTION = "the forge suite's layout test"

GITLAB_FORGE_SUITE = "test/forge_gitlab"
JOB_FORGE_GITLAB = "forge-gitlab"
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"
GITLAB_CREDENTIAL_COMMAND = "python test/forge_gitlab/write_credential.py"
GITLAB_SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret
# Both expression spellings of the secret: the property (`secrets.NAME`) and the index (`secrets['NAME']`).
GITLAB_SECRET_REFERENCE = re.compile(
    r"\bsecrets\s*(?:\.\s*" + GITLAB_SECRET_NAME + r"\b|\[\s*['\"]" + GITLAB_SECRET_NAME + r"['\"]\s*\])"
)
GITLAB_SECRET_EXPRESSION = re.compile(r"^\$\{\{\s*secrets\." + GITLAB_SECRET_NAME + r"\s*\}\}$")
# The GitLab forge job's id or its suite's directory, as a word of its own (`forge-gitlab`, `test/forge_gitlab`).
GITLAB_FORGE_MENTION = re.compile(r"(?<![\w-])forge[-_]gitlab(?![\w-])")

GITLAB_FORGE_RESULT = r"\"?\$\{\{\s*needs\.forge-gitlab\.result\s*\}\}\"?"
SUCCESS = r"\"?success\"?"
FAILING_STATUS = r"status=[1-9][0-9]*"
# `if [ "<result>" != "success" ]; then status=N; fi`, or `[ "<result>" = "success" ] || status=N`.
GITLAB_FORGE_GUARDS = (
    re.compile(
        r"^if\s+\[\[?\s*"
        + GITLAB_FORGE_RESULT
        + r"\s*!=\s*"
        + SUCCESS
        + r"\s*\]\]?\s*;\s*then\s+"
        + FAILING_STATUS
        + r"\s*;\s*fi$"
    ),
    re.compile(
        r"^\[\[?\s*" + GITLAB_FORGE_RESULT + r"\s*==?\s*" + SUCCESS + r"\s*\]\]?\s*\|\|\s*" + FAILING_STATUS + r"$"
    ),
)


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


def _layout() -> ModuleType:
    """L, ``test/test_forge_suite_layout.py``, the forge suite's layout test, loaded by path (``_load_by_path``)."""
    return _load_by_path(path=LAYOUT_PATH, name=LAYOUT_MODULE, description=LAYOUT_DESCRIPTION)


def assert_fails_unless_gitlab_forge_succeeded(*, script: str, layout: ModuleType) -> None:
    """``script`` sets a failing status unless the GitLab forge job succeeded, keeps it, and exits with it."""
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    guards = [index for index, line in enumerate(lines) if any(guard.match(line) for guard in GITLAB_FORGE_GUARDS)]
    assert guards, (
        f"no line of the verdict sets a failing status unless the `{JOB_FORGE_GITLAB}` job's result is success:\n"
        f"{script}"
    )
    overwrites = [line for line in lines[guards[-1] + 1 :] if layout.STATUS_ASSIGNMENT.match(line)]
    assert not overwrites, (
        f"the verdict overwrites the `{JOB_FORGE_GITLAB}` job's failing status afterwards: {overwrites}"
    )
    assert layout.STATUS_EXIT.match(lines[-1]), f'the verdict ends with `{lines[-1]}`, not with `exit "$status"`'


def test_the_gitlab_forge_job_runs_beside_verify() -> None:
    layout = _layout()
    workflow = layout.read_workflow()
    triggers = workflow.get(layout.KEY_ON)
    assert triggers == layout.EXPECTED_TRIGGERS, (
        f"`{layout.KEY_ON}:` is {triggers}, expected exactly {layout.EXPECTED_TRIGGERS}"
    )
    for name in (layout.JOB_VERIFY, layout.JOB_FORGE):
        job = layout.job_named(workflow=workflow, name=name)
        naming = [text for text in layout.scalars_of(node=job) if GITLAB_FORGE_MENTION.search(text)]
        assert not naming, f"the job `{name}` names `{JOB_FORGE_GITLAB}` or `{GITLAB_FORGE_SUITE}`: {naming}"
    gitlab = layout.job_named(workflow=workflow, name=JOB_FORGE_GITLAB)
    assert layout.KEY_NEEDS not in gitlab, (
        f"the job `{JOB_FORGE_GITLAB}` has `{layout.KEY_NEEDS}: {gitlab.get(layout.KEY_NEEDS)}`; it runs beside"
    )
    assert layout.KEY_CONTINUE_ON_ERROR not in gitlab, (
        f"the job `{JOB_FORGE_GITLAB}` has `{layout.KEY_CONTINUE_ON_ERROR}: "
        f"{gitlab.get(layout.KEY_CONTINUE_ON_ERROR)}`; it hides a failure"
    )
    steps = layout.steps_of(job=gitlab, name=JOB_FORGE_GITLAB)
    muted = [step for step in steps if layout.KEY_CONTINUE_ON_ERROR in step]
    assert not muted, (
        f"steps of `{JOB_FORGE_GITLAB}` have `{layout.KEY_CONTINUE_ON_ERROR}:`, so their failure passes the job: "
        f"{muted}"
    )
    last = steps[-1]
    assert layout.run_of(step=last) == GITLAB_FORGE_COMMAND, (
        f"the last step of `{JOB_FORGE_GITLAB}` is {last}, not `run: {GITLAB_FORGE_COMMAND}`"
    )


def test_the_gitlab_secret_reaches_one_step() -> None:
    layout = _layout()
    references = GITLAB_SECRET_REFERENCE.findall(layout.WORKFLOW.read_text(encoding=layout.SOURCE_ENCODING))
    assert len(references) == 1, (
        f"{layout.WORKFLOW_NAME} references the secret {GITLAB_SECRET_NAME} {len(references)} times, not once"
    )
    gitlab = layout.job_named(workflow=layout.read_workflow(), name=JOB_FORGE_GITLAB)
    steps = layout.steps_of(job=gitlab, name=JOB_FORGE_GITLAB)
    credential_steps = [step for step in steps if layout.run_of(step=step) == GITLAB_CREDENTIAL_COMMAND]
    assert len(credential_steps) == 1, (
        f"{len(credential_steps)} steps of `{JOB_FORGE_GITLAB}` run `{GITLAB_CREDENTIAL_COMMAND}`"
    )
    environment = credential_steps[0].get(layout.KEY_ENV)
    assert isinstance(environment, dict), (
        f"the credential step has no `{layout.KEY_ENV}:` mapping: {credential_steps[0]}"
    )
    secret = environment.get(GITLAB_SECRET_NAME)
    assert isinstance(secret, str) and GITLAB_SECRET_EXPRESSION.match(secret), (
        f"the credential step's `{layout.KEY_ENV}:` does not hand {GITLAB_SECRET_NAME} the secret: {environment}"
    )
    checkouts = [step for step in steps if str(step.get(layout.KEY_USES, "")).startswith(layout.CHECKOUT_ACTION)]
    assert checkouts, f"the job `{JOB_FORGE_GITLAB}` has no `{layout.CHECKOUT_ACTION}` step"
    for checkout in checkouts:
        inputs = checkout.get(layout.KEY_WITH)
        persisted = str(inputs.get(layout.KEY_PERSIST_CREDENTIALS, "")) if isinstance(inputs, dict) else ""
        assert persisted.lower() == layout.YAML_FALSE, (
            f"the checkout of `{JOB_FORGE_GITLAB}` keeps the token: {checkout}"
        )
    checks = [
        command
        for command in layout.run_commands(steps=steps)
        if command != GITLAB_CREDENTIAL_COMMAND and not layout.INSTALL_COMMAND.match(command)
    ]
    assert checks == [GITLAB_FORGE_COMMAND], (
        f"the check commands of `{JOB_FORGE_GITLAB}` are {checks}, expected [{GITLAB_FORGE_COMMAND}]"
    )


def test_the_report_judges_the_gitlab_forge_job() -> None:
    layout = _layout()
    report = layout.job_named(workflow=layout.read_workflow(), name=layout.JOB_REPORT)
    needs = layout.needs_of(job=report)
    expected = [layout.JOB_VERIFY, layout.JOB_FORGE, JOB_FORGE_GITLAB]
    missing = [job for job in expected if job not in needs]
    assert not missing, f"`{layout.JOB_REPORT}` needs {needs}, missing {missing}; it must run after {expected}"
    assert layout.condition_of(job=report) == layout.ALWAYS, (
        f"`{layout.JOB_REPORT}` runs `{layout.KEY_IF}: {report.get(layout.KEY_IF)}`, not {layout.ALWAYS}"
    )
    verdicts = [
        command
        for command in layout.run_commands(steps=layout.steps_of(job=report, name=layout.JOB_REPORT))
        if layout.SUMMARY_COMMAND in command
    ]
    assert len(verdicts) == 1, f"{len(verdicts)} steps of `{layout.JOB_REPORT}` run `{layout.SUMMARY_COMMAND}`"
    assert_fails_unless_gitlab_forge_succeeded(script=verdicts[0], layout=layout)


def test_the_default_configuration_collects_no_gitlab_forge_test() -> None:
    layout = _layout()
    completed = layout.collect_only(arguments=["-c", layout.DEFAULT_CONFIGURATION, GITLAB_FORGE_SUITE])
    output = completed.stdout + completed.stderr
    expected = int(pytest.ExitCode.NO_TESTS_COLLECTED)
    assert completed.returncode == expected, f"the collection exited {completed.returncode}, not {expected}:\n{output}"
    assert layout.NO_TESTS_COLLECTED in output, f"the collection does not say `{layout.NO_TESTS_COLLECTED}`:\n{output}"
    errors = [marker for marker in layout.COLLECTION_ERROR_MARKERS if marker in output]
    assert not errors, f"the collection reports {errors}:\n{output}"
