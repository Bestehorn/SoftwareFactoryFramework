# Iteration 01 — what the author applied (for the iteration-02 delta review)

design.md 34,663 → 42,510 bytes; requirements.md 12,083 bytes. No criterion added. Worktree rebased onto origin/main 1c69c2a (has `scripts/toolchain_manifest.py`).

requirements.md restatements: UB-1.1 excludes redirected and AC-3.2 rate-limited responses (SR-B1); UB-1.1 delivery bullet restated (SR-C1); same-host residual leaves "whether it is followed" and "whether `Authorization` is kept" to the design; the 307 residual covers every write request on a renamed repository (BP-C1); the multi-file layout residual: copy step done here (D8), manifest at promotion.

- TA-A1 → X1: UB-2.2 import check in `test/` (CI 3.10) with `sys.stdlib_module_names`; no Hypothesis test.
- TA-A2: parity excludes the `--token-stdin` cases (C expects exit 2, empty stdout, no request).
- TA-B1: `_build_parser()` exposed; `test_the_parsers_match_option_by_option` compares action attributes incl. `type`; fork's `--token-stdin` excepted; `CASES` holds `list-issues --label`.
- TA-B2: ordered route responses, expected write requests per case, `start-issue`/`issue start` exit-0 cases.
- TA-B3: retry-after-wins case. TA-B4: AC-2.1 covers `download`. TA-B5: AC-5.1 counts against the index heading total; several graphql_only rows incl. exclusions. TA-B6: capability-gap example plus covered/pending of each kind.
- TA-C1..C4: UB-1.3 oracle `str(Path("credentials") / "github-pat.txt")`; fake host records merged headers case-insensitively; P sets `sys.argv`; last page of prev/first/last row has a link header without next.
- SR-B1: all three parts; D5 deviations as bullets (same-origin follow is D3's decision; `get-issue` on a renamed repository exits 0 where the fork exits 1). SR-C2: D6 step 5 spells out steward argument lists. SR-C3: with TA-A2. SR-C4: the fork's unencoded `--labels` crash is a visible deviation. SR-C5: D2 rows for `github_wrapper_fixtures.py`, `commands/_common.py`, `errors.py`.
- ST-B1 + X2: `github_api/errors.py` with `GitHubAPIError`, `GitHubRateLimitError`, `GitHubGraphQLResponseError`.
- ST-B2 → X3: D8 edits the copy steps (setup-claude Part 5.3 incl. its docstring pointer, setup-kiro Part 6.2, both shipped-Python lists); test S (traced to UB-1.3) pins them.
- ST-C1..C4: `FIELD_*` constants (transport; `_common.py` for commands); named parameters; new `test_github_api_registry.py`; E2E bullet replaced.
- SE-B1 + X5: `_send` refuses any origin other than `API_ROOT`'s (or `UPLOAD_ORIGIN` for uploads); AC-2.2/AC-2.4 gain other-origin examples; the author dropped the claim that a prefix test admits `api.github.com.evil.test` (the fork's prefixes end in `/`).
- SE-B2: `_detect_repo` strips `user:password@`; "no message carries a URL's userinfo".
- SE-C1: `.`/`..` path segment raises `GitHubAPIError` (exit 1). SE-C2: response values in messages via `json.dumps`. SE-C3: P runs in the temporary project with the fixture token. SE-C4: `:8443` stripped, `:443` kept.
- DO-B1 → X4: residual restated (ledger row by the conductor). DO-C1 superseded by X3. DO-C2: WARNING logged before each rate-limit wait.
- BP-C1: D5 and residual. BP-C2: a `ValueError` from a malformed `Location` becomes `GitHubAPIError`.
- X5: `transport.origin()` = urllib's scheme and host lower-cased, port 443 when absent; used by the redirect handler and `_send`.
