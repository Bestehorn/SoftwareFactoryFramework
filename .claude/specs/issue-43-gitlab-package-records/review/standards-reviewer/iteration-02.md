# Standards review — issue #43, design iteration 02 (delta)

Lane: standards-reviewer. Scope: the iteration-01 fix sites and the edits the consolidated review applied.

## Iteration-01 findings

- B1 — closed. design.md § D4 "Why #41 D8's exceptions row is reached past in N" names the four edits and why AC-4.3
  needs them, as #40 D3 and D5 name theirs. Its closing sentence matches design.md § D8's N row edit for edit.
- B2 — closed. requirements.md § Residuals and design.md § Residuals each run to ten lines. The stale AC-1.4/AC-4.2
  bullet is gone from the design. The requirements' Workhorse bullet agrees with the restated AC-1.4 and AC-4.2.
- C1 — closed. § Correctness Properties AC-2.4 reads `st.sampled_from(elements=<the npm values>)`, the keyword form P
  already uses (`st.lists(elements=TEXTS)`).

## The delta

No new project-standard violation:
- D5's two JSON raw-body records use `CONTENT_TYPE_JSON`, the other raw-body records `CONTENT_TYPE_OCTET_STREAM`.
  Both constants are defined in `gitlab_api/transport.py` and imported by absolute path (`coding-standards.md` rules
  1 and 2).
- D2's `route` refusal renders caller text with `json.dumps`, as `commands/call.py` `check_parameters` does.
- D6 puts every `Param` of a raw-body record in `Location.QUERY`, following #40 D4's transcription row.
- requirements.md and design.md both stay under their tier-M caps (`proportionality.md`).
- No acceptance-criterion id was added: AC-1.1 to AC-4.4 and UB-1 to UB-4 are unchanged.
- The new Residuals bullets route to the findings ledger (D8, through `memory_compile.py ledger add`), to #11, or to
  the tenant-scale slice's gate (#41 design.md Residuals). `issue-filing-discipline.md` allows each of these routes.

CLEAN

Verdict: READY
