"""API endpoints for stress scenarios.

Provides a GET endpoint that projects the cash ladder under a settlement delay
and a margin‑call multiplier. The stress is applied on‑the‑fly – the underlying
DuckDB tables are never mutated.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from decimal import Decimal
import pandas as pd

from ..repository import DuckDBRepository, Repository
from ..calculations import apply_stress

router = APIRouter(prefix="/stress", tags=["Stress"])

def get_repo() -> Repository:
    return DuckDBRepository()

@router.get("/run")
async def run_stress(
    delay_days: int = Query(0, ge=0, description="Number of days to delay cash inflows"),
    margin_multiplier: float = Query(1.0, gt=0, description="Multiplier applied to cash outflows (margin calls)"),
    repo: Repository = Depends(get_repo),
):
    """Return a projected cash ladder after applying stress.

    * ``delay_days`` shifts **positive cash deltas** (inflows) forward.
    * ``margin_multiplier`` scales **negative cash deltas** (outflows).
    The original cash data remain unchanged.
    """
    cash_df = repo.get_cash()
    if cash_df.empty:
        raise HTTPException(status_code=404, detail="No cash data found")
    # Convert multiplier to Decimal for precise arithmetic
    multiplier = Decimal(str(margin_multiplier))
    stressed_df = apply_stress(cash_df, delay_days, multiplier)
    ladder = [
        {"date": d.date().isoformat(), "cash_balance": str(cb)}
        for d, cb in zip(stressed_df["date"], stressed_df["cash_balance"])
    ]
    return {
        "ladder": ladder,
        "applied": {"delay_days": delay_days, "margin_multiplier": margin_multiplier},
    }
