from decimal import Decimal

import pandas as pd

from .models import SettlementMatch


class SettlementMatcher:
    """
    Match processor settlements against bank deposits.
    """

    def __init__(
        self,
        tolerance: Decimal = Decimal("1.00"),
    ):
        self.tolerance = tolerance

    def match_daily(
        self,
        processor_df: pd.DataFrame,
        bank_df: pd.DataFrame,
    ) -> list[SettlementMatch]:

        matches = []

        merged = processor_df.merge(
            bank_df,
            left_on="processing_day",
            right_on="transaction_date",
            how="left",
        )

        for _, row in merged.iterrows():

            bank_amount = row["settlement_amount"]

            if pd.isna(bank_amount):
                bank_amount = Decimal("0.00")

            variance = Decimal(
                str(row["net_amount"])
            ) - Decimal(str(bank_amount))

            status = (
                "MATCH"
                if abs(variance) <= self.tolerance
                else "REVIEW"
            )

            matches.append(

                SettlementMatch(

                    processing_start=row["processing_day"],

                    processing_end=row["processing_day"],

                    settlement_date=row["transaction_date"],

                    processor_amount=Decimal(
                        str(row["net_amount"])
                    ),

                    bank_amount=Decimal(
                        str(bank_amount)
                    ),

                    variance=variance,

                    status=status,
                )

            )

        return matches