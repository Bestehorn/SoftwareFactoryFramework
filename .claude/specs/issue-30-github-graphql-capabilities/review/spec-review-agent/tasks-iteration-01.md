# Tasks review, iteration 01 — spec-review-agent (issue #30, tier M)

## Conductor checks

- D8 to tasks: all nine D8 files are owned by a task, and every file a task names is a D8 file. G is in 2.2 and 3.1,
  and Q is in 2.1 and 3.2. Those pairs fall in waves 2 and 3, and inside each wave every task owns a different file
  (`parallel-by-default.md`). Each wave-3 test stays red until its own wave-3 IMPL, so this is not a defect.
- Scope: no task adds anything beyond D1 to D8 and § Correctness Properties. The extra Run-line suites
  (`test_toolchain_manifest.py`, which reads the map, and `test_layout.py`) are existing tests.
- Precondition: it is stated. `git merge-base --is-ancestor` returns 0 for both `f374b3d` and `6fd2f64` against
  `origin/main`. The trunk tip is now `fe79965` (#29, PR #50), and `git diff aafecbb origin/main` touches none of
  `registry.py`, `graphql_only.py`, `github_wrapper.py`, V or the map. The trunk `commands/call.py` has
  `GATED_OPERATIONS: Mapping[str, Optional[str]]` and `GATED_NOT_SENT = frozenset({"pulls/merge-async"})`, and
  `refuse_gated` leaves out `SENDS_IT` for an ID in `GATED_NOT_SENT`. D4's five REST records are declared on the trunk.
  No file under `src/payload/scripts/` names `enablePullRequestAutoMerge`, so the `GATED_NOT_SENT` entry in 2.4 is
  correct.
- Cap: `tasks.md` is 13,916 B, under the 15,000 B cap.
- Stale design sentences: they do not mislead an implementer who follows the tasks. Task 2.4 and the Precondition
  state the `GATED_NOT_SENT` entry with no condition, and on the rebased branch the design's own conditionals ("once
  the rebased trunk has it", "whichever lands second") point to that same entry. They are false as statements of
  fact, though, and no test catches a missing entry (C2). Replacement text is in C1.

### C1 — Three design sentences describe #32 as not yet on the trunk
Severity: C
Location: design.md § D5 (the `GATED_NOT_SENT` bullet); § D8 (the `commands/call.py` row); § Residuals ("The
`merge-pr` refusal's wording")
Defect: #32 is merged as `6fd2f64`, an ancestor of `origin/main`. D5 still says "not on the trunk", D8 and D5 make the
entry depend on the landing order, and the Residual's "if this change lands before #32" can no longer happen.
Material-because: not material. Task 2.4 states the outcome the conditionals now reach; the fix only restates text.
Proposed-edit:
- D5: replace the bullet "#32 (branch `issue-32-issues-pulls-records`, not on the trunk) adds `GATED_NOT_SENT`: the
  gated IDs that their subcommand does not send, whose refusal leaves out "which sends it".
  `graphql/enablePullRequestAutoMerge` joins it once the rebased trunk has it (Residuals)." with "#32 (PR #48, merged
  as `6fd2f64`, an ancestor of `origin/main`) added `GATED_NOT_SENT`: the gated IDs that their subcommand does not
  send, whose refusal leaves out "which sends it". `graphql/enablePullRequestAutoMerge` joins it, because `merge-pr`
  never sends it."
- D8 `commands/call.py` row: replace "D5's `GATED_OPERATIONS` entries (and the `GATED_NOT_SENT` entry once on the
  trunk);" with "D5's `GATED_OPERATIONS` entries and its `GATED_NOT_SENT` entry;".
- Residuals: delete the bullet "**The `merge-pr` refusal's wording.** If this change lands before #32, …; whichever
  lands second adds it to `GATED_NOT_SENT`."

### C2 — No test fails if task 2.4 leaves out the `GATED_NOT_SENT` entry
Severity: C
Location: tasks.md § Wave 2, task 2.2; design.md § Correctness Properties, AC-3.2
Defect: the only check on the `graphql/enablePullRequestAutoMerge` refusal is that it names `merge-pr`. If the entry
is missing, every Run line still passes, and the log reads "use the merge-pr subcommand, which sends it". That is
false, because `merge-pr` never sends this mutation. The trunk's K `_gated_cases` case `pulls-merge-async-is-merge-pr`
asserts `lacking(text=SENDS_IT)` for the same situation.
Material-because: not a gap in an acceptance criterion. AC-3.2 (as #32 AC-6) requires naming `merge-pr`, and the test
checks that. The fix tightens an existing oracle and adds no criterion.
Proposed-edit:
- design.md AC-3.2: replace "the record for `graphql/enablePullRequestAutoMerge` names `merge-pr`;" with "the record
  for `graphql/enablePullRequestAutoMerge` names `merge-pr` and does not hold "which sends it", as K's
  `pulls-merge-async-is-merge-pr` case judges `pulls/merge-async`;".
- tasks.md 2.2: replace "`test_a_refused_mutation_sends_nothing` (over the constant)." with
  "`test_a_refused_mutation_sends_nothing` (over the constant; the `graphql/enablePullRequestAutoMerge` record names
  `merge-pr` without "which sends it")."

### C3 — F.3's file list has no room for a findings-ledger row
Severity: C
Location: tasks.md § Final, F.3
Defect: F.3 requires that, outside the spec directory, the diff name only D8's files. `issue-filing-discipline.md`
says ledger rows are "committed in the change they came from, before its push". Each sibling slice added rows to
`docs/findings-ledger.md` in its implementation commit: #27 `99c26c7`, #32 `eb63d18`, #29 `c007a9f`
(`git log aafecbb..origin/main -- docs/findings-ledger.md`). If this change routes a residual to the ledger, F.3
fails.
Material-because: not material to the product. It is a false verify failure, or a ledger row dropped to keep F.3
green.
Proposed-edit: in F.3 replace "outside the spec directory, that diff names only D8's files" with "outside the spec
directory and `docs/findings-ledger.md` (rows written by `scripts/memory_compile.py ledger add`), that diff names only
D8's files".

### D1 — The `GATED_NOT_SENT` comment gains an ID but not its reason
Severity: D
Location: tasks.md § Wave 2, task 2.4
Defect: the trunk comment above `GATED_NOT_SENT` explains only `pulls/merge-async` ("`merge-pr` merges through
`pulls/merge`, never through `pulls/merge-async`…"). Task 2.4 adds an ID without saying why it belongs there.
Proposed-edit: after "and `GATED_NOT_SENT` gains `graphql/enablePullRequestAutoMerge`" insert ", its comment adding
that `merge-pr` never turns auto-merge on".

Verdict: READY
