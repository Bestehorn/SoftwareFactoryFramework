# Standards review — design iteration 01 (issue #28)

### S-A1 — The `[]` query-name rule exists twice, and the registry copy refuses what D4 accepts
Severity: A
Location: design.md § D2 "Registry additions" (`send`); § D4 "Documented names"; § Correctness Properties AC-1.2
Defect: D4's check in `commands/call.py` compares a query name with its trailing `[]` removed, but `registry.send`
(D2: "`_check_names` for query and body") and the unchanged `registry.pages` run `registry._check_names`, which
compares the name as given (`name not in documented`), and the records hold names without `[]`
(`families/issues.py` `issues/list-for-repo` `query_params` holds `state`); so `call issues/list-for-repo --query
state[]=open` passes D4 and then raises `ValueError` before any request — an uncaught traceback through
`_run_command`, which catches only `GitHubAPIError`.
Material-because: wrong-behaviour — AC-1.2's example "`--query state[]=open` sends the name `state[]`" cannot pass;
the cause is a check restated in `call.py` instead of reused from `registry.py` (unmaintainable-by-rule
design-principles.md item 2, "reuse before adding new abstractions").
Proposed-edit: add to D2 "Registry additions" the bullet: "`query_name(name) -> str`: `name` with one trailing `[]`
(`QUERY_ARRAY_SUFFIX`) removed. `_check_names` compares each query name through it, so `send` and `pages` accept the
names D4 accepts, and D4's undocumented-name check calls it rather than restating the rule." In D8's `registry.py`
row replace "adds `path_parameters` and `send`" with "adds `path_parameters`, `query_name` and `send`;
`_check_names` compares query names through `query_name`".

### S-B1 — A Hypothesis property in a shipped suite
Severity: B
Location: design.md § Testing Strategy "Unit tests"; § Correctness Properties AC-1.3; § Acceptance Criteria Mapping
row AC-1.3; § D8 "This change"
Defect: `test_any_json_value_becomes_the_body_member` is a Hypothesis test in K, `src/payload/test/`, a suite that
installs into projects (`test_github_wrapper_compat.py` module docstring: "Installed from `src/payload/test/…` to
`test/…`"), while #17's X1 (`.claude/specs/issue-17-github-wrapper-foundation/review/review-latest.md`) puts "any
Hypothesis property test" in `test/` and keeps `src/payload/test/` "pytest-only and Python 3.9"; no Python file in
the repository imports `hypothesis` today, and the design's Security section says "No new dependency".
Material-because: unmaintainable-by-rule tech-stack.md ("only the test suites need pytest") and dependencies.md
item 1 (a third-party import under `src/payload/` is a dependency change for every project that installs the file).
Proposed-edit: in Testing Strategy replace "`json_member` and `body_of` in `test_github_api_call.py` (K) get a
Hypothesis property (AC-1.3)" with "`json_member` and `body_of` get a Hypothesis property in
`test/test_github_api_call_properties.py` (H), which loads the product package from `src/payload/scripts` as V does
(#17 X1: Hypothesis tests live in `test/`)"; add `H = test/test_github_api_call_properties.py` to the mapping's file
list and name H for `test_any_json_value_becomes_the_body_member` in Correctness Properties AC-1.3 and in the AC-1.3
row; add H to D8's "This change" table as "new (AC-1.3's property)". Write the sketch with named arguments
(coding-standards.md item 4, as the suites already write `pytest.mark.parametrize(argnames=…, argvalues=…)`):
`st.recursive(base=…, extend=lambda inner: st.lists(elements=inner) | st.dictionaries(keys=st.text(), values=inner))`.

### S-C1 — D8's slice table replaces #17 D2's without saying so
Severity: C
Location: design.md § D8 "A slice"
Defect: #17 D2 "What a family's change edits" has a slice always add `test_github_api_<family>.py` and allows
editing `commands/<group>.py`; D8 adds the test module only for a family with a `Paging.LINK` record and lists
`commands/*` under "never", without stating which table a slice follows.
Proposed-edit: append to the "A slice (#27, #29, #31, #32, #33):" lead: "This table replaces #17 D2's 'What a
family's change edits' table for these slices."

### S-C2 — D4 leaves open whether its check raises, and where `EXIT_REFUSED` lives
Severity: C
Location: design.md § D2 `cmd_call` step 1; § D4 "How a refusal is written"
Defect: D4 does not say whether its check raises or returns its problems (coding-standards.md item 5), nor where
`call.py` gets `EXIT_REFUSED`: the entry script's constant is not importable by a command module, and `ci.py` and
`claim.py` each define their own `EXIT_*`.
Proposed-edit: replace D4's first "How a refusal is written" sentence with: "D4's check raises `ValueError` with the
one message, as `registry.lookup` and `registry._check_names` do; `cmd_call` catches `ValueError` around `lookup` and
the check only, logs it with `logger.error`, and returns `call.py`'s own `EXIT_REFUSED = 2`, as `ci.py` and
`claim.py` hold their `EXIT_*`."

### S-C3 — The entry script's docstring test sits in the `call` module's suite
Severity: C
Location: design.md § Correctness Properties AC-4.1 and UB-1.1 "Verification"
Defect: `test_the_usage_names_the_operation_call` reads `github_wrapper.py`'s `__doc__` but is placed in K, which
covers `commands/call.py` (testing.md item 3: a test module covers its source module); the entry script's suite is
C, which UB-1.1 lets this change add to ("this change only adds cases") but the design's verification bars ("no
line … of C … changed").
Proposed-edit: name C for `test_the_usage_names_the_operation_call` in Correctness Properties AC-4.1 and the AC-4.1
mapping row, and restate UB-1.1's verification as "the PR diff changes no existing line of `CASES`, of C or of P; C
gains only `test_the_usage_names_the_operation_call`."

### S-D1 — A call site written positionally
Severity: D
Location: design.md § D4 "Documented names"
Defect: "path: `registry.path_parameters(record)`" writes an own-function call positionally (coding-standards.md
item 4); the rest of the design writes `registry.lookup(operation_id=...)`, `print_json(value=items)`.
Proposed-edit: "path: `registry.path_parameters(operation=record)`".

Verdict: NOT-CLEAN (1 A, 1 B)
