from pathlib import Path
import pandas as pd
from .base_normalizer import BaseNormalizer
from .column_mapping import PAYPAL_COLUMN_MAPPING


class PayPalNormalizer(BaseNormalizer):

    REQUIRED_COLUMNS = {
    "Date",
    "Time",
    "Type",
    "Status",
    "Currency",
    "Gross",
    "Fee",
    "Net",
    "Transaction ID",
    "Reference Txn ID",
    "Balance",
    "Balance Impact",
    }


    def load(self):
        """
        Load PayPal Excel export into memory.
        """

        if not self.input_file.exists():
            raise FileNotFoundError(
                f"Input file not found: {self.input_file}"
            )

        self.raw_df = pd.read_excel(
            self.input_file,
            engine="openpyxl"
        )

        print(f"Loaded {len(self.raw_df):,} PayPal transactions.")

        # print("\nColumns:")
        # print(self.raw_df.columns.tolist())

        # print("\nData types:")
        # print(self.raw_df.dtypes)

        # print("\nFirst 5 rows:")
        # print(self.raw_df.head())

    def validate_schema(self):
        """
        Validate PayPal export structure.
        """

        missing = self.REQUIRED_COLUMNS - set(self.raw_df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        print("Schema validation passed.")

    def profile_dataset(self):
        """
        Print a basic profile of the raw PayPal dataset.
        """

        print("\n" + "=" * 80)
        print("PAYPAL DATASET PROFILE")
        print("=" * 80)

        print(f"\nRows: {len(self.raw_df):,}")
        print(f"Columns: {len(self.raw_df.columns)}")

        print("\nMissing Values:")
        print(self.raw_df.isna().sum().sort_values(ascending=False))

        print("\nUnique Transaction Types:")
        print(self.raw_df["Type"].value_counts())

        print("\nUnique Status Values:")
        print(self.raw_df["Status"].value_counts())

        print("\nUnique Currency Values:")
        print(self.raw_df["Currency"].value_counts())

    def normalize(self):
        """
        Normalize the raw PayPal export into the platform's canonical schema.
        """

        df = self.raw_df.copy()

        # Create transaction datetime
        # Convert Time to string if needed
        time_str = df["Time"].astype(str)

        df["transaction_datetime"] = pd.to_datetime(
            df["Date"].dt.strftime("%Y-%m-%d") + " " + time_str
        )

        if df["transaction_datetime"].isna().any():
            raise ValueError("Some transaction datetimes could not be parsed.")

        # Preserve original PayPal transaction type
        df["raw_type"] = df["Type"]

        # Select relevant columns
        df = df[
            [
                "Transaction ID",
                "Reference Txn ID",
                "Type",
                "raw_type",
                "Status",
                "transaction_datetime",
                "Currency",
                "Gross",
                "Fee",
                "Net",
                "From Email Address",
                "To Email Address",
                "Balance",
                "Balance Impact",
            ]
        ].copy()

        # Rename columns
        df.rename(
            columns={
                **PAYPAL_COLUMN_MAPPING,
                "transaction_datetime": "transaction_datetime",
            },
            inplace=True,
        )

        # Add source system
        df.insert(
            0,
            "source_system",
            "paypal",
        )

        self.normalized_df = df

        print(
            f"Normalized {len(self.normalized_df):,} transactions."
        )

    def save(self):
        """
        Save normalized transactions to CSV.
        """

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.normalized_df.to_csv(
            self.output_file,
            index=False,
        )

        print(
            f"Saved normalized dataset to:\n{self.output_file}"
        )


if __name__ == "__main__":

    normalizer = PayPalNormalizer(
        input_file=Path("data/raw/paypal/PayPal_20260101_20260331.xlsx"),
        output_file=Path("data/normalized/payment_transactions.csv"),
)

    normalizer.load()
    normalizer.validate_schema()
    #normalizer.profile_dataset()
    normalizer.normalize()
    normalizer.save()
