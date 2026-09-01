import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON

from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SeverityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ComplaintStatus(str, enum.Enum):
    new = "new"
    triaged = "triaged"
    investigating = "investigating"
    capa_initiated = "capa_initiated"
    resolved = "resolved"
    closed = "closed"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    channel = Column(String, default="portal")  # email, portal, phone
    description = Column(Text, nullable=False)

    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.new)
    severity = Column(Enum(SeverityLevel), nullable=True)
    category = Column(String, nullable=True)

    # AI pipeline outputs
    completeness_flags = Column(JSON, nullable=True)  # missing fields, etc.
    duplicate_of = Column(String, nullable=True)       # complaint id if duplicate
    root_cause_suggestion = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    risk_classification = Column(String, nullable=True)
    capa_suggestions = Column(JSON, nullable=True)  # {"corrective": [...], "preventive": [...]}

    # Rich fields captured by the AI intake copilot (product strength, mfg/expiry
    # dates, affected quantity, suggested next action, etc.) - kept as flexible
    # JSON so the intake form can evolve without a DB migration each time.
    intake_details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    capa_actions = relationship("CAPAAction", back_populates="complaint")
    audit_entries = relationship("AuditLog", back_populates="complaint")


class CAPAAction(Base):
    __tablename__ = "capa_actions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id"))
    action_type = Column(String)  # corrective / preventive
    description = Column(Text)
    owner = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="open")
    ai_recommended = Column(String, default="false")  # "true" if AI-suggested

    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="capa_actions")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id"))
    action = Column(String)          # e.g. "status_changed", "ai_classification_run"
    details = Column(JSON, nullable=True)
    actor = Column(String, default="system")  # user id or "ai_pipeline"
    timestamp = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="audit_entries")
