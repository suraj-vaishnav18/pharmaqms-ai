from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.agents.graph import complaint_pipeline

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _write_audit(db: Session, complaint_id: str, action: str, details: dict, actor: str = "system"):
    entry = models.AuditLog(complaint_id=complaint_id, action=action, details=details, actor=actor)
    db.add(entry)
    db.commit()


@router.post("/", response_model=schemas.ComplaintOut)
def create_complaint(payload: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    complaint = models.Complaint(**payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    _write_audit(db, complaint.id, "complaint_created", {"channel": complaint.channel})
    return complaint


@router.get("/", response_model=list[schemas.ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(models.Complaint).order_by(models.Complaint.created_at.desc()).all()


@router.get("/{complaint_id}", response_model=schemas.ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.post("/{complaint_id}/run-ai-pipeline", response_model=schemas.ComplaintOut)
def run_ai_pipeline(complaint_id: str, db: Session = Depends(get_db)):
    """
    Runs the LangGraph pipeline (completeness -> duplicate check -> classify
    -> root cause -> CAPA -> summary) and persists the results onto the
    complaint row. Returns the updated complaint, including `trace` info
    logged to the audit log so the frontend can show step-by-step reasoning.
    """
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    existing = (
        db.query(models.Complaint)
        .filter(models.Complaint.product_name == complaint.product_name)
        .filter(models.Complaint.id != complaint.id)
        .all()
    )
    existing_payload = [{"id": c.id, "description": c.description} for c in existing]

    initial_state = {
        "complaint_id": complaint.id,
        "product_name": complaint.product_name,
        "batch_number": complaint.batch_number,
        "description": complaint.description,
        "existing_complaints": existing_payload,
        "trace": [],
    }

    result = complaint_pipeline.invoke(initial_state)

    complaint.completeness_flags = result.get("completeness_flags")
    complaint.duplicate_of = result.get("duplicate_of")
    complaint.severity = result.get("severity")
    complaint.category = result.get("category")
    complaint.root_cause_suggestion = result.get("root_cause_suggestion")
    complaint.ai_summary = result.get("ai_summary")
    complaint.risk_classification = result.get("risk_classification")
    complaint.capa_suggestions = result.get("capa_recommendations")
    complaint.status = models.ComplaintStatus.triaged

    db.commit()
    db.refresh(complaint)

    _write_audit(db, complaint.id, "ai_pipeline_run", {"trace": result.get("trace", [])}, actor="ai_pipeline")

    # capa_recommendations from the graph aren't auto-created as CAPAAction rows —
    # that's a deliberate human-in-the-loop step, exposed via a separate endpoint below.
    return complaint


@router.get("/{complaint_id}/ai-trace")
def get_ai_trace(complaint_id: str, db: Session = Depends(get_db)):
    """Returns the most recent AI pipeline run's step-by-step trace,
    useful for the 'show your work' panel in the UI."""
    entry = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.complaint_id == complaint_id)
        .filter(models.AuditLog.action == "ai_pipeline_run")
        .order_by(models.AuditLog.timestamp.desc())
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="No AI pipeline run found for this complaint")
    return entry.details
