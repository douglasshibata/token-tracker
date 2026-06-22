from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.schemas import ProjectCreate, Project
from ..services.database import Database
from uuid import UUID

router = APIRouter(prefix="/projects", tags=["projects"])
db = Database()

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO projects (name, description, daily_limit, monthly_limit, total_limit)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """, project.name, project.description, project.daily_limit, project.monthly_limit, project.total_limit)
        return dict(row)

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM projects WHERE id = $1", project_id)
        if not row: raise HTTPException(status_code=404, detail="Project not found")
        return dict(row)

@router.put("/{project_id}", response_model=Project)
async def update_limits(project_id: UUID, daily: Optional[float] = None, monthly: Optional[float] = None, total: Optional[float] = None):
    if not db.pool: await db.connect()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE projects
            SET daily_limit = COALESCE($2, daily_limit),
                monthly_limit = COALESCE($3, monthly_limit),
                total_limit = COALESCE($4, total_limit),
                updated_at = NOW()
            WHERE id = $1
            RETURNING *
        """, project_id, daily, monthly, total)
        if not row: raise HTTPException(status_code=404, detail="Project not found")
        return dict(row)
