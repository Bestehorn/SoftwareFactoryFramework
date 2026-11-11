# Design review — iteration 01 — lane spec-review-agent (completeness, consistency, traceability)

Reviewed: `requirements.md`, `design.md`, `decisions/decision-log.md` (DL-001..DL-005), `prompt.md`, issue #44 body,
against `gitlab_api/` (registry, transport, commands/call.py, graphql_only), the K/N/V/C/P suites and
`docs/api-reference/gitlab/graphql/`. Every document of D1 was checked field by field against `queries.md`,
`mutations-*.md`, `objects-*.md` and `interfaces.md`: each field, argument, input field, payload field and variable type
exists as written. No existing K, N, C or V case depends on what this design changes.

### B1 — AC-5.2's test cannot fail on the "a file included" half
Severity: B
Location: design.md § Correctness Properties, AC-5.2 (Q `test_the_map_names_the_graphql_call`)
Defect: The oracle checks that `docs/forLLMConsumption.md` holds `call graphql#` and `--file`. The map's existing
`call plan#retrieve-a-project-issue` sentence in the `gitlab_api/` bullet already holds `--file` (#41 D7). So that half
passes before this change, and it still passes if D8's file clause is left out.
Material-because: AC-5.2 ("SHALL name how to call a GraphQL-only capability, a file included") is not tested for the
file.
Proposed-edit: replace "`docs/forLLMConsumption.md` holds `call graphql#` and `--file`" with
"`docs/forLLMConsumption.md` holds `call graphql#` and `--file NAME=PATH` (D8's text; the map names `--file` alone
already)".

### C1 — What `call_values` does with a `--file` name that is not an `Upload` variable
Severity: C
Location: design.md § D4 "`commands/call.py`"; § D3 steps 3–4
Defect: `prepare_call` runs `call_values` (step 3) before `check_parameters` (step 4). D4 says `call_values` puts "each
`--file` variable" in the values, as a list or as one `Path` depending on its type, but does not say what happens to a
name `upload_variables` lacks. UB-1.2's example is exactly such a call (`--file projectPath=…`). If the list-or-single
decision indexes the `upload_variables` dict, it raises `KeyError`. `call_operation` catches only `ValueError`, so that
call would crash instead of exiting 2. The named G test would catch it, but the text leaves the implementer to guess.
Proposed-edit: "`call_values` puts each `--file` value into the values: a list of `pathlib.Path` for a name
`upload_variables` maps to `True`, else the one `Path` — a name outside `upload_variables` included, which step 4
then refuses before anything is sent."

### C2 — D7's closing claim about #11 contradicts the Residuals' deferral
Severity: C
Location: design.md § D7 "What #11's test project cannot exercise" (its last sentence); § Residuals "What Q and #11
leave"
Defect: D7 says every record outside its table "is proven … by #11's real-instance run once its fixture exists". The
Residuals say #11's fixture settles whether it can supply what some records need: a CI configuration for
`graphql#pipelineCreate`, and with it the `requestId` that `graphql#Project.ciPipelineCreationRequest` reads, and Git
LFS for `graphql#designManagementUpload`. So AC-1.1's answer makes a claim about #11 that the design cannot back
(`no-guessing.md`).
Proposed-edit: replace the sentence with "Every other record is proven by Q and G in CI's `tests` leg; #11's
real-instance run proves each one its fixture provides for (Residuals \"What Q and #11 leave\": a CI configuration for
`graphql#pipelineCreate` and `graphql#Project.ciPipelineCreationRequest`, Git LFS for
`graphql#designManagementUpload`)."

### D1 — The environment-text scan is credited to the wrong criterion
Severity: D
Location: design.md § D8 "Module docstrings", last bullet
Defect: "(UB-2.1's scan reads docstrings)": the scan for `os.environ`/`getenv` text is P
`test_standard_library_only`, which the mapping assigns to UB-2.2. UB-2.1's tests are C and K.
Proposed-edit: "(P `test_standard_library_only`, UB-2.2, reads the docstrings too)".

Traceability: every AC-1.1..AC-5.2 and UB-1.1..UB-3.1 has a component and a named test in the mapping, and each named
existing test exists in the tree. The issue's three open questions are answered: D1/DL-003 (granularity), D4/DL-004
(multipart in `Transport.graphql`), and D7 (row 4's instance-wide list). Refusing row 7 diverges from the issue's AC-3
"(rows 5, 7)". That is the frozen requirements' choice (AC-4.1, Residuals, DL-002), not the design's.

NOT-CLEAN (0 A, 1 B)
Verdict: NOT-READY
