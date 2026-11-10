# Tasks review, iteration 02, lane spec-review-agent (issue #13, tier M, delta)

Fix sites, judged:

- C1: closed. In 1.1, `lookup` sees synthetic `RestOperation`s through a monkeypatched `registry.discover_families`,
  and each case matches its own message. In 2.2, the record is served through `monkeypatch.setattr(registry, "lookup",
  …)`. D5 puts the twice-declared check inside `lookup`, so 1.1's patch leaves that check in place. 2.2's patch
  replaces only the id resolution, so the `ValueError` that 2.2 matches can come only from `encode`.
- C2: closed. 1.2 joins `encode`'s pairs with D4's `urlencode(pairs, safe="[]", quote_via=quote)`, copied exactly.
  P needs nothing from Wave 2.
- D1: closed. 5.5 names `setup-claude.txt` Part 5.3 ("Git repository wrapper scripts") and `setup-kiro.txt` Part 6.2
  ("Stub credentials and wrappers"). Those are the sections that copy the wrapper today and the ones D2 names.
- 3.2 `test_script_loads_by_path`, the test-architect's B1, is accepted. A `-c` interpreter run with `cwd=tmp_path`
  does not have the scripts directory on `sys.path`. Nothing in `scripts/` or `.github/` sets `PYTHONPATH`, and
  `pyproject.toml` has no pytest `pythonpath`. `[tool.setuptools] packages = []` installs no `gitlab_api`. So the test
  fails exactly when the bootstrap is missing. In Wave 3's red capture it passes on the skeleton, because the skeleton
  imports only the standard library. Task 3.2 still goes red through its `main(argv=…)` cases, because the skeleton's
  `main()` takes no argument. The design.md "Subcommands" sentence and the UB-1 row match 3.2 and 4.1: the two
  script runs are `test_script_usage_error_exits_2` and `test_script_without_config_exits_1`.
- The "imported inside the test" clauses in 2.2 and 5.1 keep R and C collectable in Waves 2 and 5.
- The waves stay disjoint: every edited task kept its `Files:`. No `Validates:` line gained an id, and the coverage
  table is unchanged. The design edit adds only a test name to UB-1's row, not a criterion.

### D1 — 5.5's second line is not wrapped
Severity: D
Location: tasks.md § Wave 5, 5.5
Defect: The fix pass joined two lines, and the result runs past the 120 columns that every other line of tasks.md
keeps.
Proposed-edit: rewrap 5.5 at 120 columns and leave the text unchanged.

CLEAN
