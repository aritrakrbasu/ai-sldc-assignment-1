# API Contract: MoneyLens v1

Base `/api`. JSON. Errors: `{"error": {"code", "message"}}`. Schema errors return 422
`VALIDATION_ERROR`.

| # | Method & path | Request | Success | Errors |
|---|---------------|---------|---------|--------|
| M1 | `POST /api/parse` | `{messages: [str] (1..50), reference_date?: "YYYY-MM-DD", save?: bool=true}` | 200 `{results: [ParseResult]}` (schema `parse_result.schema.json`) | 400 `INVALID_BATCH`; 422 |
| M2 | `GET /api/dashboard?from=&to=` | default this month to date | 200 `{from, to, by_category:[{category, value_paise, count}], total_debit_paise, total_credit_paise, recent:[Txn]}` | 422 |
| M3 | `GET /api/transactions?limit=` | — | 200 `[Txn]` newest first | — |
| M4 | `POST /api/ask` | `{question: str (1..300), reference_date?}` | 200 `QueryResult` (`query_result.schema.json`) | 422 |
| M5 | `GET /api/splitease/groups` | — | 200 proxied SplitEase group list | 502 `SPLITEASE_UNAVAILABLE` |
| M6 | `GET /api/splitease/groups/{gid}` | — | 200 `{id, name, members}` | 502 / pass-through 404 |
| M7 | `POST /api/transactions/{tid}/split` | `{group_id, paid_by, participants:[int], confirm: bool}` | 200 `{status:"preview", payload}` when confirm=false; 201 `{status:"created", splitease_expense_id}` when confirm=true | 404 `TRANSACTION_NOT_FOUND`; 400 `NOT_A_DEBIT`, `ALREADY_SHARED`; 502 `SPLITEASE_UNAVAILABLE`; 4xx pass-through SplitEase code |
| M8 | `GET /api/health` | — | 200 `{model, model_configured: bool, prompt_versions}` (never the key) | — |

`Txn = {id, amount_paise, direction, merchant, account_last4, txn_date, channel, category,
masked_text, shared_expense_id}`

The spec's "confirmation required" (US5-1) appears as `status: "preview"` with code
`CONFIRMATION_REQUIRED` in the body: `{status:"preview", code:"CONFIRMATION_REQUIRED", payload}`.

## UI contract
One page with three tabs: **Inbox** (paste textarea, upload `.txt`, Parse button, result cards
with kind badge; phishing cards red with reasons and no split action), **Dashboard** (date
range, category bars, totals, recent list; each stored DEBIT has a "Split in SplitEase" button
that opens a dialog with group/payer/participants, a Preview and a "Confirm and send" button) and **Ask**
(question box, interpreted filters, computed answer or clarification).

_Revision 2026-11-23 (during implementation, before first evaluation):_ the split button moved
from Inbox cards to stored transactions on the Dashboard. `ParseResult` (schema,
`additionalProperties: false`) has no stored-transaction id, and a split needs one (M7).
