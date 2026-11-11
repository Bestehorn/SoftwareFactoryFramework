# Change — issue #15: GitLab wrapper rewrite, part 2: the kept keys

Tier: S (DL-001). Kind: FEATURE. Follows #41's and #63's designs and #44 D6 (the `None` gate). In `src/payload/test/`:
F = `test_gitlab_api_<module>.py`, K = `test_gitlab_api_call.py`, C = `test_gitlab_wrapper_compat.py`. In
`test/`: N = `test_gitlab_wrapper_contract.py`, V = `test_gitlab_wrapper_coverage.py`, P =
`test_gitlab_api_properties.py`. Precondition: #43 (PR #65) and #63 landed; this branch rebased onto them.

## User Prompts

1. User, 2026-11-10 (`/auto-work`): "Work this project's open-issue backlog AUTONOMOUSLY, end to end, following
   `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: `prompt.md` from #15's body and the slices' decision logs; no interview (`qa_log.md`).

## Ask

Issue #15 AC-3: the pending list SHALL be empty (completing #11 AC-1). What remains: the kept keys.

## Acceptance criteria

The kept keys, by their index row's Reference ID, per module of `gitlab_api/families/`; W marks a writer:

- `agent_foundations`: W `agent-foundations#trigger-a-flow`, W `#restart-a-flow`.
- `ai_coding`: W `ai-coding#rebase-a-merge-request`.
- `create`, each W: `create#create-repository-branch`, `#create-a-commit`, `#cherry-pick-a-commit`, `#revert-a-commit`,
  `#add-changelog-data-to-file`, `#create-a-file-in-a-repository`, `#update-a-file-in-a-repository`,
  `#delete-a-file-in-a-repository`, `#update-a-submodule-reference`, `#apply-a-suggestion`,
  `#apply-multiple-suggestions`, `#start-the-pull-mirroring-process-for-a-project`.
- `gitlab_dedicated`, each W: `gitlab-dedicated#import-a-project-from-a-local-archive`,
  `#import-a-project-from-a-remote-archive`, `#import-project-resources`.
- `orbit`: `orbit#retrieve-a-deployed-skill-file`.
- `package`: W `package#change-the-visibility-of-the-container-registry`.
- `plan`: W `plan#clone-an-issue`, W `#create-a-merge-request-note`.
- `verify`: `verify#download-a-single-artifact-file-by-job-id`, `#download-a-single-artifact-file-by-reference-name`;
  W `#add-a-merge-request-to-a-merge-train`.

- AC-1: Each kept key SHALL have one `RestOperation` in its module's `OPERATIONS`, under a comment naming its section,
  with its index row's method and path, its `rest/<stage>.md` section's `Param` names, locations, `Kind`s and
  `required` by the module docstring's rules as N reads them, and `Paging.NONE`.
- AC-2: Every GitLab family module's `PENDING` SHALL be empty, and V SHALL pass.
- AC-3: `commands/call.py` `GATED_OPERATIONS` SHALL map each W ID to `None`. WHEN `call` is given a W ID with a value
  for each path parameter and required `Param`, THEN it SHALL exit 2 before any request, logging the ID and that no
  subcommand sends it.
- AC-4: WHEN `call` is given a non-W kept ID with a value for each path parameter and required `Param`, its `*name`
  value holding `/` (`orbit#retrieve-a-deployed-skill-file --path name=<n> --path path=references/usage.md`), THEN it
  SHALL exit 0 and send one `GET` whose path keeps each `/` of that value, each part one encoded segment (#40 D1).

## Unchanged behaviour

- UB-1: The existing records and the compatibility subcommands SHALL CONTINUE TO behave as they do.
- UB-2: `call` SHALL CONTINUE TO refuse with exit 2 and no request every other `GATED_OPERATIONS` ID with its message,
  and an ID no record declares.
- UB-3: Credentials SHALL CONTINUE TO come only from `config/gitlab.json`, imports only from the 3.9 standard library.
- UB-4: `github_wrapper.py`, `github_api/` and their tests SHALL CONTINUE TO be untouched, `test_wrapper_delivery.py`
  to pass.

## Files

- `src/payload/scripts/gitlab_api/families/agent_foundations.py`, `ai_coding.py`, `create.py`, `gitlab_dedicated.py`,
  `orbit.py`, `package.py`, `plan.py`, `verify.py`: AC-1's records; a constant per W ID, `OP_` and its anchor in upper
  snake case (`OP_TRIGGER_A_FLOW`), #63 D6's form; `PENDING` empty; the docstring's pending paragraph restated: each W
  record refused (AC-3), each read sent (AC-4); `agent_foundations.py`'s Kind bullet: `integer array` `ARRAY`,
  `array of objects` `ARRAY_OF_HASHES`, every other row `SCALAR`, none required.
- `gitlab_api/commands/call.py`: AC-3's entries; the `GATED_OPERATIONS` comment and the module docstring's `None`
  sentence name the class, not each ID: a record that writes a branch or a merge request's source branch, merges,
  writes into an existing project, or creates an issue or another work item. `gitlab_wrapper.py`: only the REST
  `call` entry's refusal sentence names the class; the GraphQL entry unchanged.
- F, the eight: per Tests; their pending-state tests restated: the kept-key literals (`KEPT_PENDING*`, `PENDING_KEYS`,
  package's `KEPT`) go; the record tables (`RECORD_ENDPOINTS`, `INDEX_REFERENCES`, `INDEX_ROWS`, `OPERATION_IDS`,
  typed and required) gain AC-1's records; `test_only_the_kept_keys_are_pending` (seven) and package's
  `test_nothing_is_pending_but_the_kept_keys` (with its `/projects/:id/` clause) become `test_nothing_is_pending`,
  keeping their record assertions without the kept-ID subtraction.
- K: `OP_PENDING_ONLY` and the `only-on-a-pending-list` row of `test_an_unknown_operation_is_refused` removed.
- `docs/findings-ledger.md`: per open row naming a kept key (#35 DL-002, #37 DL-003, #38 DL-002/DL-005, #39 DL-003,
  #43 DL-006), one with status `enforced <the F paths of the kept keys it names>`.

No other file or doc.

## Tests

Example tests. F's IDs, keys, paths and argv are literals from the index and sections, never read from the records or
`GATED_OPERATIONS`.

- AC-1 — N `test_every_record_matches_its_reference_section`; V `test_every_declared_key_is_in_its_family`; F's
  record-table tests (`test_every_reference_has_its_record`, `test_nothing_is_pending`'s record half in ai_coding,
  create, plan, verify and package, `test_every_param_is_typed_as_its_row`, `test_only_the_list_records_are_paged`,
  plan's `test_the_typed_attributes_are_the_sections` and `test_the_required_attributes_are_the_sections`).
- AC-2 — F `test_nothing_is_pending` (the eight); V `test_every_index_row_is_mapped_or_pending`.
- AC-3 — F `test_a_writing_record_is_refused`, a case per W ID: `registry.lookup` returns the record; exit 2, no
  request at the fake host, an ERROR record naming the ID and "no subcommand sends it".
- AC-4 — F `test_a_glob_record_is_sent_with_its_slashes` (orbit, verify): exit 0, one `GET` at the expanded URL.
  N `test_every_record_is_sent_as_its_section_documents` sends all three, skipping the W IDs.
- UB-1 — C; F's tests of the existing records.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`,
  `test_the_s3_import_is_refused`; `test_gitlab_api_graphql_only.py` `test_a_refused_mutation_sends_nothing`.
- UB-3 — C `test_load_config_refusals`, `test_environment_token_ignored`; P `test_standard_library_only`.
- UB-4 — `test_wrapper_delivery.py`; the PR diff names no GitHub file.
- E2E — no deployed system; the real-instance run is #11's (`sff-test-*`). F and N run `call` through `main` to the
  API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave, after the precondition)

- TEST-1 to TEST-8 — Files: TEST-n, the F of Files' n-th family module (`plan`'s with K). Validates: AC-1, AC-2;
  AC-3 but `orbit`; AC-4 `orbit`, `verify`; UB-2 `plan`.
- Red: the eight F; `test_nothing_is_pending` fails, AC-3's lookups find no record, AC-4's calls exit 2.
- IMPL-1 to IMPL-8 — Files: the family module of TEST-n. Validates: AC-1, AC-2.
- IMPL-9 — Files: `commands/call.py`, `gitlab_wrapper.py`. Validates: AC-3, UB-2.
- Green: F (the eight), K, N, V, C, P, `test_gitlab_api_graphql_only.py`. The wave's commit carries the ledger rows.

## Residuals

- `tenant-scale#update-a-project` (`PUT /projects/:id`, #43 DL-006) has the same mirror rows and stays callable:
  gating an existing record is not this ask → one open ledger row.
