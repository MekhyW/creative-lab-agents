def idea_divergence_node(style: str):
    def node(state: CreativeState):
        prompt = f"""
        Theme: {state['theme']}
        Constraints: {state['constraints']}
        Memory Context: {state['memory_context']}

        Generate 5 bold video concepts in style: {style}
        Avoid repeating recent formats.
        """
        ideas = llm.generate_json(prompt)
        return {"idea_pool": state["idea_pool"] + ideas}
    return node


def idea_ranking_node(state: CreativeState):
    prompt = f"""
    Score each idea (1-10) for:
    - Hook strength
    - Novelty vs past work
    - Format freshness
    - Trend alignment

    Ideas: {state['idea_pool']}
    """
    ranked = llm.generate_json(prompt)
    return {"ranked_ideas": ranked}