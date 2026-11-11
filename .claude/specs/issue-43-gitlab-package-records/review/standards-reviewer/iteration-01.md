# Standards review — issue #43, design iteration 01

Lane: standards-reviewer. Standard: `.claude/rules/` (coding-standards, tech-stack, design-principles,
project-specific, proportionality, file-organization, testing), #41 `design.md` D8, #40 `design.md` D1 to D5.

### B1 — N's edits past #41 D8's exceptions row are not recorded
Severity: B
Location: design.md § D4 (and § D8, the `test/test_gitlab_wrapper_contract.py` row)
Defect: #41 D8 puts `test_gitlab_wrapper_contract.py` under "never" "outside the exceptions", whose only N entry is
"N's path reading (`record_problems`' path-row rule, `sent_call`, `call_problems`)"; D4 edits N past it — the page
reader (`Section.route_prefixes`, `page_sections`), `prefix_problems` in `record_problems`, the call half
(`call_prefix`, `record_call`'s `prefix`, `routed_section`, the send test's loop) and #40's skip widened from `*name`
to every path name — while D3's "Why #41 D8's 'never' row yields" and DL-005 name only `call.py`, the entry script's
usage lines and the map.
Material-because: unmaintainable-by-rule `design-principles.md` (rule 4, established patterns) — #41 D8 is the
slices' file-scope table and #40 records every reach past it by name and reason (#40 D2 "Why #41 D8's 'never' row
yields", D3 "The third reaches past it", D5 "Three edits reach past that row"); an unrecorded reach leaves the next
slice (#44) no record of what the row now admits.
Proposed-edit: append to D4, after the **Raw bodies.** bullet:
"- **Why #41 D8's exceptions row is reached past in N.** The row admits N's path reading for a request form part 1
  does not build, and the route prefix is one (D3). AC-4.3 needs N to read the page's prefix values and send a prefix
  record under one, so four edits reach past the row, as #40 D3 and D5 name theirs: the page reader
  (`Section.route_prefixes`, `page_sections`), which reads a page line, not a path; `prefix_problems` in
  `record_problems`; the call half (`call_prefix`, `record_call`'s `prefix`, `routed_section` and the send test's
  loop); and #40's skip in `record_problems`, widened from `*name` to every path name (AC-1.5). Beside D7's two tests
  and the module docstring, no other line of N changes."

### B2 — Both Residuals sections exceed the ten-line cap, and the design's second bullet is stale
Severity: B
Location: requirements.md § Residuals; design.md § Residuals
Defect: `proportionality.md` "Scope freeze" caps `## Residuals` at ten lines. requirements.md's runs to 14 lines and
design.md's to 13, while #41 (requirements 7, design 10) and #40 (design 10) keep within it. The design's second
bullet also gives AC-1.4 and AC-4.2 as they read before DL-004's restatement. requirements AC-1.4 now makes every
`Param` of a raw-body record `Location.QUERY`, and AC-4.2 names those uploads raw-body.
Material-because: unmaintainable-by-rule `proportionality.md` (Scope freeze, "`## Residuals` (≤ 10 lines)"); the
stale bullet contradicts the frozen AC-1.4 and AC-4.2 it cites.
Proposed-edit:
1. design.md § Residuals: delete the bullet from "AC-1.4 reads every `form` row as a `Location.BODY` `Param`" through
   "as #40 DL-007 restated #40's." (leaves 10 lines).
2. requirements.md § Residuals: replace the two bullets beginning "\"Upload module\" lists no `file` row" and
   "npm \"Upload a package file\" lists `versions`" with:
   "- \"Upload module\" (no `file` row) and npm \"Upload a package file\" (a multipart `file`, `versions`) follow
     Workhorse's route (AC-4.2): the archive, and npm's publish document as `application/json`, are the raw body, as
     docs.gitlab.com's examples do (`design.md` D5 Sources); GitLab's own answer is #11's real-instance run."
   (leaves 10 lines at 120 columns; D8's ledger-row exclusion in design.md § Residuals still names both).

### C1 — The property's strategy call is written with a positional argument
Severity: C
Location: design.md § Correctness Properties, AC-2.4, P `test_route_accepts_only_the_records_prefixes`
Defect: the domain is written `st.text() | st.sampled_from(<the npm values>)`. P passes its strategy arguments by name
(`st.lists(elements=TEXTS)`, `st.text(alphabet=TEXT_ALPHABET)`), as `coding-standards.md` rule 4 requires.
Proposed-edit: "`st.text() | st.sampled_from(elements=<the npm values>)`".

NOT-CLEAN (0 A, 2 B)

Verdict: NOT-READY
