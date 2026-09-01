from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/capa", tags=["capa"])


@router.post("/", response_model=schemas.CAPAOut)
def create_capa(payload: schemas.CAPACreate, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    capa = models.CAPAAction(**payload.model_dump())
    db.add(capa)

    complaint.status = models.ComplaintStatus.capa_initiated
    db.commit()
    db.refresh(capa)
    return capa


@router.get("/by-complaint/{complaint_id}", response_model=list[schemas.CAPAOut])
def list_capa_for_complaint(complaint_id: str, db: Session = Depends(get_db)):
    return db.query(models.CAPAAction).filter(models.CAPAAction.complaint_id == complaint_id).all()
