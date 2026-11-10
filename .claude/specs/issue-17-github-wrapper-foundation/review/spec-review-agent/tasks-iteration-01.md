# Tasks review — iteration 01 — spec-review-agent (issue #17, tier M)

### C1 — Wave 5's run omits the existing tests that read the files 5.7 edits
Severity: C
Location: tasks.md § Wave 5 (`Run:` line), task 5.7
Defect: 5.7 edits `prompts/setup-claude.txt`, `prompts/setup-kiro.txt` and `docs/forLLMConsumption.md` ("under its
cap"), but the wave's run includes none of the tests that read those files: `test/test_layout.py` (every framework
path a live file names exists), `test/test_instruction_corpus_budget.py` (the map's cap), `test/test_toolchain_manifest.py`
(`test_the_map_names_the_manifest_command_of_the_promotion`), `test/test_setup_prompts_gitignore.py`,
`test/test_agent_rule_references.py`, `test/test_no_ai_attribution_rule.py`, `test/test_post_activity_prompts.py`.
Material-because: regression — a break in any of them passes the wave's green capture and first shows in CI
(`post-activity.md` item 1, the affected tests).
Proposed-edit: append those seven paths to Wave 5's `Run:` line.

### C2 — The issues group's golden values are first checked against the fork one wave after they drive the code
Severity: C
Location: tasks.md § Wave 4 task 4.1; § Wave 5 task 5.2
Defect: 4.1's `CASES` rows for the issues subcommands are what 4.3's handlers are built to, but
`test_the_fork_produces_the_golden_case` — the only check that a golden value is the fork's output — is written in
5.2, so a wrong golden surfaces at wave 5's red run, where no wave-5 task owns `commands/issues.py`.
Material-because: regression risk to UB-1.1 for the issues group.
Proposed-edit: in Wave 4 add, after 4.1, "4.2 TEST: P — `test_the_fork_produces_the_golden_case` over the `CASES`
rows present (design § Testing Strategy) — Files: test/test_github_wrapper_fork_parity.py — Validates: UB-1.1"
(renumber 4.2/4.3 to 4.3/4.4), add `test/test_github_wrapper_fork_parity.py` to Wave 4's `Run:` line, and restate 5.2
as "P — adds `test_the_parsers_match_option_by_option` …" keeping its text for that test.

### D1 — F.1 is labelled "Not applicable" for a change that alters runtime behaviour
Severity: D
Location: tasks.md § Final F.1
Defect: `always-test-e2e.md` reserves "E2E: not applicable" for a change that alters no runtime behaviour; design
§ Testing Strategy "E2E:" says the check stops at the API boundary until #10's fixture exists, which is what F.1's
body states.
Proposed-edit: replace "E2E: Not applicable in this change — the real-forge check runs on #10's ephemeral
`sff-test-*` fixture, which does not exist yet" with "E2E: stops at the API boundary until #10's ephemeral
`sff-test-*` fixture exists".

## Flagged exceptions

- 3.5 spanning more than three files: accepted. The index has 48 families; 3.5 writes `graphql_only.py` and the 41
  modules 3.2–3.4 do not own, which D2's family-module contract requires. They are one behaviour (pending data, no
  logic), disjoint from 3.2–3.4 by the stated ownership, and 3.1's
  `test_one_module_per_family_holding_only_its_own_ids` and `test_every_operation_is_covered_or_pending` catch any
  omission or misplacement. Splitting them into tasks of up to three files gives 34 tasks, past the M ceiling of 30
  (21 now).
- The map edit folded into 5.7: accepted. 5.7 stays at three files; the map update is `post-activity.md` item 3's
  obligation and adds no criterion or mechanism; `docs/forLLMConsumption.md` is not in `config/toolchain.json`, so it
  is a product file.

Checked and clean: waves 1–5 own disjoint files and depend only on earlier waves; TEST precedes IMPL in every wave;
every AC-1.1..AC-5.3 and UB-1.1..UB-3.2 is in a TEST task's `Validates:` (UB-3.1 also F.2); every test name matches
design § Acceptance Criteria Mapping; the 23 record IDs of 3.2–3.4 equal D5's table and exist in
`operations-index.md`; every D2 file has an owning task; `tasks.md` is under the 15,000-byte cap.

CLEAN
