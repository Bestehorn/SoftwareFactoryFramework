# Lessons Learned → mechanical memory

When the user corrects you, or a run hits a failure worth remembering:
1. Prefer a MECHANISM over prose: a test, a hook check, a lint rule, a one-line rule statement. A
   lesson a test enforces cannot recur; a lesson in prose recurs the day the prose is not read.
2. If prose is still needed, append ONE entry of at most five lines to `docs/lessons-learned.md`
   (`python scripts/memory_compile.py lesson add --lesson L --enforced-by X --scope S` writes it):
   `## <YYYY-MM-DD> — <one-line lesson>`, then `- Lesson: <one sentence>`,
   `- Enforced-by: <test path | hook | rule file | none>`, `- Scope: <component>`.
   An incident narrative goes to `docs/archive/incidents/<date>-<slug>.md`, never here.
3. Apply the lesson to the current task immediately.
4. An entry older than six weeks with `Enforced-by: none` is compiled by `/compile-memory`:
   enforced, or archived to `docs/archive/`. The file is capped at 40,000 bytes
   (`test/test_instruction_corpus_budget.py`). Grep it for the component you touch; never read it
   whole.
