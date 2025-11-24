from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime

from app.routers import (
    cost_estimation,
    insurance,
    bills,
    navigation,
    assistance,
    payment_plans,
    auth,
    user_data
)
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(
    title="MedFin - Healthcare Financial Navigator",
    description="Autonomous healthcare financial navigation system",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_data.router, prefix="/api/v1/user", tags=["User Data"])
app.include_router(cost_estimation.router, prefix="/api/v1/cost", tags=["Cost Estimation"])
app.include_router(insurance.router, prefix="/api/v1/insurance", tags=["Insurance"])
app.include_router(bills.router, prefix="/api/v1/bills", tags=["Bills"])
app.include_router(navigation.router, prefix="/api/v1/navigation", tags=["Navigation"])
app.include_router(assistance.router, prefix="/api/v1/assistance", tags=["Assistance"])
app.include_router(payment_plans.router, prefix="/api/v1/payment-plans", tags=["Payment Plans"])


@app.get("/")
async def root():
    return {
        "message": "MedFin Healthcare Financial Navigator API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
