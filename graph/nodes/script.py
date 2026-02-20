def script_split_node(style: str):
    def node(state: CreativeState):
        idea = state["selected_idea"]
        prompt = f"""
        Idea: {idea}
        Memory: {state['memory_context']}
        Style: {style}

        Produce full short-form script draft.
        """
        script = llm.generate_text(prompt)
        return {
            "script_variants": state["script_variants"] + [{
                "style": style,
                "content": script
            }]
        }
    return node