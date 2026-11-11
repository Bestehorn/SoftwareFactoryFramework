# devops-iac-reviewer — design iteration 02 (delta) — issue #41

C1, C2 and C3 are applied at their sites (D5 "The rule" and Residuals "The test instance"; Testing Strategy "Property
test"; D5 "The anchor"). The changed text adds no CI, toolchain or operability defect.

### D1 — The restated anchor rule leaves out the fenced-code exclusion it restates
Severity: D
Location: design.md § D5 "Reference half", "The anchor", step 1
Defect: `scripts/api_reference/verify.py` `anchors` removes every fenced block (`` re.sub(r"```.*?```", "", …,
flags=re.S) ``) before it matches `HEAD` (`^(#{1,6})\s+(.*?)\s*$`). The restatement says "restated" but does not
mention the fenced blocks, so a `# …` line inside a fence would count as a heading in N's slug counter but not in
`anchors`. Today no `docs/api-reference/gitlab/rest/*.md` page has a fence (Grep for `` ^``` `` finds 0 matches), so
no anchor computed today differs.
Proposed-edit: in step 1, before "The heading's backticks", insert "Lines inside fenced code blocks are not headings.".

Verdict: CLEAN
