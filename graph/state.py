from typing import TypedDict, List
class GraphState(TypedDict):
    thesis_title: str
    problem_statement: str
    thesis_goal: str
    thesis_tasks: str
    current_section: str
    draft_text: str
    pdf_context: str
    errors: List[str]
    user_decision: str
    diagram_xml: str
    human_mode: bool
    max_iterations: int
    current_iteration: int