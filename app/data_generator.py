"""Synthetic deterministic data generator for LiqShield.

All random generation is seeded for reproducibility. The dataset includes:
- Cash balances per day
- Collateral assets with haircuts and encumbrance flags
- Existing encumbrances linking collateral to exposures
"""
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

SEED = 42
np.random.seed(SEED)

def generate_cash(start_date: datetime, days: int) -> pd.DataFrame:
    """Generate deterministic cash balance series.
    Returns DataFrame with columns: date, cash_balance (Decimal).
    """
    dates = [start_date + timedelta(days=i) for i in range(days)]
    # start with 10M, random daily change between -0.5M and +0.5M
    changes = np.random.uniform(-5e5, 5e5, size=days)
    balances = []
    balance = 10_000_000.0
    for change in changes:
        balance += float(change)
        balances.append(Decimal(round(balance, 2)))
    return pd.DataFrame({"date": dates, "cash_balance": balances})

def generate_collateral(num_assets: int) -> pd.DataFrame:
    """Generate collateral assets.
    Columns: asset_id (int), market_value (Decimal), haircut (Decimal), encumbered (bool)
    """
    asset_ids = np.arange(1, num_assets + 1)
    # market values between 1M and 20M
    market_vals = np.random.uniform(1e6, 2e7, size=num_assets)
    # haircuts between 0% and 10%
    haircuts = np.random.choice([0.0, 0.02, 0.05, 0.1], size=num_assets)
    # randomly encumber 30% of assets
    encumb = np.random.rand(num_assets) < 0.3
    rows = []
    for aid, mv, hc, enc in zip(asset_ids, market_vals, haircuts, encumb):
        rows.append({
            "asset_id": int(aid),
            "market_value": Decimal(round(mv, 2)),
            "haircut": Decimal(str(hc)),
            "encumbered": bool(enc),
        })
    return pd.DataFrame(rows)

def generate_encumbrances(collateral_df: pd.DataFrame) -> pd.DataFrame:
    """Generate encumbrance records linking collateral to exposures.
    Only includes assets where encumbered == True.
    Columns: asset_id, exposure_id, amount (Decimal)
    """
    enc_assets = collateral_df[collateral_df["encumbered"]]
    rows = []
    for _, row in enc_assets.iterrows():
        # each encumbered asset linked to 1-3 exposures
        n = np.random.randint(1, 4)
        for i in range(n):
            exposure_id = f"EXP{np.random.randint(1000, 9999)}"
            amount = row["market_value"] * Decimal(str(np.random.uniform(0.2, 0.8)))
            rows.append({
                "asset_id": int(row["asset_id"]),
                "exposure_id": exposure_id,
                "amount": amount.quantize(Decimal('0.01')),
            })
    return pd.DataFrame(rows)

def create_synthetic_dataset(base_path: str = "./data"):
    """Create all CSV files under the specified base directory.
    """
    import os
    os.makedirs(base_path, exist_ok=True)
    start = datetime(2023, 1, 1)
    cash_df = generate_cash(start, 30)
    cash_df.to_csv(os.path.join(base_path, "cash.csv"), index=False)
    coll_df = generate_collateral(10)
    coll_df.to_csv(os.path.join(base_path, "collateral.csv"), index=False)
    enc_df = generate_encumbrances(coll_df)
    enc_df.to_csv(os.path.join(base_path, "encumbrances.csv"), index=False)

if __name__ == "__main__":
    create_synthetic_dataset()
