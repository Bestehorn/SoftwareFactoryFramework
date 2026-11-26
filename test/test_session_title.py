"""The session-title contract of the main-session agents and commands (Claude desktop app).

Every main session keeps its title as ``<subject> · <activity>`` (``Issue 77 · CI``, ``Spec deploy-guard · spec
review``), renamed when either changes, by the ONE rule text ``clients/claude/docs/session-title.md`` (installed at
``.claude/docs/session-title.md``) that the agents and commands point to. The orchestrator's "Session title" section
spells the issue-work subject: ``Issue 77``, ``Issues 77, 80``, ``Auto-Work 12, 15, 19``. The rename is a tool of the
desktop app, and a command that tells the session to call such a tool must pre-approve it in ``allowed-tools``:
otherwise every rename in a session outside bypass mode stops on a permission prompt, which in an unattended
``/auto-work`` run nobody answers. An agent definition's ``tools`` line is an allowlist, so the tool must be named
there as well, or a session running the agent cannot rename itself at all.

Run: ``python scripts/run_tests.py test/test_session_title.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "clients" / "claude" / "commands"
AGENTS_DIR = ROOT / "clients" / "claude" / "agents"
AGENT = AGENTS_DIR / "issue-work-orchestrator.md"
DOC_SOURCE = "clients/claude/docs/session-title.md"
DOC = ROOT / DOC_SOURCE
SETUP_CLAUDE = ROOT / "prompts" / "setup-claude.txt"

TITLE_TOOL = "mcp__ccd_session_mgmt__set_session_title"
ARCHIVE_TOOL = "mcp__ccd_session_mgmt__archive_session"
TITLE_SECTION_HEADING = "# Session title (Claude desktop app)"
TITLE_STATE_FIELD = "SESSION_ISSUES:"
DOC_POINTER = ".claude/docs/session-title.md"
WORK_ENTRY_POINTS = ("work-issue.md", "auto-work.md", "issues-work.md")
# Every main-session entry point that runs in the desktop app (issue #73's coverage list).
MAIN_SESSION_AGENTS = ("issue-work-orchestrator.md", "spec-conductor.md")
MAIN_SESSION_COMMANDS = WORK_ENTRY_POINTS + (
    "spec-new.md",
    "spec-review.md",
    "spec-tasks.md",
    "spec-implement.md",
    "close-session.md",
    "continue-work.md",
    "supervise.md",
    "compile-memory.md",
)
# One title per mode, as the section's table spells them; the formats are the operator's ask.
TITLE_FORMS = ("`Issue 77`", "`Issues 77, 80`", "`Issue 77 — done`", "`Auto-Work 12, 15, 19`", "`Issues-Work 12, 15`")
ACTIVITY_FORMS = ("`Issue 77 · CI`", "`Auto-Work 12, 15 · 15 implementing`")
# The issue-work activities, which the doc lists and the orchestrator maps its phases to.
ISSUE_WORK_ACTIVITIES = (
    "`selecting`",
    "`spec`",
    "`spec review`",
    "`implementing`",
    "`verifying`",
    "`CI`",
    "`queued`",
    "`merging`",
    "`needs you`",
)
ISSUE_WORK_BULLET = "- **Issue work**"
# The orchestrator's phase-to-activity mapping, one pair per phase that has an activity of its own (AC-5).
PHASE_MAPPING_PHRASES = (
    "SELECT `selecting`",
    "FIX's waves `implementing`",
    "PROOF_GATE `verifying`",
    "PR until its CI is green, `CI`",
    "QUEUE `queued`",
    "MERGE_CLEANUP `merging`",
)
ORCHESTRATOR_TRIGGER = "each time the set or the activity below changes"
# The trigger each work command states (AC-3), and the set-only trigger it had before issue #73.
COMMAND_TRIGGER = "each time the set or the activity changes"
SET_ONLY_IN_ORCHESTRATOR = ("each time the set below changes, and at no other time", "only when the set next changes")
SET_ONLY_IN_COMMANDS = ("only when the set changes", "each time that set changes")
# The doc's statement of the form, of when and how to rename (AC-1), and its four kept properties (AC-2).
DOC_FORM_PHRASES = (
    "`<subject> · <activity>`",
    "`<subject> — done`",
    '"self"',
    "ToolSearch",
    TITLE_TOOL,
    "Rename each time the subject or the activity changes",
    "never within a phase",
)
DOC_PROPERTY_PHRASES = (
    "never delegate",
    "A subagent ignores this rule",
    "comes before the close-out",
    "no rename follows the SESSION verdict",
    "not a blocker",
    "never ask about the title",
    "Kiro",
    "the session skips this rule",
)
# Each form bullet names its activities: a list in backticks, or the resumed run's (AC-1).
ACTIVITIES_RE = re.compile(r"\b[Aa]ctivit(?:y|ies): (?:`[^`]+`|the resumed run's)")
# The kinds of session "The forms" gives a bullet for, each by a name its bullet carries.
DOC_KINDS = (
    "/work-issue",
    "spec-conductor",
    "/close-session",
    "/continue-work",
    "/supervise",
    "/compile-memory",
    "interactive session",
)
DOC_FORMS_HEADING = "## The forms"
DOT_EXAMPLE_RE = re.compile(r"`[^`]+ · [^`]+`")
PART_8_1_HEADING = "### Part 8.1"
FLEET_HEADING = "## Fleet conventions (all agents and the main session)"
THIS_PROJECT_HEADING = "## This project"
# The setup prompt's copy list pads its columns, so the match tolerates any run of spaces.
DOC_COPY_RE = re.compile(r"^cp +" + re.escape(DOC_SOURCE) + r" +\.claude/docs/", re.MULTILINE)
WHITESPACE_RE = re.compile(r"\s+")

DESKTOP_TOOL_RE = re.compile(r"\bmcp__ccd_[a-z_]*?__[a-z_]+\b")
# The short names the prose also uses for a desktop-app tool, mapped to the name an allowlist must carry.
SHORT_NAMES = {"archive_session": ARCHIVE_TOOL, "set_session_title": TITLE_TOOL}
SHORT_NAME_RE = re.compile(r"(?<![\w])(" + "|".join(SHORT_NAMES) + r")\b")
TOOL_TOKEN_RE = re.compile(r"[A-Za-z_]\w*(?:\([^)]*\))?")


def _read(path: Path) -> str:
    assert path.is_file(), f"{path.relative_to(ROOT)} does not exist"
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _collapsed(text: str) -> str:
    """The text with each whitespace run, line breaks included, collapsed to one space."""
    return WHITESPACE_RE.sub(" ", text)


def _rename_governed_by(text: str, trigger: str) -> bool:
    """Whether a mention of the rename tool is followed, within its clause, by ``trigger``.

    The clause ends at the first ``.``, ``,`` or ``;``, so a trigger stated for something else in the same sentence
    (``Rename … each time the set changes, APPEND … each time the set or the activity changes``) does not count.
    """
    return re.search(re.escape(TITLE_TOOL) + r"`?[^.,;]*?" + re.escape(trigger), text) is not None


def _split_front_matter(path: Path) -> tuple[str, str]:
    """The YAML front matter and the body of a client asset; an asset without front matter is a test failure."""
    head = _read(path=path).split("---", 2)
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


def _form_bullets(doc: str) -> list[str]:
    """The bullets under the doc's "The forms" heading, each with its wrapped lines joined."""
    start = doc.find(DOC_FORMS_HEADING)
    assert start != -1, f"the session-title doc has no `{DOC_FORMS_HEADING}` section"
    end = doc.find("\n## ", start + len(DOC_FORMS_HEADING))
    section = doc[start:] if end == -1 else doc[start:end]
    bullets: list[str] = []
    for line in section.splitlines():
        if line.startswith("- "):
            bullets.append(line)
        elif line.startswith("  ") and bullets:
            bullets[-1] += " " + line.strip()
    return bullets


@pytest.mark.parametrize("path", sorted(COMMANDS_DIR.glob("*.md")), ids=lambda p: p.stem)
def test_every_desktop_tool_a_command_calls_is_allowlisted(path: Path) -> None:
    front_matter, body = _split_front_matter(path=path)
    named = _desktop_tools_named(body=body)
    if not named:
        return
    missing = named - _tool_list(front_matter=front_matter, key="allowed-tools")
    assert not missing, f"{path.name} tells the session to call {sorted(missing)} but does not allowlist it"


@pytest.mark.parametrize("path", sorted(AGENTS_DIR.glob("*.md")), ids=lambda p: p.stem)
def test_every_desktop_tool_an_agent_calls_is_in_its_tools(path: Path) -> None:
    front_matter, body = _split_front_matter(path=path)
    missing = _desktop_tools_named(body=body) - _tool_list(front_matter=front_matter, key="tools")
    assert not missing, f"{path.name} tells the session to call {sorted(missing)} but its `tools` line lacks it"


@pytest.mark.parametrize("name", WORK_ENTRY_POINTS)
def test_every_work_entry_point_keeps_the_session_title(name: str) -> None:
    front_matter, body = _split_front_matter(path=COMMANDS_DIR / name)
    assert TITLE_TOOL in _tool_list(front_matter=front_matter, key="allowed-tools"), f"{name}: tool not allowlisted"
    assert TITLE_TOOL in body, f"{name} does not tell the session to rename itself"
    assert '"Session title"' in body, f"{name} does not point at the agent definition's rule"


@pytest.mark.parametrize("name", MAIN_SESSION_COMMANDS)
def test_every_main_session_command_renames_by_the_shared_rule(name: str) -> None:
    front_matter, body = _split_front_matter(path=COMMANDS_DIR / name)
    assert TITLE_TOOL in body, f"{name} does not tell the session to rename itself"
    assert DOC_POINTER in body, f"{name} does not point at {DOC_POINTER}"
    assert TITLE_TOOL in _tool_list(front_matter=front_matter, key="allowed-tools"), f"{name}: tool not allowlisted"


@pytest.mark.parametrize("name", WORK_ENTRY_POINTS)
def test_no_work_entry_point_limits_the_rename_to_the_set(name: str) -> None:
    _, body = _split_front_matter(path=COMMANDS_DIR / name)
    text = _collapsed(text=body)
    assert _rename_governed_by(text=text, trigger=COMMAND_TRIGGER), f"{name} does not rename {COMMAND_TRIGGER!r}"
    kept = [phrase for phrase in SET_ONLY_IN_COMMANDS if phrase in text]
    assert not kept, f"{name} still renames only when the issue set changes: {kept}"


@pytest.mark.parametrize("name", MAIN_SESSION_AGENTS)
def test_every_main_session_agent_renames_by_the_shared_rule(name: str) -> None:
    front_matter, body = _split_front_matter(path=AGENTS_DIR / name)
    assert TITLE_TOOL in body, f"{name} does not tell the session to rename itself"
    assert DOC_POINTER in body, f"{name} does not point at {DOC_POINTER}"
    assert TITLE_TOOL in _tool_list(front_matter=front_matter, key="tools"), f"{name}: tool not in `tools`"


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


def test_the_orchestrator_renames_when_the_activity_changes() -> None:
    _, body = _split_front_matter(path=AGENT)
    section = _collapsed(text=_title_section(body=body))
    missing = [form for form in ACTIVITY_FORMS if form not in section]
    assert not missing, f"the Session title section lacks the activity forms {missing}"
    assert DOC_POINTER in section, f"the Session title section does not point at {DOC_POINTER}"
    unmapped = [activity for activity in ISSUE_WORK_ACTIVITIES if activity not in section]
    assert not unmapped, f"the Session title section maps no phase to the activities {unmapped}"
    missing_pairs = [pair for pair in PHASE_MAPPING_PHRASES if pair not in section]
    assert not missing_pairs, f"the Session title section lacks the phase-to-activity pairs {missing_pairs}"
    assert _rename_governed_by(text=section, trigger=ORCHESTRATOR_TRIGGER), (
        f"the Session title section does not rename {ORCHESTRATOR_TRIGGER!r}"
    )
    kept = [phrase for phrase in SET_ONLY_IN_ORCHESTRATOR if phrase in section]
    assert not kept, f"the Session title section still renames only when the set changes: {kept}"


def test_the_doc_lists_the_issue_work_activities() -> None:
    bullets = [bullet for bullet in _form_bullets(doc=_read(path=DOC)) if bullet.startswith(ISSUE_WORK_BULLET)]
    assert len(bullets) == 1, f"`{DOC_FORMS_HEADING}` has no single `{ISSUE_WORK_BULLET}` bullet"
    missing = [activity for activity in ISSUE_WORK_ACTIVITIES if activity not in bullets[0]]
    assert not missing, f"the doc's issue-work bullet lacks the activities {missing}"


def test_the_doc_states_the_form_and_how_to_rename() -> None:
    doc = _collapsed(text=_read(path=DOC))
    missing = [phrase for phrase in DOC_FORM_PHRASES if phrase not in doc]
    assert not missing, f"the session-title doc lacks {missing}"


@pytest.mark.parametrize("kind", DOC_KINDS)
def test_the_doc_gives_every_kind_of_session_a_form(kind: str) -> None:
    bullets = _form_bullets(doc=_read(path=DOC))
    assert any(
        kind in bullet and DOT_EXAMPLE_RE.search(bullet) and ACTIVITIES_RE.search(bullet) for bullet in bullets
    ), f"no bullet of `{DOC_FORMS_HEADING}` names {kind} with its activities and a `<subject> · <activity>` example"


def test_the_doc_keeps_the_four_properties() -> None:
    doc = _collapsed(text=_read(path=DOC))
    missing = [phrase for phrase in DOC_PROPERTY_PHRASES if phrase not in doc]
    assert not missing, f"the session-title doc lacks the properties {missing}"


def test_the_claude_md_template_names_the_rule() -> None:
    text = _read(path=SETUP_CLAUDE)
    part = text.find(PART_8_1_HEADING)
    assert part != -1, f"no `{PART_8_1_HEADING}` in the setup prompt"
    start = text.find(FLEET_HEADING, part)
    end = text.find(THIS_PROJECT_HEADING, start)
    assert start != -1 and end != -1, "Part 8.1's template has no Fleet conventions section"
    fleet = _collapsed(text=text[start:end])
    assert DOC_POINTER in fleet, f"the CLAUDE.md template's Fleet conventions do not name {DOC_POINTER}"


def test_the_setup_prompt_installs_the_doc() -> None:
    assert DOC_COPY_RE.search(_read(path=SETUP_CLAUDE)), "the setup prompt does not copy the doc into .claude/docs/"
