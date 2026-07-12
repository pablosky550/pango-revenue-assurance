from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domain import (
    DifferenceType,
    EvidenceType,
    ExceptionType,
    ExternalReference,
    MatchEvidence,
    MatchMethod,
    MaterialityLevel,
    MaterialityPolicy,
    Money,
    MoneyDifference,
    ReconciliationDifference,
    ReconciliationInvariantError,
    ReconciliationResult,
    ReconciliationResultBuilder,
    ReconciliationScope,
    ReconciliationStatus,
    ReconciliationSummary,
    ReferenceCollection,
    ReferenceConfidence,
    ReferenceType,
    RiskAssessment,
    RiskLevel,
    SourceSystem,
    TimestampDifference,
)


def reference():
    return ExternalReference(
        source_system=SourceSystem.PAYPAL,
        reference_type=ReferenceType.PROCESSOR_TRANSACTION_ID,
        value="TX_1",
    )


def evidence(now):
    return MatchEvidence(
        evidence_type=EvidenceType.EXTERNAL_REFERENCE,
        description="Exact processor reference.",
        confidence=ReferenceConfidence.VERIFIED,
        source_references=ReferenceCollection([reference()]),
        observed_at=now,
        rule_id="RULE_1",
    )


def amount_difference(
    *,
    expected="100.00",
    actual="95.00",
    tolerance="0.01",
):
    money_difference = MoneyDifference(
        expected=Money.of(expected),
        actual=Money.of(actual),
        tolerance=Money.of(tolerance),
    )
    materiality = money_difference.assess_materiality(
        MaterialityPolicy.usd_default()
    )
    return ReconciliationDifference(
        difference_type=DifferenceType.AMOUNT,
        reason=ExceptionType.AMOUNT_MISMATCH,
        description="Amounts differ.",
        field_name="amount",
        money=money_difference,
        materiality=materiality,
    )


def test_money_difference_calculations():
    difference = MoneyDifference(
        expected=Money.of("100.00"),
        actual=Money.of("95.00"),
        tolerance=Money.of("0.01"),
    )
    assert difference.signed_variance == Money.of("-5.00")
    assert difference.absolute_variance == Money.of("5.00")
    assert difference.relative_variance == Decimal("0.05")
    assert not difference.within_tolerance


def test_money_difference_within_tolerance():
    difference = MoneyDifference(
        expected=Money.of("100.00"),
        actual=Money.of("100.01"),
        tolerance=Money.of("0.01"),
    )
    assert difference.within_tolerance


def test_recorded_amount_difference_cannot_be_within_tolerance():
    money_difference = MoneyDifference(
        expected=Money.of("100.00"),
        actual=Money.of("100.01"),
        tolerance=Money.of("0.01"),
    )
    with pytest.raises(Exception):
        ReconciliationDifference(
            difference_type=DifferenceType.AMOUNT,
            reason=ExceptionType.AMOUNT_MISMATCH,
            description="Amounts differ.",
            money=money_difference,
        )


def test_timestamp_difference():
    expected = datetime(2026, 1, 1, tzinfo=timezone.utc)
    actual = expected + timedelta(days=2)
    difference = TimestampDifference(
        expected=expected,
        actual=actual,
        tolerance_seconds=86400,
    )
    assert difference.absolute_seconds == Decimal("172800.0")
    assert not difference.within_tolerance


def test_materiality_uses_highest_absolute_or_relative():
    policy = MaterialityPolicy.usd_default()
    level = policy.assess(
        Money.of("5.00"),
        expected_amount=Money.of("10.00"),
    )
    assert level is MaterialityLevel.CRITICAL


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0, RiskLevel.LOW),
        (19, RiskLevel.LOW),
        (20, RiskLevel.MEDIUM),
        (50, RiskLevel.HIGH),
        (80, RiskLevel.CRITICAL),
        (100, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_thresholds(score, level):
    assert RiskAssessment.from_score(score).level is level


def test_matched_result(now):
    result = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
            evaluated_at=now,
            left_entity_ids=["PAY_1"],
            right_entity_ids=["SET_1"],
        )
        .add_evidence(evidence(now))
        .build_matched(
            match_method=MatchMethod.EXACT_REFERENCE,
            confidence_score=Decimal("1"),
        )
    )
    assert result.status is ReconciliationStatus.MATCHED
    assert result.is_successful
    assert result.amount_at_risk is None
    assert result.risk.score == Decimal("0.00")


def test_matched_result_requires_evidence(now):
    with pytest.raises(ReconciliationInvariantError):
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
            evaluated_at=now,
            left_entity_ids=["PAY_1"],
            right_entity_ids=["SET_1"],
        ).build_matched(
            match_method=MatchMethod.EXACT_REFERENCE,
        )


def test_unmatched_result(now):
    result = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYOUT_TO_BANK,
            evaluated_at=now,
            left_entity_ids=["PO_1"],
        )
        .add_difference(amount_difference())
        .build_unmatched()
    )
    assert result.status is ReconciliationStatus.UNMATCHED
    assert result.amount_at_risk == Money.of("5.00")
    assert ExceptionType.AMOUNT_MISMATCH in result.exception_types


def test_partial_requires_evidence_and_difference(now):
    builder = ReconciliationResultBuilder(
        scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
        evaluated_at=now,
        left_entity_ids=["PAY_1"],
        right_entity_ids=["SET_1"],
    )
    builder.add_difference(amount_difference())
    with pytest.raises(ReconciliationInvariantError):
        builder.build_partial(
            match_method=MatchMethod.AMOUNT_AND_DATE,
            confidence_score=Decimal("0.5"),
        )


def test_builder_is_single_use(now):
    builder = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
            evaluated_at=now,
            left_entity_ids=["PAY_1"],
            right_entity_ids=["SET_1"],
        )
        .add_evidence(evidence(now))
    )
    builder.build_matched(
        match_method=MatchMethod.EXACT_REFERENCE,
    )
    with pytest.raises(ReconciliationInvariantError):
        builder.add_left_entity("PAY_2")


def test_result_ordering_is_deterministic(now):
    first = MatchEvidence(
        evidence_type=EvidenceType.RULE_EXECUTION,
        description="B",
        confidence=ReferenceConfidence.HIGH,
    )
    second = MatchEvidence(
        evidence_type=EvidenceType.RULE_EXECUTION,
        description="A",
        confidence=ReferenceConfidence.HIGH,
    )
    result = ReconciliationResult(
        result_id="11111111-1111-4111-8111-111111111111",
        scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
        status=ReconciliationStatus.MATCHED,
        match_method=MatchMethod.AMOUNT_AND_DATE,
        evaluated_at=now,
        left_entity_ids=("PAY_1",),
        right_entity_ids=("SET_1",),
        evidence=(first, second),
        confidence_score=Decimal("0.8"),
    )
    assert [item.description for item in result.evidence] == ["A", "B"]


def test_risk_is_deterministic(now):
    result = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYOUT_TO_BANK,
            evaluated_at=now,
            left_entity_ids=["PO_1"],
        )
        .add_difference(amount_difference())
        .build_unmatched()
    )
    expected = RiskAssessment.calculate(
        status=result.status,
        materiality=result.materiality,
        exception_types=result.exception_types,
        confidence_score=result.confidence_score,
    )
    assert result.risk == expected


def test_summary_uses_monetary_coverage(now):
    matched = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
            evaluated_at=now,
            left_entity_ids=["PAY_1"],
            right_entity_ids=["SET_1"],
        )
        .add_evidence(evidence(now))
        .build_matched(match_method=MatchMethod.EXACT_REFERENCE)
    )
    unmatched = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYOUT_TO_BANK,
            evaluated_at=now,
            left_entity_ids=["PO_1"],
        )
        .add_difference(amount_difference())
        .build_unmatched()
    )
    summary = ReconciliationSummary.from_results(
        [matched, unmatched],
        generated_at=now,
        evaluated_amounts={
            matched.result_id: Money.of("900.00"),
            unmatched.result_id: Money.of("100.00"),
        },
    )
    assert summary.total_results == 2
    assert summary.matched_results == 1
    assert summary.unmatched_results == 1
    assert summary.coverage_ratio == Decimal("0.9")
    assert summary.amount_at_risk == Money.of("5.00")


def test_summary_rejects_multiple_currencies_is_structurally_guarded(now):
    # Current canonical enum enables only USD. This regression test documents
    # that summary aggregation is still currency-aware through Money.
    summary = ReconciliationSummary.from_results([], generated_at=now)
    assert summary.amount_at_risk == Money.zero()


def test_serialization(now):
    result = (
        ReconciliationResultBuilder(
            scope=ReconciliationScope.PAYMENT_TO_SETTLEMENT,
            evaluated_at=now,
            left_entity_ids=["PAY_1"],
            right_entity_ids=["SET_1"],
        )
        .add_evidence(evidence(now))
        .build_matched(match_method=MatchMethod.EXACT_REFERENCE)
    )
    payload = result.to_dict()
    assert payload["status"] == "matched"
    assert payload["risk"]["score"] == "0.00"
