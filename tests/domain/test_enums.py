from __future__ import annotations

import pytest

from domain import (
    CurrencyCode,
    MatchMethod,
    PaymentStatus,
    PayoutStatus,
    ReconciliationStatus,
    SourceSystem,
)


@pytest.mark.parametrize(
    ("enum_type", "raw", "expected"),
    [
        (SourceSystem, " paypal ", SourceSystem.PAYPAL),
        (CurrencyCode, "usd", CurrencyCode.USD),
        (PaymentStatus, "settled", PaymentStatus.SETTLED),
        (PayoutStatus, "in_transit", PayoutStatus.IN_TRANSIT),
        (MatchMethod, "exact_reference", MatchMethod.EXACT_REFERENCE),
        (ReconciliationStatus, "matched", ReconciliationStatus.MATCHED),
    ],
)
def test_parse_accepts_canonically_equivalent_values(enum_type, raw, expected):
    assert enum_type.parse(raw) is expected


@pytest.mark.parametrize(
    ("enum_type", "invalid"),
    [
        (SourceSystem, "stripe"),
        (PaymentStatus, "Completed"),
        (MatchMethod, "fuzzy"),
        (CurrencyCode, "EUR"),
    ],
)
def test_parse_rejects_noncanonical_or_unsupported_values(enum_type, invalid):
    with pytest.raises(ValueError):
        enum_type.parse(invalid)


def test_string_conversion_returns_value():
    assert str(SourceSystem.PAYPAL) == "paypal"


def test_choices_are_deterministic():
    assert SourceSystem.choices() == tuple(
        (member.value, member.name) for member in SourceSystem
    )


@pytest.mark.parametrize(
    "enum_type",
    [SourceSystem, PaymentStatus, PayoutStatus, MatchMethod, ReconciliationStatus],
)
def test_enum_values_are_unique(enum_type):
    values = [member.value for member in enum_type]
    assert len(values) == len(set(values))
