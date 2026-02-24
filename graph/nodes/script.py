from graph.state import CreativeState

def script_split_node(style: str, llm):
    def node(state: CreativeState):
        idea = state["selected_idea"]
        memory_context = "\n".join([f"- {s['content'][:300]}..." for s in state.get('memory_context', [])])
        prompt = f"""
        Idea: {idea}
        Creative Context: {memory_context}
        Style: {style}
        Constraints: {state['constraints']}

        Produce a full short-form script draft. Include a hook, body, and call to action.
        """
        script = llm.generate_text(role="script", user_prompt=prompt)
        return {"script_variants": state["script_variants"] + [{"style": style, "content": script}]}
    return node