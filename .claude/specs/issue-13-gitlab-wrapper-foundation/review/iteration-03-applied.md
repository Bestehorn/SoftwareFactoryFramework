# Iteration 03 — C/D findings applied (design.md only; no new review round)

- SR-C1 — applied: "Every shipped suite (T, R and C) installs `FakeGitLab` and a `socket.socket.connect` guard as
  autouse fixtures" (merged with TA-C2).
- SR-D1 — applied: the restated "skeletons" sentence says the metadata and checklist toggle "arrive in a later
  framework release"; no issue number goes into shipped prompt text. The `(#15)` left in design-internal text is not
  prompt text.
- TA-C1 — applied in D8 and AC-1.2: a package name unique to each test, one `discover_families` call per package after
  its files are written.
- TA-C2 — applied together with SR-C1 (same sentence).
- TA-C3 — applied: the transport tests keep `opener` at its default, so the redirect tests run the opener
  `from_config` builds.
- SEC-C1 — applied: the UB-2 oracle requires that neither the message nor `details` contains the rejected value.
- ST-D1 — applied: every prose line over 120 characters rewrapped without word changes, including two that the rewrap
  itself pushed past the limit; tables and code blocks are untouched.
- BP-C11 — applied: any scheme other than `https`/`http` has no default port (`None`), so its origin never equals the
  configured one.
- BP-C12 — applied: "resolves or opens a redirect's `Location`".
- DO-C1 — no edit here: the #17 D8 wording is routed by the conductor.
- DO-D1 — applied: the setup-kiro tree entry reads `gitlab_api/  # if GitLab`.
