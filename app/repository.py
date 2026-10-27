"""Repository interface and DuckDB implementation for LiqShield.

Provides methods to load synthetic data and query eligible collateral, cash balances, and encumbrances.
"""
import duckdb
import pandas as pd
from pathlib import Path
from decimal import Decimal

class Repository:
    """Abstract repository interface."""
    def get_cash(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_collateral(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_encumbrances(self) -> pd.DataFrame:
        raise NotImplementedError

class DuckDBRepository(Repository):
    def __init__(self, db_path: str = "./liqshield.duckdb", data_dir: str = "./data"):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self._connect()
        self._ensure_tables()

    def _connect(self):
        self.conn = duckdb.connect(self.db_path)
        # Enable Decimal handling
        self.conn.execute("SET enable_object_cache=true;")

    def _ensure_tables(self):
        # Load CSVs into DuckDB if tables not exist
        for table, file_name in [
            ("cash", "cash.csv"),
            ("collateral", "collateral.csv"),
            ("encumbrances", "encumbrances.csv"),
        ]:
            # DuckDB does not support SHOW TABLES LIKE; query the information_schema instead
            exists = self.conn.execute(
                f"SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = '{table}' AND table_schema = 'main'"
            ).fetchone()[0]
            if not exists:
                csv_path = self.data_dir / file_name
                if csv_path.exists():
                    self.conn.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{csv_path}')")
                else:
                    raise FileNotFoundError(f"Synthetic data file not found: {csv_path}")

    def get_cash(self) -> pd.DataFrame:
        df = self.conn.execute("SELECT * FROM cash ORDER BY date").fetchdf()
        # Convert cash_balance to Decimal
        df['cash_balance'] = df['cash_balance'].apply(lambda x: Decimal(str(x)))
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        return df

    def get_collateral(self) -> pd.DataFrame:
        df = self.conn.execute("SELECT * FROM collateral").fetchdf()
        # Cast numeric columns to Decimal for precise calculations
        for col in ["market_value", "haircut"]:
            df[col] = df[col].apply(lambda x: Decimal(str(x)))
        # Ensure encumbered is boolean (DuckDB may return 0/1)
        if df["encumbered"].dtype != bool:
            df["encumbered"] = df["encumbered"].astype(bool)
        return df

    def get_encumbrances(self) -> pd.DataFrame:
        return self.conn.execute("SELECT * FROM encumbrances").fetchdf()
