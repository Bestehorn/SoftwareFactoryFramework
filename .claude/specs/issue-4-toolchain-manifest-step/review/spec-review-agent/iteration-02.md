# Spec review — issue-4-toolchain-manifest-step — iteration 02 (tier S, combined lenses, delta)

## Findings

### B1 — the B2 fix pins the v2026.11.09 values, which the trunk's committed manifest no longer carries
Severity: B
Location: change.md § Tests, AC-5 line (the iteration-01 B2 fix site); the same root cause in AC-4
Defect: AC-4 and the AC-5 test regenerate with the `v2026.11.09` tag and date and expect the committed manifest,
but the trunk's committed manifest names `v2026.11.10` / `2026-11-10` (`origin/main` f13cf20, promotion commit
882822d; this worktree's base f285222 still carries v2026.11.09), so on the PR's merge ref, on `main` after the
merge (`.github/workflows/ci.yml` `push: branches: [main]`) and after every later promotion — the release this run
cuts after the fixes land included (prompt.md § Out of scope) — the AC-4 case and the AC-5 zero case fail whichever
`--release` the test passes, and with `--release v2026.11.10` the AC-5 differing case (`--installed 2026-11-10`)
exits zero. Iteration 01's B2 Proposed-edit introduced the pinned date at this site.
Material-because: regression — CI's `tests` group goes red on `test/test_toolchain_manifest.py` at the merge and at
each promotion; AC-4 as written cannot hold against the trunk's committed file.
Proposed-edit:
1. AC-4: replace "regenerates for `v2026.11.09` with `--installed 2026-11-09` from the committed manifest" with
   "regenerates from the committed manifest with `--release` its `release_tag` and `--installed` its `installed`".
2. § Tests: replace the AC-5 line with "- AC-5 integration (arguments as in AC-4): `--check` on the committed
   manifest exits zero; with `--installed` one day later, on a `tmp_path` copy, it exits non-zero and leaves the copy
   byte-identical."
3. prompt.md § Scope, test bullet: replace "regenerating for `v2026.11.09` with `--installed 2026-11-09` from the
   committed manifest yields the committed manifest exactly (AC-4)" with "regenerating the committed manifest for
   its own `release_tag` and `installed` yields it exactly (AC-4)".

The restated AC-4 holds on both bases: the two tags list the same 129 paths under the installable trees
(`git diff --name-status v2026.11.09 v2026.11.10` over them reports modifications only), so the derivation yields
the same 110 `files` for either; `origin/main`'s blob has no CR and is byte-equal to `json.dumps(indent=2,
ensure_ascii=False)` plus a newline. Precedent: `test/test_toolchain_integrity.py` reads `MANIFEST["release_tag"]`
instead of naming a tag.

### D1 — cuts that keep change.md under its cap after B1
Severity: D
Location: change.md § Files, `scripts/toolchain_manifest.py`; § Tasks 1.1
Defect: change.md is 7,959 of 8,000 B and B1 adds about 30 B; § Files restates an always-loaded rule; 1.1's
`SCRIPT` names no defined symbol since iteration 01's D1 cut its path expression.
Proposed-edit: in § Files replace "`files`; `coding-standards.md` applies. CLI" with "`files`. CLI"; in 1.1 replace
"A fixture asserts `SCRIPT.is_file()`, then loads the repository's `scripts/toolchain_manifest.py` with" with
"A fixture asserts the repository's `scripts/toolchain_manifest.py` is a file, then loads it with".

## Fix sites judged without finding

- B1 (iteration 01): prompt.md now writes `<dir>` / `<f>`; replaying `test/test_layout.py` `FRAMEWORK_PATH` and
  `resolves` over every file of the spec directory reports no miss. change.md § Tests reads "Test and tool paths".
- C1, AC-2 exit-2 case: the `clients/claude/README.md` entry is the right choice, and "one arbitrary entry" (the
  iteration-01 wording) was wrong. That README lies directly under `clients/claude`, outside every `<d>` of the
  mapping, so without its entry it is an unmapped source and the CLI exits 2; dropping an exact entry under a mapped
  tree instead (`src/payload/scripts/merge_steward.py`) adds a `files` entry, an exit-0 regeneration. The README is
  in both tags.
- C1, UB-2 pattern drop (`templates/config/*` against a synthetic release) and AC-4 "no CR byte": as proposed.
- C2: "exit 1 only when `--check` finds a difference, 2 on any tool error, git included" agrees with the AC-2 CLI
  case (exits 2).
- C3: `git ls-tree -r -z --name-only refs/tags/<tag> --` over the five trees runs for both tags (annotated tag
  objects, peeled to their trees), 129 NUL-terminated paths each.
- C4: the precedents exist — `scripts/ci_outage_mode.py` carries `# nosec B404` on `import subprocess` and
  `# nosec B603 B607` on the git call; `scripts/github_wrapper.py` calls
  `logging.basicConfig(level=logging.INFO, …)`.
- D1 (iteration 01): applied; change.md is 7,959 B, under the 8,000 B cap.
- Security lens: no change in the delta touches auth, secrets or input beyond C3's fixed argv. E2E not applicable
  stands.

## Coverage

| Criterion | Test (change.md § Tests) | Gap |
|---|---|---|
| AC-1 | derivation sets tag and date; update.txt step 7 and map text checks | default date untested (single value) |
| AC-2 | synthetic mapping, `templates/ci/*` drop, unmapped and collision raise, report; CLI exit 2, copy unchanged | none |
| AC-3 | `ast` imports within `sys.stdlib_module_names`; AC-4 reads the tag through git | tag vs HEAD listing indistinguishable (same path set); backstop `test/test_toolchain_integrity.py` |
| AC-4 | integration: parsed JSON, normalised text, no CR | pinned to v2026.11.09 (B1) |
| AC-5 | zero case, differing case byte-identical | pinned to v2026.11.09 (B1) |
| UB-1 | integrity and gate tests unmodified; AC-4 proves `files` | none |
| UB-2 | exact entry, deviation and pattern drops reported; others keep reason and order | none |

## Verdict

NOT-READY — NOT-CLEAN (0 A, 1 B)
