"""The GitHub deploy template deploys only the trunk's tip, and a re-run of one of its jobs cannot skip that check.

`templates/ci/github-deploy.yml.template` holds the production role, so WHICH commit it deploys is a security
property, and no local run can exercise a workflow. These tests pin its structure instead:

- the trunk-tip check (`merge_steward.py deploy-guard`) is a STEP of the deploy job, run from a checkout of the
  default branch, before the job checks out the commit to deploy. A check in its own job would be skipped by a
  re-run of only the deploy job, which reuses the other jobs' results (GitHub Docs, "Re-running workflows and
  jobs");
- the verdict runs only for a commit the guard admitted: it reads the deploy job's `admitted` output, which the
  runner evaluates when the job completes, whatever its result (actions/runner, `JobExtension.FinalizeJob`), so a
  failed deploy still gets its red verdict and a refused one gets none;
- the template has no `env:` map (its header rule: the dispatch input never reaches a shell).

Run: ``python scripts/run_tests.py test/test_deploy_template.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "ci" / "github-deploy.yml.template"
JOB_RE = re.compile(r"^  ([A-Za-z][\w-]*):\s*$")
GUARD_COMMAND = "python scripts/merge_steward.py deploy-guard"
DEFAULT_BRANCH_REF = "ref: ${{ github.event.repository.default_branch }}"
DEPLOYED_REF = "ref: ${{ inputs.sha || github.sha }}"


def jobs() -> Dict[str, List[str]]:
    """The lines of every job under `jobs:`, keyed by job id, in file order."""
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    start = lines.index("jobs:") + 1
    found: Dict[str, List[str]] = {}
    current = ""
    for line in lines[start:]:
        match = JOB_RE.match(line)
        if match:
            current = match.group(1)
            found[current] = []
        elif current:
            found[current].append(line)
    return found


def first_index(lines: List[str], needle: str) -> int:
    for index, line in enumerate(lines):
        if needle in line:
            return index
    raise AssertionError(f"{needle!r} not found in the job")


def step_at(lines: List[str], index: int) -> str:
    """The whole step (from its `- ` line to the next step's) that contains line `index` of a job."""
    start = max(i for i in range(index + 1) if lines[i].lstrip().startswith("- "))
    ends = [i for i in range(index + 1, len(lines)) if lines[i].lstrip().startswith(("- ", "# {{"))]
    return "\n".join(lines[start : ends[0] if ends else len(lines)])


def test_the_trunk_tip_check_is_the_deploy_jobs_first_step() -> None:
    found = jobs()
    assert list(found) == ["deploy", "e2e", "verdict"], "no separate guard job: a single-job re-run would skip it"
    deploy = found["deploy"]
    guard = first_index(lines=deploy, needle=GUARD_COMMAND)
    assert first_index(lines=deploy, needle="uses: actions/checkout") < guard
    assert first_index(lines=deploy, needle=DEFAULT_BRANCH_REF) < guard, "the guard runs the default branch's copy"
    assert guard < first_index(lines=deploy, needle=DEPLOYED_REF), "checked before the deployed commit is checked out"
    assert guard < first_index(lines=deploy, needle="{{DEPLOY_STEPS}}"), "checked before any deploy step"
    step = step_at(lines=deploy, index=guard)
    assert "id: guard" in step and '--github-output "$GITHUB_OUTPUT"' in step, step
    assert "continue-on-error" not in "\n".join(deploy), "a refused guard must stop the job"
    assert any("admitted: ${{ steps.guard.outputs.admitted }}" in line for line in deploy), "the job's output"


def test_the_verdict_runs_only_for_an_admitted_commit() -> None:
    verdict = jobs()["verdict"]
    condition = next(line for line in verdict if line.strip().startswith("if:"))
    assert "!cancelled()" in condition, "a cancelled (superseded) deploy renders no verdict"
    assert "needs.deploy.outputs.admitted" in condition, "a refused deploy renders no verdict"
    assert "needs.guard" not in "\n".join(verdict)


def test_the_template_has_no_env_map() -> None:
    assert not [line for line in TEMPLATE.read_text(encoding="utf-8").splitlines() if line.strip() == "env:"]
