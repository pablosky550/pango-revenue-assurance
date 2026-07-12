"""Canonical enumerations for the Pango Revenue Assurance domain.

This module defines the controlled vocabulary shared by the domain,
normalization, reconciliation, persistence, reporting, and automation layers.

Provider-specific raw values must be preserved in raw/staging datasets and
mapped to these canonical values by dedicated source mappers. Consequently,
this module intentionally contains no PayPal-, Braintree-, FirstBank-, or
QuickBooks-specific aliases and has no dependency on pandas, databases,
filesystems, or network clients.
"""

from __future__ import annotations

from enum import Enum, unique
from typing import TypeVar


EnumT = TypeVar("EnumT", bound="CanonicalStrEnum")


class CanonicalStrEnum(str, Enum):
    """Base class for string-backed canonical domain enumerations.

    Members retain strict enum semantics in Python while remaining directly
    serializable as strings for JSON, CSV, SQL parameters, logs, APIs, and n8n.
    """

    def __str__(self) -> str:
        """Return the stable canonical serialized value."""

        return self.value

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """Return canonical serialized values in declaration order."""

        return tuple(member.value for member in cls)

    @classmethod
    def choices(cls) -> tuple[tuple[str, str], ...]:
        """Return ``(value, member_name)`` pairs for schemas and tooling."""

        return tuple((member.value, member.name) for member in cls)

    @classmethod
    def parse(cls: type[EnumT], value: object) -> EnumT:
        """Parse a canonical or canonically equivalent string value.

        Conservative canonicalization removes surrounding whitespace and
        compares strings case-insensitively. It does not translate aliases or
        provider-specific statuses; source mappers own that responsibility.

        Args:
            value: A member of ``cls`` or a string equivalent to a canonical
                serialized value.

        Returns:
            The corresponding enum member.

        Raises:
            TypeError: If ``value`` is neither a string nor a member of ``cls``.
            ValueError: If the normalized string is not canonical for ``cls``.
        """

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                f"{cls.__name__} requires a string or {cls.__name__} member; "
                f"received {type(value).__name__}."
            )

        normalized = value.strip().casefold()
        for member in cls:
            if member.value.casefold() == normalized:
                return member

        allowed = ", ".join(cls.values())
        raise ValueError(
            f"Unsupported {cls.__name__} value {value!r}. "
            f"Allowed values: {allowed}."
        )


@unique
class SourceSystem(CanonicalStrEnum):
    """System that produced or supplied a Revenue Assurance record.

    Only confirmed first-class project sources are represented here. Card
    networks and payment methods are modeled independently because they are
    attributes of a transaction, not necessarily autonomous data sources.
    """

    PANGO_BACKEND = "pango_backend"
    PAYPAL = "paypal"
    BRAINTREE = "braintree"
    FIRSTBANK = "firstbank"
    QUICKBOOKS = "quickbooks"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@unique
class PaymentProcessor(CanonicalStrEnum):
    """Processor responsible for authorizing or settling a payment."""

    PAYPAL = "paypal"
    BRAINTREE = "braintree"
    HEARTLAND = "heartland"
    UNKNOWN = "unknown"


@unique
class CardNetwork(CanonicalStrEnum):
    """Card scheme associated with a card transaction, when available."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    AMERICAN_EXPRESS = "american_express"
    DISCOVER = "discover"
    OTHER = "other"
    UNKNOWN = "unknown"


@unique
class PaymentMethod(CanonicalStrEnum):
    """Instrument or channel used to execute a financial transaction."""

    CARD = "card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"
    WALLET = "wallet"
    OTHER = "other"
    UNKNOWN = "unknown"


@unique
class CurrencyCode(CanonicalStrEnum):
    """Supported ISO 4217 currency codes.

    USD is the only currency currently evidenced by the project data. Another
    currency must be introduced deliberately together with its precision,
    rounding, conversion, and reconciliation rules.
    """

    USD = "USD"


@unique
class OperationalEventType(CanonicalStrEnum):
    """Revenue-generating or financially relevant Pango business event."""

    PARKING_SESSION = "parking_session"
    RESERVATION = "reservation"
    PERMIT_PURCHASE = "permit_purchase"
    VIOLATION_PAYMENT = "violation_payment"
    MERCHANT_VALIDATION = "merchant_validation"
    WALLET_TOP_UP = "wallet_top_up"
    STATEMENT_CHARGE = "statement_charge"
    OTHER = "other"
    UNKNOWN = "unknown"


@unique
class OperationalEventStatus(CanonicalStrEnum):
    """Canonical lifecycle state of an operational business event."""

    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    VOIDED = "voided"
    FAILED = "failed"
    UNKNOWN = "unknown"


@unique
class FinancialFlowType(CanonicalStrEnum):
    """High-level economic flow used to segment the audited population."""

    REVENUE = "revenue"
    REFUND = "refund"
    PROCESSING_COST = "processing_cost"
    OPERATING_EXPENSE = "operating_expense"
    TREASURY = "treasury"
    FINANCING = "financing"
    INTERNAL_TRANSFER = "internal_transfer"
    UNKNOWN = "unknown"


@unique
class TransactionType(CanonicalStrEnum):
    """Canonical economic meaning of an individual financial transaction.

    This classification is independent of processor, payment method, and card
    network. A settlement is the processor's calculated financial grouping;
    a processor payout is the actual outbound transfer toward the bank.
    """

    CUSTOMER_PAYMENT = "customer_payment"
    WALLET_TOP_UP = "wallet_top_up"
    PROCESSOR_SETTLEMENT = "processor_settlement"
    PROCESSOR_PAYOUT = "processor_payout"
    REFUND = "refund"
    DISPUTE = "dispute"
    CHARGEBACK = "chargeback"
    CHARGEBACK_HOLD = "chargeback_hold"
    FEE = "fee"
    ADJUSTMENT = "adjustment"
    INTERNAL_TRANSFER = "internal_transfer"
    PAYROLL_FUNDING = "payroll_funding"
    TREASURY_TRANSFER = "treasury_transfer"
    CITY_PAYMENT = "city_payment"
    VENDOR_PAYMENT = "vendor_payment"
    LOAN_PAYMENT = "loan_payment"
    OTHER = "other"
    UNKNOWN = "unknown"


@unique
class PaymentStatus(CanonicalStrEnum):
    """Canonical lifecycle status of an individual payment."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VOIDED = "voided"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    REVERSED = "reversed"
    SETTLED = "settled"
    UNKNOWN = "unknown"


@unique
class SettlementStatus(CanonicalStrEnum):
    """Canonical lifecycle status of a processor settlement or payout."""

    PENDING = "pending"
    INITIATED = "initiated"
    IN_TRANSIT = "in_transit"
    PARTIALLY_SETTLED = "partially_settled"
    SETTLED = "settled"
    FAILED = "failed"
    REVERSED = "reversed"
    UNKNOWN = "unknown"




@unique
class PayoutStatus(CanonicalStrEnum):
    """Canonical lifecycle of a processor-to-bank payout."""

    PENDING = "pending"
    INITIATED = "initiated"
    IN_TRANSIT = "in_transit"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    UNKNOWN = "unknown"


@unique
class RefundStatus(CanonicalStrEnum):
    """Canonical lifecycle status of a refund."""

    REQUESTED = "requested"
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    UNKNOWN = "unknown"


@unique
class AccountingStatus(CanonicalStrEnum):
    """Posting state of an accounting record or journal entry."""

    DRAFT = "draft"
    POSTED = "posted"
    VOIDED = "voided"
    REVERSED = "reversed"
    UNKNOWN = "unknown"


@unique
class EntryDirection(CanonicalStrEnum):
    """Debit or credit direction of a bank or accounting entry."""

    DEBIT = "debit"
    CREDIT = "credit"


@unique
class BalanceImpact(CanonicalStrEnum):
    """Economic effect of a transaction on the relevant account balance."""

    INCREASE = "increase"
    DECREASE = "decrease"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@unique
class ReferenceType(CanonicalStrEnum):
    """Semantic type of an identifier used for cross-system traceability."""

    OPERATIONAL_EVENT_ID = "operational_event_id"
    INTERNAL_PAYMENT_ID = "internal_payment_id"
    PROCESSOR_TRANSACTION_ID = "processor_transaction_id"
    PROCESSOR_REFERENCE = "processor_reference"
    SETTLEMENT_ID = "settlement_id"
    PAYOUT_ID = "payout_id"
    BANK_TRANSACTION_ID = "bank_transaction_id"
    BANK_REFERENCE = "bank_reference"
    ACCOUNTING_ENTRY_ID = "accounting_entry_id"
    JOURNAL_ID = "journal_id"
    REFUND_ID = "refund_id"
    CORRELATION_ID = "correlation_id"
    OTHER = "other"


@unique
class ReconciliationStatus(CanonicalStrEnum):
    """Outcome of a Revenue Assurance reconciliation decision."""

    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    REVIEW_REQUIRED = "review_required"
    EXCLUDED = "excluded"
    ERROR = "error"


@unique
class MatchMethod(CanonicalStrEnum):
    """Method that produced or justified a reconciliation result."""

    EXACT_ID = "exact_id"
    EXACT_REFERENCE = "exact_reference"
    REFERENCE_AND_AMOUNT = "reference_and_amount"
    AMOUNT_AND_DATE = "amount_and_date"
    AGGREGATE_WINDOW = "aggregate_window"
    MANUAL = "manual"
    NONE = "none"


@unique
class RiskLevel(CanonicalStrEnum):
    """Business-priority level assigned to an exception or anomaly."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@unique
class ExceptionType(CanonicalStrEnum):
    """Canonical category of a Revenue Assurance exception."""

    MISSING_OPERATIONAL_EVENT = "missing_operational_event"
    MISSING_PAYMENT = "missing_payment"
    MISSING_SETTLEMENT = "missing_settlement"
    MISSING_BANK_DEPOSIT = "missing_bank_deposit"
    MISSING_ACCOUNTING_ENTRY = "missing_accounting_entry"
    AMOUNT_MISMATCH = "amount_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    STATUS_MISMATCH = "status_mismatch"
    TIMING_DELAY = "timing_delay"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    UNEXPECTED_FEE = "unexpected_fee"
    SUSPICIOUS_REFUND = "suspicious_refund"
    SUSPICIOUS_ADJUSTMENT = "suspicious_adjustment"
    UNCLASSIFIED_TRANSACTION = "unclassified_transaction"
    DATA_QUALITY_ERROR = "data_quality_error"
    OTHER = "other"


__all__ = [
    "AccountingStatus",
    "BalanceImpact",
    "CanonicalStrEnum",
    "CardNetwork",
    "CurrencyCode",
    "EntryDirection",
    "ExceptionType",
    "FinancialFlowType",
    "MatchMethod",
    "OperationalEventStatus",
    "OperationalEventType",
    "PaymentMethod",
    "PaymentProcessor",
    "PaymentStatus",
    "PayoutStatus",
    "ReconciliationStatus",
    "ReferenceType",
    "RefundStatus",
    "RiskLevel",
    "SettlementStatus",
    "SourceSystem",
    "TransactionType",
]