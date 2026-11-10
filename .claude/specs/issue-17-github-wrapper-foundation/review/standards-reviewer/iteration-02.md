# Standards review — iteration 02 (delta) — issue-17-github-wrapper-foundation (design)

Iteration-01 findings at their fix sites: B1 resolved (D3 "Exceptions", "Failures", `graphql(...)`, Correctness
Properties AC-3.3 and AC-4.3, Mapping rows AC-3.3 and AC-4.3 name `GitHubRateLimitError` and
`GitHubGraphQLResponseError`); B2 resolved by X3/D8, and the D8 edit conforms (`prompts/` is product —
`project-specific.md`; text only — `file-organization.md` item 3; test S in `test/` beside its precedent
`test/test_setup_prompts_gitignore.py` — `testing.md` item 1); C1–C4 applied as proposed. X1's
`sys.stdlib_module_names` in `test/` follows `test/test_toolchain_manifest.py`, and `.github/workflows/ci.yml` pins
Python 3.10.

### C1 — D8 leaves two setup-prompt statements that this change makes false
Severity: C
Location: design.md § D8
Defect: `prompts/setup-claude.txt` Part 5.3's in-progress-claim bullet still ends `See the expanded docstrings in the
wrapper templates.`, which for GitHub is the skeleton's implementation-instructions comment block (its `label_add` …
`release_issue` endpoint notes) that D6 removes; and `prompts/setup-kiro.txt` "APPENDIX — QUICK REFERENCE" § "Standard
directory structure" lists `github_wrapper.py  # if GitHub` under `scripts/` without the `github_api/` that D8 now
copies.
Material-because: unmaintainable-by-rule post-activity.md item 4 (flag deviations between docs and implementation) —
a pointer to removed text and a layout that omits an installed directory; does not gate.
Proposed-edit: in D8's first bullet, after "(the endpoints are its records; `commands/pulls.py` carries the own-PR
approval caveat, D5)" add "; the claim bullet's `See the expanded docstrings in the wrapper templates` names
`src/payload/scripts/github_api/` for GitHub too"; in D8's second bullet replace "the GitHub bullet copies the same
two." with "the GitHub bullet copies the same two, and the APPENDIX \"Standard directory structure\" lists
`github_api/  # if GitHub` under `scripts/` beside `github_wrapper.py`."

### D1 — A positional call site in new text
Severity: D
Location: design.md § D3 "Origin (X5)"
Defect: "`origin(url)` builds `Request(url)`" writes the call positionally (coding-standards.md item 4; the class of
iteration-01 C2).
Proposed-edit: replace "builds `Request(url)`" with "builds `Request(url=url)`".

CLEAN
