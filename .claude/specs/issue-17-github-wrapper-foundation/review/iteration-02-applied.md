# Design iteration 02 — findings applied

- SR-B1 — applied verbatim: requirements UB-1.1 carve-out; D5 first bullet; D5 closing sentence.
- SR-C1 — applied verbatim: appended to D5's closing sentence.
- SR-C2 — merged with BP-C1 in D3 "Origin (X5)": a non-integer port raises `GitHubAPIError`; an empty port is absent.
- SR-C3 — merged with DO-C2 and ST-C1: new D8 bullet restating both "skeletons" sentences for GitHub (wrapper
  implements the caller-used set; `get-jobs`, `rerun`, `cancel` with #14; a new subcommand is a `commands/` module).
  Part 5.3's claim and checklist docstring pointers name `github_api/`. Part 6.2's "the template docstrings specify
  them" is left as is: D6 now keeps the module docstring, whose usage list specifies `wait-run` and the delivery verbs.
- SR-D1 — applied: `[str(pr_number)]`, `[str(pr_number), "--reason", reason]` in D6 step 5.
- SR-D2 — merged with ST-C1 and DO-D1: D8's setup-kiro bullet adds `github_api/` to the APPENDIX directory tree.
- SE-C1 — merged with BP-C2: the scheme's default port (443 `https`, 80 `http`, `http.client` `default_port`).
- SE-C2 — applied verbatim in D3 Redirects: `origin(req.full_url)`, never `req.host`.
- SE-C3 — applied: D6 strips all userinfo, a bare token included. The UB-1.1 compat-only example, merged with
  TA-C8, covers `ghp_T@` and `user:secret@`; P excludes it.
- SE-D1 — applied: "placed in a message or a log line".
- BP-C1 — merged into SR-C2's edit (names `http.client.InvalidURL`).
- BP-C2 — merged into SE-C1's edit.
- ST-C1 — applied: claim-bullet pointer (D8 first bullet) and setup-kiro tree (D8 second bullet).
- ST-D1 — applied: `Request(url=url)`.
- TA-C5 — applied: P compares stdout, exit code and the non-GET requests; "every golden value of a case P runs".
- TA-C6 — applied: AC-2.1's `download` answers `200` on the API host; the storage hop belongs to AC-3.1.
- TA-C7 — applied: S cuts each shipped-Python list from its heading to the next `###` heading.
- TA-C8 — merged into SE-C3's compat-only example.
- DO-C1 — applied: the X4 residual says the promotion leaves `github_api/` out of its setup-prompt step while the
  `not_installed` entries stand (`toolchain_manifest.py` lists, `test_toolchain_integrity.py` requires).
  Residuals tightened to ten lines.
- DO-C2 — merged into SR-C3's edit.
- DO-D1 — merged: claim pointer as in ST-C1; tree as in SR-D2.
