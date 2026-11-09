"""toolchain-paths — PreToolUse (Write/Edit). A PROJECT gate of the framework's own repository.

This repository develops the framework AND runs on an installed copy of it (docs/reports/
self-hosting-proposal-2026-11-07.md). The installed copy — every file listed in config/toolchain.json — is the
toolchain sessions run on; it changes only when a release is promoted with prompts/update.txt. A hand edit of
an installed file would make development run on code no release contains, and the next promotion would
silently overwrite it. So a Write or Edit of a listed path is refused, and the refusal names the product file
to change instead. The promotion itself runs on a `framework-update-*` branch, which this gate lets through.

Fails OPEN when the manifest is missing or unreadable, or the target path cannot be read from the payload: a
gate that cannot see the toolchain must not refuse work it cannot judge. Reads no run state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import hooklib as lib

HOOK = "toolchain-paths"
EVENT = "pre-tool-use"  # the dispatcher runs this gate on this event
ORDER = 110  # a project gate: after every framework gate (10..90)
TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}  # PreToolUse only: the tool names this gate judges

MANIFEST = Path("config") / "toolchain.json"
UPDATE_BRANCH_PREFIX = "framework-update-"


def _manifest(project: Path) -> Optional[Dict[str, str]]:
    try:
        data = json.loads((project / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else None


def _branch(project: Path) -> str:
    """The checked-out branch, read from HEAD without spawning git (a worktree's `.git` is a `gitdir:` file)."""
    dot = project / ".git"
    try:
        if dot.is_file():
            line = dot.read_text(encoding="utf-8").strip()
            gitdir = Path(line.split(":", 1)[1].strip()) if line.startswith("gitdir:") else dot
            if not gitdir.is_absolute():
                gitdir = (project / gitdir).resolve()
        else:
            gitdir = dot
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
    except (OSError, IndexError):
        return ""
    return head[len("ref: refs/heads/") :] if head.startswith("ref: refs/heads/") else ""


def _target(ctx: lib.Context) -> Optional[str]:
    tool_input = ctx.payload.data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    value = tool_input.get("file_path") or tool_input.get("notebook_path")
    return value if isinstance(value, str) and value else None


def run(ctx: lib.Context) -> lib.Decision:
    target = _target(ctx)
    if target is None:
        return lib.allow()
    project = ctx.project_dir
    files = _manifest(project)
    if not files:
        return lib.allow()
    path = Path(target)
    if not path.is_absolute():
        path = project / path
    try:
        relative = path.resolve().relative_to(project.resolve()).as_posix()
    except (OSError, ValueError):
        return lib.allow()  # outside this project: not this gate's question
    source = files.get(relative)
    if source is None:
        return lib.allow()
    if _branch(project).startswith(UPDATE_BRANCH_PREFIX):
        return lib.allow()
    return lib.block(
        f"{HOOK}: `{relative}` is part of this repository's TOOLCHAIN (config/toolchain.json): the installed copy of "
        f"the framework release named in .claude/FRAMEWORK_COMMIT, which sessions here run on.\n"
        f"Change the product file instead: `{source}`. The change reaches the toolchain when a release is promoted "
        f"(tag a release, then run prompts/update.txt against this repository on a `framework-update-*` branch).\n"
        f"Why: a hand edit would make development run on code no release contains, and the next promotion would "
        f"overwrite it."
    )
