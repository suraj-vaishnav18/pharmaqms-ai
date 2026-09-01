from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ComplaintCreate(BaseModel):
    product_name: str
    batch_number: Optional[str] = None
    customer_name: Optional[str] = None
    channel: str = "portal"
    description: str
    intake_details: Optional[Any] = None


class ComplaintOut(BaseModel):
    id: str
    product_name: str
    batch_number: Optional[str]
    customer_name: Optional[str]
    channel: str
    description: str
    status: str
    severity: Optional[str]
    category: Optional[str]
    completeness_flags: Optional[Any]
    duplicate_of: Optional[str]
    root_cause_suggestion: Optional[str]
    ai_summary: Optional[str]
    risk_classification: Optional[str]
    capa_suggestions: Optional[Any]
    intake_details: Optional[Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopilotTextRequest(BaseModel):
    text: str


class CopilotChatRequest(BaseModel):
    message: str
    current_fields: dict = {}


class CopilotResponse(BaseModel):
    fields: dict
    assistant_message: str


class CAPACreate(BaseModel):
    complaint_id: str
    action_type: str
    description: str
    owner: Optional[str] = None
    due_date: Optional[datetime] = None


class CAPAOut(BaseModel):
    id: str
    complaint_id: str
    action_type: str
    description: str
    owner: Optional[str]
    status: str
    ai_recommended: str
    created_at: datetime

    class Config:
        from_attributes = True
