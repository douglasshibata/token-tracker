from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime
from ..services.database import Database
from uuid import UUID

router = APIRouter(prefix="/logs", tags=["logs"])
db = Database()

@router.get("/{project_id}")
async def get_logs(project_id: UUID, limit: int = 100):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM api_logs
            WHERE project_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, project_id, limit)
        return [dict(r) for r in rows]

@router.get("/stats/{project_id}")
async def get_stats(project_id: UUID):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(cost), 0) as total_spend,
                COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                COUNT(*) FILTER (WHERE was_blocked = TRUE) as blocked_count,
                COUNT(*) as total_prompts,
                COALESCE(AVG(generation_ratio), 0) as avg_generation_ratio,
                COUNT(*) FILTER (WHERE is_tool_call = TRUE) as tool_calls_count
            FROM api_logs
            WHERE project_id = $1
        """, project_id)
        return dict(row)

@router.get("/productivity/{project_id}")
async def get_productivity(project_id: UUID):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        # Top tools used
        tool_rows = await conn.fetch("""
            SELECT tool_name, COUNT(*) as count
            FROM api_logs
            WHERE project_id = $1 AND is_tool_call = TRUE
            GROUP BY tool_name
            ORDER BY count DESC
            LIMIT 5
        """, project_id)

        # Stats summary
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_prompts,
                COALESCE(SUM(cost), 0) / NULLIF(COUNT(*), 0) as cost_per_prompt,
                (COUNT(*) FILTER (WHERE is_tool_call = TRUE)::float / NULLIF(COUNT(*), 0)) * 100 as code_vs_chat_percentage,
                COALESCE(AVG(generation_ratio), 0) as avg_generation_ratio
            FROM api_logs
            WHERE project_id = $1
        """, project_id)

        return {
            "stats": dict(stats) if stats else {},
            "top_tools": [dict(r) for r in tool_rows]
        }

@router.get("/summary/{project_id}")
async def get_summary(project_id: UUID, year: int, month: int):
    if not db.pool: await db.connect()
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    async with db.pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_prompts,
                COALESCE(SUM(cost), 0) as total_cost,
                COALESCE(AVG(generation_ratio), 0) as avg_gen_ratio
            FROM api_logs
            WHERE project_id = $1 AND created_at >= $2 AND created_at < $3
        """, project_id, start_date, end_date)

        daily_rows = await conn.fetch("""
            SELECT
                DATE(created_at) as date,
                SUM(input_tokens + output_tokens) as tokens
            FROM api_logs
            WHERE project_id = $1 AND created_at >= $2 AND created_at < $3
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, project_id, start_date, end_date)

        return {
            "totalPrompts": stats["total_prompts"],
            "totalCost": round(float(stats["total_cost"]), 4),
            "avgGenRatio": round(float(stats["avg_gen_ratio"]), 2),
            "dailyTrend": [{"name": str(r["date"]), "value": r["tokens"]} for r in daily_rows]
        }
