from pathlib import Path
from typing import Optional

import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()


class MySQLLoader:
    """
    Generic CSV loader for the Revenue Assurance platform.
    """

    def __init__(self):

        self.connection = None
        self.cursor = None

    def connect(self):

        self.connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

        self.cursor = self.connection.cursor()

        print("Connected to MySQL.")

    def close(self):

        if self.cursor:
            self.cursor.close()

        if self.connection:
            self.connection.close()

        print("Connection closed.")

    def load_csv(
        self,
        csv_file: Path,
    ) -> pd.DataFrame:

        df = pd.read_csv(csv_file)

        print(
            f"Loaded {len(df):,} rows from {csv_file.name}"
        )

        return df

    def insert_dataframe(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
    ):

        columns = list(dataframe.columns)
        print(columns)

        placeholders = ", ".join(["%s"] * len(columns))

        column_names = ", ".join(
            f"`{c}`"
            for c in columns
        )

        query = f"""
        INSERT INTO {table_name}
        ({column_names})
        VALUES ({placeholders})
        """
        print(query)

        # Replace every NaN with Python None
        clean_df = dataframe.astype(object).where(
            pd.notnull(dataframe),
            None,
        )

        data = clean_df.values.tolist()

        print(data[0])
        
        self.cursor.executemany(query, data)

        self.connection.commit()

        print(
            f"Inserted {len(data):,} rows into {table_name}."
        )


if __name__ == "__main__":

    loader = MySQLLoader()

    loader.connect()

    payment_df = loader.load_csv(
        Path(
            "data/normalized/payment_transactions.csv"
        )
    )

    loader.insert_dataframe(
        payment_df,
        "payment_transactions",
    )

    bank_df = loader.load_csv(
        Path(
            "data/normalized/bank_transactions.csv"
        )
    )

    loader.insert_dataframe(
        bank_df,
        "bank_transactions",
    )

    loader.close()