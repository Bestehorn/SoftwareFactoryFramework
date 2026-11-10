# Iteration 02 — findings applied (design.md; requirements.md untouched this pass)

- ST-B1 — applied: `test_gitlab_api_registry.py` (R) beside T in D2, Testing Strategy, Mapping; five tests moved T→R.
- DO-B1 — applied, corrected: D2 "Install path" restates the GitLab half of the "skeletons" sentence only (the GitHub
  half is #17 D8's) and the three pointers; D7 keeps the metadata and checklist-toggle notes until #15.
- DO-C1 — no edit here: the GitHub half is routed by the conductor (#17 D8 already restates it).
- DO-D1 — applied: setup-kiro appendix tree lists `gitlab_api/`; D7's SSO sentence names `gitlab_api/transport.py`.
- SR-C1 — applied: Part 5.3 pointers name `gitlab_api/`, own-MR caveat in `commands/mr.py`; docstring keeps exit notes.
- SR-C2 — (1) registry module, (2) `pages` generator, (3) `FAMILY` adopted; (4) commands and (5) body rows added.
- SR-C3 — applied: `json_body`.
- SR-C4 — applied: `discover_families(*, package=…)`, cached per package; supersedes TA-C2's monkeypatch seam.
- SR-C5 — applied: port split after the last `:` outside `[...]`; a `Location` `ValueError` raises status 0.
- SR-C6 — applied: `str(Path("config") / "gitlab.json")`.
- SR-C7 — applied, corrected: transport row names T, registry row names R (ST-B1's split).
- SR-D1 — applied: named arguments in Data flow.
- SR-D2 — applied: `CredentialStrippingRedirectHandler()`.
- SR-D3 — applied: full record id in the `issue assign` row.
- ST-C1 — applied as written (config keys, single-module response keys, shared keys in `commands/_common.py`).
- ST-C2 — applied: Data flow and "named arguments at every call site".
- ST-C3 — applied, merged into the DO-B1/DO-D1 restatement.
- BP-C7 — applied with #17 D3's rules: scheme default port (443/80), empty port absent, non-integer port raises.
- BP-C8 — applied, corrected: `secrets.token_hex(16)` cites RFC 2046 §5.1.1 without the digit/character figures.
- BP-C9 — applied in D7 and Security: only `!` to `~`; UB-2 example adds a zero-width space.
- BP-C10 — applied: `exclude_categories`.
- SEC-C7 — applied: `CREDENTIAL_HEADERS` respelled; Redirects parenthesis simplified; AC-3.1 compares names
  case-insensitively.
- TA-C1 — applied: dict clause uses the same `parse_qsl(..., keep_blank_values=True)`.
- TA-C2 — superseded by SR-C4's `package=` seam (per-package cache, synthetic package on `sys.path`).
- TA-C3 — applied: unscripted request is recorded, then raises `AssertionError`.
- TA-C4 — applied: the properties module puts `src/payload/scripts` on `sys.path`.
- TA-C5 — applied: the scanned set names the three files.
- TA-D1 — applied: `insufficient_scope: ` plus the fixture's `error_description`.
- #17 D3 wording — adopted: `origin` of the target vs `origin(req.full_url)`, never `req.host`.
