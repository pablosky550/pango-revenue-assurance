from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class SettlementMatch:
    """
    Represents a reconciliation result between
    processor activity and bank settlement.
    """

    processing_start: date
    processing_end: date

    settlement_date: date

    processor_amount: Decimal
    bank_amount: Decimal

    variance: Decimal

    status: str