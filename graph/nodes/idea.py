from graph.state import CreativeState

def idea_divergence_node(style: str, llm):
    def node(state: CreativeState):
        trend_context = "\n".join([f"- {t['topic']}: {t.get('rationale', '')}" for t in state.get('trend_signals', [])])
        memory_context = "\n".join([f"- Content from {s.get('source', 'Vault')}: {s['content'][:300]}..." for s in state.get('memory_context', [])])
        prompt = f"""
        You are a creative brainstormer. 
        Theme: {state['theme']}
        Style: {style}
        Constraints: {state['constraints']}
        
        ### TREND SIGNALS
        {trend_context}
        
        ### CREATIVE SEEDS (From Obsidian Vault)
        {memory_context}
        
        Task: Generate 3 video concepts that combine a trending topic with a unique 'twist' from the creative seeds.
        Format: JSON list of objects with 'title', 'hook', 'twist', 'trend_alignment'.
        """
        ideas = llm.generate_json(role="brainstorm", user_prompt=prompt)
        if not isinstance(ideas, list):
            ideas = [ideas]
        return {"idea_pool": state["idea_pool"] + ideas}
    return node


def idea_ranking_node(llm):
    def node(state: CreativeState):
        prompt = f"""
        You are a content critic. Rank these ideas based on:
        1. Hook strength
        2. Trend alignment
        3. Uniqueness of the 'twist'
        
        Ideas: {state['idea_pool']}
        
        Return JSON list of ideas sorted by rank, with a 'score' and 'ranking_rationale'.
        """
        ranked = llm.generate_json(role="critic", user_prompt=prompt)
        return {"ranked_ideas": ranked}
    return node