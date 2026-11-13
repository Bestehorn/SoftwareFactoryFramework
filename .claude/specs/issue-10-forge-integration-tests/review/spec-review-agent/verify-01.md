# VERIFY 01 — spec-review-agent (intent and internal consistency), issue #10, diff 590e4a9..59d5928

The code was checked against the approved design (D1–D10, as DL-003 to DL-005 restate it), one criterion at a time.
The wrapper guard (`_test_marker_set`, `_refuse_unless_ephemeral`, called in `main` after `_detect_repo` and before
`steward_delegate` and `_run_command`), the D5 YAML, the D3 helper snippet, every D9 step and guard, the D6 table rows
and the D8 lookup, read and write all match the design text. The signatures match too: `provision`,
`EphemeralRepository`'s ten fields, `WrapperRunner.run`, `GitRunner.run`, `delete_ephemeral`, the sweep functions,
`credential_helper_arguments`, `find_test_credential`, `read_test_token`, `write_test_credential`. The contracts hold:
the fixture binds both runners to `workspace / CLONE_DIRECTORY`, which is the clone `provision` prepares, and the sweep
runs after `prepare_clone`, so the guard reads a `sff-test-*` origin. The CI step and the suite resolve the same
`CHECKOUT` test credential file. Every test the Correctness Properties name exists. Neither finding below gates.

### C1 — A creation that exits 0 without a readable record leaves the repository to the sweep
Severity: C
Location: test/forge/ephemeral.py § `create_ephemeral`, `provision` (AC-1.4, AC-2.3)
Defect: when `call repos/create-in-org` exits 0 but `Invocation.json` or `_created_record` raises `ForgeCommandError`,
`provision` leaves `created` as `None`. The teardown then sends no deletion even though the repository exists, and
only a sweep more than a day later removes it (AC-3.1).
Material-because: not observed. `call` prints the answer with `print_json`, and GitHub documents `owner.login`,
`name` and `default_branch` in the 201 answer. This is a residual, not a defect of this change.
Proposed-edit: none in this change; add one findings-ledger row ("forge provision: a creation that exits 0 with an
unreadable answer is not deleted by the teardown; the sweep removes it after a day").

### D1 — The map names the wrong mechanism for keeping the forge suite out of the default collection
Severity: D
Location: docs/forLLMConsumption.md § Testing, the forge-suite bullet (AC-9.2; design D1 "The default collection")
Defect: the text says "its own `pytest.ini` keeps it out of the default collection". The default collection reads
`pyproject.toml` and never `test/forge/pytest.ini`. What keeps the forge modules out is their `forge_*.py` names,
which no default `python_files` pattern matches (D1). A reader who believes the map could add a `test_*.py` under
`test/forge/` that the `verify` leg `tests` would then collect.
Material-because: wording.
Proposed-edit: replace "its own `pytest.ini` keeps it out of the default collection" with "its modules are named
`forge_*.py`, which the default `python_files` never matches, and only its own `pytest.ini` collects them".

CLEAN
