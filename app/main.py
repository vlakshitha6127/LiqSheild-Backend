"""FastAPI entry point for LiqShield backend.

Provides routes for health check, collateral eligibility, liquidity ladder, and stress testing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import health, collateral, liquidity, stress

app = FastAPI(title="LiqShield API", version="0.1.0")

# Allow CORS for local development (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router modules
app.include_router(health.router)
app.include_router(collateral.router)
app.include_router(liquidity.router)
app.include_router(stress.router)

# Root endpoint provides brief info
@app.get("/")
async def root():
    return {"message": "LiqShield backend is running"}
