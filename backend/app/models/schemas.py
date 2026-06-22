from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    budget_limit: Optional[Decimal] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class APICallBase(BaseModel):
    project_id: UUID
    provider_id: UUID
    model: str
    user_id: Optional[str] = None
    input_tokens: int
    output_tokens: int
    input_cost: Decimal
    output_cost: Decimal
    request_metadata: Optional[Dict[str, Any]] = None

class APICall(APICallBase):
    id: UUID
    total_tokens: int
    total_cost: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class UsageReport(BaseModel):
    project_id: str
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    breakdown_by_provider: Dict[str, Any]
    breakdown_by_model: Dict[str, Any]
    daily_trend: List[Dict[str, Any]]

class BudgetAlertBase(BaseModel):
    project_id: UUID
    threshold_percentage: int
    notification_channel: str

class BudgetAlert(BudgetAlertBase):
    id: UUID
    is_triggered: bool
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
