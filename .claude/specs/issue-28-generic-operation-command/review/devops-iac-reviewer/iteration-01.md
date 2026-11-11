# Design review — devops-iac-reviewer — iteration 01

### B1 — The AC-1.3 Hypothesis property goes into a shipped suite, so the change adds a third-party import while the design says it adds no dependency
Severity: B
Location: design.md § Testing Strategy "Unit tests"; § Correctness Properties AC-1.3; § Acceptance Criteria Mapping
  AC-1.3; § Security Considerations "Dependencies"
Defect: K is `src/payload/test/test_github_api_call.py`, a shipped suite under `src/payload/`. Its
  `test_any_json_value_becomes_the_body_member` would be the tree's first `hypothesis` import (no file imports it
  today). That contradicts #17 X1 (`issue-17-github-wrapper-foundation/review/review-latest.md`: "any Hypothesis
  property test live in `test/` … Shipped suites under `src/payload/test/` stay pytest-only"; #17 design.md D7: "the
  shipped suites stay pytest-only and Python 3.9"). It also makes § Security Considerations' "No new dependency"
  false.
Material-because: unmaintainable-by-rule `dependencies.md` (rule 1: shipped `src/payload/` Python is standard library
  only and its suites need only pytest; a third-party import there is a dependency change that must be flagged as a
  design change), with `tech-stack.md` ("only the test suites need pytest").
Proposed-edit:
  - § Testing Strategy, "Unit tests": replace "`json_member` and `body_of` in `test_github_api_call.py` (K) get a
    Hypothesis property (AC-1.3)." with "`json_member` and `body_of` get a Hypothesis property in N,
    `test/test_github_wrapper_contract.py`, which loads the product package as V does (#17 X1: a Hypothesis test
    lives in `test/`; the shipped suites stay pytest-only)."
  - § Correctness Properties AC-1.3: replace "Property, K `test_any_json_value_becomes_the_body_member`" with
    "Property, N `test_any_json_value_becomes_the_body_member`".
  - § Acceptance Criteria Mapping, row AC-1.3: replace "K `test_any_json_value_becomes_the_body_member`,
    `test_a_body_member_holds_the_given_json_value`" with "N `test_any_json_value_becomes_the_body_member`; K
    `test_a_body_member_holds_the_given_json_value`".

### C1 — D7 does not say where the map's `call` sentence goes, so it can follow the bullet's caveat that sessions here run the fork, which has no `call`
Severity: C
Location: design.md § D7 "The map."
Defect: D7 says only that the `github_api/` bullet "gains" the sentence, without saying where. The bullet now ends
  "Not yet installed here: sessions run the fork (`config/toolchain.json`)." The installed `scripts/github_wrapper.py`
  is the fork (`config/toolchain.json` `deviations`) and has no `call` subparser. So in this repository, `python
  scripts/github_wrapper.py call issues/get --path issue_number=5`, run as the map writes it, exits 2 with argparse's
  invalid-choice error.
Proposed-edit: in D7 replace "gains:" with "gains, before its closing sentence (which stays last and becomes "Not
  yet installed here: sessions run the fork, which has no `call` (`config/toolchain.json`)."):".

### D1 — The E2E statement says the in-process tests use the "real command-line interface"
Severity: D
Location: design.md § Testing Strategy "E2E."
Defect: K and N run the product's `main(argv=...)` in process (`run_product_case`). The run through the real entry
  point is C `test_the_script_runs_by_path`, which is unchanged. Its child interpreter builds the parser and so
  imports `commands/call.py` through `_discover_command_modules`.
Proposed-edit: replace "`call` is exercised through its real command-line interface up to the API boundary by K and
  N, in CI's `tests` leg." with "`call` is exercised through `main`'s argv up to the API boundary by K and N, and
  the entry script loads `commands/call.py` by path in C `test_the_script_runs_by_path` (unchanged), all in CI's
  `tests` leg."

Verdict: NOT-CLEAN (0 A, 1 B)
