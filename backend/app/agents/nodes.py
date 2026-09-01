"""
Each function is a LangGraph node. They all take the pipeline state (a dict)
and return a dict of the fields they want to update — LangGraph merges it
into the overall state.

State shape (see graph.py for the TypedDict):
    complaint_id, product_name, batch_number, description,
    existing_complaints (for duplicate check, passed in from the router),
    completeness_flags, is_duplicate, duplicate_of,
    severity, category, root_cause_suggestion,
    capa_recommendations, ai_summary, risk_classification,
    trace  (list of step logs, useful for the frontend "show your work" UI)
"""
from app.agents.llm import call_fast_model, call_reasoning_model, safe_json_parse


def _log(state: dict, step: str, detail: str) -> list:
    trace = list(state.get("trace", []))
    trace.append({"step": step, "detail": detail})
    return trace


def completeness_check_node(state: dict) -> dict:
    """Flags missing info a real QMS complaint record needs."""
    required_fields = ["product_name", "batch_number", "description"]
    missing = [f for f in required_fields if not state.get(f)]

    prompt = (
        f"Complaint description: {state['description']}\n\n"
        "Does this description mention a specific defect/issue, a date or timeframe, "
        "and enough detail to start an investigation? "
        'Reply as JSON: {"missing_context": ["item1", "item2"], "notes": "short note"}'
    )
    raw = call_fast_model(
        system_prompt="You are a QMS intake assistant checking complaint completeness.",
        user_prompt=prompt,
        json_mode=True,
    )
    parsed = safe_json_parse(raw, {"missing_context": [], "notes": ""})

    flags = {"missing_fields": missing, **parsed}
    return {
        "completeness_flags": flags,
        "trace": _log(state, "completeness_check", f"Missing/flagged: {flags}"),
    }


def _tfidf_vector(text: str, idf: dict) -> dict:
    words = [w for w in text.lower().split() if w.isalpha()]
    if not words:
        return {}
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    total = len(words)
    return {w: (c / total) * idf.get(w, 1.0) for w, c in counts.items()}


def _cosine_sim(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    numerator = sum(a[w] * b[w] for w in common)
    mag_a = sum(v * v for v in a.values()) ** 0.5
    mag_b = sum(v * v for v in b.values()) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return numerator / (mag_a * mag_b)


def duplicate_check_node(state: dict) -> dict:
    """
    TF-IDF + cosine similarity duplicate check against existing complaints for
    the same product. This avoids pulling in a heavy embeddings model just for
    the assignment demo, while still being meaningfully better than raw
    keyword overlap (rare/distinctive words are weighted higher than common
    ones like 'the' or 'tablet').
    """
    import math

    existing = state.get("existing_complaints", [])
    if not existing:
        return {"is_duplicate": False, "duplicate_of": None, "trace": _log(state, "duplicate_check", "No prior complaints to compare against")}

    corpus = [state["description"]] + [c["description"] for c in existing]
    doc_count = len(corpus)

    # Build IDF across this small corpus
    word_doc_freq = {}
    for doc in corpus:
        seen = set(w for w in doc.lower().split() if w.isalpha())
        for w in seen:
            word_doc_freq[w] = word_doc_freq.get(w, 0) + 1
    idf = {w: math.log((doc_count + 1) / (freq + 1)) + 1 for w, freq in word_doc_freq.items()}

    target_vec = _tfidf_vector(state["description"], idf)

    best_match, best_score = None, 0.0
    for c in existing:
        other_vec = _tfidf_vector(c["description"], idf)
        score = _cosine_sim(target_vec, other_vec)
        if score > best_score:
            best_match, best_score = c, score

    is_duplicate = best_match is not None and best_score > 0.6
    return {
        "is_duplicate": is_duplicate,
        "duplicate_of": best_match["id"] if is_duplicate else None,
        "trace": _log(
            state, "duplicate_check",
            f"Best TF-IDF cosine similarity={best_score:.2f} (threshold 0.60), duplicate={is_duplicate}",
        ),
    }


def classification_node(state: dict) -> dict:
    """Severity + category classification. Fast model — this is a routine task."""
    prompt = (
        f"Product: {state.get('product_name')}\n"
        f"Complaint: {state['description']}\n\n"
        "Classify this pharmaceutical customer complaint. "
        'Reply as JSON: {"severity": "low|medium|high|critical", '
        '"category": "short category e.g. packaging, potency, contamination, labeling", '
        '"reasoning": "one sentence"}'
    )
    raw = call_fast_model(
        system_prompt=(
            "You are a pharmaceutical QMS triage assistant. Severity should reflect "
            "patient safety risk: critical = potential harm/contamination, "
            "high = efficacy/quality concern, medium = packaging/labeling, low = cosmetic/delivery."
        ),
        user_prompt=prompt,
        json_mode=True,
    )
    parsed = safe_json_parse(raw, {"severity": "medium", "category": "unclassified", "reasoning": ""})

    return {
        "severity": parsed.get("severity", "medium"),
        "category": parsed.get("category", "unclassified"),
        "trace": _log(state, "classification", parsed.get("reasoning", "")),
    }


def root_cause_node(state: dict) -> dict:
    """Deeper reasoning task -> the 70b model."""
    prompt = (
        f"Product: {state.get('product_name')}\n"
        f"Batch: {state.get('batch_number')}\n"
        f"Category: {state.get('category')}\n"
        f"Complaint: {state['description']}\n\n"
        "Suggest 2-3 plausible root causes an investigator should check first, "
        "and one recommended next investigative step. Keep it concise."
    )
    root_cause = call_reasoning_model(
        system_prompt=(
            "You are assisting a pharma quality investigator with root cause hypotheses "
            "for a customer complaint. You are not making a final determination — you are "
            "giving starting hypotheses for a human investigator to verify."
        ),
        user_prompt=prompt,
    )
    return {
        "root_cause_suggestion": root_cause,
        "trace": _log(state, "root_cause", "Generated root cause hypotheses"),
    }


def capa_recommendation_node(state: dict) -> dict:
    prompt = (
        f"Category: {state.get('category')}\n"
        f"Severity: {state.get('severity')}\n"
        f"Root cause hypotheses: {state.get('root_cause_suggestion')}\n\n"
        'Suggest CAPA actions as JSON: {"corrective": ["action1"], "preventive": ["action1"]}'
    )
    raw = call_reasoning_model(
        system_prompt="You are a pharma QMS assistant drafting CAPA (Corrective and Preventive Action) suggestions.",
        user_prompt=prompt,
        json_mode=True,
    )
    parsed = safe_json_parse(raw, {"corrective": [], "preventive": []})
    return {
        "capa_recommendations": parsed,
        "trace": _log(state, "capa_recommendation", f"{parsed}"),
    }


def summary_node(state: dict) -> dict:
    prompt = (
        f"Product: {state.get('product_name')}, Severity: {state.get('severity')}, "
        f"Category: {state.get('category')}\n"
        f"Complaint: {state['description']}\n"
        f"Root cause hypotheses: {state.get('root_cause_suggestion')}\n\n"
        "Write a 2-3 sentence executive summary of this complaint for a quality manager's dashboard."
    )
    summary = call_fast_model(
        system_prompt="You write concise, factual QMS complaint summaries for management review.",
        user_prompt=prompt,
    )
    return {
        "ai_summary": summary,
        "risk_classification": state.get("severity", "medium"),
        "trace": _log(state, "summary", "Generated executive summary"),
    }
