from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain import (
    AccountingEntry,
    AccountingEntryId,
    AccountingStatus,
    BankTransaction,
    BankTransactionId,
    EntryDirection,
    FinancialFlowType,
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


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def later(now: datetime) -> datetime:
    return now + timedelta(days=1)


@pytest.fixture
def operational_event(now: datetime) -> OperationalEvent:
    return OperationalEvent(
        event_id=OperationalEventId("EVENT_1"),
        event_type=OperationalEventType.PARKING_SESSION,
        status=OperationalEventStatus.COMPLETED,
        source_system=SourceSystem.PANGO_BACKEND,
        occurred_at=now,
        expected_amount=Money.of("10.00"),
        final_amount=Money.of("10.00"),
    )


@pytest.fixture
def payment(now: datetime) -> PaymentTransaction:
    return PaymentTransaction(
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
    )


@pytest.fixture
def refund(now: datetime, later: datetime) -> Refund:
    return Refund(
        refund_id=RefundId("REF_1"),
        payment_id=PaymentId("PAY_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=RefundStatus.SUCCEEDED,
        amount=Money.of("2.00"),
        requested_at=now,
        processed_at=later,
    )


@pytest.fixture
def settlement(now: datetime, later: datetime) -> Settlement:
    return Settlement(
        settlement_id=SettlementId("SET_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=SettlementStatus.SETTLED,
        period_start=now,
        period_end=later,
        gross_amount=Money.of("100.00"),
        fee_amount=Money.of("3.00"),
        refund_amount=Money.of("5.00"),
        adjustment_amount=Money.of("-2.00"),
        net_amount=Money.of("90.00"),
        completed_at=later,
    )


@pytest.fixture
def payout(now: datetime, later: datetime) -> ProcessorPayout:
    return ProcessorPayout(
        payout_id=PayoutId("PO_1"),
        source_system=SourceSystem.PAYPAL,
        processor=PaymentProcessor.PAYPAL,
        status=PayoutStatus.PAID,
        amount=Money.of("90.00"),
        initiated_at=now,
        arrived_at=later,
        settlement_ids=(SettlementId("SET_1"),),
    )


@pytest.fixture
def bank_transaction(now: datetime) -> BankTransaction:
    return BankTransaction(
        bank_transaction_id=BankTransactionId("BANK_1"),
        source_system=SourceSystem.FIRSTBANK,
        account_id="2092",
        transaction_date=now,
        amount=Money.of("90.00"),
        direction=EntryDirection.CREDIT,
        transaction_type=TransactionType.PROCESSOR_PAYOUT,
        financial_flow=FinancialFlowType.REVENUE,
        description="PAYPAL TRANSFER",
    )


@pytest.fixture
def accounting_entry(now: datetime) -> AccountingEntry:
    return AccountingEntry(
        accounting_entry_id=AccountingEntryId("AE_1"),
        source_system=SourceSystem.QUICKBOOKS,
        journal_id=JournalId("JRN_1"),
        account_code="1010",
        posting_date=now,
        amount=Money.of("90.00"),
        direction=EntryDirection.DEBIT,
        status=AccountingStatus.POSTED,
    )
