from datetime import datetime
from decimal import Decimal

from src.normalization.models import BankTransaction

from .patterns import (
    BEGINNING_BALANCE_PATTERN,
    TRANSACTION_DATE_PATTERN,
    TRANSACTION_PATTERN,
)


class FirstBankParser:

    def is_transaction_line(self, line: str) -> bool:

        if not line:
            return False

        return bool(
            TRANSACTION_DATE_PATTERN.match(line.strip())
        )

    def find_beginning_balance(
        self,
        lines: list[str],
    ) -> Decimal:

        for line in lines:

            match = BEGINNING_BALANCE_PATTERN.search(line)

            if match:
                return Decimal(
                    match.group(1).replace(",", "")
                )

        raise ValueError(
            "Beginning balance not found."
        )

    def parse_paypal_transaction(
        self,
        line: str,
    ) -> BankTransaction:

        match = TRANSACTION_PATTERN.match(line)

        if not match:
            raise ValueError(
                f"Unable to parse:\n{line}"
            )

        transaction_date = datetime.strptime(
            match.group("date"),
            "%m/%d/%Y",
        )

        description = match.group("description")

        amount = Decimal(
            match.group("amount").replace(",", "")
        )

        balance = Decimal(
            match.group("balance").replace(",", "")
        )

        return BankTransaction(
            source_system="firstbank",
            account_number="2092",
            transaction_date=transaction_date,
            description=description,
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
            running_balance=balance,
            currency="USD",
            transaction_reference=None,
            transaction_type="PAYPAL_SETTLEMENT",
        )


if __name__ == "__main__":

    parser = FirstBankParser()

    line = (
        "03/02/2026 PAYPAL TRANSFER "
        "1048615785827 $1,069.86 $47,169.27"
    )

    transaction = parser.parse_paypal_transaction(line)

    print(transaction)