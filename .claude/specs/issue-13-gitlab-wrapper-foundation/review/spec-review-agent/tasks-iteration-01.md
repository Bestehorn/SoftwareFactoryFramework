# Tasks review, iteration 01, lane spec-review-agent (issue #13, tier M)

The author's flagged conventions, judged:

- Empty `__init__.py` markers not counted: accepted. Each marker has one owning task (1.4: `gitlab_api/`,
  `families/`; 3.12: `commands/`). No other task in that wave writes it, and it lands no later than the first module
  of its package. D2 lists all three as never edited afterwards.
- Test modules written across several waves: accepted. R (1.1, 2.2), P (1.2, 2.3), V (1.3, 3.1) and C (3.2, 4.1,
  5.1) each have exactly one owner per wave, and disjointness is a per-wave rule. Each later case needs only code from
  its own wave or an earlier one. `test_script_without_config_exits_1` correctly waits for Wave 4: D7 parses before it
  loads the config, and no subcommand parses before `commands/issue.py` exists.
- F.2 with `Files: none`: accepted. design.md gives UB-3 "verifier evidence" and AC-1.3 "review" as their oracles, and
  F.2 is where they enter a TEST task's `Validates:`. Its second clause checks AC-1.3 and adds no scope. Every file the
  plan creates under `gitlab_api/` matches a row of D2's "What a family's change edits" table.

### C1 — The registry tests that look up records run before any family has a record, and the tasks do not say where their records come from
Severity: C
Location: tasks.md § Wave 2, 2.2; § Wave 1, 1.1 (`test_lookup_refuses_unknown_and_duplicate_ids`)
Defect: Family modules first appear in Wave 3, and `graphql_only.OPERATIONS` is empty. D5's `lookup(operation_id)`
and `call(transport, operation_id, *, values=None)` take no `package=` argument. If 2.2 is written with a real id
(`plan#create-an-issue`), it goes green in Wave 2 on `lookup`'s unknown-id `ValueError`, not on `encode`'s
undeclared-value `ValueError`. The duplicate case in 1.1 has no second record to collide with.
Proposed-edit: append to 2.2, and to 1.1 after `test_lookup_refuses_unknown_and_duplicate_ids`: "— the records are
synthetic `RestOperation`s that the test makes `lookup` see by monkeypatching `registry.discover_families`, so the
refusal the test checks is the one it names."

### C2 — P's AC-2.3 property parses "the encoded query" in a wave where no product code joins pairs into a query
Severity: C
Location: tasks.md § Wave 1, 1.2 (`test_array_and_hash_pairs`); design.md § Correctness Properties, AC-2.3
Defect: The oracle is `parse_qsl` of the encoded query. D4 names the join
(`urlencode(pairs, safe="[]", quote_via=quote)`) only inside `Transport.request`, which 2.4 builds in Wave 2. So a
1.2 that reaches the query through `Transport` cannot go green in Wave 1.
Proposed-edit: in 1.2, after `test_array_and_hash_pairs`, add: "(over `registry.encode`'s pairs joined with
`urllib.parse.urlencode(pairs, safe="[]", quote_via=urllib.parse.quote)`, the join D4 names)".

### D1 — "Part 6.2" in 5.5 names two different sections
Severity: D
Location: tasks.md § Wave 5, 5.5
Defect: `prompts/setup-claude.txt` has its own `### Part 6.2 — Event-driven automation → settings.json hooks`. The
copy step D2 means is `prompts/setup-kiro.txt` Part 6.2.
Proposed-edit: "D2's install path — `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` Part 6.2 copy
`src/payload/scripts/gitlab_api/` with the entry script, …".

CLEAN
