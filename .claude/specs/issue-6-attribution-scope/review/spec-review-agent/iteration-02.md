# Spec review — issue-6-attribution-scope — iteration 02 (tier S, combined, delta)

Scope: the iteration-01 fix sites (B1, B2, C1, C2) and the regions they changed. Text passed in iteration 01 stays
passed.

### C1 — UB-2's K2 check is red on today's text, against T1's red profile
Severity: C
Location: change.md § Tests UB-2; § Tasks T1
Defect: UB-2 now asserts K2 `names you author` in each body's opening paragraph. Neither body has that phrase today
(Claude rule opening paragraph: "… into any name or message you create.** … any ref or label."; setup-kiro 8.28: "…
into any name or message you create.** … NO exceptions to:"), so the UB-2 test fails before I1 while T1 says "the
other UB checks pass". The K2 half came from the iteration-01 B2 edit. Its note "the UB checks still pass on red"
was wrong about K2. No behaviour breaks: K2 in the opening paragraph is already AC-1's check, and after I1 every
check is green.
Proposed-edit: Tests, replace "UB-2 — the kept auto-name phrases in each body, and K4 and K2 in each body's opening
paragraph." with "UB-2 — the kept auto-name phrases in each body, and K4 in each body's opening paragraph (K2 there
is AC-1's check)."

### C2 — B4 also matches a correct restatement that keeps "Claude/AI/bot into" for names
Severity: C
Location: change.md § Key phrases B4; § Files restatement bullet
Defect: `[^.]*` runs to the first period. A restated sentence such as "put no Claude/AI/bot into any branch or
worktree name, attribute no work to a tool in a commit, PR or issue" carries exactly the scope § Files asks for, but
it still matches B4 and keeps T1 red after a correct I1.
Proposed-edit: Key phrases, replace "B4 regex `claude/ai/bot into [^.]*\b(commit|pr|issue)\b`" with "B4 regex
`claude/ai/bot into (a|any) branch, (worktree, )?commit`". This still matches both command files today
(work-issue "Claude/AI/bot into a branch, commit,"; auto-work "Claude/AI/bot into any branch, worktree, commit,").

### C3 — No decision-log entry records taking iteration-01 C1 into the change
Severity: C
Location: decisions/decision-log.md
Defect: iteration-01 C1 recommended a residual. Instead the change now includes the four restatement files: the
Ask's last clause, UB-3 and I1's Files. DL-001 still records only "setup-claude restatements need no edit", and the
run's `runs/1aba3b99/decision-log.md` has no issue-6 entry. `agent-state-convention.md` §2 rule 4 requires an entry
for a choice between alternatives and for a finding whose grade changed.
Proposed-edit: append `DL-002`. Decision: restate the four restatement files in this change instead of leaving a
residual. Driver: review/spec-review-agent/iteration-01.md#C1, `issue-filing-discipline.md` fix-first branch 2.
Evidence: the work-issue, auto-work and both issue-work-orchestrator clauses that B4 and B5 quote.

## Fix-site verification (no finding)

- B1 fix: the § Files rule bullet states K3's domain (commit messages with subject line, PR/MR titles and bodies,
  issue text, never a branch/worktree/tag/stash/ref/label name). Both naming sentences become "name and message".
  B3 matches today's Claude "Every name you create describes" and Kiro "every name describes", and matches neither
  rewritten form. AC-3 is red today and can go green.
- B2 fix: K4 is present verbatim today in both opening paragraphs (rule § opening bold paragraph; setup-kiro 8.28
  `"claude"/"AI"/…/a model name into any`).
- Restatements start red. After whitespace collapse and case-folding:
  - work-issue `Honor the always-loaded rules throughout:` "Claude/AI/bot into a branch, commit" and auto-work
    `# The mandates that apply to every step` "Claude/AI/bot into any branch, worktree, commit" both match B4.
  - The `NO AI ATTRIBUTION` paragraphs of both issue-work-orchestrator files match B5 ("any mention of
    Claude/AI/assistant/bot").
  - No other line in the four files matches B4 or B5. work-issue's branch-name line "never put claude/ai/bot in
    the name" is "in", not "into".
  - B1 and B2 match none of the four files today.
- Trailer bans survive the rewrite.
  - Each command file keeps "never add a `Co-Authored-By`" after the reworded clause, in the same sentence.
  - Each agent file keeps "Strip any such trailer the tool adds", the sentence after the reworded one.
  - UB-1's rule and twin phrases are untouched by the delta.
- Ask coverage: no other file under `clients/` or `prompts/` carries the blanket form. The other hits state
  attribution only ("no Claude/AI attribution", "no AI attribution", "no Claude/AI/bot attribution").
- C2 (iteration 01): `prompts.md` exists.

Security lens (K3 domain, restatement allowance): no finding. The allowance covers a path or product "named as the
subject", and every restatement keeps its trailer ban. DevOps and standards lenses: the delta changes neither E2E,
CI wiring nor file layout. No finding.

## Coverage

| Criterion | Test in change.md § Tests | Can fail | Gap |
|---|---|---|---|
| AC-1 | K0, K1, K2 in each opening paragraph | yes, red today | none |
| AC-2 | K3 in each body | yes, red today | none |
| AC-3 | K1, K2 in each self-check; B1, B2, B3 absent | yes, red today | none |
| AC-4 | AC-1..AC-3 checks on the Kiro body; `.kiro/` present | yes, red today | none |
| UB-1 | kept trailer phrases, each body | yes | none |
| UB-2 | kept auto-name phrases; K4 (+K2) in each opening paragraph | yes | K2 half red today (C1) |
| UB-3 | R1–R4 anchors free of B1/B2; four files free of B1, B2, B4, B5, kept phrase held | yes, files red today | B4 over-matches (C2) |
| E2E | not applicable (rule text) | n/a | none |

CLEAN — READY
