# Standards review — iteration 02 (delta) — issue #13 (tier M)

Iteration-01 fix sites: X1 closes B1 and C1 (precedent: `test/test_toolchain_manifest.py` already reads
`sys.stdlib_module_names`). C2 is restated, and its new text is C1 below. C3 to C6 and D1 are applied. X3's cited parts
(`setup-claude.txt` Part 5.3, `setup-kiro.txt` Part 6.2) and both "Shipped Python" lists exist, and
`test/test_layout.py` `resolves` accepts the directory token through `Path.exists`.

### B1 — The registry tests sit in the transport test module, unlike #17 and testing.md rule 3
Severity: B
Location: design.md § D2 Layout (`src/payload/test/`); § Testing Strategy, "Transport and registry"; § Acceptance
Criteria Mapping, AC-1.1, AC-2.2, AC-2.3
Defect: `test_gitlab_api_transport.py` is declared to cover both `transport.py` and `registry.py`, and the registry
tests (`test_call_refuses_an_undeclared_value`, `test_lookup_refuses_unknown_and_duplicate_ids`,
`test_project_path_is_encoded`, `test_empty_and_dot_segments_are_refused`, `test_array_of_hashes_pairs`) are mapped to
T. `testing.md` rule 3 says "A test module covers its source module", and the existing shipped suites follow it
(`test_merge_steward.py`, `test_run_checks.py`, `test_reap_agent_temp.py`). #17, whose test-module naming X2 adopts,
splits the same pair (`test_github_api_transport.py`, `test_github_api_registry.py`). No row of "Differences from #17"
records the merge, although the Overview says every remaining difference is one.
Material-because: unmaintainable-by-rule testing.md. `registry.py` gets no test module of its own, and the layout
differs from #17 without the row X2 requires.
Proposed-edit: in D2 replace `test_gitlab_api_transport.py   transport.py, registry.py` with the two lines
`test_gitlab_api_transport.py   transport.py` and `test_gitlab_api_registry.py    registry.py`. In Testing Strategy
replace "**Transport and registry** — `src/payload/test/test_gitlab_api_transport.py` puts" with "**Transport and
registry** — `src/payload/test/test_gitlab_api_transport.py` (`transport.py`) and
`src/payload/test/test_gitlab_api_registry.py` (`registry.py`) put". In the Acceptance Criteria Mapping add
"R = `src/payload/test/test_gitlab_api_registry.py`", and move these tests from T to R: AC-1.1's two tests, AC-2.2's
`test_project_path_is_encoded` and `test_empty_and_dot_segments_are_refused`, and AC-2.3's `test_array_of_hashes_pairs`.

### C1 — "The package module that reads it" names no owner for a response key two command modules read
Severity: C
Location: design.md § Existing patterns followed
Defect: The ST-C2 restatement puts each `FIELD_*` constant in "the package module that reads it". More than one command
module reads some response keys. `id` is read in `commands/pipeline.py` (the pipeline and job ids) and in
`commands/issue.py` (the `GET /user` and `GET /users` ids). For such a key the sentence still allows two definitions,
which is the gap C2 was meant to close.
Proposed-edit: replace "each defined once in the package module that reads it (the config keys in `transport.py`)"
with "each defined once: the config keys in `transport.py`, a response key in the one module that reads it, and a key
more than one command module reads in `commands/_common.py`".

### C2 — The data flow writes a call site with positional arguments
Severity: C
Location: design.md § Data flow; § Existing patterns followed ("keyword-only parameters")
Defect: The data flow shows `registry.call(transport, "plan#retrieve-a-project-issue", …)`, a positional call, but
`coding-standards.md` item 4 requires named parameters at every call site. "Existing patterns followed" claims
keyword-only parameters, yet D4, D5 and D8 give positional signatures (`call(transport, operation_id, *, values=None)`,
`expand(operation, values)`, `_send(method, url, data, headers)`, `coverage_gaps(rows, mapped, pending)`). The
skeleton itself is mixed: `pipeline_wait(*, …)` is keyword-only, `steward_delegate(verb, args, token, host)` is not.
Proposed-edit: in Data flow write `registry.call(transport=…, operation_id="plan#retrieve-a-project-issue", …)`. In
"Existing patterns followed" replace "keyword-only parameters" with "named arguments at every call site
(`coding-standards.md` item 4)".

### C3 — Text the edited prompt parts keep becomes untrue for GitLab
Severity: C
Location: design.md § D2, "Install path"
Defect: The parts X3 edits keep sentences that this change makes untrue for GitLab. `setup-claude.txt` Part 5.3 says
"The wrapper templates are skeletons; implement the subcommands the project's agents invoke". `setup-kiro.txt` Part 6.2
says "The template wrapper scripts are skeletons. The agent should extend them". The setup-kiro project tree lists
`gitlab_wrapper.py # if GitLab` under `scripts/` with no `gitlab_api/`. After this change the GitLab wrapper serves
every subcommand of both prompts' required GitLab lists (D6, UB-1). `post-activity.md` item 4 asks for such deviations
between docs and implementation to be flagged.
Proposed-edit: append to "Install path": "In the same parts, the 'skeletons' sentence names the GitHub wrapper only,
and the setup-kiro project tree lists `gitlab_api/` under `scripts/`." If the conductor judges this to be scope, record
it under Residuals instead.

NOT-CLEAN (0 A, 1 B)
