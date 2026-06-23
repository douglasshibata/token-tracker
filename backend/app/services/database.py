import asyncpg
from datetime import datetime
from typing import Dict, Any, Optional
import os
import json
from uuid import UUID

class Database:
    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://tracker:password@localhost:5432/token_tracker")
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.dsn)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def check_budget(self, user_id: UUID, estimated_cost: float) -> Dict[str, Any]:
        if not self.pool: await self.connect()

        async with self.pool.acquire() as conn:
            # Check budgets for this user
            row = await conn.fetchrow(
                "SELECT cost_limit, cost_used FROM budgets WHERE entity_id = $1 AND is_active = TRUE",
                str(user_id)
            )

            if not row:
                return {"allowed": True}

            cost_limit, cost_used = row['cost_limit'], row['cost_used']

            if cost_limit and (float(cost_used) + estimated_cost) > float(cost_limit):
                return {"allowed": False, "reason": f"Budget limit (${cost_limit}) exceeded."}

            return {"allowed": True}
