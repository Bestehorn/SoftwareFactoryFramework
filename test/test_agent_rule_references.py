"""Agents name the three conditionally installed rules only with the marker ``(where installed)``.

``aws-config.md`` is installed only in an AWS project, ``cdk-deployment-only.md`` only where the project has a
``cdk/`` directory, and ``use-doc-mcp-servers.md`` only where documentation MCP servers are configured, yet every
agent is installed in every project. An agent body that tells the agent to apply one of the three unconditionally
sends it after a file a project without AWS, CDK or documentation MCP servers does not have (issue #8). So every
backticked occurrence of the three names in a Claude or Kiro agent body is followed by ``(where installed)``, no
other rule name carries the marker, each body still names each rule under the heading it names it in, and both
setup prompts state each rule's install condition and the agents that name it.

Run: ``python scripts/run_tests.py test/test_agent_rule_references.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = "claude"
KIRO = "kiro"
CLIENTS = (CLAUDE, KIRO)
SETUP_CLAUDE = ROOT / "prompts" / "setup-claude.txt"
SETUP_KIRO = ROOT / "prompts" / "setup-kiro.txt"

AWS_CONFIG = "aws-config.md"
CDK_DEPLOYMENT_ONLY = "cdk-deployment-only.md"
USE_DOC_MCP_SERVERS = "use-doc-mcp-servers.md"
CONDITIONAL_RULES = (AWS_CONFIG, CDK_DEPLOYMENT_ONLY, USE_DOC_MCP_SERVERS)
# Whitespace, a line break included, then the marker: a marker wrapped onto the next line still counts.
MARKER_PATTERN = r"\s+\(where installed\)"
MARKED_RULE_RE = re.compile(pattern=r"`([\w.-]+\.md)`" + MARKER_PATTERN)

# The heading each body names each rule under; the Claude and Kiro bodies are identical in this.
BINDING_RULES = "# Binding rules"
ASK_REFERENCES = (
    ("devops-iac-reviewer", BINDING_RULES, CDK_DEPLOYMENT_ONLY),
    ("devops-iac-reviewer", BINDING_RULES, AWS_CONFIG),
    ("devops-iac-reviewer", "# Checklist (apply what the change touches)", USE_DOC_MCP_SERVERS),
    ("security-reviewer", BINDING_RULES, AWS_CONFIG),
    ("best-practice-reviewer", BINDING_RULES, USE_DOC_MCP_SERVERS),
    ("spec-author", "# What you produce", USE_DOC_MCP_SERVERS),
    ("spec-conductor", "# Binding rules (always loaded; the ones you apply most)", USE_DOC_MCP_SERVERS),
)
NAMED_REFERENCES = [(client, *reference) for client in CLIENTS for reference in ASK_REFERENCES]

# The agents sentence both setup prompts carry verbatim; phrases are compared whitespace-collapsed.
S_AGENTS = (
    "`aws-config.md` is named by `devops-iac-reviewer` and `security-reviewer`, `cdk-deployment-only.md` by "
    "`devops-iac-reviewer`, and `use-doc-mcp-servers.md` by `best-practice-reviewer`, `devops-iac-reviewer`, "
    "`spec-author` and `spec-conductor`, each with the marker `(where installed)`; a project that omits any of the "
    "three installs these agents unchanged."
)
SETUP_CLAUDE_PART_8_2 = "### Part 8.2 — .claude/rules/ (the detailed rules)"
SETUP_CLAUDE_PART_8_2_END = "### Part 8.2a"
SETUP_CLAUDE_CONDITIONS = (
    "`aws-config.md` (installed only in an AWS project)",
    "`use-doc-mcp-servers.md` (installed only where documentation MCP servers are configured)",
    "`cdk-deployment-only.md` (installed only where the project has a `cdk/` directory)",
)
SETUP_KIRO_HEADINGS = (
    "### 8.9 `aws-config.md` (always; installed only in an AWS project)",
    "### 8.17 `cdk-deployment-only.md` (conditional, CDK; installed only where the project has a `cdk/` directory)",
    "### 8.19 `use-doc-mcp-servers.md` (always; installed only where documentation MCP servers are configured)"
    " — replaces 4 separate files",
)
SETUP_KIRO_8A_1 = "### 8A.1 Create the agents directory and install the fleet"
SETUP_KIRO_8A_1_END = "### 8A.2"


def _agents_dir(client: str) -> Path:
    return ROOT / "clients" / client / "agents"


def _bodies(client: str) -> list[Path]:
    """The agent prompt bodies one client ships; for Kiro, the ``<name>.md`` files its descriptors load."""
    return sorted(_agents_dir(client=client).glob("*.md"))


def _body_id(path: Path) -> str:
    return f"{path.parent.parent.name}-{path.stem}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _unmarked_rules(text: str) -> dict[str, tuple[int, int]]:
    """Each conditional rule whose backticked occurrences are not all marked, as (occurrences, marked ones)."""
    unmarked = {}
    for rule in CONDITIONAL_RULES:
        named = text.count(f"`{rule}`")
        marked = len(re.findall(pattern=f"`{re.escape(rule)}`{MARKER_PATTERN}", string=text))
        if named != marked:
            unmarked[rule] = (named, marked)
    return unmarked


def _prompt_section(text: str, heading: str, end_prefix: str) -> str:
    """From the column-1 line ``heading`` up to the next column-1 line that starts with ``end_prefix``."""
    start = re.search(pattern=f"^{re.escape(heading)}$", string=text, flags=re.MULTILINE)
    assert start is not None, f"no heading line {heading!r}"
    end = re.compile(pattern=f"^{re.escape(end_prefix)}", flags=re.MULTILINE).search(string=text, pos=start.end())
    assert end is not None, f"no heading starting {end_prefix!r} after {heading!r}"
    return text[start.start() : end.start()]


def _body_section(text: str, heading: str) -> str:
    """From the column-1 line ``heading`` up to the next line beginning ``# ``."""
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.rstrip() == heading]
    assert starts, f"no heading line {heading!r}"
    first = starts[0]
    ends = [index for index in range(first + 1, len(lines)) if lines[index].startswith("# ")]
    return "\n".join(lines[first : ends[0] if ends else len(lines)])


def _assert_marked(path: Path) -> None:
    unmarked = _unmarked_rules(text=_read(path=path))
    assert not unmarked, (
        f"{_body_id(path=path)} names a conditionally installed rule without `(where installed)`; "
        f"rule: (backticked occurrences, marked occurrences) = {unmarked}"
    )


@pytest.mark.parametrize("path", _bodies(client=CLAUDE), ids=lambda path: path.stem)
def test_claude_bodies_mark_conditional_rules(path: Path) -> None:
    _assert_marked(path=path)


@pytest.mark.parametrize("path", _bodies(client=KIRO), ids=lambda path: path.stem)
def test_kiro_bodies_mark_conditional_rules(path: Path) -> None:
    _assert_marked(path=path)


def test_setup_claude_states_install_conditions() -> None:
    section = _collapse(
        text=_prompt_section(
            text=_read(path=SETUP_CLAUDE), heading=SETUP_CLAUDE_PART_8_2, end_prefix=SETUP_CLAUDE_PART_8_2_END
        )
    )
    missing = [phrase for phrase in (*SETUP_CLAUDE_CONDITIONS, S_AGENTS) if _collapse(text=phrase) not in section]
    assert not missing, f"setup-claude Part 8.2 lacks the install-condition phrases {missing}"


def test_setup_kiro_states_install_conditions() -> None:
    text = _read(path=SETUP_KIRO)
    lines = {line.strip() for line in text.splitlines()}
    missing = [heading for heading in SETUP_KIRO_HEADINGS if heading not in lines]
    section = _collapse(text=_prompt_section(text=text, heading=SETUP_KIRO_8A_1, end_prefix=SETUP_KIRO_8A_1_END))
    if _collapse(text=S_AGENTS) not in section:
        missing.append(f"{SETUP_KIRO_8A_1}: {S_AGENTS}")
    assert not missing, f"setup-kiro lacks the install-condition headings or sentence {missing}"


@pytest.mark.parametrize(
    ("client", "agent", "heading", "rule"),
    NAMED_REFERENCES,
    ids=[f"{client}-{agent}-{rule}" for client, agent, _, rule in NAMED_REFERENCES],
)
def test_conditional_rules_still_named(client: str, agent: str, heading: str, rule: str) -> None:
    path = _agents_dir(client=client) / f"{agent}.md"
    section = _body_section(text=_read(path=path), heading=heading)
    assert f"`{rule}`" in section, f"{client} {agent} no longer names `{rule}` under {heading!r}"


@pytest.mark.parametrize("path", [*_bodies(client=CLAUDE), *_bodies(client=KIRO)], ids=_body_id)
def test_marker_only_on_conditional_rules(path: Path) -> None:
    marked = MARKED_RULE_RE.findall(string=_read(path=path))
    others = sorted({name for name in marked if name not in CONDITIONAL_RULES})
    assert not others, f"{_body_id(path=path)} marks always-installed rules with `(where installed)`: {others}"
