# Tasks review — iteration 01 — lane spec-review-agent

Reviewed: `tasks.md` (new, untracked on 1a34bd9; 14,810 B, under the 15,000 B cap) against the frozen
`requirements.md`, the approved `design.md` (D1-D9) and DL-001..DL-007.

Checked, no finding:

- Traceability. Every `Validates` id exists in `requirements.md` (AC-1.1..AC-5.2, UB-1.1..UB-3.1), and every
  criterion has a Coverage row. Each row names the TEST or VERIFY task, or the Run-line test, that design § Acceptance
  Criteria Mapping and § Correctness Properties assign to it. K, N, R, C, P, H and V sit on the Run lines their rows
  claim.
- Files. The tasks' Files are exactly D9's ten files. Within each wave they are disjoint: wave 1 is R, T, `registry.py`
  and `transport.py`; wave 2 is Q, G, `graphql_only.py`, `commands/call.py` and `registry.py`; wave 3 is G, Q,
  `gitlab_wrapper.py` and the map. The no-edit list is D9's untouched list plus P and H, which D9 does not name.
- Ordering. 2.4 reads 2.3's `OP_*` constants in the same wave. 2.4 states this, DL-007 records the wave choice, and
  it has the shape of #30's approved 2.4/2.5. Every other dependency is on an earlier wave: 2.4 on 1.3's
  `upload_variables`, and 2.5 on 1.3's `split_uploads` and 1.4's `files`.
- The red reasons hold on the tree:
  - R and T import `gitlab_api` inside each test (`gitlab_module`). So the missing `upload_variables` and
    `split_uploads` raise `AttributeError`, and `Transport.graphql(files=...)` raises `TypeError`: its keywords are
    `document` and `variables` only.
  - `refuse_gated` reads `GATED_OPERATIONS.get`, and `registry.lookup` raises for every `graphql#` ID today, so the
    call exits 2.
  - The entry docstring has no `call graphql#` line.
  - The map's `gitlab_api/` bullet holds `--file` but none of `call graphql#`, `--file NAME=PATH` and `Upload`.
  - The `call plan#retrieve-a-project-issue` entry and "Not installed here" both exist.
- The cited names exist:
  - fx: `install_socket_guard`, `FakeGitLab.script_next`, `write_config`, `load_wrapper(module_name=...)`, `run_main`.
  - K: `run_call`, `test_call_takes_no_token_option`, `test_a_gated_operation_names_its_subcommand`.
  - N: `sent_call`, which reads a multipart body with `BytesParser` through `multipart_names`.
  - C: `test_load_config_refusals`, `test_environment_token_ignored`. P: `test_standard_library_only`.
  - H: `test_any_json_value_becomes_the_attribute_value`. V: `test_every_graphql_only_capability_is_served_or_pending`.
  - Also `transport.request_body(form, json_body, files)` and `test_llm_map_within_cap`.
- `None` values in `GATED_OPERATIONS` break no existing test. N's REST loop tests membership
  (`in call.GATED_OPERATIONS`), and V's `capability_problems` collects capabilities into a set.
- Final.
  - The `verify` job of `.github/workflows/ci.yml` runs `run_checks.py --group` over the matrix
    `[lint, types, security, tests]`, and `pyproject.toml` `testpaths` holds `src/payload/test` and `test`. So F.1's
    claim about CI holds.
  - F.1 defers the real-instance run exactly as requirements "Out of scope" does.
  - F.2 to F.4 restate UB-3.1, D9 and D8 and add no scope.
  - `origin/main` has moved since the merge base (the plan and no-stage records, one K constant). None of that touches
    a D9 file or a premise of the design, so no rebase precondition is owed.
- `tasks.md` carries no line numbers, no figures that a commit invalidates, and nothing beyond the design.

### D1 — The legend credits H to the design's mapping, which does not define it
Severity: D
Location: tasks.md § preamble, the test-file legend
Defect: The legend opens "Test files as design § Acceptance Criteria Mapping" and then defines H =
`test/test_gitlab_api_call_properties.py`. The design's mapping legend ends at P; H comes from design § Testing
Strategy "Property tests" ("#41's H").
Material-because: none (wording).
Proposed-edit: replace "Test files as design § Acceptance Criteria Mapping:" with "Test files as design § Acceptance
Criteria Mapping (H: § Testing Strategy):".

CLEAN
Verdict: READY
