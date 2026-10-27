"""API endpoints for collateral eligibility.

Provides a GET endpoint returning total eligible collateral and breakdown.
"""
from fastapi import APIRouter, Depends, HTTPException
from decimal import Decimal
import pandas as pd

from ..repository import DuckDBRepository, Repository
from ..calculations import compute_eligible_collateral

router = APIRouter(prefix="/collateral", tags=["Collateral"])

def get_repo() -> Repository:
    # In a real app this could be a dependency with lifecycle management
    return DuckDBRepository()

@router.get("/eligible")
async def eligible_collateral(repo: Repository = Depends(get_repo)):
    collateral_df = repo.get_collateral()
    if collateral_df.empty:
        raise HTTPException(status_code=404, detail="No collateral data found")
    total = compute_eligible_collateral(collateral_df)
    # Return breakdown per asset for transparency
    breakdown = []
    for _, row in collateral_df.iterrows():
        if not row["encumbered"]:
            eligible = (row["market_value"] * (Decimal('1') - row["haircut"]))
            breakdown.append({
                "asset_id": int(row["asset_id"]),
                "market_value": str(row["market_value"]),
                "haircut": str(row["haircut"]),
                "eligible": str(eligible.quantize(Decimal('0.01'))),
            })
    return {
        "total_eligible_collateral": str(total),
        "breakdown": breakdown,
    }
