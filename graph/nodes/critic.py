def critic_node(state: CreativeState):
    prompt = f"""
    Evaluate script variants.
    Score 1-10 for:
    - Opening hook
    - Escalation
    - Emotional payoff
    - Originality

    Scripts: {state['script_variants']}
    """
    scored = llm.generate_json(prompt)
    return {
        "scored_variants": scored,
        "iteration_count": state["iteration_count"] + 1
    }


def critic_router(state: CreativeState):
    best_score = max(v["score"] for v in state["scored_variants"])
    if best_score < 8 and state["iteration_count"] < 3:
        return "rewrite"
    else:
        return "approve"