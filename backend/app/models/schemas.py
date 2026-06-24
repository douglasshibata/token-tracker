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
    project_id: UUID
    capture_mode: str
    method: str
    provider_id: Optional[UUID] = None
    model: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    was_blocked: bool
    generation_ratio: Optional[Decimal] = None
    is_tool_call: bool
    tool_name: Optional[str] = None
    latency_ms: int
    created_at: datetime
