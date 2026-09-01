from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader
import io

from app import schemas
from app.agents.copilot import extract_fields_from_text, apply_chat_correction, assistant_ack_message

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/extract-text", response_model=schemas.CopilotResponse)
def extract_from_text(payload: schemas.CopilotTextRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    fields = extract_fields_from_text(payload.text)
    return {"fields": fields, "assistant_message": assistant_ack_message(fields)}


@router.post("/extract-file", response_model=schemas.CopilotResponse)
def extract_from_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF upload is supported right now — paste text for other formats.")

    contents = file.file.read()
    try:
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this PDF. Try pasting the text instead.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in this PDF (it may be scanned/image-only).")

    fields = extract_fields_from_text(text)
    return {"fields": fields, "assistant_message": assistant_ack_message(fields)}


@router.post("/chat", response_model=schemas.CopilotResponse)
def chat_correction(payload: schemas.CopilotChatRequest):
    updated_fields = apply_chat_correction(payload.message, payload.current_fields)
    return {
        "fields": updated_fields,
        "assistant_message": "Got it — I've updated the form with your correction.",
    }
