"""T015 [US1] — group/member validation. FR-001."""

import pytest

from splitease.core.errors import DomainError
from splitease.core.groups import validate_group_name, validate_members


def test_fr001_members_trimmed_order_kept():
    assert validate_members(["  Asha ", "Bilal", "Chen"]) == ["Asha", "Bilal", "Chen"]


def test_fr001_two_members_minimum_ok():
    assert validate_members(["A", "B"]) == ["A", "B"]


def test_fr001_fifty_members_ok():
    names = [f"M{i}" for i in range(50)]
    assert validate_members(names) == names


@pytest.mark.parametrize(
    "names",
    [["Solo"], [f"M{i}" for i in range(51)], ["Asha", "asha"], ["Asha", " Asha "], ["A", ""],
     ["A", "   "], ["A", "x" * 41], []],
)
def test_fr001_invalid_members(names):
    with pytest.raises(DomainError) as exc:
        validate_members(names)
    assert exc.value.code == "INVALID_MEMBERS"


def test_fr001_member_name_40_chars_ok():
    assert validate_members(["x" * 40, "y"]) == ["x" * 40, "y"]


def test_fr001_group_name_trimmed():
    assert validate_group_name("  Goa Trip ") == "Goa Trip"


@pytest.mark.parametrize("name", ["", "   ", "g" * 61])
def test_fr001_invalid_group_name(name):
    with pytest.raises(DomainError) as exc:
        validate_group_name(name)
    assert exc.value.code == "INVALID_GROUP_NAME"


def test_fr001_group_name_60_ok():
    assert validate_group_name("g" * 60) == "g" * 60
