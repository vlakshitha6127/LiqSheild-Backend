"""Business calculation utilities for LiqShield.

All monetary amounts use Decimal to avoid floating‑point errors.
"""
from decimal import Decimal
import pandas as pd

def compute_eligible_collateral(collateral_df: pd.DataFrame) -> Decimal:
    """Return total eligible collateral value.

    Eligible collateral = sum of (market_value * (1 - haircut)) for assets
    where ``encumbered`` is False.
    Missing haircut values are treated as 0 (no haircut).
    """
    # Ensure required columns exist and correct types
    df = collateral_df.copy()
    if "encumbered" not in df.columns:
        df["encumbered"] = False
    if "haircut" not in df.columns:
        df["haircut"] = Decimal('0')
    # Fill missing values
    df["encumbered"] = df["encumbered"].fillna(False).astype(bool)
    df["haircut"] = df["haircut"].apply(lambda x: Decimal(str(x)) if x is not None else Decimal('0'))
    # Filter non‑encumbered assets
    df = df[df["encumbered"] == False]
    # Compute after‑haircut value
    df["eligible"] = df["market_value"] * (Decimal('1') - df["haircut"])
    total = df["eligible"].sum()
    return total.quantize(Decimal('0.01'))

# ---------------------------------------------------------------------------
# Cash transaction utilities
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Cash transaction utilities
# ---------------------------------------------------------------------------

def compute_cash_deltas(cash_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with columns:
        date (datetime), delta (Decimal)
    where ``delta`` is the change in cash_balance from the previous day.
    The first day delta is the initial cash balance.
    """
    df = cash_df.sort_values("date").copy()
    df["prev"] = df["cash_balance"].shift(fill_value=Decimal("0"))
    df["delta"] = (df["cash_balance"] - df["prev"]).apply(lambda x: Decimal(str(x)))
    return df[["date", "delta"]]

def apply_stress(cash_df: pd.DataFrame, delay_days: int, margin_multiplier: Decimal) -> pd.DataFrame:
    """Apply stress to cash balances.

    * ``delay_days`` – shift **inflows only** (positive deltas, excluding the opening cash) forward by the given number of days.
    * ``margin_multiplier`` – multiply **outflows only** (negative deltas) by the factor.
    The function works on a copy and never mutates the original ``cash_df``.
    Returns a DataFrame with the same schema as ``cash_df`` (``date`` and ``cash_balance`` as ``Decimal``).
    """
    # Compute daily deltas
    deltas = compute_cash_deltas(cash_df)
    # Identify inflows (positive) and outflows (negative)
    inflow_mask = deltas["delta"] > Decimal("0")
    outflow_mask = deltas["delta"] < Decimal("0")

    # Apply margin multiplier to outflows (keep them on their original day)
    deltas.loc[outflow_mask, "delta"] = deltas.loc[outflow_mask, "delta"] * margin_multiplier

    # Prepare a new deltas series initialized to zero
    stressed_deltas = pd.DataFrame({"delta": [Decimal("0")] * len(deltas)})
    # Preserve the opening cash balance (the first delta) exactly once
    stressed_deltas.at[0, "delta"] = deltas.at[0, "delta"]

    # Shift inflows (excluding the opening cash at index 0)
    for idx, row in deltas[inflow_mask & (deltas.index != 0)].iterrows():
        target_idx = idx + delay_days
        if target_idx < len(deltas):
            stressed_deltas.at[target_idx, "delta"] += row["delta"]
        # If the shift exceeds the horizon we drop the inflow (cash unavailable)

    # Add outflows back to their original positions (they were already scaled)
    stressed_deltas.loc[outflow_mask, "delta"] += deltas.loc[outflow_mask, "delta"]

    # Re‑accumulate cash balances from the opening balance using the stressed deltas
    stressed_deltas["cash_balance"] = stressed_deltas["delta"].cumsum()
    # Preserve dates from the original dataframe
    stressed_deltas["date"] = cash_df["date"].values
    return stressed_deltas[["date", "cash_balance"]]
    """Apply stress to cash balances.

    * ``delay_days`` – shift **inflows only** (positive deltas) forward by the given number of days.
    * ``margin_multiplier`` – multiply **outflows only** (negative deltas) by the factor.
    The function works on a copy and never mutates the original DataFrame.
    Returns a DataFrame with the same schema as ``cash_df`` (date, cash_balance as Decimal).
    """
    # Compute deltas
    deltas = compute_cash_deltas(cash_df)
    # Separate inflows and outflows
    inflow_mask = deltas["delta"] > Decimal("0")
    outflow_mask = deltas["delta"] < Decimal("0")

    # Apply margin multiplier to outflows
    deltas.loc[outflow_mask, "delta"] = (
        deltas.loc[outflow_mask, "delta"] * margin_multiplier
    )

    # Shift inflows forward by delay_days (keeping same amount on the shifted day)
    shifted = deltas.copy()
    shifted["delta"] = Decimal("0")
    for idx, row in deltas[inflow_mask].iterrows():
        target_idx = idx + delay_days
        if target_idx < len(deltas):
            shifted.at[target_idx, "delta"] += row["delta"]
        else:
            # If shift goes beyond the horizon, drop it (cash is unavailable)
            pass
    # Add the (possibly modified) outflows back to the shifted frame
    shifted.loc[outflow_mask, "delta"] = deltas.loc[outflow_mask, "delta"]

    # Re‑accumulate cash balances starting from the first day cash (which is delta[0])
    shifted = shifted.sort_index()
    shifted["cash_balance"] = shifted["delta"].cumsum()
    # Preserve dates
    shifted["date"] = cash_df["date"].values
    return shifted[["date", "cash_balance"]]

