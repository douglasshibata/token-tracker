from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    total_limit: Optional[Decimal] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
