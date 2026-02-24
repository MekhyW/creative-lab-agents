from graph.state import CreativeState

def final_package_node(llm):
    def node(state: CreativeState):
        prompt = f"""
        Finalizing production package for:
        Script: {state['selected_script']}
        
        Generate:
        - Hook Title
        - Shot list
        - B-roll cues
        - Thumbnail concepts
        
        Return JSON object.
        """
        package = llm.generate_json(role="utility", user_prompt=prompt)
        return {"final_package": package}
    return node