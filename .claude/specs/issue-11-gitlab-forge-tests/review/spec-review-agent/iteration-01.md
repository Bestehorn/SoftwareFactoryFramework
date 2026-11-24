# spec-review-agent — design review iteration 01 (whole-artefact, report-only)

Lens: internal consistency and fidelity to the worktree's code. Every symbol, record id and argv the design cites was
checked against `gitlab_wrapper.py`, `gitlab_api/` (`commands/call.py` `GATED_OPERATIONS`, `path_values`,
`check_parameters`; `registry._segment`, `KIND_ACCEPTS`; `transport.Transport._send`; the `families/` records),
`test/forge/ephemeral.py`, `test/forge/conftest.py`, `test/test_forge_suite_layout.py` and `.github/workflows/ci.yml`.
All records resolve, with the declared parameters D6 and D9 send. The reused #10 symbols exist. L's `FORGE_GUARDS`,
`STATUS_ASSIGNMENT` and `SECRET_REFERENCE` behave as D5 states. Every AC and UB is mapped.

### B1 — AC-4.1 demands exit 2 for every configuration whose project the wrapper cannot judge; D2 exits 1 for those `_load_config` refuses
Severity: B
Location: requirements.md § AC-4.1; design.md § D2 (`_run` calls the guard "right after each `_load_config()`")
Defect: AC-4.1's trigger is "IF the wrapper cannot establish that the configured project's path is an `sff-test-*`
path". That covers a missing `config/gitlab.json`, invalid JSON, an empty or `PASTE_` `project_id`, a bad token
character and a bad `token_type`. In each of those cases D2 never reaches `_refuse_unless_ephemeral`:
`_read_config`, `_refuse_incomplete`, `_refuse_token_characters` and `_token_type` raise `GitLabAPIError` first, and
`main` `_report` returns `EXIT_API_ERROR` (1) with the load message, not 2 with the marker message. GitLab differs from
#10 here: the GitHub `main` maps its token and origin refusals to `EXIT_REFUSED` as well
(`github_wrapper.py` `main`), but the GitLab `main` maps every `GitLabAPIError` to 1.
Material-because: AC-4.1 is contradicted by D2. A W case written from AC-4.1, such as the marker set and no config
file, fails against the design as written. Nothing is sent in either branch, so the defect is the contradiction, not
a leak.
Proposed-edit: in requirements.md AC-4.1, replace "IF the wrapper cannot establish that the configured project's
path is an `sff-test-*` path, THEN" with "IF `config/gitlab.json` passes `_load_config` and its `project_id` is not an
`sff-test-*` project path (`design.md` D2), THEN". Then append to AC-4.1: "A configuration `_load_config` refuses
exits 1 with nothing sent, as it does without the marker." In design.md D2, after "argv is still parsed first, so a
usage error exits 2 whatever the config", add: ", and a config `_load_config` refuses exits 1 before the guard, as
before".

### C1 — F:fixture reads the clone's token-bearing `config/gitlab.json`; nothing bounds what its failure output prints
Severity: C
Location: design.md § D6 table, `test_the_run_owns_a_private_seeded_project`; requirements.md § AC-6.3 ("no ... test
report")
Defect: the test asserts the clone config's `hostname` and `project_id`. That file also holds `token` (D8 "Writing").
The AC-6.3 checks S `test_the_token_is_written_only_to_the_clone` and G `test_the_gitlab_secret_reaches_one_step`
cover the argv, `caplog` and the `EphemeralProject` `repr`, but not an F assertion's failure text.
Proposed-edit: in the D6 row, replace "the clone's `config/gitlab.json` holds `hostname` `gitlab.com` and `project_id`
P" with "the clone's `config/gitlab.json`, read into its `hostname` and `project_id` values alone (the loaded mapping
is never compared or printed), holds `hostname` `gitlab.com` and `project_id` P".

### D1 — AC-8.6 says "the test's docstring"; D6 and G use the module docstring
Severity: D
Location: requirements.md § AC-8.6; design.md § D6 "The forms of #63 not called", Correctness Properties AC-8.6
Defect: the requirement names the test's docstring, but the design names the uncalled forms in
`forge_request_forms.py`'s module docstring, and that is the docstring G reads.
Proposed-edit: in AC-8.6, replace "be named with that reason in the test's docstring" with "be named with that reason
in the docstring of its test module".

### D2 — D6's `--header` record list leaves out one of the three records that declare a header
Severity: D
Location: design.md § D6 "The forms of #63 not called" (`--header` is declared by ...)
Defect: `openapi-only#the-nuget-symbol-file-download-endpoint` (`/groups/:id/-/packages/nuget/symbolfiles/...`,
`families/openapi_only.py`) also declares a `Location.HEADER` `Param` (`Symbolchecksum`). The sentence names only
the Ultimate record and the `-1` project record.
Proposed-edit: replace "and `openapi-only#the-nuget-symbol-file-download-endpoint-1`, "source: `openapi_v2.yaml`
only", with no documented answer" with "and the two NuGet symbol-file records,
`openapi-only#the-nuget-symbol-file-download-endpoint` (a group record, outside the ephemeral project, AC-8.7) and
`...-endpoint-1`, "source: `openapi_v2.yaml` only", with no documented answer".

## Residuals

None.

Verdict: NOT-READY (A 0, B 1, C 1, D 2) — NOT-CLEAN (0 A, 1 B)
