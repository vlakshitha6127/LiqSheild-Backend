# LiqShield

## Collateral & Liquidity Stress Intelligence

This repository implements a backend service that answers the question:

> "Can a financial institution meet its time-sensitive obligations using the cash and collateral it can actually mobilise?"

The backend is built with **FastAPI**, uses **DuckDB** for local data storage, and **pandas** for data manipulation. It provides deterministic synthetic data for development and a clear repository layer that can later be swapped for an Exasol implementation.

### Project Structure
```
LiqShield/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ api/
│  │   ├─ __init__.py
│  │   ├─ health.py
│  │   ├─ collateral.py
│  │   ├─ liquidity.py
│  │   └─ stress.py
│  ├─ models.py
│  ├─ repository.py
│  ├─ calculations.py
│  └─ data_generator.py
├─ tests/
│  ├─ __init__.py
│  ├─ test_collateral.py
│  ├─ test_liquidity.py
│  └─ test_stress.py
├─ pyproject.toml
├─ requirements.txt
├─ README.md
└─ .gitignore
```

### Getting Started
1. **Install dependencies** (run on your Windows machine where `py` points to Python):
   ```
   py -m pip install -r requirements.txt
   ```
2. **Run the API**:
   ```
   py -m uvicorn app.main:app --reload
   ```
3. **Run tests**:
   ```
   py -m pytest
   ```

### Design Notes
- All monetary amounts are stored as `Decimal` to avoid floating‑point inaccuracies.
- Haircuts are defined as fractional values (e.g., `0.02` for 2 %).
- Collateral that is already encumbered (used as security for other exposures) is excluded from the eligible pool.
- The repository pattern abstracts the data source – DuckDB is used now, but Member 1 can replace it with an Exasol implementation without touching the business logic.
- Synthetic data is deterministic, seeded for reproducibility, and covers cash balances, collateral assets, and existing encumbrances.

### Future Work
- Integrate with Exasol via `pyexasol` (to be done by Member 1).
- Add more stress‑scenario types.
- Expose health metrics and OpenAPI documentation (already available via FastAPI).

---
