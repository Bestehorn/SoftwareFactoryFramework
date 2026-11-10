# Design review, iteration 03 (delta), lane spec-review-agent (issue #13, tier M)

Fix sites verified: C1 (Install path pointers; D7 docstring keeps the `pipeline wait` and delivery exit notes, and
the skeleton docstring's SSO sentence is the one D7 retargets), C2 (registry module, `pages` generator, `FAMILY`
adopted; the commands and request-body rows added), C3 (`json_body` at both sites), C4 (`package=` seam in D2, D8
and AC-1.2), C5, C6, C7 (T and R named per row), D1 to D3. The ST-B1 split agrees across the D2 tree, the table,
the Testing Strategy, the Mapping and the toolchain residual. The DO-B1 restatement quotes the prompts' sentences as
they read (`prompts/setup-claude.txt` Part 5.3, `prompts/setup-kiro.txt` Part 6.2 and APPENDIX "Standard directory
structure"), and the requirements' "Design inputs" copy-step bullet matches D2 "Install path".

### C1 — "Both shipped suites" is stale after the registry suite was split out
Severity: C
Location: design.md § Testing Strategy, "Fake host"
Defect: The bullet says "Both shipped suites also install a `socket.socket.connect` guard as an autouse fixture".
Since ST-B1, `src/payload/test/` holds three shipped suites: T, R and C (D2 tree, Mapping). R's
`test_call_refuses_an_undeclared_value` drives a `Transport`, so it is unclear whether R gets the guard.
Proposed-edit: "Every shipped suite (T, R and C) also installs a `socket.socket.connect` guard as an autouse
fixture."

### D1 — The restated "skeletons" sentence carries this repository's issue number into shipped prompt text
Severity: D
Location: design.md § D2 "Install path", first bullet
Defect: "(#15)" in a sentence of `prompts/setup-claude.txt` / `prompts/setup-kiro.txt` sends an installing project
to its own issue #15. Neither prompt names a framework issue number anywhere today. #17 D8 words the same half as
"arrive in a later framework release".
Proposed-edit: "…except the issue metadata and the checklist toggle, which arrive in a later framework release; a
project that needs them sooner adds a module of `scripts/gitlab_api/commands/` defining `register(subparsers)`."

CLEAN
