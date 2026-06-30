from dataclasses import asdict

from pathlib import Path

import pandas as pd

from src.extractors.firstbank_pdf_extractor import (
    FirstBankPDFExtractor,
)
from src.parsers.firstbank_parser import FirstBankParser

from .base_normalizer import BaseNormalizer


class BankNormalizer(BaseNormalizer):
    """
    Normalize FirstBank statements into the canonical
    bank transaction dataset.
    """

    def load(self):

        extractor = FirstBankPDFExtractor(
            self.input_file
        )

        self.raw_lines = extractor.extract_lines()

        print(
            f"Loaded {len(self.raw_lines):,} raw lines."
        )

    def normalize(self):

        parser = FirstBankParser()

        transactions = []

        for line in self.raw_lines:

            if "PAYPAL TRANSFER" not in line:
                continue

            transaction = parser.parse_paypal_transaction(
                line
            )

            transactions.append(asdict(transaction))

        self.normalized_df = pd.DataFrame(
            transactions
        )

        print(
            f"Normalized {len(self.normalized_df):,} bank transactions."
        )

    def save(self):

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.normalized_df.to_csv(
            self.output_file,
            index=False,
        )

        print(
            f"Saved:\n{self.output_file}"
        )


if __name__ == "__main__":

    normalizer = BankNormalizer(
        input_file=Path(
            "data/raw/bank/2026/2026-2092"
        ),
        output_file=Path(
            "data/normalized/bank_transactions.csv"
        ),
    )

    normalizer.load()
    normalizer.normalize()
    normalizer.save()