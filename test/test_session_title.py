"""The session-title contract of the issue-work entry points (Claude desktop app).

The orchestrator keeps its session's title equal to the issues it is working on (the agent definition's
"Session title" section): ``Issue 77``, ``Issues 77, 80``, ``Auto-Work 12, 15, 19``. The rename is a tool of the
desktop app, and a command that tells the session to call such a tool must pre-approve it in ``allowed-tools``:
otherwise every rename in a session outside bypass mode stops on a permission prompt, which in an unattended
``/auto-work`` run nobody answers. The agent definition's ``tools`` line is an allowlist, so the tool must be
named there as well, or a session running the agent cannot rename itself at all.

Run: ``python scripts/run_tests.py test/test_session_title.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "clients" / "claude" / "commands"
AGENT = ROOT / "clients" / "claude" / "agents" / "issue-work-orchestrator.md"

TITLE_TOOL = "mcp__ccd_session_mgmt__set_session_title"
ARCHIVE_TOOL = "mcp__ccd_session_mgmt__archive_session"
TITLE_SECTION_HEADING = "# Session title (Claude desktop app)"
TITLE_STATE_FIELD = "SESSION_ISSUES:"
WORK_ENTRY_POINTS = ("work-issue.md", "auto-work.md", "issues-work.md")
# One title per mode, as the section's table spells them; the formats are the operator's ask.
TITLE_FORMS = ("`Issue 77`", "`Issues 77, 80`", "`Issue 77 — done`", "`Auto-Work 12, 15, 19`", "`Issues-Work 12, 15`")

DESKTOP_TOOL_RE = re.compile(r"\bmcp__ccd_[a-z_]*?__[a-z_]+\b")
# The short names the prose also uses for a desktop-app tool, mapped to the name an allowlist must carry.
SHORT_NAMES = {"archive_session": ARCHIVE_TOOL, "set_session_title": TITLE_TOOL}
SHORT_NAME_RE = re.compile(r"(?<![\w])(" + "|".join(SHORT_NAMES) + r")\b")
TOOL_TOKEN_RE = re.compile(r"[A-Za-z_]\w*(?:\([^)]*\))?")


def _split_front_matter(path: Path) -> tuple[str, str]:
    """The YAML front matter and the body of a client asset; an asset without front matter is a test failure."""
    head = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("---", 2)
    assert len(head) == 3 and head[0] == "", f"{path.name}: no YAML front matter"
    return head[1], head[2]


def _tool_list(front_matter: str, key: str) -> set[str]:
    """The tool names of one front-matter key (``tools`` or ``allowed-tools``); ``Agent(a, b)`` is one entry."""
    match = re.search(rf"^{re.escape(key)}:\s*(.*)$", front_matter, re.MULTILINE)
    assert match is not None, f"no `{key}:` line in the front matter"
    return {token.split("(", 1)[0] for token in TOOL_TOKEN_RE.findall(match.group(1))}


def _desktop_tools_named(body: str) -> set[str]:
    full = set(DESKTOP_TOOL_RE.findall(body))
    short = {SHORT_NAMES[name] for name in SHORT_NAME_RE.findall(body)}
    return full | short


def _title_section(body: str) -> str:
    start = body.find(TITLE_SECTION_HEADING)
    assert start != -1, f"the agent definition has no `{TITLE_SECTION_HEADING}` section"
    end = body.find("\n# ", start + len(TITLE_SECTION_HEADING))
    return body[start:] if end == -1 else body[start:end]


@pytest.mark.parametrize("path", sorted(COMMANDS_DIR.glob("*.md")), ids=lambda p: p.stem)
def test_every_desktop_tool_a_command_calls_is_allowlisted(path: Path) -> None:
    front_matter, body = _split_front_matter(path=path)
    named = _desktop_tools_named(body=body)
    if not named:
        return
    missing = named - _tool_list(front_matter=front_matter, key="allowed-tools")
    assert not missing, f"{path.name} tells the session to call {sorted(missing)} but does not allowlist it"


@pytest.mark.parametrize("name", WORK_ENTRY_POINTS)
def test_every_work_entry_point_keeps_the_session_title(name: str) -> None:
    front_matter, body = _split_front_matter(path=COMMANDS_DIR / name)
    assert TITLE_TOOL in _tool_list(front_matter=front_matter, key="allowed-tools"), f"{name}: tool not allowlisted"
    assert TITLE_TOOL in body, f"{name} does not tell the session to rename itself"
    assert '"Session title"' in body, f"{name} does not point at the agent definition's rule"


def test_the_orchestrator_may_rename_its_own_session() -> None:
    front_matter, body = _split_front_matter(path=AGENT)
    assert TITLE_TOOL in _tool_list(front_matter=front_matter, key="tools")
    assert _desktop_tools_named(body=body) <= _tool_list(front_matter=front_matter, key="tools")


def test_the_title_rule_names_every_mode_and_survives_compaction() -> None:
    _, body = _split_front_matter(path=AGENT)
    section = _title_section(body=body)
    missing = [form for form in TITLE_FORMS if form not in section]
    assert not missing, f"the Session title section lacks the title forms {missing}"
    assert TITLE_STATE_FIELD in section, "the set must be recorded in resume_state.md so a compaction keeps it"
    assert '"self"' in section, "the rename targets this session"
