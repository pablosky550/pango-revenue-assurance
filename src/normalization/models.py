from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class PaymentTransaction:
    """
    Canonical payment transaction model.

    Every payment processor (PayPal, Braintree, etc.) must be
    normalized into this structure before being loaded into the
    Revenue Assurance platform.
    """

    source_system: str

    transaction_id: str
    reference_transaction_id: Optional[str]

    transaction_type: str
    raw_transaction_type: str

    transaction_status: str

    transaction_datetime: datetime

    currency: str

    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal

    payer: Optional[str]
    payee: Optional[str]

    balance: Optional[Decimal]
    balance_impact: Optional[str]