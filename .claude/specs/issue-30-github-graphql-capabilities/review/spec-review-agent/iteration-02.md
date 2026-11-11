# Spec review, iteration 02 (delta), SPEC lane (issue #30, tier M)

Scope: the fix sites of `review/review-latest.md` (Y1 to Y6 and every C/D) in `requirements.md` and `design.md`, the
scope freeze, and the caps. I did not re-open any text that passed iteration 01.

## Fix sites

| Finding | Site | Status |
|---|---|---|
| SR-B1 / Y3 | requirements § Glossary "Declared variables" | APPLIED verbatim. AC-2.1, AC-2.5, D3 `declared_variables`, R `test_variables_are_the_documents_definitions` and G's `["owner", "name"]` oracle now name one set. The `-f after=c` case is attributed to D3/DL-004. |
| SR-B2 / TA-A1 / Y1 | design § D6 `document_problems`, connection bullet; § Correctness Properties "Q's method" | APPLIED. The `after`/`pageInfo` checks now run only on a matching path, and the oracle reads "at least one problem, and one of them names what differs". The `since:` case (`since` is not an argument; there is no `after: $after`) and the `mergeQueue` case each give at least one problem. |
| SR-B3 / BP-B1 / Y2 | design § D4 `ownerId` row; § Sources | APPLIED verbatim. "Get a repository" is listed as the source. |
| SR-C1 | design § D6 `reference_schema` | APPLIED. It agrees with `test_the_reference_is_read_as_written`: the Type cells of `objects-p-w.md` `Repository.mergeQueue` and `objects-a-p.md` `MergeQueue.entries` carry no wrapper. |
| SEC-B1 / Y4 | D6 mutation bullet; the "Q's method" cases; mapping row AC-3.1 | APPLIED. The swapped-document case gives exactly the ID problem, because `EnablePullRequestAutoMergePayload` and `DisablePullRequestAutoMergePayload` both have `pullRequest` (`mutations.md`). |
| TA-B1 / Y5 | D6 G `test_every_record_is_called_through_main` | APPLIED. |
| TA-B2 / Y6 | Correctness Properties AC-4.1 | APPLIED, but it introduces B1 below. |
| TA-C1 to C6, TA-D1 | Correctness Properties AC-2.1, the AC-1.3 example, AC-2.5, "Q's method", AC-4.2; mapping row AC-4.2 | APPLIED. |
| ST-C1 | D3 step 3, "Registry additions", D8, mapping row AC-2.5 | APPLIED. A grep finds no `registry.variables` or `` `variables(* `` left. |
| ST-C2 | D7 "Module docstrings" | APPLIED. |
| BP-C1, BP-C2 | design § Residuals | APPLIED. BP-C1 is merged with the discussion-comment residual. |
| SEC-C1 | Security Considerations "Output"; § Sources | APPLIED. The `json.dump` `ensure_ascii` quote matches docs.python.org verbatim. |
| DV-C1, DV-D1 | the closing sentence of D6; Operability | APPLIED. |

**Scope freeze.** In `requirements.md` only the Glossary bullet changed. Neither file adds an AC or UB id: the design
header and the mapping table still list AC-1.1..AC-4.2 and UB-1.1..UB-3.1. Y4's Q rule and TA-C6's map test prove
existing criteria (AC-3.1, AC-4.2). BP-C1 and BP-C2 were added as Residuals, not as criteria.

**Caps.** `requirements.md` is 10,458 B (cap 20,000) and `design.md` is 41,832 B (cap 60,000). Residuals run to 6 lines
in `requirements.md` and 10 in `design.md`.

### B1 — The scoped AC-4.1 oracle looks for `JSON array`, which D7's literal lines split across two lines
Severity: B
Location: design.md § Correctness Properties AC-4.1 `test_the_usage_names_every_graphql_record`; § D7 "The usage
docstring"
Defect: Since Y6, the test reads only the GraphQL entry. D7's fenced lines, which "go into the usage list", end the
third `#` line with "A connection prints as one JSON" and start the fourth with "# array of every page's nodes". So the
entry never holds the substring `JSON array`. Before Y6, the oracle was met by the `call issues/get` entry's
"A list prints as one JSON array" (`src/payload/scripts/github_wrapper.py` module docstring), which is now out of the
test's scope.
Material-because: AC-4.1. The test as specified fails on the docstring as specified, so the implementation has to depart
from one of them.
Proposed-edit: in D7's fenced block, move "JSON" from the end of the third `#` line to the start of the fourth. The third
line then ends "…record printed. A connection prints as one", and the fourth reads
`        # JSON array of every page's nodes, any other result as its data, both as indented JSON. --path, --query and a`.
I counted both lines: each stays within 120 columns.

Verdict: NOT-READY (0 A, 1 B)
