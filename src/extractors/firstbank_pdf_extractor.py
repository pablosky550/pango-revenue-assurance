from pathlib import Path

import pdfplumber
from src.parsers.firstbank_parser import FirstBankParser


class FirstBankPDFExtractor:
    """
    Extract raw text lines from FirstBank PDF statements.

    Responsibility:
        Folder of PDFs -> List[str]
    """

    def __init__(self, input_folder: Path):
        self.input_folder = input_folder

    def extract_lines(self) -> list[str]:

        pdf_files = sorted(self.input_folder.glob("*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in {self.input_folder}"
            )

        all_lines = []
        parser = FirstBankParser()

        print(f"\nFound {len(pdf_files)} PDF statements.\n")

        for pdf_file in pdf_files:

            print(f"Processing: {pdf_file.name}")

            with pdfplumber.open(pdf_file) as pdf:

                for page in pdf.pages:

                    text = page.extract_text()

                    if not text:
                        continue

                    page_lines = text.splitlines()

                    for line in page_lines:

                        if parser.is_transaction_line(line):
                            all_lines.append(line)

                print(f"\nExtracted {len(all_lines):,} text lines.")

        return all_lines


if __name__ == "__main__":

    extractor = FirstBankPDFExtractor(
        Path("data/raw/bank/2026/2026-2092")
    )

    lines = extractor.extract_lines()

    print("\nFirst 40 lines:\n")

    for line in lines[:40]:
        print(line)