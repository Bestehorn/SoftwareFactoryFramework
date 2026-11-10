# Standards review — iteration 03 (delta) — issue-17-github-wrapper-foundation (design)

Iteration-02 at its fix sites: C1 resolved (D8 names the Part 5.3 claim bullet and the checklist bullet's "(See the
wrapper docstrings.)" and the `setup-kiro.txt` "### Standard directory structure" tree, all present in `prompts/`; the S
cuts end at headings that exist, `### Part 5.4`, `### Part 6.3` and the `###` after each shipped-Python list); D1
resolved (`Request(url=url)`). The UB-1.1 carve-out restates exceptions AC-3.1 and AC-3.2 already make and adds no id
(`proportionality.md` "Scope freeze"); D5's deviations and D6's stderr-only userinfo strip are flagged
(`design-principles.md` item 3).

### C1 — D5's closing sentence contradicts its own list heading on the fork's exit code
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged"
Defect: the list is headed "Visible only where the fork exited 1" and the fork's `main` catches only `GitHubAPIError`
(`scripts/github_wrapper.py` `main`), so the uncaught `http.client.InvalidURL` (MRO `HTTPException`, `Exception`; no
`ValueError`) exits 1, yet the closing sentence calls it "none of UB-1.1's listed exit codes".
Material-because: unmaintainable-by-rule design-principles.md item 3 — the flag misstates which fork outcome the change
breaks; does not gate.
Proposed-edit: replace "The unencoded-value case is an uncaught crash on the fork, none of UB-1.1's listed exit codes;
no golden case builds it." with "The unencoded-value case is an uncaught `InvalidURL` traceback on the fork — exit 1
without a `GitHubAPIError`, none of UB-1.1's listed outcomes; no golden case builds it."

### C2 — Residuals meets its ten-line cap only through an over-width line
Severity: C
Location: design.md § Residuals, X4
Defect: X4's third line ("… leaves `github_api/` out of its setup-prompt step") runs past the 120 columns the file's
prose keeps; rewrapped at 120 as written, X4 takes eight lines and the section eleven.
Material-because: unmaintainable-by-rule proportionality.md "Scope freeze" (`## Residuals` ≤ 10 lines); ten physical
lines as written, so it does not gate.
Proposed-edit: replace "and while they stand leaves `github_api/` out of its setup-prompt step although Part 5.3 now
copies it (" with "and while they stand skips Part 5.3's `github_api/` copy (" and rewrap X4 at 120 columns (seven
lines; the section stays at ten).

### D1 — A positional call site in new text
Severity: D
Location: design.md § D3 "Redirects"
Defect: "`origin(req.full_url)`" writes the call positionally (coding-standards.md item 4; the class of iteration-02
D1).
Proposed-edit: replace "`origin(req.full_url)`" with "`origin(url=req.full_url)`".

### D2 — Fix-site prose not rewrapped
Severity: D
Location: requirements.md § UB-1.1; design.md § D3 "Redirects", D3 "Failures, in `_send`", D6 step 5
Defect: the inserted text leaves lines past 120 columns (UB-1.1's carve-out line, D3's `ProxyHandler` line, the
"Failures" lead line, D6 step 5's list line) and a ragged break (UB-1.1's "codes: 0" line).
Proposed-edit: rewrap each named paragraph at 120 columns; no word changes.

CLEAN
