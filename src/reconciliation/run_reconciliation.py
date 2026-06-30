from dataclasses import asdict

from pathlib import Path

import pandas as pd

from src.reconciliation.matcher import SettlementMatcher


PAYPAL_FILE = Path(
    "data/normalized/payment_transactions.csv"
)

BANK_FILE = Path(
    "data/normalized/bank_transactions.csv"
)

OUTPUT_FILE = Path(
    "data/reports/reconciliation_results.csv"
)


def main():

    print("Loading datasets...")

    paypal = pd.read_csv(
        PAYPAL_FILE,
        parse_dates=["transaction_datetime"],
    )

    bank = pd.read_csv(
        BANK_FILE,
        parse_dates=["transaction_date"],
    )
    print(paypal.dtypes)
    print(bank.dtypes)

    print(
        f"PayPal transactions: {len(paypal):,}"
    )

    print(
        f"Bank transactions: {len(bank):,}"
    )

    print("\nPreparing daily datasets...")

    paypal_daily = (
        paypal[
            paypal["raw_type"]
            == "PreApproved Payment Bill User Payment"
        ]
        .groupby(
            paypal["transaction_datetime"].dt.normalize()
        )
        .agg(
            net_amount=("net_amount", "sum")
        )
        .reset_index()
        .rename(
            columns={
                "transaction_datetime": "processing_day"
            }
        )
    )

    bank_daily = (
        bank[
            bank["transaction_type"]
            == "PAYPAL_SETTLEMENT"
        ]
        .groupby("transaction_date")
        .agg(
            settlement_amount=(
                "credit_amount",
                "sum",
            )
        )
        .reset_index()
    )

    print(paypal_daily.dtypes)
    print(bank_daily.dtypes)

    matcher = SettlementMatcher()

    matches = matcher.match_daily(
        paypal_daily,
        bank_daily,
    )

    reconciliation = pd.DataFrame(
        [
            asdict(match)
            for match in matches
        ]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    reconciliation.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nGenerated {len(reconciliation)} reconciliation rows."
    )

    print(
        f"Saved:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":

    main()