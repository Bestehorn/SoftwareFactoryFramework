# Standards review — issue #63, design iteration 01

Lane: standards-reviewer. Standard: `.claude/rules/` (coding-standards, tech-stack, design-principles,
file-organization, no-environment-vars, project-specific, proportionality, testing), #41 `design.md` D8, the #40 and
#43 designs, and `src/payload/scripts/gitlab_api/` at `origin/main` 252c21e.

### B1 — requirements.md § Residuals runs over the ten-line cap
Severity: B
Location: requirements.md § Residuals
Defect: The section's five bullets run to eleven lines, and `proportionality.md` § Scope freeze caps `## Residuals` at
ten. The S3 bullet's last sentence ("A `bearer` token has no documented registry login, so the registry keys refuse
it.") repeats design.md § Residuals' `token_type` `bearer` bullet, which sends that residual to a ledger row of its own.
design.md also says "The `requirements.md` Residuals stand, each a findings-ledger row", so the bearer residual becomes
two rows.
Material-because: unmaintainable-by-rule `.claude/rules/proportionality.md` ("`## Residuals` (≤ 10 lines)"), the cap
the #40 and #43 standards reviews enforced as B.
Proposed-edit: replace the S3 bullet (from "- The S3 import takes `overwrite`" through "so the registry keys refuse
it.") with:
"- The S3 import takes `overwrite`, which replaces an existing project (#38 DL-005); `call` refuses its record (UB-3),
  and the archive imports stay pending, the gated kept IDs' slice."
That leaves ten lines at 120 columns.

### C1 — design.md § Residuals lists a restatement DL-004 already made
Severity: C
Location: design.md § Residuals, second bullet
Defect: The bullet reads "Requirements restatement owed: UB-1's 'no existing assertion edited' against D9's tests, and
UB-3's `GATED_OPERATIONS` clause and the S3 Residual against D6's gate." DL-004 has already made that restatement.
UB-1 now admits an assertion "that pins what this change retires … restated to the new state". UB-3 reads "but for one
`None` entry for the S3 import". The S3 Residual reads "its record is refused by `call` (UB-3)". So the bullet names
no open residual.
Proposed-edit: delete the bullet.

### C2 — the design does not say whether #41 D8's file table binds it
Severity: C
Location: design.md § D12
Defect: #41 D8's "A slice" table, written for #35–#40 and #42–#44, puts three things under "never": `gitlab_wrapper.py`,
`commands/*` other than `GATED_OPERATIONS`, and N beyond "N's path reading". #40 (D2, D3, D5) and #43 (D3, D4) record
each reach past that row by name and reason. #63 is not one of the listed slices, but D1, D5, D7 and D11 edit exactly
those files: `--endpoint`, `--header`, `path_values`, the entry script's docstring, and N's `Section.headers`,
`header_problems` and `record_call`. Neither D7 nor D12 says whether the row governs this change.
Proposed-edit: open D12 with "#41 D8's slice table names #35–#40 and #42–#44. This change is the request-form work its
exceptions row leaves to a later change ('a request form that part 1 does not build'), and this table is the change's
own. Its edits beyond that row are `commands/call.py` past `GATED_OPERATIONS` (D1 to D6), the entry script's docstring
(D11) and N past its path reading (D7). Every other row of #41 D8 still holds."

### C3 — the new module has no paired test module
Severity: C
Location: design.md § D10; § Correctness Properties AC-5.2 (R `test_send_fetches_the_registry_token_before_the_registry`);
§ Acceptance Criteria Mapping row AC-5.2
Defect: `testing.md` item 3 pairs each test module with the source module it covers, and each core `gitlab_api` module
has its own (`test_gitlab_api_registry.py`, `_transport.py`, `_call.py`, `_graphql_only.py`, one per family). D4's
steps 1 and 2 live in the new `gitlab_api/container_registry.py`: the login chosen by token type, and the origin read
from `container_registry_image_prefix`. Their example is in R and F:package, and no test module covers
`container_registry.py`.
Proposed-edit: in D10 and the mapping legend add "G = `src/payload/test/test_gitlab_api_container_registry.py`". Move
the job-token case of R `test_send_fetches_the_registry_token_before_the_registry` to G as
`test_a_job_token_logs_in_as_gitlab_ci_token`. R keeps the "sent without `project`" case, which belongs to
`registry.send`. Update the AC-5.2 mapping row to match.

### C4 — the header-value check is specified twice
Severity: C
Location: design.md § D5 "`encode`." and "The transport."
Defect: `registry.encode` and `transport._build_request` each refuse a header value holding CR, LF or NUL with
`ValueError`. D5 does not say they share one function, so the rule could be coded twice, against `coding-standards.md`
rule 10 and `design-principles.md` rule 2.
Proposed-edit: in D5 "`encode`.", replace "A value holding CR, LF or NUL raises `ValueError` (RFC 9110 §5.5)." with "A
value holding CR, LF or NUL raises `ValueError` (RFC 9110 §5.5) through `registry.check_header_value(*, name, value)`,
which `_build_request` also calls (`transport.py` already imports `gitlab_api.registry`)."

### C5 — a sentence of the `call` docstring becomes false for a positional name
Severity: C
Location: design.md § D11 (the `commands/call.py` docstring); § D2 "`call`."
Defect: The module docstring of `commands/call.py` says "A path name, or an attribute given by ``-f`` or ``-F``, given
twice keeps its last value". Under D2, `path_values` collects every `--path` value of a positional name as a list.
D11 lists the docstring's grammar, its option bullets and its refusals, but not that paragraph. The sentence would stay
stale in a file this change edits (`post-activity.md` item 4; precedent: #44's standards C1).
Proposed-edit: append to D11's first paragraph: "The sentence 'A path name … given twice keeps its last value' gains
'but a name of the record's `positional_names`, whose values fill its places in command-line order (D2)'."

### D1 — a key count in AC-1.1
Severity: D
Location: requirements.md § Requirement 1, AC-1.1, the F1 item
Defect: "the 37 keys issue #63 counts under F1" carries a count (`proportionality.md` "Specs state behaviour, not
measurements"). The issue's list identifies the keys without it. #44's standards review graded the same as D1.
Proposed-edit: "the keys issue #63 lists under F1".

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
