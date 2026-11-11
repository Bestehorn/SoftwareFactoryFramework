# Review — issue #15 `change.md`, iteration 02 (tier S, combined, DELTA: all lenses)

`change.md` is 7,975 B (`wc -c`), under the 8,000 B cap.

## Iteration-01 findings

| ID | Sev | Status | Evidence in the current text |
|---|---|---|---|
| B1 | B | resolved | Files, family bullet: "`agent_foundations.py`'s Kind bullet: `integer array` `ARRAY`, `array of objects` `ARRAY_OF_HASHES`, every other row `SCALAR`, none required". That matches "Trigger a flow"'s three array rows and its empty Required column in `rest/agent-foundations.md`, "Restart a flow"'s single path row, `create.py`'s and `gitlab_dedicated.py`'s array-of-hashes rule, and `registry.Kind`'s members. TEST-1's `NON_SCALAR_PARAMS` and IMPL-1's docstring now follow one rule. |
| B2 | B | resolved | Files: "a constant per W ID, `OP_` and its anchor in upper snake case (`OP_TRIGGER_A_FLOW`)". The 22 anchors are distinct, and no family module defines an `OP_*` today, so IMPL-9's imports are fixed before the wave. |
| C1 | C | resolved | The ledger bullet reads "one with status `enforced <the F paths of the kept keys it names>`", and Residuals ends "→ one open ledger row". The five cited DLs are ledger rows 31, 39, 43, 51, 52 and origin/main's row 72. |
| C2 | C | resolved | Files: "… become `test_nothing_is_pending`, keeping their record assertions without the kept-ID subtraction". Tests AC-1 names "`test_nothing_is_pending`'s record half in ai_coding, create, plan, verify and package". |
| C3 | C | resolved | Files: "only the REST `call` entry's refusal sentence names the class; the GraphQL entry unchanged". The GraphQL entry carries `REFUSAL_SENTENCE` (`test_the_usage_says_which_mutations_are_refused`), and the REST entry is pinned only by C's `USAGE_CALL_TEXTS` "exit 2", which the restated sentence keeps. |
| D1 | D | resolved | "… writes into an existing project, or creates an issue or another work item". |
| D2 | D | resolved | "the docstring's pending paragraph restated: each W record refused (AC-3), each read sent (AC-4)". |

## The delta's cuts

- AC-1 no longer says "(`gitlab_dedicated`'s as #63 leaves them)". No defect: the header's precondition puts #63 on the branch before the wave, so "the module docstring's rules" is #63's text. #63 design.md D8 changes that docstring's rules, and D7 changes N's member reading.
- Header: "#44 D6 (the `None` gate)" is still defined. The pointers the body uses (#40 D1 in AC-4, #63 D6 in Files) resolve to `registry._glob`/`expand` and to #63 design.md D6.
- Tasks: "TEST-n, the F of Files' n-th family module" maps one-to-one onto Files' module order (agent_foundations … verify). Each task's Validates matches its family: orbit has no W ID, and orbit and verify have the glob reads. Red states a failure for each criterion: AC-3's `registry.lookup` assertion and AC-4's exit 2.
- Security: the restated `GATED_OPERATIONS` class is comment text only, and it covers every W ID:
  - flows write code, merge requests and issues (`agent_foundations.py` docstring);
  - the merge quick action of the merge-request note (ledger row 31);
  - the pull-mirror rows of `PUT /projects/:id/` (row 72);
  - `overwrite` on the archive imports (`gitlab_dedicated.py` docstring).

  The gate still runs before `registry.lookup`. `_glob` still refuses the parts `""`, `.` and `..`. `tenant-scale#update-a-project` stays the one recorded residual.

## A — Execution blockers

None.

## B — Intent deviations

None.

## C — Clarifications / risks

None.

## D — Minor nits

None.

## Coverage

Iteration 01's table stands. The AC-1 row adds `test_nothing_is_pending`'s record half (ai_coding, create, plan, verify, package). The UB-2 row adds `test_gitlab_api_graphql_only.py` to Green, as the spec lists it.

Verdict: READY
