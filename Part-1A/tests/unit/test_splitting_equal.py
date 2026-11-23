"""T013 [US1] — EQUAL split. FR-004, FR-009, FR-010."""

import pytest

from splitease.core.errors import DomainError
from splitease.core.model import Member, SplitInput
from splitease.core.splitting import compute_shares

ASHA, BILAL, CHEN = 1, 2, 3
MEMBERS = [Member(ASHA, "Asha", 0), Member(BILAL, "Bilal", 1), Member(CHEN, "Chen", 2)]


def eq(*ids):
    return [SplitInput(member_id=i) for i in ids]


def test_us1_2_fr004_100000_among_three_remainder_to_first_in_member_order():
    shares = compute_shares(MEMBERS, 100000, ASHA, "EQUAL", eq(ASHA, BILAL, CHEN))
    assert shares == {ASHA: 33334, BILAL: 33333, CHEN: 33333}


def test_fr004_remainder_follows_member_order_not_input_order():
    shares = compute_shares(MEMBERS, 100000, ASHA, "EQUAL", eq(CHEN, BILAL, ASHA))
    assert shares == {ASHA: 33334, BILAL: 33333, CHEN: 33333}


def test_fr004_remainder_two_paise():
    shares = compute_shares(MEMBERS, 100001, ASHA, "EQUAL", eq(ASHA, BILAL, CHEN))
    assert shares == {ASHA: 33334, BILAL: 33334, CHEN: 33333}


def test_us1_3_payer_not_participant():
    shares = compute_shares(MEMBERS, 90000, ASHA, "EQUAL", eq(BILAL, CHEN))
    assert shares == {BILAL: 45000, CHEN: 45000}
    assert shares.get(ASHA, 0) == 0


def test_edge_one_paisa_among_three():
    shares = compute_shares(MEMBERS, 1, ASHA, "EQUAL", eq(ASHA, BILAL, CHEN))
    assert shares == {ASHA: 1, BILAL: 0, CHEN: 0}


def test_fr009_single_participant_gets_all():
    assert compute_shares(MEMBERS, 777, BILAL, "EQUAL", eq(CHEN)) == {CHEN: 777}


def test_fr010_unknown_participant_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 100, ASHA, "EQUAL", eq(ASHA, 99))
    assert exc.value.code == "UNKNOWN_MEMBER"


def test_fr010_unknown_payer_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 100, 42, "EQUAL", eq(ASHA))
    assert exc.value.code == "UNKNOWN_MEMBER"


def test_fr010_duplicate_participant_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 100, ASHA, "EQUAL", eq(ASHA, ASHA))
    assert exc.value.code == "DUPLICATE_PARTICIPANT"


def test_fr010_empty_split_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 100, ASHA, "EQUAL", [])
    assert exc.value.code == "EMPTY_SPLIT"


def test_fr003_invalid_amount_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 0, ASHA, "EQUAL", eq(ASHA))
    assert exc.value.code == "INVALID_AMOUNT"


def test_unknown_mode_rejected():
    with pytest.raises(DomainError) as exc:
        compute_shares(MEMBERS, 100, ASHA, "HALF", eq(ASHA))
    assert exc.value.code == "INVALID_SPLIT_MODE"
