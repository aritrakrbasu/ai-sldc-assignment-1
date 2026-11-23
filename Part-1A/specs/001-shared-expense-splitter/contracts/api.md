# API Contract: SplitEase v1

Base path `/api`. JSON in/out, UTF-8. Money = integer paise. Errors:
`{"error": {"code": "<CODE>", "message": "<text>"}}` (422 adds `"details"`).

| # | Method & path | Request | Success | Errors |
|---|---------------|---------|---------|--------|
| C1 | `POST /api/groups` | `{name, members: [str]}` | 201 `Group` | 422 VALIDATION_ERROR; 400 INVALID_MEMBERS |
| C2 | `GET /api/groups` | — | 200 `[{id, name, member_count}]` (id asc) | — |
| C3 | `GET /api/groups/{gid}` | — | 200 `GroupDetail` | 404 GROUP_NOT_FOUND |
| C4 | `POST /api/groups/{gid}/expenses` | `ExpenseIn` | 201 `Expense` (with `shares`) | 404 GROUP_NOT_FOUND; 400 UNKNOWN_MEMBER, DUPLICATE_PARTICIPANT, SPLIT_SUM_MISMATCH, PERCENT_SUM_INVALID, INVALID_WEIGHT, EMPTY_SPLIT; 422 |
| C5 | `DELETE /api/groups/{gid}/expenses/{eid}` | — | 204 | 404 GROUP_NOT_FOUND / EXPENSE_NOT_FOUND |
| C6 | `POST /api/groups/{gid}/settlements` | `{from_member, to_member, amount, date}` | 201 `Settlement` | 404; 400 UNKNOWN_MEMBER, SAME_MEMBER; 422 |
| C7 | `GET /api/groups/{gid}/balances` | — | 200 `[{member_id, name, balance}]` (member order) | 404 |
| C8 | `GET /api/groups/{gid}/settle-up` | — | 200 `[{from_member, to_member, amount}]` | 404 |
| C9 | `GET /api/groups/{gid}/export.csv` | — | 200 `text/csv`, `Content-Disposition: attachment` | 404 |
| — | `DELETE /api/groups/{gid}/settlements/{sid}` | — | **405** (not offered, clarification Q2) | — |

## Schemas
```text
Group        = {id, name, members: [{id, name, position}]}
GroupDetail  = Group + {expenses: [Expense], settlements: [Settlement],
                         balances: [Balance], settle_up: [Payment]}
ExpenseIn    = {description: str(1..120), amount: int(1..1e9), paid_by: int,
                date: "YYYY-MM-DD", split_mode: "EQUAL"|"EXACT"|"PERCENT"|"SHARES",
                splits: [{member_id: int, amount?: int>=0, percent?: "dd.dd", weight?: int>=1}]}
Expense      = ExpenseIn + {id, shares: [{member_id, amount}]}
Settlement   = {id, from_member, to_member, amount, date}
Balance      = {member_id, name, balance}
Payment      = {from_member, to_member, amount}
```

## CSV (C9)
Header: `date,type,description,paid_by,amount_inr,split_mode,participants`
- `type` = `expense` | `settlement`; settlements: description `Settlement to <name>`,
  `split_mode` empty, `participants` = receiver name.
- `participants` = `Name:amount_inr` joined by `;` in member order.
- Rows ordered by (`date`, creation sequence across both entry types).
- `amount_inr` formatted `"{paise//100}.{paise%100:02d}"`.
- Text cells starting with `= + - @` prefixed `'` (FR-017).

## UI contract (FR-020)
Single page at `/`: group list + create form; group view with tabs/panels: Add expense (mode
selector), Expenses list (delete), Balances, Settle up (+ "Record" button per payment),
Record settlement form, Export CSV link. Errors from the API are shown verbatim (`message`).
