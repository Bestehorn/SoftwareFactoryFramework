# Review — issue #15 `change.md`, iteration 01 (tier S, combined: all lenses)

Held: the kept set is exactly origin/main 6beeb77's `PENDING` minus #63 D8 (25 keys, 2+1+12+3+1+1+2+3); every ID is its
index row's Reference and every section exists; each W is backed by its family docstring and #35 DL-002, #37 DL-003,
#38 DL-005, #39 DL-003 or #43 DL-006; the `None` form is `GATED_OPERATIONS`' today, checked by `refuse_gated` before
`registry.lookup`; `_glob` sends the three reads; AC-1 to AC-4 are EARS and can fail.

## A — Execution blockers

None.

## B — Intent deviations

### B1 — agent-foundations' Kind rule types "Trigger a flow"'s arrays SCALAR
Severity: B
Location: change.md § AC-1; § Files (family modules)
Defect: AC-1 takes each `Kind` "by the module docstring's rules", and `families/agent_foundations.py`'s is "every row
is `Kind.SCALAR`", but "Trigger a flow" has `additional_context` (`array of objects`), `agent_privileges` and
`pre_approved_agent_privileges` (`integer array`); Files restates only the pending paragraph, so IMPL-1 follows the
docstring while TEST-1, transcribing F's `NON_SCALAR_PARAMS` from the section, types them as arrays.
Material-because: AC-1 — the parallel authors take opposite Kinds, so `test_every_param_is_typed_as_its_row` is red at
Green, or the docstring is left false.
Proposed-edit: Files, family bullet, append: "; `agent_foundations.py`'s Kind bullet: `integer array` is `ARRAY`,
`array of objects` `ARRAY_OF_HASHES`, every other row `SCALAR`, none required".

### B2 — IMPL-9 imports constants whose names no task fixes
Severity: B
Location: change.md § Files ("an `OP_*` constant per W ID"); § Tasks IMPL-9
Defect: IMPL-9's `GATED_OPERATIONS` entries name the 22 `<family>.OP_*` constants that IMPL-1 to IMPL-8 define in the
same wave, dispatched together, and the spec names none (#63 D6 named `OP_IMPORT_FROM_S3`); a mismatch raises when
`gitlab_wrapper.py` `command_modules` imports `commands/call.py`, which it does for every subcommand.
Material-because: unmaintainable-by-rule `parallel-by-default.md` (a wave's tasks depend only on earlier waves); a
regression of UB-1 when the names differ.
Proposed-edit: replace "an `OP_*` constant per W ID (#63 D6's `OP_IMPORT_FROM_S3` form)" with "a constant per W ID,
`OP_` and its anchor in upper snake case (`OP_TRIGGER_A_FLOW`), #63 D6's form".

## C — Clarifications / risks

### C1 — The ledger pass closes the row the residual points at
Severity: C
Location: change.md § Files (`docs/findings-ledger.md`); § Residuals
Defect: #43 DL-006's row (`PUT /projects/:id/`, Why "mapped and gated with tenant-scale's Update a project") names a
kept key, so Files marks it `enforced`, while Residuals keeps `tenant-scale#update-a-project` callable citing that row;
#38 DL-002/DL-005's two rows each span several families, so "its F path" names no one file.
Material-because: risk — the residual is left with no open ledger row (`issue-filing-discipline.md`).
Proposed-edit: the Residuals line ends "→ one open ledger row"; the ledger bullet reads "one with status
`enforced <the F paths of the kept keys it names>`".

### C2 — AC-1's F record assertion sits in the renamed test in five files
Severity: C
Location: change.md § Tests AC-1; § Files (F)
Defect: `test_every_reference_has_its_record` exists only in agent_foundations, gitlab_dedicated and orbit F; in
ai_coding, create, plan, verify and package F, "OPERATIONS declares each Reference once at its row's key" is the second
half of the test that becomes `test_nothing_is_pending`, and `INDEX_ROWS`/`INDEX_REFERENCES` already hold the kept IDs
(the kept literal is subtracted). A #14-form `test_nothing_is_pending`, `PENDING` only, drops it.
Material-because: risk — AC-1's "one `RestOperation` … with its index row's method and path" then rests on N and V.
Proposed-edit: "… become `test_nothing_is_pending`, keeping their record assertions without the kept-ID subtraction";
Tests AC-1 gains "`test_nothing_is_pending`'s record half (ai_coding, create, plan, verify, package)".

### C3 — "the `call` usage" leaves open which entry
Severity: C
Location: change.md § Files (`gitlab_wrapper.py`)
Defect: The docstring has the REST `call plan#retrieve-a-project-issue` entry, which names the refused IDs, and the
GraphQL `call graphql#…` entry, whose refusal sentence `test_gitlab_api_graphql_only.py`
`test_the_usage_says_which_mutations_are_refused` pins verbatim.
Material-because: risk — restating the GraphQL sentence to the class turns that test red.
Proposed-edit: "`gitlab_wrapper.py`: the REST `call` entry's refusal sentence names the class too; the GraphQL entry is
unchanged."

## D — Minor nits

### D1 — The class drops "another work item"
Severity: D
Location: change.md § Files (`commands/call.py`)
Defect: Today's comment covers `graphql#workItemCreate` as creating "an issue or another work item".
Proposed-edit: "… writes into an existing project, or creates an issue or another work item".

### D2 — "restated as AC-3's refusal" for the reads
Severity: D
Location: change.md § Files (family modules)
Defect: `orbit.py` has no W ID, and `verify.py`'s paragraph also covers its two downloads.
Proposed-edit: "the docstring's pending paragraph restated: each W record refused (AC-3), each read sent (AC-4)".

## The author's assumptions

1. Verify's downloads as reads: correct (`GET`; #37 DL-002, downloads printed byte for byte).
2. Archive imports depend on #63's N reading: harmless but not needed — base N's `parent_of` already reads the
   two-level rows as members of the `override_params` hash row both archive sections have; the precondition covers it.
3. `test_a_writing_record_is_refused`: fits; the class is wider than branch writing.
4. `OP_*` constants: the right form (`graphql_only`, #63 D6), but unnamed — B2.
5. `gitlab_wrapper.py` usage and ledger rows in Files: needed (the REST entry lists the refused IDs; #14's ledger form)
   — C1, C3.
6. K's row removed: sound; it would keep passing under a false label (the gate's refusal names the ID, exit 2, nothing
   sent), as #14's iteration-01 C1 found; `not-in-the-reference` keeps UB-2.
7. Task ranges: unambiguous (one F, one family per number); IMPL-9's same-wave dependency is B2.

## Coverage table

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | N `test_every_record_matches_its_reference_section`; V `test_every_declared_key_is_in_its_family`; F record, typed, required and paging tables | a record missing, mis-keyed or mistyped; Red: no record |
| AC-2 | F `test_nothing_is_pending` (eight); V `test_every_index_row_is_mapped_or_pending` | a key left on `PENDING`; Red: each of the eight holds its kept keys |
| AC-3 | F `test_a_writing_record_is_refused` (seven families, 22 IDs) | Red: `lookup` raises; no `None` entry: a request is sent; a subcommand is named |
| AC-4 | F `test_a_glob_record_is_sent_with_its_slashes` (orbit, verify); N send test | Red: exit 2, unknown ID; a `/` encoded; a second request |
| UB-1 | C; F's existing record tests | a compatibility case or existing record changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`, `test_the_s3_import_is_refused`; `test_a_refused_mutation_sends_nothing` | a gate entry or the lookup refusal is lost |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only` | a non-file credential or a third-party import |
| UB-4 | `test_wrapper_delivery.py`; the PR diff | a GitHub file in the diff |
| E2E | none deployed; F and N through `main` in `ci.yml` job `verify`, leg `tests` | — |

Security: the gate matches the ID before `registry.lookup`, so no option reaches a W record; no W key is another
Reference's endpoint (#63 D8) and `lookup` refuses two records of one key; `_glob` refuses `.` and `..` parts;
`tenant-scale#update-a-project`, the one equivalent callable record, is the residual.

Verdict: NOT-READY
