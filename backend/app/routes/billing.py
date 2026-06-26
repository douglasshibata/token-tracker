from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..services.database import Database
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter(prefix="/billing", tags=["billing"])
db = Database()

class TopUpRequest(BaseModel):
    user_id: UUID
    amount: Decimal

class TierUpgradeRequest(BaseModel):
    user_id: UUID
    tier: str

@router.get("/status/{user_id}")
async def get_billing_status(user_id: UUID):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT subscription_tier, balance FROM gateway_users WHERE id = $1",
            user_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)

@router.post("/topup")
async def top_up_balance(request: TopUpRequest):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE gateway_users SET balance = balance + $2 WHERE id = $1 RETURNING balance",
            request.user_id, request.amount
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return {"new_balance": row['balance']}

@router.post("/upgrade")
async def upgrade_tier(request: TierUpgradeRequest):
    if request.tier not in ['free', 'pro', 'enterprise']:
        raise HTTPException(status_code=400, detail="Invalid tier")

    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE gateway_users SET subscription_tier = $2 WHERE id = $1 RETURNING subscription_tier",
            request.user_id, request.tier
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return {"new_tier": row['subscription_tier']}
