"""Tests for this repository's project gate `toolchain-paths` (.claude/hooks/gate_toolchain_paths.py).

The gate refuses a Write/Edit of an installed toolchain file (config/toolchain.json) outside a
`framework-update-*` branch and names the product file instead. Each case builds a scratch project with its own
manifest and git HEAD, so the decision never depends on this checkout's branch.

Run: ``python scripts/run_tests.py test/test_gate_toolchain_paths.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

import gate_toolchain_paths as gate  # noqa: E402

import hooklib as lib  # noqa: E402

INSTALLED = "scripts/run_tests.py"
SOURCE = "src/payload/scripts/run_tests.py"


def scratch_project(tmp_path: Path, branch: str, worktree: bool = False) -> Path:
    project = tmp_path / "project"
    (project / "config").mkdir(parents=True)
    (project / "config" / "toolchain.json").write_text(json.dumps({"files": {INSTALLED: SOURCE}}), encoding="utf-8")
    if worktree:
        gitdir = tmp_path / "common" / "worktrees" / "wt"
        gitdir.mkdir(parents=True)
        (gitdir / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
        (project / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    else:
        (project / ".git").mkdir()
        (project / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
    return project


def decide(project: Path, tool: str, file_path: str) -> lib.Decision:
    payload = lib.Payload.parse(
        json.dumps({"tool_name": tool, "tool_input": {"file_path": file_path}, "cwd": str(project)})
    )
    return gate.run(lib.Context(payload, environ={}, cwd=project))


@pytest.mark.parametrize("tool", ["Write", "Edit"])
def test_a_hand_edit_of_a_toolchain_file_is_refused_and_names_the_source(tmp_path: Path, tool: str) -> None:
    project = scratch_project(tmp_path, "main")
    decision = decide(project, tool, str(project / INSTALLED))
    assert decision.exit_code == 2
    assert SOURCE in decision.stderr and "toolchain" in decision.stderr


def test_a_relative_path_is_judged_from_the_project_root(tmp_path: Path) -> None:
    project = scratch_project(tmp_path, "issue-12-fix")
    assert decide(project, "Edit", INSTALLED).exit_code == 2


@pytest.mark.parametrize("worktree", [False, True])
def test_a_framework_update_branch_may_write_the_toolchain(tmp_path: Path, worktree: bool) -> None:
    project = scratch_project(tmp_path, "framework-update-20261109", worktree=worktree)
    assert decide(project, "Write", str(project / INSTALLED)).exit_code == 0


def test_a_product_file_is_not_this_gates_business(tmp_path: Path) -> None:
    project = scratch_project(tmp_path, "main")
    assert decide(project, "Edit", str(project / SOURCE)).exit_code == 0


def test_the_gate_fails_open_without_a_manifest(tmp_path: Path) -> None:
    project = scratch_project(tmp_path, "main")
    (project / "config" / "toolchain.json").unlink()
    assert decide(project, "Edit", str(project / INSTALLED)).exit_code == 0


def test_the_gate_fails_open_on_a_payload_without_a_path(tmp_path: Path) -> None:
    project = scratch_project(tmp_path, "main")
    payload = lib.Payload.parse(json.dumps({"tool_name": "Write", "tool_input": {}, "cwd": str(project)}))
    assert gate.run(lib.Context(payload, environ={}, cwd=project)).exit_code == 0
