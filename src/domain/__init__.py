"""Public API for the Pango Revenue Assurance domain layer.

The domain package exposes stable business contracts only. Infrastructure,
provider-specific adapters, pandas models, SQL mappings, and implementation
helpers must import from their own modules and must not become part of this
public surface accidentally.

Recommended usage:

    from domain import Money, PaymentTransaction, ReconciliationResult

Direct submodule imports remain valid when a caller intentionally depends on a
specialised contract, but application code should prefer this package-level API.
"""

from __future__ import annotations

# Canonical vocabulary
from .enums import (
    AccountingStatus,
    BalanceImpact,
    CanonicalStrEnum,
    CardNetwork,
    CurrencyCode,
    EntryDirection,
    ExceptionType,
    FinancialFlowType,
    MatchMethod,
    OperationalEventStatus,
    OperationalEventType,
    PaymentMethod,
    PaymentProcessor,
    PaymentStatus,
    PayoutStatus,
    ReconciliationStatus,
    ReferenceType,
    RefundStatus,
    RiskLevel,
    SettlementStatus,
    SourceSystem,
    TransactionType,
)

# Structured domain exceptions
from .exceptions import (
    AmbiguousMatchError,
    AuditTrailIntegrityError,
    CurrencyMismatchError,
    DataIntegrityError,
    DomainError,
    DomainValidationError,
    DuplicateRecordError,
    InvalidIdentifierError,
    InvalidMoneyError,
    InvalidStateTransitionError,
    InvalidTimestampError,
    InvariantViolationError,
    MissingRequiredValueError,
    ReconciliationError,
    ReconciliationInvariantError,
    ReferentialIntegrityError,
    RevenueAssuranceError,
    UnsupportedMatchMethodError,
)

# Monetary value objects
from .money import (
    CurrencySpecification,
    Money,
    currency_specification,
)

# Identity and lineage
from .identifiers import (
    AccountingEntryId,
    BankTransactionId,
    CorrelationId,
    DomainIdentifier,
    ExternalReference,
    IdentityGraph,
    JournalId,
    LineageEdge,
    OperationalEventId,
    PaymentId,
    PayoutId,
    ReferenceCollection,
    ReferenceConfidence,
    ReferenceProvenance,
    ReferenceRelationship,
    RefundId,
    SettlementId,
)

# Canonical financial entities
from .entities import (
    AccountingEntry,
    BankTransaction,
    OperationalEvent,
    PaymentTransaction,
    ProcessorPayout,
    Refund,
    Settlement,
)

# Reconciliation contracts
from .reconciliation import (
    DifferenceType,
    EvidenceType,
    MatchEvidence,
    MaterialityLevel,
    MaterialityPolicy,
    MoneyDifference,
    ReconciliationDifference,
    ReconciliationResult,
    ReconciliationResultBuilder,
    ReconciliationScope,
    ReconciliationSummary,
    RiskAssessment,
    TimestampDifference,
)


__all__ = [
    # Enums
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
    # Exceptions
    "AmbiguousMatchError",
    "AuditTrailIntegrityError",
    "CurrencyMismatchError",
    "DataIntegrityError",
    "DomainError",
    "DomainValidationError",
    "DuplicateRecordError",
    "InvalidIdentifierError",
    "InvalidMoneyError",
    "InvalidStateTransitionError",
    "InvalidTimestampError",
    "InvariantViolationError",
    "MissingRequiredValueError",
    "ReconciliationError",
    "ReconciliationInvariantError",
    "ReferentialIntegrityError",
    "RevenueAssuranceError",
    "UnsupportedMatchMethodError",
    # Money
    "CurrencySpecification",
    "Money",
    "currency_specification",
    # Identifiers and lineage
    "AccountingEntryId",
    "BankTransactionId",
    "CorrelationId",
    "DomainIdentifier",
    "ExternalReference",
    "IdentityGraph",
    "JournalId",
    "LineageEdge",
    "OperationalEventId",
    "PaymentId",
    "PayoutId",
    "ReferenceCollection",
    "ReferenceConfidence",
    "ReferenceProvenance",
    "ReferenceRelationship",
    "RefundId",
    "SettlementId",
    # Entities
    "AccountingEntry",
    "BankTransaction",
    "OperationalEvent",
    "PaymentTransaction",
    "ProcessorPayout",
    "Refund",
    "Settlement",
    # Reconciliation
    "DifferenceType",
    "EvidenceType",
    "MatchEvidence",
    "MaterialityLevel",
    "MaterialityPolicy",
    "MoneyDifference",
    "ReconciliationDifference",
    "ReconciliationResult",
    "ReconciliationResultBuilder",
    "ReconciliationScope",
    "ReconciliationSummary",
    "RiskAssessment",
    "TimestampDifference",
]