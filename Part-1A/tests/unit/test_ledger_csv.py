"""T039 [US6] — CSV export. FR-016, FR-017, SC-006 (contract C9 format)."""

from splitease.core.ledger_csv import build_csv
from splitease.core.model import Expense, Member, Settlement

MEMBERS = [Member(1, "Asha", 0), Member(2, "Bilal", 1), Member(3, "Chen", 2)]


def ledger():
    e1 = Expense(id=10, description="Groceries", amount=100000, paid_by=1, date="2026-11-02",
                 split_mode="EQUAL", shares={1: 33334, 2: 33333, 3: 33333}, seq=2)
    e2 = Expense(id=11, description="Cab, airport", amount=50000, paid_by=2, date="2026-11-01",
                 split_mode="EXACT", shares={3: 30000, 2: 20000}, seq=1)
    s1 = Settlement(id=5, from_member=2, to_member=1, amount=33333, date="2026-11-02", seq=3)
    return [e1, e2], [s1]


EXPECTED = (
    "date,type,description,paid_by,amount_inr,split_mode,participants\r\n"
    '2026-11-01,expense,"Cab, airport",Bilal,500.00,EXACT,Bilal:200.00;Chen:300.00\r\n'
    "2026-11-02,expense,Groceries,Asha,1000.00,EQUAL,Asha:333.34;Bilal:333.33;Chen:333.33\r\n"
    "2026-11-02,settlement,Settlement to Asha,Bilal,333.33,,Asha\r\n"
)


def test_us6_1_fr016_exact_csv():
    expenses, settlements = ledger()
    assert build_csv(MEMBERS, expenses, settlements) == EXPECTED


def test_sc006_deterministic_regardless_of_input_order():
    expenses, settlements = ledger()
    assert build_csv(MEMBERS, list(reversed(expenses)), settlements) == EXPECTED


def test_header_only_when_empty():
    assert build_csv(MEMBERS, [], []) == (
        "date,type,description,paid_by,amount_inr,split_mode,participants\r\n"
    )


def test_us6_2_fr017_formula_injection_neutralised():
    for prefix in "=+-@":
        e = Expense(id=1, description=f"{prefix}HYPERLINK(\"x\")", amount=100, paid_by=1,
                    date="2026-11-01", split_mode="EQUAL", shares={1: 100}, seq=1)
        out = build_csv(MEMBERS, [e], [])
        row = out.split("\r\n")[1]
        assert f"'{prefix}HYPERLINK" in row, row


def test_fr017_member_name_formula_neutralised():
    members = [Member(1, "=cmd", 0), Member(2, "B", 1)]
    e = Expense(id=1, description="ok", amount=100, paid_by=1, date="2026-11-01",
                split_mode="EQUAL", shares={1: 50, 2: 50}, seq=1)
    row = build_csv(members, [e], []).split("\r\n")[1]
    assert row == "2026-11-01,expense,ok,'=cmd,1.00,EQUAL,'=cmd:0.50;B:0.50"
