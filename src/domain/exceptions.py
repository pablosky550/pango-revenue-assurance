"""Structured domain exceptions for Pango Revenue Assurance.

This module defines predictable business, validation, reconciliation, and
financial-integrity failures raised by the canonical domain layer.

Design guarantees:
- stable class-level machine-readable error codes;
- immutable, JSON-safe diagnostic context;
- deterministic, log-friendly string rendering;
- safe exception chaining through standard ``raise ... from ...`` semantics;
- pickle compatibility, including subclasses with specialised constructors;
- no dependency on pandas, databases, filesystems, HTTP frameworks, or
  provider SDKs.

Security boundary:
Diagnostic context must contain only non-sensitive identifiers and summary
values. This module validates shape and serialisability, but no generic
mechanism can reliably detect every secret or item of personal data.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import ClassVar, TypeAlias, TypedDict
from uuid import UUID


ContextInputValue: TypeAlias = str | int | float | bool | None | Decimal | date | datetime | UUID | Enum
ContextValue: TypeAlias = str | int | float | bool | None
ErrorContext: TypeAlias = Mapping[str, ContextInputValue]


class ErrorPayload(TypedDict):
    """JSON-compatible representation of a Revenue Assurance exception."""

    error_type: str
    code: str
    message: str
    context: dict[str, ContextValue]


_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")


def _restore_exception(
    exception_type: type["RevenueAssuranceError"],
    message: str,
    context: dict[str, ContextValue],
) -> "RevenueAssuranceError":
    """Restore a pickled exception without invoking specialised constructors."""

    instance = exception_type.__new__(exception_type)
    RevenueAssuranceError._initialise(instance, message=message, context=context)
    return instance


class RevenueAssuranceError(Exception):
    """Base class for expected Revenue Assurance failures.

    Attributes:
        code: Stable machine-readable code defined by the exception class.
        message: Human-readable explanation of the failure.
        context: Immutable, JSON-compatible, non-sensitive diagnostic metadata.

    Context should contain opaque identifiers, source names, field names, and
    safe summary values only. Do not include raw source rows, card data, bank
    account numbers, credentials, personal data, or provider payloads.
    """

    default_code: ClassVar[str] = "REVENUE_ASSURANCE_ERROR"
    default_message: ClassVar[str] = "A Revenue Assurance error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        context: ErrorContext | None = None,
    ) -> None:
        self._initialise(
            message=self.default_message if message is None else message,
            context=context,
        )

    def _initialise(
        self,
        *,
        message: str,
        context: ErrorContext | Mapping[str, ContextValue] | None,
    ) -> None:
        """Initialise validated state for normal construction and unpickling."""

        resolved_message = self._validate_message(message)
        resolved_code = self._validate_code(type(self).default_code)
        resolved_context = self._normalise_context(context)

        self.code = resolved_code
        self.message = resolved_message
        self.context = MappingProxyType(resolved_context)

        # Keep Exception.args conventional and concise. Context is available
        # through ``context`` and ``to_dict``.
        Exception.__init__(self, resolved_message)

    @staticmethod
    def _validate_message(message: str) -> str:
        if not isinstance(message, str):
            raise TypeError(
                "Exception message must be a string; "
                f"received {type(message).__name__}."
            )

        normalised = message.strip()
        if not normalised:
            raise ValueError("Exception message cannot be empty.")
        return normalised

    @staticmethod
    def _validate_code(code: str) -> str:
        if not isinstance(code, str):
            raise TypeError(
                "Exception code must be a string; "
                f"received {type(code).__name__}."
            )

        normalised = code.strip().upper()
        if not _CODE_PATTERN.fullmatch(normalised):
            raise ValueError(
                "Exception code must use upper snake case and begin with a "
                f"letter; received {code!r}."
            )
        return normalised

    @classmethod
    def _normalise_context(
        cls,
        context: ErrorContext | Mapping[str, ContextValue] | None,
    ) -> dict[str, ContextValue]:
        if context is None:
            return {}
        if not isinstance(context, Mapping):
            raise TypeError(
                "Exception context must be a mapping; "
                f"received {type(context).__name__}."
            )

        normalised: dict[str, ContextValue] = {}
        for raw_key, raw_value in context.items():
            if not isinstance(raw_key, str):
                raise TypeError(
                    "Exception context keys must be strings; "
                    f"received {type(raw_key).__name__}."
                )

            key = raw_key.strip()
            if not key:
                raise ValueError("Exception context keys cannot be empty.")
            if key in normalised:
                raise ValueError(
                    "Exception context contains duplicate keys after "
                    f"normalisation: {key!r}."
                )

            normalised[key] = cls._normalise_context_value(key, raw_value)

        return normalised

    @staticmethod
    def _normalise_context_value(
        key: str,
        value: ContextInputValue,
    ) -> ContextValue:
        if value is None or isinstance(value, (str, bool, int)):
            return value

        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(
                    "Exception context floats must be finite for strict JSON "
                    f"serialisation; key {key!r} received {value!r}."
                )
            return value

        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError(
                    "Exception context Decimal values must be finite; "
                    f"key {key!r} received {value!r}."
                )
            # String conversion preserves financial precision.
            return str(value)

        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(
                    "Datetime context values must be timezone-aware; "
                    f"key {key!r} received a naive datetime."
                )
            return value.isoformat()

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, Enum):
            enum_value = value.value
            if isinstance(enum_value, (str, bool, int)):
                return enum_value
            if isinstance(enum_value, float) and math.isfinite(enum_value):
                return enum_value
            return str(enum_value)

        raise TypeError(
            "Exception context values must be supported scalar values; "
            f"key {key!r} received {type(value).__name__}."
        )

    @staticmethod
    def merge_context(
        base: ErrorContext | None,
        extra: ErrorContext | None,
    ) -> dict[str, ContextInputValue]:
        """Merge contexts while rejecting accidental key overwrites."""

        merged: dict[str, ContextInputValue] = dict(base or {})
        for key, value in (extra or {}).items():
            if key in merged:
                raise ValueError(
                    f"Exception context key {key!r} was supplied more than once."
                )
            merged[key] = value
        return merged

    def __str__(self) -> str:
        """Return a deterministic, concise representation for logs."""

        if not self.context:
            return f"[{self.code}] {self.message}"

        rendered_context = ", ".join(
            f"{key}={value!r}" for key, value in sorted(self.context.items())
        )
        return f"[{self.code}] {self.message} ({rendered_context})"

    def to_dict(self) -> ErrorPayload:
        """Return a detached JSON-compatible payload for logs and APIs."""

        return {
            "error_type": type(self).__name__,
            "code": self.code,
            "message": self.message,
            "context": dict(self.context),
        }

    def __reduce__(
        self,
    ) -> tuple[
        object,
        tuple[type["RevenueAssuranceError"], str, dict[str, ContextValue]],
    ]:
        """Provide reliable pickling for all specialised subclasses."""

        return (
            _restore_exception,
            (type(self), self.message, dict(self.context)),
        )


class DomainError(RevenueAssuranceError):
    """Base class for canonical financial-domain failures."""

    default_code = "DOMAIN_ERROR"
    default_message = "A financial-domain error occurred."


class DomainValidationError(DomainError):
    """A domain value or entity failed validation."""

    default_code = "DOMAIN_VALIDATION_ERROR"
    default_message = "Domain validation failed."


class MissingRequiredValueError(DomainValidationError):
    """A required domain field was absent or blank."""

    default_code = "MISSING_REQUIRED_VALUE"
    default_message = "A required domain value is missing."

    def __init__(
        self,
        field_name: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        message: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        details: dict[str, ContextInputValue] = {"field_name": field_name}
        if entity_type is not None:
            details["entity_type"] = entity_type
        if entity_id is not None:
            details["entity_id"] = entity_id

        super().__init__(
            message,
            context=self.merge_context(details, context),
        )


class InvalidMoneyError(DomainValidationError):
    """A monetary amount, precision, sign, or representation is invalid."""

    default_code = "INVALID_MONEY"
    default_message = "The monetary value is invalid."


class CurrencyMismatchError(DomainValidationError):
    """An operation attempted to combine incompatible currencies."""

    default_code = "CURRENCY_MISMATCH"
    default_message = "The monetary currencies are incompatible."

    def __init__(
        self,
        left_currency: str | Enum,
        right_currency: str | Enum,
        *,
        operation: str | None = None,
        message: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        details: dict[str, ContextInputValue] = {
            "left_currency": left_currency,
            "right_currency": right_currency,
        }
        if operation is not None:
            details["operation"] = operation

        super().__init__(
            message,
            context=self.merge_context(details, context),
        )


class InvalidIdentifierError(DomainValidationError):
    """An identifier is empty, malformed, or inconsistent with its type."""

    default_code = "INVALID_IDENTIFIER"
    default_message = "The domain identifier is invalid."


class InvalidTimestampError(DomainValidationError):
    """A timestamp is missing, naive, malformed, or temporally inconsistent."""

    default_code = "INVALID_TIMESTAMP"
    default_message = "The domain timestamp is invalid."


class InvalidStateTransitionError(DomainValidationError):
    """An entity attempted an unsupported lifecycle transition."""

    default_code = "INVALID_STATE_TRANSITION"
    default_message = "The requested state transition is not allowed."

    def __init__(
        self,
        from_status: str | Enum,
        to_status: str | Enum,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        message: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        details: dict[str, ContextInputValue] = {
            "from_status": from_status,
            "to_status": to_status,
        }
        if entity_type is not None:
            details["entity_type"] = entity_type
        if entity_id is not None:
            details["entity_id"] = entity_id

        super().__init__(
            message,
            context=self.merge_context(details, context),
        )


class InvariantViolationError(DomainValidationError):
    """A financial relationship or entity invariant does not hold."""

    default_code = "INVARIANT_VIOLATION"
    default_message = "A financial-domain invariant was violated."


class ReconciliationError(DomainError):
    """Base class for failures produced by reconciliation logic."""

    default_code = "RECONCILIATION_ERROR"
    default_message = "Reconciliation could not be completed."


class AmbiguousMatchError(ReconciliationError):
    """Multiple candidates satisfy the current matching rule."""

    default_code = "AMBIGUOUS_MATCH"
    default_message = "Reconciliation produced multiple plausible matches."

    def __init__(
        self,
        candidate_count: int,
        *,
        entity_id: str | None = None,
        match_method: str | Enum | None = None,
        message: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        if isinstance(candidate_count, bool) or not isinstance(candidate_count, int):
            raise TypeError("candidate_count must be an integer.")
        if candidate_count < 2:
            raise ValueError(
                "AmbiguousMatchError requires at least two candidates."
            )

        details: dict[str, ContextInputValue] = {
            "candidate_count": candidate_count,
        }
        if entity_id is not None:
            details["entity_id"] = entity_id
        if match_method is not None:
            details["match_method"] = match_method

        super().__init__(
            message,
            context=self.merge_context(details, context),
        )


class UnsupportedMatchMethodError(ReconciliationError):
    """A matching method is unavailable for the supplied entity types."""

    default_code = "UNSUPPORTED_MATCH_METHOD"
    default_message = "The reconciliation match method is not supported."


class ReconciliationInvariantError(ReconciliationError):
    """A reconciliation result is internally inconsistent."""

    default_code = "RECONCILIATION_INVARIANT_VIOLATION"
    default_message = "The reconciliation result violates a required invariant."


class DataIntegrityError(DomainError):
    """Canonical data is structurally valid but financially inconsistent."""

    default_code = "DATA_INTEGRITY_ERROR"
    default_message = "A financial data-integrity failure was detected."


class DuplicateRecordError(DataIntegrityError):
    """A record violates an expected uniqueness constraint."""

    default_code = "DUPLICATE_RECORD"
    default_message = "A duplicate financial record was detected."


class ReferentialIntegrityError(DataIntegrityError):
    """A required cross-entity or cross-system reference cannot be resolved."""

    default_code = "REFERENTIAL_INTEGRITY_ERROR"
    default_message = "A required financial reference cannot be resolved."


class AuditTrailIntegrityError(DataIntegrityError):
    """Audit evidence is missing, inconsistent, or fails integrity validation."""

    default_code = "AUDIT_TRAIL_INTEGRITY_ERROR"
    default_message = "Audit-trail integrity validation failed."


__all__ = [
    "AmbiguousMatchError",
    "AuditTrailIntegrityError",
    "ContextInputValue",
    "ContextValue",
    "CurrencyMismatchError",
    "DataIntegrityError",
    "DomainError",
    "DomainValidationError",
    "DuplicateRecordError",
    "ErrorContext",
    "ErrorPayload",
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
]