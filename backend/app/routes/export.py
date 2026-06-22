from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from datetime import datetime
from ..services.database import Database
from uuid import UUID

router = APIRouter(prefix="/export", tags=["export"])
db = Database()

@router.get("/monthly")
async def export_monthly_report(
    project_id: str,
    year: int,
    month: int,
    format: str = "csv"
):
    start_date = datetime(year, month, 1)
    # Simple end date calculation
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                DATE(created_at) as date,
                provider as source,
                COUNT(id) as total_prompts,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(cost) as total_cost,
                SUM(CASE WHEN is_tool_call = TRUE THEN 1 ELSE 0 END) as code_actions
            FROM api_logs
            WHERE project_id = $1 AND created_at >= $2 AND created_at < $3
            GROUP BY DATE(created_at), provider
            ORDER BY date ASC
        """, UUID(project_id) if len(project_id) == 36 else project_id, start_date, end_date)

    if not rows:
        raise HTTPException(status_code=404, detail="No data found for this period")

    df = pd.DataFrame([dict(r) for r in rows])

    # Calculate Productivity Metrics
    df['total_tokens'] = df['total_input_tokens'] + df['total_output_tokens']
    df['generation_ratio'] = (df['total_output_tokens'] / df['total_input_tokens'].replace(0, 1)).round(2)
    df['cost_per_prompt'] = (df['total_cost'] / df['total_prompts']).round(4)
    df['code_vs_chat_pct'] = ((df['code_actions'] / df['total_prompts']) * 100).round(1)

    output = io.BytesIO()
    if format == "excel":
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Daily Trends', index=False)

            tool_summary = df.groupby('source')[['total_prompts', 'total_cost']].sum()
            tool_summary.to_excel(writer, sheet_name='Tool Comparison')

        output.seek(0)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        file_name = f"AI_Metrics_{year}_{month}.xlsx"
    else:
        df.to_csv(output, index=False)
        output.seek(0)
        media_type = "text/csv"
        file_name = f"AI_Metrics_{year}_{month}.csv"

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )
