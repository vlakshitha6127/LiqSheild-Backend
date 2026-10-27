"""API endpoints for liquidity ladder.

Provides a GET endpoint returning the deterministic cash balance series (date, cash_balance).
"""
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from ..repository import DuckDBRepository, Repository

router = APIRouter(prefix="/liquidity", tags=["Liquidity"])

def get_repo() -> Repository:
    return DuckDBRepository()

@router.get("/ladder")
async def cash_ladder(repo: Repository = Depends(get_repo)):
    cash_df = repo.get_cash()
    if cash_df.empty:
        raise HTTPException(status_code=404, detail="No cash data found")
    ladder = [
        {"date": d.date().isoformat(), "cash_balance": str(cb)}
        for d, cb in zip(cash_df["date"], cash_df["cash_balance"])
    ]
    return {"ladder": ladder}
