# Prompt — issue #6: no-ai-attribution bans the word, not the attribution

Tier: S — wording change in one shipped rule and its Kiro twin; no new interface.

Kind: BUGFIX (a rule that contradicts itself).

## Goal

`clients/claude/rules/no-ai-attribution.md` opens with a blanket ban — never put "claude" (or "AI",
"assistant", …) "into any name or message you create" — and closes with a narrower self-check: a hit "used as
attribution or in a name" is a defect. The only exemption is the `.claude/` config directory. This repository's
product paths contain the word (`clients/claude/`, `prompts/setup-claude.txt`), so an agent following the
opening sentence literally cannot describe a change to them in a commit, PR or issue. The Kiro twin
(`prompts/setup-kiro.txt` section `### 8.28 \`no-ai-attribution.md\` (always) — fleet convention`) carries
the same blanket sentence and exempts only `.kiro/`.

## Scope (the ask)

- Reword the opening bold paragraph and the closing self-check of `clients/claude/rules/no-ai-attribution.md`
  to ONE scope: the ban covers (a) attributing work to a tool — co-author trailers, "generated with" lines,
  sign-offs, "fixed by <agent>" — in commits, PR/MR titles and bodies and issue text, and (b) the words in names
  an agent AUTHORS — branches, worktrees, tags, stashes, refs, labels.
- Add an explicit allowance: naming an existing file or directory path, command, setting, or a product or
  client as the SUBJECT of the work (`clients/claude/`, `prompts/setup-claude.txt`, "the Claude client's
  hooks") is not attribution and is permitted. Decided (DL-001): the allowance is phrased generally, not as a
  named list, and covers subject matter as well as paths (the issue's two open questions).
- The same scope and allowance in the Kiro twin, section 8.28 of `prompts/setup-kiro.txt`.
- One pass over the rule's restatements in `prompts/setup-claude.txt` (the commands paragraph "These commands
  MUST follow `.claude/rules/no-ai-attribution.md`", the fleet-conventions bullet, the Part 12 shared-rules
  bullet and the final-report shared-rules line): checked during prompt synthesis — each states attribution and
  names only ("no Claude/AI/bot attribution", "never an AI trailer", "descriptive names, no AI attribution"),
  none states the blanket word ban, so no edit is needed there. The test pins that.
- A test under `test/` that pins the single scope and the allowance in both bodies.

## Out of scope

- The installed `.claude/rules/no-ai-attribution.md` (toolchain; it changes only by release and promotion —
  the issue's fourth work item is delivered by the release that batches this run's fixes).

## Tests

Every acceptance criterion and unchanged-behaviour clause is pinned by a test.
E2E: not applicable — rule text; no runtime behaviour of a deployed system changes. CI's `tests` group runs the
new test.
