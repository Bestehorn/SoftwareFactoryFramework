# Standards review — iteration 01 — issue-17-github-wrapper-foundation (design)

### B1 — The rate-limit and GraphQL exception names hide their base class
Severity: B
Location: design.md § D3 "Exceptions" (also § D3 "Failures", `graphql(...)`; § Correctness Properties AC-3.3, AC-4.3;
§ Acceptance Criteria Mapping AC-3.3, AC-4.3)
Defect: `RateLimitError` and `GraphQLResponseError` subclass `GitHubAPIError`, but neither name shows that base, while
the fork names its subclass of the same base `GitHubRedirectRefusedError` (`scripts/github_wrapper.py`), and the AC-3.3
property has to add "(a `GitHubAPIError`)" to say what the name does not.
Material-because: unmaintainable-by-rule coding-standards.md item 9 ("The inheritance hierarchy must be visible from
class names").
Proposed-edit: in D3 "Exceptions" replace "with `RateLimitError` and `GraphQLResponseError` as subclasses" with "with
`GitHubRateLimitError` and `GitHubGraphQLResponseError` as subclasses, named as the fork names
`GitHubRedirectRefusedError`", and use the two new names in D3 "Failures", D3 `graphql(...)`, Correctness Properties
AC-3.3 and AC-4.3 (dropping "(a `GitHubAPIError`)"), and the Mapping rows AC-3.3 and AC-4.3.

### B2 — The break of the shipped setup copy step is not flagged
Severity: B
Location: design.md § Overview ("Nothing is installed or promoted"), § D6 "Removed", § Residuals (first bullet)
Defect: `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` install the wrapper by copying
`src/payload/scripts/github_wrapper.py` alone, and Part 5.3 sends the implementer to "the expanded docstrings in
`src/payload/scripts/github_wrapper.py`" for the endpoints and the own-PR approval caveat; after D6 the entry script
imports `github_api` at load and that comment block is gone, so a project set up from the first release that contains
this change gets a wrapper whose every call fails with an import error (and, under the steward, an installed
`test/test_wrapper_delivery.py` that fails in `load`), plus a pointer to text that no longer exists. The design records
the copy step only as this repository's promotion work and says "Nothing is installed", which holds for this
repository's toolchain, not for installs of the product.
Material-because: regression — unmaintainable-by-rule design-principles.md item 3 ("If unavoidable, flag
explicitly"), with post-activity.md item 4 (flag deviations between docs and implementation).
Proposed-edit: in § Overview replace "Nothing is installed or promoted: sessions keep running the fork
(`config/toolchain.json` `deviations`)." with "Nothing is promoted here: this repository's sessions keep running the
fork (`config/toolchain.json` `deviations`). **Breaking change, flagged (design-principles.md item 3):**
`prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` copy only `github_wrapper.py`, and Part 5.3 points to
the instruction block D6 removes; a project set up from a release that contains this change but not the copy-step
update gets an entry script whose `import github_api` fails (Residuals)." In § Residuals, first bullet, replace
"Promotion must carry" with "The setup prompts' copy step (product, `prompts/`) and this repository's promotion must
carry".

### C1 — No field constants named for the transport, and no shared home for the commands' fields
Severity: C
Location: design.md § D3 "Constants"; § D2 layout (`commands/_common.py`); § D6 "Removed"
Defect: D3's constant list names none of the JSON fields the transport reads and writes (`query`, `variables`, `after`,
`data`, `errors`, `message`, `pageInfo`, `endCursor`, `hasNextPage`, `nodes`), D6 removes the skeleton's `FIELD_*`
constants, and no file is named for the fork's `FIELD_*` names the four command modules share, so each module would
define its own copy (coding-standards.md item 1; the fork keeps them in one block).
Proposed-edit: append to D3 "Constants." the clause "and one `FIELD_*` constant for every JSON field the transport reads
or writes (coding-standards.md item 1)"; in the D2 tree change the `_common.py` note to "body resolution, JSON printing,
the `FIELD_*` constants the command modules share (the fork's names); not a command module".

### C2 — Positional call sites written into the design
Severity: C
Location: design.md § D6 `main` step 5; § Data flow
Defect: D6 step 5 writes `steward_delegate(verb, args, token, "github")` and the data flow writes
`registry.call("pulls/get", ...)`, while coding-standards.md item 4 names the parameters at every call site.
Proposed-edit: write `steward_delegate(verb=verb, args=<the rebuilt list>, token=token, host="github")` in D6 step 5 and
`registry.call(transport=transport, operation_id="pulls/get", ...)` in the data flow.

### C3 — The registry's tests are filed under the transport's test module
Severity: C
Location: design.md § Testing Strategy "Transport and registry unit tests"; § Acceptance Criteria Mapping AC-1.1
Defect: the `registry.py` tests (AC-1.1 `test_call_refuses_an_undocumented_parameter`) live in
`test_github_api_transport.py`, so `registry.py` has no test module of its own. testing.md item 3 maps a test module to
its source module, and D2 gives each family its own `test_github_api_<family>.py`. The hook suite's `test_stop_gates.py`
groups several modules, so it is unclear whether this conforms.
Proposed-edit: add `src/payload/test/test_github_api_registry.py` to the D2 tree, name it in the Testing Strategy bullet
("Transport unit tests — `test_github_api_transport.py`; registry unit tests — `test_github_api_registry.py`"), and
point the AC-1.1 Mapping row to it.

### C4 — "E2E: not applicable" for a change that gives shipped code its runtime behaviour
Severity: C
Location: design.md § Testing Strategy, the "E2E" bullet
Defect: always-test-e2e.md keeps "E2E: not applicable" for a change that alters no runtime behaviour; this change
gives the shipped wrapper its behaviour, and the reason the bullet gives (no session runs it until promotion) defers
the check to #10's fixture (requirements Residuals). It does not show that runtime behaviour is absent.
Proposed-edit: replace the bullet with "**E2E:** the real-forge check is #10's fixture on an ephemeral `sff-test-*`
repository (requirements Residuals; its item stays open on #17); until then the CLI is exercised through its real
interface up to the API boundary by `test_the_script_runs_by_path` and the golden `CASES`, in CI's `tests` leg."

NOT-CLEAN (0 A, 2 B)
