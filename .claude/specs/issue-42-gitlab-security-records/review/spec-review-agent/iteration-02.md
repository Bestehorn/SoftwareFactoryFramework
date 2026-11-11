# spec-review-agent — iteration 02 (tier S, combined, DELTA)

Scope: iteration 01's fix sites, the text they changed, DL-005 to DL-007 and the #42 correction. change.md is 7,970 B
(cap 8,000); Residuals 8 lines (cap 10). No acceptance-criterion or unchanged-behaviour id was added (AC-1 to AC-7,
UB-1 to UB-4, as in iteration 01).

## Fix sites

| Finding | Site | Applied | Evidence |
|---|---|---|---|
| A1 | change.md AC-5 | verbatim | the proposed AC-5 text |
| A1 | Tests AC-5 | "AC-5's set;" | Tests § AC-5 |
| A1 | DL-006 | supersedes DL-004's paging rule | decision-log DL-006 |
| B1 | change.md AC-4 | verbatim | `rest/software-supply-chain-security.md` `#create-a-user` (`POST /users`) and `#modify-a-user` (`PUT /users/:id`) each have an `avatar` body row; both keys are on `PENDING` |
| B1 | DL-006 | supersedes DL-004's avatar exception | decision-log DL-006 |
| B2 | DL-005 | supersedes only DL-002's administrator clause; the Ask still cites DL-002 for downloads | decision-log DL-005, DL-002 |
| B2 | Ask; Residuals second bullet | verbatim | change.md § Ask, § Residuals |
| B2 | #42 comment | posted | comment 6789018796 (06:41:19Z): "DL-005 supersedes DL-002's \"records of their own\"; a findings-ledger row records them" |
| C1 | Residuals last bullet | "(the `DELETE`'s URL and error)" | change.md § Residuals |
| C2 | Tests AC-7 | "(four modules)" | still true after A1, below |
| D1 | Files "Nothing else"; Residuals first bullet | both deletions applied; DL-007 carries the citation | docs.gitlab.com/api/policy_store version history, GitLab 19.4: "changed to persist policies to the database" |

## The edited text, checked: no finding

- **AC-5's three IDs.** Each names exactly one section across the five `rest/` files, and each is a single-endpoint
  `GET`: `security-factory.md` `#list-all-project-security-settings`, `software-supply-chain-security.md`
  `#list-all-token-associations`, `security-risk-management.md` `#retrieve-project-external-status-check-services`
  (path `id` only, so its AC-7 case needs no other value).
- **"(four modules)" after A1.** `security_factory` keeps two `Paging.OFFSET` records (`#list-project-dependencies`,
  `#list-all-license-templates`). `software_supply_chain_security`, `security_risk_management` and `security_platform`
  keep "List" `GET`s. `security_governance`'s only section is a `PUT`. Four modules have an AC-7 case and none is
  parametrized over nothing.
- **`#list-all-token-associations` as `Paging.NONE`.** Its section has `page` and `per_page` query rows, so AC-3
  gives it those `Param`s and a caller asks for page N with `-f page=N`. Under `Paging.OFFSET`, `transport` raises on
  the object answer. `NONE` is the only paging that answers.
- **`FILE` on a `BodyFormat.JSON` record.** `registry.py` `BodyFormat` says "any FILE value makes the body multipart
  instead", and `transport` builds `multipart/form-data`. `#update-application-appearance` and `#create-a-secure-file`
  use the same path, and iteration 01 passed them.
- **Residuals second bullet.** `-1`'s key `GET /users/:id` is mapped by AC-1's
  `#retrieve-a-single-user-as-a-regular-user`, and its only row `id` is that section's own row, so it needs no record.
  "N refuses their rows" holds for `#as-an-administrator` (`extern_uid`, `order_by`) and `-2` (`sudo`).
- **Decision log against change.md.** DL-005 matches the Ask and Residuals. DL-006 matches AC-4 and AC-5. DL-007
  matches Files "Nothing else". No two entries in force contradict each other.

## Coverage (rows the delta touched)

| Criterion | Test | Fails when |
|---|---|---|
| AC-4 | F `test_every_kind_is_its_rows_type` | `avatar` on `#create-a-user`, `#modify-a-user` or `#upload-an-avatar-for-yourself` is not `FILE` |
| AC-5 | F `test_every_list_record_has_a_case` | either object-answer ID is `OFFSET`, or `#retrieve-project-external-status-check-services` is `NONE` |
| AC-7 | F `test_a_list_record_prints_every_item` (four modules) | a page-two item is missing (red: exit 2) |

Findings: none.

Verdict: READY
