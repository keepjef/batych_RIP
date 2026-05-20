from langgraph.graph import StateGraph, END

from graph.state import GraphState
from graph.nodes import (
    init_project,
    drafter,
    reviewer,
    error_gateway,
    diagram_maker,
    doc_writer,
)


def router(state: GraphState):
    errors = state.get("errors", [])
    draft_text = state.get("draft_text", "").lower()
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 3)

    if len(errors) > 0:
        if current_iteration >= max_iterations:
            if "схема" in draft_text:
                return "diagram_maker"
            return "doc_writer"
        return "error_gateway"

    if "схема" in draft_text:
        return "diagram_maker"

    return "doc_writer"


def gateway_router(state: GraphState):
    decision = state.get("user_decision", "").strip().lower()
    draft_text = state.get("draft_text", "").lower()

    if decision in ["принять", "ok", "ок", "дальше"]:
        if "схема" in draft_text:
            return "diagram_maker"
        return "doc_writer"

    return "drafter"


workflow = StateGraph(GraphState)

workflow.add_node("init_project", init_project)
workflow.add_node("drafter", drafter)
workflow.add_node("reviewer", reviewer)
workflow.add_node("error_gateway", error_gateway)
workflow.add_node("diagram_maker", diagram_maker)
workflow.add_node("doc_writer", doc_writer)

workflow.set_entry_point("init_project")

workflow.add_edge("init_project", "drafter")
workflow.add_edge("drafter", "reviewer")
workflow.add_conditional_edges("reviewer", router)
workflow.add_conditional_edges("error_gateway", gateway_router)
workflow.add_edge("diagram_maker", "doc_writer")
workflow.add_edge("doc_writer", END)

app = workflow.compile()
