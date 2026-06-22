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

    async def check_budget(self, project_id: str, estimated_cost: float) -> Dict[str, Any]:
        if not self.pool: await self.connect()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT daily_limit, monthly_limit, total_limit FROM projects WHERE id = $1",
                UUID(project_id) if isinstance(project_id, str) and len(project_id) == 36 else project_id
            )

            if not row:
                return {"allowed": True}

            daily_lim, monthly_lim, total_lim = row['daily_limit'], row['monthly_limit'], row['total_limit']

            spend_row = await conn.fetchrow("""
                SELECT
                    COALESCE(SUM(CASE WHEN created_at >= NOW() - INTERVAL '1 day' THEN cost ELSE 0 END), 0) as daily_spend,
                    COALESCE(SUM(CASE WHEN created_at >= DATE_TRUNC('month', NOW()) THEN cost ELSE 0 END), 0) as monthly_spend,
                    COALESCE(SUM(cost), 0) as total_spend
                FROM api_logs
                WHERE project_id = $1 AND was_blocked = FALSE
            """, UUID(project_id) if isinstance(project_id, str) and len(project_id) == 36 else project_id)

            daily_spend = float(spend_row['daily_spend'])
            monthly_spend = float(spend_row['monthly_spend'])
            total_spend = float(spend_row['total_spend'])

            if daily_lim and (daily_spend + estimated_cost) > float(daily_lim):
                return {"allowed": False, "reason": f"Daily limit (${daily_lim}) exceeded."}
            if monthly_lim and (monthly_spend + estimated_cost) > float(monthly_lim):
                return {"allowed": False, "reason": f"Monthly limit (${monthly_lim}) exceeded."}
            if total_lim and (total_spend + estimated_cost) > float(total_lim):
                return {"allowed": False, "reason": f"Total limit (${total_lim}) exceeded."}

            return {"allowed": True}

    async def get_or_create_session(self, project_id: str, source: str, session_id: Optional[str] = None) -> UUID:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            if session_id:
                try:
                    s_uuid = UUID(session_id)
                    exists = await conn.fetchval("SELECT id FROM ai_sessions WHERE id = $1", s_uuid)
                    if exists: return exists
                except:
                    pass

            row = await conn.fetchrow("""
                INSERT INTO ai_sessions (project_id, source)
                VALUES ($1, $2)
                RETURNING id
            """, UUID(project_id) if isinstance(project_id, str) and len(project_id) == 36 else project_id, source)
            return row['id']

    async def log_request(self, project_id: str, provider: str, model: str,
                          session_id: Optional[UUID] = None,
                          input_tokens: int = 0, output_tokens: int = 0,
                          cost: float = 0, latency_ms: int = 0,
                          was_blocked: bool = False, block_reason: str = None,
                          is_tool_call: bool = False, tool_name: str = None,
                          generation_ratio: float = 0,
                          metadata: dict = None):
        if not self.pool: await self.connect()

        metadata_json = json.dumps(metadata) if metadata else None

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO api_logs
                (project_id, session_id, provider, model, input_tokens, output_tokens,
                 cost, latency_ms, was_blocked, block_reason, is_tool_call, tool_name,
                 generation_ratio, request_metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, UUID(project_id) if isinstance(project_id, str) and len(project_id) == 36 else project_id,
            session_id, provider, model, input_tokens, output_tokens, float(cost), latency_ms,
            was_blocked, block_reason, is_tool_call, tool_name, float(generation_ratio), metadata_json)
