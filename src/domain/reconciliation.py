"""Canonical reconciliation value objects for Pango Revenue Assurance.

This module defines the immutable output contract of every reconciliation rule.
It does not extract data, perform provider-specific matching, query databases,
or depend on pandas. Matching engines produce these objects; reporting,
alerting, APIs, dashboards, n8n workflows, and future AI agents consume them.

Core design:
- evidence explains why a decision was made;
- differences quantify why records do not agree;
- materiality translates variance into business significance;
- risk is deterministic and auditable;
- results are immutable, serializable, and reproducible;
- summaries aggregate results without losing monetary precision.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, unique
from types import MappingProxyType
from typing import ClassVar, Final, TypeAlias
from uuid import UUID, uuid4

from .enums import (
    CanonicalStrEnum,
    ExceptionType,
    MatchMethod,
    ReconciliationStatus,
    RiskLevel,
)
from .exceptions import (
    AmbiguousMatchError,
    DomainValidationError,
    InvalidTimestampError,
    InvariantViolationError,
    ReconciliationInvariantError,
)
from .identifiers import (
    CorrelationId,
    ExternalReference,
    IdentityGraph,
    ReferenceCollection,
    ReferenceConfidence,
)
from .money import Money


# ---------------------------------------------------------------------------
# Reconciliation-specific vocabulary
# ---------------------------------------------------------------------------


@unique
class ReconciliationScope(CanonicalStrEnum):
    """Financial lifecycle segment evaluated by a reconciliation result."""

    OPERATIONAL_EVENT_TO_PAYMENT = "operational_event_to_payment"
    PAYMENT_TO_SETTLEMENT = "payment_to_settlement"
    SETTLEMENT_TO_PAYOUT = "settlement_to_payout"
    PAYOUT_TO_BANK = "payout_to_bank"
    BANK_TO_ACCOUNTING = "bank_to_accounting"
    REFUND_END_TO_END = "refund_end_to_end"
    END_TO_END = "end_to_end"
    INTRA_SOURCE = "intra_source"
    OTHER = "other"


@unique
class DifferenceType(CanonicalStrEnum):
    """Canonical dimension in which expected and actual facts differ."""

    AMOUNT = "amount"
    CURRENCY = "currency"
    DATE = "date"
    REFERENCE = "reference"
    STATUS = "status"
    COUNT = "count"
    FEE = "fee"
    REFUND = "refund"
    DUPLICATE = "duplicate"
    MISSING_RECORD = "missing_record"
    DATA_QUALITY = "data_quality"
    OTHER = "other"


@unique
class EvidenceType(CanonicalStrEnum):
    """Type of evidence supporting a reconciliation decision."""

    IDENTIFIER = "identifier"
    EXTERNAL_REFERENCE = "external_reference"
    AMOUNT = "amount"
    DATE = "date"
    STATUS = "status"
    AGGREGATION = "aggregation"
    LINEAGE = "lineage"
    MANUAL_REVIEW = "manual_review"
    RULE_EXECUTION = "rule_execution"
    OTHER = "other"


@unique
class MaterialityLevel(CanonicalStrEnum):
    """Business significance of an amount variance."""

    IMMATERIAL = "immaterial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Shared types and validation helpers
# ---------------------------------------------------------------------------


DiagnosticInputValue: TypeAlias = (
    str | int | float | bool | None | Decimal | datetime | UUID | Enum
)
DiagnosticValue: TypeAlias = str | int | float | bool | None
DiagnosticInput: TypeAlias = Mapping[str, DiagnosticInputValue]
FrozenDiagnostics: TypeAlias = Mapping[str, DiagnosticValue]


def _parse_enum(
    enum_type: type[CanonicalStrEnum],
    value: object,
    *,
    field_name: str,
) -> CanonicalStrEnum:
    try:
        return enum_type.parse(value)
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
            "A reconciliation timestamp must be a datetime value.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidTimestampError(
            "Reconciliation timestamps must be timezone-aware.",
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
    max_length: int = 4096,
) -> str:
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
        raise DomainValidationError(
            f"The {field_name} value cannot be empty.",
            context={"field_name": field_name},
        )
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
    max_length: int = 4096,
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


def _normalise_score(value: object, *, field_name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainValidationError(
            f"The {field_name} score must be Decimal or int.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    if isinstance(value, int):
        candidate = Decimal(value)
    elif isinstance(value, Decimal):
        candidate = value
    else:
        raise DomainValidationError(
            f"The {field_name} score must be Decimal or int.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )
    if not candidate.is_finite():
        raise DomainValidationError(
            f"The {field_name} score must be finite.",
            context={"field_name": field_name, "value": str(candidate)},
        )
    if candidate < 0 or candidate > 100:
        raise DomainValidationError(
            f"The {field_name} score must be between 0 and 100.",
            context={"field_name": field_name, "value": str(candidate)},
        )
    return candidate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalise_confidence(value: object) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainValidationError(
            "confidence_score must be Decimal or int.",
            context={"value_type": type(value).__name__},
        )
    if isinstance(value, int):
        candidate = Decimal(value)
    elif isinstance(value, Decimal):
        candidate = value
    else:
        raise DomainValidationError(
            "confidence_score must be Decimal or int.",
            context={"value_type": type(value).__name__},
        )
    if not candidate.is_finite() or candidate < 0 or candidate > 1:
        raise DomainValidationError(
            "confidence_score must be finite and between 0 and 1.",
            context={"value": str(candidate)},
        )
    return candidate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _normalise_diagnostic_value(
    key: str,
    value: DiagnosticInputValue,
) -> DiagnosticValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DomainValidationError(
                "Diagnostic floats must be finite.",
                context={"diagnostic_key": key, "value": str(value)},
            )
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise DomainValidationError(
                "Diagnostic Decimal values must be finite.",
                context={"diagnostic_key": key, "value": str(value)},
            )
        return str(value)
    if isinstance(value, datetime):
        return _require_datetime(
            value,
            field_name=f"diagnostics.{key}",
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
        "Diagnostic values must be JSON-compatible scalars.",
        context={
            "diagnostic_key": key,
            "value_type": type(value).__name__,
        },
    )


def _freeze_diagnostics(
    diagnostics: DiagnosticInput | None,
) -> FrozenDiagnostics:
    if diagnostics is None:
        return MappingProxyType({})
    if not isinstance(diagnostics, Mapping):
        raise DomainValidationError(
            "diagnostics must be a mapping.",
            context={"value_type": type(diagnostics).__name__},
        )
    normalized: dict[str, DiagnosticValue] = {}
    for raw_key, raw_value in diagnostics.items():
        if not isinstance(raw_key, str):
            raise DomainValidationError(
                "Diagnostic keys must be strings.",
                context={"key_type": type(raw_key).__name__},
            )
        key = raw_key.strip()
        if not key:
            raise DomainValidationError("Diagnostic keys cannot be empty.")
        if key in normalized:
            raise DomainValidationError(
                "Diagnostics contain duplicate keys after normalization.",
                context={"diagnostic_key": key},
            )
        normalized[key] = _normalise_diagnostic_value(key, raw_value)
    return MappingProxyType(normalized)


def _normalise_references(
    references: ReferenceCollection | Iterable[ExternalReference],
) -> ReferenceCollection:
    if isinstance(references, ReferenceCollection):
        return references
    return ReferenceCollection(references)


def _require_unique_text_values(
    values: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(
        sorted(
            {
                _require_text(
                    value,
                    field_name=field_name,
                    max_length=512,
                )
                for value in values
            }
        )
    )
    return normalized


# ---------------------------------------------------------------------------
# Materiality and risk policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MaterialityPolicy:
    """Explicit absolute and relative thresholds for amount variances."""

    low_threshold: Money
    medium_threshold: Money
    high_threshold: Money
    critical_threshold: Money
    relative_low: Decimal = Decimal("0.001")
    relative_medium: Decimal = Decimal("0.005")
    relative_high: Decimal = Decimal("0.01")
    relative_critical: Decimal = Decimal("0.05")

    def __post_init__(self) -> None:
        thresholds = (
            self.low_threshold,
            self.medium_threshold,
            self.high_threshold,
            self.critical_threshold,
        )
        for index, threshold in enumerate(thresholds):
            _require_money(threshold, field_name=f"threshold_{index}")
            if threshold.is_negative:
                raise InvariantViolationError(
                    "Materiality thresholds cannot be negative."
                )
        if len({threshold.currency for threshold in thresholds}) != 1:
            raise InvariantViolationError(
                "All materiality thresholds must use the same currency."
            )
        if not (
            self.low_threshold
            <= self.medium_threshold
            <= self.high_threshold
            <= self.critical_threshold
        ):
            raise InvariantViolationError(
                "Materiality amount thresholds must be non-decreasing."
            )

        relatives: list[Decimal] = []
        for name in (
            "relative_low",
            "relative_medium",
            "relative_high",
            "relative_critical",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or isinstance(value, float):
                raise DomainValidationError(
                    "Relative materiality thresholds must be Decimal.",
                    context={"field_name": name},
                )
            if isinstance(value, int):
                value = Decimal(value)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise DomainValidationError(
                    "Relative materiality thresholds must be finite Decimal.",
                    context={"field_name": name},
                )
            if value < 0:
                raise InvariantViolationError(
                    "Relative materiality thresholds cannot be negative.",
                    context={"field_name": name},
                )
            relatives.append(value)
            object.__setattr__(self, name, value)

        if relatives != sorted(relatives):
            raise InvariantViolationError(
                "Relative materiality thresholds must be non-decreasing."
            )

    @classmethod
    def usd_default(cls) -> MaterialityPolicy:
        """Conservative starting policy; configurable by deployment."""

        return cls(
            low_threshold=Money.of("1.00"),
            medium_threshold=Money.of("25.00"),
            high_threshold=Money.of("250.00"),
            critical_threshold=Money.of("2500.00"),
        )

    def assess(
        self,
        absolute_variance: Money,
        *,
        expected_amount: Money | None = None,
    ) -> MaterialityLevel:
        absolute_variance = _require_money(
            absolute_variance,
            field_name="absolute_variance",
        )
        if absolute_variance.currency is not self.low_threshold.currency:
            raise InvariantViolationError(
                "Materiality policy and variance currency differ.",
                context={
                    "policy_currency": self.low_threshold.currency,
                    "variance_currency": absolute_variance.currency,
                },
            )

        if absolute_variance >= self.critical_threshold:
            absolute_level = MaterialityLevel.CRITICAL
        elif absolute_variance >= self.high_threshold:
            absolute_level = MaterialityLevel.HIGH
        elif absolute_variance >= self.medium_threshold:
            absolute_level = MaterialityLevel.MEDIUM
        elif absolute_variance >= self.low_threshold:
            absolute_level = MaterialityLevel.LOW
        else:
            absolute_level = MaterialityLevel.IMMATERIAL

        relative_level = MaterialityLevel.IMMATERIAL
        if expected_amount is not None and not expected_amount.is_zero:
            if expected_amount.currency is not absolute_variance.currency:
                raise InvariantViolationError(
                    "Expected amount and variance currency differ."
                )
            relative = absolute_variance.ratio(expected_amount.absolute())
            if relative >= self.relative_critical:
                relative_level = MaterialityLevel.CRITICAL
            elif relative >= self.relative_high:
                relative_level = MaterialityLevel.HIGH
            elif relative >= self.relative_medium:
                relative_level = MaterialityLevel.MEDIUM
            elif relative >= self.relative_low:
                relative_level = MaterialityLevel.LOW

        order = {
            MaterialityLevel.IMMATERIAL: 0,
            MaterialityLevel.LOW: 1,
            MaterialityLevel.MEDIUM: 2,
            MaterialityLevel.HIGH: 3,
            MaterialityLevel.CRITICAL: 4,
        }
        return max(
            (absolute_level, relative_level),
            key=order.__getitem__,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "low_threshold": self.low_threshold.to_dict(),
            "medium_threshold": self.medium_threshold.to_dict(),
            "high_threshold": self.high_threshold.to_dict(),
            "critical_threshold": self.critical_threshold.to_dict(),
            "relative_low": str(self.relative_low),
            "relative_medium": str(self.relative_medium),
            "relative_high": str(self.relative_high),
            "relative_critical": str(self.relative_critical),
        }


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """Deterministic business-risk assessment attached to a result."""

    score: Decimal
    level: RiskLevel
    rationale: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        score = _normalise_score(self.score, field_name="risk")
        level = _parse_enum(RiskLevel, self.level, field_name="risk_level")
        rationale = _require_unique_text_values(
            self.rationale,
            field_name="risk_rationale",
        )

        expected_level = self.level_for_score(score)
        if level is not expected_level:
            raise InvariantViolationError(
                "Risk level does not match the risk score.",
                context={
                    "score": score,
                    "supplied_level": level,
                    "expected_level": expected_level,
                },
            )

        object.__setattr__(self, "score", score)
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "rationale", rationale)

    @staticmethod
    def level_for_score(score: Decimal) -> RiskLevel:
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 50:
            return RiskLevel.HIGH
        if score >= 20:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @classmethod
    def from_score(
        cls,
        score: Decimal | int,
        *,
        rationale: Iterable[str] = (),
    ) -> RiskAssessment:
        normalized = _normalise_score(score, field_name="risk")
        return cls(
            score=normalized,
            level=cls.level_for_score(normalized),
            rationale=tuple(rationale),
        )

    @classmethod
    def calculate(
        cls,
        *,
        status: ReconciliationStatus,
        materiality: MaterialityLevel,
        exception_types: Iterable[ExceptionType] = (),
        confidence_score: Decimal = Decimal("1"),
    ) -> RiskAssessment:
        """Calculate a transparent score from reconciliation facts."""

        status = _parse_enum(
            ReconciliationStatus,
            status,
            field_name="status",
        )
        materiality = _parse_enum(
            MaterialityLevel,
            materiality,
            field_name="materiality",
        )
        confidence = _normalise_confidence(confidence_score)
        exceptions = tuple(
            _parse_enum(
                ExceptionType,
                item,
                field_name="exception_type",
            )
            for item in exception_types
        )

        score = {
            ReconciliationStatus.MATCHED: Decimal("0"),
            ReconciliationStatus.EXCLUDED: Decimal("0"),
            ReconciliationStatus.PARTIALLY_MATCHED: Decimal("30"),
            ReconciliationStatus.REVIEW_REQUIRED: Decimal("45"),
            ReconciliationStatus.UNMATCHED: Decimal("65"),
            ReconciliationStatus.ERROR: Decimal("75"),
        }[status]

        materiality_increment = {
            MaterialityLevel.IMMATERIAL: Decimal("0"),
            MaterialityLevel.LOW: Decimal("5"),
            MaterialityLevel.MEDIUM: Decimal("15"),
            MaterialityLevel.HIGH: Decimal("25"),
            MaterialityLevel.CRITICAL: Decimal("35"),
        }[materiality]
        score += materiality_increment

        severe_types = {
            ExceptionType.MISSING_PAYMENT,
            ExceptionType.MISSING_BANK_DEPOSIT,
            ExceptionType.DUPLICATE_TRANSACTION,
            ExceptionType.SUSPICIOUS_REFUND,
            ExceptionType.SUSPICIOUS_ADJUSTMENT,
        }
        if any(item in severe_types for item in exceptions):
            score += Decimal("10")

        if confidence < Decimal("0.50") and status not in {
            ReconciliationStatus.MATCHED,
            ReconciliationStatus.EXCLUDED,
        }:
            score += Decimal("5")

        score = min(score, Decimal("100"))
        rationale = [
            f"status={status.value}",
            f"materiality={materiality.value}",
            f"confidence={confidence}",
        ]
        if exceptions:
            rationale.append(
                "exceptions=" + ",".join(sorted(item.value for item in exceptions))
            )

        return cls.from_score(score, rationale=rationale)

    def to_dict(self) -> dict[str, object]:
        return {
            "score": str(self.score),
            "level": self.level.value,
            "rationale": list(self.rationale),
        }


# ---------------------------------------------------------------------------
# Differences and evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MoneyDifference:
    """Expected-versus-actual monetary variance."""

    expected: Money
    actual: Money
    tolerance: Money
    signed_variance: Money = field(init=False)
    absolute_variance: Money = field(init=False)
    relative_variance: Decimal | None = field(init=False)
    within_tolerance: bool = field(init=False)

    def __post_init__(self) -> None:
        expected = _require_money(self.expected, field_name="expected")
        actual = _require_money(self.actual, field_name="actual")
        tolerance = _require_money(self.tolerance, field_name="tolerance")

        if len({expected.currency, actual.currency, tolerance.currency}) != 1:
            raise InvariantViolationError(
                "MoneyDifference values must use the same currency."
            )
        if tolerance.is_negative:
            raise InvariantViolationError(
                "MoneyDifference tolerance cannot be negative."
            )

        signed = actual - expected
        absolute = signed.absolute()
        relative = (
            None
            if expected.is_zero
            else absolute.ratio(expected.absolute())
        )

        object.__setattr__(self, "expected", expected)
        object.__setattr__(self, "actual", actual)
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "signed_variance", signed)
        object.__setattr__(self, "absolute_variance", absolute)
        object.__setattr__(self, "relative_variance", relative)
        object.__setattr__(
            self,
            "within_tolerance",
            absolute <= tolerance,
        )

    def assess_materiality(
        self,
        policy: MaterialityPolicy,
    ) -> MaterialityLevel:
        return policy.assess(
            self.absolute_variance,
            expected_amount=self.expected,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "expected": self.expected.to_dict(),
            "actual": self.actual.to_dict(),
            "tolerance": self.tolerance.to_dict(),
            "signed_variance": self.signed_variance.to_dict(),
            "absolute_variance": self.absolute_variance.to_dict(),
            "relative_variance": (
                str(self.relative_variance)
                if self.relative_variance is not None
                else None
            ),
            "within_tolerance": self.within_tolerance,
        }


@dataclass(frozen=True, slots=True)
class TimestampDifference:
    """Expected-versus-actual timing variance."""

    expected: datetime
    actual: datetime
    tolerance_seconds: int = 0
    signed_seconds: Decimal = field(init=False)
    absolute_seconds: Decimal = field(init=False)
    within_tolerance: bool = field(init=False)

    def __post_init__(self) -> None:
        expected = _require_datetime(self.expected, field_name="expected")
        actual = _require_datetime(self.actual, field_name="actual")
        if isinstance(self.tolerance_seconds, bool) or not isinstance(
            self.tolerance_seconds,
            int,
        ):
            raise DomainValidationError(
                "tolerance_seconds must be an integer."
            )
        if self.tolerance_seconds < 0:
            raise InvariantViolationError(
                "tolerance_seconds cannot be negative."
            )

        signed = Decimal(str((actual - expected).total_seconds()))
        absolute = abs(signed)

        object.__setattr__(self, "expected", expected)
        object.__setattr__(self, "actual", actual)
        object.__setattr__(self, "signed_seconds", signed)
        object.__setattr__(self, "absolute_seconds", absolute)
        object.__setattr__(
            self,
            "within_tolerance",
            absolute <= Decimal(self.tolerance_seconds),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "expected": self.expected.isoformat(),
            "actual": self.actual.isoformat(),
            "tolerance_seconds": self.tolerance_seconds,
            "signed_seconds": str(self.signed_seconds),
            "absolute_seconds": str(self.absolute_seconds),
            "within_tolerance": self.within_tolerance,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationDifference:
    """One typed discrepancy found during reconciliation."""

    difference_type: DifferenceType
    reason: ExceptionType
    description: str
    field_name: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None
    money: MoneyDifference | None = None
    timestamp: TimestampDifference | None = None
    materiality: MaterialityLevel = MaterialityLevel.IMMATERIAL
    diagnostics: FrozenDiagnostics = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        difference_type = _parse_enum(
            DifferenceType,
            self.difference_type,
            field_name="difference_type",
        )
        reason = _parse_enum(
            ExceptionType,
            self.reason,
            field_name="reason",
        )
        materiality = _parse_enum(
            MaterialityLevel,
            self.materiality,
            field_name="materiality",
        )
        description = _require_text(
            self.description,
            field_name="description",
        )
        field_name = _optional_text(
            self.field_name,
            field_name="field_name",
            max_length=256,
        )
        expected_value = _optional_text(
            self.expected_value,
            field_name="expected_value",
        )
        actual_value = _optional_text(
            self.actual_value,
            field_name="actual_value",
        )

        if self.money is not None and not isinstance(
            self.money,
            MoneyDifference,
        ):
            raise DomainValidationError(
                "money must be a MoneyDifference."
            )
        if self.timestamp is not None and not isinstance(
            self.timestamp,
            TimestampDifference,
        ):
            raise DomainValidationError(
                "timestamp must be a TimestampDifference."
            )
        if self.money is not None and self.timestamp is not None:
            raise InvariantViolationError(
                "A difference cannot contain both money and timestamp details."
            )
        if (
            difference_type is DifferenceType.AMOUNT
            and self.money is None
        ):
            raise InvariantViolationError(
                "Amount differences require MoneyDifference details."
            )
        if (
            difference_type is DifferenceType.DATE
            and self.timestamp is None
        ):
            raise InvariantViolationError(
                "Date differences require TimestampDifference details."
            )
        if self.money is not None:
            if self.money.within_tolerance:
                raise InvariantViolationError(
                    "A recorded amount difference cannot be within tolerance."
                )
            if materiality is MaterialityLevel.IMMATERIAL:
                # Immaterial is valid only when explicitly produced by policy;
                # do not infer a different level here.
                pass
        if self.timestamp is not None and self.timestamp.within_tolerance:
            raise InvariantViolationError(
                "A recorded date difference cannot be within tolerance."
            )

        object.__setattr__(self, "difference_type", difference_type)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "materiality", materiality)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "field_name", field_name)
        object.__setattr__(self, "expected_value", expected_value)
        object.__setattr__(self, "actual_value", actual_value)
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "difference_type": self.difference_type.value,
            "reason": self.reason.value,
            "description": self.description,
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "money": (
                self.money.to_dict() if self.money is not None else None
            ),
            "timestamp": (
                self.timestamp.to_dict()
                if self.timestamp is not None
                else None
            ),
            "materiality": self.materiality.value,
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    """One auditable fact supporting a reconciliation conclusion."""

    evidence_type: EvidenceType
    description: str
    confidence: ReferenceConfidence
    source_references: ReferenceCollection = field(
        default_factory=ReferenceCollection.empty
    )
    observed_at: datetime | None = None
    rule_id: str | None = None
    diagnostics: FrozenDiagnostics = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        evidence_type = _parse_enum(
            EvidenceType,
            self.evidence_type,
            field_name="evidence_type",
        )
        confidence = _parse_enum(
            ReferenceConfidence,
            self.confidence,
            field_name="confidence",
        )
        description = _require_text(
            self.description,
            field_name="description",
        )
        observed_at = _optional_datetime(
            self.observed_at,
            field_name="observed_at",
        )
        rule_id = _optional_text(
            self.rule_id,
            field_name="rule_id",
            max_length=256,
        )
        references = _normalise_references(self.source_references)

        if (
            evidence_type
            in {EvidenceType.IDENTIFIER, EvidenceType.EXTERNAL_REFERENCE}
            and not references
        ):
            raise InvariantViolationError(
                "Identifier/reference evidence requires source references."
            )

        object.__setattr__(self, "evidence_type", evidence_type)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "source_references", references)
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_type": self.evidence_type.value,
            "description": self.description,
            "confidence": self.confidence.value,
            "source_references": list(self.source_references.to_dicts()),
            "observed_at": (
                self.observed_at.isoformat()
                if self.observed_at is not None
                else None
            ),
            "rule_id": self.rule_id,
            "diagnostics": dict(self.diagnostics),
        }


# ---------------------------------------------------------------------------
# Reconciliation result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Immutable, auditable result produced by one reconciliation decision."""

    result_id: UUID
    scope: ReconciliationScope
    status: ReconciliationStatus
    match_method: MatchMethod
    evaluated_at: datetime
    left_entity_ids: tuple[str, ...]
    right_entity_ids: tuple[str, ...]
    evidence: tuple[MatchEvidence, ...] = ()
    differences: tuple[ReconciliationDifference, ...] = ()
    confidence_score: Decimal = Decimal("0")
    materiality: MaterialityLevel = MaterialityLevel.IMMATERIAL
    risk: RiskAssessment | None = None
    correlation_id: CorrelationId | None = None
    identity_graph: IdentityGraph | None = None
    rule_id: str | None = None
    rule_version: str | None = None
    created_by: str = "reconciliation_engine"
    diagnostics: FrozenDiagnostics = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        result_id = self.result_id
        if isinstance(result_id, str):
            try:
                result_id = UUID(result_id.strip())
            except (ValueError, AttributeError) as exc:
                raise DomainValidationError(
                    "result_id must be a valid UUID."
                ) from exc
        elif not isinstance(result_id, UUID):
            raise DomainValidationError(
                "result_id must be a UUID.",
                context={"value_type": type(result_id).__name__},
            )

        scope = _parse_enum(
            ReconciliationScope,
            self.scope,
            field_name="scope",
        )
        status = _parse_enum(
            ReconciliationStatus,
            self.status,
            field_name="status",
        )
        match_method = _parse_enum(
            MatchMethod,
            self.match_method,
            field_name="match_method",
        )
        evaluated_at = _require_datetime(
            self.evaluated_at,
            field_name="evaluated_at",
        )
        left_ids = _require_unique_text_values(
            self.left_entity_ids,
            field_name="left_entity_id",
        )
        right_ids = _require_unique_text_values(
            self.right_entity_ids,
            field_name="right_entity_id",
        )
        evidence = tuple(self.evidence)
        differences = tuple(self.differences)

        if any(not isinstance(item, MatchEvidence) for item in evidence):
            raise DomainValidationError(
                "evidence must contain MatchEvidence instances only."
            )
        if any(
            not isinstance(item, ReconciliationDifference)
            for item in differences
        ):
            raise DomainValidationError(
                "differences must contain ReconciliationDifference instances only."
            )

        confidence_score = _normalise_confidence(self.confidence_score)
        materiality = _parse_enum(
            MaterialityLevel,
            self.materiality,
            field_name="materiality",
        )
        correlation_id = (
            None
            if self.correlation_id is None
            else CorrelationId.parse(self.correlation_id)
        )
        if self.identity_graph is not None and not isinstance(
            self.identity_graph,
            IdentityGraph,
        ):
            raise DomainValidationError(
                "identity_graph must be an IdentityGraph."
            )
        rule_id = _optional_text(
            self.rule_id,
            field_name="rule_id",
            max_length=256,
        )
        rule_version = _optional_text(
            self.rule_version,
            field_name="rule_version",
            max_length=64,
        )
        created_by = _require_text(
            self.created_by,
            field_name="created_by",
            max_length=256,
        )

        self._validate_state_contract(
            status=status,
            match_method=match_method,
            left_ids=left_ids,
            right_ids=right_ids,
            evidence=evidence,
            differences=differences,
            confidence_score=confidence_score,
        )

        derived_materiality = self._highest_materiality(differences)
        if differences and materiality is not derived_materiality:
            raise ReconciliationInvariantError(
                "Result materiality must equal the highest difference materiality.",
                context={
                    "supplied_materiality": materiality,
                    "derived_materiality": derived_materiality,
                },
            )
        if not differences and materiality is not MaterialityLevel.IMMATERIAL:
            raise ReconciliationInvariantError(
                "A result without differences must be immaterial."
            )

        exception_types = tuple(
            sorted(
                {difference.reason for difference in differences},
                key=lambda item: item.value,
            )
        )
        calculated_risk = RiskAssessment.calculate(
            status=status,
            materiality=materiality,
            exception_types=exception_types,
            confidence_score=confidence_score,
        )
        if self.risk is not None:
            if not isinstance(self.risk, RiskAssessment):
                raise DomainValidationError(
                    "risk must be a RiskAssessment."
                )
            if self.risk != calculated_risk:
                raise ReconciliationInvariantError(
                    "Supplied risk assessment does not match deterministic policy.",
                    context={
                        "supplied_score": self.risk.score,
                        "calculated_score": calculated_risk.score,
                    },
                )
            risk = self.risk
        else:
            risk = calculated_risk

        object.__setattr__(self, "result_id", result_id)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "match_method", match_method)
        object.__setattr__(self, "evaluated_at", evaluated_at)
        object.__setattr__(self, "left_entity_ids", left_ids)
        object.__setattr__(self, "right_entity_ids", right_ids)
        object.__setattr__(
            self,
            "evidence",
            tuple(sorted(evidence, key=self._evidence_sort_key)),
        )
        object.__setattr__(
            self,
            "differences",
            tuple(sorted(differences, key=self._difference_sort_key)),
        )
        object.__setattr__(self, "confidence_score", confidence_score)
        object.__setattr__(self, "materiality", materiality)
        object.__setattr__(self, "risk", risk)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "rule_version", rule_version)
        object.__setattr__(self, "created_by", created_by)
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics),
        )

    @staticmethod
    def _highest_materiality(
        differences: Sequence[ReconciliationDifference],
    ) -> MaterialityLevel:
        order = {
            MaterialityLevel.IMMATERIAL: 0,
            MaterialityLevel.LOW: 1,
            MaterialityLevel.MEDIUM: 2,
            MaterialityLevel.HIGH: 3,
            MaterialityLevel.CRITICAL: 4,
        }
        if not differences:
            return MaterialityLevel.IMMATERIAL
        return max(
            (difference.materiality for difference in differences),
            key=order.__getitem__,
        )

    @staticmethod
    def _evidence_sort_key(
        evidence: MatchEvidence,
    ) -> tuple[str, str, str]:
        return (
            evidence.evidence_type.value,
            evidence.rule_id or "",
            evidence.description,
        )

    @staticmethod
    def _difference_sort_key(
        difference: ReconciliationDifference,
    ) -> tuple[str, str, str]:
        return (
            difference.difference_type.value,
            difference.field_name or "",
            difference.description,
        )

    @staticmethod
    def _validate_state_contract(
        *,
        status: ReconciliationStatus,
        match_method: MatchMethod,
        left_ids: tuple[str, ...],
        right_ids: tuple[str, ...],
        evidence: tuple[MatchEvidence, ...],
        differences: tuple[ReconciliationDifference, ...],
        confidence_score: Decimal,
    ) -> None:
        if status is ReconciliationStatus.MATCHED:
            if not left_ids or not right_ids:
                raise ReconciliationInvariantError(
                    "Matched results require entities on both sides."
                )
            if match_method is MatchMethod.NONE:
                raise ReconciliationInvariantError(
                    "Matched results require a match method."
                )
            if not evidence:
                raise ReconciliationInvariantError(
                    "Matched results require supporting evidence."
                )
            if differences:
                raise ReconciliationInvariantError(
                    "Matched results cannot contain differences."
                )
            if confidence_score <= 0:
                raise ReconciliationInvariantError(
                    "Matched results require positive confidence."
                )

        elif status is ReconciliationStatus.PARTIALLY_MATCHED:
            if not left_ids or not right_ids:
                raise ReconciliationInvariantError(
                    "Partially matched results require both sides."
                )
            if match_method is MatchMethod.NONE:
                raise ReconciliationInvariantError(
                    "Partially matched results require a match method."
                )
            if not evidence or not differences:
                raise ReconciliationInvariantError(
                    "Partially matched results require evidence and differences."
                )

        elif status is ReconciliationStatus.UNMATCHED:
            if not left_ids and not right_ids:
                raise ReconciliationInvariantError(
                    "Unmatched results require at least one entity."
                )
            if match_method is not MatchMethod.NONE:
                raise ReconciliationInvariantError(
                    "Unmatched results must use MatchMethod.NONE."
                )
            if not differences:
                raise ReconciliationInvariantError(
                    "Unmatched results require at least one difference."
                )

        elif status is ReconciliationStatus.REVIEW_REQUIRED:
            if not left_ids and not right_ids:
                raise ReconciliationInvariantError(
                    "Review-required results require at least one entity."
                )
            if not evidence and not differences:
                raise ReconciliationInvariantError(
                    "Review-required results require evidence or differences."
                )

        elif status is ReconciliationStatus.EXCLUDED:
            if match_method is not MatchMethod.NONE:
                raise ReconciliationInvariantError(
                    "Excluded results must use MatchMethod.NONE."
                )
            if differences:
                raise ReconciliationInvariantError(
                    "Excluded results cannot contain financial differences."
                )

        elif status is ReconciliationStatus.ERROR:
            if match_method is not MatchMethod.NONE:
                raise ReconciliationInvariantError(
                    "Error results must use MatchMethod.NONE."
                )
            if not differences:
                raise ReconciliationInvariantError(
                    "Error results require a data-quality difference."
                )

    @property
    def is_successful(self) -> bool:
        return self.status in {
            ReconciliationStatus.MATCHED,
            ReconciliationStatus.EXCLUDED,
        }

    @property
    def exception_types(self) -> tuple[ExceptionType, ...]:
        return tuple(
            sorted(
                {difference.reason for difference in self.differences},
                key=lambda item: item.value,
            )
        )

    @property
    def amount_at_risk(self) -> Money | None:
        monetary_differences = [
            difference.money.absolute_variance
            for difference in self.differences
            if difference.money is not None
        ]
        if not monetary_differences:
            return None

        currency = monetary_differences[0].currency
        if any(item.currency is not currency for item in monetary_differences):
            raise ReconciliationInvariantError(
                "A single result cannot aggregate amount at risk across currencies."
            )
        total = Money.zero(currency)
        for item in monetary_differences:
            total = total + item
        return total

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": str(self.result_id),
            "scope": self.scope.value,
            "status": self.status.value,
            "match_method": self.match_method.value,
            "evaluated_at": self.evaluated_at.isoformat(),
            "left_entity_ids": list(self.left_entity_ids),
            "right_entity_ids": list(self.right_entity_ids),
            "evidence": [item.to_dict() for item in self.evidence],
            "differences": [item.to_dict() for item in self.differences],
            "confidence_score": str(self.confidence_score),
            "materiality": self.materiality.value,
            "risk": self.risk.to_dict() if self.risk is not None else None,
            "amount_at_risk": (
                self.amount_at_risk.to_dict()
                if self.amount_at_risk is not None
                else None
            ),
            "exception_types": [
                item.value for item in self.exception_types
            ],
            "correlation_id": (
                self.correlation_id.to_dict()
                if self.correlation_id is not None
                else None
            ),
            "identity_graph": (
                self.identity_graph.to_dict()
                if self.identity_graph is not None
                else None
            ),
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "created_by": self.created_by,
            "diagnostics": dict(self.diagnostics),
        }


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ReconciliationResultBuilder:
    """Mutable assembly helper that produces one immutable validated result.

    The builder is deliberately single-use after ``build`` to prevent accidental
    reuse of evidence or differences across independent decisions.
    """

    def __init__(
        self,
        *,
        scope: ReconciliationScope,
        evaluated_at: datetime,
        left_entity_ids: Iterable[str] = (),
        right_entity_ids: Iterable[str] = (),
        result_id: UUID | None = None,
        correlation_id: CorrelationId | None = None,
        identity_graph: IdentityGraph | None = None,
        rule_id: str | None = None,
        rule_version: str | None = None,
        created_by: str = "reconciliation_engine",
        diagnostics: DiagnosticInput | None = None,
    ) -> None:
        self._scope = _parse_enum(
            ReconciliationScope,
            scope,
            field_name="scope",
        )
        self._evaluated_at = _require_datetime(
            evaluated_at,
            field_name="evaluated_at",
        )
        self._left_entity_ids = list(left_entity_ids)
        self._right_entity_ids = list(right_entity_ids)
        self._result_id = result_id or uuid4()
        self._correlation_id = correlation_id
        self._identity_graph = identity_graph
        self._rule_id = rule_id
        self._rule_version = rule_version
        self._created_by = created_by
        self._diagnostics = dict(diagnostics or {})
        self._evidence: list[MatchEvidence] = []
        self._differences: list[ReconciliationDifference] = []
        self._built = False

    def _ensure_open(self) -> None:
        if self._built:
            raise ReconciliationInvariantError(
                "A ReconciliationResultBuilder cannot be reused after build."
            )

    def add_left_entity(self, entity_id: str) -> ReconciliationResultBuilder:
        self._ensure_open()
        self._left_entity_ids.append(entity_id)
        return self

    def add_right_entity(self, entity_id: str) -> ReconciliationResultBuilder:
        self._ensure_open()
        self._right_entity_ids.append(entity_id)
        return self

    def add_evidence(
        self,
        evidence: MatchEvidence,
    ) -> ReconciliationResultBuilder:
        self._ensure_open()
        if not isinstance(evidence, MatchEvidence):
            raise TypeError("evidence must be MatchEvidence.")
        self._evidence.append(evidence)
        return self

    def add_difference(
        self,
        difference: ReconciliationDifference,
    ) -> ReconciliationResultBuilder:
        self._ensure_open()
        if not isinstance(difference, ReconciliationDifference):
            raise TypeError(
                "difference must be ReconciliationDifference."
            )
        self._differences.append(difference)
        return self

    def add_diagnostic(
        self,
        key: str,
        value: DiagnosticInputValue,
    ) -> ReconciliationResultBuilder:
        self._ensure_open()
        normalized_key = _require_text(
            key,
            field_name="diagnostic_key",
            max_length=256,
        )
        if normalized_key in self._diagnostics:
            raise ReconciliationInvariantError(
                "A diagnostic key cannot be overwritten.",
                context={"diagnostic_key": normalized_key},
            )
        self._diagnostics[normalized_key] = value
        return self

    def build(
        self,
        *,
        status: ReconciliationStatus,
        match_method: MatchMethod,
        confidence_score: Decimal,
    ) -> ReconciliationResult:
        self._ensure_open()

        materiality = ReconciliationResult._highest_materiality(
            self._differences
        )
        result = ReconciliationResult(
            result_id=self._result_id,
            scope=self._scope,
            status=status,
            match_method=match_method,
            evaluated_at=self._evaluated_at,
            left_entity_ids=tuple(self._left_entity_ids),
            right_entity_ids=tuple(self._right_entity_ids),
            evidence=tuple(self._evidence),
            differences=tuple(self._differences),
            confidence_score=confidence_score,
            materiality=materiality,
            correlation_id=self._correlation_id,
            identity_graph=self._identity_graph,
            rule_id=self._rule_id,
            rule_version=self._rule_version,
            created_by=self._created_by,
            diagnostics=self._diagnostics,
        )
        self._built = True
        return result

    def build_matched(
        self,
        *,
        match_method: MatchMethod,
        confidence_score: Decimal = Decimal("1"),
    ) -> ReconciliationResult:
        return self.build(
            status=ReconciliationStatus.MATCHED,
            match_method=match_method,
            confidence_score=confidence_score,
        )

    def build_partial(
        self,
        *,
        match_method: MatchMethod,
        confidence_score: Decimal,
    ) -> ReconciliationResult:
        return self.build(
            status=ReconciliationStatus.PARTIALLY_MATCHED,
            match_method=match_method,
            confidence_score=confidence_score,
        )

    def build_unmatched(self) -> ReconciliationResult:
        return self.build(
            status=ReconciliationStatus.UNMATCHED,
            match_method=MatchMethod.NONE,
            confidence_score=Decimal("0"),
        )

    def build_review_required(
        self,
        *,
        match_method: MatchMethod = MatchMethod.NONE,
        confidence_score: Decimal = Decimal("0"),
    ) -> ReconciliationResult:
        return self.build(
            status=ReconciliationStatus.REVIEW_REQUIRED,
            match_method=match_method,
            confidence_score=confidence_score,
        )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReconciliationSummary:
    """Immutable aggregate of reconciliation results for one currency."""

    generated_at: datetime
    total_results: int
    matched_results: int
    partially_matched_results: int
    unmatched_results: int
    review_required_results: int
    excluded_results: int
    error_results: int
    amount_at_risk: Money
    matched_amount: Money
    evaluated_amount: Money
    coverage_ratio: Decimal | None
    results_by_risk: Mapping[RiskLevel, int]
    results_by_exception: Mapping[ExceptionType, int]

    def __post_init__(self) -> None:
        generated_at = _require_datetime(
            self.generated_at,
            field_name="generated_at",
        )
        counts = (
            self.total_results,
            self.matched_results,
            self.partially_matched_results,
            self.unmatched_results,
            self.review_required_results,
            self.excluded_results,
            self.error_results,
        )
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in counts
        ):
            raise DomainValidationError(
                "Summary counts must be non-negative integers."
            )
        if sum(counts[1:]) != self.total_results:
            raise ReconciliationInvariantError(
                "Summary status counts must equal total_results."
            )

        amount_at_risk = _require_money(
            self.amount_at_risk,
            field_name="amount_at_risk",
        )
        matched_amount = _require_money(
            self.matched_amount,
            field_name="matched_amount",
        )
        evaluated_amount = _require_money(
            self.evaluated_amount,
            field_name="evaluated_amount",
        )
        if len(
            {
                amount_at_risk.currency,
                matched_amount.currency,
                evaluated_amount.currency,
            }
        ) != 1:
            raise ReconciliationInvariantError(
                "Summary monetary values must use one currency."
            )
        if any(
            amount.is_negative
            for amount in (
                amount_at_risk,
                matched_amount,
                evaluated_amount,
            )
        ):
            raise ReconciliationInvariantError(
                "Summary monetary values cannot be negative."
            )
        if matched_amount > evaluated_amount:
            raise ReconciliationInvariantError(
                "matched_amount cannot exceed evaluated_amount."
            )

        expected_coverage = (
            None
            if evaluated_amount.is_zero
            else matched_amount.ratio(evaluated_amount)
        )
        if self.coverage_ratio != expected_coverage:
            raise ReconciliationInvariantError(
                "coverage_ratio does not match monetary totals."
            )

        risk_counts: dict[RiskLevel, int] = {}
        for key, value in self.results_by_risk.items():
            canonical_key = _parse_enum(
                RiskLevel,
                key,
                field_name="risk_level",
            )
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DomainValidationError(
                    "Risk summary counts must be non-negative integers."
                )
            risk_counts[canonical_key] = value

        exception_counts: dict[ExceptionType, int] = {}
        for key, value in self.results_by_exception.items():
            canonical_key = _parse_enum(
                ExceptionType,
                key,
                field_name="exception_type",
            )
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DomainValidationError(
                    "Exception summary counts must be non-negative integers."
                )
            exception_counts[canonical_key] = value

        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "amount_at_risk", amount_at_risk)
        object.__setattr__(self, "matched_amount", matched_amount)
        object.__setattr__(self, "evaluated_amount", evaluated_amount)
        object.__setattr__(
            self,
            "results_by_risk",
            MappingProxyType(dict(sorted(
                risk_counts.items(),
                key=lambda item: item[0].value,
            ))),
        )
        object.__setattr__(
            self,
            "results_by_exception",
            MappingProxyType(dict(sorted(
                exception_counts.items(),
                key=lambda item: item[0].value,
            ))),
        )

    @classmethod
    def from_results(
        cls,
        results: Iterable[ReconciliationResult],
        *,
        generated_at: datetime,
        evaluated_amounts: Mapping[UUID, Money] | None = None,
    ) -> ReconciliationSummary:
        materialized = tuple(results)
        if any(
            not isinstance(result, ReconciliationResult)
            for result in materialized
        ):
            raise TypeError(
                "results must contain ReconciliationResult instances."
            )

        amount_map = dict(evaluated_amounts or {})
        currency = None
        for amount in amount_map.values():
            _require_money(amount, field_name="evaluated_amount")
            currency = amount.currency if currency is None else currency
            if amount.currency is not currency:
                raise ReconciliationInvariantError(
                    "Summary cannot aggregate multiple currencies."
                )
        for result in materialized:
            risk_amount = result.amount_at_risk
            if risk_amount is not None:
                currency = (
                    risk_amount.currency if currency is None else currency
                )
                if risk_amount.currency is not currency:
                    raise ReconciliationInvariantError(
                        "Summary cannot aggregate multiple currencies."
                    )

        if currency is None:
            currency = Money.DEFAULT_CURRENCY

        amount_at_risk = Money.zero(currency)
        matched_amount = Money.zero(currency)
        evaluated_amount = Money.zero(currency)

        status_counts = {
            status: 0 for status in ReconciliationStatus
        }
        risk_counts = {level: 0 for level in RiskLevel}
        exception_counts: dict[ExceptionType, int] = {}

        for result in materialized:
            status_counts[result.status] += 1
            risk_counts[result.risk.level] += 1
            for exception_type in result.exception_types:
                exception_counts[exception_type] = (
                    exception_counts.get(exception_type, 0) + 1
                )

            risk_amount = result.amount_at_risk
            if risk_amount is not None:
                amount_at_risk = amount_at_risk + risk_amount

            evaluation_amount = amount_map.get(result.result_id)
            if evaluation_amount is not None:
                evaluated_amount = evaluated_amount + evaluation_amount
                if result.status is ReconciliationStatus.MATCHED:
                    matched_amount = matched_amount + evaluation_amount

        coverage = (
            None
            if evaluated_amount.is_zero
            else matched_amount.ratio(evaluated_amount)
        )

        return cls(
            generated_at=generated_at,
            total_results=len(materialized),
            matched_results=status_counts[ReconciliationStatus.MATCHED],
            partially_matched_results=status_counts[
                ReconciliationStatus.PARTIALLY_MATCHED
            ],
            unmatched_results=status_counts[ReconciliationStatus.UNMATCHED],
            review_required_results=status_counts[
                ReconciliationStatus.REVIEW_REQUIRED
            ],
            excluded_results=status_counts[ReconciliationStatus.EXCLUDED],
            error_results=status_counts[ReconciliationStatus.ERROR],
            amount_at_risk=amount_at_risk,
            matched_amount=matched_amount,
            evaluated_amount=evaluated_amount,
            coverage_ratio=coverage,
            results_by_risk=risk_counts,
            results_by_exception=exception_counts,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_results": self.total_results,
            "matched_results": self.matched_results,
            "partially_matched_results": self.partially_matched_results,
            "unmatched_results": self.unmatched_results,
            "review_required_results": self.review_required_results,
            "excluded_results": self.excluded_results,
            "error_results": self.error_results,
            "amount_at_risk": self.amount_at_risk.to_dict(),
            "matched_amount": self.matched_amount.to_dict(),
            "evaluated_amount": self.evaluated_amount.to_dict(),
            "coverage_ratio": (
                str(self.coverage_ratio)
                if self.coverage_ratio is not None
                else None
            ),
            "results_by_risk": {
                key.value: value
                for key, value in self.results_by_risk.items()
            },
            "results_by_exception": {
                key.value: value
                for key, value in self.results_by_exception.items()
            },
        }


__all__ = [
    "DiagnosticInput",
    "DiagnosticInputValue",
    "DiagnosticValue",
    "DifferenceType",
    "EvidenceType",
    "FrozenDiagnostics",
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