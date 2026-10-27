import os
import pytest
import pandas as pd
from decimal import Decimal
from app.repository import DuckDBRepository
from app.calculations import compute_eligible_collateral, apply_stress

# Helper to create temporary CSV data for repository
@pytest.fixture
def temp_data_dir(tmp_path):
    # cash.csv
    cash_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "cash_balance": [Decimal('1000.00'), Decimal('1500.00'), Decimal('1200.00')],
    })
    cash_df.to_csv(tmp_path / "cash.csv", index=False)
    # collateral.csv
    coll_df = pd.DataFrame({
        "asset_id": [1, 2],
        "market_value": [Decimal('2000.00'), Decimal('3000.00')],
        "haircut": [Decimal('0.02'), Decimal('0.05')],
        "encumbered": [False, True],
    })
    coll_df.to_csv(tmp_path / "collateral.csv", index=False)
    # encumbrances.csv (empty but with header)
    pd.DataFrame({"asset_id": [], "exposure_id": [], "amount": []}).to_csv(tmp_path / "encumbrances.csv", index=False)
    return tmp_path

def test_repository_loads_types(temp_data_dir):
    repo = DuckDBRepository(data_dir=str(temp_data_dir))
    cash = repo.get_cash()
    assert cash['cash_balance'].dtype == object  # Decimal objects
    collateral = repo.get_collateral()
    assert collateral['market_value'].dtype == object
    assert collateral['haircut'].dtype == object
    assert collateral['encumbered'].dtype == bool

def test_compute_eligible_collateral_basic(temp_data_dir):
    repo = DuckDBRepository(data_dir=str(temp_data_dir))
    collateral = repo.get_collateral()
    result = compute_eligible_collateral(collateral)
    # Only asset 1 eligible: 2000 * (1-0.02) = 1960.00
    assert result == Decimal('1960.00')

def test_apply_stress_immutable(temp_data_dir):
    repo = DuckDBRepository(data_dir=str(temp_data_dir))
    cash = repo.get_cash()
    cash_copy = cash.copy()
    # Apply stress with delay 1
    _ = apply_stress(cash, delay_days=1, margin_multiplier=Decimal('2'))
    # Original cash DataFrame must remain unchanged
    assert cash.equals(cash_copy)

    repo = DuckDBRepository(data_dir=str(temp_data_dir))
    cash = repo.get_cash()
    # No delay, margin multiplier 2
    stressed = apply_stress(cash, delay_days=0, margin_multiplier=Decimal('2'))
    # Expected: day0 1000, day1 1500, day2 900 (outflow doubled)
    expected_balances = [Decimal('1000.00'), Decimal('1500.00'), Decimal('900.00')]
    assert list(stressed['cash_balance']) == expected_balances

    repo = DuckDBRepository(data_dir=str(temp_data_dir))
    cash = repo.get_cash()
    # delay 1 day, margin multiplier 2 (outflows double)
    stressed = apply_stress(cash, delay_days=1, margin_multiplier=Decimal('2'))
    # Expected cash balances: day0 1000, day1 1000, day2 900
    expected_balances = [Decimal('1000.00'), Decimal('1000.00'), Decimal('900.00')]
    assert list(stressed['cash_balance']) == expected_balances
