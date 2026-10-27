import os
import pandas as pd
from decimal import Decimal
from datetime import datetime

# Ensure data directory exists
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# cash.csv – deterministic three‑day series
cash_path = os.path.join(DATA_DIR, "cash.csv")
pd.DataFrame({
    "date": [
        datetime(2023, 1, 1).date(),
        datetime(2023, 1, 2).date(),
        datetime(2023, 1, 3).date(),
    ],
    "cash_balance": [
        Decimal('1000.00'),
        Decimal('1500.00'),
        Decimal('1200.00'),
    ],
}).to_csv(cash_path, index=False)

# collateral.csv – two assets, one encumbered
coll_path = os.path.join(DATA_DIR, "collateral.csv")
pd.DataFrame({
    "asset_id": [1, 2],
    "market_value": [Decimal('2000.00'), Decimal('3000.00')],
    "haircut": [Decimal('0.02'), Decimal('0.05')],
    "encumbered": [False, True],
}).to_csv(coll_path, index=False)

# encumbrances.csv – placeholder (empty) – still valid CSV with header
enc_path = os.path.join(DATA_DIR, "encumbrances.csv")
pd.DataFrame({
    "asset_id": [],
    "exposure_id": [],
    "amount": [],
}).to_csv(enc_path, index=False)
