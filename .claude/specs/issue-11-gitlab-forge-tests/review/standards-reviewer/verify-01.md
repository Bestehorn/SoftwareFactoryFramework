# Standards review — VERIFY 01 (implemented diff 83a1415..HEAD, src test .github docs)

No A or B finding. Facts behind that result:
- `ruff check` and `ruff format --check` on all 15 changed Python files: `All checks passed!`, `15 files already
  formatted`. That covers E501 at 120 columns and the py39 target. CI run 45033382186 passed lint, types, security
  and tests on c389d46, and since c389d46 only `docs/findings-ledger.md` changed under these paths.
- No path listed in `config/toolchain.json` `files` is in the diff. That file records `.github/workflows/ci.yml` as
  the project's own.
- `src/` stays standard-library only.
- `GitLabProjectRefusedError` is a `GitLabAPIError`, so it gets `details=None` from the base.
- The marker guard copies `github_wrapper.py`'s `_test_marker_set` pattern and its values.
- The one environment read, `os.getenv(key=..., default="")`, is the same as `test/forge/write_credential.py` in #10.
- No module skips or xfails a test.
- `test/test_forge_suite_layout.py` keeps its exact `needs` comparison and only adds `forge-gitlab` to it.
- The four new ledger rows are 223 to 230 B each, under the 240 B row limit. The map is 9,292 B, under its
  40,000 B cap.

### C1 — Regex and `ast` calls in the new files pass positional arguments, which rule 4's wording forbids
Severity: C
Location: `test/test_forge_gitlab_layout.py` module constants (`GITLAB_SECRET_REFERENCE` to `MARKDOWN_FENCE`) and
  `assert_fails_unless_gitlab_forge_succeeded`, `gitlab_fixture_loads`, `markdown_headings`,
  `uncalled_record_problems`, `other_constants_naming` and the `test_the_*` bodies; `test/test_forge_gitlab_support.py`
  `EPHEMERAL_PATH_FORM`, `RUN_ID_PATTERN`; `test/forge_gitlab/ephemeral.py` `NOT_FOUND_ANSWER`, `BAD_REQUEST_ANSWER`
Defect: `coding-standards.md` rule 4 says "Named parameters at all call sites". These new call sites pass a positional
  argument to functions that also accept it by keyword:
  - `re.compile(r"...")` and `re.escape(X)`
  - `Pattern.match(line)`, `.search(text)` and `.findall(text)`
  - `ast.walk(tree)`

  The same files already use the keyword form elsewhere: `re.compile(pattern=...)` in `REASON_*`,
  `NOT_FOUND_ANSWER.search(string=stderr)`, `RUN_ID_PATTERN.fullmatch(string=...)`. Whether the rule applies to these
  calls is unclear, because the merged suites these files extend use the positional form:
  - `test/test_forge_suite_layout.py` (#10, which this lane passed): 37 sites of `re.compile(r`, `re.escape` and
    `ast.walk`, plus positional `.match`, `.search` and `.findall` calls
  - `test_gitlab_graphql_contract.py`, `test_gitlab_wrapper_contract.py`, `test_gitlab_wrapper_coverage.py`,
    `test_gitlab_api_properties.py`, `test_setup_prompts_gitlab_wrapper.py`: 42 sites between them
Material-because: unmaintainable-by-rule `coding-standards.md` (rule 4) — the rule's text and the repository's merged
  practice disagree, so this is graded C, not B.
Proposed-edit: in the files named above:
  - `re.compile(r"...")` becomes `re.compile(pattern=r"...")`
  - `re.escape(X)` becomes `re.escape(pattern=X)`
  - `P.match(x)`, `P.search(x)` and `P.findall(x)` become `P.match(string=x)`, `P.search(string=x)` and
    `P.findall(string=x)`
  - `ast.walk(tree)` becomes `ast.walk(node=tree)`

  Positional-only builtins and C methods (`len`, `isinstance`, `getattr`, `str.join`, `str.replace`, `dict.get`,
  `dict.pop`, `datetime.strptime`, `functools.partial`, `st.builds`, `Match.group`) stay as they are. The
  repository-wide question goes to one findings-ledger row and is not fixed in this change.

### D1 — The `errors.py` module docstring's exit-code sentence does not read
Severity: D
Location: `src/payload/scripts/gitlab_api/errors.py` module docstring
Defect: "still maps any of them to exit code 1, but ``GitLabProjectRefusedError``, which it maps to 2" uses "but" where
  it means "except".
Material-because: wording.
Proposed-edit: "so ``gitlab_wrapper.py`` still maps each of them to exit code 1, except ``GitLabProjectRefusedError``,
  which it maps to 2."

CLEAN

Counts: A 0, B 0, C 1, D 1

Verdict: READY
