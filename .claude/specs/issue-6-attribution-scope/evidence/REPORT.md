# Evidence report — issue #6: no-ai-attribution states one scope

Tier S, one wave (T1, I1; both reopened once). Branch `issue-6-attribution-scope`.

| Criterion | Test (`test/test_no_ai_attribution_rule.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 one scope: attribution of work to a tool, and names you author | `test_ac1_opening_paragraph_states_one_scope[claude|kiro]` | red/wave-1.txt; green/wave-1.txt | green |
| AC-2 naming a path, command, setting or product as the subject is permitted in messages | `test_ac2_body_permits_a_path_or_product_named_as_the_subject[*]` | red; green | green |
| AC-3 opening and self-check state the same scope; no blanket ban | `test_ac3_self_check_states_the_opening_scope[*]`, `test_ac3_no_sentence_bans_the_listed_words_in_every_message[*]` | red; green | green |
| AC-4 the Kiro twin (8.28) carries the same scope and allowance | `test_ac4_kiro_body_carries_the_scope_the_allowance_and_the_agreement` | red; green | green |
| UB-1 trailers and tool attribution still forbidden | `test_ub1_body_still_forbids_attribution_trailers[*]` | green | green |
| UB-2 authored names still exclude the words; the allowance never reaches a name | `test_ub2_*` (auto-name, word list, message domain + guard, self-check limited to messages) | red/wave-1-reopen.txt; green | green |
| UB-3 restatements state attribution and names only | `test_ub3_*` (four setup-claude anchors; work-issue, auto-work, both orchestrator bodies incl. their name clauses) | red; green | green |

Green capture (`# tasks: T1 I1`): the module with `test/test_layout.py`, 85 passed.

**Verifier.** First pass REFUTED UB-2 and UB-3 (the allowance's message domain, its never-a-name guard and the restatements' name clauses had no test; the self-check's allowance sentence was not limited to messages). T1 and I1 were reopened; re-verification VERIFIED (`verify/refutation-report.md`).

**Whole suite.** The CI run on the pushed head SHA (target: one run).

**Release item.** The installed `.claude/rules/no-ai-attribution.md` changes at the release and promotion this run cuts.
