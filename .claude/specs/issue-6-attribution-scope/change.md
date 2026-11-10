# Change — issue #6: no-ai-attribution bans attribution and authored names, not words in paths

Tier: S. Kind: bugfix.

## User Prompts

- The run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end" (`/auto-work`).
- Issue #6 title: "no-ai-attribution: ban attribution, not file paths that contain 'claude'".

## Ask

`clients/claude/rules/no-ai-attribution.md` opens with a ban on the listed words "into any name or message you create"
but its self-check counts only a hit "used as attribution or in a name". Reword it to the one scope of AC-1 with the
general allowance of AC-2 (DL-001). The Kiro twin (``### 8.28 `no-ai-attribution.md` (always) — fleet convention``
in `prompts/setup-kiro.txt`) and the shipped commands and agents that restate the ban follow.

## Acceptance criteria

- AC-1 The rule SHALL state one scope: the ban covers attribution of work to a tool (co-author trailers, "generated
  with" lines, sign-offs) in commit messages, PR/MR titles and bodies and issue text, and the listed words in names an
  agent authors (branches, worktrees, tags, stashes, refs, labels).
- AC-2 WHEN a commit message, PR/MR title or body, or issue text names an existing file or directory path, or a
  command, setting or product as the subject of the work, that contains a listed word, the rule SHALL permit it.
- AC-3 The rule's opening bold paragraph and its closing self-check SHALL state the same scope, and no sentence of the
  rule SHALL forbid the listed words in a message outside that scope.
- AC-4 The Kiro twin's body SHALL carry the scope of AC-1, the allowance of AC-2 and the agreement of AC-3, and SHALL
  continue to exempt the `.kiro/` configuration directory.

## Unchanged behaviour

- UB-1 The rule and its Kiro twin SHALL CONTINUE TO forbid co-author and "generated with" trailers and any
  attribution of work to a tool in commits, PRs/MRs and issues.
- UB-2 They SHALL CONTINUE TO exclude the listed words from authored branch, worktree and ref names, including the
  tool's `claude/<adjective>-<name>` auto-name.
- UB-3 The rule's restatements SHALL CONTINUE TO state attribution and names only, without the blanket word ban: the
  four in `prompts/setup-claude.txt`, not edited, and the four restatement files of § Files, restated by I1.

## Key phrases

Matched case-insensitively after collapsing each whitespace run to one space; no phrase is split by emphasis or
backticks. K1–K3 are written verbatim; K0, K4, the kept phrases and R1–R4 stay as today.

| Id | Phrase | Where |
|---|---|---|
| K0 | `**Never attribute work to` | begins each body's opening paragraph |
| K1 | `attribution of work to a tool` | each body's opening paragraph AND self-check paragraph |
| K2 | `names you author` | each body's opening paragraph AND self-check paragraph |
| K3 | `naming an existing file or directory path, command, setting or product as the subject of the work is not attribution` | each body, the allowance sentence |
| K4 | Claude `"claude" (or "AI", "assistant", "bot", "LLM", "Anthropic", "Copilot", a model name)`; Kiro `"claude"/"AI"/"assistant"/"bot"/"LLM"/"Anthropic"/"Copilot"/a model name` | each body's opening paragraph |

Absent — B1 and B2 from each body and each restatement file, B3 from each body, B4 and B5 from each restatement file:

- B1 `into any name or message you create`
- B2 regex `never put[^.]*into any[^.]*message`
- B3 regex `every name (you create )?describes`
- B4 regex `claude/ai/bot into (a|any) branch, (worktree, )?commit`
- B5 `any mention of claude/ai/assistant/bot`

Kept (in text left unreworded):

- Claude, `## Overriding the tool defaults (IMPORTANT)`: `actively remove any AI/tool trailer or co-author line`,
  `strip any auto-added "Generated with`, `` `claude/<adjective>-<name>` auto-name ``, `rename it before pushing`.
- Kiro bullets: `` no `Co-Authored-By: ``, `strip any auto-added "Generated with`,
  `` auto-generated `<tool>/<adjective>-<name>` ``, `never any name containing "claude"`.
- Each command file: `` never add a `Co-Authored-By` ``; each agent file: `strip any such trailer the tool adds`.

Anchors in `prompts/setup-claude.txt`:

- R1 `` These commands MUST follow `.claude/rules/no-ai-attribution.md` ``
- R2 `` `keep-git-clean.md` and `no-ai-attribution.md`: no stale worktrees ``
- R3 `` `no-ai-attribution.md` (descriptive names only; ``
- R4 `no-ai-attribution.md (descriptive names, no AI attribution)`

## Files

Every edited file keeps its line style, within 120 columns.

- `clients/claude/rules/no-ai-attribution.md` — reword the opening bold paragraph and the closing self-check to carry
  K1 and K2; add the K3 sentence beside the `.claude/` exemption sentence, which stays. The K3 sentence states its
  domain: commit messages (subject line included), PR/MR titles and bodies, and issue text, never a branch,
  worktree, tag, stash, ref or label name (UB-2). `Every name you create describes the work:` becomes `Every name and
  message you create describes the work:`.
- `prompts/setup-kiro.txt` — the fenced body of section 8.28 only: the same edits, with `every name describes` →
  `every name and message describes` in the naming-standard sentence and the K3 sentence beside the `.kiro/`
  sentence.
- The restatement files — `clients/claude/commands/work-issue.md` (the `Honor the always-loaded rules throughout:`
  paragraph), `clients/claude/commands/auto-work.md` (`# The mandates that apply to every step`), and the
  `NO AI ATTRIBUTION` paragraph of `clients/claude/agents/issue-work-orchestrator.md` and
  `clients/kiro/agents/issue-work-orchestrator.md`: restate the Claude/AI clause to the rule's scope — no attribution
  of work to a tool in a commit, PR/MR or issue, a path or product named as the subject allowed, no listed word in a
  branch or worktree name; the trailer clause stays.
- `test/test_no_ai_attribution_rule.py` — new framework test.

## Tests

`test/test_no_ai_attribution_rule.py`: example tests, the two bodies parametrised, files read as UTF-8 from
`Path(__file__).resolve().parents[1]`. The Claude body is the rule file; the Kiro body is `prompts/setup-kiro.txt`
from the `### 8.28` heading line to the next line starting `### 8.`. The opening paragraph is the first
blank-line-delimited paragraph starting with K0; the self-check paragraph is the one containing `Self-check before`.

- AC-1 — K0, K1 and K2 in each body's opening paragraph.
- AC-2 — K3 in each body.
- AC-3 — K1 and K2 in each body's self-check paragraph; B1, B2 and B3 absent from each body.
- AC-4 — the AC-1 to AC-3 checks on the Kiro body, and `.kiro/` in it.
- UB-1 — the kept trailer phrases in each body.
- UB-2 — the kept auto-name phrases in each body, and K4 in each body's opening paragraph.
- UB-3 — R1 to R4 present in `prompts/setup-claude.txt`, the text from each anchor to the next `. ` free of B1 and
  B2; each restatement file free of B1, B2, B4 and B5 and holding its kept phrase.
- E2E: not applicable; CI's `tests` group runs the new test (`pyproject.toml` `testpaths` includes `test`).

## Tasks (one wave)

- [ ] T1 TEST: the test as in Tests, captured red before I1 (the AC checks and the restatement-file UB-3 check fail
  on today's text, the other UB checks pass) — Files: `test/test_no_ai_attribution_rule.py` — Validates: AC-1, AC-2,
  AC-3, AC-4, UB-1, UB-2, UB-3
- [ ] I1 IMPL: the rule, the 8.28 body and the restatement files per Files and Key phrases; T1 green — Files:
  `clients/claude/rules/no-ai-attribution.md`, `prompts/setup-kiro.txt`, `clients/claude/commands/work-issue.md`,
  `clients/claude/commands/auto-work.md`, `clients/claude/agents/issue-work-orchestrator.md`,
  `clients/kiro/agents/issue-work-orchestrator.md` — Validates: AC-1, AC-2, AC-3, AC-4, UB-1, UB-2, UB-3

## Residuals

- The installed `.claude/rules/no-ai-attribution.md` (toolchain) changes only by the release and promotion that
  batches this run's fixes — the issue's fourth work item.
