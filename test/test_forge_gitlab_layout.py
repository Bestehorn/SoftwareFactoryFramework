"""G: the GitLab forge suite's separation and its CI wiring, read from the repository (issue #11, design.md D1, D5).

The GitLab forge suite (``test/forge_gitlab/``) talks to gitlab.com and runs in its own CI job, ``forge-gitlab``,
beside ``verify`` and ``forge``; these tests run in the default collection with no network and no test credential
(UB-1). They load L, ``test/test_forge_suite_layout.py``, by path from inside each test body (``_layout``), registered
in ``sys.modules`` under its own key before it runs, as #10's S ``_load_by_path`` does, and never at import, so this
file collects whatever L holds. They apply L's workflow reader (``read_workflow``, ``job_named``, ``steps_of``,
``needs_of``, ``run_of``, ``run_commands``, ``scalars_of``, ``condition_of``) to the ``forge-gitlab`` and ``report``
jobs of ``.github/workflows/ci.yml`` (AC-5.1, AC-5.2, AC-5.4, AC-6.3), and L's ``collect_only`` to
``test/forge_gitlab`` under the default configuration, which no fixture runs under, so no token or network is needed
(AC-7.1). They parse the ``.py`` files of ``test/forge_gitlab/`` with ``ast`` into L's ``ForgeModule`` and apply L's
``ast`` helpers to bound what the suite reaches: ``product_wrapper_problems`` to ``ephemeral.py``, so
``PRODUCT_WRAPPER`` is named in ``SubprocessWrapperRunner`` and ``product_wrapper`` and nowhere else but its
definition (D10), and to every module the checks of L's ``module_problems`` with this suite's fake host, project
argument and project records, so only ``ephemeral.py`` starts the product wrapper or names, creates or deletes a
project (AC-4.3, AC-8.1, AC-8.7).

Run: ``python scripts/run_tests.py test/test_forge_gitlab_layout.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

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

# The GitLab forge suite's modules, read with L's `ast` helpers (D10; AC-8.7): every `.py` file under
# test/forge_gitlab/, whichever wave adds it.
GITLAB_FORGE_DIRECTORY = ROOT / GITLAB_FORGE_SUITE
# The GitLab fake host, which no module of the suite may load (AC-8.7).
GITLAB_FIXTURES_MODULE = "gitlab_wrapper_fixtures"
# A `--path id=`, which names a project other than the configured one: its value an argv entry of its own (`id=...`)
# or after `--path` in one string; `--path merge_request_iid=` and `--path issue_iid=` name no project.
GITLAB_TARGETING_ARGUMENT = re.compile(r"(?:^|--path[ =])id=")
GITLAB_TARGETING_DESCRIPTION = "a string starting `id=` or holding `--path id=`"
# The records that create and delete a project (D9); `create-a-project-for-a-user` and the `-topic` records are others.
PROJECT_CREATION = "tenant-scale#create-a-project"
PROJECT_DELETION = "tenant-scale#delete-a-project"
GITLAB_PROJECT_LIFECYCLE = re.compile(
    r"(?<![\w#/-])(?:" + re.escape(PROJECT_CREATION) + r"|" + re.escape(PROJECT_DELETION) + r")(?![\w-])"
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


def read_gitlab_forge_modules(*, layout: ModuleType) -> list[Any]:
    """Every ``.py`` file under ``test/forge_gitlab/``, parsed into L's ``ForgeModule``, its ``name`` its path from the
    repository root; ``ephemeral.py`` at the top of the suite is its support module."""
    support = GITLAB_FORGE_DIRECTORY / layout.SUPPORT_MODULE
    return [
        layout.ForgeModule(
            name=path.relative_to(ROOT).as_posix(),
            tree=ast.parse(source=path.read_text(encoding=layout.SOURCE_ENCODING), filename=str(path)),
            is_support=path == support,
        )
        for path in sorted(GITLAB_FORGE_DIRECTORY.rglob(layout.PYTHON_FILES))
    ]


def gitlab_fixture_loads(*, tree: ast.Module, layout: ModuleType) -> list[int]:
    """L's ``fixture_loads`` for the GitLab fake host: an import of ``gitlab_wrapper_fixtures`` (as any dotted part), or
    a string naming it, as a load by path would."""
    imports = [
        layout.line_of(node=node)
        for node in ast.walk(tree)
        if any(
            GITLAB_FIXTURES_MODULE in module.split(layout.MODULE_SEPARATOR)
            for module in layout.imported_modules(node=node)
        )
    ]
    paths = [line for line, text in layout.string_constants(tree=tree) if GITLAB_FIXTURES_MODULE in text]
    return sorted(imports + paths)


def gitlab_module_problems(*, module: Any, layout: ModuleType) -> list[str]:
    """What ``module`` may not do (L's ``module_problems`` with this suite's fake host, project argument and project
    records): read an attribute ``main``, load ``gitlab_wrapper_fixtures`` or patch ``urllib``; and, unless it is
    ``ephemeral.py``, import ``subprocess``, name ``product_wrapper`` or ``PRODUCT_WRAPPER``, give a string starting
    ``id=`` or holding ``--path id=``, or name ``tenant-scale#create-a-project`` or
    ``tenant-scale#delete-a-project``."""
    tree = module.tree
    checks = [
        (layout.entry_point_reads(tree=tree), f"reads the attribute `{layout.ENTRY_POINT}`"),
        (gitlab_fixture_loads(tree=tree, layout=layout), f"loads `{GITLAB_FIXTURES_MODULE}`"),
        (layout.urllib_patches(tree=tree), f"patches `{layout.URLLIB_PACKAGE}`"),
    ]
    if not module.is_support:
        only_support = f"which only {layout.SUPPORT_MODULE} may"
        checks += [
            (layout.subprocess_imports(tree=tree), f"imports `{layout.SUBPROCESS_MODULE}`, {only_support}"),
            (
                layout.lines_naming(root=tree, identifier=layout.PRODUCT_WRAPPER_LOADER),
                f"names `{layout.PRODUCT_WRAPPER_LOADER}`, {only_support}",
            ),
            (
                layout.lines_naming(root=tree, identifier=layout.PRODUCT_WRAPPER_PATH),
                f"names `{layout.PRODUCT_WRAPPER_PATH}`, {only_support}",
            ),
            (
                layout.constants_matching(tree=tree, pattern=GITLAB_TARGETING_ARGUMENT),
                f"gives {GITLAB_TARGETING_DESCRIPTION}, {only_support}",
            ),
            (
                layout.constants_matching(tree=tree, pattern=GITLAB_PROJECT_LIFECYCLE),
                f"names `{PROJECT_CREATION}` or `{PROJECT_DELETION}`, {only_support}",
            ),
        ]
    return [problem for lines, text in checks for problem in layout.located(module=module, lines=lines, problem=text)]


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


def test_the_gitlab_forge_tests_reach_only_the_ephemeral_project() -> None:
    layout = _layout()
    modules = read_gitlab_forge_modules(layout=layout)
    supports = [module for module in modules if module.is_support]
    assert len(supports) == 1, (
        f"{GITLAB_FORGE_SUITE} holds no {layout.SUPPORT_MODULE}; its files are {[module.name for module in modules]}"
    )
    # D10: one module-level definition of PRODUCT_WRAPPER, named outside it in SubprocessWrapperRunner and
    # product_wrapper only, and in each of them.
    problems = list(layout.product_wrapper_problems(module=supports[0]))
    problems += [problem for module in modules for problem in gitlab_module_problems(module=module, layout=layout)]
    assert not problems, "the GitLab forge suite reaches past its ephemeral project:\n" + "\n".join(problems)
