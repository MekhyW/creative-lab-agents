def final_package_node(state: CreativeState):
    prompt = f"""
    Script: {state['selected_script']}
    Generate:
    - Shot list
    - B-roll cues
    - Title ideas
    - Thumbnail concepts
    """
    package = llm.generate_json(prompt)
    return {"final_package": package}