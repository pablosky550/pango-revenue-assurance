"""Immutable monetary value object for Pango Revenue Assurance.

The canonical domain never represents money with binary floating-point values
and never discards monetary precision silently. ``Money`` therefore:

- stores amounts with :class:`decimal.Decimal`;
- requires a supported canonical currency;
- enforces the currency's minor-unit scale;
- rejects implicit rounding;
- rejects cross-currency arithmetic;
- remains independent of providers, persistence, pandas, and infrastructure.

Provider-specific sign conventions belong in source normalizers. ``Money``
stores the signed economic amount after canonical normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    localcontext,
)
from types import MappingProxyType
from typing import ClassVar, Final, TypeAlias

from .enums import CurrencyCode
from .exceptions import CurrencyMismatchError, InvalidMoneyError


DecimalInput: TypeAlias = Decimal | int | str
Scalar: TypeAlias = Decimal | int
RoundingMode: TypeAlias = str

_SUPPORTED_ROUNDING_MODES: Final[frozenset[str]] = frozenset(
    {
        ROUND_05UP,
        ROUND_CEILING,
        ROUND_DOWN,
        ROUND_FLOOR,
        ROUND_HALF_DOWN,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_UP,
    }
)


def _decimal_precision(*values: Decimal, extra: int = 24) -> int:
    """Return a safe local precision for deterministic decimal operations."""

    significant_digits = sum(max(1, len(value.as_tuple().digits)) for value in values)
    exponent_span = sum(max(0, abs(value.as_tuple().exponent)) for value in values)
    return max(50, significant_digits + exponent_span + extra)


def _validate_rounding_mode(rounding: str) -> str:
    if not isinstance(rounding, str):
        raise InvalidMoneyError(
            "The rounding mode must be a decimal rounding constant.",
            context={"value_type": type(rounding).__name__},
        )
    if rounding not in _SUPPORTED_ROUNDING_MODES:
        raise InvalidMoneyError(
            "The rounding mode is unsupported.",
            context={"rounding": rounding},
        )
    return rounding


@dataclass(frozen=True, slots=True)
class CurrencySpecification:
    """Immutable arithmetic specification for one supported currency."""

    code: CurrencyCode
    decimal_places: int
    rounding: RoundingMode = ROUND_HALF_EVEN

    def __post_init__(self) -> None:
        try:
            canonical_code = CurrencyCode.parse(self.code)
        except (TypeError, ValueError) as exc:
            raise InvalidMoneyError(
                "The currency specification uses an unsupported currency.",
                context={"currency": str(self.code)},
            ) from exc

        if isinstance(self.decimal_places, bool) or not isinstance(
            self.decimal_places, int
        ):
            raise TypeError("decimal_places must be an integer.")
        if self.decimal_places < 0:
            raise ValueError("decimal_places cannot be negative.")

        canonical_rounding = _validate_rounding_mode(self.rounding)

        object.__setattr__(self, "code", canonical_code)
        object.__setattr__(self, "rounding", canonical_rounding)

    @property
    def quantum(self) -> Decimal:
        """Smallest representable major-currency unit."""

        return Decimal(1).scaleb(-self.decimal_places)

    @property
    def minor_unit_factor(self) -> int:
        """Number of minor units in one major currency unit."""

        return 10**self.decimal_places


_CURRENCY_SPECIFICATIONS = MappingProxyType(
    {
        CurrencyCode.USD: CurrencySpecification(
            code=CurrencyCode.USD,
            decimal_places=2,
            rounding=ROUND_HALF_EVEN,
        ),
    }
)


def _canonical_currency(currency: CurrencyCode | str) -> CurrencyCode:
    try:
        return CurrencyCode.parse(currency)
    except (TypeError, ValueError) as exc:
        raise InvalidMoneyError(
            "The monetary currency is unsupported.",
            context={"currency": str(currency)},
        ) from exc


def currency_specification(
    currency: CurrencyCode | str,
) -> CurrencySpecification:
    """Return the immutable specification for ``currency``."""

    canonical_currency = _canonical_currency(currency)
    try:
        return _CURRENCY_SPECIFICATIONS[canonical_currency]
    except KeyError as exc:
        raise InvalidMoneyError(
            "No arithmetic specification exists for the monetary currency.",
            context={"currency": canonical_currency},
        ) from exc


def _decimal_from_input(value: DecimalInput, *, field_name: str) -> Decimal:
    """Convert decimal-compatible input while explicitly rejecting floats."""

    if isinstance(value, bool):
        raise InvalidMoneyError(
            "Boolean values cannot represent money.",
            context={"field_name": field_name, "value_type": "bool"},
        )
    if isinstance(value, float):
        raise InvalidMoneyError(
            "Binary floating-point values cannot represent money.",
            context={"field_name": field_name, "value_type": "float"},
        )
    if not isinstance(value, (Decimal, int, str)):
        raise InvalidMoneyError(
            "The monetary amount has an unsupported type.",
            context={
                "field_name": field_name,
                "value_type": type(value).__name__,
            },
        )

    candidate: Decimal | int | str = value
    if isinstance(candidate, str):
        candidate = candidate.strip()
        if not candidate:
            raise InvalidMoneyError(
                "The monetary amount cannot be empty.",
                context={"field_name": field_name},
            )

    try:
        decimal_value = (
            candidate if isinstance(candidate, Decimal) else Decimal(candidate)
        )
    except (DecimalException, ValueError) as exc:
        raise InvalidMoneyError(
            "The monetary amount is not a valid decimal value.",
            context={"field_name": field_name},
        ) from exc

    if not decimal_value.is_finite():
        raise InvalidMoneyError(
            "The monetary amount must be finite.",
            context={"field_name": field_name, "amount": str(decimal_value)},
        )
    return decimal_value


def _scalar_from_input(value: Scalar, *, operation: str) -> Decimal:
    """Validate an arithmetic scalar without allowing float contamination."""

    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidMoneyError(
            "Money arithmetic requires an integer or Decimal scalar.",
            context={"operation": operation, "value_type": type(value).__name__},
        )
    if not isinstance(value, (Decimal, int)):
        raise InvalidMoneyError(
            "Money arithmetic requires an integer or Decimal scalar.",
            context={"operation": operation, "value_type": type(value).__name__},
        )

    scalar = value if isinstance(value, Decimal) else Decimal(value)
    if not scalar.is_finite():
        raise InvalidMoneyError(
            "Money arithmetic requires a finite scalar.",
            context={"operation": operation, "scalar": str(scalar)},
        )
    return scalar


def _quantize(
    amount: Decimal,
    specification: CurrencySpecification,
    *,
    rounding: str | None = None,
) -> Decimal:
    """Quantize independently of the process-wide Decimal context."""

    mode = specification.rounding if rounding is None else _validate_rounding_mode(rounding)
    try:
        with localcontext() as context:
            context.prec = _decimal_precision(amount, specification.quantum)
            return amount.quantize(specification.quantum, rounding=mode)
    except (DecimalException, ValueError, TypeError) as exc:
        raise InvalidMoneyError(
            "The monetary amount cannot be represented at currency precision.",
            context={
                "amount": str(amount),
                "currency": specification.code,
                "decimal_places": specification.decimal_places,
            },
        ) from exc


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable, currency-aware monetary amount.

    Construction is strict. Values with fewer fractional digits are padded to
    the currency scale. Non-zero excess precision is rejected. Use
    :meth:`rounded` only when an explicit business rule authorises rounding.
    """

    amount: Decimal
    currency: CurrencyCode = CurrencyCode.USD

    DEFAULT_CURRENCY: ClassVar[CurrencyCode] = CurrencyCode.USD

    def __post_init__(self) -> None:
        decimal_amount = _decimal_from_input(self.amount, field_name="amount")
        canonical_currency = _canonical_currency(self.currency)
        specification = currency_specification(canonical_currency)
        canonical_amount = _quantize(decimal_amount, specification)

        if canonical_amount != decimal_amount:
            raise InvalidMoneyError(
                "The monetary amount exceeds the currency precision.",
                context={
                    "amount": str(decimal_amount),
                    "currency": canonical_currency,
                    "decimal_places": specification.decimal_places,
                },
            )

        object.__setattr__(self, "amount", canonical_amount)
        object.__setattr__(self, "currency", canonical_currency)

    @classmethod
    def of(
        cls,
        amount: DecimalInput,
        currency: CurrencyCode | str = DEFAULT_CURRENCY,
    ) -> Money:
        """Create strict canonical money from decimal-compatible input."""

        return cls(
            amount=_decimal_from_input(amount, field_name="amount"),
            currency=_canonical_currency(currency),
        )

    @classmethod
    def rounded(
        cls,
        amount: DecimalInput,
        currency: CurrencyCode | str = DEFAULT_CURRENCY,
        *,
        rounding: RoundingMode | None = None,
    ) -> Money:
        """Create money using an explicit, auditable rounding decision."""

        canonical_currency = _canonical_currency(currency)
        specification = currency_specification(canonical_currency)
        decimal_amount = _decimal_from_input(amount, field_name="amount")
        rounded_amount = _quantize(
            decimal_amount,
            specification,
            rounding=rounding,
        )
        return cls(rounded_amount, canonical_currency)

    @classmethod
    def zero(
        cls,
        currency: CurrencyCode | str = DEFAULT_CURRENCY,
    ) -> Money:
        """Return canonical zero for a currency."""

        return cls.of(0, currency)

    @classmethod
    def from_minor_units(
        cls,
        minor_units: int,
        currency: CurrencyCode | str = DEFAULT_CURRENCY,
    ) -> Money:
        """Create money from an exact integer number of minor units."""

        if isinstance(minor_units, bool) or not isinstance(minor_units, int):
            raise InvalidMoneyError(
                "Minor units must be provided as an integer.",
                context={"value_type": type(minor_units).__name__},
            )

        canonical_currency = _canonical_currency(currency)
        specification = currency_specification(canonical_currency)
        with localcontext() as context:
            context.prec = _decimal_precision(Decimal(minor_units))
            amount = Decimal(minor_units) / Decimal(
                specification.minor_unit_factor
            )
        return cls(amount, canonical_currency)

    @property
    def specification(self) -> CurrencySpecification:
        return currency_specification(self.currency)

    @property
    def minor_units(self) -> int:
        """Exact signed integer number of minor units."""

        scaled = self.amount * Decimal(self.specification.minor_unit_factor)
        integral = scaled.to_integral_exact()
        return int(integral)

    @property
    def is_zero(self) -> bool:
        return self.amount.is_zero()

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    def _require_same_currency(self, other: Money, *, operation: str) -> None:
        if not isinstance(other, Money):
            raise TypeError(
                f"Money {operation} requires another Money instance; "
                f"received {type(other).__name__}."
            )
        if self.currency is not other.currency:
            raise CurrencyMismatchError(
                self.currency,
                other.currency,
                operation=operation,
            )

    def _exact_result(self, amount: Decimal, *, operation: str) -> Money:
        try:
            return Money(amount, self.currency)
        except InvalidMoneyError as exc:
            raise InvalidMoneyError(
                "Money arithmetic produced excess currency precision; "
                "apply an explicit rounding rule.",
                context={
                    "operation": operation,
                    "result": str(amount),
                    "currency": self.currency,
                },
            ) from exc

    def add(self, other: Money) -> Money:
        self._require_same_currency(other, operation="addition")
        return self._exact_result(self.amount + other.amount, operation="addition")

    def subtract(self, other: Money) -> Money:
        self._require_same_currency(other, operation="subtraction")
        return self._exact_result(
            self.amount - other.amount,
            operation="subtraction",
        )

    def multiply(
        self,
        scalar: Scalar,
        *,
        rounding: RoundingMode | None = None,
    ) -> Money:
        """Multiply, rejecting implicit rounding."""

        decimal_scalar = _scalar_from_input(scalar, operation="multiplication")
        with localcontext() as context:
            context.prec = _decimal_precision(self.amount, decimal_scalar)
            result = self.amount * decimal_scalar

        if rounding is None:
            return self._exact_result(result, operation="multiplication")
        return Money.rounded(result, self.currency, rounding=rounding)

    def divide(
        self,
        scalar: Scalar,
        *,
        rounding: RoundingMode | None = None,
    ) -> Money:
        """Divide, rejecting implicit rounding."""

        decimal_scalar = _scalar_from_input(scalar, operation="division")
        if decimal_scalar.is_zero():
            raise InvalidMoneyError(
                "Money cannot be divided by zero.",
                context={"currency": self.currency},
            )

        with localcontext() as context:
            context.prec = _decimal_precision(self.amount, decimal_scalar, extra=40)
            result = self.amount / decimal_scalar

        if rounding is None:
            return self._exact_result(result, operation="division")
        return Money.rounded(result, self.currency, rounding=rounding)

    def ratio(
        self,
        other: Money,
        *,
        precision: int = 28,
    ) -> Decimal:
        """Return a Decimal ratio using explicit calculation precision.

        Ratios can be non-terminating decimals. The returned value is therefore
        calculated to ``precision`` significant digits rather than described as
        mathematically exact.
        """

        self._require_same_currency(other, operation="ratio")
        if other.is_zero:
            raise InvalidMoneyError(
                "A monetary ratio cannot use a zero denominator.",
                context={"currency": self.currency},
            )
        if isinstance(precision, bool) or not isinstance(precision, int):
            raise InvalidMoneyError(
                "Ratio precision must be an integer.",
                context={"value_type": type(precision).__name__},
            )
        if precision < 1:
            raise InvalidMoneyError(
                "Ratio precision must be positive.",
                context={"precision": precision},
            )

        with localcontext() as context:
            context.prec = max(
                precision,
                _decimal_precision(self.amount, other.amount, extra=8),
            )
            value = self.amount / other.amount
            context.prec = precision
            return +value

    def absolute(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def negate(self) -> Money:
        return Money(-self.amount, self.currency)

    def to_dict(self) -> dict[str, str]:
        """Precision-preserving JSON-compatible representation."""

        return {
            "amount": format(self.amount, "f"),
            "currency": self.currency.value,
        }

    def __str__(self) -> str:
        return f"{self.currency.value} {format(self.amount, 'f')}"

    def __repr__(self) -> str:
        return (
            f"Money(amount=Decimal({str(self.amount)!r}), "
            f"currency=CurrencyCode.{self.currency.name})"
        )

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return self.add(other)

    def __sub__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return self.subtract(other)

    def __mul__(self, scalar: object) -> Money:
        if isinstance(scalar, bool) or not isinstance(scalar, (Decimal, int)):
            return NotImplemented
        return self.multiply(scalar)

    def __rmul__(self, scalar: object) -> Money:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: object) -> Money:
        if isinstance(scalar, bool) or not isinstance(scalar, (Decimal, int)):
            return NotImplemented
        return self.divide(scalar)

    def __neg__(self) -> Money:
        return self.negate()

    def __abs__(self) -> Money:
        return self.absolute()

    def __bool__(self) -> bool:
        return not self.is_zero

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, operation="comparison")
        return self.amount < other.amount

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, operation="comparison")
        return self.amount <= other.amount

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, operation="comparison")
        return self.amount > other.amount

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._require_same_currency(other, operation="comparison")
        return self.amount >= other.amount


__all__ = [
    "CurrencySpecification",
    "DecimalInput",
    "Money",
    "RoundingMode",
    "Scalar",
    "currency_specification",
]