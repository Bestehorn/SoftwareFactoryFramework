# Spec review — issue-6-attribution-scope — iteration 01 (tier S, combined)

### B1 — Commit subjects and PR titles stay "names", so the allowance does not reach them
Severity: B
Location: change.md § Files (rule bullet, setup-kiro bullet); § Tests AC-2, AC-3
Defect: The paragraph this change keeps calls commit subjects and PR titles names ("Every name you create describes
the work: … commit subjects …; PR titles the outcome"; Kiro: "every name describes … commit subjects …; PR/MR titles
the outcome"), the new scope bans the listed words in "names you author", and K3 says only that subject-naming "is
not attribution". So a commit subject or PR title naming `clients/claude/` stays forbidden. K3 also sits in that
names paragraph, beside the `.claude/` exemption, where it reads as a second exemption for branch names.
Material-because: AC-2 (a commit message or PR/MR title naming a path SHALL be permitted) is contradicted; the
names-paragraph placement weakens UB-2.
Proposed-edit: (1) Files, rule bullet: replace "The allowance covers messages (commit messages, PR/MR titles and
bodies, issue text), never authored names (UB-2)." with "The K3 sentence states its domain in the rule: commit
messages (subject line included), PR/MR titles and bodies, and issue text, never a branch, worktree, tag, stash, ref
or label name (UB-2). The second paragraph's `Every name you create describes the work:` becomes `Every name and
message you create describes the work:`." (2) Files, setup-kiro bullet: after "the same edits" insert ", with
`every name describes` → `every name and message describes` in the naming-standard sentence". (3) Key phrases: add
row `B3 | regex every name (you create )?describes | absent from the body`. Tests: AC-3 reads "B1, B2 and B3 absent
from each body". B3 matches both bodies today, so T1 is red on it.

### B2 — UB-2's general ban on the listed words in names is not pinned
Severity: B
Location: change.md § Tests UB-2; § Key phrases
Defect: Apart from the auto-name, the listed words are kept out of branch, worktree, tag and ref names only by the
opening paragraph this change rewrites ("Never put "claude" (or "AI", …, a model name) into any name …"). The UB-2
test checks only the auto-name phrases (Claude) and `never any name containing "claude"` (Kiro, branch bullet, three
words). K2 `names you author` passes on a rewrite that drops the word list or the ban, so the exclusion of "LLM",
"Anthropic", "Copilot" and model names from authored names can disappear while T1 stays green.
Material-because: UB-2 (listed words excluded from authored branch, worktree and ref names) is not protected.
Proposed-edit: Key phrases: add row `K4 | the word list as written today, Claude: "claude" (or "AI", "assistant",
"bot", "LLM", "Anthropic", "Copilot", a model name); Kiro: "claude"/"AI"/"assistant"/"bot"/"LLM"/"Anthropic"/
"Copilot"/a model name | the opening paragraph, verbatim`. Tests: replace "UB-2 — the kept auto-name phrases in
each body." with "UB-2 — the kept auto-name phrases in each body, and K4 and K2 in each body's opening paragraph."
(K4 is present today, so the UB checks still pass on red.)

### C1 — Residual: two shipped commands keep the blanket form
Severity: C
Location: change.md § Residuals
Defect: `clients/claude/commands/work-issue.md` ("never put Claude/AI/bot into a branch, commit, PR, or issue") and
`clients/claude/commands/auto-work.md` ("put no Claude/AI/bot into any branch, worktree, commit, PR, or issue text")
restate the word ban for commit, PR and issue text, so they will contradict the reworded rule. Issue #6's
restatement work item names only `prompts/setup-claude.txt`, so both files are outside this ask.
Proposed-edit: add to Residuals: "- `clients/claude/commands/work-issue.md` and `auto-work.md` restate the blanket
word ban for commit, PR and issue text; outside this ask; routed per `issue-filing-discipline.md`."

### C2 — The spec directory has no `prompts.md`
Severity: C
Location: spec directory (conductor-owned)
Defect: `.claude/rules/document-user-prompts.md` item 2 requires `prompts.md` with the chronological conversation,
but the directory holds only `prompt.md`, `qa_log.md`, `change.md` and `decisions/`.
Proposed-edit: the conductor writes `prompts.md` holding the `/auto-work` invocation and the issue #6 text quoted in
change.md § User Prompts.

Security lens (K3 as cover for attribution): no finding. K3 is limited to "as the subject of the work". K0 keeps
"Never attribute work to" at the head of the opening paragraph and K1 keeps the attribution ban in both the opening
and the self-check. The trailer phrases stay pinned in both bodies (UB-1, verified present in
`clients/claude/rules/no-ai-attribution.md` § Overriding the tool defaults and `prompts/setup-kiro.txt` 8.28 bullets).
A "generated with" line names the tool as producer, not as subject, so K3 does not cover it. The names-side leak is B1.

DevOps lens: no finding. `E2E: not applicable` matches `always-test-e2e.md` § What needs no end-to-end check;
`pyproject.toml` `testpaths` includes `test`, and `scripts/run_checks.py` `tests` delegates to `scripts/run_tests.py`.
No existing test reads the rule or section 8.28. `test/test_toolchain_integrity.py` compares the installed copy
against the pinned commit, so editing the product file does not break it.

## Coverage

| Criterion | Test in change.md § Tests | Can fail | Gap |
|---|---|---|---|
| AC-1 | K0, K1, K2 in each opening paragraph | yes, red today | none |
| AC-2 | K3 in each body | yes, red today | the domain is not pinned (B1) |
| AC-3 | K1, K2 in each self-check; B1, B2 absent | yes, red today | the "every name … commit subjects" sentence (B1, B3) |
| AC-4 | AC-1..AC-3 checks on the Kiro body; `.kiro/` present | yes, red today | none |
| UB-1 | kept trailer phrases, each body | yes | none |
| UB-2 | kept auto-name phrases, each body | yes | the general name ban and word list (B2, K4) |
| UB-3 | R1–R4 present; anchor-to-". " text free of B1, B2 | yes | none |
| E2E | not applicable (rule text) | n/a | none |

All UB kept phrases and R1–R4 were checked present in today's text after whitespace collapse; B1 and B2 match
both bodies today.

NOT-CLEAN (0 A, 2 B) — NOT-READY
