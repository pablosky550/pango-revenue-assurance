from decimal import Decimal


def safe_decimal(value: str) -> Decimal:
    """
    Safely converts monetary values into Decimal.
    """
    if value in ("", None):
        return Decimal("0.00")

    value = str(value).replace(",", "")

    return Decimal(value)