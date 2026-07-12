from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from domain import (
    AccountingEntry,
    AccountingEntryId,
    AccountingStatus,
    BalanceImpact,
    BankTransaction,
    BankTransactionId,
    CardNetwork,
    DomainValidationError,
    EntryDirection,
    FinancialFlowType,
    InvariantViolationError,
    InvalidTimestampError,
    JournalId,
    Money,
    OperationalEvent,
    OperationalEventId,
    OperationalEventStatus,
    OperationalEventType,
    PaymentId,
    PaymentMethod,
    PaymentProcessor,
    PaymentStatus,
    PaymentTransaction,
    PayoutId,
    PayoutStatus,
    ProcessorPayout,
    Refund,
    RefundId,
    RefundStatus,
    Settlement,
    SettlementId,
    SettlementStatus,
    SourceSystem,
    TransactionType,
)


def test_operational_event_revenue_amount(operational_event):
    assert operational_event.revenue_amount == Money.of("10.00")


def test_completed_event_requires_final_amount(now):
    with pytest.raises(InvariantViolationError):
        OperationalEvent(
            event_id=OperationalEventId("EVENT_1"),
            event_type=OperationalEventType.PARKING_SESSION,
            status=OperationalEventStatus.COMPLETED,
            source_system=SourceSystem.PANGO_BACKEND,
            occurred_at=now,
            expected_amount=Money.of("10.00"),
        )


def test_event_rejects_naive_timestamp():
    with pytest.raises(InvalidTimestampError):
        OperationalEvent(
            event_id=OperationalEventId("EVENT_1"),
            event_type=OperationalEventType.PARKING_SESSION,
            status=OperationalEventStatus.CREATED,
            source_system=SourceSystem.PANGO_BACKEND,
            occurred_at=datetime(2026, 1, 1),
            expected_amount=Money.of("10.00"),
        )


def test_payment_paypal_fee_invariant(payment):
    assert payment.net_amount == payment.gross_amount - payment.fee_amount


def test_payment_without_withheld_fees_requires_net_equal_gross(now):
    with pytest.raises(InvariantViolationError):
        PaymentTransaction(
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.BRAINTREE,
            processor=PaymentProcessor.BRAINTREE,
            status=PaymentStatus.SUCCEEDED,
            occurred_at=now,
            gross_amount=Money.of("10.00"),
            fee_amount=Money.of("0.30"),
            net_amount=Money.of("9.70"),
            fees_withheld=False,
        )


def test_payment_source_processor_mismatch(now):
    with pytest.raises(InvariantViolationError):
        PaymentTransaction(
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.BRAINTREE,
            status=PaymentStatus.SUCCEEDED,
            occurred_at=now,
            gross_amount=Money.of("10.00"),
            fee_amount=Money.of("0.00"),
            net_amount=Money.of("10.00"),
        )


def test_backend_can_observe_external_processor(now):
    payment = PaymentTransaction(
        payment_id=PaymentId("PAY_1"),
        source_system=SourceSystem.PANGO_BACKEND,
        processor=PaymentProcessor.PAYPAL,
        status=PaymentStatus.SUCCEEDED,
        occurred_at=now,
        gross_amount=Money.of("10.00"),
        fee_amount=Money.of("0.30"),
        net_amount=Money.of("9.70"),
        fees_withheld=True,
    )
    assert payment.processor is PaymentProcessor.PAYPAL


def test_card_network_requires_card_method(now):
    with pytest.raises(InvariantViolationError):
        PaymentTransaction(
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=PaymentStatus.SUCCEEDED,
            occurred_at=now,
            gross_amount=Money.of("10.00"),
            fee_amount=Money.of("0.30"),
            net_amount=Money.of("9.70"),
            fees_withheld=True,
            payment_method=PaymentMethod.PAYPAL,
            card_network=CardNetwork.VISA,
        )


def test_settled_payment_requires_settled_at(now):
    with pytest.raises(InvariantViolationError):
        PaymentTransaction(
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=PaymentStatus.SETTLED,
            occurred_at=now,
            gross_amount=Money.of("10.00"),
            fee_amount=Money.of("0.30"),
            net_amount=Money.of("9.70"),
            fees_withheld=True,
        )


def test_payment_timestamps_are_ordered(now):
    with pytest.raises(InvalidTimestampError):
        PaymentTransaction(
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=PaymentStatus.SUCCEEDED,
            occurred_at=now,
            authorized_at=now - timedelta(seconds=1),
            gross_amount=Money.of("10.00"),
            fee_amount=Money.of("0.30"),
            net_amount=Money.of("9.70"),
            fees_withheld=True,
        )


def test_refund_must_be_positive(now):
    with pytest.raises(InvariantViolationError):
        Refund(
            refund_id=RefundId("REF_1"),
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=RefundStatus.PENDING,
            amount=Money.zero(),
            requested_at=now,
        )


def test_successful_refund_requires_processed_at(now):
    with pytest.raises(InvariantViolationError):
        Refund(
            refund_id=RefundId("REF_1"),
            payment_id=PaymentId("PAY_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=RefundStatus.SUCCEEDED,
            amount=Money.of("1.00"),
            requested_at=now,
        )


def test_settlement_formula(settlement):
    assert settlement.net_amount == Money.of("90.00")


def test_invalid_settlement_formula(now, later):
    with pytest.raises(InvariantViolationError):
        Settlement(
            settlement_id=SettlementId("SET_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=SettlementStatus.PENDING,
            period_start=now,
            period_end=later,
            gross_amount=Money.of("100.00"),
            fee_amount=Money.of("3.00"),
            refund_amount=Money.of("5.00"),
            adjustment_amount=Money.of("-2.00"),
            net_amount=Money.of("91.00"),
        )


def test_paid_payout_requires_arrival(now):
    with pytest.raises(InvariantViolationError):
        ProcessorPayout(
            payout_id=PayoutId("PO_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=PayoutStatus.PAID,
            amount=Money.of("10.00"),
            initiated_at=now,
        )


def test_payout_settlement_ids_are_sorted(now):
    payout = ProcessorPayout(
        payout_id=PayoutId("PO_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=PayoutStatus.IN_TRANSIT,
        amount=Money.of("10.00"),
        initiated_at=now,
        settlement_ids=(SettlementId("B"), SettlementId("A")),
    )
    assert payout.settlement_ids == (SettlementId("A"), SettlementId("B"))


def test_payout_rejects_duplicate_settlement_ids(now):
    with pytest.raises(Exception):
        ProcessorPayout(
            payout_id=PayoutId("PO_1"),
            source_system=SourceSystem.PAYPAL,
            processor=PaymentProcessor.PAYPAL,
            status=PayoutStatus.IN_TRANSIT,
            amount=Money.of("10.00"),
            initiated_at=now,
            settlement_ids=(SettlementId("A"), SettlementId("A")),
        )


def test_bank_transaction_infers_balance_impact(bank_transaction):
    assert bank_transaction.balance_impact is BalanceImpact.INCREASE
    assert bank_transaction.signed_amount == Money.of("90.00")


def test_bank_transaction_rejects_conflicting_impact(now):
    with pytest.raises(InvariantViolationError):
        BankTransaction(
            bank_transaction_id=BankTransactionId("BANK_1"),
            source_system=SourceSystem.FIRSTBANK,
            account_id="2092",
            transaction_date=now,
            amount=Money.of("10.00"),
            direction=EntryDirection.CREDIT,
            balance_impact=BalanceImpact.DECREASE,
            transaction_type=TransactionType.PROCESSOR_PAYOUT,
            financial_flow=FinancialFlowType.REVENUE,
            description="TRANSFER",
        )


def test_accounting_signed_amount(accounting_entry):
    assert accounting_entry.signed_amount == Money.of("90.00")


def test_entity_equality_uses_identity(now):
    first = PaymentTransaction(
        payment_id=PaymentId("PAY_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=PaymentStatus.SUCCEEDED,
        occurred_at=now,
        gross_amount=Money.of("10.00"),
        fee_amount=Money.zero(),
        net_amount=Money.of("10.00"),
    )
    second = PaymentTransaction(
        payment_id=PaymentId("PAY_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=PaymentStatus.SUCCEEDED,
        occurred_at=now,
        gross_amount=Money.of("20.00"),
        fee_amount=Money.zero(),
        net_amount=Money.of("20.00"),
    )
    assert first == second
    assert hash(first) == hash(second)


def test_metadata_is_immutable(payment):
    with pytest.raises(TypeError):
        payment.metadata["x"] = "y"


def test_entity_is_immutable(payment):
    with pytest.raises(FrozenInstanceError):
        payment.status = PaymentStatus.FAILED


@pytest.mark.parametrize(
    "entity_fixture",
    [
        "operational_event",
        "payment",
        "refund",
        "settlement",
        "payout",
        "bank_transaction",
        "accounting_entry",
    ],
)
def test_entity_serialization_is_dict(request, entity_fixture):
    entity = request.getfixturevalue(entity_fixture)
    payload = entity.to_dict()
    assert isinstance(payload, dict)
    assert payload["source_system"]
