"""The scope of the no-ai-attribution rule, in both of its bodies and in the texts that restate it (issue #6).

The rule bans two things: attribution of work to a tool (co-author trailers, "generated with" lines, sign-offs)
in commit messages, PR/MR text and issue text, and the listed words ("claude", "AI", "bot", ...) in the names an
agent authors (branches, worktrees, tags, stashes, refs, labels). It never bans a listed word inside a file or
directory path, a command, a setting or a product that a message names as the subject of the work. Its opening
paragraph once banned the words "into any name or message you create" while its self-check counted only a hit
"used as attribution or in a name", so the two halves of the one rule disagreed about every commit subject that
names a client directory. These tests pin the one scope in the Claude rule file, in its Kiro twin (section 8.28
of the Kiro setup prompt, from that heading line to the next section 8 heading line) and in the commands and
agents that restate it.

Every phrase is matched case-insensitively after collapsing each whitespace run to one space.

Run: ``python scripts/run_tests.py test/test_no_ai_attribution_rule.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_RULE_PATH = ROOT / "clients" / "claude" / "rules" / "no-ai-attribution.md"
KIRO_SETUP_PROMPT_PATH = ROOT / "prompts" / "setup-kiro.txt"
CLAUDE_SETUP_PROMPT_PATH = ROOT / "prompts" / "setup-claude.txt"
WORK_ISSUE_COMMAND_PATH = ROOT / "clients" / "claude" / "commands" / "work-issue.md"
AUTO_WORK_COMMAND_PATH = ROOT / "clients" / "claude" / "commands" / "auto-work.md"
CLAUDE_ORCHESTRATOR_PATH = ROOT / "clients" / "claude" / "agents" / "issue-work-orchestrator.md"
KIRO_ORCHESTRATOR_PATH = ROOT / "clients" / "kiro" / "agents" / "issue-work-orchestrator.md"

KIRO_SECTION_HEADING = "### 8.28 "
NEXT_SECTION_HEADING = "### 8."
SELF_CHECK_MARKER = "Self-check before"
KIRO_CONFIG_DIRECTORY = ".kiro/"
SENTENCE_END = ". "

WHITESPACE_RUN = re.compile(pattern=r"\s+")
PARAGRAPH_BREAK = re.compile(pattern=r"\n[ \t]*\n")
CLAUSE_BREAK = re.compile(pattern=r"\. |; ")

# The key phrases of the change.
K0 = "**Never attribute work to"
K1 = "attribution of work to a tool"
K2 = "names you author"
K3 = (
    "naming an existing file or directory path, command, setting or product as the subject of the work"
    " is not attribution"
)
CLAUDE_K4 = '"claude" (or "AI", "assistant", "bot", "LLM", "Anthropic", "Copilot", a model name)'
KIRO_K4 = '"claude"/"AI"/"assistant"/"bot"/"LLM"/"Anthropic"/"Copilot"/a model name'

# UB-2: the allowance sentence names its message domain directly before K3 and keeps the guard that bars it from
# every authored name; the self-check's own allowance clause is limited to messages the same way.
ALLOWANCE_DOMAIN = "In commit messages (subject line included), PR/MR titles and bodies, and issue text,"
ALLOWANCE_NAME_GUARD = "the allowance never extends to a branch, worktree, tag, stash, ref or label name"
SELF_CHECK_ALLOWANCE = "a path, command, setting or product named as the subject of the work"
SELF_CHECK_ALLOWANCE_DOMAIN = "in a commit message, PR/MR text or issue text"

# The anchors of the four restatements in the Claude setup prompt.
SETUP_CLAUDE_ANCHORS = (
    "These commands MUST follow `.claude/rules/no-ai-attribution.md`",
    "`keep-git-clean.md` and `no-ai-attribution.md`: no stale worktrees",
    "`no-ai-attribution.md` (descriptive names only;",
    "no-ai-attribution.md (descriptive names, no AI attribution)",
)
SETUP_CLAUDE_ANCHOR_IDS = ("R1", "R2", "R3", "R4")


@dataclass(frozen=True)
class BannedForm:
    """A wording of the blanket word ban that the rescoped rule and its restatements no longer carry."""

    label: str
    pattern: re.Pattern[str]


B1 = BannedForm(label="B1", pattern=re.compile(pattern=re.escape("into any name or message you create")))
B2 = BannedForm(label="B2", pattern=re.compile(pattern=r"never put[^.]*into any[^.]*message"))
B3 = BannedForm(label="B3", pattern=re.compile(pattern=r"every name (you create )?describes"))
B4 = BannedForm(label="B4", pattern=re.compile(pattern=r"claude/ai/bot into (a|any) branch, (worktree, )?commit"))
B5 = BannedForm(label="B5", pattern=re.compile(pattern=re.escape("any mention of claude/ai/assistant/bot")))


@dataclass(frozen=True)
class RuleBody:
    """One body of the rule: where it is read from and the phrases its unreworded text keeps."""

    name: str
    path: Path
    k4: str
    kept_trailer_phrases: tuple[str, ...]
    kept_auto_name_phrases: tuple[str, ...]

    def read(self) -> str:
        """The body's text: here the whole rule file."""
        return self.path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class KiroRuleBody(RuleBody):
    """The Kiro twin, embedded in the Kiro setup prompt as section 8.28."""

    def read(self) -> str:
        """The setup prompt from the section 8.28 heading line to the next line starting a section 8 heading."""
        lines = self.path.read_text(encoding="utf-8").splitlines(keepends=True)
        starts = [index for index, line in enumerate(lines) if line.startswith(KIRO_SECTION_HEADING)]
        assert starts, f"{self.path.name}: no line starts with {KIRO_SECTION_HEADING.strip()!r}"
        start = starts[0]
        ends = [index for index in range(start + 1, len(lines)) if lines[index].startswith(NEXT_SECTION_HEADING)]
        end = ends[0] if ends else len(lines)
        return "".join(lines[start:end])


@dataclass(frozen=True)
class Restatement:
    """A command or agent that restates the rule's clause, with the trailer phrase and the name clause it keeps."""

    name: str
    path: Path
    kept_phrase: str
    kept_name_phrase: str


CLAUDE_BODY = RuleBody(
    name="claude",
    path=CLAUDE_RULE_PATH,
    k4=CLAUDE_K4,
    kept_trailer_phrases=(
        "actively remove any AI/tool trailer or co-author line",
        'strip any auto-added "Generated with',
    ),
    kept_auto_name_phrases=(
        "`claude/<adjective>-<name>` auto-name",
        "rename it before pushing",
    ),
)
KIRO_BODY = KiroRuleBody(
    name="kiro",
    path=KIRO_SETUP_PROMPT_PATH,
    k4=KIRO_K4,
    kept_trailer_phrases=(
        "no `Co-Authored-By:",
        'strip any auto-added "Generated with',
    ),
    kept_auto_name_phrases=(
        "auto-generated `<tool>/<adjective>-<name>`",
        'never any name containing "claude"',
    ),
)
BODIES = (CLAUDE_BODY, KIRO_BODY)

COMMAND_KEPT_PHRASE = "never add a `Co-Authored-By`"
AGENT_KEPT_PHRASE = "strip any such trailer the tool adds"
COMMAND_NAME_PHRASE = "put no Claude/AI/bot into a branch or worktree name"
AGENT_NAME_PHRASE = "no branch or worktree name carries Claude/AI/assistant/bot"
RESTATEMENTS = (
    Restatement(
        name="work-issue-command",
        path=WORK_ISSUE_COMMAND_PATH,
        kept_phrase=COMMAND_KEPT_PHRASE,
        kept_name_phrase=COMMAND_NAME_PHRASE,
    ),
    Restatement(
        name="auto-work-command",
        path=AUTO_WORK_COMMAND_PATH,
        kept_phrase=COMMAND_KEPT_PHRASE,
        kept_name_phrase=COMMAND_NAME_PHRASE,
    ),
    Restatement(
        name="claude-orchestrator",
        path=CLAUDE_ORCHESTRATOR_PATH,
        kept_phrase=AGENT_KEPT_PHRASE,
        kept_name_phrase=AGENT_NAME_PHRASE,
    ),
    Restatement(
        name="kiro-orchestrator",
        path=KIRO_ORCHESTRATOR_PATH,
        kept_phrase=AGENT_KEPT_PHRASE,
        kept_name_phrase=AGENT_NAME_PHRASE,
    ),
)


def _normalise(text: str) -> str:
    """Each whitespace run collapsed to one space, lower-cased: the form every phrase is matched in."""
    return WHITESPACE_RUN.sub(repl=" ", string=text).strip().lower()


def _missing(text: str, phrases: tuple[str, ...]) -> list[str]:
    """The phrases that do not occur in the text (both normalised)."""
    normalised = _normalise(text=text)
    return [phrase for phrase in phrases if _normalise(text=phrase) not in normalised]


def _banned_found(text: str, forms: tuple[BannedForm, ...]) -> list[str]:
    """Every occurrence of a banned form in the normalised text, labelled with the form's id."""
    normalised = _normalise(text=text)
    return [f"{form.label}: {match.group(0)!r}" for form in forms for match in form.pattern.finditer(normalised)]


def _paragraphs(text: str) -> list[str]:
    """The blank-line-delimited paragraphs of a text, normalised."""
    return [_normalise(text=part) for part in PARAGRAPH_BREAK.split(text) if part.strip()]


def _opening_paragraph(body: RuleBody) -> str:
    """The first paragraph of the body that begins with K0."""
    opening = [part for part in _paragraphs(text=body.read()) if part.startswith(_normalise(text=K0))]
    assert opening, f"{body.name} body: no paragraph begins with {K0!r}"
    return opening[0]


def _self_check_paragraph(body: RuleBody) -> str:
    """The first paragraph of the body that contains the self-check marker."""
    marker = _normalise(text=SELF_CHECK_MARKER)
    self_check = [part for part in _paragraphs(text=body.read()) if marker in part]
    assert self_check, f"{body.name} body: no paragraph contains {SELF_CHECK_MARKER!r}"
    return self_check[0]


def _sentence_around(normalised: str, index: int) -> str:
    """The sentence of a normalised text that holds the character at ``index``, without its closing period."""
    previous_end = normalised.rfind(SENTENCE_END, 0, index)
    start = 0 if previous_end == -1 else previous_end + len(SENTENCE_END)
    end = normalised.find(SENTENCE_END, index)
    return normalised[start:] if end == -1 else normalised[start:end]


def _clauses(paragraph: str) -> list[str]:
    """The clauses of a normalised paragraph: the parts between one sentence end or semicolon and the next."""
    return [clause for clause in CLAUSE_BREAK.split(string=paragraph) if clause]


def _ub2_allowance_problems(body: RuleBody) -> list[str]:
    normalised = _normalise(text=body.read())
    k3_at = normalised.find(_normalise(text=K3))
    assert k3_at != -1, f"{body.name} body lacks the allowance sentence {K3!r}"
    problems = []
    if _normalise(text=f"{ALLOWANCE_DOMAIN} {K3}") not in normalised:
        problems.append(
            f"{body.name} allowance sentence does not name its message domain {ALLOWANCE_DOMAIN!r} right before K3"
        )
    if _normalise(text=ALLOWANCE_NAME_GUARD) not in _sentence_around(normalised=normalised, index=k3_at):
        problems.append(f"{body.name} allowance sentence lost the guard {ALLOWANCE_NAME_GUARD!r}")
    return problems


def _ub2_self_check_allowance_problems(body: RuleBody) -> list[str]:
    exemption = _normalise(text=SELF_CHECK_ALLOWANCE)
    clauses = [clause for clause in _clauses(paragraph=_self_check_paragraph(body=body)) if exemption in clause]
    assert clauses, f"{body.name} self-check paragraph: no clause exempts {SELF_CHECK_ALLOWANCE!r}"
    domain = _normalise(text=SELF_CHECK_ALLOWANCE_DOMAIN)
    return [
        f"{body.name} self-check exempts a path or product beyond messages (lacks {SELF_CHECK_ALLOWANCE_DOMAIN!r}):"
        f" {clause!r}"
        for clause in clauses
        if domain not in clause
    ]


def _ac1_problems(body: RuleBody) -> list[str]:
    missing = _missing(text=_opening_paragraph(body=body), phrases=(K0, K1, K2))
    return [f"{body.name} opening paragraph lacks {phrase!r}" for phrase in missing]


def _ac2_problems(body: RuleBody) -> list[str]:
    missing = _missing(text=body.read(), phrases=(K3,))
    return [f"{body.name} body lacks the allowance sentence {phrase!r}" for phrase in missing]


def _ac3_self_check_problems(body: RuleBody) -> list[str]:
    missing = _missing(text=_self_check_paragraph(body=body), phrases=(K1, K2))
    return [f"{body.name} self-check paragraph lacks {phrase!r}" for phrase in missing]


def _ac3_blanket_ban_problems(body: RuleBody) -> list[str]:
    found = _banned_found(text=body.read(), forms=(B1, B2, B3))
    return [f"{body.name} body still bans the listed words in every message: {hit}" for hit in found]


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ac1_opening_paragraph_states_one_scope(body: RuleBody) -> None:
    problems = _ac1_problems(body=body)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ac2_body_permits_a_path_or_product_named_as_the_subject(body: RuleBody) -> None:
    problems = _ac2_problems(body=body)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ac3_self_check_states_the_opening_scope(body: RuleBody) -> None:
    problems = _ac3_self_check_problems(body=body)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ac3_no_sentence_bans_the_listed_words_in_every_message(body: RuleBody) -> None:
    problems = _ac3_blanket_ban_problems(body=body)
    assert not problems, "\n".join(problems)


def test_ac4_kiro_body_carries_the_scope_the_allowance_and_the_agreement() -> None:
    problems = (
        _ac1_problems(body=KIRO_BODY)
        + _ac2_problems(body=KIRO_BODY)
        + _ac3_self_check_problems(body=KIRO_BODY)
        + _ac3_blanket_ban_problems(body=KIRO_BODY)
    )
    if KIRO_CONFIG_DIRECTORY not in KIRO_BODY.read():
        problems.append(f"kiro body no longer exempts the {KIRO_CONFIG_DIRECTORY} configuration directory")
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ub1_body_still_forbids_attribution_trailers(body: RuleBody) -> None:
    missing = _missing(text=body.read(), phrases=body.kept_trailer_phrases)
    assert not missing, f"{body.name} body lost the kept trailer phrases {missing}"


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ub2_body_still_bans_the_listed_words_in_authored_names(body: RuleBody) -> None:
    missing = _missing(text=body.read(), phrases=body.kept_auto_name_phrases)
    assert not missing, f"{body.name} body lost the kept auto-name phrases {missing}"
    missing_k4 = _missing(text=_opening_paragraph(body=body), phrases=(body.k4,))
    assert not missing_k4, f"{body.name} opening paragraph lost the listed words {missing_k4}"


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ub2_allowance_sentence_names_its_message_domain_and_keeps_the_name_guard(body: RuleBody) -> None:
    problems = _ub2_allowance_problems(body=body)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("body", BODIES, ids=lambda body: body.name)
def test_ub2_self_check_allowance_is_limited_to_messages(body: RuleBody) -> None:
    problems = _ub2_self_check_allowance_problems(body=body)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("anchor", SETUP_CLAUDE_ANCHORS, ids=SETUP_CLAUDE_ANCHOR_IDS)
def test_ub3_setup_claude_restatement_states_attribution_and_names_only(anchor: str) -> None:
    text = _normalise(text=CLAUDE_SETUP_PROMPT_PATH.read_text(encoding="utf-8"))
    normalised_anchor = _normalise(text=anchor)
    start = text.find(normalised_anchor)
    assert start != -1, f"{CLAUDE_SETUP_PROMPT_PATH.name} no longer carries the restatement anchor {anchor!r}"
    end = text.find(SENTENCE_END, start + len(normalised_anchor))
    restatement = text[start:] if end == -1 else text[start:end]
    found = _banned_found(text=restatement, forms=(B1, B2))
    assert not found, f"the restatement at {anchor!r} bans the listed words in every message: {found}"


@pytest.mark.parametrize("restatement", RESTATEMENTS, ids=lambda restatement: restatement.name)
def test_ub3_restatement_file_states_attribution_and_names_only(restatement: Restatement) -> None:
    text = restatement.path.read_text(encoding="utf-8")
    found = _banned_found(text=text, forms=(B1, B2, B4, B5))
    assert not found, f"{restatement.name} restates the blanket word ban: {found}"
    missing = _missing(text=text, phrases=(restatement.kept_phrase,))
    assert not missing, f"{restatement.name} lost the kept trailer phrase {missing}"


@pytest.mark.parametrize("restatement", RESTATEMENTS, ids=lambda restatement: restatement.name)
def test_ub3_restatement_file_keeps_its_branch_and_worktree_name_clause(restatement: Restatement) -> None:
    missing = _missing(text=restatement.path.read_text(encoding="utf-8"), phrases=(restatement.kept_name_phrase,))
    assert not missing, f"{restatement.name} lost its branch and worktree name clause {missing}"
