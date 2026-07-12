"""Canonical financial entities for Pango Revenue Assurance.

The entities in this module describe the business facts that Revenue Assurance
must reconcile:

    operational event -> payment -> settlement -> payout -> bank -> accounting

They are immutable, currency-aware, timezone-safe, and independent of pandas,
SQL schemas, provider SDKs, files, and APIs. Provider-specific values must be
mapped into these canonical entities by normalization adapters.

Important modeling principle:
A processor settlement and a processor payout are separate facts. A settlement
is the processor's calculated financial grouping; a payout is the transfer of
funds initiated toward the bank.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import ClassVar, TypeAlias, TypeVar, cast
from uuid import UUID

from .enums import (
    AccountingStatus,
    BalanceImpact,
    CardNetwork,
    EntryDirection,
    FinancialFlowType,
    OperationalEventStatus,
    OperationalEventType,
    PaymentMethod,
    PaymentProcessor,
    PaymentStatus,
    PayoutStatus,
    RefundStatus,
    SettlementStatus,
    SourceSystem,
    TransactionType,
)
from .exceptions import (
    DomainValidationError,
    InvalidTimestampError,
    InvariantViolationError,
    MissingRequiredValueError,
)
from .identifiers import (
    AccountingEntryId,
    BankTransactionId,
    CorrelationId,
    ExternalReference,
    JournalId,
    OperationalEventId,
    PaymentId,
    PayoutId,
    ReferenceCollection,
    RefundId,
    SettlementId,
)
from .money import Money


MetadataInputValue: TypeAlias = (
    str | int | float | bool | None | Decimal | datetime | UUID | Enum
)
MetadataValue: TypeAlias = str | int | float | bool | None
MetadataInput: TypeAlias = Mapping[str, MetadataInputValue]
FrozenMetadata: TypeAlias = Mapping[str, MetadataValue]


EnumT = TypeVar("EnumT", bound=Enum)


def _parse_enum(
    enum_type: type[EnumT],
    value: object,
    *,
    field_name: str,
) -> EnumT:
    """Parse a canonical enum while preserving precise static typing."""

    try:
        parse = getattr(enum_type, "parse")
        return cast(EnumT, parse(value))
    except (TypeError, ValueError) as exc:
        raise DomainValidationError(
            f"The {field_name} value is invalid.",
            context={
                "field_name": field_name,
                "value": str(value),
                "enum_type": enum_type.__name__,
            },
        ) from exc


def _require_datetime(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidTimestampError(
            "A required timestamp must be a datetime value.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidTimestampError(
            "Domain timestamps must be timezone-aware.",
            context={"field_name": field_name},
        )
    return value


def _optional_datetime(
    value: object | None,
    *,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None
    return _require_datetime(value, field_name=field_name)


def _require_text(
    value: object,
    *,
    field_name: str,
    max_length: int = 512,
) -> str:
    if value is None:
        raise MissingRequiredValueError(field_name=field_name)
    if not isinstance(value, str):
        raise DomainValidationError(
            f"The {field_name} value must be a string.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    normalized = value.strip()
    if not normalized:
        raise MissingRequiredValueError(field_name=field_name)
    if len(normalized) > max_length:
        raise DomainValidationError(
            f"The {field_name} value exceeds the maximum length.",
            context={
                "field_name": field_name,
                "length": len(normalized),
                "max_length": max_length,
            },
        )
    return normalized


def _optional_text(
    value: object | None,
    *,
    field_name: str,
    max_length: int = 512,
) -> str | None:
    if value is None:
        return None
    return _require_text(
        value,
        field_name=field_name,
        max_length=max_length,
    )


def _require_money(value: object, *, field_name: str) -> Money:
    if not isinstance(value, Money):
        raise DomainValidationError(
            f"The {field_name} value must be Money.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    return value


def _optional_money(
    value: object | None,
    *,
    field_name: str,
) -> Money | None:
    if value is None:
        return None
    return _require_money(value, field_name=field_name)


def _require_non_negative_money(
    value: object,
    *,
    field_name: str,
) -> Money:
    money = _require_money(value, field_name=field_name)
    if money.is_negative:
        raise InvariantViolationError(
            f"The {field_name} amount cannot be negative.",
            context={
                "field_name": field_name,
                "amount": money.amount,
                "currency": money.currency,
            },
        )
    return money


def _require_positive_money(
    value: object,
    *,
    field_name: str,
) -> Money:
    money = _require_money(value, field_name=field_name)
    if not money.is_positive:
        raise InvariantViolationError(
            f"The {field_name} amount must be positive.",
            context={
                "field_name": field_name,
                "amount": money.amount,
                "currency": money.currency,
            },
        )
    return money


def _ensure_same_currency(
    *named_amounts: tuple[str, Money | None],
) -> None:
    present = [
        (name, amount)
        for name, amount in named_amounts
        if amount is not None
    ]
    if not present:
        return

    expected = present[0][1].currency
    mismatches = [
        f"{name}:{amount.currency.value}"
        for name, amount in present
        if amount.currency is not expected
    ]
    if mismatches:
        raise InvariantViolationError(
            "Related monetary values must use the same currency.",
            context={
                "expected_currency": expected,
                "mismatched_fields": ", ".join(mismatches),
            },
        )


def _ensure_ordered(
    earlier: datetime | None,
    later: datetime | None,
    *,
    earlier_name: str,
    later_name: str,
) -> None:
    if earlier is not None and later is not None and later < earlier:
        raise InvalidTimestampError(
            f"{later_name} cannot occur before {earlier_name}.",
            context={
                earlier_name: earlier,
                later_name: later,
            },
        )


def _normalise_metadata_value(
    key: str,
    value: MetadataInputValue,
) -> MetadataValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise DomainValidationError(
                "Metadata floats must be finite.",
                context={"metadata_key": key, "value": str(value)},
            )
        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise DomainValidationError(
                "Metadata Decimal values must be finite.",
                context={"metadata_key": key, "value": str(value)},
            )
        return str(value)

    if isinstance(value, datetime):
        return _require_datetime(
            value,
            field_name=f"metadata.{key}",
        ).isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        enum_value = value.value
        if isinstance(enum_value, (str, bool, int)):
            return enum_value
        if isinstance(enum_value, float) and math.isfinite(enum_value):
            return enum_value
        return str(enum_value)

    raise DomainValidationError(
        "Metadata values must be JSON-compatible scalar values.",
        context={
            "metadata_key": key,
            "value_type": type(value).__name__,
        },
    )


def _freeze_metadata(
    metadata: MetadataInput | None,
) -> FrozenMetadata:
    if metadata is None:
        return MappingProxyType({})
    if not isinstance(metadata, Mapping):
        raise DomainValidationError(
            "Entity metadata must be a mapping.",
            context={"value_type": type(metadata).__name__},
        )

    normalized: dict[str, MetadataValue] = {}
    for raw_key, raw_value in metadata.items():
        if not isinstance(raw_key, str):
            raise DomainValidationError(
                "Metadata keys must be strings.",
                context={"key_type": type(raw_key).__name__},
            )
        key = raw_key.strip()
        if not key:
            raise DomainValidationError("Metadata keys cannot be empty.")
        if key in normalized:
            raise DomainValidationError(
                "Metadata contains duplicate keys after normalization.",
                context={"metadata_key": key},
            )
        normalized[key] = _normalise_metadata_value(key, raw_value)

    return MappingProxyType(normalized)


def _normalise_references(
    references: ReferenceCollection | Iterable[ExternalReference],
) -> ReferenceCollection:
    if isinstance(references, ReferenceCollection):
        return references
    return ReferenceCollection(references)


def _normalise_correlation_id(
    value: CorrelationId | str | UUID | None,
) -> CorrelationId | None:
    if value is None:
        return None
    return CorrelationId.parse(value)


def _base_payload(
    *,
    source_system: SourceSystem,
    references: ReferenceCollection,
    correlation_id: CorrelationId | None,
    metadata: FrozenMetadata,
) -> dict[str, object]:
    return {
        "source_system": source_system.value,
        "references": list(references.to_dicts()),
        "correlation_id": (
            correlation_id.to_dict()
            if correlation_id is not None
            else None
        ),
        "metadata": dict(metadata),
    }


class _IdentityEntity:
    """DDD entity equality based exclusively on concrete type and identity."""

    identity_field: ClassVar[str]

    @property
    def identity(self) -> object:
        return getattr(self, type(self).identity_field)

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self.identity == cast(
            _IdentityEntity,
            other,
        ).identity

    def __hash__(self) -> int:
        return hash((type(self), self.identity))


def _normalise_identifier_tuple(
    values: Iterable[SettlementId],
    *,
    field_name: str,
) -> tuple[SettlementId, ...]:
    materialised = tuple(values)
    seen: set[SettlementId] = set()
    for value in materialised:
        if not isinstance(value, SettlementId):
            raise DomainValidationError(
                f"{field_name} must contain SettlementId values only.",
                context={"value_type": type(value).__name__},
            )
        if value in seen:
            raise InvariantViolationError(
                f"{field_name} cannot contain duplicate identifiers.",
                context={"settlement_id": value.value},
            )
        seen.add(value)
    return tuple(sorted(materialised, key=lambda identifier: identifier.value))


def _validate_processor_source(
    source_system: SourceSystem,
    processor: PaymentProcessor,
) -> None:
    """Reject direct provider records attributed to a different processor."""

    direct_pairs = {
        SourceSystem.PAYPAL: PaymentProcessor.PAYPAL,
        SourceSystem.BRAINTREE: PaymentProcessor.BRAINTREE,
    }
    expected = direct_pairs.get(source_system)
    if expected is not None and processor is not expected:
        raise InvariantViolationError(
            "The direct source system conflicts with the payment processor.",
            context={
                "source_system": source_system,
                "processor": processor,
                "expected_processor": expected,
            },
        )


@dataclass(frozen=True, slots=True, eq=False)
class OperationalEvent(_IdentityEntity):
    identity_field: ClassVar[str] = "event_id"

    """Canonical revenue-generating or financially relevant Pango event."""

    event_id: OperationalEventId
    event_type: OperationalEventType
    status: OperationalEventStatus
    source_system: SourceSystem
    occurred_at: datetime
    expected_amount: Money
    final_amount: Money | None = None
    customer_id: str | None = None
    location_id: str | None = None
    zone_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, OperationalEventId):
            raise DomainValidationError(
                "event_id must be an OperationalEventId.",
                context={"value_type": type(self.event_id).__name__},
            )

        event_type = _parse_enum(
            OperationalEventType,
            self.event_type,
            field_name="event_type",
        )
        status = _parse_enum(
            OperationalEventStatus,
            self.status,
            field_name="status",
        )
        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        occurred_at = _require_datetime(
            self.occurred_at,
            field_name="occurred_at",
        )
        expected_amount = _require_non_negative_money(
            self.expected_amount,
            field_name="expected_amount",
        )
        final_amount = _optional_money(
            self.final_amount,
            field_name="final_amount",
        )
        if final_amount is not None and final_amount.is_negative:
            raise InvariantViolationError(
                "final_amount cannot be negative.",
                context={"event_id": self.event_id.value},
            )

        _ensure_same_currency(
            ("expected_amount", expected_amount),
            ("final_amount", final_amount),
        )

        created_at = _optional_datetime(
            self.created_at,
            field_name="created_at",
        )
        updated_at = _optional_datetime(
            self.updated_at,
            field_name="updated_at",
        )
        _ensure_ordered(
            created_at,
            updated_at,
            earlier_name="created_at",
            later_name="updated_at",
        )

        if status is OperationalEventStatus.COMPLETED and final_amount is None:
            raise InvariantViolationError(
                "A completed operational event requires final_amount.",
                context={"event_id": self.event_id.value},
            )

        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "expected_amount", expected_amount)
        object.__setattr__(self, "final_amount", final_amount)
        object.__setattr__(
            self,
            "customer_id",
            _optional_text(self.customer_id, field_name="customer_id"),
        )
        object.__setattr__(
            self,
            "location_id",
            _optional_text(self.location_id, field_name="location_id"),
        )
        object.__setattr__(
            self,
            "zone_id",
            _optional_text(self.zone_id, field_name="zone_id"),
        )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def revenue_amount(self) -> Money:
        """Best available canonical amount expected to generate revenue."""

        return self.final_amount or self.expected_amount

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id.value,
            "event_type": self.event_type.value,
            "status": self.status.value,
            "occurred_at": self.occurred_at.isoformat(),
            "expected_amount": self.expected_amount.to_dict(),
            "final_amount": (
                self.final_amount.to_dict()
                if self.final_amount is not None
                else None
            ),
            "customer_id": self.customer_id,
            "location_id": self.location_id,
            "zone_id": self.zone_id,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at is not None
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at is not None
                else None
            ),
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class PaymentTransaction(_IdentityEntity):
    identity_field: ClassVar[str] = "payment_id"
    """Canonical customer payment captured or attempted by a processor."""

    payment_id: PaymentId
    source_system: SourceSystem
    processor: PaymentProcessor
    status: PaymentStatus
    occurred_at: datetime
    gross_amount: Money
    fee_amount: Money
    net_amount: Money
    transaction_type: TransactionType = TransactionType.CUSTOMER_PAYMENT
    financial_flow: FinancialFlowType = FinancialFlowType.REVENUE
    payment_method: PaymentMethod = PaymentMethod.UNKNOWN
    card_network: CardNetwork = CardNetwork.UNKNOWN
    operational_event_id: OperationalEventId | None = None
    authorized_at: datetime | None = None
    captured_at: datetime | None = None
    settled_at: datetime | None = None
    fees_withheld: bool | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.payment_id, PaymentId):
            raise DomainValidationError(
                "payment_id must be a PaymentId.",
                context={"value_type": type(self.payment_id).__name__},
            )
        if self.operational_event_id is not None and not isinstance(
            self.operational_event_id,
            OperationalEventId,
        ):
            raise DomainValidationError(
                "operational_event_id must be an OperationalEventId.",
                context={
                    "value_type": type(self.operational_event_id).__name__
                },
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        processor = _parse_enum(
            PaymentProcessor,
            self.processor,
            field_name="processor",
        )
        _validate_processor_source(source_system, processor)
        status = _parse_enum(
            PaymentStatus,
            self.status,
            field_name="status",
        )
        transaction_type = _parse_enum(
            TransactionType,
            self.transaction_type,
            field_name="transaction_type",
        )
        financial_flow = _parse_enum(
            FinancialFlowType,
            self.financial_flow,
            field_name="financial_flow",
        )
        payment_method = _parse_enum(
            PaymentMethod,
            self.payment_method,
            field_name="payment_method",
        )
        card_network = _parse_enum(
            CardNetwork,
            self.card_network,
            field_name="card_network",
        )

        occurred_at = _require_datetime(
            self.occurred_at,
            field_name="occurred_at",
        )
        authorized_at = _optional_datetime(
            self.authorized_at,
            field_name="authorized_at",
        )
        captured_at = _optional_datetime(
            self.captured_at,
            field_name="captured_at",
        )
        settled_at = _optional_datetime(
            self.settled_at,
            field_name="settled_at",
        )

        gross_amount = _require_non_negative_money(
            self.gross_amount,
            field_name="gross_amount",
        )
        fee_amount = _require_non_negative_money(
            self.fee_amount,
            field_name="fee_amount",
        )
        net_amount = _require_non_negative_money(
            self.net_amount,
            field_name="net_amount",
        )
        _ensure_same_currency(
            ("gross_amount", gross_amount),
            ("fee_amount", fee_amount),
            ("net_amount", net_amount),
        )

        if self.fees_withheld is not None and not isinstance(
            self.fees_withheld,
            bool,
        ):
            raise DomainValidationError(
                "fees_withheld must be bool or None.",
                context={
                    "value_type": type(self.fees_withheld).__name__,
                },
            )

        if self.fees_withheld is True:
            expected_net = gross_amount - fee_amount
            if net_amount != expected_net:
                raise InvariantViolationError(
                    "net_amount must equal gross_amount minus fee_amount when "
                    "fees are withheld by the processor.",
                    context={
                        "payment_id": self.payment_id.value,
                        "gross_amount": gross_amount.amount,
                        "fee_amount": fee_amount.amount,
                        "net_amount": net_amount.amount,
                    },
                )
        elif self.fees_withheld is False and net_amount != gross_amount:
            raise InvariantViolationError(
                "net_amount must equal gross_amount when fees are not withheld.",
                context={
                    "payment_id": self.payment_id.value,
                    "gross_amount": gross_amount.amount,
                    "net_amount": net_amount.amount,
                },
            )

        _ensure_ordered(
            occurred_at,
            authorized_at,
            earlier_name="occurred_at",
            later_name="authorized_at",
        )
        _ensure_ordered(
            authorized_at or occurred_at,
            captured_at,
            earlier_name="authorized_at",
            later_name="captured_at",
        )
        _ensure_ordered(
            captured_at or authorized_at or occurred_at,
            settled_at,
            earlier_name="captured_at",
            later_name="settled_at",
        )

        if payment_method is not PaymentMethod.CARD and (
            card_network is not CardNetwork.UNKNOWN
        ):
            raise InvariantViolationError(
                "card_network is only valid for card payments.",
                context={"payment_id": self.payment_id.value},
            )

        if status is PaymentStatus.SETTLED and settled_at is None:
            raise InvariantViolationError(
                "A settled payment requires settled_at.",
                context={"payment_id": self.payment_id.value},
            )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "processor", processor)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "transaction_type", transaction_type)
        object.__setattr__(self, "financial_flow", financial_flow)
        object.__setattr__(self, "payment_method", payment_method)
        object.__setattr__(self, "card_network", card_network)
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "authorized_at", authorized_at)
        object.__setattr__(self, "captured_at", captured_at)
        object.__setattr__(self, "settled_at", settled_at)
        object.__setattr__(self, "gross_amount", gross_amount)
        object.__setattr__(self, "fee_amount", fee_amount)
        object.__setattr__(self, "net_amount", net_amount)
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def effective_fee_rate(self) -> Decimal | None:
        if self.gross_amount.is_zero:
            return None
        return self.fee_amount.ratio(self.gross_amount)

    def to_dict(self) -> dict[str, object]:
        return {
            "payment_id": self.payment_id.value,
            "operational_event_id": (
                self.operational_event_id.value
                if self.operational_event_id is not None
                else None
            ),
            "processor": self.processor.value,
            "status": self.status.value,
            "transaction_type": self.transaction_type.value,
            "financial_flow": self.financial_flow.value,
            "payment_method": self.payment_method.value,
            "card_network": self.card_network.value,
            "occurred_at": self.occurred_at.isoformat(),
            "authorized_at": (
                self.authorized_at.isoformat()
                if self.authorized_at is not None
                else None
            ),
            "captured_at": (
                self.captured_at.isoformat()
                if self.captured_at is not None
                else None
            ),
            "settled_at": (
                self.settled_at.isoformat()
                if self.settled_at is not None
                else None
            ),
            "gross_amount": self.gross_amount.to_dict(),
            "fee_amount": self.fee_amount.to_dict(),
            "net_amount": self.net_amount.to_dict(),
            "fees_withheld": self.fees_withheld,
            "effective_fee_rate": (
                str(self.effective_fee_rate)
                if self.effective_fee_rate is not None
                else None
            ),
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class Refund(_IdentityEntity):
    identity_field: ClassVar[str] = "refund_id"
    """Canonical refund linked to an original payment."""

    refund_id: RefundId
    payment_id: PaymentId
    source_system: SourceSystem
    processor: PaymentProcessor
    status: RefundStatus
    amount: Money
    requested_at: datetime
    processed_at: datetime | None = None
    operational_event_id: OperationalEventId | None = None
    reason: str | None = None
    requested_by: str | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.refund_id, RefundId):
            raise DomainValidationError(
                "refund_id must be a RefundId.",
                context={"value_type": type(self.refund_id).__name__},
            )
        if not isinstance(self.payment_id, PaymentId):
            raise DomainValidationError(
                "payment_id must be a PaymentId.",
                context={"value_type": type(self.payment_id).__name__},
            )
        if self.operational_event_id is not None and not isinstance(
            self.operational_event_id,
            OperationalEventId,
        ):
            raise DomainValidationError(
                "operational_event_id must be an OperationalEventId.",
                context={
                    "value_type": type(self.operational_event_id).__name__
                },
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        processor = _parse_enum(
            PaymentProcessor,
            self.processor,
            field_name="processor",
        )
        _validate_processor_source(source_system, processor)
        status = _parse_enum(
            RefundStatus,
            self.status,
            field_name="status",
        )
        amount = _require_positive_money(
            self.amount,
            field_name="amount",
        )
        requested_at = _require_datetime(
            self.requested_at,
            field_name="requested_at",
        )
        processed_at = _optional_datetime(
            self.processed_at,
            field_name="processed_at",
        )
        _ensure_ordered(
            requested_at,
            processed_at,
            earlier_name="requested_at",
            later_name="processed_at",
        )

        if status is RefundStatus.SUCCEEDED and processed_at is None:
            raise InvariantViolationError(
                "A successful refund requires processed_at.",
                context={"refund_id": self.refund_id.value},
            )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "processor", processor)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "requested_at", requested_at)
        object.__setattr__(self, "processed_at", processed_at)
        object.__setattr__(
            self,
            "reason",
            _optional_text(
                self.reason,
                field_name="reason",
                max_length=2048,
            ),
        )
        object.__setattr__(
            self,
            "requested_by",
            _optional_text(
                self.requested_by,
                field_name="requested_by",
            ),
        )
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "refund_id": self.refund_id.value,
            "payment_id": self.payment_id.value,
            "operational_event_id": (
                self.operational_event_id.value
                if self.operational_event_id is not None
                else None
            ),
            "processor": self.processor.value,
            "status": self.status.value,
            "amount": self.amount.to_dict(),
            "requested_at": self.requested_at.isoformat(),
            "processed_at": (
                self.processed_at.isoformat()
                if self.processed_at is not None
                else None
            ),
            "reason": self.reason,
            "requested_by": self.requested_by,
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class Settlement(_IdentityEntity):
    identity_field: ClassVar[str] = "settlement_id"
    """Processor-calculated financial grouping for a settlement period."""

    settlement_id: SettlementId
    source_system: SourceSystem
    processor: PaymentProcessor
    status: SettlementStatus
    period_start: datetime
    period_end: datetime
    gross_amount: Money
    fee_amount: Money
    refund_amount: Money
    adjustment_amount: Money
    net_amount: Money
    initiated_at: datetime | None = None
    completed_at: datetime | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.settlement_id, SettlementId):
            raise DomainValidationError(
                "settlement_id must be a SettlementId.",
                context={"value_type": type(self.settlement_id).__name__},
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        processor = _parse_enum(
            PaymentProcessor,
            self.processor,
            field_name="processor",
        )
        _validate_processor_source(source_system, processor)
        status = _parse_enum(
            SettlementStatus,
            self.status,
            field_name="status",
        )
        period_start = _require_datetime(
            self.period_start,
            field_name="period_start",
        )
        period_end = _require_datetime(
            self.period_end,
            field_name="period_end",
        )
        initiated_at = _optional_datetime(
            self.initiated_at,
            field_name="initiated_at",
        )
        completed_at = _optional_datetime(
            self.completed_at,
            field_name="completed_at",
        )

        _ensure_ordered(
            period_start,
            period_end,
            earlier_name="period_start",
            later_name="period_end",
        )
        _ensure_ordered(
            initiated_at,
            completed_at,
            earlier_name="initiated_at",
            later_name="completed_at",
        )

        gross_amount = _require_non_negative_money(
            self.gross_amount,
            field_name="gross_amount",
        )
        fee_amount = _require_non_negative_money(
            self.fee_amount,
            field_name="fee_amount",
        )
        refund_amount = _require_non_negative_money(
            self.refund_amount,
            field_name="refund_amount",
        )
        adjustment_amount = _require_money(
            self.adjustment_amount,
            field_name="adjustment_amount",
        )
        net_amount = _require_money(
            self.net_amount,
            field_name="net_amount",
        )

        _ensure_same_currency(
            ("gross_amount", gross_amount),
            ("fee_amount", fee_amount),
            ("refund_amount", refund_amount),
            ("adjustment_amount", adjustment_amount),
            ("net_amount", net_amount),
        )

        expected_net = (
            gross_amount
            - fee_amount
            - refund_amount
            + adjustment_amount
        )
        if net_amount != expected_net:
            raise InvariantViolationError(
                "Settlement net_amount must equal gross minus fees minus "
                "refunds plus signed adjustments.",
                context={
                    "settlement_id": self.settlement_id.value,
                    "gross_amount": gross_amount.amount,
                    "fee_amount": fee_amount.amount,
                    "refund_amount": refund_amount.amount,
                    "adjustment_amount": adjustment_amount.amount,
                    "net_amount": net_amount.amount,
                    "expected_net_amount": expected_net.amount,
                },
            )

        if status is SettlementStatus.SETTLED and completed_at is None:
            raise InvariantViolationError(
                "A settled settlement requires completed_at.",
                context={"settlement_id": self.settlement_id.value},
            )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "processor", processor)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "period_start", period_start)
        object.__setattr__(self, "period_end", period_end)
        object.__setattr__(self, "initiated_at", initiated_at)
        object.__setattr__(self, "completed_at", completed_at)
        object.__setattr__(self, "gross_amount", gross_amount)
        object.__setattr__(self, "fee_amount", fee_amount)
        object.__setattr__(self, "refund_amount", refund_amount)
        object.__setattr__(self, "adjustment_amount", adjustment_amount)
        object.__setattr__(self, "net_amount", net_amount)
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "settlement_id": self.settlement_id.value,
            "processor": self.processor.value,
            "status": self.status.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "initiated_at": (
                self.initiated_at.isoformat()
                if self.initiated_at is not None
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at is not None
                else None
            ),
            "gross_amount": self.gross_amount.to_dict(),
            "fee_amount": self.fee_amount.to_dict(),
            "refund_amount": self.refund_amount.to_dict(),
            "adjustment_amount": self.adjustment_amount.to_dict(),
            "net_amount": self.net_amount.to_dict(),
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class ProcessorPayout(_IdentityEntity):
    identity_field: ClassVar[str] = "payout_id"
    """Transfer initiated by a processor toward a receiving bank account."""

    payout_id: PayoutId
    source_system: SourceSystem
    processor: PaymentProcessor
    status: PayoutStatus
    amount: Money
    initiated_at: datetime
    expected_arrival_at: datetime | None = None
    arrived_at: datetime | None = None
    settlement_ids: tuple[SettlementId, ...] = ()
    receiving_account_id: str | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.payout_id, PayoutId):
            raise DomainValidationError(
                "payout_id must be a PayoutId.",
                context={"value_type": type(self.payout_id).__name__},
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        processor = _parse_enum(
            PaymentProcessor,
            self.processor,
            field_name="processor",
        )
        _validate_processor_source(source_system, processor)
        status = _parse_enum(
            PayoutStatus,
            self.status,
            field_name="status",
        )
        amount = _require_positive_money(
            self.amount,
            field_name="amount",
        )
        settlement_ids = _normalise_identifier_tuple(
            self.settlement_ids,
            field_name="settlement_ids",
        )
        initiated_at = _require_datetime(
            self.initiated_at,
            field_name="initiated_at",
        )
        expected_arrival_at = _optional_datetime(
            self.expected_arrival_at,
            field_name="expected_arrival_at",
        )
        arrived_at = _optional_datetime(
            self.arrived_at,
            field_name="arrived_at",
        )

        _ensure_ordered(
            initiated_at,
            expected_arrival_at,
            earlier_name="initiated_at",
            later_name="expected_arrival_at",
        )
        _ensure_ordered(
            initiated_at,
            arrived_at,
            earlier_name="initiated_at",
            later_name="arrived_at",
        )

        if status is PayoutStatus.PAID and arrived_at is None:
            raise InvariantViolationError(
                "A settled processor payout requires arrived_at.",
                context={"payout_id": self.payout_id.value},
            )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "processor", processor)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "settlement_ids", settlement_ids)
        object.__setattr__(self, "initiated_at", initiated_at)
        object.__setattr__(
            self,
            "expected_arrival_at",
            expected_arrival_at,
        )
        object.__setattr__(self, "arrived_at", arrived_at)
        object.__setattr__(
            self,
            "receiving_account_id",
            _optional_text(
                self.receiving_account_id,
                field_name="receiving_account_id",
            ),
        )
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "payout_id": self.payout_id.value,
            "settlement_ids": [
                settlement_id.value
                for settlement_id in self.settlement_ids
            ],
            "processor": self.processor.value,
            "status": self.status.value,
            "amount": self.amount.to_dict(),
            "initiated_at": self.initiated_at.isoformat(),
            "expected_arrival_at": (
                self.expected_arrival_at.isoformat()
                if self.expected_arrival_at is not None
                else None
            ),
            "arrived_at": (
                self.arrived_at.isoformat()
                if self.arrived_at is not None
                else None
            ),
            "receiving_account_id": self.receiving_account_id,
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class BankTransaction(_IdentityEntity):
    identity_field: ClassVar[str] = "bank_transaction_id"
    """Canonical bank movement used as settlement evidence."""

    bank_transaction_id: BankTransactionId
    source_system: SourceSystem
    account_id: str
    transaction_date: datetime
    amount: Money
    direction: EntryDirection
    transaction_type: TransactionType
    financial_flow: FinancialFlowType
    description: str
    value_date: datetime | None = None
    balance_impact: BalanceImpact = BalanceImpact.UNKNOWN
    running_balance: Money | None = None
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.bank_transaction_id, BankTransactionId):
            raise DomainValidationError(
                "bank_transaction_id must be a BankTransactionId.",
                context={
                    "value_type": type(self.bank_transaction_id).__name__
                },
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        direction = _parse_enum(
            EntryDirection,
            self.direction,
            field_name="direction",
        )
        transaction_type = _parse_enum(
            TransactionType,
            self.transaction_type,
            field_name="transaction_type",
        )
        financial_flow = _parse_enum(
            FinancialFlowType,
            self.financial_flow,
            field_name="financial_flow",
        )
        balance_impact = _parse_enum(
            BalanceImpact,
            self.balance_impact,
            field_name="balance_impact",
        )

        transaction_date = _require_datetime(
            self.transaction_date,
            field_name="transaction_date",
        )
        value_date = _optional_datetime(
            self.value_date,
            field_name="value_date",
        )
        amount = _require_positive_money(
            self.amount,
            field_name="amount",
        )
        running_balance = _optional_money(
            self.running_balance,
            field_name="running_balance",
        )
        _ensure_same_currency(
            ("amount", amount),
            ("running_balance", running_balance),
        )

        inferred_impact = (
            BalanceImpact.INCREASE
            if direction is EntryDirection.CREDIT
            else BalanceImpact.DECREASE
        )
        if (
            balance_impact is not BalanceImpact.UNKNOWN
            and balance_impact is not inferred_impact
        ):
            raise InvariantViolationError(
                "Bank balance_impact conflicts with entry direction.",
                context={
                    "bank_transaction_id": self.bank_transaction_id.value,
                    "direction": direction,
                    "balance_impact": balance_impact,
                },
            )
        if balance_impact is BalanceImpact.UNKNOWN:
            balance_impact = inferred_impact

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(
            self,
            "account_id",
            _require_text(self.account_id, field_name="account_id"),
        )
        object.__setattr__(self, "transaction_date", transaction_date)
        object.__setattr__(self, "value_date", value_date)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "transaction_type", transaction_type)
        object.__setattr__(self, "financial_flow", financial_flow)
        object.__setattr__(self, "balance_impact", balance_impact)
        object.__setattr__(
            self,
            "description",
            _require_text(
                self.description,
                field_name="description",
                max_length=4096,
            ),
        )
        object.__setattr__(self, "running_balance", running_balance)
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def signed_amount(self) -> Money:
        return (
            self.amount
            if self.direction is EntryDirection.CREDIT
            else -self.amount
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "bank_transaction_id": self.bank_transaction_id.value,
            "account_id": self.account_id,
            "transaction_date": self.transaction_date.isoformat(),
            "value_date": (
                self.value_date.isoformat()
                if self.value_date is not None
                else None
            ),
            "amount": self.amount.to_dict(),
            "signed_amount": self.signed_amount.to_dict(),
            "direction": self.direction.value,
            "balance_impact": self.balance_impact.value,
            "transaction_type": self.transaction_type.value,
            "financial_flow": self.financial_flow.value,
            "description": self.description,
            "running_balance": (
                self.running_balance.to_dict()
                if self.running_balance is not None
                else None
            ),
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


@dataclass(frozen=True, slots=True, eq=False)
class AccountingEntry(_IdentityEntity):
    identity_field: ClassVar[str] = "accounting_entry_id"
    """Canonical QuickBooks journal line or accounting posting."""

    accounting_entry_id: AccountingEntryId
    source_system: SourceSystem
    journal_id: JournalId
    account_code: str
    posting_date: datetime
    amount: Money
    direction: EntryDirection
    status: AccountingStatus
    description: str | None = None
    transaction_type: TransactionType = TransactionType.UNKNOWN
    financial_flow: FinancialFlowType = FinancialFlowType.UNKNOWN
    references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    correlation_id: CorrelationId | None = None
    metadata: FrozenMetadata = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.accounting_entry_id, AccountingEntryId):
            raise DomainValidationError(
                "accounting_entry_id must be an AccountingEntryId.",
                context={
                    "value_type": type(self.accounting_entry_id).__name__
                },
            )
        if not isinstance(self.journal_id, JournalId):
            raise DomainValidationError(
                "journal_id must be a JournalId.",
                context={"value_type": type(self.journal_id).__name__},
            )

        source_system = _parse_enum(
            SourceSystem,
            self.source_system,
            field_name="source_system",
        )
        direction = _parse_enum(
            EntryDirection,
            self.direction,
            field_name="direction",
        )
        status = _parse_enum(
            AccountingStatus,
            self.status,
            field_name="status",
        )
        transaction_type = _parse_enum(
            TransactionType,
            self.transaction_type,
            field_name="transaction_type",
        )
        financial_flow = _parse_enum(
            FinancialFlowType,
            self.financial_flow,
            field_name="financial_flow",
        )
        posting_date = _require_datetime(
            self.posting_date,
            field_name="posting_date",
        )
        amount = _require_positive_money(
            self.amount,
            field_name="amount",
        )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(
            self,
            "account_code",
            _require_text(
                self.account_code,
                field_name="account_code",
            ),
        )
        object.__setattr__(self, "posting_date", posting_date)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "transaction_type", transaction_type)
        object.__setattr__(self, "financial_flow", financial_flow)
        object.__setattr__(
            self,
            "description",
            _optional_text(
                self.description,
                field_name="description",
                max_length=4096,
            ),
        )
        object.__setattr__(
            self,
            "references",
            _normalise_references(self.references),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalise_correlation_id(self.correlation_id),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def signed_amount(self) -> Money:
        """Debit-positive, credit-negative arithmetic representation.

        This is a computational convention only. Financial meaning still
        depends on the account type and is not inferred by this entity.
        """

        return (
            self.amount
            if self.direction is EntryDirection.DEBIT
            else -self.amount
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "accounting_entry_id": self.accounting_entry_id.value,
            "journal_id": self.journal_id.value,
            "account_code": self.account_code,
            "posting_date": self.posting_date.isoformat(),
            "amount": self.amount.to_dict(),
            "signed_amount": self.signed_amount.to_dict(),
            "direction": self.direction.value,
            "status": self.status.value,
            "description": self.description,
            "transaction_type": self.transaction_type.value,
            "financial_flow": self.financial_flow.value,
            **_base_payload(
                source_system=self.source_system,
                references=self.references,
                correlation_id=self.correlation_id,
                metadata=self.metadata,
            ),
        }


__all__ = [
    "AccountingEntry",
    "BankTransaction",
    "FrozenMetadata",
    "MetadataInput",
    "MetadataInputValue",
    "MetadataValue",
    "OperationalEvent",
    "PaymentTransaction",
    "ProcessorPayout",
    "Refund",
    "Settlement",
]