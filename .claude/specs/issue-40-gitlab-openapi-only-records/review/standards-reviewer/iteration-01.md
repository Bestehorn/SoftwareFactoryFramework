# Standards review — design iteration 01 — issue #40

Lane: standards-reviewer. Subject: `design.md` against `.claude/rules/`, the conventions of
`src/payload/scripts/gitlab_api/` and #41 D8.

### B1 — The design's Residuals section is over the ten-line cap
Severity: B
Location: design.md § Residuals
Defect: The section runs to eleven lines, which is over `proportionality.md` § Scope freeze's "`## Residuals` (≤ 10 lines)". Its first bullet uses three lines to repeat `requirements.md` § Residuals.
Material-because: unmaintainable-by-rule `.claude/rules/proportionality.md`. The cap is a stated rule, and this section breaks it.
Proposed-edit: replace the first bullet ("The four residuals of `requirements.md` stand: … Each gets one findings-ledger row (D6).") with the single line "- The four `requirements.md` Residuals stand, each one findings-ledger row (D6)."

### B2 — D1 leaves `expand`'s own docstring stating the old rule
Severity: B
Location: design.md § D1 "The functions" (the bullet "`send` and `pages` call `expand` as before"); § D6 row D1
Defect: D1 allows only two docstring edits: the module's `expand` bullet and `placeholders`'. That leaves `registry.expand`'s docstring saying "every `:name` replaced by its value as ONE percent-encoded segment" and "a path parameter without a value raises `ValueError`". D1 step 1 makes the second statement false for an optional group's parameter, and the first leaves out `*name` and both parenthesis forms.
Material-because: unmaintainable-by-rule `.claude/rules/post-activity.md` (item 4: docs must not deviate from the implementation). The design follows this convention itself in D2, where `missing_path_parameters`' docstring is rewritten along with its rule. `issue-filing-discipline.md` also lists a stale docstring as a defect to fix.
Proposed-edit: in D1, replace "Nothing else in the module changes but two docstrings: the module's `expand` bullet and `placeholders`'." with "Nothing else in the module changes but three docstrings: the module's `expand` bullet, `placeholders`', and `expand`'s, which states the three steps and that a group whose parameter has no value is left out." In D6 row D1, replace "the module docstring's `expand` bullet and `placeholders`' docstring" with "the module docstring's `expand` bullet and the docstrings of `placeholders` and `expand`". In D6 row D3, add "the docstrings of `expanded_path` and `route_problems`", because both say "each `:name` replaced".

### B3 — The new patterns are compiled with a positional argument
Severity: B
Location: design.md § D1 "Representation" (the code block)
Defect: The block writes `PLACEHOLDER`, `OPTIONAL_GROUP` and `ESCAPED_PARENTHESIS` as `re.compile(r"…")`, passing the pattern positionally. `coding-standards.md` rule 4 requires named parameters at every call site. N already compiles its patterns as `re.compile(pattern=…)` (`test/test_gitlab_wrapper_contract.py` `PATH_PLACEHOLDER`, `ENDPOINT`), and the same block writes `quote(string=part, safe="")` with named parameters.
Material-because: unmaintainable-by-rule `.claude/rules/coding-standards.md` (rule 4, "NO EXCEPTIONS"). The implementer copies the code block as written.
Proposed-edit: in the code block, write the three patterns as `re.compile(pattern=r"(?P<sigil>[:*])(?P<name>[A-Za-z_][A-Za-z0-9_]*)")`, `re.compile(pattern=r"(?<!\\)\((?P<inner>[^()]*)(?<!\\)\)")` and `re.compile(pattern=r"\\(?P<parenthesis>[()])")`.

### C1 — D3 says all three edits fall inside #41 D8's exception, but one does not
Severity: C
Location: design.md § D3, the sentence "all three are N's path reading, #41 D8's exception"
Defect: #41 D8's exceptions row limits N's path reading to "`record_problems`' path-row rule, `sent_call`, `call_problems`". D3's third edit changes `record_problems`' rule for a row the record lacks. It also adds `glob_names` and a new N test, and neither is on that list. The Overview says D3 "edits past" D8, so the two passages disagree.
Material-because: if the text stays, the next slice reading D8's boundary will be misled about where it lies. This is a clarification only.
Proposed-edit: replace the sentence with "The first two are `call_problems`' path reading, #41 D8's exception. The third reaches past it, into `record_problems`' rule for a row the record lacks: AC-1.4 reads a `query`, `body` or `form` row as a path parameter, and the path-row rule never sees such a row. `test_a_path_form_is_read_and_sent_as_written` pins all three."

### C2 — D2's change to `call.py` is tested only outside `call.py`'s test module
Severity: C
Location: design.md § D5 (F's tests; "Additions to existing modules"); § Acceptance Criteria Mapping rows AC-2.3, AC-2.4
Defect: D2 changes which path parameters `commands/call.py` refuses. Its refusal test, `test_a_missing_path_parameter_is_refused_unless_optional`, is placed in F, the family module. `testing.md` item 3 pairs a test module with the source module it covers, which for `call.py` is K. K's `test_a_missing_path_parameter_is_refused` already exercises this refusal against real records, so that is where its "unless optional" counterpart belongs.
Material-because: ambiguous conformance with `.claude/rules/testing.md` item 3. The behaviour is tested, but in a module other than the paired one.
Proposed-edit: in D5, move `test_a_missing_path_parameter_is_refused_unless_optional` from F's list to "Additions to existing modules" as "K gains `test_a_missing_path_parameter_is_refused_unless_optional` (the two cases of Correctness Properties AC-2.3 and AC-2.4)". In the mapping rows and Correctness Properties AC-2.3 and AC-2.4, replace "F `test_a_missing_path_parameter_is_refused_unless_optional`" with "K `test_a_missing_path_parameter_is_refused_unless_optional`".

NOT-CLEAN (0 A, 3 B)

Verdict: NOT-READY
