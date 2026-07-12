from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_HALF_UP

import pytest

from domain import (
    CurrencyCode,
    CurrencyMismatchError,
    InvalidMoneyError,
    Money,
    currency_specification,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10", Decimal("10.00")),
        ("10.2", Decimal("10.20")),
        (10, Decimal("10.00")),
        (Decimal("10.20"), Decimal("10.20")),
        ("-0.01", Decimal("-0.01")),
    ],
)
def test_strict_construction(raw, expected):
    assert Money.of(raw).amount == expected


@pytest.mark.parametrize(
    "invalid",
    [10.2, True, "", "NaN", "Infinity", object()],
)
def test_invalid_construction_is_rejected(invalid):
    with pytest.raises(InvalidMoneyError):
        Money.of(invalid)


def test_excess_precision_is_rejected():
    with pytest.raises(InvalidMoneyError):
        Money.of("1.001")


def test_explicit_rounding():
    assert Money.rounded(
        "1.005",
        rounding=ROUND_HALF_UP,
    ) == Money.of("1.01")


def test_default_rounding_can_be_used_explicitly():
    assert Money.rounded("1.005") == Money.of("1.00")


def test_zero_factory():
    assert Money.zero() == Money.of("0.00")


@pytest.mark.parametrize(
    ("minor_units", "amount"),
    [(1234, "12.34"), (-1, "-0.01"), (0, "0.00")],
)
def test_minor_unit_roundtrip(minor_units, amount):
    money = Money.from_minor_units(minor_units)
    assert money == Money.of(amount)
    assert money.minor_units == minor_units


def test_addition_and_subtraction():
    assert Money.of("10.00") + Money.of("2.50") == Money.of("12.50")
    assert Money.of("10.00") - Money.of("2.50") == Money.of("7.50")


def test_multiplication_exact():
    assert Money.of("2.50") * 4 == Money.of("10.00")
    assert 4 * Money.of("2.50") == Money.of("10.00")


def test_multiplication_requires_explicit_rounding():
    with pytest.raises(InvalidMoneyError):
        Money.of("0.01").multiply(Decimal("0.5"))
    assert Money.of("0.01").multiply(
        Decimal("0.5"),
        rounding=ROUND_HALF_UP,
    ) == Money.of("0.01")


def test_division_exact_and_rounded():
    assert Money.of("10.00") / 2 == Money.of("5.00")
    with pytest.raises(InvalidMoneyError):
        Money.of("1.00") / 3
    assert Money.of("1.00").divide(
        3,
        rounding=ROUND_HALF_UP,
    ) == Money.of("0.33")


def test_division_by_zero():
    with pytest.raises(InvalidMoneyError):
        Money.of("1.00") / 0


def test_ratio():
    assert Money.of("3.00").ratio(Money.of("100.00")) == Decimal("0.03")
    assert Money.of("1.00").ratio(
        Money.of("3.00"),
        precision=6,
    ) == Decimal("0.333333")


def test_ratio_zero_denominator():
    with pytest.raises(InvalidMoneyError):
        Money.of("1.00").ratio(Money.zero())


def test_sign_helpers():
    assert Money.zero().is_zero
    assert Money.of("1.00").is_positive
    assert Money.of("-1.00").is_negative
    assert abs(Money.of("-1.00")) == Money.of("1.00")
    assert -Money.of("1.00") == Money.of("-1.00")


def test_boolean_value():
    assert not Money.zero()
    assert Money.of("0.01")


def test_comparisons():
    assert Money.of("2.00") > Money.of("1.00")
    assert Money.of("1.00") <= Money.of("1.00")


def test_serialization_preserves_scale():
    assert Money.of("10.20").to_dict() == {
        "amount": "10.20",
        "currency": "USD",
    }


def test_money_is_immutable():
    money = Money.of("1.00")
    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal("2.00")


def test_currency_registry_is_immutable():
    specification = currency_specification(CurrencyCode.USD)
    assert specification.decimal_places == 2
