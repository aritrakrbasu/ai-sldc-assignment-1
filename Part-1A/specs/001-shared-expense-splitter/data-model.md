# Data Model: SplitEase

All money fields are integers in **paise**. All ids are positive integers assigned by storage.

## Group
| Field | Type | Rules |
|-------|------|-------|
| id | int | assigned |
| name | str | trimmed, 1–60 chars (FR-001) |
| created_at | str (ISO-8601 UTC) | assigned by storage, not used by core |
| members | list[Member] | 2–50, ordered (member order) |

## Member
| Field | Type | Rules |
|-------|------|-------|
| id | int | assigned |
| group_id | int | FK Group |
| name | str | trimmed, 1–40 chars, unique case-insensitively within group (FR-001) |
| position | int | 0-based member order; tie-break key everywhere (FR-008, FR-014) |

Members are immutable after group creation (spec Assumptions).

## Expense
| Field | Type | Rules |
|-------|------|-------|
| id | int | assigned |
| group_id | int | FK Group |
| description | str | trimmed, 1–120 chars |
| amount | int | 1 … 1,000,000,000 |
| paid_by | int | member id in group (`UNKNOWN_MEMBER`) |
| date | date | ISO `YYYY-MM-DD` |
| split_mode | enum | `EQUAL` \| `EXACT` \| `PERCENT` \| `SHARES` |
| splits | list[SplitInput] | ≥ 1, unique member ids (`DUPLICATE_PARTICIPANT`) |
| shares | dict[member_id → int] | computed by core; Σ = amount (FR-009) |
| seq | int | creation sequence (ordering tie-break for CSV) |

### SplitInput (per participant)
| Mode | Field used | Rules / error |
|------|-----------|---------------|
| EQUAL | — | n ≥ 1 |
| EXACT | `amount` int ≥ 0 | Σ = expense amount else `SPLIT_SUM_MISMATCH` |
| PERCENT | `percent` str `^\d{1,3}(\.\d{1,2})?$`, 0–100 | Σ = 100.00 else `PERCENT_SUM_INVALID` |
| SHARES | `weight` int ≥ 1 | else `INVALID_WEIGHT` |

Deletion: hard delete (FR-011).

## Settlement (immutable)
| Field | Type | Rules |
|-------|------|-------|
| id | int | assigned |
| group_id | int | FK Group |
| from_member | int | member in group |
| to_member | int | member in group, ≠ from_member (`SAME_MEMBER`) |
| amount | int | 1 … 1,000,000,000; may exceed current debt (clarification Q1) |
| date | date | ISO |
| seq | int | creation sequence |

No delete/update operation exists (clarification Q2).

## Derived (never stored)
- **Balance**: `member_id → int`, FR-012. Invariant Σ = 0 (FR-013).
- **Payment**: `{from_member, to_member, amount>0}`; plan per FR-014.

## Error codes (core)
`INVALID_MEMBERS`, `UNKNOWN_MEMBER`, `DUPLICATE_PARTICIPANT`, `SPLIT_SUM_MISMATCH`,
`PERCENT_SUM_INVALID`, `INVALID_WEIGHT`, `INVALID_AMOUNT`, `SAME_MEMBER`, `EMPTY_SPLIT`.
API-level: `GROUP_NOT_FOUND`, `EXPENSE_NOT_FOUND`, `VALIDATION_ERROR`.
