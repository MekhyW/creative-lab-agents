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