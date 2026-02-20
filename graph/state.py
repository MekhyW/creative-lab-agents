from typing import TypedDict, List, Optional, Dict, Any

class CreativeState(TypedDict):
    # User Input
    theme: Optional[str]
    constraints: List[str]

    # External context
    memory_context: List[str]
    trend_signals: List[Dict[str, Any]]

    # Idea phase
    idea_pool: List[Dict[str, Any]]
    ranked_ideas: List[Dict[str, Any]]
    selected_idea: Optional[Dict[str, Any]]

    # Script phase
    script_variants: List[Dict[str, Any]]
    scored_variants: List[Dict[str, Any]]
    selected_script: Optional[Dict[str, Any]]

    # Critique loop
    critique_log: List[str]
    iteration_count: int

    # Human control
    human_feedback: Optional[str]
    approval_stage: Optional[str]

    # Output
    final_package: Optional[Dict[str, Any]]