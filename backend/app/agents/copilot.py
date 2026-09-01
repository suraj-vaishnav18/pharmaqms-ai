"""
Powers the chat-driven "AI Complaint Intake Assistant" panel — mirrors the
reference demo: paste text or drop a PDF, the AI extracts structured fields
and populates the form; you can then correct fields conversationally.
"""
import json

from app.agents.llm import call_fast_model, safe_json_parse

FIELD_SCHEMA_DESCRIPTION = """
Extract these fields from the complaint text as JSON (use null for anything not mentioned,
never invent data that isn't in the text):
{
  "complaint_source": "Email | Phone | Pharmacy | Portal | Distributor | ...",
  "customer_name": "string or null",
  "product_name": "string or null",
  "product_strength": "e.g. '500 mg' or null",
  "batch_number": "string or null",
  "manufacturing_date": "string or null",
  "expiry_date": "string or null",
  "affected_quantity": "string or null, e.g. '12 capsules'",
  "complaint_category": "short category, e.g. 'Product Defect - Discoloration'",
  "complaint_description": "1-2 sentence clean summary of the complaint itself",
  "severity_suggested": "Minor | Major | Critical",
  "suggested_next_action": "short recommended next step, e.g. 'Route to QA Investigation & Issue Replacement'",
  "initial_risk_assessment": "1-2 sentence plain-language risk assessment"
}
"""


def extract_fields_from_text(text: str) -> dict:
    raw = call_fast_model(
        system_prompt=(
            "You are an AI intake assistant for a pharmaceutical Quality Management System. "
            "You read raw customer complaint text (emails, verbal notes, PDF reports) and extract "
            "structured fields for a QA analyst's form. " + FIELD_SCHEMA_DESCRIPTION +
            "\nReply with ONLY the JSON object, no other text."
        ),
        user_prompt=text,
        json_mode=True,
    )
    return safe_json_parse(raw, {})


def apply_chat_correction(message: str, current_fields: dict) -> dict:
    """
    Handles follow-up corrections like 'ah sorry the batch number is X and
    affected quantity is 48 capsules' — merges only the fields the user
    actually mentioned into the existing extracted fields.
    """
    prompt = (
        f"Current extracted form fields (JSON): {json.dumps(current_fields)}\n\n"
        f"User correction/follow-up message: \"{message}\"\n\n"
        "Return the FULL updated JSON object with the same schema, applying only "
        "the changes implied by the user's message and leaving everything else unchanged. "
        "Reply with ONLY the JSON object."
    )
    raw = call_fast_model(
        system_prompt=(
            "You update a partially-filled pharma complaint intake form based on a user's "
            "natural-language correction. " + FIELD_SCHEMA_DESCRIPTION
        ),
        user_prompt=prompt,
        json_mode=True,
    )
    updated = safe_json_parse(raw, current_fields)
    # Fallback safety: never drop fields the model forgot to echo back
    merged = {**current_fields, **{k: v for k, v in updated.items() if v is not None}}
    return merged


def assistant_ack_message(fields: dict, source_label: str = "the complaint") -> str:
    """Simple templated confirmation, mirrors the reference demo's tone."""
    product = fields.get("product_name") or "the product"
    issue = fields.get("complaint_category") or "the reported issue"
    return (
        f"Complaint parsed successfully. I've extracted the product details for {product}, "
        f"mapped the batch information, and generated an initial risk assessment for {issue}."
    )
