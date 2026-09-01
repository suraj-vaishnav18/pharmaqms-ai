from typing import TypedDict, Optional, Any, List

from langgraph.graph import StateGraph, END

from app.agents.nodes import (
    completeness_check_node,
    duplicate_check_node,
    classification_node,
    root_cause_node,
    capa_recommendation_node,
    summary_node,
)


class ComplaintState(TypedDict, total=False):
    complaint_id: str
    product_name: str
    batch_number: Optional[str]
    description: str
    existing_complaints: List[dict]

    completeness_flags: dict
    is_duplicate: bool
    duplicate_of: Optional[str]
    severity: str
    category: str
    root_cause_suggestion: str
    capa_recommendations: dict
    ai_summary: str
    risk_classification: str
    trace: List[dict]


def route_after_duplicate_check(state: ComplaintState) -> str:
    """If it's a duplicate, skip straight to summary — no need to re-run
    classification/root-cause/CAPA, just point at the existing complaint."""
    if state.get("is_duplicate"):
        return "summary"
    return "classification"


def build_complaint_graph():
    graph = StateGraph(ComplaintState)

    graph.add_node("completeness_check", completeness_check_node)
    graph.add_node("duplicate_check", duplicate_check_node)
    graph.add_node("classification", classification_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("capa_recommendation", capa_recommendation_node)
    graph.add_node("summary", summary_node)

    graph.set_entry_point("completeness_check")
    graph.add_edge("completeness_check", "duplicate_check")
    graph.add_conditional_edges(
        "duplicate_check",
        route_after_duplicate_check,
        {"summary": "summary", "classification": "classification"},
    )
    graph.add_edge("classification", "root_cause")
    graph.add_edge("root_cause", "capa_recommendation")
    graph.add_edge("capa_recommendation", "summary")
    graph.add_edge("summary", END)

    return graph.compile()


# Compiled once, reused across requests
complaint_pipeline = build_complaint_graph()
