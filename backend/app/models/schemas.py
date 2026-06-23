from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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

class User(BaseModel):
    id: UUID
    display_name: str
    email: str
    role: str
    department: Optional[str] = None
    class Config:
        from_attributes = True

class LLMRequest(BaseModel):
    id: UUID
    capture_mode: str
    method: str
    provider_name: Optional[str] = None
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: Decimal
    latency_ms: int
    created_at: datetime
