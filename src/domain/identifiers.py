"""Canonical identifiers, references, and lineage for Revenue Assurance.

This module models identity independently from provider payloads, persistence,
matching algorithms, and infrastructure.

It distinguishes four concepts that must not be conflated:

1. ``DomainIdentifier``
   A strongly typed identifier for a canonical domain entity.

2. ``ExternalReference``
   An identifier observed in a specific source system and classified by its
   semantic reference type.

3. ``CorrelationId``
   A system-generated trace identifier used to connect processing steps, logs,
   alerts, and reconciliation runs.

4. ``IdentityGraph``
   An immutable graph describing how identifiers and references relate across
   the financial lifecycle: event -> payment -> settlement -> bank ->
   accounting.

Identifiers are opaque. Case, punctuation, and leading zeroes are preserved
because changing them could break cross-system reconciliation.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import unique
from types import MappingProxyType
from typing import ClassVar, Final, Generic, TypeVar
from uuid import UUID, uuid4

from .enums import CanonicalStrEnum, ReferenceType, SourceSystem
from .exceptions import (
    DuplicateRecordError,
    InvalidIdentifierError,
    InvalidTimestampError,
    MissingRequiredValueError,
    ReferentialIntegrityError,
)


_MAX_IDENTIFIER_LENGTH: Final[int] = 512
_CONTROL_CHARACTER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x1f\x7f]"
)


@unique
class ReferenceProvenance(CanonicalStrEnum):
    """Technical channel through which a reference was observed."""

    API = "api"
    DATABASE = "database"
    FILE = "file"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    DERIVED = "derived"
    UNKNOWN = "unknown"


@unique
class ReferenceConfidence(CanonicalStrEnum):
    """Reliability assigned to the existence and meaning of a reference."""

    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@unique
class ReferenceRelationship(CanonicalStrEnum):
    """Semantic relationship between two references in the identity graph."""

    GENERATED = "generated"
    IDENTIFIES = "identifies"
    PAID_BY = "paid_by"
    SETTLED_BY = "settled_by"
    PAID_OUT_AS = "paid_out_as"
    DEPOSITED_AS = "deposited_as"
    POSTED_AS = "posted_as"
    REFUNDED_BY = "refunded_by"
    REVERSED_BY = "reversed_by"
    ADJUSTED_BY = "adjusted_by"
    MATCHED_TO = "matched_to"
    DERIVED_FROM = "derived_from"
    CORRELATED_WITH = "correlated_with"


def _normalise_identifier_value(
    value: object,
    *,
    field_name: str,
    max_length: int = _MAX_IDENTIFIER_LENGTH,
) -> str:
    """Validate an opaque identifier without changing semantic content."""

    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("field_name must be a non-empty string.")
    if isinstance(max_length, bool) or not isinstance(max_length, int):
        raise TypeError("max_length must be an integer.")
    if max_length < 1:
        raise ValueError("max_length must be positive.")

    if value is None:
        raise MissingRequiredValueError(field_name=field_name)
    if not isinstance(value, str):
        raise InvalidIdentifierError(
            "Identifiers must be provided as strings.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )

    stripped = value.strip()
    if not stripped:
        raise MissingRequiredValueError(field_name=field_name)

    canonical = unicodedata.normalize("NFC", stripped)

    if len(canonical) > max_length:
        raise InvalidIdentifierError(
            "The identifier exceeds the maximum supported length.",
            context={
                "field_name": field_name,
                "length": len(canonical),
                "max_length": max_length,
            },
        )

    if _CONTROL_CHARACTER_PATTERN.search(canonical):
        raise InvalidIdentifierError(
            "The identifier contains control characters.",
            context={"field_name": field_name},
        )

    return canonical


def _normalise_optional_datetime(
    value: datetime | None,
    *,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise InvalidTimestampError(
            "Reference timestamps must be datetime values.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidTimestampError(
            "Reference timestamps must be timezone-aware.",
            context={"field_name": field_name},
        )
    return value


@dataclass(frozen=True, slots=True)
class DomainIdentifier:
    """Strongly typed opaque identifier for one canonical domain entity."""

    value: str

    reference_type: ClassVar[ReferenceType] = ReferenceType.OTHER
    field_name: ClassVar[str] = "identifier"
    max_length: ClassVar[int] = _MAX_IDENTIFIER_LENGTH

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalise_identifier_value(
                self.value,
                field_name=type(self).field_name,
                max_length=type(self).max_length,
            ),
        )

    @classmethod
    def parse(cls, value: object) -> DomainIdentifier:
        """Return ``value`` as this exact identifier subtype."""

        if isinstance(value, cls):
            return value
        if isinstance(value, DomainIdentifier):
            raise InvalidIdentifierError(
                "An identifier of a different semantic type was supplied.",
                context={
                    "expected_type": cls.__name__,
                    "actual_type": type(value).__name__,
                },
            )
        return cls(value)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
            "reference_type": type(self).reference_type.value,
        }

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class OperationalEventId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = (
        ReferenceType.OPERATIONAL_EVENT_ID
    )
    field_name: ClassVar[str] = "operational_event_id"


@dataclass(frozen=True, slots=True)
class PaymentId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.INTERNAL_PAYMENT_ID
    field_name: ClassVar[str] = "payment_id"


@dataclass(frozen=True, slots=True)
class SettlementId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.SETTLEMENT_ID
    field_name: ClassVar[str] = "settlement_id"


@dataclass(frozen=True, slots=True)
class PayoutId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.PAYOUT_ID
    field_name: ClassVar[str] = "payout_id"


@dataclass(frozen=True, slots=True)
class BankTransactionId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.BANK_TRANSACTION_ID
    field_name: ClassVar[str] = "bank_transaction_id"


@dataclass(frozen=True, slots=True)
class AccountingEntryId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.ACCOUNTING_ENTRY_ID
    field_name: ClassVar[str] = "accounting_entry_id"


@dataclass(frozen=True, slots=True)
class JournalId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.JOURNAL_ID
    field_name: ClassVar[str] = "journal_id"


@dataclass(frozen=True, slots=True)
class RefundId(DomainIdentifier):
    reference_type: ClassVar[ReferenceType] = ReferenceType.REFUND_ID
    field_name: ClassVar[str] = "refund_id"


IdentifierT = TypeVar("IdentifierT", bound=DomainIdentifier)


@dataclass(frozen=True, slots=True)
class ExternalReference:
    """Opaque identifier observed in one source system."""

    source_system: SourceSystem
    reference_type: ReferenceType
    value: str
    is_primary: bool = False
    observed_at: datetime | None = None
    provenance: ReferenceProvenance = ReferenceProvenance.UNKNOWN
    confidence: ReferenceConfidence = ReferenceConfidence.UNKNOWN

    def __post_init__(self) -> None:
        try:
            source_system = SourceSystem.parse(self.source_system)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The external reference source system is invalid.",
                context={"source_system": str(self.source_system)},
            ) from exc

        try:
            reference_type = ReferenceType.parse(self.reference_type)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The external reference type is invalid.",
                context={"reference_type": str(self.reference_type)},
            ) from exc

        try:
            provenance = ReferenceProvenance.parse(self.provenance)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The external reference provenance is invalid.",
                context={"provenance": str(self.provenance)},
            ) from exc

        try:
            confidence = ReferenceConfidence.parse(self.confidence)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The external reference confidence is invalid.",
                context={"confidence": str(self.confidence)},
            ) from exc

        value = _normalise_identifier_value(
            self.value,
            field_name="external_reference",
        )
        observed_at = _normalise_optional_datetime(
            self.observed_at,
            field_name="observed_at",
        )

        if not isinstance(self.is_primary, bool):
            raise InvalidIdentifierError(
                "is_primary must be a boolean.",
                context={"value_type": type(self.is_primary).__name__},
            )

        object.__setattr__(self, "source_system", source_system)
        object.__setattr__(self, "reference_type", reference_type)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "confidence", confidence)

    @classmethod
    def from_identifier(
        cls,
        identifier: DomainIdentifier,
        source_system: SourceSystem | str,
        *,
        is_primary: bool = False,
        observed_at: datetime | None = None,
        provenance: ReferenceProvenance | str = ReferenceProvenance.UNKNOWN,
        confidence: ReferenceConfidence | str = ReferenceConfidence.VERIFIED,
    ) -> ExternalReference:
        """Create a source reference from a typed domain identifier."""

        if not isinstance(identifier, DomainIdentifier):
            raise TypeError(
                "identifier must be a DomainIdentifier instance."
            )

        return cls(
            source_system=source_system,
            reference_type=type(identifier).reference_type,
            value=identifier.value,
            is_primary=is_primary,
            observed_at=observed_at,
            provenance=provenance,
            confidence=confidence,
        )

    @property
    def key(self) -> tuple[SourceSystem, ReferenceType, str]:
        return (self.source_system, self.reference_type, self.value)

    @property
    def namespace(self) -> tuple[SourceSystem, ReferenceType]:
        return (self.source_system, self.reference_type)

    def to_identifier(self, identifier_type: type[IdentifierT]) -> IdentifierT:
        if not isinstance(identifier_type, type) or not issubclass(
            identifier_type,
            DomainIdentifier,
        ):
            raise TypeError(
                "identifier_type must be a DomainIdentifier subclass."
            )

        expected_type = identifier_type.reference_type
        if self.reference_type is not expected_type:
            raise InvalidIdentifierError(
                "The external reference cannot be converted to the requested "
                "identifier type.",
                context={
                    "expected_reference_type": expected_type,
                    "actual_reference_type": self.reference_type,
                    "source_system": self.source_system,
                },
            )

        return identifier_type(self.value)

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "source_system": self.source_system.value,
            "reference_type": self.reference_type.value,
            "value": self.value,
            "is_primary": self.is_primary,
            "observed_at": (
                self.observed_at.isoformat()
                if self.observed_at is not None
                else None
            ),
            "provenance": self.provenance.value,
            "confidence": self.confidence.value,
        }


@dataclass(frozen=True, slots=True)
class CorrelationId:
    """UUID-backed trace identifier for processing and audit lineage."""

    value: UUID
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        value = self.value
        if isinstance(value, str):
            try:
                value = UUID(value.strip())
            except (ValueError, AttributeError) as exc:
                raise InvalidIdentifierError(
                    "The correlation ID is not a valid UUID.",
                    context={"field_name": "correlation_id"},
                ) from exc
        elif not isinstance(value, UUID):
            raise InvalidIdentifierError(
                "The correlation ID must be a UUID or UUID string.",
                context={"value_type": type(value).__name__},
            )

        created_at = _normalise_optional_datetime(
            self.created_at,
            field_name="created_at",
        )

        object.__setattr__(self, "value", value)
        object.__setattr__(self, "created_at", created_at)

    @classmethod
    def new(cls, *, created_at: datetime | None = None) -> CorrelationId:
        return cls(
            uuid4(),
            created_at=created_at or datetime.now(timezone.utc),
        )

    @classmethod
    def parse(
        cls,
        value: object,
        *,
        created_at: datetime | None = None,
    ) -> CorrelationId:
        if isinstance(value, cls):
            if created_at is not None and value.created_at != created_at:
                raise InvalidIdentifierError(
                    "The supplied correlation ID already has a different "
                    "creation timestamp.",
                    context={"field_name": "correlation_id"},
                )
            return value
        return cls(value, created_at=created_at)  # type: ignore[arg-type]

    @property
    def reference_type(self) -> ReferenceType:
        return ReferenceType.CORRELATION_ID

    def to_reference(
        self,
        source_system: SourceSystem | str = SourceSystem.PANGO_BACKEND,
        *,
        is_primary: bool = False,
        observed_at: datetime | None = None,
        provenance: ReferenceProvenance | str = ReferenceProvenance.DERIVED,
        confidence: ReferenceConfidence | str = ReferenceConfidence.VERIFIED,
    ) -> ExternalReference:
        return ExternalReference(
            source_system=source_system,
            reference_type=ReferenceType.CORRELATION_ID,
            value=str(self.value),
            is_primary=is_primary,
            observed_at=observed_at or self.created_at,
            provenance=provenance,
            confidence=confidence,
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "value": str(self.value),
            "reference_type": ReferenceType.CORRELATION_ID.value,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at is not None
                else None
            ),
        }

    def __str__(self) -> str:
        return str(self.value)


ReferenceKey = tuple[SourceSystem, ReferenceType, str]
ReferenceNamespace = tuple[SourceSystem, ReferenceType]


@dataclass(frozen=True, slots=True, init=False)
class ReferenceCollection:
    """Immutable, indexed, duplicate-safe collection of references."""

    _references: tuple[ExternalReference, ...]
    _by_key: Mapping[ReferenceKey, ExternalReference]
    _by_namespace: Mapping[ReferenceNamespace, tuple[ExternalReference, ...]]
    _by_source: Mapping[SourceSystem, tuple[ExternalReference, ...]]
    _by_type: Mapping[ReferenceType, tuple[ExternalReference, ...]]

    def __init__(
        self,
        references: Iterable[ExternalReference] = (),
    ) -> None:
        materialised = tuple(references)

        for reference in materialised:
            if not isinstance(reference, ExternalReference):
                raise InvalidIdentifierError(
                    "ReferenceCollection accepts ExternalReference instances "
                    "only.",
                    context={"value_type": type(reference).__name__},
                )

        ordered = tuple(
            sorted(
                materialised,
                key=lambda reference: (
                    reference.source_system.value,
                    reference.reference_type.value,
                    reference.value,
                    not reference.is_primary,
                ),
            )
        )

        by_key: dict[ReferenceKey, ExternalReference] = {}
        by_namespace_mutable: dict[
            ReferenceNamespace,
            list[ExternalReference],
        ] = {}
        by_source_mutable: dict[
            SourceSystem,
            list[ExternalReference],
        ] = {}
        by_type_mutable: dict[
            ReferenceType,
            list[ExternalReference],
        ] = {}
        primary_namespaces: set[ReferenceNamespace] = set()

        for reference in ordered:
            if reference.key in by_key:
                raise DuplicateRecordError(
                    "The same external reference was supplied more than once.",
                    context={
                        "source_system": reference.source_system,
                        "reference_type": reference.reference_type,
                        "reference_value": reference.value,
                    },
                )

            if reference.is_primary:
                if reference.namespace in primary_namespaces:
                    raise DuplicateRecordError(
                        "A reference namespace cannot contain multiple primary "
                        "references.",
                        context={
                            "source_system": reference.source_system,
                            "reference_type": reference.reference_type,
                        },
                    )
                primary_namespaces.add(reference.namespace)

            by_key[reference.key] = reference
            by_namespace_mutable.setdefault(reference.namespace, []).append(
                reference
            )
            by_source_mutable.setdefault(reference.source_system, []).append(
                reference
            )
            by_type_mutable.setdefault(reference.reference_type, []).append(
                reference
            )

        by_namespace = {
            key: tuple(values)
            for key, values in by_namespace_mutable.items()
        }
        by_source = {
            key: tuple(values)
            for key, values in by_source_mutable.items()
        }
        by_type = {
            key: tuple(values)
            for key, values in by_type_mutable.items()
        }

        object.__setattr__(self, "_references", ordered)
        object.__setattr__(self, "_by_key", MappingProxyType(by_key))
        object.__setattr__(
            self,
            "_by_namespace",
            MappingProxyType(by_namespace),
        )
        object.__setattr__(self, "_by_source", MappingProxyType(by_source))
        object.__setattr__(self, "_by_type", MappingProxyType(by_type))

    @classmethod
    def empty(cls) -> ReferenceCollection:
        return cls()

    def add(self, reference: ExternalReference) -> ReferenceCollection:
        return ReferenceCollection((*self._references, reference))

    def merge(
        self,
        other: ReferenceCollection | Iterable[ExternalReference],
    ) -> ReferenceCollection:
        additional = (
            other._references
            if isinstance(other, ReferenceCollection)
            else tuple(other)
        )
        return ReferenceCollection((*self._references, *additional))

    def get(
        self,
        source_system: SourceSystem | str,
        reference_type: ReferenceType | str,
        value: str,
    ) -> ExternalReference | None:
        """Return one exact reference in O(1) average time."""

        canonical_source = SourceSystem.parse(source_system)
        canonical_type = ReferenceType.parse(reference_type)
        canonical_value = _normalise_identifier_value(
            value,
            field_name="reference_value",
        )
        return self._by_key.get(
            (canonical_source, canonical_type, canonical_value)
        )

    def find(
        self,
        *,
        source_system: SourceSystem | str | None = None,
        reference_type: ReferenceType | str | None = None,
        value: str | None = None,
        primary_only: bool = False,
    ) -> tuple[ExternalReference, ...]:
        """Return references using indexed narrowing before final filtering."""

        canonical_source = (
            SourceSystem.parse(source_system)
            if source_system is not None
            else None
        )
        canonical_type = (
            ReferenceType.parse(reference_type)
            if reference_type is not None
            else None
        )
        canonical_value = (
            _normalise_identifier_value(
                value,
                field_name="reference_value",
            )
            if value is not None
            else None
        )

        if (
            canonical_source is not None
            and canonical_type is not None
            and canonical_value is not None
        ):
            exact = self._by_key.get(
                (canonical_source, canonical_type, canonical_value)
            )
            candidates = () if exact is None else (exact,)
        elif canonical_source is not None and canonical_type is not None:
            candidates = self._by_namespace.get(
                (canonical_source, canonical_type),
                (),
            )
        elif canonical_source is not None:
            candidates = self._by_source.get(canonical_source, ())
        elif canonical_type is not None:
            candidates = self._by_type.get(canonical_type, ())
        else:
            candidates = self._references

        return tuple(
            reference
            for reference in candidates
            if (
                canonical_value is None
                or reference.value == canonical_value
            )
            and (not primary_only or reference.is_primary)
        )

    def require_one(
        self,
        *,
        source_system: SourceSystem | str | None = None,
        reference_type: ReferenceType | str | None = None,
        value: str | None = None,
        primary_only: bool = False,
    ) -> ExternalReference:
        matches = self.find(
            source_system=source_system,
            reference_type=reference_type,
            value=value,
            primary_only=primary_only,
        )

        criteria: dict[str, str | bool] = {}
        if source_system is not None:
            criteria["source_system"] = SourceSystem.parse(
                source_system
            ).value
        if reference_type is not None:
            criteria["reference_type"] = ReferenceType.parse(
                reference_type
            ).value
        if value is not None:
            criteria["reference_value"] = value
        if primary_only:
            criteria["primary_only"] = True

        if not matches:
            raise ReferentialIntegrityError(
                "No external reference satisfies the requested criteria.",
                context=criteria,
            )

        if len(matches) > 1:
            raise ReferentialIntegrityError(
                "Multiple external references satisfy criteria that require "
                "one unique result.",
                context={**criteria, "match_count": len(matches)},
            )

        return matches[0]

    def contains(self, reference: ExternalReference) -> bool:
        return (
            isinstance(reference, ExternalReference)
            and reference.key in self._by_key
        )

    def to_tuple(self) -> tuple[ExternalReference, ...]:
        return self._references

    def to_dicts(self) -> tuple[dict[str, str | bool | None], ...]:
        return tuple(reference.to_dict() for reference in self._references)

    def __iter__(self) -> Iterator[ExternalReference]:
        return iter(self._references)

    def __len__(self) -> int:
        return len(self._references)

    def __bool__(self) -> bool:
        return bool(self._references)

    def __contains__(self, reference: object) -> bool:
        return isinstance(reference, ExternalReference) and self.contains(
            reference
        )

    def __getitem__(self, index: int) -> ExternalReference:
        return self._references[index]


@dataclass(frozen=True, slots=True)
class LineageEdge:
    """Directed, auditable relationship between two identity references."""

    source: ExternalReference
    target: ExternalReference
    relationship: ReferenceRelationship
    observed_at: datetime | None = None
    confidence: ReferenceConfidence = ReferenceConfidence.VERIFIED

    def __post_init__(self) -> None:
        if not isinstance(self.source, ExternalReference):
            raise InvalidIdentifierError(
                "Lineage edge source must be an ExternalReference.",
                context={"value_type": type(self.source).__name__},
            )
        if not isinstance(self.target, ExternalReference):
            raise InvalidIdentifierError(
                "Lineage edge target must be an ExternalReference.",
                context={"value_type": type(self.target).__name__},
            )

        try:
            relationship = ReferenceRelationship.parse(self.relationship)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The lineage relationship is invalid.",
                context={"relationship": str(self.relationship)},
            ) from exc

        try:
            confidence = ReferenceConfidence.parse(self.confidence)
        except (TypeError, ValueError) as exc:
            raise InvalidIdentifierError(
                "The lineage confidence is invalid.",
                context={"confidence": str(self.confidence)},
            ) from exc

        observed_at = _normalise_optional_datetime(
            self.observed_at,
            field_name="observed_at",
        )

        if self.source.key == self.target.key:
            raise InvalidIdentifierError(
                "A lineage edge cannot reference the same node as source and "
                "target.",
                context={
                    "source_system": self.source.source_system,
                    "reference_type": self.source.reference_type,
                },
            )

        object.__setattr__(self, "relationship", relationship)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "observed_at", observed_at)

    @property
    def key(
        self,
    ) -> tuple[ReferenceKey, ReferenceKey, ReferenceRelationship]:
        return (self.source.key, self.target.key, self.relationship)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "relationship": self.relationship.value,
            "observed_at": (
                self.observed_at.isoformat()
                if self.observed_at is not None
                else None
            ),
            "confidence": self.confidence.value,
        }


@dataclass(frozen=True, slots=True, init=False)
class IdentityGraph:
    """Immutable indexed graph for cross-system financial identity lineage."""

    references: ReferenceCollection
    edges: tuple[LineageEdge, ...]
    _outgoing: Mapping[ReferenceKey, tuple[LineageEdge, ...]]
    _incoming: Mapping[ReferenceKey, tuple[LineageEdge, ...]]

    def __init__(
        self,
        references: ReferenceCollection | Iterable[ExternalReference] = (),
        edges: Iterable[LineageEdge] = (),
    ) -> None:
        collection = (
            references
            if isinstance(references, ReferenceCollection)
            else ReferenceCollection(references)
        )
        materialised_edges = tuple(edges)

        seen_edges: set[
            tuple[ReferenceKey, ReferenceKey, ReferenceRelationship]
        ] = set()
        outgoing_mutable: dict[ReferenceKey, list[LineageEdge]] = {}
        incoming_mutable: dict[ReferenceKey, list[LineageEdge]] = {}

        for edge in materialised_edges:
            if not isinstance(edge, LineageEdge):
                raise InvalidIdentifierError(
                    "IdentityGraph accepts LineageEdge instances only.",
                    context={"value_type": type(edge).__name__},
                )

            if edge.source not in collection:
                raise ReferentialIntegrityError(
                    "The lineage source reference is absent from the graph.",
                    context={
                        "source_system": edge.source.source_system,
                        "reference_type": edge.source.reference_type,
                        "reference_value": edge.source.value,
                    },
                )

            if edge.target not in collection:
                raise ReferentialIntegrityError(
                    "The lineage target reference is absent from the graph.",
                    context={
                        "source_system": edge.target.source_system,
                        "reference_type": edge.target.reference_type,
                        "reference_value": edge.target.value,
                    },
                )

            if edge.key in seen_edges:
                raise DuplicateRecordError(
                    "The same lineage edge was supplied more than once.",
                    context={
                        "relationship": edge.relationship,
                        "source_value": edge.source.value,
                        "target_value": edge.target.value,
                    },
                )

            seen_edges.add(edge.key)
            outgoing_mutable.setdefault(edge.source.key, []).append(edge)
            incoming_mutable.setdefault(edge.target.key, []).append(edge)

        ordered_edges = tuple(
            sorted(
                materialised_edges,
                key=lambda edge: (
                    edge.source.key,
                    edge.target.key,
                    edge.relationship.value,
                ),
            )
        )

        outgoing = {
            key: tuple(values)
            for key, values in outgoing_mutable.items()
        }
        incoming = {
            key: tuple(values)
            for key, values in incoming_mutable.items()
        }

        object.__setattr__(self, "references", collection)
        object.__setattr__(self, "edges", ordered_edges)
        object.__setattr__(
            self,
            "_outgoing",
            MappingProxyType(outgoing),
        )
        object.__setattr__(
            self,
            "_incoming",
            MappingProxyType(incoming),
        )

    @classmethod
    def empty(cls) -> IdentityGraph:
        return cls()

    def add_reference(
        self,
        reference: ExternalReference,
    ) -> IdentityGraph:
        return IdentityGraph(
            self.references.add(reference),
            self.edges,
        )

    def add_edge(self, edge: LineageEdge) -> IdentityGraph:
        updated_references = self.references
        if edge.source not in updated_references:
            updated_references = updated_references.add(edge.source)
        if edge.target not in updated_references:
            updated_references = updated_references.add(edge.target)

        return IdentityGraph(
            updated_references,
            (*self.edges, edge),
        )

    def outgoing(
        self,
        reference: ExternalReference,
        *,
        relationship: ReferenceRelationship | str | None = None,
    ) -> tuple[LineageEdge, ...]:
        if not isinstance(reference, ExternalReference):
            raise TypeError("reference must be an ExternalReference.")

        candidates = self._outgoing.get(reference.key, ())
        if relationship is None:
            return candidates

        canonical_relationship = ReferenceRelationship.parse(relationship)
        return tuple(
            edge
            for edge in candidates
            if edge.relationship is canonical_relationship
        )

    def incoming(
        self,
        reference: ExternalReference,
        *,
        relationship: ReferenceRelationship | str | None = None,
    ) -> tuple[LineageEdge, ...]:
        if not isinstance(reference, ExternalReference):
            raise TypeError("reference must be an ExternalReference.")

        candidates = self._incoming.get(reference.key, ())
        if relationship is None:
            return candidates

        canonical_relationship = ReferenceRelationship.parse(relationship)
        return tuple(
            edge
            for edge in candidates
            if edge.relationship is canonical_relationship
        )

    def neighbours(
        self,
        reference: ExternalReference,
    ) -> tuple[ExternalReference, ...]:
        """Return unique directly connected references in deterministic order."""

        connected: dict[ReferenceKey, ExternalReference] = {}

        for edge in self.outgoing(reference):
            connected[edge.target.key] = edge.target
        for edge in self.incoming(reference):
            connected[edge.source.key] = edge.source

        return tuple(
            connected[key]
            for key in sorted(connected)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "references": self.references.to_dicts(),
            "edges": tuple(edge.to_dict() for edge in self.edges),
        }

    def __len__(self) -> int:
        return len(self.references)

    def __bool__(self) -> bool:
        return bool(self.references)


__all__ = [
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
]