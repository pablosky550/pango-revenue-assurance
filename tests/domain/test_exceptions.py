from __future__ import annotations

import json
import math
import pickle
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from domain import (
    AmbiguousMatchError,
    CurrencyMismatchError,
    MissingRequiredValueError,
    RevenueAssuranceError,
)


def test_base_exception_has_stable_payload():
    error = RevenueAssuranceError(
        "Failure",
        context={"amount": Decimal("10.20")},
    )
    assert error.code == "REVENUE_ASSURANCE_ERROR"
    assert error.to_dict()["context"]["amount"] == "10.20"
    json.dumps(error.to_dict(), allow_nan=False)


def test_context_is_immutable():
    error = RevenueAssuranceError("Failure", context={"id": "X"})
    with pytest.raises(TypeError):
        error.context["id"] = "Y"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_float_context_is_rejected(value):
    with pytest.raises(ValueError):
        RevenueAssuranceError("Failure", context={"value": value})


def test_naive_datetime_context_is_rejected():
    with pytest.raises(ValueError):
        RevenueAssuranceError(
            "Failure",
            context={"when": datetime(2026, 1, 1)},
        )


def test_timezone_aware_datetime_is_serialized():
    error = RevenueAssuranceError(
        "Failure",
        context={"when": datetime(2026, 1, 1, tzinfo=timezone.utc)},
    )
    assert error.context["when"].endswith("+00:00")


def test_empty_message_is_rejected():
    with pytest.raises(ValueError):
        RevenueAssuranceError("   ")


def test_currency_mismatch_contains_context():
    error = CurrencyMismatchError("USD", "EUR", operation="addition")
    assert error.context == {
        "left_currency": "USD",
        "right_currency": "EUR",
        "operation": "addition",
    }


def test_missing_required_value_contains_field():
    error = MissingRequiredValueError(
        "payment_id",
        entity_type="PaymentTransaction",
    )
    assert error.context["field_name"] == "payment_id"


@pytest.mark.parametrize("count", [0, 1, -1])
def test_ambiguous_match_requires_two_candidates(count):
    with pytest.raises(ValueError):
        AmbiguousMatchError(count)


def test_ambiguous_match_rejects_bool():
    with pytest.raises(TypeError):
        AmbiguousMatchError(True)


def test_specialized_exception_is_pickle_safe():
    original = CurrencyMismatchError("USD", "EUR", operation="addition")
    restored = pickle.loads(pickle.dumps(original))
    assert restored.to_dict() == original.to_dict()


def test_context_collision_is_rejected():
    with pytest.raises(ValueError):
        CurrencyMismatchError(
            "USD",
            "EUR",
            context={"left_currency": "GBP"},
        )
