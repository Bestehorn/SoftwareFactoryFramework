# Design iteration 03 — findings applied

- TA-A1 — applied verbatim: the UB-1.1 userinfo example asserts on the `caplog` records. They must hold the refusal
  naming `.git/config` and `github.com/o/socket.io.git`, and neither they nor stderr may hold `ghp_T` or `secret`.
- TA-B1 — applied verbatim: AC-3.1's cross-host `302` is followed "from `request` and from `download`" with no
  `Authorization`.
- TA-C9 — applied: AC-3.1 adds a `302` to `https://user:pw@api.github.com/x`, which raises `GitHubAPIError` with no <!-- pragma: allowlist secret -->
  request recorded to it, and `https://api.github.com:/x`, which keeps `Authorization`.
- BP-C1 — applied verbatim in D3 "Failures": "a `ValueError` or an `http.client.InvalidURL` raised while urllib
  resolves or opens a redirect's `Location`".
- BP-C2 — merged with ST-C1 and SR-C1 (iteration 03). D5's closing sentence now reads "an uncaught
  `http.client.InvalidURL` — exit status 1 with a traceback, not the `GitHubAPIError` that UB-1.1's exit 1 names".
- ST-C1 — merged into BP-C2.
- ST-C2 — applied: the X4 wording is "skips Part 5.3's `github_api/` copy", and the Residuals section is ten lines.
- ST-D1 — applied: `origin(url=req.full_url)`.
- ST-D2 — applied without word changes. Rewrapped at 120 columns: requirements UB-1.1, D3 "Redirects", the
  "Failures" lead line, D5's first bullet, D6 `_detect_repo` and step 5, AC-2.1 and UB-1.1 parser parity. The Sources
  link lines still run past 120 columns because a URL cannot be broken.
- SE-D1 — applied verbatim: "No message carries the git remote URL's userinfo (`_detect_repo`)."
- SR-C1 (iteration 03) — applied as the merged D5 sentence (see BP-C2).
- SR-C2 (iteration 03) — applied verbatim: in D8, `get-jobs`, `rerun` and `cancel` "arrive in a later framework
  release", so the shipped prompts cite no issue of this repository.
- SR-D1 (iteration 03) — applied verbatim: the D6 gloss reads "the authority's text up to and including its last
  `@`, a bare token included".
- DO (iteration 03) — no findings.
