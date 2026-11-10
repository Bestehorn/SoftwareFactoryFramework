# Standards review — iteration 03 (delta) — issue #13 (tier M)

Fix sites from iteration 02:

- B1 is closed. D2 lists `test_gitlab_api_transport.py` (`transport.py`) and `test_gitlab_api_registry.py`
  (`registry.py`), the same split #17 uses. Testing Strategy names both. The Mapping defines R and lists under R
  AC-1.1's two tests, AC-2.2's `test_project_path_is_encoded` and `test_empty_and_dot_segments_are_refused`, and
  AC-2.3's `test_array_of_hashes_pairs`. In the D2 table, the `transport.py` and `registry.py` rows each name their own
  test module. The `test_gitlab_*.py` glob in Residuals covers the new file. No stem under
  `docs/api-reference/gitlab/rest/` is `transport` or `registry`, so no per-family `test_gitlab_api_<family>.py` can
  collide with these two.
- C1 is closed. § Existing patterns followed now gives each `FIELD_*` key one owner, as proposed.
- C2 is closed. Data flow calls `registry.call(transport=…, operation_id=…, values=…)`, and the patterns sentence reads
  "named arguments at every call site (`coding-standards.md` item 4)".
- C3 is closed. The sentences D2 quotes appear word for word in `prompts/setup-claude.txt` Part 5.3 ("The wrapper
  templates are skeletons; …", "See the expanded docstrings …", "(See the wrapper docstrings.)") and in
  `prompts/setup-kiro.txt` Part 6.2 ("The template wrapper scripts are skeletons. …", "the template docstrings specify
  them"). The setup-kiro APPENDIX "Standard directory structure" has the `gitlab_wrapper.py # if GitLab` line that D2
  extends with `gitlab_api/`.

New text checked against `.claude/rules/`:

- Named arguments: `discover_families(*, package=…)`, `Transport.from_config(config=…)`,
  `steward_delegate(verb=…, …, host="gitlab")`, `Request(url=url)` and `st.characters(exclude_categories=…)` are all
  named. `secrets.token_hex(16)` and `parse_qsl(query, keep_blank_values=True)` pass a standard-library function's
  first argument by position. The shipped scripts do the same (`json.dumps(payload)` and
  `time.sleep(interval_seconds)` in `src/payload/scripts/gitlab_wrapper.py`, `urllib.parse.quote(label)` in
  `merge_steward.py`), so this is not a finding.
- Constants: `CREDENTIAL_HEADERS` and `MAX_PER_PAGE` are named constants, each `FIELD_*` key has one owner, and the
  default ports are taken from `http.client`'s `default_port`.
- Dependencies: `hypothesis` is in the `pyproject.toml` `dev` extra.
- Exceptions: the new refusals (a non-integer port, a `Location` `ValueError`) raise `GitLabAPIError`.

### D1 — Eight prose lines are longer than the 120 columns the rest of design.md keeps
Severity: D
Location: design.md § D2 "Family module contract"; § D4 `pages` and GraphQL bullets; § D7 `_load_config`; § D8
synthetic-package bullet; § Testing Strategy "Framework tests"; § Correctness Properties AC-2.3, AC-3.1
Defect: Each of these sections has one prose line longer than 120 characters. Every other prose line of design.md
wraps at 120 (table rows are excluded).
Material-because: wording only. `coding-standards.md` item 7 applies to Python through ruff, not to Markdown.
Proposed-edit: rewrap those paragraphs at 120 columns without changing the text.

CLEAN
