from pathlib import Path

import pandas as pd
import pdfplumber


class FirstBankPDFExtractor:
    """
    Extract raw transaction tables from a folder containing
    FirstBank PDF statements.

    Responsibility:
        Folder -> Raw DataFrame
    """

    def __init__(self, input_folder: Path):
        self.input_folder = input_folder

        self.raw_df: pd.DataFrame | None = None

    def extract(self) -> pd.DataFrame:

        pdf_files = sorted(
            self.input_folder.glob("*.pdf")
        )

        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in {self.input_folder}"
            )

        rows = []

        print(
            f"\nFound {len(pdf_files)} PDF statements.\n"
        )

        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")

            with pdfplumber.open(pdf_file) as pdf:
                page = pdf.pages[0]

                print("=" * 80)
                print(f"FIRST PAGE OF: {pdf_file.name}")
                print("=" * 80)

                text = page.extract_text()

                print(text[:2000])

                break

        self.raw_df = pd.DataFrame(rows)

        print(
            f"\nExtracted {len(self.raw_df):,} rows."
        )

        return self.raw_df


if __name__ == "__main__":

    extractor = FirstBankPDFExtractor(
        Path(
            "data/raw/bank/2026/2026-2092"
        )
    )

    df = extractor.extract()

    print()

    print(df.head())

    print()

    print(df.shape)