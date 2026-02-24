from graph.state import CreativeState

def critic_node(llm):
    def node(state: CreativeState):
        prompt = f"""
        Evaluate these script variants for:
        - Hook strength (1-10)
        - Retention potential
        - Emotional payoff
        
        Scripts: {state['script_variants']}
        
        Return JSON list of objects with 'style', 'score', and 'critique_points'.
        """
        scored = llm.generate_json(role="critic", user_prompt=prompt)
        return {
            "scored_variants": scored,
            "iteration_count": state["iteration_count"] + 1
        }
    return node

def critic_router(state: CreativeState):
    if not state.get("scored_variants"):
        return "approve" # Safety
    best_score = max(v.get("score", 0) for v in state["scored_variants"])
    if best_score < 7 and state["iteration_count"] < 3:
        return "rewrite"
    else:
        return "approve"